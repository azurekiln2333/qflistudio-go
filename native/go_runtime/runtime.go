package main

import (
	"bytes"
	"context"
	"fmt"
	"io/fs"
	"os"
	"path"
	"path/filepath"
	"strings"
	"sync"

	"github.com/traefik/yaegi/interp"
	"github.com/traefik/yaegi/stdlib"
)

type runResult struct {
	Stdout   string `json:"stdout"`
	Stderr   string `json:"stderr"`
	ExitCode int    `json:"exitCode"`
}

const virtualProject = "src/qfli-project"

type outputBuffer struct {
	mutex sync.Mutex
	data  bytes.Buffer
}

func (buffer *outputBuffer) Write(data []byte) (int, error) {
	buffer.mutex.Lock()
	defer buffer.mutex.Unlock()
	return buffer.data.Write(data)
}

func (buffer *outputBuffer) String() string {
	buffer.mutex.Lock()
	defer buffer.mutex.Unlock()
	return buffer.data.String()
}

type projectSourceFS struct {
	root fs.FS
}

func (source projectSourceFS) Open(name string) (fs.File, error) {
	if name == virtualProject {
		return source.root.Open(".")
	}
	if strings.HasPrefix(name, virtualProject+"/") {
		return source.root.Open(strings.TrimPrefix(name, virtualProject+"/"))
	}
	return nil, fs.ErrNotExist
}

func runGo(projectPath, entryFile string) (result runResult) {
	return runGoWithContext(context.Background(), projectPath, entryFile)
}

func runGoWithContext(ctx context.Context, projectPath, entryFile string) (result runResult) {
	project, err := filepath.Abs(projectPath)
	if err != nil {
		return runResult{Stderr: err.Error(), ExitCode: 127}
	}
	entry, err := filepath.Abs(entryFile)
	if err != nil {
		return runResult{Stderr: err.Error(), ExitCode: 127}
	}
	relative, err := filepath.Rel(project, entry)
	if err != nil || relative == ".." || strings.HasPrefix(relative, ".."+string(filepath.Separator)) {
		return runResult{Stderr: "entry file is outside the project", ExitCode: 127}
	}
	if _, err := os.Stat(entry); err != nil {
		return runResult{Stderr: err.Error(), ExitCode: 127}
	}

	var stdout, stderr outputBuffer
	defer func() {
		if recovered := recover(); recovered != nil {
			fmt.Fprintln(&stderr, recovered)
			result.ExitCode = 1
		}
		result.Stdout = stdout.String()
		result.Stderr = stderr.String()
	}()

	interpreter := interp.New(interp.Options{
		GoPath:               ".",
		SourcecodeFilesystem: projectSourceFS{root: os.DirFS(project)},
		Stdout:               &stdout,
		Stderr:               &stderr,
		Args:                 []string{entry},
	})
	if err := interpreter.Use(stdlib.Symbols); err != nil {
		fmt.Fprintln(&stderr, err)
		return runResult{ExitCode: 1}
	}
	packagePath, err := filepath.Rel(project, filepath.Dir(entry))
	if err != nil {
		fmt.Fprintln(&stderr, err)
		return runResult{ExitCode: 1}
	}
	if _, err := interpreter.EvalPathWithContext(ctx, path.Join("qfli-project", filepath.ToSlash(packagePath))); err != nil {
		fmt.Fprintln(&stderr, err)
		return runResult{ExitCode: 1}
	}
	return runResult{}
}
