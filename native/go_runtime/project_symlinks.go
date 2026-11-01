// Copyright 2012 The Go Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE.go-standard-library file.
// Adapted from Go 1.27.1 path/filepath/symlink.go.

package main

import (
	"errors"
	"io/fs"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"syscall"
)

// projectEvalSymlinks adapts Go's component walker to an interpreter-owned cwd.
// Keep the logical path relative while looking up its components from cwd;
// an absolute link target still replaces that logical path with an absolute one.
func projectEvalSymlinks(cwd, path string) (string, error) {
	volLen := len(filepath.VolumeName(path))
	pathSeparator := string(os.PathSeparator)

	if volLen < len(path) && os.IsPathSeparator(path[volLen]) {
		volLen++
	}
	vol := path[:volLen]
	dest := vol
	linksWalked := 0
	for start, end := volLen, volLen; start < len(path); start = end {
		for start < len(path) && os.IsPathSeparator(path[start]) {
			start++
		}
		end = start
		for end < len(path) && !os.IsPathSeparator(path[end]) {
			end++
		}

		// On Windows, "." can be a symlink.
		// We look it up, and use the value if it is absolute.
		// If not, we just return ".".
		isWindowsDot := runtime.GOOS == "windows" && path[len(filepath.VolumeName(path)):] == "."

		// The next path component is in path[start:end].
		if end == start {
			// No more path components.
			break
		} else if path[start:end] == "." && !isWindowsDot {
			// Ignore path component ".".
			continue
		} else if path[start:end] == ".." {
			// Back up to previous component if possible.
			// Note that volLen includes any leading slash.

			// Set r to the index of the last slash in dest,
			// after the volume.
			var r int
			for r = len(dest) - 1; r >= volLen; r-- {
				if os.IsPathSeparator(dest[r]) {
					break
				}
			}
			if r < volLen || dest[r+1:] == ".." {
				// Either path has no slashes
				// (it's empty or just "C:")
				// or it ends in a ".." we had to keep.
				// Either way, keep this "..".
				if len(dest) > volLen {
					dest += pathSeparator
				}
				dest += ".."
			} else {
				// Discard everything since the last slash.
				dest = dest[:r]
			}
			continue
		}

		// Ordinary path component. Add it to result.

		if len(dest) > len(filepath.VolumeName(dest)) && !os.IsPathSeparator(dest[len(dest)-1]) {
			dest += pathSeparator
		}

		dest += path[start:end]

		// Resolve symlink.

		fi, err := os.Lstat(projectSymlinkLookup(cwd, dest))
		if err != nil {
			return "", err
		}

		if fi.Mode()&fs.ModeSymlink == 0 {
			if !fi.Mode().IsDir() && end < len(path) {
				return "", syscall.ENOTDIR
			}
			continue
		}

		// Found symlink.

		linksWalked++
		if linksWalked > 255 {
			return "", errors.New("EvalSymlinks: too many links")
		}

		link, err := os.Readlink(projectSymlinkLookup(cwd, dest))
		if err != nil {
			return "", err
		}

		if isWindowsDot && !filepath.IsAbs(link) {
			// On Windows, if "." is a relative symlink,
			// just return ".".
			break
		}

		path = link + path[end:]

		v := len(filepath.VolumeName(link))
		if v > 0 {
			// Symlink to drive name is an absolute path.
			if v < len(link) && os.IsPathSeparator(link[v]) {
				v++
			}
			vol = link[:v]
			dest = vol
			end = len(vol)
		} else if len(link) > 0 && os.IsPathSeparator(link[0]) {
			// Symlink to absolute path.
			dest = link[:1]
			end = 1
			vol = link[:1]
			volLen = 1
		} else {
			// Symlink to relative path; replace last
			// path component in dest.
			var r int
			for r = len(dest) - 1; r >= volLen; r-- {
				if os.IsPathSeparator(dest[r]) {
					break
				}
			}
			if r < volLen {
				dest = vol
			} else {
				dest = dest[:r]
			}
			end = 0
		}
	}
	return projectSymlinkNormalize(cwd, filepath.Clean(dest))
}

// Do not filepath.Join here: cleaning before walking would erase link/.. and
// change which parent directory is visited. Absolute paths keep OS permissions.
func projectSymlinkLookup(cwd, name string) string {
	if filepath.IsAbs(name) {
		return name
	}
	if volume := filepath.VolumeName(name); volume != "" {
		if strings.EqualFold(volume, filepath.VolumeName(cwd)) {
			return cwd + string(os.PathSeparator) + name[len(volume):]
		}
		// A different drive retains the host OS's per-drive cwd semantics.
		return name
	}
	if len(name) > 0 && os.IsPathSeparator(name[0]) {
		return filepath.VolumeName(cwd) + name
	}
	return cwd + string(os.PathSeparator) + name
}

func projectSymlinkNormalize(cwd, name string) (string, error) {
	if runtime.GOOS != "windows" {
		return name, nil
	}
	if filepath.IsAbs(name) {
		return filepath.EvalSymlinks(name)
	}
	volume := filepath.VolumeName(name)
	leading := name[len(volume):]
	if len(volume) == 2 {
		volume = strings.ToUpper(volume)
	}
	if leading == "" {
		return volume, nil
	}
	// Windows EvalSymlinks also normalizes actual filename casing. Retain the
	// relative leading parents, and take only the ordinary component suffix
	// from the OS-normalized absolute result.
	absolute, err := filepath.EvalSymlinks(projectSymlinkLookup(cwd, name))
	if err != nil {
		return "", err
	}
	if os.IsPathSeparator(leading[0]) {
		return absolute[len(filepath.VolumeName(absolute)):], nil
	}
	var suffix []string
	for leading != "." && filepath.Base(leading) != ".." {
		suffix = append(suffix, filepath.Base(absolute))
		absolute = filepath.Dir(absolute)
		leading = filepath.Dir(leading)
	}
	result := leading
	for index := len(suffix) - 1; index >= 0; index-- {
		result = filepath.Join(result, suffix[index])
	}
	return volume + result, nil
}
