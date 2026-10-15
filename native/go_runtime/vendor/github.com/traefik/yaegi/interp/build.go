package interp

import (
	"errors"
	"go/ast"
	"go/build"
	"go/build/constraint"
	"go/parser"
	"path"
	"strconv"
	"strings"
)

// buildOk returns true if a file or script matches build constraints
// as specified in https://golang.org/pkg/go/build/#hdr-Build_Constraints.
// An error from parser is returned as well.
func (interp *Interpreter) buildOk(ctx *build.Context, name, src string) (bool, error) {
	// Extract comments before the first clause
	f, err := parser.ParseFile(interp.fset, name, src, parser.PackageClauseOnly|parser.ParseComments)
	if err != nil {
		return false, err
	}
	ok, err := buildConstraintsOk(ctx, f.Comments)
	if err != nil {
		return false, err
	}
	if !ok {
		return false, nil
	}
	setYaegiTags(ctx, f.Comments)
	return true, nil
}

// buildConstraintsOk evaluates the build constraints declared by the package's
// leading comment groups.
//
// Both constraint syntaxes are honored: the modern `//go:build` expression
// (Go 1.17+) and the legacy `// +build` lines. When a file carries a
// `//go:build` line it takes precedence, matching the go command, which treats
// the two as equivalent and reads the expression form. Legacy files keep the
// original semantics: the AND of multiple `// +build` lines, each the OR of
// space-separated options, each option the AND of comma-separated tags.
//
// The comments are read from the raw `ast.Comment` text (which retains the
// `//` marker) because constraint.Parse expects a full source line;
// CommentGroup.Text strips the marker and would hide `//go:build`.
//
// An unparsable expression is returned as an error so a selected source surfaces
// a real diagnostic instead of being silently included or excluded.
func buildConstraintsOk(ctx *build.Context, comments []*ast.CommentGroup) (bool, error) {
	var plusBuild []string
	var goBuild string
	for _, g := range comments {
		for _, c := range g.List {
			// Directive text inside a block comment is documentation, even if
			// one of its lines starts with //go:build.
			if !strings.HasPrefix(c.Text, "//") {
				continue
			}
			switch {
			case constraint.IsGoBuild(c.Text):
				if goBuild != "" {
					return false, errors.New("multiple //go:build comments")
				}
				goBuild = c.Text
			case constraint.IsPlusBuild(c.Text):
				plusBuild = append(plusBuild, c.Text)
			}
		}
	}

	tagOk := func(tag string) bool { return buildTagOk(ctx, tag) }

	// A single `//go:build` expression wins over legacy `// +build` lines.
	if goBuild != "" {
		expr, err := constraint.Parse(goBuild)
		if err != nil {
			return false, err
		}
		return expr.Eval(tagOk), nil
	}

	// Legacy `// +build` lines: AND across lines, OR across space options,
	// AND across comma-separated tags.
	for _, line := range plusBuild {
		if !buildPlusLineOk(ctx, line) {
			return false, nil
		}
	}
	return true, nil
}

// buildPlusLineOk returns true if a legacy `// +build` line is satisfied.
//
// Kept separate from the expression parser so the original option/tag semantics
// (including the `go1.x` release-tag comparison) are preserved exactly.
func buildPlusLineOk(ctx *build.Context, line string) bool {
	if !constraint.IsPlusBuild(line) {
		return true
	}
	// Drop the leading comment marker and the `+build` keyword.
	body := strings.TrimSpace(line)
	body = strings.TrimSpace(strings.TrimPrefix(body, "//"))
	body = strings.TrimSpace(strings.TrimPrefix(body, "+build"))
	// In line, evaluate the OR of space-separated options.
	options := strings.Fields(body)
	if len(options) == 0 {
		// A bare `// +build` with no options excludes the file, matching go/build.
		return false
	}
	for _, o := range options {
		if buildOptionOk(ctx, o) {
			return true
		}
	}
	return false
}

