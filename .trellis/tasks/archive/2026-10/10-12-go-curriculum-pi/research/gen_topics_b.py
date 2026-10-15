#!/usr/bin/env python3
"""Generate topic JSON for T061..T120 (w8:p3 owned slice).

Each topic file follows tool/go_curriculum/schema.md exactly:
  {id, runtime, importKind, runCommand, verification, sampleFiles, tutorial, example}

`code` is always exactly one syntactically valid Go file. For test/module topics
it is the single most representative file; the companion files and commands are
described in `explain`/`pitfalls`.
"""
import json
import os

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
ROOT = os.path.join(REPO, "tool", "go_curriculum")
TOPICS = os.path.join(ROOT, "topics")
SAMPLES = os.path.join(ROOT, "samples")

UPDATED = "2026-10-12"

try:
    from data_b_outputs import TEST_OUTPUT
except Exception:
    TEST_OUTPUT = {}
SRC = "https://go.dev/doc/"
LICENSE = "Original QFLI curriculum; reference link retained. CC BY 4.0"

# codeFile = representative single file whose bytes become tutorial.code/example.code
# files = every file under samples/<id>/ needed to run (listed in sampleFiles)
# kind = single-file | test-package | module-project
# runtime = desktop | mobile
# vkind/vexp = verification kind + expected
# run = runCommand
# title/level/summary/concepts/objective/prereq/pitfalls/exercises/explain

T = {}

def add(tid, **kw):
    T[tid] = kw

# ---------------- S6 packages/modules/generics ----------------

add("T061", title="内部包 internal 与可见性", level="intermediate",
    kind="module-project", runtime="desktop",
    files=["main.go"], codeFile="main.go",
    vkind="stdout-exact",
    expected="exported constant: visible outside package\nunexported constant: visible only inside package\ninternal rule: a package under an internal/ directory may only\nbe imported by code in the directory tree rooted at internal's parent.",
    run="go run .",
    concepts=["internal", "可见性", "导出规则"],
    summary="用 internal 目录限制包只能在模块内被导入，并区分导出与非导出标识符。",
    objective="能说明导出（大写）与非导出（小写）标识符的可见范围，并能用 internal/ 目录把包限制在模块内。",
    prereq=["T059 包、导出规则与初始化顺序"],
    pitfalls=["把 internal 当成安全边界：它只是编译期导入限制，不是运行时沙箱。",
              "以为 internal 里的标识符仍然导出：internal 限制的是“包能否被导入”，包内小写标识符照样不导出。"],
    exercises=[{"prompt": "把本示例的 main 拆成 cmd/ 与 internal/secret/ 两个目录，使 cmd 能导入 internal/secret，并在模块外新建另一个 module 尝试导入它，观察编译错误。",
                "hint": "内部包只能被以 internal 父目录为根的目录树内的代码导入。",
                "answer": "cmd/main.go 导入 demo/internal/secret 成功；另一个 module 导入 demo/internal/secret 时报 'use of internal package not allowed'。"}],
    explain="""Go 的可见性由标识符首字母决定：大写导出、小写不导出，这比很多语言的 public/private 关键字更简单，但粒度是“包”级。internal 规则再进一步：任何路径中含有 internal 的目录，其包只能被以该 internal 目录父目录为根的树内代码导入。于是 internal/ 成为“模块私有”的约定手段——外部模块即使知道 import 路径，编译器也会拒绝。需要强调的是，它是编译期约束，不是运行时安全边界；能拿到源码或二进制的人仍可读代码。示例本身在单文件内演示导出/非导出差异，并在注释中给出完整的 cmd/ 与 internal/secret/ 目录结构；因为真实的 internal 规则需要子目录，故标记为 module-project。""",
    )

