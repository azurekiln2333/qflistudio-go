param(
  [Parameter(Mandatory)][string]$Url,
  [Parameter(Mandatory)][string]$Sha256,
  [Parameter(Mandatory)][string]$Destination
)
$ErrorActionPreference = 'Stop'
if ($Sha256 -notmatch '^[a-fA-F0-9]{64}$') { throw 'OHOS SDK SHA-256 must contain 64 hexadecimal characters.' }
if (-not $Url.StartsWith('https://')) { throw 'OHOS SDK download URL must use HTTPS.' }
if (Test-Path -LiteralPath $Destination) { throw 'OHOS SDK destination must be new.' }
New-Item -ItemType Directory -Path $Destination | Out-Null
$archive = Join-Path $Destination 'sdk-download'
& curl.exe --fail --location --retry 3 --output $archive $Url
if ($LASTEXITCODE -ne 0) { throw 'OHOS SDK download failed.' }
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $Sha256) { throw 'OHOS SDK archive SHA-256 mismatch.' }
$listing = @(& tar -tf $archive)
if ($LASTEXITCODE -ne 0) { throw 'Cannot list OHOS SDK archive.' }
# The official SDK bundle contains separate ZIP packages per host/component.
$nativePackages = @($listing | Where-Object { $_ -match '(?i)(windows.*native|native.*windows).*\.zip$' })
$extract = Join-Path $Destination 'extracted'
New-Item -ItemType Directory -Path $extract | Out-Null
if ($nativePackages.Count -eq 1) {
  & tar -xf $archive -C $extract $nativePackages[0]
  if ($LASTEXITCODE -ne 0) { throw 'Cannot extract OHOS Windows native package.' }
  $package = Join-Path $extract $nativePackages[0]
  Expand-Archive -LiteralPath $package -DestinationPath (Join-Path $Destination 'native-package')
} elseif ($nativePackages.Count -eq 0) {
  # Also accept a checksum-pinned archive of the native SDK directory itself.
  & tar -xf $archive -C $extract
  if ($LASTEXITCODE -ne 0) { throw 'Cannot extract OHOS SDK archive.' }
} else {
  throw 'OHOS SDK archive contains multiple Windows native packages.'
}
$compilers = @(Get-ChildItem -LiteralPath $Destination -Recurse -File -Filter clang.exe |
  Where-Object { $_.FullName -match '[\\/]native[\\/]llvm[\\/]bin[\\/]clang\.exe$' })
if ($compilers.Count -ne 1) { throw 'OHOS SDK must contain exactly one native/llvm/bin/clang.exe.' }
$sdk = Split-Path (Split-Path (Split-Path (Split-Path $compilers[0].FullName)))
foreach ($relative in @('native/sysroot', 'native/llvm/bin/llvm-strip.exe', 'native/llvm/bin/llvm-readelf.exe')) {
  if (-not (Test-Path -LiteralPath (Join-Path $sdk $relative))) { throw "Missing OHOS SDK component: $relative" }
}
if ($env:GITHUB_ENV) { "OHOS_SDK_HOME=$sdk" | Out-File -FilePath $env:GITHUB_ENV -Encoding utf8 -Append }
Write-Output "OHOS SDK ready: $sdk"
