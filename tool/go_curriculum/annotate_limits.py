#!/usr/bin/env python3
"""Add an explicit native-Yaegi platform-limit note to w8:p2 boundary topics."""
import json
from pathlib import Path

TOPICS = Path(__file__).resolve().parent / "topics"

NOTES = {
    "T040": "平台限制：方法表达式（T.method; g(recv)）在当前项目移动端 Yaegi 解释器下会 panic（reflect: Call with too many input arguments），本主题仅桌面官方 Go 可运行；移动端请使用方法值（recv.method）形式。",
    "T047": "平台限制：涉及接口赋值/反射的实现路径在移动端 Yaegi 解释器下会 panic（reflect.Set: value of type interp.valueInterface...），本主题仅桌面官方 Go 可运行。",
    "T052": "平台限制：errors.As 在移动端 Yaegi 解释器下会报 errors: *target must be interface or implement error，本主题仅桌面官方 Go 可运行。",
    "T053": "平台限制：自定义错误配合 errors.As/Unwrap 在移动端 Yaegi 解释器下不受支持（同 errors.As 报错），本主题仅桌面官方 Go 可运行。",
}

for tid, note in NOTES.items():
    p = TOPICS / f"{tid}.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    pitfalls = d["tutorial"]["pitfalls"]
    if note not in pitfalls:
        pitfalls.append(note)
    # Also append to example summary context via explain tail if not present.
    if note not in d["tutorial"]["explain"]:
        d["tutorial"]["explain"] = d["tutorial"]["explain"].rstrip() + "\n\n" + note
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("annotated", tid)
