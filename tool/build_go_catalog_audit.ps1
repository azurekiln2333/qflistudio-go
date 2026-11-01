param(
  [ValidateSet('ohos-x64', 'ohos-arm64')]
  [string]$TargetPlatform = 'ohos-x64',
  [string]$FlutterExecutable = 'flutter',
  [string]$OutputDirectory
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
if (-not $OutputDirectory) {
  $OutputDirectory = Join-Path $root "build/go-catalog-audit/$TargetPlatform"
}
$output = [IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Force -Path $output | Out-Null
$profilePath = Join-Path $root 'ohos/entry/build-profile.json5'
$abi = if ($TargetPlatform -eq 'ohos-x64') { 'x86_64' } else { 'arm64-v8a' }
$excludedAbi = if ($abi -eq 'x86_64') { 'arm64-v8a' } else { 'x86_64' }
# These three compiled sources own the catalog plus all five API/four UI cases.
# Keep the same list as AUDIT_SOURCE_PATHS in inspect_go_catalog_hap.py.
$auditSourcePaths = @(
  'integration_test/go_catalog_test.dart',
  'integration_test/go_native_ide_acceptance.dart',
  'integration_test/go_product_ui_acceptance.dart'
)

function Get-AuditSourceHashes {
  $hashes = [ordered]@{}
  foreach ($relative in $auditSourcePaths) {
    $path = Join-Path $root $relative
    $hashes[$relative] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
  }
  return $hashes
}

# This preflight precedes public entry-profile mutation. The inspector also
# compares each exact source payload with the debug kernel, not only markers.
$auditSourcesBefore = Get-AuditSourceHashes

function Get-BytesHash([byte[]]$Bytes) {
  $sha = [Security.Cryptography.SHA256]::Create()
  try { return [BitConverter]::ToString($sha.ComputeHash($Bytes)).Replace('-', '').ToLowerInvariant() }
  finally { $sha.Dispose() }
}

function Read-ProfileBytes {
  $profileStream.Position = 0
  $copy = [IO.MemoryStream]::new()
  try { $profileStream.CopyTo($copy); return ,$copy.ToArray() }
  finally { $copy.Dispose() }
}

function Write-ProfileBytes([byte[]]$Bytes) {
  $profileStream.Position = 0
  $profileStream.Write($Bytes, 0, $Bytes.Length)
  $profileStream.SetLength($Bytes.Length)
  $profileStream.Flush($true)
}

$profileStream = $null
$profileChanged = $false
$temporaryWriteFinished = $false
$locationPushed = $false
try {
  # Keep the same file handle throughout read/modify/build/restore. On Windows
  # sharing allows build readers but excludes a second writer or script run.
  $profileStream = [IO.File]::Open($profilePath, [IO.FileMode]::Open,
    [IO.FileAccess]::ReadWrite, [IO.FileShare]::Read)
  $originalBytes = Read-ProfileBytes
  $originalHash = Get-BytesHash $originalBytes
  $profile = [Text.Encoding]::UTF8.GetString($originalBytes)
  $abiPattern = '"abiFilters"\s*:\s*\[[^\]]*\]'
  $excludePattern = '"excludes"\s*:\s*\[[^\]]*\]'
  if ([regex]::Matches($profile, $abiPattern).Count -ne 1 -or
      [regex]::Matches($profile, $excludePattern).Count -ne 1) {
    throw 'Expected exactly one entry ABI filter and native-library exclusion list.'
  }
  $temporaryProfile = [regex]::Replace($profile, $abiPattern, '"abiFilters": ["' + $abi + '"]')
  $temporaryProfile = [regex]::Replace($temporaryProfile, $excludePattern,
    '"excludes": ["**/' + $excludedAbi + '/**", "**/armeabi-v7a/**"]')
  $temporaryBytes = [Text.UTF8Encoding]::new($false).GetBytes($temporaryProfile)
  $temporaryHash = Get-BytesHash $temporaryBytes
  $runId = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffffff') + "-$PID"
  $backupPath = Join-Path $output "entry-build-profile-original-$runId.json5"
  [IO.File]::WriteAllBytes($backupPath, $originalBytes)
  # The mutation flag precedes the first write so a partial write also restores.
  $profileChanged = $true
  Write-ProfileBytes $temporaryBytes
  $temporaryWriteFinished = $true
  Push-Location $root
  $locationPushed = $true
  $LASTEXITCODE = $null
  & $FlutterExecutable build hap --debug --no-pub `
    --target integration_test/go_catalog_test.dart --target-platform $TargetPlatform
  if ($null -eq $LASTEXITCODE -or $LASTEXITCODE -ne 0) {
    throw "Go catalog audit HAP build failed: $LASTEXITCODE"
  }
  $auditSourcesAfter = Get-AuditSourceHashes
  foreach ($relative in $auditSourcePaths) {
    if ($auditSourcesBefore[$relative] -ne $auditSourcesAfter[$relative]) {
      throw "Audit source changed during HAP build: $relative"
    }
  }
  $hap = Join-Path $root 'build/ohos/hap/entry-default-signed.hap'
  if (-not (Test-Path -LiteralPath $hap -PathType Leaf)) {
    throw 'The build produced no signed-named HAP; inspect the existing Go signing setup.'
  }
  $hash = (Get-FileHash -LiteralPath $hap -Algorithm SHA256).Hash.ToLowerInvariant()
  $preservedHap = Join-Path $output "go-catalog-audit-$hash.hap"
  Copy-Item -LiteralPath $hap -Destination $preservedHap
  [ordered]@{
    schemaVersion = 2
    auditSources = $auditSourcesBefore
    targetPlatform = $TargetPlatform
    abi = $abi
    hap = $preservedHap
    hapSha256 = $hash
    entryPoint = 'integration_test/go_catalog_test.dart'
    originalEntryBuildProfileSha256 = $originalHash
    temporaryEntryBuildProfileSha256 = $temporaryHash
    recoveryProfile = $backupPath
    signatureVerified = $false
    archiveInspected = $false
    deviceExecution = $false
  } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $output 'build.json') -Encoding utf8
  Write-Output "Preserved audit HAP: $preservedHap"
} finally {
  try {
    if ($locationPushed) { Pop-Location }
    if ($profileChanged) {
      $currentHash = Get-BytesHash (Read-ProfileBytes)
      if ($temporaryWriteFinished -and $currentHash -ne $temporaryHash) {
        throw "Entry profile changed despite the writer lock; preserved it. Original bytes are at $backupPath"
      }
      Write-ProfileBytes $originalBytes
      if ((Get-BytesHash (Read-ProfileBytes)) -ne $originalHash) {
        throw 'Entry profile byte restoration failed.'
      }
    }
  } finally {
    if ($profileStream) { $profileStream.Dispose() }
  }
}
