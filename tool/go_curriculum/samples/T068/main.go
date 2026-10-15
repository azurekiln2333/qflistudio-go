// T068 语义化版本与最小版本选择（MVS）。
//
// 本示例演示"最小版本选择"的决策逻辑，不联网：给定若干依赖对版本的要求，
// 计算最终选中的版本——Go 的选择规则是"满足所有要求的最小可行版本"，
// 而不是"取最大"或"取最新"。这保证构建可复现。
//
// 完整工程结构（module-project，不能一键导入）：
//   demo/
//   ├── go.mod                // module demo\n\ngo 1.27
//   ├── main.go               // 本文件
//   ├── internal/version/     // 语义化版本解析
//   │   └── version.go
//   └── internal/mvs/mvs.go   // MVS 计算
// 运行：go run .
package main

import (
	"fmt"
	"sort"
	"strconv"
	"strings"
)

// Version 是解析后的语义化版本 major.minor.patch。
type Version struct {
	Major, Minor, Patch int
}

// Parse 解析 "1.2.3" 形式的版本字符串。
func Parse(s string) (Version, error) {
	s = strings.TrimPrefix(s, "v")
	parts := strings.Split(s, ".")
	if len(parts) != 3 {
		return Version{}, fmt.Errorf("invalid version %q", s)
	}
	nums := make([]int, 3)
	for i, p := range parts {
		n, err := strconv.Atoi(p)
		if err != nil {
			return Version{}, fmt.Errorf("invalid version %q: %w", s, err)
		}
		nums[i] = n
	}
	return Version{nums[0], nums[1], nums[2]}, nil
}

// String 输出规范化的 v1.2.3 形式。
func (v Version) String() string { return fmt.Sprintf("v%d.%d.%d", v.Major, v.Minor, v.Patch) }

// Compare 按语义化版本规则比较：-1 小于，0 相等，1 大于。
func (v Version) Compare(o Version) int {
	switch {
	case v.Major != o.Major:
		return sign(v.Major - o.Major)
	case v.Minor != o.Minor:
		return sign(v.Minor - o.Minor)
	default:
		return sign(v.Patch - o.Patch)
	}
}

func sign(n int) int {
	if n < 0 {
		return -1
	}
	if n > 0 {
		return 1
	}
	return 0
}

// SelectMVS 返回满足所有约束的最小版本。
// constraints 是"每个依赖方要求的版本"列表。
func SelectMVS(constraints []Version) (Version, error) {
	if len(constraints) == 0 {
		return Version{}, fmt.Errorf("no constraints")
	}
	sorted := append([]Version(nil), constraints...)
	sort.Slice(sorted, func(i, j int) bool { return sorted[i].Compare(sorted[j]) < 0 })
	// 最小可行版本 = 所有下界中的最大者（因为每个版本都是它的下界）。
	best := sorted[0]
	for _, v := range sorted[1:] {
		if v.Compare(best) > 0 {
			best = v
		}
	}
	return best, nil
}

func main() {
	// 三个依赖方分别要求不同版本；MVS 选中满足全部要求的最小版本。
	raw := []string{"v1.2.0", "v1.5.3", "v1.4.9"}
	var cs []Version
	for _, r := range raw {
		v, err := Parse(r)
		if err != nil {
			panic(err)
		}
		cs = append(cs, v)
	}
	selected, err := SelectMVS(cs)
	if err != nil {
		panic(err)
	}
	fmt.Println("constraints:", strings.Join(raw, ", "))
	fmt.Println("selected (MVS) =", selected)

	// 对比：如果错误地"取最新/最大"，结果会不同，从而破坏最小依赖原则。
	maxV := cs[0]
	for _, v := range cs[1:] {
		if v.Compare(maxV) > 0 {
			maxV = v
		}
	}
	if maxV == selected {
		fmt.Println("此时最大版本恰好等于最小可行版本")
	}
}
