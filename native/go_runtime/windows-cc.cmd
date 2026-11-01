@echo off
setlocal EnableExtensions DisableDelayedExpansion
rem Optional clang + existing MinGW sysroot adapter. All paths are supplied by
rem the build script; no toolchain is downloaded and no machine PATH is changed.
rem Clang 15 requests the absent libgcc_eh for C executable links. Object-only
rem links use its C++ driver runtime choice (libgcc_s), without a C++ standard
rem library. Source compilation and preprocessing keep the original C driver.
set "QFLI_GO_LINK_DRIVER="
set "QFLI_GO_OBJECT_INPUT="
set "QFLI_GO_SOURCE_OR_COMPILE="
:scan_arguments
if "%~1"=="" goto select_driver
if "%~1"=="-c" set "QFLI_GO_SOURCE_OR_COMPILE=1"
if "%~1"=="-E" set "QFLI_GO_SOURCE_OR_COMPILE=1"
if "%~1"=="-S" set "QFLI_GO_SOURCE_OR_COMPILE=1"
if "%~1"=="-fsyntax-only" set "QFLI_GO_SOURCE_OR_COMPILE=1"
if "%~1"=="-M" set "QFLI_GO_SOURCE_OR_COMPILE=1"
if "%~1"=="-MM" set "QFLI_GO_SOURCE_OR_COMPILE=1"
if /i "%~x1"==".c" set "QFLI_GO_SOURCE_OR_COMPILE=1"
if /i "%~x1"==".h" set "QFLI_GO_SOURCE_OR_COMPILE=1"
if /i "%~x1"==".s" set "QFLI_GO_SOURCE_OR_COMPILE=1"
if /i "%~x1"==".i" set "QFLI_GO_SOURCE_OR_COMPILE=1"
if /i "%~x1"==".ii" set "QFLI_GO_SOURCE_OR_COMPILE=1"
if /i "%~x1"==".cc" set "QFLI_GO_SOURCE_OR_COMPILE=1"
if /i "%~x1"==".cpp" set "QFLI_GO_SOURCE_OR_COMPILE=1"
if /i "%~x1"==".cxx" set "QFLI_GO_SOURCE_OR_COMPILE=1"
if /i "%~x1"==".c++" set "QFLI_GO_SOURCE_OR_COMPILE=1"
if /i "%~x1"==".m" set "QFLI_GO_SOURCE_OR_COMPILE=1"
if /i "%~x1"==".mm" set "QFLI_GO_SOURCE_OR_COMPILE=1"
if /i "%~x1"==".o" set "QFLI_GO_OBJECT_INPUT=1"
if /i "%~x1"==".obj" set "QFLI_GO_OBJECT_INPUT=1"
shift /1
goto scan_arguments
:select_driver
if defined QFLI_GO_SOURCE_OR_COMPILE goto invoke_clang
if defined QFLI_GO_OBJECT_INPUT set "QFLI_GO_LINK_DRIVER=--driver-mode=g++ -nostdlib++"
:invoke_clang
rem SHIFT does not alter %%*: forward the original arguments and quoting.
"%QFLI_GO_CLANG%" --target=x86_64-w64-windows-gnu --sysroot="%QFLI_GO_MINGW%/x86_64-w64-mingw32" -L"%QFLI_GO_MINGW_GCC%" -fuse-ld=lld -Qunused-arguments %QFLI_GO_LINK_DRIVER% %*
exit /b %errorlevel%
