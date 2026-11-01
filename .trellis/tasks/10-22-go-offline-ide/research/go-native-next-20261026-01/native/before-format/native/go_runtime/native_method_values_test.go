package main

import (
	"path/filepath"
	"strings"
	"testing"
)

func TestRunGoNativeMethodValuesAndExpressions(t *testing.T) {
	for _, item := range []struct{ name, source, output string }{
		{"pointer-value", `package main
import ("fmt"; "strings")
func main() {
 buffer := new(strings.Builder)
 write := buffer.WriteString
 write("bound")
 fmt.Print(buffer.String())
}`, "bound"},
		{"pointer-expression", `package main
import ("fmt"; "strings")
func main() {
 buffer := new(strings.Builder)
 write := (*strings.Builder).WriteString
 write(buffer, "expression")
 fmt.Print(buffer.String())
}`, "expression"},
		{"value-value", `package main
import ("fmt"; "time")
func main() {
 duration := 3 * time.Second
 text := duration.String
 fmt.Print(text())
}`, "3s"},
		{"interface-value", `package main
import ("fmt"; "bytes"; "io")
func main() {
 buffer := new(bytes.Buffer)
 var writer io.Writer = buffer
 write := writer.Write
 write([]byte("interface"))
 fmt.Print(buffer.String())
}`, "interface"},
		{"interface-expression", `package main
import ("fmt"; "bytes"; "io")
func main() {
 buffer := new(bytes.Buffer)
 var writer io.Writer = buffer
 write := io.Writer.Write
 write(writer, []byte("expression"))
 fmt.Print(buffer.String())
}`, "expression"},
		{"deferred-value", `package main
import ("fmt"; "bytes")
func main() {
 buffer := new(bytes.Buffer)
 defer func() { fmt.Print(buffer.String()) }()
 write := buffer.WriteString
 defer write("deferred")
}`, "deferred"},
		{"promoted-value", `package main
import ("fmt"; "bytes")
type Wrapped struct { *bytes.Buffer }
func main() {
 wrapped := Wrapped{new(bytes.Buffer)}
 var write func(string) (int, error) = wrapped.WriteString
 write("promoted")
 fmt.Print(wrapped.String())
}`, "promoted"},
		{"promoted-pointer-expression", `package main
import ("fmt"; "bytes")
type Wrapped struct { *bytes.Buffer }
func main() {
 wrapped := Wrapped{new(bytes.Buffer)}
 var write func(*Wrapped, string) (int, error) = (*Wrapped).WriteString
 write(&wrapped, "selected receiver")
 fmt.Print(wrapped.String())
}`, "selected receiver"},
		{"promoted-value-expression", `package main
import ("fmt"; "bytes")
type Wrapped struct { *bytes.Buffer }
func main() {
 wrapped := Wrapped{new(bytes.Buffer)}
 var write func(Wrapped, string) (int, error) = Wrapped.WriteString
 write(wrapped, "embedded pointer")
 fmt.Print(wrapped.String())
}`, "embedded pointer"},
		{"promoted-address-expression", `package main
import ("fmt"; "bytes")
type Wrapped struct { bytes.Buffer }
func main() {
 var wrapped Wrapped
 var write func(*Wrapped, string) (int, error) = (*Wrapped).WriteString
 write(&wrapped, "projected address")
 fmt.Print(wrapped.String())
}`, "projected address"},
		{"promoted-nested-pointer-expression", `package main
import ("fmt"; "bytes")
type Inner struct { bytes.Buffer }
type Outer struct { *Inner }
func main() {
 outer := Outer{new(Inner)}
 var write func(Outer, string) (int, error) = Outer.WriteString
 write(outer, "nested embedded address")
 fmt.Print(outer.String())
}`, "nested embedded address"},
		{"promoted-interface-expression", `package main
import ("fmt"; "bytes"; "io")
type Wrapped struct { io.Writer }
func main() {
 buffer := new(bytes.Buffer)
 wrapped := Wrapped{buffer}
 var write func(Wrapped, []byte) (int, error) = Wrapped.Write
 write(wrapped, []byte("embedded interface"))
 fmt.Print(buffer.String())
}`, "embedded interface"},
		{"promoted-deferred-expression", `package main
import ("fmt"; "bytes")
type Wrapped struct { *bytes.Buffer }
func main() {
 wrapped := Wrapped{new(bytes.Buffer)}
 defer func() { fmt.Print(wrapped.String()) }()
 var write func(*Wrapped, string) (int, error) = (*Wrapped).WriteString
 defer write(&wrapped, "deferred projection")
}`, "deferred projection"},
		{"addressable-native-pointer-value", `package main
import ("fmt"; "bytes")
func main() {
 var buffer bytes.Buffer
 write := buffer.WriteString
 write("native address")
 fmt.Print(buffer.String())
}`, "native address"},
		{"addressable-promoted-pointer-value", `package main
import ("fmt"; "bytes")
type Wrapped struct { bytes.Buffer }
func main() {
 var wrapped Wrapped
 write := wrapped.WriteString
 write("promoted address")
 fmt.Print(wrapped.String())
}`, "promoted address"},
	} {
		t.Run(item.name, func(t *testing.T) {
			project := t.TempDir()
			entry := filepath.Join(project, "main.go")
			writeGoSource(t, entry, item.source)
			result := runGo(project, entry)
			if result.ExitCode != 0 || result.Stdout != item.output || result.Stderr != "" {
				t.Fatalf("native method lost its callable signature or receiver: %+v", result)
			}
		})
	}
}

func TestRunGoNativeMethodValueRejectsIncompatibleSignature(t *testing.T) {
	project := t.TempDir()
	entry := filepath.Join(project, "main.go")
	writeGoSource(t, entry, `package main
import "strings"
func main() {
 buffer := new(strings.Builder)
 var write func(int) int = buffer.WriteString
 _ = write
}`)
	result := runGo(project, entry)
	if result.ExitCode != 1 || !strings.Contains(result.Stderr, "cannot use") {
		t.Fatalf("incompatible native method value was accepted: %+v", result)
	}
}

func TestRunGoNativeMethodExpressionRejectsImplicitReceiverAddress(t *testing.T) {
	for _, declaration := range []string{
		`var write = bytes.Buffer.WriteString`,
		`type Wrapped struct { bytes.Buffer }; var write = Wrapped.WriteString`,
		`type Inner struct { bytes.Buffer }; type Wrapped struct { Inner }; var write = Wrapped.WriteString`,
	} {
		project := t.TempDir()
		entry := filepath.Join(project, "main.go")
		writeGoSource(t, entry, "package main\nimport \"bytes\"\n"+declaration+"\nfunc main(){_ = write}\n")
		result := runGo(project, entry)
		if result.ExitCode != 1 || !strings.Contains(result.Stderr, "method") {
			t.Fatalf("method expression silently took a by-value receiver's address: %+v", result)
		}
	}
}
