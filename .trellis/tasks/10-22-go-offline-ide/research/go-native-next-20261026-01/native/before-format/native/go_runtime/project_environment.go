package main

import (
	"io/fs"
	"os"
	"path/filepath"
	"reflect"
	"sync"
	"time"

	"github.com/traefik/yaegi/interp"
)

// Each interpreted execution starts in its selected package directory, with a
// writable temp base at the project root. Changing the host cwd or TMPDIR races
// sessions and Flutter. This is path resolution, not an OS security sandbox:
// absolute paths still have the permissions of the application process.
func useProjectEnvironment(interpreter *interp.Interpreter, project, initialDirectory string) error {
	root, err := filepath.Abs(project)
	if err != nil {
		return err
	}
	cwd, err := filepath.Abs(initialDirectory)
	if err != nil {
		return err
	}
	environment := &goProjectEnvironment{
		cwd:       cwd,
		temporary: filepath.Join(root, ".qfli", "tmp"),
	}
	return interpreter.Use(interp.Exports{
		"os/os": {
			"Getwd":   reflect.ValueOf(environment.getwd),
			"Chdir":   reflect.ValueOf(environment.chdir),
			"TempDir": reflect.ValueOf(func() string { return environment.temporary }),
			"Open":    reflect.ValueOf(func(name string) (*os.File, error) { return os.Open(environment.resolve(name)) }),
			"Create":  reflect.ValueOf(func(name string) (*os.File, error) { return os.Create(environment.resolve(name)) }),
			"OpenFile": reflect.ValueOf(func(name string, flag int, perm fs.FileMode) (*os.File, error) {
				return os.OpenFile(environment.resolve(name), flag, perm)
			}),
			"ReadFile": reflect.ValueOf(func(name string) ([]byte, error) { return os.ReadFile(environment.resolve(name)) }),
			"WriteFile": reflect.ValueOf(func(name string, data []byte, perm fs.FileMode) error {
				return os.WriteFile(environment.resolve(name), data, perm)
			}),
			"ReadDir":  reflect.ValueOf(func(name string) ([]os.DirEntry, error) { return os.ReadDir(environment.resolve(name)) }),
			"Mkdir":    reflect.ValueOf(func(name string, perm fs.FileMode) error { return os.Mkdir(environment.resolve(name), perm) }),
			"MkdirAll": reflect.ValueOf(func(name string, perm fs.FileMode) error { return os.MkdirAll(environment.resolve(name), perm) }),
			"Remove":   reflect.ValueOf(func(name string) error { return os.Remove(environment.resolve(name)) }),
			"RemoveAll": reflect.ValueOf(func(name string) error {
				// os.RemoveAll("") is a no-op. Do not turn it into deletion of cwd.
				if name == "" {
					return nil
				}
				return os.RemoveAll(environment.resolve(name))
			}),
			"Rename": reflect.ValueOf(func(old, next string) error { return os.Rename(environment.resolve(old), environment.resolve(next)) }),
			"Stat":   reflect.ValueOf(func(name string) (os.FileInfo, error) { return os.Stat(environment.resolve(name)) }),
			"Lstat":  reflect.ValueOf(func(name string) (os.FileInfo, error) { return os.Lstat(environment.resolve(name)) }),
			"Chmod":  reflect.ValueOf(func(name string, mode fs.FileMode) error { return os.Chmod(environment.resolve(name), mode) }),
			"Chtimes": reflect.ValueOf(func(name string, atime, mtime time.Time) error {
				return os.Chtimes(environment.resolve(name), atime, mtime)
			}),
			"Truncate": reflect.ValueOf(func(name string, size int64) error { return os.Truncate(environment.resolve(name), size) }),
			"Readlink": reflect.ValueOf(func(name string) (string, error) { return os.Readlink(environment.resolve(name)) }),
			"Link":     reflect.ValueOf(func(old, next string) error { return os.Link(environment.resolve(old), environment.resolve(next)) }),
			"Symlink": reflect.ValueOf(func(old, next string) error {
				// A relative symlink target is relative to the link's directory.
				return os.Symlink(old, environment.resolve(next))
			}),
			"DirFS":      reflect.ValueOf(func(name string) fs.FS { return os.DirFS(environment.resolve(name)) }),
			"CreateTemp": reflect.ValueOf(environment.createTemp),
			"MkdirTemp":  reflect.ValueOf(environment.mkdirTemp),
		},
		"io/ioutil/ioutil": {
			"ReadFile": reflect.ValueOf(func(name string) ([]byte, error) { return os.ReadFile(environment.resolve(name)) }),
			"WriteFile": reflect.ValueOf(func(name string, data []byte, perm fs.FileMode) error {
				return os.WriteFile(environment.resolve(name), data, perm)
			}),
			"ReadDir": reflect.ValueOf(func(name string) ([]os.FileInfo, error) {
				entries, err := os.ReadDir(environment.resolve(name))
				if err != nil {
					return nil, err
				}
				result := make([]os.FileInfo, 0, len(entries))
				for _, entry := range entries {
					info, err := entry.Info()
					if err != nil {
						return nil, err
					}
					result = append(result, info)
				}
				return result, nil
			}),
			"TempFile": reflect.ValueOf(environment.createTemp),
			"TempDir":  reflect.ValueOf(environment.mkdirTemp),
		},
		"path/filepath/filepath": {
			"Abs": reflect.ValueOf(func(name string) (string, error) {
				if name == "" {
					return environment.getwd()
				}
				return environment.resolve(name), nil
			}),
			"EvalSymlinks": reflect.ValueOf(func(name string) (string, error) {
				cwd, _ := environment.getwd()
				return projectEvalSymlinks(cwd, name)
			}),
			"Glob": reflect.ValueOf(func(pattern string) ([]string, error) {
				base, _ := environment.getwd()
				resolved := pattern
				if pattern != "" && !filepath.IsAbs(pattern) {
					resolved = filepath.Join(base, pattern)
				}
				matches, err := filepath.Glob(resolved)
				if err != nil || filepath.IsAbs(pattern) {
					return matches, err
				}
				for index, name := range matches {
					matches[index], err = filepath.Rel(base, name)
					if err != nil {
						return nil, err
					}
				}
				return matches, nil
			}),
			"Walk": reflect.ValueOf(func(root string, walk filepath.WalkFunc) error {
				resolved := environment.resolve(root)
				return filepath.Walk(resolved, func(name string, info fs.FileInfo, err error) error {
					return walk(projectWalkPath(root, resolved, name), info, err)
				})
			}),
			"WalkDir": reflect.ValueOf(func(root string, walk fs.WalkDirFunc) error {
				resolved := environment.resolve(root)
				return filepath.WalkDir(resolved, func(name string, entry fs.DirEntry, err error) error {
					return walk(projectWalkPath(root, resolved, name), entry, err)
				})
			}),
		},
	})
}

