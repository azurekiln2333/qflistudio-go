package main

import (
	"bufio"
	"fmt"
	"io"
	"net/http"
	"strings"
)

func main() {
	wire := "HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nTrailer: X-Total\r\n\r\n3\r\ngo!\r\n2\r\nok\r\n0\r\nX-Total: 5\r\n\r\n"
	r, err := http.ReadResponse(bufio.NewReader(strings.NewReader(wire)), nil)
	if err != nil {
		panic(err)
	}
	before := r.Trailer.Get("X-Total")
	body, err := io.ReadAll(r.Body)
	r.Body.Close()
	if err != nil {
		panic(err)
	}
	fmt.Printf("status=%d\nbody=%s\ntrailer-before=%q\ntrailer-after=%s\n", r.StatusCode, body, before, r.Trailer.Get("X-Total"))
}
