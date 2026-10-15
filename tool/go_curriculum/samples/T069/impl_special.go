//go:build special

package main

// implName 在 -tags special 时选中本文件，返回 special。
func implName() string { return "special" }

// specialImplName 与默认实现同名，保证 main.go 两种构建下都能编译。
func specialImplName() string { return "special" }
