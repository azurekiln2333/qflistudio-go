package main

import (
	"fmt"
	"io"
	"strings"
)

func main() {
	reader := io.MultiReader(strings.NewReader(""), strings.NewReader("HDR:"), strings.NewReader("go "), strings.NewReader("offline"), strings.NewReader(""))
	var output strings.Builder
	buffer := make([]byte, 3)
	for {
		n, err := reader.Read(buffer)
		if n > 0 {
			output.Write(buffer[:n])
		}
		if err == io.EOF {
			break
		}
		if err != nil {
			panic(err)
		}
	}
	fmt.Printf("combined=%s\n", output.String())
	fmt.Printf("bytes=%d\n", output.Len())
	fmt.Printf("empty-fragments=%t\n", output.String() == "HDR:go offline")
}
