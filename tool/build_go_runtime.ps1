param(
  [string]$GoExecutable = 'go',
  [string]$OhosGoExecutable = 'go',
  [string]$PythonExecutable = 'python',
  [string]$AndroidNdk = $env:ANDROID_NDK_HOME,
  [string]$OhosSdk = $env:OHOS_SDK_HOME,
  [ValidateSet('all', 'android', 'ohos')]
  [string]$Platform = 'all'
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$module = Join-Path $root 'native/go_runtime'
$buildAndroid = $Platform -in @('all', 'android')
$buildOhos = $Platform -in @('all', 'ohos')

function Get-RuntimeSourceHash {
  $hash = & $PythonExecutable -c 'import sys; sys.path.insert(0, sys.argv[1]); import audit_native; print(audit_native.native_source_hash())' (Join-Path $root 'tool/go_curriculum')
  if ($LASTEXITCODE -ne 0 -or "$hash" -notmatch '^[a-f0-9]{64}$') {
    throw 'Could not capture the native runtime source digest.'
  }
  return "$hash"
}

$sourceHash = Get-RuntimeSourceHash
$buildStarted = [DateTime]::UtcNow.ToString('o')
$buildInputs = @{}
foreach ($relative in @('tool/build_go_runtime.ps1', 'tool/go_curriculum/audit_native.py', 'native/go_runtime/android-cc.cmd', 'native/go_runtime/ohos-cc.cmd')) {
  $buildInputs[$relative] = (Get-FileHash -LiteralPath (Join-Path $root $relative) -Algorithm SHA256).Hash.ToLowerInvariant()
}
$builtLibraries = @()
$toolchains = @{}
$selectedTools = @()
if ($buildAndroid) { $selectedTools += @{ Name = 'go'; Executable = $GoExecutable } }
if ($buildOhos) { $selectedTools += @{ Name = 'ohosGo'; Executable = $OhosGoExecutable } }
foreach ($tool in $selectedTools) {
  $toolPath = (Get-Command $tool.Executable -CommandType Application -ErrorAction Stop).Source
  $toolchains[$tool.Name] = [ordered]@{
    path = $toolPath
    sha256 = (Get-FileHash -LiteralPath $toolPath -Algorithm SHA256).Hash.ToLowerInvariant()
  }
}

function Assert-RuntimeSourceUnchanged {
  if ((Get-RuntimeSourceHash) -ne $sourceHash) {
    throw 'Native sources changed during the build; no final provenance will be published. Rebuild from stable sources.'
  }
  foreach ($relative in $buildInputs.Keys) {
    if ((Get-FileHash -LiteralPath (Join-Path $root $relative) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $buildInputs[$relative]) {
      throw "Build input changed during the build: $relative"
    }
  }
}

if ($buildAndroid -and (-not $AndroidNdk -or -not (Test-Path -LiteralPath $AndroidNdk))) {
  throw 'Android NDK path is required (-AndroidNdk).'
}
if ($buildOhos -and (-not $OhosSdk -or -not (Test-Path -LiteralPath $OhosSdk))) {
  throw 'OpenHarmony SDK path is required (-OhosSdk).'
}

$savedEnvironment = @{}
foreach ($name in @('ANDROID_NDK_HOME', 'OHOS_SDK_HOME', 'CGO_ENABLED', 'GOOS', 'GOARCH', 'GOARM', 'CC', 'QFLI_ANDROID_TARGET', 'QFLI_OHOS_TARGET', 'GOROOT', 'GOTOOLCHAIN', 'GOCACHE', 'GOWORK', 'GOENV', 'GOPROXY', 'GOSUMDB', 'GO_TELEMETRY_CHILD')) {
  $savedEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}

Push-Location $module
try {
  if ($buildAndroid) { $env:ANDROID_NDK_HOME = (Resolve-Path -LiteralPath $AndroidNdk).Path }
  if ($buildOhos) { $env:OHOS_SDK_HOME = (Resolve-Path -LiteralPath $OhosSdk).Path }
  $env:CGO_ENABLED = '1'
  $env:GOTOOLCHAIN = 'local'
  $env:GOWORK = 'off'
  $env:GOENV = 'off'
  $env:GOPROXY = 'off'
  $env:GOSUMDB = 'off'
  $env:GO_TELEMETRY_CHILD = '2'
  if ($buildAndroid) {
    $env:GOOS = 'android'
    $env:CC = Join-Path $module 'android-cc.cmd'
    foreach ($target in @(
      @{ Abi = 'arm64-v8a'; Arch = 'arm64'; Compiler = 'aarch64-linux-android21' },
      @{ Abi = 'armeabi-v7a'; Arch = 'arm'; Compiler = 'armv7a-linux-androideabi21' },
      @{ Abi = 'x86_64'; Arch = 'amd64'; Compiler = 'x86_64-linux-android21' }
    )) {
      Assert-RuntimeSourceUnchanged
      $androidOutput = Join-Path $root "android/app/src/main/jniLibs/$($target.Abi)/libqfli_go_runtime.so"
      New-Item -ItemType Directory -Force -Path (Split-Path $androidOutput) | Out-Null
      $env:GOARCH = $target.Arch
      $env:GOARM = '7'
      $env:QFLI_ANDROID_TARGET = $target.Compiler
      & $GoExecutable build -mod=vendor -buildmode=c-shared '-ldflags=-extldflags=-Wl,-z,max-page-size=16384' -o $androidOutput .
      if ($LASTEXITCODE -ne 0) { throw "Android Go runtime build failed ($($target.Abi))." }
      & (Join-Path $env:ANDROID_NDK_HOME 'toolchains/llvm/prebuilt/windows-x86_64/bin/llvm-strip.exe') --strip-unneeded $androidOutput
      if ($LASTEXITCODE -ne 0) { throw "Android Go runtime strip failed ($($target.Abi))." }
      Assert-RuntimeSourceUnchanged
      $builtLibraries += [ordered]@{
        platform = 'android'; abi = $target.Abi
        path = $androidOutput.Substring($root.Length + 1).Replace('\', '/')
        sha256 = (Get-FileHash -LiteralPath $androidOutput -Algorithm SHA256).Hash.ToLowerInvariant()
        bytes = (Get-Item -LiteralPath $androidOutput).Length
      }
    }
  }

  if ($buildOhos) {
    $env:GOROOT = $null
    $env:GOTOOLCHAIN = 'local'
    $env:GOCACHE = Join-Path $root 'native/build/ohos-go-cache'
    $targets = & $OhosGoExecutable tool dist list
    if ($LASTEXITCODE -ne 0 -or $targets -notcontains 'openharmony/amd64' -or $targets -notcontains 'openharmony/arm64') {
      throw 'OpenHarmony requires an OHOS Go toolchain with dynamic TLS. Build one with tool/build_ohos_go_toolchain.ps1 and pass -OhosGoExecutable.'
    }
    $env:GOOS = 'openharmony'
    $env:CC = Join-Path $module 'ohos-cc.cmd'
    foreach ($target in @(
      @{ Abi = 'arm64-v8a'; Arch = 'arm64'; Compiler = 'aarch64-linux-ohos' },
      @{ Abi = 'x86_64'; Arch = 'amd64'; Compiler = 'x86_64-linux-ohos' }
    )) {
      Assert-RuntimeSourceUnchanged
      $ohosOutput = Join-Path $root "ohos/entry/libs/$($target.Abi)/libqfli_go_runtime.so"
      New-Item -ItemType Directory -Force -Path (Split-Path $ohosOutput) | Out-Null
      $env:GOARCH = $target.Arch
      $env:QFLI_OHOS_TARGET = $target.Compiler
      & $OhosGoExecutable build -mod=vendor -buildmode=c-shared -o $ohosOutput .
      if ($LASTEXITCODE -ne 0) { throw "OpenHarmony Go runtime build failed ($($target.Abi))." }
      & (Join-Path $env:OHOS_SDK_HOME 'native/llvm/bin/llvm-strip.exe') --strip-unneeded $ohosOutput
      if ($LASTEXITCODE -ne 0) { throw "OpenHarmony Go runtime strip failed ($($target.Abi))." }
      Assert-RuntimeSourceUnchanged
      $builtLibraries += [ordered]@{
        platform = 'openharmony'; abi = $target.Abi
        path = $ohosOutput.Substring($root.Length + 1).Replace('\', '/')
        sha256 = (Get-FileHash -LiteralPath $ohosOutput -Algorithm SHA256).Hash.ToLowerInvariant()
        bytes = (Get-Item -LiteralPath $ohosOutput).Length
      }
    }
  }
  Assert-RuntimeSourceUnchanged
  $manifestName = if ($Platform -eq 'all') { 'bundled-go-runtime-build.json' } else { "bundled-go-runtime-build-$Platform.json" }
  $provenancePath = Join-Path $root "native/build/$manifestName"
  New-Item -ItemType Directory -Force -Path (Split-Path $provenancePath) | Out-Null
  [ordered]@{
    schemaVersion = 1
    startedUtc = $buildStarted
    finishedUtc = [DateTime]::UtcNow.ToString('o')
    nativeSourceSha256 = $sourceHash
    buildInputs = $buildInputs
    toolchains = $toolchains
    offline = [ordered]@{ GOTOOLCHAIN = 'local'; GOWORK = 'off'; GOENV = 'off'; GOPROXY = 'off'; GOSUMDB = 'off'; GO_TELEMETRY_CHILD = '2' }
    libraries = $builtLibraries
    deviceExecution = $false
  } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $provenancePath -Encoding utf8
  Write-Output "Bundled runtime provenance: $provenancePath"
} finally {
  Pop-Location
  foreach ($name in $savedEnvironment.Keys) {
    [Environment]::SetEnvironmentVariable($name, $savedEnvironment[$name], 'Process')
  }
}
