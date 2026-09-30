@echo off
if not defined QFLI_ANDROID_TARGET set QFLI_ANDROID_TARGET=aarch64-linux-android21
"%ANDROID_NDK_HOME%\toolchains\llvm\prebuilt\windows-x86_64\bin\%QFLI_ANDROID_TARGET%-clang.cmd" %*
