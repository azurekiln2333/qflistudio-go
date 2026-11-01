param(
  [string]$GoExecutable = 'go',
  [string]$CCompiler = 'gcc',
  [string]$ClangExecutable,
  [string]$MingwRoot,
  [string]$OutputDirectory
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$module = Join-Path $root 'native/go_runtime'
if (-not $OutputDirectory) {
  $OutputDirectory = Join-Path $root 'native/build/desktop/windows/x64'
}
$output = [IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Force -Path $output | Out-Null
$savedEnvironment = @{}
$names = @('CC', 'CGO_ENABLED', 'GOOS', 'GOARCH', 'GOTOOLCHAIN', 'GOWORK', 'GOENV', 'GOPROXY', 'GOSUMDB', 'GO_TELEMETRY_CHILD', 'QFLI_GO_CLANG', 'QFLI_GO_MINGW', 'QFLI_GO_MINGW_GCC')
foreach ($name in $names) {
  $savedEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}
try {
  if ($ClangExecutable -or $MingwRoot) {
    if (-not $ClangExecutable -or -not $MingwRoot) {
      throw 'ClangExecutable and MingwRoot must be supplied together.'
    }
    $env:QFLI_GO_CLANG = (Resolve-Path -LiteralPath $ClangExecutable).Path
    $env:QFLI_GO_MINGW = (Resolve-Path -LiteralPath $MingwRoot).Path
    $gccLibraries = Join-Path $env:QFLI_GO_MINGW 'lib/gcc/x86_64-w64-mingw32'
    $versions = @(Get-ChildItem -LiteralPath $gccLibraries -Directory | Sort-Object Name -Descending)
    if ($versions.Count -eq 0) { throw 'No x64 MinGW GCC support library was found.' }
    $env:QFLI_GO_MINGW_GCC = $versions[0].FullName
    $env:CC = Join-Path $module 'windows-cc.cmd'
  } else {
    $env:CC = $CCompiler
  }
  $env:CGO_ENABLED = '1'
  $env:GOOS = 'windows'
  $env:GOARCH = 'amd64'
  $env:GOTOOLCHAIN = 'local'
  $env:GOWORK = 'off'
  $env:GOENV = 'off'
  $env:GOPROXY = 'off'
  $env:GOSUMDB = 'off'
  $env:GO_TELEMETRY_CHILD = '2'
  & $GoExecutable -C $module build -mod=vendor -buildmode=c-shared -o (Join-Path $output 'qfli_go_runtime.dll') .
  if ($LASTEXITCODE -ne 0) { throw 'Desktop Go runtime build failed.' }
  Get-Item -LiteralPath (Join-Path $output 'qfli_go_runtime.dll') | Select-Object FullName, Length
} finally {
  foreach ($name in $names) {
    [Environment]::SetEnvironmentVariable($name, $savedEnvironment[$name], 'Process')
  }
}
