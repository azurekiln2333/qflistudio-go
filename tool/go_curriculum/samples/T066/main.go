// T066 依赖注入：显式传递优于全局。
//
// 反例：handler 里直接调用 time.Now() 或某个全局单例，测试无法替换、结果不可控。
// 正例：把"时钟"抽象成接口，由构造函数注入。生产用 realClock，测试注入固定时钟，
// 于是同一份业务逻辑既能在真实环境运行，也能在测试中得到确定结果。
package main

import (
	"fmt"
	"time"
)

// Clock 抽象"现在几点"，是唯一的外部依赖。
type Clock interface {
	Now() time.Time
}

// realClock 是生产实现。
type realClock struct{}

func (realClock) Now() time.Time { return time.Now() }

// fixedClock 是测试/演示用的确定性实现。
type fixedClock struct{ t time.Time }

func (c fixedClock) Now() time.Time { return c.t }

// Greeter 通过构造函数接收 Clock，而不是自己去 new 或读全局变量。
type Greeter struct {
	clock Clock
}

// NewGreeter 是唯一组装依赖的地方。
func NewGreeter(c Clock) *Greeter { return &Greeter{clock: c} }

// Greeting 使用注入的时钟；逻辑本身不关心时间从哪来。
func (g *Greeter) Greeting(name string) string {
	hour := g.clock.Now().Hour()
	part := "上午好"
	switch {
	case hour < 6:
		part = "凌晨好"
	case hour < 12:
		part = "上午好"
	case hour < 18:
		part = "下午好"
	default:
		part = "晚上好"
	}
	return fmt.Sprintf("%s，%s", part, name)
}

func main() {
	// 演示：注入固定时钟，输出完全确定（不受运行时刻影响）。
	noon := time.Date(2026, 10, 12, 14, 0, 0, 0, time.UTC)
	g := NewGreeter(fixedClock{t: noon})
	fmt.Println(g.Greeting("gopher"))

	morning := NewGreeter(fixedClock{t: time.Date(2026, 10, 12, 8, 0, 0, 0, time.UTC)})
	fmt.Println(morning.Greeting("gopher"))

	// 生产环境换成 realClock 即可，Greeter 代码一行不改。
	_ = realClock{}
}
