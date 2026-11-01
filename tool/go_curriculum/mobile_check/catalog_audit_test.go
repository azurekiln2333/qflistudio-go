//go:build hostcheck

// Injected into native/go_runtime by audit_native.py using go test -overlay.
// Each invocation is a separate process: cwd, interpreter globals and leaked
// interpreted goroutines cannot contaminate the next catalog item.
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestCatalogAuditCase(t *testing.T) {
	requestPath := os.Getenv("QFLI_GO_AUDIT_REQUEST")
	responsePath := os.Getenv("QFLI_GO_AUDIT_RESPONSE")
	if requestPath == "" || responsePath == "" {
		t.Fatal("QFLI_GO_AUDIT_REQUEST and QFLI_GO_AUDIT_RESPONSE are required")
	}
	var request struct {
		ID        string `json:"id"`
		Project   string `json:"project"`
		EntryFile string `json:"entryFile"`
		TimeoutMS int    `json:"timeoutMs"`
	}
	data, err := os.ReadFile(requestPath)
	if err != nil {
		t.Fatal(err)
	}
	if err := json.Unmarshal(data, &request); err != nil {
		t.Fatal(err)
	}
	if request.ID == "" || request.TimeoutMS <= 0 {
		t.Fatal("invalid audit request")
	}
	project, err := filepath.Abs(request.Project)
	if err != nil {
		t.Fatal(err)
	}
	// The production interpreter must resolve project paths without changing
	// the host process cwd. Starting in the fixture would hide that contract.
	originalCwd, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(request.TimeoutMS)*time.Millisecond)
	defer cancel()
	started := time.Now()
	result := runGoWithContext(ctx, project, filepath.Join(project, request.EntryFile))
	if currentCwd, err := os.Getwd(); err != nil || currentCwd != originalCwd {
		result.Stderr += fmt.Sprintf("\nhost cwd changed: before=%q after=%q error=%v", originalCwd, currentCwd, err)
		result.ExitCode = 125
		t.Error(result.Stderr)
	}
	response := struct {
		ID         string    `json:"id"`
		Result     runResult `json:"result"`
		DurationMS int64     `json:"durationMs"`
		TimedOut   bool      `json:"timedOut"`
	}{request.ID, result, time.Since(started).Milliseconds(), ctx.Err() != nil}
	encoded, err := json.Marshal(response)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(responsePath, encoded, 0o600); err != nil {
		t.Fatal(err)
	}
}
