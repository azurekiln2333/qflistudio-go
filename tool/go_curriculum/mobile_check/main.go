// Host-side Yaegi probe for the Go curriculum.
//
// This is a CHECK-TIME helper (not product code). It interprets a single-file
// Go sample with the SAME Yaegi version the shipped mobile runtime pins
// (native/go_runtime/go.mod) and reports stdout/exit, so mobile-support claims
// can be backed by a real interpreter run instead of vendor claims.
//
// Evidence level: HOST interpreter run on the pinned Yaegi version. This is NOT
// a device/emulator run; a passing result here only means "the interpreter
// accepts and runs the sample", not "the app runs it on a phone".
//
// Usage:
//   go run ./tool/go_curriculum/mobile_check -file path/to/main.go
package main

import (
	"bytes"
	"flag"
	"fmt"
	"os"
	"path/filepath"

	"github.com/traefik/yaegi/interp"
	"github.com/traefik/yaegi/stdlib"
)

func main() {
	src := flag.String("file", "", "path to a single main.go sample")
	flag.Parse()
	if *src == "" {
		fmt.Fprintln(os.Stderr, "mobile_check: -file is required")
		os.Exit(2)
	}
	abs, err := filepath.Abs(*src)
	if err != nil {
		fmt.Fprintln(os.Stderr, "mobile_check:", err)
		os.Exit(2)
	}
	if _, err := os.Stat(abs); err != nil {
		fmt.Fprintln(os.Stderr, "mobile_check:", err)
		os.Exit(2)
	}

	var stdout, stderr bytes.Buffer
	exit := 0
	defer func() {
		if r := recover(); r != nil {
			fmt.Fprintln(&stderr, r)
			exit = 1
		}
		fmt.Print(stdout.String())
		if stderr.Len() > 0 {
			fmt.Fprintln(os.Stderr, stderr.String())
		}
		os.Exit(exit)
	}()

	interpreter := interp.New(interp.Options{
		GoPath: filepath.Dir(abs),
		Stdout: &stdout,
		Stderr: &stderr,
		Args:   []string{abs},
	})
	if err := interpreter.Use(stdlib.Symbols); err != nil {
		fmt.Fprintln(&stderr, err)
		exit = 1
		return
	}
	if _, err := interpreter.EvalPath(abs); err != nil {
		fmt.Fprintln(&stderr, err)
		exit = 1
	}
}
