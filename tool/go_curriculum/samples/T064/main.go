// T064 泛型三：泛型类型（容器）。
//
// 泛型不仅能用于函数，也能定义带类型参数的类型。Stack[T] 用切片存元素，
// 压栈/弹栈/判空都由同一份代码实现，实例化 Stack[int]、Stack[string] 都行。
// 泛型 = desktop only（移动端 Yaegi 未实测）。
package main

import "fmt"

// Stack 是一个后进先出（LIFO）栈。类型参数 T 是元素类型。
type Stack[T any] struct {
	items []T
}

// Push 把元素压入栈顶。
func (s *Stack[T]) Push(v T) {
	s.items = append(s.items, v)
}

// Pop 弹出栈顶元素。第二个返回值表示是否成功（空栈时 ok=false）。
func (s *Stack[T]) Pop() (T, bool) {
	var zero T
	if len(s.items) == 0 {
		return zero, false
	}
	last := len(s.items) - 1
	v := s.items[last]
	s.items = s.items[:last]
	return v, true
}

// Len 返回当前元素个数。
func (s *Stack[T]) Len() int { return len(s.items) }

func main() {
	var ints Stack[int]
	ints.Push(1)
	ints.Push(2)
	ints.Push(3)

	for ints.Len() > 0 {
		v, _ := ints.Pop()
		fmt.Println("popped int:", v)
	}
	_, ok := ints.Pop()
	fmt.Println("pop empty stack ok =", ok)

	var words Stack[string]
	words.Push("go")
	words.Push("generics")
	w, _ := words.Pop()
	fmt.Println("popped string:", w)
}
