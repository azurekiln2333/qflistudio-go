package main

import (
	"path/filepath"
	"testing"
)

// These tests keep valid language/stdlib behavior independent of curriculum
// wording. A topic rewrite must not hide a regression in the shipped runtime.
func TestCurriculumLanguageCompatibility(t *testing.T) {
	for _, test := range []struct{ name, source, want string }{
		{"method_expression", `package main
import "fmt"
type rectangle struct { w, h int }
func (r rectangle) area() int { return r.w*r.h }
func main() { r := rectangle{3,4}; bound := r.area; expression := rectangle.area; fmt.Println(bound(), expression(r)) }
`, "12 12\n"},
		{"interface_field_reassignment", `package main
import "fmt"
type pricing interface { Price(int) int }
type normal struct{}
func (normal) Price(n int) int { return n }
type discount struct{}
func (discount) Price(n int) int { return n*8/10 }
type order struct { strategy pricing }
func main() { o := &order{strategy: normal{}}; fmt.Println(o.strategy.Price(100)); o.strategy = discount{}; fmt.Println(o.strategy.Price(100)) }
`, "100\n80\n"},
		{"recovered_panic_is_silent", `package main
import "fmt"
func fail() { panic("caught") }
func main() { defer func() { fmt.Println(recover()) }(); fail() }
`, "caught\n"},
		{"untyped_ordered_float", `package main
import "fmt"
import "cmp"
func max[T cmp.Ordered](a,b T) T { if a>b { return a }; return b }
func main() { fmt.Println(max(2.5,1.5), max('a','b')) }
`, "2.5 98\n"},
		{"native_error_to_source_interface", `package main
import "fmt"
import "errors"
type many interface { Unwrap() []error }
func main() { var err error = errors.Join(errors.New("one"), errors.New("two")); value, ok := err.(many); fmt.Println(ok); if ok { fmt.Println(len(value.Unwrap())) } }
`, "true\n2\n"},
		{"errors_is_pointer_identity", `package main
import "fmt"
import "errors"
type problem struct { message string }
func (p *problem) Error() string { return p.message }
func main() { var p error = &problem{"one"}; fmt.Println(errors.Is(p,p)) }
`, "true\n"},
		{"errors_as_interpreted_pointer", `package main
import "fmt"
import "errors"
type problem struct { message string }
func (p *problem) Error() string { return p.message }
func main() { var p error = &problem{"one"}; wrapped := fmt.Errorf("wrap: %w",p); var target *problem; fmt.Println(errors.As(wrapped,&target)); fmt.Println(target.message) }
`, "true\none\n"},
		{"formatter_preserves_numeric_verbs", `package main
import "fmt"
type color int
func (color) String() string { return "green" }
func main() { fmt.Printf("%v %d\n",color(1),color(1)) }
`, "green 1\n"},
		{"named_type_formatting", `package main
import "fmt"
type point struct { X,Y int }
func main() { fmt.Printf("%T %v %+v\n",point{1,2},point{1,2},point{1,2}) }
`, "main.point {1 2} {X:1 Y:2}\n"},
		{"format_width_precision_and_indices", `package main
import "fmt"
type point struct { X int }
func main() { fmt.Printf("%*.*f\n",7,2,1.25); fmt.Printf("%[2]T %[1]d\n",5,point{1}); fmt.Printf("%[1]*[1]T %%T\n",3) }
`, "   1.25\nmain.point 5\nint %T\n"},
		{"format_pointer_flags_and_variadic", `package main
import "fmt"
import "strings"
type color int
func (color) String() string { return "green" }
func main() { p := new(int); text := fmt.Sprintf("%p",p); fmt.Println(strings.HasPrefix(text,"0x"), !strings.Contains(text,"{")); fmt.Printf("%+06d\n",color(7)); args := []any{7,2,1.25}; var out strings.Builder; fmt.Fprintf(&out,"%*.*f",args...); fmt.Println(out.String()) }
`, "true true\n+00007\n   1.25\n"},
		{"format_diagnostics", `package main
import "fmt"
func main() { fmt.Printf("%d %d\n",1); fmt.Printf("%d\n",1,2); fmt.Printf("%[3]d\n",1); fmt.Printf("%*d\n","bad",2) }
`, "1 %!d(MISSING)\n1\n%!(EXTRA int=2)%!d(BADINDEX)\n%!(BADWIDTH)2\n"},
		{"source_error_assertions", `package main
import "fmt"
import "errors"
type problem struct { message string; inner error }
func (p *problem) Error() string { return p.message }
func (p *problem) Unwrap() error { return p.inner }
type other struct { message string; inner error }
func (p *other) Error() string { return p.message }
func main() { var err error = &problem{"one",errors.New("inner")}; p, ok := err.(*problem); fmt.Println(ok); if ok { fmt.Println(p.message) }; u, ok := err.(interface{Unwrap() error}); fmt.Println(ok); if ok { fmt.Println(u.Unwrap()) }; _, wrong := err.(*other); fmt.Println(wrong) }
`, "true\none\ntrue\ninner\nfalse\n"},
		{"source_error_equality", `package main
import "fmt"
type problem struct { message string }
func (p *problem) Error() string { return p.message }
type other struct { message string }
func (p *other) Error() string { return p.message }
func main() { p := &problem{"one"}; var a,b error = p,p; var c error = &other{"one"}; fmt.Println(a==b, a!=b, a==p, a==c); if a==b { fmt.Println("equal") }; if a!=b { fmt.Println("unequal") } }
`, "true false true false\nequal\n"},
		{"source_error_uncomparable", `package main
import "fmt"
type problem []string
func (problem) Error() string { return "slice" }
func main() { defer func(){ fmt.Println(recover()!=nil) }(); var a error = problem{"one"}; fmt.Println(a==a) }
`, "true\n"},
		{"error_unwrap_and_custom_is", `package main
import "fmt"
import "errors"
type problem struct { inner error }
func (p *problem) Error() string { return "outer" }
func (p *problem) Unwrap() error { return p.inner }
func (p *problem) Is(target error) bool { return target==p.inner }
func main() { inner := errors.New("inner"); var outer error = &problem{inner}; fmt.Println(errors.Unwrap(outer)==inner,errors.Is(outer,inner)); var empty *problem; var typed error = empty; fmt.Println(typed==nil,typed==empty) }
`, "true true\nfalse true\n"},
		{"errors_as_interfaces_and_wrong_source_type", `package main
import "fmt"
import "errors"
type problem struct { message string }
func (p *problem) Error() string { return p.message }
func (p *problem) Code() int { return 7 }
type other struct { message string }
func (p *other) Error() string { return p.message }
func main() { err := fmt.Errorf("wrap: %w",&problem{"one"}); var wrong *other; fmt.Println(errors.As(err,&wrong)); var coded interface{ Code() int }; fmt.Println(errors.As(err,&coded)); fmt.Println(coded.Code()); var native error; fmt.Println(errors.As(err,&native),native.Error()); fmt.Println(errors.As(nil,&wrong)) }
`, "false\ntrue\n7\ntrue wrap: one\nfalse\n"},
		{"native_interface_comparison", `package main
import "fmt"
import "errors"
func main() { var a any = 1; var b any = 1; fmt.Println(a==b,a==1,a==int64(1)); err:=errors.New("same"); var left,right error=err,err; fmt.Println(left==right,left!=right); var empty error; fmt.Println(empty==nil,left==nil); if left!=errors.New("same") { fmt.Println("distinct") } }
`, "true true false\ntrue false\ntrue false\ndistinct\n"},
		{"error_uncomparable_is_and_invalid_optional_methods", `package main
import "fmt"
import "errors"
type problem []string
func (problem) Error() string { return "slice" }
type unusual struct{}
func (unusual) Error() string { return "unusual" }
func (unusual) Is() bool { return true }
func (unusual) As() bool { return true }
func (unusual) Unwrap(int) error { return nil }
type other struct{}
func (*other) Error() string { return "other" }
func main() { var a error = problem{"one"}; fmt.Println(errors.Is(a,a)); var err error = unusual{}; fmt.Println(errors.Is(err,errors.New("missing"))); var target *other; fmt.Println(errors.As(err,&target),errors.Unwrap(err)==nil) }
`, "false\nfalse\nfalse true\n"},
		{"error_custom_is_and_as_hooks", `package main
import "fmt"
import "errors"
type problem struct { message string }
func (p *problem) Error() string { return p.message }
type redirect struct{}
func (redirect) Error() string { return "redirect" }
func (redirect) Is(target error) bool { return target.Error()=="tag" }
func (redirect) As(target any) bool { p,ok := target.(**problem); if ok { *p = &problem{"selected"} }; return ok }
func main() { var err error = redirect{}; fmt.Println(errors.Is(err,errors.New("tag"))); var target *problem; fmt.Println(errors.As(err,&target)); fmt.Println(target.message) }
`, "true\ntrue\nselected\n"},
	} {
		t.Run(test.name, func(t *testing.T) {
			project := t.TempDir()
			entry := filepath.Join(project, "main.go")
			writeGoSource(t, entry, test.source)
			result := runGo(project, entry)
			if result.ExitCode != 0 || result.Stdout != test.want || result.Stderr != "" {
				t.Fatalf("want stdout %q, empty stderr and exit 0; got %+v", test.want, result)
			}
		})
	}
}
