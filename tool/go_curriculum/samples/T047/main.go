// T047 组合优于继承：策略与装饰模式。
//
// Go 没有继承，用“接口 + 组合”实现行为的可替换与增强：
// 策略模式把可变的算法抽成接口，装饰模式用组合在原有行为上叠加。
package main

import (
	"fmt"
	"strings"
)

// Pricing 是价格计算策略。
type Pricing interface {
	Price(base int) int
}

// NormalPrice 原价。
type NormalPrice struct{}

func (NormalPrice) Price(base int) int { return base }

// DiscountPrice 打八折。
type DiscountPrice struct{}

func (DiscountPrice) Price(base int) int { return base * 8 / 10 }

// Order 组合一个 Pricing 策略（而非继承一个具体类）。
type Order struct {
	base     int
	strategy Pricing
}

// Total 委托给当前策略，切换策略即改变行为。
func (o *Order) Total() int { return o.strategy.Price(o.base) }

// Job 是被装饰的核心行为。
type Job interface {
	Run() string
}

// SimpleJob 基础实现。
type SimpleJob struct{ name string }

func (j SimpleJob) Run() string { return "run " + j.name }

// LogJob 是装饰器：在原有 Job 前后叠加日志（组合，而非改写 SimpleJob）。
type LogJob struct {
	inner Job
	lines *[]string
}

func (l LogJob) Run() string {
	*l.lines = append(*l.lines, "before "+l.inner.Run())
	out := l.inner.Run()
	*l.lines = append(*l.lines, "after "+l.inner.Run())
	return out
}

func main() {
	o := &Order{base: 100, strategy: NormalPrice{}}
	fmt.Println("normal total:", o.Total())

	o.strategy = DiscountPrice{} // 运行期切换策略
	fmt.Println("discount total:", o.Total())

	var lines []string
	var job Job = SimpleJob{name: "build"}
	job = LogJob{inner: job, lines: &lines} // 装饰
	fmt.Println("decorated run:", job.Run())
	fmt.Println("log lines:")
	for _, l := range lines {
		fmt.Println(" ", strings.TrimSpace(l))
	}
}
