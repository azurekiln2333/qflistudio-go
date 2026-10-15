// T067 包级 API 设计与向后兼容：函数选项模式（Functional Options）。
//
// 直接暴露很多参数会让 API 一旦想加参数就破坏所有调用方。
// 选项模式把"可变配置"做成 func(*Server) 类型，NewServer 接收 0..N 个选项，
// 于是未来新增选项不会改变已有调用的签名——这就是向后兼容的关键。
package main

import (
	"fmt"
	"time"
)

// Server 是一个可配置的服务器描述（此处只做结构演示，不真正监听）。
type Server struct {
	Addr         string
	ReadTimeout  time.Duration
	MaxConns     int
	EnableAccess bool
}

// Option 是作用于 *Server 的配置函数。
type Option func(*Server)

// WithAddr 返回一个设置地址的选项。
func WithAddr(addr string) Option {
	return func(s *Server) { s.Addr = addr }
}

// WithReadTimeout 返回一个设置读超时的选项。
func WithReadTimeout(d time.Duration) Option {
	return func(s *Server) { s.ReadTimeout = d }
}

// WithMaxConns 返回一个设置最大连接数的选项。
func WithMaxConns(n int) Option {
	return func(s *Server) { s.MaxConns = n }
}

// WithAccessLog 打开访问日志。
func WithAccessLog() Option {
	return func(s *Server) { s.EnableAccess = true }
}

// NewServer 先建立一组安全默认值，再依次应用调用方传入的选项。
// 未来新增 WithXxx 也只是新增一个函数，不触碰此签名。
func NewServer(opts ...Option) *Server {
	s := &Server{
		Addr:        "127.0.0.1:8080",
		ReadTimeout: 5 * time.Second,
		MaxConns:    128,
	}
	for _, opt := range opts {
		opt(s)
	}
	return s
}

func main() {
	def := NewServer()
	fmt.Printf("default: addr=%s readTimeout=%s maxConns=%d access=%v\n",
		def.Addr, def.ReadTimeout, def.MaxConns, def.EnableAccess)

	custom := NewServer(
		WithAddr("0.0.0.0:9000"),
		WithReadTimeout(30*time.Second),
		WithMaxConns(1024),
		WithAccessLog(),
	)
	fmt.Printf("custom:  addr=%s readTimeout=%s maxConns=%d access=%v\n",
		custom.Addr, custom.ReadTimeout, custom.MaxConns, custom.EnableAccess)
}
