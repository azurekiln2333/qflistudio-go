package main

// This file deliberately uses only Go's syntax packages. Import resolution,
// type checking through Yaegi, and program execution are not analysis steps.
import (
	"go/ast"
	"go/format"
	"go/parser"
	"go/scanner"
	"go/token"
	"strconv"
	"unicode/utf8"
)

const goAnalysisSchemaVersion = 1
const maxGoAnalysisBytes = 4 * 1024 * 1024

type goSourceDiagnostic struct {
	StartOffset int    `json:"startOffset"`
	EndOffset   int    `json:"endOffset"`
	Message     string `json:"message"`
	Severity    string `json:"severity"`
	Source      string `json:"source"`
	Code        string `json:"code"`
}

type goSourceImport struct {
	Path        string `json:"path"`
	Alias       string `json:"alias"`
	StartOffset int    `json:"startOffset"`
	EndOffset   int    `json:"endOffset"`
}

type goSourceSymbol struct {
	Name        string `json:"name"`
	Kind        string `json:"kind"`
	Receiver    string `json:"receiver"`
	StartOffset int    `json:"startOffset"`
	EndOffset   int    `json:"endOffset"`
}

type goSourceAnalysis struct {
	SchemaVersion   int                  `json:"schemaVersion"`
	FilePath        string               `json:"filePath"`
	UTF16Length     int                  `json:"utf16Length"`
	PackageName     string               `json:"packageName"`
	Diagnostics     []goSourceDiagnostic `json:"diagnostics"`
	Imports         []goSourceImport     `json:"imports"`
	Symbols         []goSourceSymbol     `json:"symbols"`
	FormattedSource *string              `json:"formattedSource,omitempty"`
	Error           string               `json:"error,omitempty"`
}

// byteToUTF16 maps every byte boundary, including EOF, into the original text.
// Interior UTF-8 bytes point at the beginning of the rune. CR and LF remain two
// separate code units; token.Position.Column is a byte column and is not used.
func byteToUTF16(source string) []int {
	offsets := make([]int, len(source)+1)
	units := 0
	for start := 0; start < len(source); {
		r, width := utf8.DecodeRuneInString(source[start:])
		for i := start; i < start+width; i++ {
			offsets[i] = units
		}
		units++
		if r > 0xffff {
			units++
		}
		start += width
		offsets[start] = units
	}
	return offsets
}

func boundedByteOffset(offset, length int) int {
	if offset < 0 {
		return 0
	}
	if offset > length {
		return length
	}
	return offset
}

func newGoSourceAnalysis(filePath, source string) (goSourceAnalysis, []int) {
	offsets := byteToUTF16(source)
	return goSourceAnalysis{
		SchemaVersion: goAnalysisSchemaVersion,
		FilePath:      filePath,
		UTF16Length:   offsets[len(source)],
		Diagnostics:   []goSourceDiagnostic{},
		Imports:       []goSourceImport{},
		Symbols:       []goSourceSymbol{},
	}, offsets
}

// analyzeGoSource never opens filePath: it is an identity supplied by the
// editor, while source is the exact unsaved snapshot to parse.
func analyzeGoSource(filePath, source string) goSourceAnalysis {
	result, offsets := newGoSourceAnalysis(filePath, source)
	if len(source) > maxGoAnalysisBytes {
		result.Error = "Go source exceeds the 4 MiB analysis limit"
		return result
	}
	fset := token.NewFileSet()
	file, err := parser.ParseFile(fset, filePath, source,
		parser.AllErrors|parser.ParseComments|parser.SkipObjectResolution)
	result.Diagnostics = goSyntaxDiagnostics(err, source, offsets)
	if file == nil {
		return result
	}
	if file.Name != nil {
		result.PackageName = file.Name.Name
	}
	rangeOf := func(node ast.Node) (int, int) {
		start := boundedByteOffset(fset.PositionFor(node.Pos(), false).Offset, len(source))
		end := boundedByteOffset(fset.PositionFor(node.End(), false).Offset, len(source))
		return offsets[start], offsets[end]
	}
	for _, spec := range file.Imports {
		if spec.Path == nil {
			continue
		}
		path, err := strconv.Unquote(spec.Path.Value)
		if err != nil {
			continue
		}
		alias := ""
		if spec.Name != nil {
			alias = spec.Name.Name
		}
		start, end := rangeOf(spec.Path)
		result.Imports = append(result.Imports, goSourceImport{
			Path: path, Alias: alias, StartOffset: start, EndOffset: end,
		})
	}
	addSymbol := func(name *ast.Ident, kind, receiver string) {
		if name == nil {
			return
		}
		start, end := rangeOf(name)
		result.Symbols = append(result.Symbols, goSourceSymbol{
			Name: name.Name, Kind: kind, Receiver: receiver,
			StartOffset: start, EndOffset: end,
		})
	}
	for _, declaration := range file.Decls {
		switch decl := declaration.(type) {
		case *ast.FuncDecl:
			kind, receiver := "function", ""
			if decl.Recv != nil {
				kind = "method"
				if len(decl.Recv.List) > 0 {
					node := decl.Recv.List[0].Type
					start := boundedByteOffset(fset.PositionFor(node.Pos(), false).Offset, len(source))
					end := boundedByteOffset(fset.PositionFor(node.End(), false).Offset, len(source))
					receiver = source[start:end]
				}
			}
			addSymbol(decl.Name, kind, receiver)
		case *ast.GenDecl:
			for _, declarationSpec := range decl.Specs {
				switch spec := declarationSpec.(type) {
				case *ast.TypeSpec:
					addSymbol(spec.Name, "type", "")
				case *ast.ValueSpec:
					for _, name := range spec.Names {
						addSymbol(name, decl.Tok.String(), "")
					}
				}
			}
		}
	}
	return result
}

func goSyntaxDiagnostics(err error, source string, offsets []int) []goSourceDiagnostic {
	diagnostics := []goSourceDiagnostic{}
	if err == nil {
		return diagnostics
	}
	errors, ok := err.(scanner.ErrorList)
	if !ok {
		return []goSourceDiagnostic{{Message: err.Error(), Severity: "error", Source: "go/parser", Code: "syntax"}}
	}
	for _, parseError := range errors {
		start := boundedByteOffset(parseError.Pos.Offset, len(source))
		end := start
		if start < len(source) {
			_, width := utf8.DecodeRuneInString(source[start:])
			end += width
		}
		diagnostics = append(diagnostics, goSourceDiagnostic{
			StartOffset: offsets[start], EndOffset: offsets[end],
			Message: parseError.Msg, Severity: "error", Source: "go/parser", Code: "syntax",
		})
	}
	return diagnostics
}

func formatGoSource(filePath, source string) goSourceAnalysis {
	result := analyzeGoSource(filePath, source)
	if result.Error != "" || len(result.Diagnostics) != 0 {
		return result
	}
	formatted, err := format.Source([]byte(source))
	if err != nil {
		// Parse and format use the same grammar. Preserve a genuine formatter
		// failure instead of returning the original text as formatted output.
		result.Error = "Go formatting failed: " + err.Error()
		return result
	}
	text := string(formatted)
	result.FormattedSource = &text
	return result
}
