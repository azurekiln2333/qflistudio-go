// Classify 按符号对整数分类。此文件与 calc_test.go 同属 covertest 包，
// 演示"同一包内多个文件"如何组织测试。
package covertest

// Classify 返回 negative / zero / positive。
func Classify(n int) string {
	switch {
	case n < 0:
		return "negative"
	case n == 0:
		return "zero"
	default:
		return "positive"
	}
}
