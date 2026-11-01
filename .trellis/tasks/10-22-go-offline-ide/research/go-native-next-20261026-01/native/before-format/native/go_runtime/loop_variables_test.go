package main

import (
	"context"
	"path/filepath"
	"testing"
	"time"
)

func TestRunGoForIterationVariables(t *testing.T) {
	for _, test := range []struct{ name, body, want string }{
		{"body_mutation", `for i:=0;i<5;i++ { fmt.Print(i); if i==1 { i++ } }`, "0134"},
		{"continue_mutation", `for i:=0;i<5;i++ { fmt.Print(i); if i==1 { i++; continue } }`, "0134"},
		{"body_closures", `var fs []func()int; for i:=0;i<3;i++ { fs=append(fs,func()int{return i}) }; for _,f:=range fs { fmt.Print(f()) }`, "012"},
		{"multiple_variables", `var fs []func(); for i,j:=0,10;i<3;i,j=i+1,j+10 { fs=append(fs,func(){fmt.Printf("%d:%d;",i,j)}) }; for _,f:=range fs { f() }`, "0:10;1:20;2:30;"},
		{"tuple_variables", `pair:=func()(int,int){return 0,10}; var fs []func(); for i,j:=pair();i<3;i,j=i+1,j+10 { fs=append(fs,func(){fmt.Printf("%d:%d;",i,j)}) }; for _,f:=range fs { f() }`, "0:10;1:20;2:30;"},
		{"tuple_blank_variable", `pair:=func()(int,int){return 0,10}; var fs []func()int; for i,_:=pair();i<3;i++ { fs=append(fs,func()int{return i}) }; for _,f:=range fs { fmt.Print(f()) }`, "012"},
		{"post_closures", `var fs []func()int; for i:=0;i<3;i=func()int{fs=append(fs,func()int{return i});return i+1}() {fs=append(fs,func()int{return i})}; for _,f:=range fs { fmt.Print(f()) }`, "011223"},
		{"condition_closures", `var fs []func()int; check:=func(p *int)bool{fs=append(fs,func()int{return *p});return *p<3}; for i:=0;check(&i);i++ {} ; for _,f:=range fs { fmt.Print(f()) }`, "0123"},
		{"condition_literal_closures", `var fs []func()int; for i:=0;func()bool{fs=append(fs,func()int{return i});return i<3}();i++ {} ; for _,f:=range fs { fmt.Print(f()) }`, "0123"},
		{"empty_body", `for i:=0;i<3;i++ {};fmt.Print("finished")`, "finished"},
		{"without_post", `var fs []func()int; for i:=0;i<3; { fs=append(fs,func()int{return i});i++ }; for _,f:=range fs { fmt.Print(f()) }`, "123"},
		{"without_condition", `var fs []func()int; for i:=0;;i++ {if i==3{break};fs=append(fs,func()int{return i})}; for _,f:=range fs { fmt.Print(f()) }`, "012"},
		{"without_condition_or_post", `var fs []func()int; for i:=0;; {if i==3{break};fs=append(fs,func()int{return i});i++}; for _,f:=range fs { fmt.Print(f()) }`, "123"},
		{"assigned_variable", `var fs []func()int; i:=0; for i=0;i<3;i++ { fs=append(fs,func()int{return i}) }; for _,f:=range fs { fmt.Print(f()) }`, "333"},
		{"labeled_continue", `var fs []func()int; outer:for i:=0;i<3;i++ {fs=append(fs,func()int{return i});for {continue outer}};for _,f:=range fs{fmt.Print(f())}`, "012"},
	} {
		t.Run(test.name, func(t *testing.T) {
			project := t.TempDir()
			entry := filepath.Join(project, "main.go")
			writeGoSource(t, entry, "package main\nimport \"fmt\"\nfunc main(){"+test.body+"}\n")
			ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
			defer cancel()
			result := runGoWithContext(ctx, project, entry)
			if result.ExitCode != 0 || result.Stdout != test.want {
				t.Fatalf("loop variables: want %q, got %+v", test.want, result)
			}
		})
	}
}
