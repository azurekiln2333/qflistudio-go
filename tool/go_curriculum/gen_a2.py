#!/usr/bin/env python3
"""Generate topic JSON for T006-T010."""
from author import build_topic, write_topic

SPECS = [
    dict(
        topic_id="T006", level="beginner",
        title="类型转换与数值精度",
        summary="显式类型转换、截断与浮点取整，理解 Go 不做隐式数值转换。",
        concepts=["类型转换", "截断", "精度"],
        objective="能在数值类型间做显式转换，并解释截断与浮点取整的行为。",
        prerequisites=["T004 基础类型"],
        pitfalls=[
            "期待隐式转换：Go 不会在 int 与 float64 间自动转换，必须写 float64(i)，否则编译报错。",
            "把 3.9 直接写成 int(3.9)：无类型浮点常量不能直接转成 int，会报 cannot convert；要先赋给 float64 变量再转换。",
        ],
        exercises=[{
            "prompt": "把一个大 int64 转成 int32 并打印，解释看到的数值变化。",
            "hint": "窄化转换会保留低 32 位，符号位按目标类型解释。",
            "answer": "1<<40 转 int32 后为 0，因为低 32 位全为 0；说明窄化是截断而非饱和。",
        }],
        explain="Go 的数值类型之间没有隐式转换：把 int 赋给 float64 或反向都不允许，必须显式写出目标类型。这消除了大量因隐式提升导致的精度意外。转换语义分两类：整数窄化（如 int64 到 int32）按位截断，只保留能放进目标宽度的低位；浮点到整数丢弃小数部分（向零取整）。\n\n一个容易踩的细节：无类型常量 3.9 不能被写成 int(3.9)，因为它是精度无限的常量，编译器不允许直接窄化为整数；要先把它放进 float64 变量，再做转换。\n\n本样例演示显式转换、int64 到 int32 的截断，以及浮点变量的取整结果。",
        output="3 3\nbig=1099511627776 small=0\ntrunc(3.9)=3",
        example_title="显式转换与截断",
        example_summary="演示 int/float 显式转换、int64 到 int32 的截断与浮点取整。",
    ),
    dict(
        topic_id="T007", level="beginner",
        title="字符串、rune 与字节",
        summary="区分 string、byte、rune，按字节与按字符两种方式遍历 UTF-8 文本。",
        concepts=["string", "byte", "rune", "UTF-8"],
        objective="能说明 len(s) 与 RuneCountInString 的差异，并用 range 正确遍历含中文的字符串。",
        prerequisites=["T004 基础类型"],
        pitfalls=[
            "用 s[i] 遍历字符串：索引得到的是单个字节（byte），遇到多字节 UTF-8 字符会切碎，应使用 range 得到 rune。",
            "以为 len(s) 是字符数：len 返回字节数，含中文的字符串字节数大于字符数。",
        ],
        exercises=[{
            "prompt": "对同一字符串分别打印 len 与 RuneCountInString，并解释差异来源。",
            "hint": "UTF-8 中一个中文字符通常占 3 个字节。",
            "answer": "len 统计字节数，RuneCountInString 统计 Unicode 码点个数；中文每字 3 字节，所以字节数更大。",
        }],
        explain="Go 的 string 是不可变的字节序列，按 UTF-8 编码存储。len(s) 返回字节数；若文本含多字节字符，字符数会小于字节数，需要用 utf8.RuneCountInString 或 range 遍历来按「字符」（rune，即 Unicode 码点）处理。\n\nrange 遍历字符串时，第一个返回值是当前 rune 起始处的字节索引，第二个是该 rune。这解释了为什么样例里索引是 0、1、3、4……：é 与中文字符占多个字节，跳过了中间字节位置。\n\n本样例对含 é 与中文的字符串打印字节数、字符数，并按 rune 逐字打印索引与字符。",
        output="bytes: 14\nrunes: 9\nat 0: h\nat 1: é\nat 3: l\nat 4: l\nat 5: o\nat 6: ,\nat 7:  \nat 8: 世\nat 11: 界",
        example_title="字节与字符计数",
        example_summary="用 len 与 utf8.RuneCountInString 对比同一字符串的字节数与字符数。",
        example_code="package main\n\nimport (\n\t\"fmt\"\n\t\"unicode/utf8\"\n)\n\nfunc main() {\n\ts := \"héllo, 世界\"\n\tfmt.Println(\"bytes:\", len(s))\n\tfmt.Println(\"runes:\", utf8.RuneCountInString(s))\n}\n",
        example_expected="bytes: 14\nrunes: 9",
    ),
    dict(
        topic_id="T008", level="beginner",
        title="格式化输出与 fmt 谓词",
        summary="用 %v/%+v/%T/%q/%d/%f 等谓词精确控制输出格式。",
        concepts=["fmt", "格式化谓词"],
        objective="能选用合适的 fmt 谓词打印结构体、字符串、数值与类型。",
        prerequisites=["T004 基础类型"],
        pitfalls=[
            "%v 与 %+v 的差别：%v 打印结构体字段值，%+v 额外带上字段名，调试结构体时 %+v 更有用。",
            "对字符串用 %d 之类错误谓词：谓词与参数类型不匹配会打印 %!d(string=...)，go vet 也会告警。",
        ],
        exercises=[{
            "prompt": "为 point 增加一个字段 Z，并分别用 %v 和 %+v 打印，观察输出差异。",
            "hint": "%+v 会显示字段名。",
            "answer": "%v 显示 {3 4 5}，%+v 显示 {X:3 Y:4 Z:5}。",
        }],
        explain="fmt 用谓词描述如何格式化参数：%v 是通用默认，%+v 为结构体附加字段名，%T 打印类型，%q 给字符串加引号并转义，%d/%f/%e 控制整数与浮点的表示。理解谓词能让你在调试和输出时一次表达清楚意图，而不是手工拼接字符串。\n\n谓词数量或类型不匹配时，fmt 会输出以 %! 开头的诊断占位符（如 %!d(string=go)），而 go vet 能静态发现最常见的这类错误。\n\n本样例对同一结构体分别用 %v 与 %+v，并对字符串、整数、类型使用不同谓词。",
        output='v={3 4} +v={X:3 Y:4}\nd=42 q="go" t=main.point\nf=3.14 e=1.234500e+03',
        example_title="谓词对比",
        example_summary="对结构体与标量值展示常用的 fmt 谓词输出。",
    ),
    dict(
        topic_id="T009", level="beginner",
        title="输入读取：bufio.Scanner 扫描多行",
        summary="用 bufio.Scanner 逐行读取文本并统计行数与词数，正确处理扫描错误。",
        concepts=["bufio", "Scanner", "输入读取"],
        objective="能用 bufio.Scanner 逐行读取并以空白分词，同时检查 scanner.Err()。",
        prerequisites=["T007 字符串与 rune"],
        pitfalls=[
            "忘记检查 scanner.Err()：扫描在出错（如超长行）时会提前停止，不检查就会静默漏读。",
            "把 Scanner 用于超大 token：默认最大 token 64K，超长行会触发 ErrTooLong，需要手动调 Buffer。",
        ],
        exercises=[{
            "prompt": "把输入改成三行并预测 lines 与 words，再运行验证。",
            "hint": "strings.Fields 按任意空白分词，空行不计词。",
            "answer": "三行分别为若干词时，lines=3，words 等于所有行词数之和；空行 contributes 0。",
        }],
        explain="读取输入常用 bufio.Scanner：它把来源抽象成逐 token 读取，默认按行（ScanLines）。每次 Scan() 前进一个 token 并返回是否还有数据，Text() 返回该 token。扫描结束后必须检查 Err()，否则会把错误当成「正常结束」。\n\n本样例用 strings.NewReader 构造一个内存输入源（便于确定性验证），逐行扫描并用 strings.Fields 按空白切词统计。真实场景可把来源换成 os.Stdin 或文件。\n\nScanner 的默认 token 上限是 64K；处理超长行时要显式调用 scanner.Buffer 调大上限，这是常见生产陷阱。",
        output="lines=2 words=3",
        example_title="逐行扫描统计",
        example_summary="对固定内存输入逐行扫描并统计行数与词数。",
    ),
    dict(
        topic_id="T010", level="beginner",
        title="运算符、优先级与位运算",
        summary="掌握算术、比较、位运算及其优先级，理解整数除法与取余。",
        concepts=["运算符", "位运算", "优先级"],
        objective="能正确使用算术与位运算符，并说明整数除法截断与逻辑短路。",
        prerequisites=["T003 变量与零值"],
        pitfalls=[
            "整数除法截断：6/4 结果是 1 而不是 1.5，需要浮点结果时要先转换类型。",
            "混淆 & 与 &&：& 是按位与（对整数逐位运算），&& 是逻辑短路；用于布尔条件时只能用 &&。",
        ],
        exercises=[{
            "prompt": "计算 12>>2 与 12&3 并解释二进制层面的含义。",
            "hint": "12 的二进制是 1100。",
            "answer": "12>>2=3（右移两位得 11），12&3=0（1100 & 0011 = 0000）。",
        }],
        explain="Go 的算术运算符与多数语言一致，但整数除法直接截断小数、取余用 %。位运算 &、|、^、<<、>> 作用于整数的二进制表示。优先级上，乘除模高于加减，比较低于算术，&& 低于 ||，且 && 与 || 短路——右侧只在必要时求值。\n\n本样例同时打印算术结果与位运算结果，并用一个复合表达式演示优先级：1+2*3 == 7 && 4%2 == 0 先算乘除与取余，再比较，最后做逻辑与。\n\n整数除法是常见误区：需要浮点结果时必须先做类型转换，否则会静默截断。",
        output="add 10 sub 2 mul 24 div 1 mod 2\nand 4 or 6 xor 2 shl 12 shr 3\nexpr true",
        example_title="算术与位运算",
        example_summary="对同一组数打印算术、位运算与优先级表达式的结果。",
    ),
]

if __name__ == "__main__":
    for spec in SPECS:
        write_topic(build_topic(**spec))
        print("wrote", spec["topic_id"])
