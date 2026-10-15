# Go 学习路线与运行指南（120 课）

本目录包含完整的 Go 课程：**120 篇教程 + 120 个可运行示例**，从零基础到
工程实践。本文件是学习者入口：路线、章节索引、如何运行、常见错误、平台限制。

> 稳定的 120 条 ID（`go-tutorial-NNN` / `go-example-NNN`）是课程契约；新增内容
> 只追加、不重编号。教程原文见 `content/go/{tutorials,examples}.json`，
> 可运行源码见 `samples/T<NNN>/`。

## 1. 学习路线（按阶段递进）

| 阶段 | 主题范围 | 学完能做什么 |
| --- | --- | --- |
| S1 从零起步与开发环境 | T001–T010 | 安装/运行工具链，写第一个程序，掌握变量、类型、字符串、格式化、输入、运算符 |
| S2 基础与流程控制 | T011–T022 | 用 if/switch/for 组织逻辑，熟练切片、数组、映射 |
| S3 集合、函数、指针 | T023–T036 | 多返回值、闭包、递归、指针语义、排序查找、字符串处理 |
| S4 结构体、方法与接口 | T037–T048 | 结构体/嵌入、值/指针接收者、接口与类型断言、组合优于继承 |
| S5 错误处理、defer、panic | T049–T058 | 错误即值、%w 包装链、errors.Is/As、defer/recover 边界 |
| S6 包、模块与泛型 | T059–T070 | 包与初始化、go.mod 与 MVS、泛型函数/类型、构建标签、go:generate |
| S7 并发与同步、context | T071–T084 | goroutine/channel/select、Mutex/RWMutex/atomic/Pool、context 取消与超时、worker pool |
| S8 标准库：IO/JSON/时间/正则 | T085–T098 | io 抽象、文件与 bufio、JSON 编解码、时间、正则、模板、strconv、哈希 |
| S9 网络与 HTTP | T099–T104 | http 客户端/服务端、JSON API、中间件、超时与优雅关闭（httptest 离线） |
| S10 测试、基准与 fuzz | T105–T111 | 表驱动、t.Helper、夹具、benchmark、覆盖率、fuzz、打桩 |
| S11 性能与工程实践 | T112–T117 | 逃逸分析、pprof、预分配优化、vet/gofmt、slog、配置 |
| S12 综合项目 | T118–T120 | CLI+JSON 持久化、并发词频、极简 HTTP 服务 |

**建议路径**：初学者按 S1→S2→S3→S4 顺序；有编程经验可直接从 S4/S5 起，
遇到不熟的概念回查前置 ID（每篇 `prerequisites` 标注了前置课）。

## 2. 章节索引（按 S 阶段）

- **S1**：T001 工具链概览 · T002 第一个程序 · T003 变量与零值 · T004 基础类型 ·
  T005 常量/iota · T006 类型转换 · T007 字符串/rune/字节 · T008 fmt 谓词 ·
  T009 bufio 输入 · T010 运算符与位运算
- **S2**：T011 if/else · T012 switch · T013 类型 switch · T014 for · T015 range ·
  T016 label · T017 goto · T018 数组 · T019 切片一 · T020 切片二 · T021 切片三 ·
  T022 映射
- **S3**：T023 多返回值 · T024 变参 · T025 高阶函数 · T026 闭包 · T027 递归/记忆化 ·
  T028 defer · T029 指针一 · T030 指针二 · T031 new/取址 · T032 sort.Slice ·
  T033 sort.Search · T034 映射进阶 · T035 strings · T036 strings.Builder
- **S4**：T037 结构体 · T038 嵌入 · T039 接收者 · T040 方法值/表达式 · T041 接口 ·
  T042 类型断言 · T043 any/类型 switch · T044 接口组合 · T045 Stringer/error ·
  T046 sort.Interface · T047 组合/策略/装饰 · T048 接口 nil 陷阱
- **S5**：T049 error 即值 · T050 哨兵错误 · T051 %w 链 · T052 Is vs As ·
  T053 自定义错误 · T054 panic/recover · T055 defer 清理 · T056 上下文补充 ·
  T057 日志边界 · T058 并发错误收集
- **S6**：T059 包/init · T060 go.mod · T061 internal · T062–T065 泛型 ·
  T066 依赖注入 · T067 函数选项 · T068 MVS · T069 构建标签 · T070 go:generate
- **S7**：T071 goroutine · T072–T074 channel · T075 select · T076 单向 channel ·
  T077 Mutex · T078 RWMutex · T079 WaitGroup/Once · T080 Pool · T081 atomic ·
  T082–T083 context · T084 worker pool
- **S8**：T085 io 抽象 · T086 文件 · T087 bufio · T088 目录 · T089–T091 JSON ·
  T092–T093 时间 · T094–T095 正则 · T096 模板 · T097 strconv · T098 SHA-256
