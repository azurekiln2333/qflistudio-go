package main

import (
	"bytes"
	"context"
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"io/fs"
	"os"
	"path"
	"path/filepath"
	"runtime"
	"sort"
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
	// entryDir is the project-relative, slash-separated directory of the
	// selected entry. Only this directory's listing is filtered.
	entryDir string
	// excluded holds base file names in entryDir that declare a competing
	// top-level main and must not be visible to the interpreter package import.
	excluded map[string]bool
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

// ReadDir satisfies fs.ReadDirFS, which io/fs.ReadDir prefers over Open. It
// hides only competing top-level main files in the selected entry directory so
// Yaegi's directory import compiles the selected entry with every other helper,
// imported subpackage and build-constrained file intact.
func (source projectSourceFS) ReadDir(name string) ([]fs.DirEntry, error) {
	root := source.rootPath(name)
	if root == "" {
		return nil, fs.ErrNotExist
	}
	entries, err := fs.ReadDir(source.root, root)
	if err != nil {
		return nil, err
	}
	if root != source.entryDir {
		return entries, nil
	}
	filtered := make([]fs.DirEntry, 0, len(entries))
	for _, entry := range entries {
		if source.excluded[entry.Name()] {
			continue
		}
		filtered = append(filtered, entry)
	}
	return filtered, nil
}

// rootPath maps a virtual path to a path under the project root, or "" when it
// is outside the virtual project.
func (source projectSourceFS) rootPath(name string) string {
	if name == virtualProject {
		return "."
	}
	if strings.HasPrefix(name, virtualProject+"/") {
		return strings.TrimPrefix(name, virtualProject+"/")
	}
	return ""
}

// fileFacts holds the package clause and whether a receiver-free top-level
// main function is declared.
type fileFacts struct {
	packageName string
	hasMain     bool
}

// isRunnableEntry reports whether the file is a package main entry.
func (facts fileFacts) isRunnableEntry() bool {
	return facts.packageName == "main" && facts.hasMain
}

// parseFileFacts parses path and reports its package name and whether it
// declares a receiver-free top-level main. Keep partial AST facts on syntax
// errors so an unfinished competing program can still be identified. The
// selected entry must always surface its parse error before using these facts.
func parseFileFacts(path string) (fileFacts, error) {
	file, err := parser.ParseFile(token.NewFileSet(), path, nil, parser.SkipObjectResolution)
	facts := fileFacts{}
	if file == nil {
		return facts, err
	}
	if file.Name != nil {
		facts.packageName = file.Name.Name
	}
	for _, decl := range file.Decls {
		fn, ok := decl.(*ast.FuncDecl)
		if !ok || fn.Recv != nil || fn.Name == nil {
			continue
		}
		if fn.Name.Name == "main" {
			facts.hasMain = true
			break
		}
	}
	return facts, err
}

// competingMainFiles returns the base names of non-entry package main siblings
// in dir that declare a top-level main function, using go/parser so comments,
// strings and method names never count. A partial AST may identify an unfinished
// competing main, which is still another program. Unidentified files and helpers
// stay in the normal interpreter view for build filtering and diagnostics.
func competingMainFiles(dir, entryName string) ([]string, error) {
	entries, err := os.ReadDir(dir)
	if err != nil {
		return nil, err
	}
	var competing []string
	for _, entry := range entries {
		name := entry.Name()
		if entry.IsDir() || name == entryName || (runtime.GOOS == "windows" && strings.EqualFold(name, entryName)) {
			continue
		}
		if !strings.HasSuffix(name, ".go") || strings.HasPrefix(name, "_") || strings.HasPrefix(name, ".") {
			continue
		}
		if strings.HasSuffix(name, "_test.go") {
			continue
		}
		facts, _ := parseFileFacts(filepath.Join(dir, name))
		if facts.isRunnableEntry() {
			competing = append(competing, name)
		}
	}
	sort.Strings(competing)
	return competing, nil
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

	entryDirectory := filepath.Dir(entry)
	entryFacts, err := parseFileFacts(entry)
	if err != nil {
		// A malformed selected source is a real diagnostic, not a missing entry.
		return runResult{Stderr: err.Error(), ExitCode: 1}
	}
	if !entryFacts.isRunnableEntry() {
		return runResult{
			Stderr:   fmt.Sprintf("no main function in %s; cannot use it as the Go entry.", filepath.Base(entry)),
			ExitCode: 1,
		}
	}

	packagePath, err := filepath.Rel(project, entryDirectory)
	if err != nil {
		return runResult{Stderr: err.Error(), ExitCode: 127}
	}
	packagePath = filepath.ToSlash(packagePath)

	var stdout, stderr outputBuffer
	defer func() {
		if recovered := recover(); recovered != nil {
			fmt.Fprintln(&stderr, recovered)
			result.ExitCode = 1
		}
		result.Stdout = stdout.String()
		result.Stderr = stderr.String()
	}()

	excluded := make(map[string]bool)
	competing, err := competingMainFiles(entryDirectory, filepath.Base(entry))
	if err != nil {
		fmt.Fprintln(&stderr, err)
		return runResult{ExitCode: 1}
	}
	for _, name := range competing {
		excluded[name] = true
	}

	interpreter := interp.New(interp.Options{
		GoPath: ".",
		SourcecodeFilesystem: projectSourceFS{
			root:     os.DirFS(project),
			entryDir: packagePath,
			excluded: excluded,
		},
		Stdout: &stdout,
		Stderr: &stderr,
		Args:   []string{entry},
	})
	if err := interpreter.Use(stdlib.Symbols); err != nil {
		fmt.Fprintln(&stderr, err)
		return runResult{ExitCode: 1}
	}
	importPath := path.Join("qfli-project", packagePath)
	if _, err := interpreter.EvalPathWithContext(ctx, importPath); err != nil {
		fmt.Fprintln(&stderr, err)
		return runResult{ExitCode: 1}
	}

	// Yaegi permits a package containing only helpers to finish successfully.
	// Resolve main in the already evaluated package to detect an entry excluded
	// by Yaegi's own filename/build rules. Importing the cached package and
	// taking the function reference do not invoke main a second time.
	if _, err := interpreter.Eval(fmt.Sprintf("import qfliRunEntry %q", importPath)); err != nil {
		fmt.Fprintln(&stderr, err)
		return runResult{ExitCode: 1}
	}
	if _, err := interpreter.Eval("qfliRunEntry.main"); err != nil {
		fmt.Fprintf(&stderr, "selected entry %s is excluded from the Go package by its filename or build constraints: %v\n", filepath.Base(entry), err)
		return runResult{ExitCode: 1}
	}
	return runResult{}
}
