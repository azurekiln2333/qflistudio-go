"""Real, non-empty deterministic `output` text for test-package/bench topics.

These are the actual result lines produced by the pinned SDK (or the linux SDK
under WSL). Pass/fail is decided ONLY by verification.kind; this text is the
human-readable result shown in the lesson.
"""

TEST_OUTPUT = {
    "T077": "ok  \tqfli.example/t077\t0.003s",
    "T078": "ok  \tqfli.example/t078\t0.003s",
    "T080": "BenchmarkRenderPool-2    \t26144017\t43.59 ns/op\t16 B/op\t1 allocs/op\nBenchmarkRenderNoPool-2  \t23817556\t49.87 ns/op\t80 B/op\t2 allocs/op",
    "T081": "ok  \tqfli.example/t081\t0.004s",
    "T099": "ok  \tqfli.example/t099\t0.006s",
    "T100": "ok  \tqfli.example/t100\t0.003s",
    "T101": "ok  \tqfli.example/t101\t0.003s",
    "T102": "ok  \tqfli.example/t102\t0.003s",
    "T103": "ok  \tqfli.example/t103\t0.003s",
    "T104": "ok  \tqfli.example/t104\t0.058s",
    "T105": "ok  \tqfli.example/t105\t0.002s",
    "T106": "ok  \tqfli.example/t106\t0.002s",
    "T107": "ok  \tqfli.example/t107\t0.002s",
    "T108": "BenchmarkSum-2          \t7809880\t170.8 ns/op\t0 B/op\t0 allocs/op\nBenchmarkSumParallel-2  \t35680834\t29.04 ns/op\t0 B/op\t0 allocs/op",
    "T109": "ok  \tqfli.example/t109\t0.002s",
    "T110": "ok  \tqfli.example/t110\t0.002s",
    "T111": "ok  \tqfli.example/t111\t0.002s",
    "T114": "BenchmarkAppendNoPrealloc-2  \t1000000\t1093 ns/op\t4088 B/op\t9 allocs/op\nBenchmarkAppendPrealloc-2    \t11728428\t103.5 ns/op\t0 B/op\t0 allocs/op",
}
