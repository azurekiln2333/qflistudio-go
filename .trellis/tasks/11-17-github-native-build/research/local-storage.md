# 本地原生构建目录复核

复核日期为 2026 年 11 月 17 日。
`native/build` 的文件总量为 2.0848 GiB。
统计不含文件系统额外占用。

| 一级目录 | GiB | 内容 |
| --- | ---: | --- |
| `go-cache-windows` | 0.6365 | Windows Go 构建缓存 |
| `ohos-go-cache` | 0.3215 | OHOS 构建缓存 |
| `ohos-go-f2cb443…` | 0.2680 | OHOS 工具链源码和生成工具 |
| `go-sdk-1.27.1` | 0.2300 | Windows Go SDK |
| `go-linux-1.27.1` | 0.2272 | Linux Go SDK |
| `go-cache-linux` | 0.1654 | Linux Go 构建缓存 |
| `cmake-probe` | 0.0744 | CMake 探测构建和安装输出 |
| `desktop` | 0.0371 | Windows 原生库产物 |
| `host` | 0.0371 | 主机原生库、头文件和编译脚本 |
| `verify-ohos` | 0.0197 | OHOS 库验证副本 |

Linux SDK 下载包另占 0.0657 GiB。
三个构建缓存目录合计 1.1234 GiB。
停止本地构建后，可以清理这些缓存。
下次本地构建会重新生成缓存。

Windows Go SDK 供本地审计脚本使用。
Linux Go SDK 供 WSL 和 race 脚本使用。
清理 SDK 后，本地验证需要重新下载。
清理 OHOS 工具链后，本地构建需要重新编译。

Android 打包库位于 `android/app/src/main/jniLibs/`。
OHOS 打包库位于 `ohos/entry/libs/`。
这些打包库不在上述缓存目录中。

本次未删除原有缓存、SDK 或证据。
本次仅清理已校验的临时下载副本。
