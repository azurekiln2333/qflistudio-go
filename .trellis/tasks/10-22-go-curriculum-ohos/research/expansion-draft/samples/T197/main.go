package main

import (
	"bytes"
	"fmt"
	"strings"
	"text/tabwriter"
)

func main() {
	var buffer bytes.Buffer
	writer := tabwriter.NewWriter(&buffer, 0, 4, 2, ' ', 0)
	if _, err := writer.Write([]byte("name\tqty\npen\t2\nnotebook\t12\n")); err != nil {
		panic(err)
	}
	fmt.Printf("before=%d\n", buffer.Len())
	if err := writer.Flush(); err != nil {
		panic(err)
	}
	fmt.Print(buffer.String())
	rows := strings.Split(strings.TrimSuffix(buffer.String(), "\n"), "\n")
	aligned := strings.Index(rows[0], "qty") == 10 && strings.Index(rows[1], "2") == 10 && strings.Index(rows[2], "12") == 10
	fmt.Printf("quantity-column=%t\n", aligned)
}
