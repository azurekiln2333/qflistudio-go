// T118 综合项目一：命令行待办清单（CLI + JSON 持久化）。
//
// 整合：命令分发、JSON 持久化、错误处理。待办项存为 JSON 文件，
// 增/删/列/完成操作后落盘，重载后状态一致。
//
// module-project 工程例子，不能一键导入。完整结构：
//   todoapp/
//   ├── go.mod        // module todoapp\n\ngo 1.27
//   ├── main.go       // 本文件：CLI 入口
//   ├── store.go      // 文件存储
//   └── store_test.go // 端到端测试
// 运行（官方 SDK）：
//   go run . add "learn go"
//   go run . list
//   go test ./...
// desktop only（文件系统 + go test）。
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
)

// Item 是一条待办。
type Item struct {
	ID   int    `json:"id"`
	Text string `json:"text"`
	Done bool   `json:"done"`
}

// Store 是待办存储。
type Store struct {
	path  string
	items []Item
}

// Load 从文件加载；文件不存在时返回空存储。
func Load(path string) (*Store, error) {
	s := &Store{path: path}
	data, err := os.ReadFile(path)
	if os.IsNotExist(err) {
		return s, nil
	}
	if err != nil {
		return nil, err
	}
	if err := json.Unmarshal(data, &s.items); err != nil {
		return nil, fmt.Errorf("decode %s: %w", path, err)
	}
	return s, nil
}

// Save 原子落盘：先写临时文件再改名，避免半写状态。
func (s *Store) Save() error {
	if err := os.MkdirAll(filepath.Dir(s.path), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(s.items, "", "  ")
	if err != nil {
		return err
	}
	tmp := s.path + ".tmp"
	if err := os.WriteFile(tmp, data, 0o644); err != nil {
		return err
	}
	return os.Rename(tmp, s.path)
}

// Add 追加一条并返回其 id。
func (s *Store) Add(text string) int {
	id := 1
	for _, it := range s.items {
		if it.ID >= id {
			id = it.ID + 1
		}
	}
	s.items = append(s.items, Item{ID: id, Text: text})
	return id
}

// Complete 标记完成；找不到返回错误。
func (s *Store) Complete(id int) error {
	for i := range s.items {
		if s.items[i].ID == id {
			s.items[i].Done = true
			return nil
		}
	}
	return fmt.Errorf("item %d not found", id)
}

// Items 返回按 id 排序的副本，保证输出确定。
func (s *Store) Items() []Item {
	out := append([]Item(nil), s.items...)
	sort.Slice(out, func(i, j int) bool { return out[i].ID < out[j].ID })
	return out
}

func main() {
	// 演示：用临时目录中的固定文件完成一轮增改查并重载。
	dir, err := os.MkdirTemp("", "qfli-t118-")
	if err != nil {
		panic(err)
	}
	defer os.RemoveAll(dir)
	path := filepath.Join(dir, "todo.json")

	st, err := Load(path)
	if err != nil {
		panic(err)
	}
	st.Add("learn go")
	st.Add("write tests")
	if err := st.Complete(1); err != nil {
		panic(err)
	}
	if err := st.Save(); err != nil {
		panic(err)
	}

	// 重载并打印，证明持久化一致。
	reloaded, err := Load(path)
	if err != nil {
		panic(err)
	}
	for _, it := range reloaded.Items() {
		status := "todo"
		if it.Done {
			status = "done"
		}
		fmt.Printf("%d [%s] %s\n", it.ID, status, it.Text)
	}
}
