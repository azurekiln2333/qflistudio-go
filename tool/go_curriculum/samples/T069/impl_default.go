//go:build !special

package main

// implName 默认实现（未加 -tags special 时选中本文件）。
func implName() string { return "default" }

// specialImplName 演示另一条标签分支的取值，便于单次运行对照。
func specialImplName() string { return "special" }