- **S9**：T099 客户端 · T100 服务端 · T101 方法/头/状态码 · T102 JSON API ·
  T103 中间件 · T104 超时/优雅关闭
- **S10**：T105 表驱动 · T106 helper · T107 夹具 · T108 benchmark ·
  T109 覆盖率 · T110 fuzz · T111 打桩
- **S11**：T112 逃逸 · T113 pprof · T114 预分配优化 · T115 vet/gofmt ·
  T116 slog · T117 配置
- **S12**：T118 CLI+JSON · T119 并发词频 · T120 HTTP 服务

## 3. 如何运行示例

源码在 `samples/T<NNN>/`。三种交付形态，运行方式不同：

### 3.1 单文件示例（`single-file`，可直接导入）

一个目录一个 `main.go`（部分带 `go.mod`）。运行：

```powershell
cd samples/T066
go run main.go        # 无 go.mod 时
# 或
go run .              # 有 go.mod 时
```

### 3.2 测试/基准示例（`test-package`）

含 `*_test.go` 与 `go.mod`，用官方 Go 工具链运行：

```powershell
cd samples/T105
go test ./...                       # 运行测试
go test -run TestAdd ./...          # 只跑某个测试
cd ../T108
go test -bench . -benchmem -run '^$' ./...   # benchmark
cd ../T110
go test -fuzz FuzzParsePort -fuzztime 10s ./...   # fuzz（限时！）
```

### 3.3 多文件/模块工程（`module-project`）

含 `go.mod` 与多个源文件，按教程给出的命令运行：

```powershell
cd samples/T069
go run .                    # 默认构建
go run -tags special .      # 带构建标签
cd ../T070
go generate ./...           # 运行 //go:generate（生成 day_string.go）
go run .
```

**统一验证命令**（在 `tool/go_curriculum/` 下）：

```powershell
$go = "native/build/go-sdk-1.27.1/go/bin/go.exe"   # 固定 SDK
python tool/go_curriculum/assemble.py     # 生成 content/go/*
python tool/go_curriculum/verify.py       # 编译并运行全部样例
python tool/go_curriculum/dedup.py        # 重复度检查
python tool/go_curriculum/patch.py emit   # 生成可评审补丁
python tool/go_curriculum/patch.py dry-run
```

## 4. 常见错误诊断

| 症状 | 原因 | 处理 |
| --- | --- | --- |
| `constant 128 overflows int8` | 无类型常量超出目标类型范围 | 用更宽类型或修正字面量 |
| `cannot use x (int) as float64` | Go 无隐式数值转换 | 显式 `float64(x)` |
| `x declared and not used` | 局部变量声明未使用 | 使用或删除（`_` 丢弃） |
| `impossible type assertion` | 断言到接口不可能实现的类型 | 检查方法集或改用 any |
| `send on closed channel` | 向已关闭 channel 发送 | 发送方负责 close，收尾后再关 |
| `all goroutines are asleep - deadlock` | 无缓冲 channel 先发后收 | 用 goroutine 并发收发，或加缓冲 |
| `fatal error: concurrent map writes` | 多 goroutine 写同一 map | 加 Mutex 或各自统计后合并 |
| `token too long` | bufio.Scanner 默认 64K 上限 | `scanner.Buffer(...)` 调大 |
| `missing go.sum entry` | 依赖校验和缺失 | `go mod tidy`（离线用本地 replace） |
| `.*output is required` (校验器) | lesson.output 为空 | 每篇 output 必须非空 |

## 5. 桌面/移动平台限制

课程默认在**桌面官方 Go 工具链**（`native/build/go-sdk-1.27.1`）验证。移动端
（Android/OHOS/iOS）使用项目内置 Yaegi 解释器，能力受限。**全部 120 课当前
标记为 `desktop`**（未做设备实测，不做移动端承诺）。

已知移动端 Yaegi 限制（以 `research/mobile-validation.md` 为准）：

- 泛型（T062–T065）、`go test`/bench/fuzz/race、多文件/模块、`go:generate`：
  移动端不支持或未实测，保持 desktop。
- 方法表达式（T040）、接口赋值（T047）、`errors.As`（T052/T053）：移动端会
  panic。
- `text/template`（T096）、`log/slog`（T116）：移动端 stdout 为空（示例已改为
  渲染到缓冲再打印，官方 Go 可运行）。
- `%T` 具名类型输出（T008）、目录 size（T088）、context 时序（T083）：跨平台
  表现不同，示例已改为确定性写法。

**切勿**仅凭"同版本 Yaegi"就把任一课标为 mobile-safe；移动端结论必须来自本
项目 native runtime 的设备实测。
