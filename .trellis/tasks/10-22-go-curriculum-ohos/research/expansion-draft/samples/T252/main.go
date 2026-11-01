package main

import (
	"fmt"
	"net"
)

func main() {
	_, subnet, err := net.ParseCIDR("192.0.2.0/24")
	if err != nil {
		panic(err)
	}
	for _, text := range []string{"192.0.2.0", "192.0.2.255", "192.0.3.1", "not-ip"} {
		ip := net.ParseIP(text)
		fmt.Printf("%s valid=%t member=%t\n", text, ip != nil, ip != nil && subnet.Contains(ip))
	}
	ip := net.ParseIP("2001:db8::1")
	_, v6, err := net.ParseCIDR("2001:db8::/32")
	if err != nil {
		panic(err)
	}
	fmt.Printf("ipv6=%t\n", v6.Contains(ip))
}
