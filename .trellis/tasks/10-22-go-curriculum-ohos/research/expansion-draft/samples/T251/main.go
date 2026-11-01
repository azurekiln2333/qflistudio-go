package main

import (
	"fmt"
	"net/mail"
)

func main() {
	for _, input := range []string{`Li Yu <li@example.test>`, `reader@example.test`, `bad@@example.test`} {
		address, err := mail.ParseAddress(input)
		if err != nil {
			fmt.Println("invalid")
			continue
		}
		fmt.Printf("name=%q address=%s\n", address.Name, address.Address)
	}
	list, err := mail.ParseAddressList("a@example.test, B <b@example.test>")
	if err != nil {
		panic(err)
	}
	fmt.Printf("list=%d\n", len(list))
}