func projectWalkPath(root, resolved, name string) string {
	if filepath.IsAbs(root) {
		return name
	}
	if name == resolved {
		return root
	}
	relative, err := filepath.Rel(resolved, name)
	if err != nil {
		return name
	}
	return filepath.Join(root, relative)
}

type goProjectEnvironment struct {
	mutex     sync.RWMutex
	cwd       string
	temporary string
}

func (environment *goProjectEnvironment) resolve(name string) string {
	if filepath.IsAbs(name) {
		return filepath.Clean(name)
	}
	// Empty OS paths must keep their ordinary ENOENT semantics.
	if name == "" {
		return name
	}
	environment.mutex.RLock()
	defer environment.mutex.RUnlock()
	return filepath.Join(environment.cwd, name)
}

func (environment *goProjectEnvironment) getwd() (string, error) {
	environment.mutex.RLock()
	defer environment.mutex.RUnlock()
	return environment.cwd, nil
}

func (environment *goProjectEnvironment) chdir(name string) error {
	destination := environment.resolve(name)
	info, err := os.Stat(destination)
	if err != nil {
		return err
	}
	if !info.IsDir() {
		return &os.PathError{Op: "chdir", Path: name, Err: fs.ErrInvalid}
	}
	environment.mutex.Lock()
	environment.cwd = destination
	environment.mutex.Unlock()
	return nil
}

func (environment *goProjectEnvironment) tempBase(dir string) (string, error) {
	if dir != "" {
		return environment.resolve(dir), nil
	}
	if err := os.MkdirAll(environment.temporary, 0700); err != nil {
		return "", err
	}
	return environment.temporary, nil
}

func (environment *goProjectEnvironment) createTemp(dir, pattern string) (*os.File, error) {
	base, err := environment.tempBase(dir)
	if err != nil {
		return nil, err
	}
	return os.CreateTemp(base, pattern)
}

func (environment *goProjectEnvironment) mkdirTemp(dir, pattern string) (string, error) {
	base, err := environment.tempBase(dir)
	if err != nil {
		return "", err
	}
	return os.MkdirTemp(base, pattern)
}