add("T062", title="泛型一：类型参数与约束", level="advanced",
    kind="module-project", runtime="desktop",
    files=["main.go"], codeFile="main.go",
    vkind="stdout-exact",
    expected="Min[int](3, 7) = 3\nMax[int](3, 7) = 7\nMin[string](\"pear\", \"apple\") = apple\nMax[float64](2.5, 1.5) = 2.5",
    run="go run .",
    concepts=["泛型", "类型参数", "约束", "cmp.Ordered"],
    summary="用类型参数与 cmp.Ordered 约束编写一份可服务多种类型的 Min/Max。",
    objective="能声明带类型参数的函数并为其指定约束，说明泛型在编译期如何实例化。",
    prereq=["T023 函数签名、多返回值与命名返回", "T041 接口基础与鸭子类型"],
    pitfalls=["把任何类型都塞进 any：失去 < 比较能力，编译失败；应使用 cmp.Ordered 之类的约束。",
              "以为泛型有运行期类型信息：Go 泛型在编译期为每个实例化类型生成代码，运行期没有“泛型擦除”这回事。",
              "忘记泛型需要 Go 1.18+，且本项目移动端 Yaegi 未实测支持——本主题标记为 desktop only。"],
    exercises=[{"prompt": "为 Min 增加第三个参数（三值取最小），并为 []int 实现一个泛型 SliceMin。",
                "hint": "同一约束函数体里可以反复使用 < 比较。",
                "answer": "func Min3[T cmp.Ordered](a, b, c T) T { return Min(a, Min(b, c)) }；SliceMin 循环取小。"}],
    explain="""没有泛型时，同一算法要为每种类型复制一份，或在 interface{} 上做断言而丢失类型安全。类型参数 [T cmp.Ordered] 表示 T 可以是任何满足 cmp.Ordered 的类型；cmp.Ordered 是一个预声明的约束，涵盖所有可用 <、> 比较的内置类型与字符串。函数体里因此可以直接写 a < b。编译器在调用点用实际类型实例化：Min(3,7) 实例化为 int 版本，Min("pear","apple") 实例化为 string 版本，各自是独立的静态代码，因而没有装箱与断言开销。泛型属于 Go 的静态编译特性，本项目移动端的 Yaegi 解释器未实测支持，故标记 desktop only，不得声称移动端可运行。""",
    )

add("T063", title="泛型二：自定义约束与联合类型", level="advanced",
    kind="module-project", runtime="desktop",
    files=["main.go"], codeFile="main.go",
    vkind="stdout-exact",
    expected="Sum([]int{1,2,3}) = 6\nSum([]int64{10,20,30}) = 60\nSum([]float64{1.5,2.5}) = 4\nSum([]Celsius{...}) = 61",
    run="go run .",
    concepts=["自定义约束", "联合类型", "~ 底层类型", "泛型"],
    summary="自定义 interface 约束并用 ~ 与 | 表达“底层为这些类型的任意类型”。",
    objective="能定义形如 `~int | ~float64` 的联合约束，并用它让泛型函数接受命名类型。",
    prereq=["T062 泛型一：类型参数与约束", "T006 类型转换与数值精度"],
    pitfalls=["写出 `int | float64` 而漏掉 `~`：这样只能匹配原名类型，自定义的 Celsius 不满足约束。",
              "在联合约束上做超出允许范围的运算，例如想对 ~string 求和；+ 对字符串是拼接，语义会出乎意料。"],
    exercises=[{"prompt": "定义约束 Integer 仅允许底层为整数类型，并实现泛型 Average 返回 float64 平均值。",
                "hint": "求和后用 float64(total) / float64(len(xs))。",
                "answer": "type Integer interface{ ~int | ~int64 }；Average 内部先 Sum 再转 float64 相除。"}],
    explain="""自定义约束本质是一个只含类型集合的 interface。`~int` 里的波浪号表示“底层类型为 int 的任意命名类型”，因此 `type Celsius float64` 也满足 `~float64`。`|` 是集合并，把多个候选类型合并成一个约束。这样 Sum 就能同时服务 int、int64、float64 以及它们的命名类型，而仍然保有编译期检查——传入一个 []bool 会直接编译失败。与 T062 用现成约束不同，本例重点在“如何自己写约束”，这也是设计可复用泛型库的关键。desktop only，理由同 T062。""",
    )

