// T092 时间一：time.Time、Duration 与格式化。
//
// Go 的时间格式化不使用格式串（如 yyyy-MM-dd），而是用一个"参考时间"
// 2006-01-02 15:04:05 作为布局。本示例使用固定时区与固定时间，
// 因此输出完全确定，不依赖当前时刻。
package main

import (
	"fmt"
	"time"
)

func main() {
	// 固定时区 UTC，构造一个确定的时间点。
	loc := time.UTC
	t := time.Date(2026, 10, 12, 14, 30, 45, 0, loc)

	// 参考布局 "2006-01-02 15:04:05"。
	fmt.Println("formatted:", t.Format("2006-01-02 15:04:05"))
	fmt.Println("date only:", t.Format("2006-01-02"))
	fmt.Println("RFC3339:  ", t.Format(time.RFC3339))

	// 解析：布局必须与实际字符串一致，否则报错。
	parsed, err := time.ParseInLocation("2006-01-02 15:04:05", "2020-01-02 03:04:05", loc)
	if err != nil {
		panic(err)
	}
	fmt.Println("parsed:", parsed.Format(time.RFC3339))

	// Duration 运算：纯时长加减，与墙钟无关。
	d := 90 * time.Minute
	fmt.Println("duration:", d)
	fmt.Println("duration minutes:", d.Minutes())

	later := t.Add(d)
	diff := later.Sub(t)
	fmt.Println("add 90m ->", later.Format("15:04:05"))
	fmt.Println("diff == 90m:", diff == d)
}
