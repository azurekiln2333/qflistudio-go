@echo off
if not defined QFLI_OHOS_TARGET set QFLI_OHOS_TARGET=aarch64-linux-ohos
"%OHOS_SDK_HOME%\native\llvm\bin\clang.exe" --target=%QFLI_OHOS_TARGET% --sysroot="%OHOS_SDK_HOME%\native\sysroot" -D__MUSL__ %*