add("T064", title="泛型三：泛型类型（容器）", level="advanced",
    kind="module-project", runtime="desktop",
    files=["main.go"], codeFile="main.go",
    vkind="stdout-exact",
    expected="popped int: 3\npopped int: 2\npopped int: 1\npop empty stack ok = false\npopped string: generics",
    run="go run .",
    concepts=["泛型类型", "容器", "方法", "LIFO"],
    summary="用类型参数定义泛型 Stack[T]，实现压栈、弹栈与长度，支持任意元素类型。",
    objective="能定义带类型参数的类型并为它编写方法，理解泛型类型如何实例化。",
    prereq=["T062 泛型一：类型参数与约束", "T039 方法：值接收者与指针接收者"],
    pitfalls=["在泛型类型方法上误用值接收者：Push 需要修改切片，必须用指针接收者 *Stack[T]。",
              "Pop 空栈返回的零值容易被忽略：必须用逗号-ok 形式区分“零值”与“空栈”。"],
    exercises=[{"prompt": "为 Stack 增加 Peek（只看栈顶不出栈）和 PushAll（批量压栈）两个方法。",
                "hint": "Peek 与 Pop 类似但不改 items；PushAll 可先 append slice 再展开。",
                "answer": "Peek 返回最后一个元素与 ok；PushAll 用 s.items = append(s.items, vs...)。"}],
    explain="""泛型不仅用于函数，也能定义类型：Stack[T] 中的 T 是元素类型，字段 items 的类型因此写成 []T。方法接收者写 *Stack[T]，让方法体里的 T 与方法绑定的类型参数一致。用 Stack[int] 与 Stack[string] 分别实例化，得到两份独立、类型安全的实现——不会有 interface{} 断言，也不会混入错误类型。本例还演示 Pop 用逗号-ok 报告空栈。泛型类型同样是编译期特性，desktop only。""",
    )

add("T065", title="泛型与接口的选型对比", level="advanced",
    kind="module-project", runtime="desktop",
    files=["main.go"], codeFile="main.go",
    vkind="stdout-exact",
    expected="generic Sum[int] = 10\ngeneric Sum[float64] = 4\ninterface sum = 7",
    run="go run .",
    concepts=["泛型", "接口", "多态", "选型"],
    summary="同一“求和”题用泛型与接口两种方式实现，比较类型安全、性能与扩展性的取舍。",
    objective="能根据“是否需要跨类型复用运算”与“是否需要运行期异构”选择泛型还是接口。",
    prereq=["T063 泛型二：自定义约束与联合类型", "T041 接口基础与鸭子类型"],
    pitfalls=["用 interface{} 求和再断言：运行期才暴露错误，且每次断言有开销。",
              "以为泛型能替代所有接口：需要运行期多态（异构集合、插件式扩展）时仍应用接口。"],
    exercises=[{"prompt": "为两种方案各补充一个“求最大值”的变体，并说明哪种更适合在运行期插入新类型。",
                "hint": "泛型要求编译期已知类型集；接口允许运行期新实现。",
                "answer": "接口方案更适合运行期扩展新类型；泛型方案类型更安全、无断言开销。"}],
    explain="""泛型与接口解决的是不同问题。泛型适合“同一套算法服务一组已知、可约束的类型”，优点是编译期安全检查、无装箱/断言开销。接口适合“运行期多态”，例如一个集合里同时放不同类型、或允许第三方插件新增实现。本例用同一求和需求展示两者：SumGeneric[T] 靠约束直接相加；SumInterface 靠 Value() 方法取数值。运行结果相同，选型取决于你是想要静态类型安全与性能，还是运行期扩展性。二者并非互斥——实际代码常在接口边界内使用泛型容器。""",
    )

