// T098 哈希与校验：crypto/sha256 与 encoding/hex。
//
// SHA-256 把任意字节映射为固定的 32 字节摘要。本示例对固定输入计算摘要，
// 并与公开已知测试向量对照（"abc" 的 SHA-256 是广为人知的标准向量），
// 因此结果确定、可离线核对。
package main

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
)

func main() {
	// 已知测试向量：SHA-256("abc")
	// = ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad
	const want = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"

	sum := sha256.Sum256([]byte("abc"))
	got := hex.EncodeToString(sum[:])
	fmt.Println("sha256(abc) =", got)
	fmt.Println("matches known vector:", got == want)

	// 空串的已知向量。
	empty := sha256.Sum256(nil)
	fmt.Println("sha256(\"\") length bytes:", len(empty))
	fmt.Println("sha256(\"\") hex:", hex.EncodeToString(empty[:]))

	// 流式哈希：对分块写入的内容求和，结果与一次性相同。
	h := sha256.New()
	_, _ = h.Write([]byte("a"))
	_, _ = h.Write([]byte("bc"))
	streamed := hex.EncodeToString(h.Sum(nil))
	fmt.Println("streamed == one-shot:", streamed == got)

	// hex 解码往返。
	decoded, err := hex.DecodeString(got)
	fmt.Println("decoded bytes:", len(decoded), "err:", err)
}
