package main

import "fmt"

func describe(v any) string {
	switch x := v.(type) {
	case int:
		return fmt.Sprintf("int:%d", x)
	case string:
		return fmt.Sprintf("string:%s", x)
	case bool:
		return fmt.Sprintf("bool:%t", x)
	default:
		return "unknown"
	}
}

func main() {
	for _, v := range []any{1, "go", true, 3.14} {
		fmt.Println(describe(v))
	}
}
