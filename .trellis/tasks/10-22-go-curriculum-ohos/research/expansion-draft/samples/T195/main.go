package main

import (
	"bufio"
	"fmt"
	"strings"
)

type LineError struct {
	Line   int
	Reason string
}

func (e *LineError) Error() string { return fmt.Sprintf("line %d: %s", e.Line, e.Reason) }
func parse(text string) (map[string]map[string]string, error) {
	result := map[string]map[string]string{}
	section := ""
	scanner := bufio.NewScanner(strings.NewReader(text))
	line := 0
	for scanner.Scan() {
		line++
		row := strings.TrimSpace(scanner.Text())
		if row == "" || strings.HasPrefix(row, "#") || strings.HasPrefix(row, ";") {
			continue
		}
		if strings.HasPrefix(row, "[") {
			if !strings.HasSuffix(row, "]") {
				return nil, &LineError{line, "unclosed section"}
			}
			section = strings.TrimSpace(row[1 : len(row)-1])
			if section == "" {
				return nil, &LineError{line, "empty section"}
			}
			if result[section] == nil {
				result[section] = map[string]string{}
			}
			continue
		}
		key, value, ok := strings.Cut(row, "=")
		key = strings.TrimSpace(key)
		if !ok || key == "" || section == "" {
			return nil, &LineError{line, "invalid key-value"}
		}
		if _, exists := result[section][key]; exists {
			return nil, &LineError{line, "duplicate key"}
		}
		result[section][key] = strings.TrimSpace(value)
	}
	if err := scanner.Err(); err != nil {
		return nil, err
	}
	return result, nil
}
func main() {
	cfg, err := parse("# local\n[server]\nport=8080\n\n[ui]\ntheme=dark\n")
	if err != nil {
		panic(err)
	}
	fmt.Printf("server.port=%s ui.theme=%s\n", cfg["server"]["port"], cfg["ui"]["theme"])
	_, err = parse("[server]\nport=1\nport=2")
	problem, ok := err.(*LineError)
	fmt.Printf("duplicate-line3=%t\n", ok && problem.Line == 3)
	_, err = parse("[server]\nport")
	problem, ok = err.(*LineError)
	fmt.Printf("malformed-line2=%t\n", ok && problem.Line == 2)
}
