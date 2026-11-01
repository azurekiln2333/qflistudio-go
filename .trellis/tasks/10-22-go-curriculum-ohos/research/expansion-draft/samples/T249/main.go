package main

import (
	"fmt"
	"strings"
)

func escape(text string) string {
	r := strings.NewReplacer("\\", "\\\\", "|", "\\|", "\r\n", "<br>", "\n", "<br>", "\r", "<br>")
	return r.Replace(text)
}
func main() {
	fmt.Println("| name | notes |")
	fmt.Println("| --- | --- |")
	for _, row := range [][2]string{{"A|B", `C:\docs`}, {"中文", "first\nsecond"}} {
		fmt.Printf("| %s | %s |\n", escape(row[0]), escape(row[1]))
	}
}