add("T066", title="依赖注入：显式传递优于全局", level="intermediate",
    kind="single-file", runtime="desktop",
    files=["main.go"], codeFile="main.go",
    vkind="stdout-exact",
    expected="下午好，gopher\n上午好，gopher",
    run="go run main.go",
    concepts=["依赖注入", "接口", "可测试性", "时钟抽象"],
    summary="把外部依赖（时钟）抽象成接口并由构造函数注入，使业务逻辑可确定性测试。",
    objective="能识别隐式依赖（time.Now、全局单例）并用构造函数显式注入接口依赖。",
    prereq=["T041 接口基础与鸭子类型", "T037 结构体定义、字面量与字段访问"],
    pitfalls=["在业务函数里直接调用 time.Now()：结果随运行时刻变化，测试无法固定。",
              "注入具体类型而不是接口：仍然无法在测试中用替身替换。"],
    exercises=[{"prompt": "再抽象一个 ID 生成器接口并注入，用固定序列实现让输出确定。",
                "hint": "接口方法签名如 NextID() int。",
                "answer": "定义 IDGen 接口，fixedIDGen 每次返回预置序列；Greeter 同时注入 Clock 与 IDGen。"}],
    explain="""依赖注入的核心是“把外部依赖从内部 new 出来，改为从外部传进来”。示例把“现在几点”抽象成 Clock 接口，Greeter 通过 NewGreeter(Clock) 接收它。生产环境传 realClock，测试/演示传 fixedClock，于是同一份业务逻辑既能对接真实时间，又能得到完全确定的输出。这样做的直接好处：业务逻辑不依赖全局状态、便于单测、便于替换实现。反例是直接调用 time.Now() 或读全局变量，那会让测试结果不可控、无法隔离。""",
    )

add("T067", title="包级 API 设计与向后兼容", level="intermediate",
    kind="single-file", runtime="desktop",
    files=["main.go"], codeFile="main.go",
    vkind="stdout-exact",
    expected="default: addr=127.0.0.1:8080 readTimeout=5s maxConns=128 access=false\ncustom:  addr=0.0.0.0:9000 readTimeout=30s maxConns=1024 access=true",
    run="go run main.go",
    concepts=["函数选项", "向后兼容", "默认值", "API 设计"],
    summary="用函数选项模式（Functional Options）让构造函数在新增配置时不破坏既有调用方。",
    objective="能用 Option func(*T) 模式设计可扩展、向后兼容的构造 API。",
    prereq=["T066 依赖注入：显式传递优于全局", "T025 函数是一等值：高阶函数"],
    pitfalls=["用固定长参数列表：每加一个配置就破坏所有调用方，需要改签名。",
              "选项里不先设默认值：未传选项时字段为零值，产生隐蔽 bug。"],
    exercises=[{"prompt": "新增一个 WithTLS(bool) 选项，并保证旧调用点无需修改。",
                "hint": "只需新增一个返回 Option 的函数，NewServer 签名不变。",
                "answer": "func WithTLS(on bool) Option { return func(s *Server){ s.TLS = on } }，现有调用零改动。"}],
    explain="""包级 API 一旦发布就很难改签名。函数选项模式把“可变配置”做成 func(*Server) 类型，NewServer(opts ...Option) 接收零到多个选项：先建立安全默认值，再依次应用。于是未来新增 WithXxx 只是新增一个函数，不触碰 NewServer 的签名，因此对已有调用方完全向后兼容。这比“config 结构体指针”更有表达力（可只覆盖想改的字段而不必给其余字段填零值），也比大量重载更符合 Go 的单一函数风格。""",
    )

