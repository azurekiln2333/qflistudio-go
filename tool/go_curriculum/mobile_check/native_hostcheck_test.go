//go:build hostcheck

// Host-native check of the SHIPPED runtime path.
//
// This file is injected into package main (native/go_runtime) via `go test
// -overlay` (see run_native_check.sh) so it calls the real `runGo` -- the exact
// function the mobile FFI calls (vendored Yaegi fixes + projectSourceFS +
// stdlib.Symbols). It is NOT compiled into the product (build tag `hostcheck`,
// and it lives under tool/go_curriculum/mobile_check/).
//
// It runs a set of candidate single-file samples and records the interpreter's
// stdout/exit. A pass here is HOST-native interpreter evidence, still not a
// device run.
package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func TestHostNativeCandidateSamples(t *testing.T) {
	dir := os.Getenv("QFLI_HOSTCHECK_DIR")
	if dir == "" {
		t.Skip("QFLI_HOSTCHECK_DIR not set")
	}
	entries, err := os.ReadDir(dir)
	if err != nil {
		t.Fatalf("read dir: %v", err)
	}
	type record struct {
		Topic  string `json:"topic"`
		Stdout string `json:"stdout"`
		Stderr string `json:"stderr"`
		Exit   int    `json:"exit"`
	}
	var records []record
	for _, e := range entries {
		if !e.IsDir() {
			continue
		}
		project := filepath.Join(dir, e.Name())
		entry := filepath.Join(project, "main.go")
		if _, err := os.Stat(entry); err != nil {
			continue
		}
		res := runGo(project, entry)
		records = append(records, record{
			Topic: e.Name(), Stdout: res.Stdout, Stderr: res.Stderr, Exit: res.ExitCode,
		})
	}
	out := os.Getenv("QFLI_HOSTCHECK_OUT")
	if out == "" {
		out = "native-check-host.json"
	}
	data, _ := json.MarshalIndent(records, "", "  ")
	if err := os.WriteFile(out, data, 0o644); err != nil {
		t.Fatalf("write out: %v", err)
	}
	t.Logf("recorded %d topics -> %s", len(records), out)
}
