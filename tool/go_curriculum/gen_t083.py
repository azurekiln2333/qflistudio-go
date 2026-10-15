#!/usr/bin/env python3
"""Regenerate T083 after making its assertions deterministic."""
from author import build_topic, write_topic

write_topic(build_topic(
    topic_id="T083", level="intermediate",
    title="context 二：超时与截止时间",
    summary="用 WithTimeout 在指定时长后自动取消，断言超时是否发生而非具体耗时。",
    concepts=["context", "WithTimeout", "DeadlineExceeded"],
    objective="能用 context.WithTimeout 让任务在截止时间后取消，并用 errors.Is 判断 DeadlineExceeded。",
    prerequisites=["T082 context 取消与传播"],
    pitfalls=[
        "把超时当成「一定会等满给定时长」：WithTimeout 只是设置截止时间，若任务在到期前完成则不会超时；断言具体耗时会让测试在不同机器上不稳定。",
        "忘记调用 cancel：WithTimeout 返回的 cancel 必须 defer 调用以释放定时器资源，否则可能造成 goroutine/定时器泄漏。",
    ],
    exercises=[{
        "prompt": "把慢任务的超时从 1 改为 50（纳秒），观察 slow 分支仍走超时，并解释为什么这个分支是确定性的。",
        "hint": "慢任务用永不就绪的 channel 等待，超时一定先触发。",
        "answer": "只要超时为正、等待方永不就绪，Done() 必然先于任务完成触发，因此超时分支确定发生，与具体时长无关。",
    }],
    explain="context.WithTimeout(parent, d) 返回一个带截止时间的子 context 和 cancel：到达 d 后子 context 自动取消，Err() 返回 DeadlineExceeded。它常用于给下游调用设置上限，避免无限等待。\n\n关键是把断言建立在语义结果而非墙钟：样例的慢任务用一个永不就绪的 channel 等待，超时分支必然先触发，因此 slow 分支的输出与机器速度无关；「未取消」路径用不会被取消的 context 顺序返回 42；「已取消」路径显式 cancel 后立即得到 context.Canceled。三条路径都不依赖调度竞速或真实 sleep。\n\n无论超时多短，只要等待方永不就绪，超时一定先发生——这就是确定性断言的依据。",
    output="slow: deadline exceeded = true\nok: result = 42 err = <nil>\ncanceled: err is context canceled = true",
    example_title="超时判定",
    example_summary="用 WithTimeout 触发超时分支，并断言 errors.Is(..., DeadlineExceeded)。",
    example_code="package main\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"fmt\"\n\t\"time\"\n)\n\nfunc main() {\n\tctx, cancel := context.WithTimeout(context.Background(), time.Millisecond)\n\tdefer cancel()\n\tselect {\n\tcase <-ctx.Done():\n\t\tfmt.Println(\"deadline exceeded =\", errors.Is(ctx.Err(), context.DeadlineExceeded))\n\tcase <-time.After(time.Second):\n\t\tfmt.Println(\"finished in time\")\n\t}\n}\n",
    example_expected="deadline exceeded = true",
))
print("wrote T083")
