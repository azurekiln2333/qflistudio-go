package main

import (
	"bytes"
	"flag"
	"fmt"
)

func execute(arguments []string) (string, string, error) {
	if len(arguments) == 0 {
		return "", "", fmt.Errorf("missing command")
	}
	var diagnostics bytes.Buffer
	flags := flag.NewFlagSet(arguments[0], flag.ContinueOnError)
	flags.SetOutput(&diagnostics)
	source := ""
	limit := 0
	switch arguments[0] {
	case "import":
		flags.StringVar(&source, "source", "", "source file")
	case "export":
		flags.IntVar(&limit, "limit", 10, "record limit")
	default:
		return "", "", fmt.Errorf("unknown command")
	}
	if err := flags.Parse(arguments[1:]); err != nil {
		return "", diagnostics.String(), err
	}
	if flags.NArg() != 0 {
		return "", diagnostics.String(), fmt.Errorf("unexpected positional arguments")
	}
	if arguments[0] == "import" {
		if source == "" {
			return "", "", fmt.Errorf("missing source")
		}
		return "import source=" + source, "", nil
	}
	if limit < 1 {
		return "", "", fmt.Errorf("invalid limit")
	}
	return fmt.Sprintf("export limit=%d", limit), "", nil
}
func main() {
	for _, arguments := range [][]string{{"import", "-source", "notes.json"}, {"export", "-limit", "3"}} {
		result, _, err := execute(arguments)
		if err != nil {
			panic(err)
		}
		fmt.Println(result)
	}
	_, diagnostics, err := execute([]string{"export", "-limit", "no"})
	fmt.Printf("parse-error=%t captured=%t\n", err != nil, len(diagnostics) > 0)
	_, _, err = execute([]string{"delete"})
	fmt.Printf("unknown=%t\n", err != nil)
}
