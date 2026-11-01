"""Remove obsolete import/runtime notes without changing executable Go or expectations."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TOOL = ROOT / "tool/go_curriculum"

MODULE_PREFIX_OLD = "导入到编辑器或新项目时会同时保存本课的全部辅助文件，所示源码保持为选中的入口文件。代码注释中的手动文件清单也可用于桌面复现；构建标签、生成器和完整 go 命令仍按各自工具链能力使用。"
MODULE_PREFIX = "导入到编辑器或新项目时会同时保存辅助文件。所示入口与同包辅助源码、数据位于 src/；go.mod、go.sum 和被导入子包的完整目录树保留模块根路径。运行从所选入口所在目录开始。源码注释展示原始工程布局；构建标签、生成器、覆盖率和剖析命令按各自工具链能力使用。"
TEST_PREFIX_OLD = "导入时默认入口为 snippet_test.go，并自动附带模块与同包辅助源码。内置运行器执行该包的真实测试、基准及已登记 fuzz seed，断言失败会返回非零状态。它不提供完整 Go SDK 的持续模糊搜索或 race 检测；相应 go 命令由桌面官方工具链执行。源码注释保留原工程结构供对照。"
TEST_PREFIX = "导入时默认入口为 src/snippet_test.go，同包辅助源码和数据一并保存，模块文件保留根目录。选中测试入口运行会执行该包的测试、基准及已登记 fuzz seed，断言失败返回非零状态。内置运行器不提供完整 Go SDK 的持续模糊搜索、race 检测、覆盖率或性能剖析；相应命令使用桌面官方工具链。源码注释展示原始工程布局。"

EXPLAIN_REPLACEMENTS = {
    "T062": {"泛型属于 Go 的静态编译特性，本项目移动端的 Yaegi 解释器未实测支持，故标记 desktop only，不得声称移动端可运行。": "类型参数及约束要求 Go 1.18+；本例使用的标准库 cmp 包要求 Go 1.21+。", "cmp.Ordered 是一个预声明的约束": "cmp.Ordered 是标准库 cmp 包提供的约束"},
    "T063": {"desktop only，理由同 T062。": "类型集合约束用于类型参数，不能作为普通运行时接口值的类型。"},
    "T064": {"泛型类型同样是编译期特性，desktop only。": "泛型类型的每次使用都要提供或推断具体类型参数。"},
    "T077": {"官方 Go 还可用 go test -race 检测竞争（本项目环境无 C 工具链，-race 需 CGO，故仅作为文档命令）。移动端 Yaegi 不支持 go test/-race，desktop only。": "桌面官方工具链在具备相应平台和 C 工具链条件时，还可用 go test -race 检测竞争。普通测试通过不等于完成 race 检测。"},
    "T078": {"移动端 Yaegi 未实测，desktop only。": "测试入口直接运行这些确定性断言；race 检测另用具备相应条件的官方工具链。"},
    "T080": {"移动端不支持 bench，desktop only。": "内置运行器执行有界基准循环；需要自动校准与可比较的性能报告时使用官方工具链。", "benchmark 只要求能跑出 ns/op，不作为通过条件（数值随机器变化）。": "benchmark 要求实际执行循环，不把耗时数值作为通过条件（数值随机器变化）。"},
    "T081": {"go test 运行，desktop only（移动端未实测）。": "选中测试入口运行，或使用官方工具链 go test。"},
    "T086": {"移动端文件系统能力未实测，标 Yaegi*（待实测），默认 desktop。": "文件操作应限定到应用可写目录，并处理权限与 I/O 错误。"},
    "T088": {"移动端目录访问能力未实测，标 Yaegi*（待实测），默认 desktop。": "目录操作仍须检查访问权限及每次 I/O 的错误。"},
    "T093": {"桌面与移动端差异需实测，本主题默认 desktop。": "避免把调度延迟和真实耗时作为跨平台固定输出。"},
    "T096": {"移动端模板能力未实测，标 Yaegi*（待实测），默认 desktop。": "执行失败时目标可能已经写入部分文本，需要完整成功结果时先渲染到缓冲区。"},
    "T099": {"移动端 net 能力未实测，标 Yaegi*（待实测），默认 desktop。": "测试只使用本机回环服务，不依赖外部网络。"},
    "T100": {"desktop only（移动端 net 未实测）。": "可选中测试入口执行这些离线断言。"},
    "T105": {"用官方 SDK 的 go test 运行；移动端不执行 go test，desktop only。": "选中测试入口运行；桌面官方工具链也可使用 go test。"},
    "T108": {"验证只要求“基准能运行并报出指标”（bench-exists）。": "验证要求实际执行基准循环（bench-exists），不能只匹配一行成功文字。", "移动端不支持 bench，desktop only。": "内置运行器执行有界基准循环；自动校准和性能指标比较使用官方工具链。"},
    "T110": {"移动端不支持 fuzz，desktop only。": "内置运行器只执行已登记的种子；持续生成输入与最小化使用官方工具链。"},
    "T112": {"用 go run 运行并可用 -gcflags=-m 观察；desktop only。": "普通入口展示程序结果；逃逸分析报告使用官方工具链的 -gcflags=-m。"},
    "T113": {"go test 采集 + go run 演示；desktop only（移动端无 pprof 工具链）。": "普通入口演示结果；CPU 采集与交互式 pprof 分析使用桌面官方工具链。"},
    "T114": {"bench 需官方 SDK，desktop only。": "内置运行器可执行有界基准循环；性能测量与比较使用官方工具链。"},
    "T115": {"single-file 示例可被 CodeSnippet 导入；静态检查需官方 SDK，移动端不提供，desktop only。": "单文件示例可直接导入运行。编辑器的格式化操作可在内置运行器完成；本课列出的 gofmt 与 go vet 命令使用官方工具链。"},
    "T116": {"移动端 slog 支持未实测，标 Yaegi*（待实测），默认 desktop。": "处理器输出位置应显式指定，测试时写入可核对的缓冲区。"},
    "T118": {"涉及文件系统，desktop only。": "普通入口运行存储示范，选中 store_test.go 可运行端到端测试。"},
    "T119": {"并发+文件，desktop only。": "普通入口展示词频，选中 freq_test.go 运行并发一致性测试。"},
    "T120": {"涉及 net/监听，desktop only。": "普通入口展示配置，选中 api_test.go 运行无需监听端口的处理器测试。"},
}

PITFALL_REPLACEMENTS = {
    "T040": "方法表达式的第一个显式参数是接收者；把它当成已绑定接收者的方法值调用会造成参数不匹配。",
    "T047": "把策略重新赋给接口变量只会替换该变量保存的实现；其他已构造的装饰器仍持有原先的依赖。",
    "T052": "errors.As 的目标必须是非空指针，并且所指类型应实现 error 或为接口；不满足要求会 panic。",
    "T053": "Error、Unwrap、Is 和 As 的方法签名必须准确；名称相同但签名不同的方法不会参与错误链协议。",
    "T062": "泛型语法需要 Go 1.18+，本例的标准库 cmp 包需要 Go 1.21+；使用旧工具链会失败。",
    "T070": "运行程序不会自动运行生成器；内置运行器使用已存在的生成源码，重新生成需使用官方工具链。",
    "T096": "Execute 失败前可能已写入部分内容；需要完整输出时先写缓冲区，成功后再提交。",
    "T116": "处理器写入哪个目标取决于构造参数；测试中显式传入缓冲区，避免混淆标准输出和标准错误。",
}

COMMENT_REPLACEMENTS = {
    "// 注意：泛型属于 Go 1.18+ 的静态编译特性，本项目的移动端 Yaegi 解释器\n// 未实测支持，因此本主题标记为 desktop only。": "// 类型参数需要 Go 1.18+；本例的标准库 cmp 包需要 Go 1.21+。",
    "// 泛型 = desktop only（移动端 Yaegi 未实测）。": "// 类型参数与约束需要 Go 1.18+。",
    "// 移动端 Yaegi 不支持 go test/-race，故本主题 desktop only。": "// 选中测试入口运行测试；-race 检测另需具备相应条件的官方工具链。",
    "// 移动端 Yaegi 不支持 go test/-race，desktop only。": "// 选中测试入口运行测试；-race 检测另需具备相应条件的官方工具链。",
    "// 移动端 Yaegi 对 sync/atomic 未实测，desktop only。": "// 选中测试入口执行原子计数断言；普通测试通过不等于完成 race 检测。",
    "// 移动端 Yaegi 对 net 未实测，desktop only。": "// 测试使用回环服务，不依赖外部网络。",
    "// 移动端不支持 bench，desktop only。": "// 内置运行器执行有界基准循环；性能测量与比较使用官方工具链。",
    "// desktop only（移动端不执行 go test）。": "// 选中测试入口执行断言，或使用桌面官方工具链 go test。",
    "// desktop only（移动端不支持 fuzz）。": "// 内置运行器执行已登记种子；持续 fuzz 搜索使用桌面官方工具链。",
    "// desktop only（移动端不提供这些工具）。": "// 下列命令使用官方工具链；单文件程序可直接导入运行。",
    "// desktop only（文件系统 + go test）。": "// 普通入口演示文件操作，选中 store_test.go 运行相应测试。",
    "// desktop only（并发 + 文件）。": "// 普通入口演示词频，选中 freq_test.go 运行相应测试。",
    "// desktop only（net 监听 + go test）。": "// 普通入口演示配置，选中 api_test.go 运行无需监听的处理器测试。",
}


def rewrite_code(text: str, topic_id: str, import_kind: str) -> str:
    result = text.replace("，不能一键导入", "，导入时附带辅助文件")
    result = result.replace("，不能一键导入。完整结构：", "，导入时附带辅助文件。原始结构：")
    # The first replacement handles both parentheses and sentence forms.
    result = result.replace("，导入时附带辅助文件。完整结构：", "，导入时附带辅助文件。原始结构：")
    for before, after in COMMENT_REPLACEMENTS.items():
        # Preserve existing source-file line endings.
        result = result.replace(before, after).replace(before.replace("\n", "\r\n"), after.replace("\n", "\r\n"))
    result = re.sub(r"(// 运行：go test ./\.\.\.)   desktop only(?:（[^\n]*?）)?。", r"\1；也可选中测试入口运行。", result)
    if topic_id == "T109":
        result = result.replace("// desktop only。", "// 测试入口执行断言；覆盖率报告使用桌面官方工具链。")
    elif topic_id == "T112":
        result = result.replace("// desktop only。", "// 普通入口展示结果；逃逸分析报告使用桌面官方工具链。")
    elif topic_id == "T113":
        result = result.replace("// desktop only。", "// 普通入口展示结果；剖析采集与 pprof 分析使用桌面官方工具链。")
    elif topic_id == "T114":
        result = result.replace("// desktop only。", "// 内置运行器执行有界基准循环；性能测量与比较使用官方工具链。")
    if "导入时附带辅助文件" in result:
        newline = "\r\n" if "\r\n" in result else "\n"
        marker = ("// 导入后本文件默认为 src/snippet_test.go，同包辅助源码一并保存。"
                  if import_kind == "test-package" else
                  "// 导入后入口和同包辅助源码位于 src/，模块及子包保留根目录布局。")
        if marker not in result:
            result = marker + newline + result
    # Every edited source line must be a line comment; executable text is exact.
    executable = lambda value: [line for line in value.splitlines() if not line.lstrip().startswith("//")]
    assert executable(text) == executable(result), f"executable change: {topic_id}"
    return result


def main() -> None:
    changes = []
    for path in sorted((TOOL / "topics").glob("T*.json")):
        before_bytes = path.read_bytes()
        topic = json.loads(before_bytes)
        topic_id = topic["id"]
        expectations = json.dumps([topic["verification"], topic["tutorial"]["output"], topic["example"]["expectedOutput"]], ensure_ascii=False)
        tutorial = topic["tutorial"]
        tutorial["explain"] = tutorial["explain"].replace(MODULE_PREFIX_OLD, MODULE_PREFIX).replace(TEST_PREFIX_OLD, TEST_PREFIX)
        for before, after in EXPLAIN_REPLACEMENTS.get(topic_id, {}).items():
            tutorial["explain"] = tutorial["explain"].replace(before, after)
        # These suffixes applied to ordinary test execution, not optional SDK tools.
        tutorial["explain"] = tutorial["explain"].replace("，desktop only。", "。")
        if topic_id in PITFALL_REPLACEMENTS:
            tutorial["pitfalls"] = [PITFALL_REPLACEMENTS[topic_id] if "平台限制：" in item or "desktop only" in item else item for item in tutorial["pitfalls"]]
        for kind in ("tutorial", "example"):
            topic[kind]["code"] = rewrite_code(topic[kind]["code"], topic_id, topic["importKind"])
        sample_changes = []
        for sample_path in sorted((TOOL / "samples" / topic_id).rglob("*.go")):
            old = sample_path.read_bytes()
            new = rewrite_code(old.decode("utf-8"), topic_id, topic["importKind"]).encode("utf-8")
            if old != new:
                sample_path.write_bytes(new)
                sample_changes.append({"path": sample_path.relative_to(ROOT).as_posix(), "beforeSha256": hashlib.sha256(old).hexdigest(), "afterSha256": hashlib.sha256(new).hexdigest()})
        assert expectations == json.dumps([topic["verification"], topic["tutorial"]["output"], topic["example"]["expectedOutput"]], ensure_ascii=False)
        if topic != json.loads(before_bytes):
            path.write_text(json.dumps(topic, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
            changes.append({"topicId": topic_id, "sampleChanges": sample_changes})
    report = {"description": "Obsolete import/runtime notes removed; all changed Go lines are comments and all expected results are preserved.", "changedTopics": len(changes), "changes": changes}
    if changes:
        (HERE / "legacy-note-cleanup.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"updated {len(changes)} topics; executable code and expected results preserved")


if __name__ == "__main__":
    main()