add("T068", title="语义化版本与最小版本选择", level="advanced",
    kind="module-project", runtime="desktop",
    files=["main.go"], codeFile="main.go",
    vkind="stdout-exact",
    expected="constraints: v1.2.0, v1.5.3, v1.4.9\nselected (MVS) = v1.5.3\n此时最大版本恰好等于最小可行版本",
    run="go run .",
    concepts=["语义化版本", "MVS", "依赖解析", "可复现构建"],
    summary="实现最小版本选择（MVS）：在多个依赖版本要求中选出“满足全部要求的最小可行版本”。",
    objective="能说明语义化版本 major/minor/patch 的含义，并解释 MVS 为何能保证可复现构建。",
    prereq=["T060 Go Modules：go.mod 与依赖版本", "T032 排序：sort.Slice 与自定义比较"],
    pitfalls=["误以为 Go 总是选“最新版”：MVS 选的是满足所有约束的最小版本，不是最大/最新。",
              "忽略 major 版本是互不兼容的不同模块路径（v1 与 v2 是不同 import path）。"],
    exercises=[{"prompt": "扩展 SelectMVS，当存在多个 major 版本要求时报告不兼容错误。",
                "hint": "先按 major 分组，若出现两个不同 major 则返回错误。",
                "answer": "按 Major 分组；若组数大于 1 返回 error 说明需要不同的模块路径。"}],
    explain="""语义化版本用 major.minor.patch 表达兼容性：major 变更表示破坏性改动，minor 增加向后兼容的新功能，patch 为向后兼容的修复。Go 的最小版本选择（MVS）在解析依赖时，对所有约束取“满足全部要求的最小可行版本”。这与很多包管理器“取最新”不同，好处是升级只在你显式要求时发生，构建因此可复现。本例用 Version 类型与 Compare 实现语义化版本比较，再对一组要求求 MVS，并对照“取最大”的差异。工程上是 module-project：真实 MVS 由 go 命令在 go.mod/go.sum 上完成，本例用纯逻辑演示其规则。""",
    )

add("T069", title="构建标签与多平台文件后缀", level="intermediate",
    kind="module-project", runtime="desktop",
    files=["go.mod", "main.go", "impl_default.go", "impl_special.go"], codeFile="main.go",
    vkind="stdout-exact",
    expected="selected impl = default\nwith -tags special impl = special",
    run="go run .",
    concepts=["构建标签", "文件后缀", "多平台", "GOOS"],
    summary="用 //go:build 标签与 _GOOS 文件后缀在编译期选择平台相关实现。",
    objective="能用构建约束与文件后缀为不同平台/特性集提供互斥实现。",
    prereq=["T060 Go Modules：go.mod 与依赖版本"],
    pitfalls=["用运行期 if runtime.GOOS 替代编译期构建标签：会同时编译两份代码，依赖的平台库可能无法在某些平台编译。",
              "//go:build 与旧的 // +build 混用且不一致：新工具链以 //go:build 为准，可能产生困惑。"],
    exercises=[{"prompt": "为本示例补一个 file_windows.go 与 file_linux.go，各提供一个同名函数，用 go build 分别交叉编译验证。",
                "hint": "文件名后缀 _windows.go/_linux.go 会自动按 GOOS 生效。",
                "answer": "两个文件各定义 func platformName() string；GOOS=windows/linux 交叉编译各自生效，且无需 //go:build。"}],
    explain="""构建标签与文件后缀都参与“哪些文件进入本次编译”的决定。文件后缀（_windows.go、_linux_amd64.go）由工具链按 GOOS/GOARCH 自动选择，简单直观；//go:build 行可表达更复杂条件，如 -tags special 或 !release。二者都在编译期生效，未选中的文件根本不参与编译，因此可以安全地在不同平台使用不同依赖。本例由 implName/specialImplName 两个函数演示标签切换，并刻意不打印 runtime.GOOS/GOARCH（那会随平台变化，破坏确定输出）。完整的标签切换需在多文件工程里用 `go run .` 与 `go run -tags special .` 对照验证。""",
    )

