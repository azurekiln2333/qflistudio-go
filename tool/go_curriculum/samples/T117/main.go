// T117 配置、标志与环境变量。
//
// flag 解析命令行参数；环境变量常用于容器/CI 注入配置。
// 常见优先级：命令行标志优先于环境变量，环境变量优先于默认值。
// 本示例构造确定参数并打印生效配置，输出确定（不读真实环境）。
package main

import (
	"flag"
	"fmt"
	"os"
)

// config 是最终生效的配置。
type config struct {
	Addr  string
	Level string
	Port  int
}

// loadConfig 依次从默认值、环境变量、命令行标志解析配置。
func loadConfig(args []string, getenv func(string) string) (config, error) {
	c := config{Addr: "127.0.0.1", Level: "info", Port: 8080}

	// 环境变量层。
	if v := getenv("APP_ADDR"); v != "" {
		c.Addr = v
	}
	if v := getenv("APP_LEVEL"); v != "" {
		c.Level = v
	}

	// 命令行标志层（优先级最高）。
	fs := flag.NewFlagSet("demo", flag.ContinueOnError)
	addr := fs.String("addr", c.Addr, "listen address")
	level := fs.String("level", c.Level, "log level")
	port := fs.Int("port", c.Port, "listen port")
	if err := fs.Parse(args); err != nil {
		return config{}, err
	}
	c.Addr, c.Level, c.Port = *addr, *level, *port
	return c, nil
}

func main() {
	// 模拟环境变量：通过注入的 getenv 获得确定性。
	env := map[string]string{"APP_ADDR": "10.0.0.1", "APP_LEVEL": "warn"}
	getenv := func(k string) string { return env[k] }

	// 仅带命令行标志覆盖（应覆盖 env 的 addr）。
	c, err := loadConfig([]string{"-addr", "192.168.1.5", "-port", "9000"}, getenv)
	if err != nil {
		panic(err)
	}
	fmt.Printf("addr=%s level=%s port=%d\n", c.Addr, c.Level, c.Port)

	// 不带标志时，环境变量生效。
	c2, _ := loadConfig(nil, getenv)
	fmt.Printf("addr=%s level=%s port=%d\n", c2.Addr, c2.Level, c2.Port)

	// 无 env、无标志时，默认值生效。
	c3, _ := loadConfig(nil, func(string) string { return "" })
	fmt.Printf("addr=%s level=%s port=%d\n", c3.Addr, c3.Level, c3.Port)

	_ = os.Getenv // 说明真实环境变量读法；此处为确定性不直接使用。
}
