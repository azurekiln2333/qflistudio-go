# QFLIGoShift

[简体中文](README.md) | [繁體中文](README.zh-TW.md) | [English](README.en.md)

QFLIGoShift 是以 Flutter 開發的 Go 學習與編輯應用程式。
本倉庫透過本機路徑依賴共用核心 `qfli_studio_core`。

## 基本功能

- 編輯器提供語法醒目提示與檔案導覽。
- 教程與範例支援複製程式碼及匯入專案。
- 桌面端透過官方 Go SDK 執行程式。
- 桌面端支援建置、測試、格式化與模組指令。
- 行動端透過內建 Yaegi 解譯器執行程式。
- 內建終端機依平台選擇執行後端。
- 行動端終端機只支援 `go run` 形式的指令。

## 開發中的功能

以下功能來自尚未發佈的開發變更。
這些變更可能存在問題。

- 語法診斷與編輯器波浪線。
- 格式化、匯入、符號與本機模組工具。
- JSON 轉 Go 結構工具。
- 中斷點、逐步執行、呼叫堆疊與變數檢視。
- 具名工作區與多根專案還原。

這些功能尚未通過目前版本的完整驗證。
原始碼存在不代表安裝套件已包含該能力。

## 平台與執行後端

下表區分後端設計與歷史檢查。
歷史結果只適用於當時的原始碼與安裝套件。

| 平台 | 執行後端 | 前置條件 | 歷史檢查與限制 |
| --- | --- | --- | --- |
| Android | Yaegi，經 C ABI 與 Flutter FFI | 對應 ABI 的原生程式庫 | x86_64 曾通過，ARM 裝置未驗證 |
| OpenHarmony | Yaegi，經 C ABI 與 Flutter FFI | OHOS Go 移植版建置的原生程式庫 | x86_64 有歷史證據，arm64 未驗證 |
| iOS | Yaegi，經靜態程式庫與行程符號 | Mac、Xcode、Go SDK | 尚未完成 Apple 建置與裝置驗證 |
| Windows | 官方 Go SDK | 應用程式能在 `PATH` 找到 `go` | 工具鏈有歷史證據，介面尚未打包驗證 |
| Linux | 官方 Go SDK | 應用程式能在 `PATH` 找到 `go` | 後端有歷史證據，Flutter 介面未驗證 |
| macOS | 官方 Go SDK | 應用程式能在 `PATH` 找到 `go` | 尚未在 macOS 主機驗證 |
| Web／其他平台 | 無法使用 | 無 | 不提供原生 Go 執行 |

`lib/go_platform.dart` 定義平台對應。
行動端回報 `embedded-go-runtime`。
桌面端回報 `official-go-sdk`。

## 離線邊界

獨立版的應用程式功能以離線使用為目標。
內建課程不要求下載 Go 相依套件。
行動端解譯器不等於完整 Go SDK。
行動端不提供官方 SDK 的建置與模組下載指令。
本應用程式不提供通用網路沙箱。
自訂 Go 程式可能存取網路或主機檔案。
開發時取得 Flutter 相依套件可能需要連線。
離線開發前須備齊相依套件與工具鏈。

## 開發前置條件

- Flutter SDK 必須符合 Dart `>=3.11.5 <4.0.0`。
- 桌面執行需要本機安裝 Go SDK。
- 本專案需要同層的共用核心倉庫。
- OpenHarmony 建置需要 OHOS 版 Flutter SDK。

共用編輯器來自 `../qfli_studio_core/vendor/re_editor`。
目錄結構如下：

```text
checkout-parent/
  qfli_studio_core/
  qfli_go/
```

## 開發指令

請在 `qfli_go` 目錄操作。
下列指令是開發步驟，不是本次檢查結果。

取得相依套件：

```powershell
flutter pub get
```

執行應用程式：

```powershell
flutter run
```

檢查 Dart 原始碼：

```powershell
flutter analyze --no-pub
```

請將 SDK 路徑換成本機路徑。
執行測試：

```powershell
$env:QFLI_GO_TEST_EXECUTABLE = "C:\path\to\go.exe"
flutter test --no-pub --concurrency 1
```

課程工具使用 `tool/go_curriculum/` 的原始檔。
主機檢查不能取代裝置檢查。

```powershell
python tool/go_curriculum/assemble.py
python tool/go_curriculum/verify.py --go "C:\path\to\go.exe"
python tool/go_curriculum/dedup.py
```

## 原生程式庫與安裝套件

Android 建置需要 Android NDK。
OpenHarmony 建置需要 OHOS SDK。
OpenHarmony 使用固定的 OHOS Go 移植版。
版本與原始碼說明見[原生執行說明](native/go_runtime/README.md)。

先建置 OHOS Go 主機工具鏈：

```powershell
./tool/build_ohos_go_toolchain.ps1 -BootstrapGoExecutable "C:\path\to\go.exe"
```

請使用指令碼輸出的 OHOS Go 路徑。
建置五個 Android／OpenHarmony 原生程式庫：

```powershell
./tool/build_go_runtime.ps1 `
  -GoExecutable "C:\path\to\go.exe" `
  -OhosGoExecutable "C:\path\to\ohos-go.exe" `
  -AndroidNdk "C:\path\to\ndk" `
  -OhosSdk "C:\path\to\ohos-sdk"
```

指令碼涵蓋三個 Android ABI 與兩個 OpenHarmony ABI。
iOS 的 Xcode 建置階段呼叫 `tool/build_ios_go_runtime.sh`。
修改原生原始碼後須重建對應安裝套件的原生程式庫。
舊程式庫不會自動取得原始碼修復。

使用 OHOS 版 Flutter 建置偵錯套件：

```powershell
flutter build hap --debug --no-pub
```

安裝套件建置不能證明裝置上的執行結果。

## 課程與驗證狀態

- 現有課程包含 120 個 Go 主題。
- 每個主題對應一篇教程與一個範例。
- 共用核心提供目前的課程介面。
- 開發工作區另有 160 個草稿主題。
- 草稿尚未進入正式課程。
- 主機檢查已有歷史結果。
- 原始範例的 OHOS 全量檢查仍未完成。
- 目前的原生變更尚未通過完整檢查。
- 目前的介面變更尚未驗證。

本倉庫不宣稱目前版本已通過 OHOS 全量驗證。
裝置證據必須對應實際原始碼與安裝套件。

## 延伸文件

- [原生執行、建置與平台證據](native/go_runtime/README.md)
- [課程工具](tool/go_curriculum/README.md)
- [學習路線](tool/go_curriculum/GUIDE.md)
- [課程內容格式](tool/go_curriculum/schema.md)
- [主機探測說明](tool/go_curriculum/mobile_check/README.md)

## 第三方聲明

- [Go 標準程式庫聲明](assets/licenses/go.txt)
- [Yaegi 聲明](assets/licenses/yaegi.txt)
