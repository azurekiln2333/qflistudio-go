package main

import (
	"fmt"
	"strconv"
	"strings"
)

func parse(text string) (map[string]string, error) {
	result := map[string]string{}
	for text = strings.TrimSpace(text); text != ""; text = strings.TrimSpace(text) {
		eq := strings.IndexByte(text, '=')
		if eq < 1 {
			return nil, fmt.Errorf("missing key or equals")
		}
		key := strings.TrimSpace(text[:eq])
		text = strings.TrimSpace(text[eq+1:])
		if text == "" {
			return nil, fmt.Errorf("missing value for %s", key)
		}
		value := ""
		if text[0] == '"' {
			end, escaped := -1, false
			for i := 1; i < len(text); i++ {
				if escaped {
					escaped = false
					continue
				}
				if text[i] == '\\' {
					escaped = true
					continue
				}
				if text[i] == '"' {
					end = i
					break
				}
			}
			if end < 0 {
				return nil, fmt.Errorf("unclosed quote")
			}
			var err error
			value, err = strconv.Unquote(text[:end+1])
			if err != nil {
				return nil, err
			}
			text = text[end+1:]
			if text != "" && !strings.ContainsAny(text[:1], " \t\r\n") {
				return nil, fmt.Errorf("missing field separator")
			}
		} else {
			end := strings.IndexAny(text, " \t\r\n")
			if end < 0 {
				end = len(text)
			}
			value, text = text[:end], text[end:]
		}
		result[key] = value
	}
	return result, nil
}

func main() {
	values, err := parse(`name="Li Yu" enabled=true note="say \"hi\""`)
	if err != nil {
		panic(err)
	}
	enabled, err := strconv.ParseBool(values["enabled"])
	if err != nil {
		panic(err)
	}
	fmt.Printf("name=%s enabled=%t note=%s\n", values["name"], enabled, values["note"])
	_, err = parse(`name="unfinished`)
	fmt.Printf("unclosed=%t\n", err != nil)
	_, err = parse(`name="Lin"junk`)
	fmt.Printf("missing-separator=%t\n", err != nil)
}
