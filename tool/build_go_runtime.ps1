param(
  [string]$GoExecutable = 'go',
  [string]$OhosGoExecutable = 'go',
  [string]$AndroidNdk = $env:ANDROID_NDK_HOME,
  [string]$OhosSdk = $env:OHOS_SDK_HOME
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$module = Join-Path $root 'native/go_runtime'

if (-not (Test-Path -LiteralPath $AndroidNdk)) {
  throw 'Android NDK path is required (-AndroidNdk).'
}
if (-not (Test-Path -LiteralPath $OhosSdk)) {
  throw 'OpenHarmony SDK path is required (-OhosSdk).'
}

$savedEnvironment = @{}
foreach ($name in @('ANDROID_NDK_HOME', 'OHOS_SDK_HOME', 'CGO_ENABLED', 'GOOS', 'GOARCH', 'GOARM', 'CC', 'QFLI_ANDROID_TARGET', 'QFLI_OHOS_TARGET', 'GOROOT', 'GOTOOLCHAIN', 'GOCACHE')) {
  $savedEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}

Push-Location $module
try {
  $env:ANDROID_NDK_HOME = (Resolve-Path -LiteralPath $AndroidNdk).Path
  $env:OHOS_SDK_HOME = (Resolve-Path -LiteralPath $OhosSdk).Path
  $env:CGO_ENABLED = '1'
  $env:GOOS = 'android'
  $env:CC = Join-Path $module 'android-cc.cmd'
  foreach ($target in @(
    @{ Abi = 'arm64-v8a'; Arch = 'arm64'; Compiler = 'aarch64-linux-android21' },
    @{ Abi = 'armeabi-v7a'; Arch = 'arm'; Compiler = 'armv7a-linux-androideabi21' },
    @{ Abi = 'x86_64'; Arch = 'amd64'; Compiler = 'x86_64-linux-android21' }
  )) {
    $androidOutput = Join-Path $root "android/app/src/main/jniLibs/$($target.Abi)/libqfli_go_runtime.so"
    New-Item -ItemType Directory -Force -Path (Split-Path $androidOutput) | Out-Null
    $env:GOARCH = $target.Arch
    $env:GOARM = '7'
    $env:QFLI_ANDROID_TARGET = $target.Compiler
    & $GoExecutable build -mod=vendor -buildmode=c-shared '-ldflags=-extldflags=-Wl,-z,max-page-size=16384' -o $androidOutput .
    if ($LASTEXITCODE -ne 0) { throw "Android Go runtime build failed ($($target.Abi))." }
    & (Join-Path $env:ANDROID_NDK_HOME 'toolchains/llvm/prebuilt/windows-x86_64/bin/llvm-strip.exe') --strip-unneeded $androidOutput
    if ($LASTEXITCODE -ne 0) { throw "Android Go runtime strip failed ($($target.Abi))." }
  }

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
    $ohosOutput = Join-Path $root "ohos/entry/libs/$($target.Abi)/libqfli_go_runtime.so"
    New-Item -ItemType Directory -Force -Path (Split-Path $ohosOutput) | Out-Null
    $env:GOARCH = $target.Arch
    $env:QFLI_OHOS_TARGET = $target.Compiler
    & $OhosGoExecutable build -mod=vendor -buildmode=c-shared -o $ohosOutput .
    if ($LASTEXITCODE -ne 0) { throw "OpenHarmony Go runtime build failed ($($target.Abi))." }
    & (Join-Path $env:OHOS_SDK_HOME 'native/llvm/bin/llvm-strip.exe') --strip-unneeded $ohosOutput
    if ($LASTEXITCODE -ne 0) { throw "OpenHarmony Go runtime strip failed ($($target.Abi))." }
  }
} finally {
  Pop-Location
  foreach ($name in $savedEnvironment.Keys) {
    [Environment]::SetEnvironmentVariable($name, $savedEnvironment[$name], 'Process')
  }
}
