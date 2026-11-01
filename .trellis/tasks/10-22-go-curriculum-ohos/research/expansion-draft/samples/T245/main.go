package main

import (
	"encoding/json"
	"fmt"
	"strings"
)

type Account struct{ Name, Token string }

func (a Account) MarshalJSON() ([]byte, error) {
	type View struct {
		Name  string `json:"name"`
		Token string `json:"token"`
	}
	masked := "***"
	if len(a.Token) >= 4 {
		masked += a.Token[len(a.Token)-4:]
	}
	return json.Marshal(View{a.Name, masked})
}
func main() {
	account := Account{"Li", "secret-1234"}
	wire, err := json.Marshal(account)
	if err != nil {
		panic(err)
	}
	fmt.Println(string(wire))
	fmt.Printf("memory-intact=%t\nsecret-absent=%t\n", account.Token == "secret-1234", !strings.Contains(string(wire), "secret-"))
}
