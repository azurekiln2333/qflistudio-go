#!/usr/bin/env python3
"""Generate topic JSON for batch A (T002-T020). Run from the tool dir."""
from author import build_topic, write_topic

SPECS = [
    dict(
        topic_id="T002", level="beginner",
        title="第一个程序：package main 与 main 函数",
        summary="编写、编译并运行最小 Go 程序，理解 package main 与 main 函数的约定。",
        concepts=["package main", "main 函数", "go run"],
        objective="能写出一个最小可运行的 Go 程序，并解释 package main 与 func main 各自的角色。",
        prerequisites=["T001 工具链概览"],
        pitfalls=[
            "把函数名写成 Main 或 mian：Go 区分大小写，入口必须是全小写的 main，否则编译通过但运行时报 'function main is undeclared'。",
            "在同一个包里写多个 func main：Go 会报 main redeclared，入口必须唯一。",
        ],
        exercises=[{
            "prompt": "把输出文本改成 hello, qfli 并重新运行；再故意把 main 改成 Main 观察报错信息。",
            "hint": "go run 会先编译，编译错误在运行前就会显示。",
            "answer": "正常输出 hello, qfli；改成 Main 后报 function main is undeclared in the main package。",
        }],
        explain="Go 程序由包组成，可执行程序的入口包固定叫 main，入口函数固定叫 func main()，二者都是约定而非配置。编译时工具链会寻找 package main 里的 func main 作为起点。fmt.Println 是标准库 fmt 包导出的函数——Go 只有首字母大写的标识符才会导出到包外。\n\nimport \"fmt\" 声明本文件依赖 fmt 包；Go 在编译期检查未使用的导入并直接报错，这强迫依赖显式而干净。\n\n运行：在样例目录执行 go run .，等效于先 go build 再执行产物。",
        output="hello, go",
        example_title="最小 main 包",
        example_summary="只导入 fmt，打印一行固定文本，作为一切 Go 程序的起点骨架。",
    ),
    dict(
        topic_id="T003", level="beginner",
        title="变量声明：var、短变量与零值",
        summary="区分 var、:= 与零值初始化，理解 Go 为何强调零值可用。",
        concepts=["var", "短变量声明", "零值"],
        objective="能用 var 和 := 声明变量，并说明未显式初始化时各类型的零值。",
        prerequisites=["T002 package main 与 main"],
        pitfalls=[
            "在函数外用 :=：短变量声明只能出现在函数内部，包级别必须用 var。",
            "误以为 var x int 是未初始化：Go 会把 x 设为零值 0，不存在未定义值的变量。",
        ],
        exercises=[{
            "prompt": "声明一个未初始化的 string 和 bool，打印它们并解释看到的零值。",
            "hint": "string 的零值是空串，bool 的零值是 false。",
            "answer": "打印 name=\"\" 与 ok=false，因为字符串和布尔的零值分别是空串和 false。",
        }],
        explain="Go 的变量总有确定的值。var 声明的变量若不带初始化表达式，会被赋予该类型的零值：数值为 0，字符串为空串，布尔为 false，指针/切片/映射/通道/接口为 nil。:= 是短变量声明，只在函数体内可用，它同时声明并推断类型，是局部变量的常用写法。\n\n把零值设计成「可用状态」是 Go 的重要取向：例如未初始化的 map 为 nil，但可以通过 make 创建；这减少了大量显式初始化样板。\n\n本样例混合使用 var 与 :=，并用 %q 打印字符串以看清空串。",
        output='count=0 name="" ok=false total=42 msg=零值演示',
        example_title="零值一览",
        example_summary="演示 int/string/bool 的零值以及短变量声明的推断类型。",
    ),
    dict(
        topic_id="T004", level="beginner",
        title="基础类型与类型推断",
        summary="认识 bool、定长整数、浮点与 string 的宽度，并用 %T 观察推断出的类型。",
        concepts=["基础类型", "类型推断", "%T"],
        objective="能说明 int8/uint8/float64/bool/string 的表示范围，并用 %T 验证推断类型。",
        prerequisites=["T003 变量与零值"],
        pitfalls=[
            "假设 int 是 32 位：int 的宽度随平台变化（64 位平台通常是 64 位），需要固定宽度时必须显式用 int32/int64。",
            "把无类型整数常量直接赋给 int8 而不检查范围：超出范围会在编译期报错，而不是运行时溢出。",
        ],
        exercises=[{
            "prompt": "声明一个 int8 等于 127 并尝试 +1，观察编译或运行行为并解释。",
            "hint": "127 是 int8 的上界，127+1 作为常量表达式会溢出。",
            "answer": "将 128 赋给 int8 会在编译期报 constant 128 overflows int8，说明 Go 在编译期就检查常量范围。",
        }],
        explain="Go 的基础类型是定长且显式的：int8/uint8 占 1 字节，float64 是 8 字节双精度，bool 是布尔，string 是不可变字节序列（UTF-8 编码）。int 与 uint 的宽度依赖平台，需要精确控制宽度时应使用定长类型，否则跨平台行为可能不一致。\n\n类型推断只发生在有初始化表达式时：typed := 10 推断为 int。fmt 的 %T 谓词会打印变量的动态类型，是理解推断结果的实用工具。\n\n本样例打印每种类型的值和类型，并演示 := 推断出 int。",
        output='int8=127 uint8=255 float64=3.5 bool=true string="go"\ntyped 是 int',
        example_title="类型与 %T",
        example_summary="用 %T 打印多个基础类型变量的实际类型。",
    ),
    dict(
        topic_id="T005", level="beginner",
        title="常量、iota 与无类型常量",
        summary="用 const 与 iota 构造枚举，并理解无类型常量的延迟定型。",
        concepts=["const", "iota", "无类型常量"],
        objective="能用 iota 定义一组递增枚举常量，并说明无类型常量在赋值时才确定类型。",
        prerequisites=["T004 基础类型"],
        pitfalls=[
            "以为 iota 是运行时计数器：iota 是编译期常量生成器，每个 const 块从 0 重新计数。",
            "把无类型常量当作有具体类型：const pi = 3.14159 本身是无类型的，赋给 float64 变量时才成为 float64。",
        ],
        exercises=[{
            "prompt": "在第 2 个枚举后插入一行 _ 跳过某个 iota 值，观察后续常量数值变化。",
            "hint": "iota 每行递增 1，_ 也占用一个 iota 值。",
            "answer": "插入 _ 后，其后的枚举值会整体后移 1，说明 iota 按行计数，未命名的行同样递增。",
        }],
        explain="const 定义编译期常量，不能取地址、不能重新赋值。iota 在 const 块中从 0 开始、每行递增 1，用来写枚举。把枚举基于一个具名类型（如 type Weekday int）可以让类型更清晰。\n\n无类型常量是 Go 的独特之处：字面量 3.14159 在未赋给变量前没有确定类型，赋给 float64 变量时成为 float64，赋给 float32 时成为 float32，从而在不损失精度语义的前提下复用同一常量。\n\n本样例打印三个枚举的整数值，并把无类型常量 pi 赋给 float64 后再格式化输出。",
        output="0 1 2\npi as float64 = 3.14",
        example_title="iota 枚举",
        example_summary="用 iota 生成 0、1、2 的枚举值并打印。",
    ),
]

if __name__ == "__main__":
    for spec in SPECS:
        write_topic(build_topic(**spec))
        print("wrote", spec["topic_id"])