add("T070", title="代码生成与 go:generate 边界", level="advanced",
    kind="module-project", runtime="desktop",
    files=["go.mod", "main.go", "day.go", "day_string.go", "gen_main.go"], codeFile="main.go",
    vkind="stdout-exact",
    expected="Monday  => Monday\nTuesday => Tuesday\nDay(99) => Day(99)\nnote: `go generate ./...` reruns the generator for day_string.go;\n      it is not part of `go build` and is desktop only here.",
    run="go run .",
    concepts=["go:generate", "代码生成", "Stringer", "枚举"],
    summary="理解 go:generate 是显式约定的生成步骤，并用“生成器等价物”手写枚举的 String()。",
    objective="能说明 go:generate 不参与 go build、需要显式运行，并写出等价的 String() 实现。",
    prereq=["T045 标准接口：Stringer 与 error", "T059 包、导出规则与初始化顺序"],
    pitfalls=["以为 go build 会自动运行生成器：不会，必须显式 go generate。",
              "生成文件忘了提交或忘了重新生成：CI 会因为源码缺失或过期而失败。",
              "移动端 Yaegi 不执行 go:generate——本主题 desktop only。"],
    exercises=[{"prompt": "为 Day 增加一个越界值并在 String() 中打印数值回退，验证与 stringer 行为一致。",
                "hint": "回退格式 Day(N)。",
                "answer": "dayNames 索引越界时返回 fmt.Sprintf(\"Day(%d)\", int(d))。"}],
    explain="""//go:generate 是一条普通注释里的约定指令：运行 go generate 时，Go 执行注释中的命令来生成源码（典型是 stringer 为枚举生成 String()）。它是显式的开发步骤，不参与 go build，也不会在别人 clone 后自动跑，因此生成结果通常要一并提交。本例不依赖外部生成器，而是手写“生成器会产出的那张表”（dayNames）并实现 String()，从而在不联网、不装工具的前提下理解生成的本质与边界（越界回退）。真实工程是 module-project：需要 day.go + 生成文件 + go.mod，并用 go generate 触发生成。""",
    )

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    for m in ("data_a1", "data_a2", "data_a3", "data_b2", "data_b3", "data_b4", "data_b5", "data_b6", "data_b7"):
        __import__(m).register(add)
    os.makedirs(TOPICS, exist_ok=True)
    for tid, meta in T.items():
        code_path = os.path.join(SAMPLES, tid, meta["codeFile"])
        with open(code_path, "r", encoding="utf-8") as fh:
            code = fh.read()
        # Derive sampleFiles from the real directory so the declaration's file
        # list can never drift from what is on disk.
        real_files = sorted(
            f for f in os.listdir(os.path.join(SAMPLES, tid))
            if os.path.isfile(os.path.join(SAMPLES, tid, f))
        )
        meta["files"] = real_files
        num = tid[1:]
        explain = meta["explain"]
        kind = meta["kind"]
        # Non-single-file topics must declare the工程例子 status in the body.
        if kind != "single-file" and "一键导入" not in explain:
            files_list = "、".join(meta["files"])
            decl = (
                "本例为工程例子，不能由 CodeSnippet 一键导入；请按下列文件清单手动创建，"
                "并运行官方 Go SDK 命令。文件清单：" + files_list + "。运行命令："
                + meta["run"] + "。"
            )
            explain = decl + explain
        # Real, non-empty deterministic result text for the lesson.output field.
        out_text = meta.get("output", "")
        if not out_text:
            out_text = TEST_OUTPUT.get(tid, "") or meta["expected"]
        tutorial = {
            "id": f"go-tutorial-{num}",
            "language": "go",
            "type": "go",
            "locale": "zh-CN",
            "level": meta["level"],
            "title": meta["title"],
            "summary": meta["summary"],
            "concepts": meta["concepts"],
            "source": SRC,
            "license": LICENSE,
            "updatedAt": UPDATED,
            "objective": meta["objective"],
            "prerequisites": meta["prereq"],
            "pitfalls": meta["pitfalls"],
            "exercises": meta["exercises"],
            "explain": explain,
            "code": code,
            "output": out_text,
        }
        example = {
            "id": f"go-example-{num}",
            "language": "go",
            "type": "go",
            "locale": "zh-CN",
            "level": meta["level"],
            "title": meta["title"] + "（示例）",
            "summary": "对应主题 " + tid + " 的可运行示例。",
            "concepts": meta["concepts"],
            "source": SRC,
            "license": LICENSE,
            "updatedAt": UPDATED,
            "code": code,
            "expectedOutput": meta["expected"],
            "templateType": "go",
        }
        doc = {
            "id": tid,
            "runtime": meta["runtime"],
            "importKind": meta["kind"],
            "runCommand": meta["run"],
            "verification": {"kind": meta["vkind"], "expected": meta["expected"]},
            "sampleFiles": meta["files"],
            "tutorial": tutorial,
            "example": example,
        }
        out = os.path.join(TOPICS, f"{tid}.json")
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
    print(f"wrote {len(T)} topic files")
