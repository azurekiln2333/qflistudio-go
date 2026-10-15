// store_test.go 是 T118 的端到端测试：增/改/存/重载后状态一致。
// 与 main.go、store.go 同属 todoapp 包。
package main

import (
	"path/filepath"
	"testing"
)

func TestAddCompleteReload(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "todo.json")

	st, err := Load(path)
	if err != nil {
		t.Fatalf("load: %v", err)
	}
	if got := st.Add("a"); got != 1 {
		t.Fatalf("first id = %d, want 1", got)
	}
	if got := st.Add("b"); got != 2 {
		t.Fatalf("second id = %d, want 2", got)
	}
	if err := st.Complete(1); err != nil {
		t.Fatalf("complete: %v", err)
	}
	if err := st.Save(); err != nil {
		t.Fatalf("save: %v", err)
	}

	// 重载：状态必须与保存前一致。
	reloaded, err := Load(path)
	if err != nil {
		t.Fatalf("reload: %v", err)
	}
	items := reloaded.Items()
	if len(items) != 2 {
		t.Fatalf("items = %d, want 2", len(items))
	}
	if !items[0].Done || items[1].Done {
		t.Fatalf("done flags wrong: %+v", items)
	}

	// 完成不存在的 id 应报错。
	if err := reloaded.Complete(99); err == nil {
		t.Fatal("expected error for missing id")
	}
}