// buildOptionOk return true if all comma separated tags match, false otherwise.
func buildOptionOk(ctx *build.Context, tag string) bool {
	// in option, evaluate the AND of individual tags
	for _, t := range strings.Split(tag, ",") {
		if !buildTagOk(ctx, t) {
			return false
		}
	}
	return true
}

// buildTagOk returns true if a build tag matches, false otherwise
// if first character is !, result is negated.
func buildTagOk(ctx *build.Context, s string) (r bool) {
	not := s[0] == '!'
	if not {
		s = s[1:]
	}
	switch {
	case contains(ctx.BuildTags, s):
		r = true
	case s == ctx.GOOS:
		r = true
	case s == ctx.GOARCH:
		r = true
	case len(s) > 4 && s[:4] == "go1.":
		if n, err := strconv.Atoi(s[4:]); err != nil {
			r = false
		} else {
			r = goMinorVersion(ctx) >= n
		}
	}
	if not {
		r = !r
	}
	return
}

// setYaegiTags scans a comment group for "yaegi:tags tag1 tag2 ..." lines
// and adds the corresponding tags to the interpreter build tags.
func setYaegiTags(ctx *build.Context, comments []*ast.CommentGroup) {
	for _, g := range comments {
		for _, line := range strings.Split(strings.TrimSpace(g.Text()), "\n") {
			if len(line) < 11 || line[:11] != "yaegi:tags " {
				continue
			}

			tags := strings.Split(strings.TrimSpace(line[10:]), " ")
			for _, tag := range tags {
				if !contains(ctx.BuildTags, tag) {
					ctx.BuildTags = append(ctx.BuildTags, tag)
				}
			}
		}
	}
}

func contains(tags []string, tag string) bool {
	for _, t := range tags {
		if t == tag {
			return true
		}
	}
	return false
}

// goMinorVersion returns the go minor version number.
func goMinorVersion(ctx *build.Context) int {
	current := ctx.ReleaseTags[len(ctx.ReleaseTags)-1]

	v := strings.Split(current, ".")
	if len(v) < 2 {
		panic("unsupported Go version: " + current)
	}

	m, err := strconv.Atoi(v[1])
	if err != nil {
		panic("unsupported Go version: " + current)
	}
	return m
}

// skipFile returns true if file should be skipped.
func skipFile(ctx *build.Context, p string, skipTest bool) bool {
	if !strings.HasSuffix(p, ".go") {
		return true
	}
	p = strings.TrimSuffix(path.Base(p), ".go")
	if pp := path.Base(p); strings.HasPrefix(pp, "_") || strings.HasPrefix(pp, ".") {
		return true
	}
	if skipTest && strings.HasSuffix(p, "_test") {
		return true
	}
	i := strings.Index(p, "_")
	if i < 0 {
		return false
	}
	a := strings.Split(p[i+1:], "_")
	last := len(a) - 1
	if last-1 >= 0 {
		switch x, y := a[last-1], a[last]; {
		case x == ctx.GOOS:
			if knownArch[y] {
				return y != ctx.GOARCH
			}
			return false
		case knownOs[x] && knownArch[y]:
			return true
		case knownArch[y] && y != ctx.GOARCH:
			return true
		default:
			return false
		}
	}
	if x := a[last]; knownOs[x] && x != ctx.GOOS || knownArch[x] && x != ctx.GOARCH {
		return true
	}
	return false
}

var knownOs = map[string]bool{
	"aix":       true,
	"android":   true,
	"darwin":    true,
	"dragonfly": true,
	"freebsd":   true,
	"illumos":   true,
	"ios":       true,
	"js":        true,
	"linux":     true,
	"netbsd":    true,
	"openbsd":   true,
	"plan9":     true,
	"solaris":   true,
	"wasip1":    true,
	"windows":   true,
}

var knownArch = map[string]bool{
	"386":      true,
	"amd64":    true,
	"arm":      true,
	"arm64":    true,
	"loong64":  true,
	"mips":     true,
	"mips64":   true,
	"mips64le": true,
	"mipsle":   true,
	"ppc64":    true,
	"ppc64le":  true,
	"s390x":    true,
	"wasm":     true,
}
