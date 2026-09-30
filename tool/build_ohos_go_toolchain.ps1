param([string]$BootstrapGoExecutable = 'go')

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$revision = 'f2cb44316b789bc12d0b5fd562d853f6fec3ab28'
$source = Join-Path $root "native/build/ohos-go-$revision"
$go = Join-Path $source 'bin/go.exe'

if (-not (Test-Path -LiteralPath $source)) {
  New-Item -ItemType Directory -Force -Path (Split-Path $source) | Out-Null
  git -c http.sslBackend=openssl clone --depth 1 --branch v1.27.1-ohos https://github.com/sysit/ohos-go.git $source
  if ($LASTEXITCODE -ne 0) { throw 'OpenHarmony Go source download failed.' }
}
$actualRevision = git -C $source rev-parse HEAD
if ($LASTEXITCODE -ne 0 -or $actualRevision -ne $revision) {
  throw "OpenHarmony Go source must be at $revision."
}

if (-not (Test-Path -LiteralPath $go)) {
  $bootstrap = & $BootstrapGoExecutable env GOROOT
  if ($LASTEXITCODE -ne 0) { throw 'A working official Go bootstrap SDK is required.' }
  $savedEnvironment = @{}
  foreach ($name in @('GOROOT_BOOTSTRAP', 'GOOS', 'GOARCH', 'CGO_ENABLED', 'GOTOOLCHAIN', 'GOCACHE')) {
    $savedEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
  }
  Push-Location (Join-Path $source 'src')
  try {
    $env:GOROOT_BOOTSTRAP = $bootstrap
    $env:GOOS = 'windows'
    $env:GOARCH = 'amd64'
    $env:CGO_ENABLED = '0'
    $env:GOTOOLCHAIN = 'local'
    $env:GOCACHE = Join-Path $root 'native/build/ohos-go-cache'
    & ./make.bat
    if ($LASTEXITCODE -ne 0) { throw 'OpenHarmony Go host toolchain build failed.' }
  } finally {
    Pop-Location
    foreach ($name in $savedEnvironment.Keys) {
      [Environment]::SetEnvironmentVariable($name, $savedEnvironment[$name], 'Process')
    }
  }
}
$targets = & $go tool dist list
if ($LASTEXITCODE -ne 0 -or $targets -notcontains 'openharmony/amd64' -or $targets -notcontains 'openharmony/arm64') {
  throw 'OpenHarmony Go toolchain is incomplete.'
}
$go
