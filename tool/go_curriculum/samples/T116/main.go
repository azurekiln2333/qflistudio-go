// T116 日志与可观测性基线：log/slog。
//
// log/slog（Go 1.21+）提供结构化日志：键值对可被机器检索。
// 可设置级别（Info/Warn/Error），并选择 Text 或 JSON handler。
//
// 为让输出确定且可被任何运行环境捕获，本示例把日志写入 bytes.Buffer
// （而非直接写 os.Stdout），并用 ReplaceAttr 去掉默认的时间戳字段——
// 日志时间依赖运行时刻，不能作为固定输出。
package main

import (
	"bytes"
	"fmt"
	"log/slog"
)

// dropTime 删除 slog 默认的 time 属性，使输出与运行时刻无关。
func dropTime(_ []string, a slog.Attr) slog.Attr {
	if a.Key == slog.TimeKey {
		return slog.Attr{} // 空 Attr 会被忽略
	}
	return a
}

func main() {
	var buf bytes.Buffer
	opts := &slog.HandlerOptions{Level: slog.LevelInfo, ReplaceAttr: dropTime}

	// Text handler，级别 Info；输出写入内存缓冲。
	logger := slog.New(slog.NewTextHandler(&buf, opts))

	logger.Info("server starting", "addr", "127.0.0.1:8080", "pid", 1)
	logger.With("component", "db").Warn("slow query", "ms", 120)
	logger.Debug("this is filtered out") // 低于 Info，被过滤

	// JSON handler，级别 Error；同一缓冲区继续追加。
	jsonLogger := slog.New(slog.NewJSONHandler(&buf, &slog.HandlerOptions{
		Level:       slog.LevelError,
		ReplaceAttr: dropTime,
	}))
	jsonLogger.Error("failed to connect", "host", "db1")

	logger.Info("shutdown complete")

	// 一次性打印全部结构化日志，输出确定。
	fmt.Print(buf.String())
}
