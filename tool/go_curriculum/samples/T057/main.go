// T057 错误与日志打印边界。
//
// 反模式：每一层都 log 一次，同一个错误被打印多遍，噪音大且难追踪。
// 惯例：中间层只 return（可包装），到“边界”（main、HTTP handler、job runner）
// 才记录一次日志或向用户展示。
package main

import "fmt"

// 用内存 logger 模拟，保证输出确定（生产可换 log/slog）。
type logger struct{ lines []string }

func (l *logger) Errorf(format string, args ...any) {
	l.lines = append(l.lines, fmt.Sprintf(format, args...))
}

// read 最底层：只返回错误，不记录。
func read() error { return fmt.Errorf("disk failure") }

// service 中间层：补充上下文后继续 return，不记录。
func service() error {
	if err := read(); err != nil {
		return fmt.Errorf("service: %w", err)
	}
	return nil
}

// handle 边界层：在这里记录恰好一次。
func handle(log *logger) error {
	if err := service(); err != nil {
		log.Errorf("request failed: %v", err)
		return err
	}
	return nil
}

func main() {
	log := &logger{}
	_ = handle(log)

	fmt.Println("log entries:", len(log.lines))
	for _, l := range log.lines {
		fmt.Println("  logged:", l)
	}

	// 对照反模式：若每层都记录，会出现多条重复噪音。
	antiLog := &logger{}
	if err := read(); err != nil {
		antiLog.Errorf("read: %v", err)
	}
	if err := read(); err != nil {
		antiLog.Errorf("service: %v", err)
	}
	fmt.Println("anti-pattern entries (duplicated):", len(antiLog.lines))
}
