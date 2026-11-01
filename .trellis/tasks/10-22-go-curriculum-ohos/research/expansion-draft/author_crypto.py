"""T201-T210: offline integrity, authentication and key formats."""
from author_second_half import emit

emit(201, r'''
package main
import("crypto/sha256";"encoding/hex";"fmt";"os";"path/filepath";"sort")
func digest(text string) string { sum:=sha256.Sum256([]byte(text)); return hex.EncodeToString(sum[:]) }
func validDigest(text string)bool{decoded,err:=hex.DecodeString(text);return err==nil&&len(decoded)==sha256.Size}
func main(){
 directory,err:=os.MkdirTemp("","qfli-integrity-");if err!=nil{panic(err)};defer os.RemoveAll(directory)
 for name,text:=range map[string]string{"a.txt":"alpha","b.txt":"changed"}{if err=os.WriteFile(filepath.Join(directory,name),[]byte(text),0600);err!=nil{panic(err)}}
 manifest:=map[string]string{"a.txt":digest("alpha"),"b.txt":digest("beta")}
 names:=[]string{}; for name:=range manifest { names=append(names,name) }; sort.Strings(names)
 for _,name:=range names { if !validDigest(manifest[name]){panic("invalid manifest digest")};data,err:=os.ReadFile(filepath.Join(directory,name));if err!=nil&&!os.IsNotExist(err){panic(err)};exists:=err==nil;fmt.Printf("%s exists=%t match=%t\n",name,exists,exists&&digest(string(data))==manifest[name]) }
 fmt.Printf("bad-manifest=%t\n",!validDigest("xyz"))
}
''', 'a.txt exists=true match=true\nb.txt exists=true match=false\nbad-manifest=true',
'程序先创建独占临时目录并写入两个真实文件，验证阶段用 ReadFile 读取磁盘内容，重新计算 SHA256 并与清单比较，结束时清理目录。a.txt 未改变，b.txt 的内容被替换，因此分别报告匹配与不匹配。先排序文件名再输出，避免 map 遍历顺序影响审计记录。摘要条目必须是恰好三十二字节的十六进制编码；摘要可检测变化，却不能证明清单来自可信发布者。本例文件名由程序固定，外部清单还需要独立的路径包含关系验证。',
['文件不存在和摘要不符是不同问题，不能把空内容当成不存在。','攻击者若能同时修改文件和清单，普通摘要不能提供身份认证。'],
'增加清单中存在但临时目录中缺失的 c.txt，保持按文件名排序。','只向 manifest 加入 c.txt，不创建对应文件；用 os.IsNotExist 区分缺失与其他读取错误，缺失项输出 exists=false、match=false。')

emit(202, r'''
package main
import("crypto/hmac";"crypto/sha256";"fmt")
func tag(key,message []byte) []byte { mac:=hmac.New(sha256.New,key); mac.Write(message); return mac.Sum(nil) }
func verify(key,message,want []byte) bool { return hmac.Equal(tag(key,message),want) }
func main(){
 key:=[]byte("lesson-only-shared-key"); message:=[]byte("invoice:7:1250")
 signature:=tag(key,message)
 fmt.Printf("tag-bytes=%d\nvalid=%t\ntampered=%t\nwrong-key=%t\n",len(signature),verify(key,message,signature),verify(key,[]byte("invoice:7:9250"),signature),verify([]byte("other-key"),message,signature))
}
''', 'tag-bytes=32\nvalid=true\ntampered=false\nwrong-key=false',
'HMAC 把共享密钥与消息一起用于认证。发送方计算标签，接收方用相同密钥重新计算，并通过 hmac.Equal 比较。示例分别检验原始账单、改过金额的账单和错误密钥，只有第一种通过。标签不是加密，账单仍可被读取；示例密钥只用于演示，实际密钥应从受控存储取得并定期轮换。',
['直接计算 sha256(key+message) 不能替代标准 HMAC 构造。','认证通过不阻止旧消息被重放，业务协议还需要序号或唯一请求标识。'],
'把账单序号加入消息并维护已处理序号集合。','先校验完整消息的 HMAC，再检查序号是否已出现，成功处理后才登记序号。')

emit(203, r'''
package main
import("crypto/subtle";"encoding/hex";"fmt")
func valid(input string,want []byte) bool {
 decoded,err:=hex.DecodeString(input)
 if err!=nil||len(decoded)!=len(want)||len(want)!=4 { return false }
 return subtle.ConstantTimeCompare(decoded,want)==1
}
func main(){
 token:=[]byte{0x21,0x4a,0xb0,0x09}
 for _,input:=range []string{"214ab009","214ab008","21","zzzzzzzz"} { fmt.Printf("%s=%t\n",input,valid(input,token)) }
}
''', '214ab009=true\n214ab008=false\n21=false\nzzzzzzzz=false',
'外部输入先经过十六进制解码，再检查是否符合固定四字节协议，最后比较内容。ConstantTimeCompare 只用于同长度有效字节串；格式和长度拒绝本来就是可见的协议边界。四字节仅便于阅读，不是足够强的生产认证令牌。示例同时覆盖一个正确令牌、末字节修改、长度不足与非十六进制字符。',
['常量时间比较不会修复过短、可猜测的令牌设计。','不同长度输入会提前被拒绝，不能据此宣称整个解析过程都是恒定耗时。'],
'把协议改成 32 字节令牌并增加过长输入测试。','将长度条件改为 32，使用 crypto/rand 生成令牌；只打印验证结果，不打印真实密钥材料。')

emit(204, r'''
package main
import("bytes";"crypto/aes";"crypto/cipher";"crypto/rand";"fmt")
func main(){
 key:=make([]byte,32); if _,err:=rand.Read(key);err!=nil {panic(err)}
 block,err:=aes.NewCipher(key);if err!=nil{panic(err)};gcm,err:=cipher.NewGCM(block);if err!=nil{panic(err)}
 nonce:=make([]byte,gcm.NonceSize());if _,err:=rand.Read(nonce);err!=nil{panic(err)}
 message:=[]byte("offline report"); aad:=[]byte("report:v1")
 sealed:=gcm.Seal(nil,nonce,message,aad); plain,err:=gcm.Open(nil,nonce,sealed,aad)
 fmt.Printf("roundtrip=%t\n",err==nil&&bytes.Equal(plain,message))
 sealed[len(sealed)-1]^=1;_,err=gcm.Open(nil,nonce,sealed,aad);fmt.Printf("tamper-rejected=%t\n",err!=nil)
}
''', 'roundtrip=true\ntamper-rejected=true',
'GCM 同时提供加密与认证，Seal 接收 nonce、明文和需要认证但不加密的附加数据。每次运行生成新密钥和 nonce，因此不对随机密文字节作固定断言，只验证往返一致性。翻转认证密文最后一个字节后，Open 返回错误。接收端必须先验证成功，才能使用返回的明文。',
['同一密钥下重复使用 nonce 会破坏 GCM 安全性，不能把示例 nonce 改成固定常量。','附加数据必须在解密时逐字节一致，它不会自动包含在密文中。'],
'保持密文不变，只修改附加数据，再验证认证失败。','用 report:v2 调用 Open，断言错误非 nil，并且不消费失败返回的明文。')

emit(205, r'''
package main
import("crypto/ed25519";"crypto/rand";"fmt")
func main(){
 public,private,err:=ed25519.GenerateKey(rand.Reader);if err!=nil{panic(err)}
 manifest:=[]byte("files=2;version=3");signature:=ed25519.Sign(private,manifest)
 fmt.Printf("signature-bytes=%d\nvalid=%t\nchanged=%t\n",len(signature),ed25519.Verify(public,manifest,signature),ed25519.Verify(public,[]byte("files=9;version=3"),signature))
 signature[0]^=1;fmt.Printf("bad-signature=%t\n",ed25519.Verify(public,manifest,signature))
}
''', 'signature-bytes=64\nvalid=true\nchanged=false\nbad-signature=false',
'签名者保留私钥，验证者只需要公钥。Ed25519.Sign 直接签署清单字节，Verify 同时依赖清单、公钥和签名。示例验证原清单，然后分别修改清单和签名；两种变更都会被拒绝。程序每次使用临时密钥，输出长度与真假结果保持确定。公钥本身仍需通过可信渠道分发。',
['不能把私钥放进需要公开分发的验证清单。','两个语义相同但空白不同的 JSON 字节串仍会产生不同签名输入。'],
'再生成一对密钥，用第二个公钥验证第一个私钥生成的签名。','保留原始清单和签名，只替换 Verify 的 public 参数，结果应为 false。')

emit(206, r'''
package main
import("crypto/ecdsa";"crypto/elliptic";"crypto/rand";"crypto/sha256";"fmt")
func main(){
 key,err:=ecdsa.GenerateKey(elliptic.P256(),rand.Reader);if err!=nil{panic(err)}
 digest:=sha256.Sum256([]byte("release:42"));signature,err:=ecdsa.SignASN1(rand.Reader,key,digest[:]);if err!=nil{panic(err)}
 changed:=sha256.Sum256([]byte("release:43"))
 fmt.Printf("valid=%t\nchanged=%t\nmalformed=%t\n",ecdsa.VerifyASN1(&key.PublicKey,digest[:],signature),ecdsa.VerifyASN1(&key.PublicKey,changed[:],signature),ecdsa.VerifyASN1(&key.PublicKey,digest[:],[]byte{1,2,3}))
}
''', 'valid=true\nchanged=false\nmalformed=false',
'ECDSA 的这组接口签署摘要而非原始业务文本。程序先用 SHA256 得到固定长度摘要，再使用 P256 临时密钥签署 ASN.1 编码签名。验证阶段对原摘要成功，对另一发布版本的摘要和损坏签名失败。签名长度可能变化，因此只断言认证结果。签署和验证必须约定同一种哈希算法及字节编码。',
['把原始长文本直接当 digest 传入会偏离协议约定。','手工拼接 r、s 整数不能冒充 ASN.1 签名，需要采用匹配的编码接口。'],
'修改签名中间一个字节后再调用 VerifyASN1。','复制 signature 到新切片后翻转一个字节，检查返回 false，并保留原签名仍能通过的断言。')

emit(207, r'''
package main
import("bytes";"crypto/ecdh";"crypto/rand";"fmt")
func main(){
 curve:=ecdh.P256();alice,err:=curve.GenerateKey(rand.Reader);if err!=nil{panic(err)};bob,err:=curve.GenerateKey(rand.Reader);if err!=nil{panic(err)}
 first,err:=alice.ECDH(bob.PublicKey());if err!=nil{panic(err)};second,err:=bob.ECDH(alice.PublicKey());if err!=nil{panic(err)}
 fmt.Printf("same=%t\nsecret-bytes=%d\n",bytes.Equal(first,second),len(first))
 _,err=curve.NewPublicKey([]byte{1,2,3});fmt.Printf("bad-key-rejected=%t\n",err!=nil)
}
''', 'same=true\nsecret-bytes=32\nbad-key-rejected=true',
'双方各自生成私钥，只交换公钥。Alice 的私钥配 Bob 的公钥、Bob 的私钥配 Alice 的公钥，会得到相同的共享秘密。示例不输出秘密，只检查一致性和长度，并拒绝损坏公钥编码。ECDH 本身不验证对方身份，也不直接完成应用加密；生产协议还需要身份认证与密钥派生。',
['共享秘密不可直接打印到日志或作为公开会话标识。','没有认证的公钥交换会面临中间人替换，秘密一致并不证明对方身份。'],
'将 Bob 公钥序列化后重新读取，再检查 Alice 推导的秘密是否一致。','对 bob.PublicKey().Bytes() 调用 curve.NewPublicKey，检查错误后交给 alice.ECDH。')

emit(208, r'''
package main
import("bytes";"crypto/ed25519";"crypto/rand";"crypto/x509";"encoding/pem";"fmt")
func main(){
 public,_,err:=ed25519.GenerateKey(rand.Reader);if err!=nil{panic(err)}
 der,err:=x509.MarshalPKIXPublicKey(public);if err!=nil{panic(err)}
 encoded:=pem.EncodeToMemory(&pem.Block{Type:"PUBLIC KEY",Bytes:der});block,rest:=pem.Decode(encoded)
 if block==nil||block.Type!="PUBLIC KEY"||len(rest)!=0{panic("unexpected PEM")}
 parsed,err:=x509.ParsePKIXPublicKey(block.Bytes);if err!=nil{panic(err)}
 restored,ok:=parsed.(ed25519.PublicKey)
 fmt.Printf("block=%s\nroundtrip=%t\n",block.Type,ok&&bytes.Equal(public,restored))
 bad,_:=pem.Decode([]byte("not a PEM block"));fmt.Printf("invalid-rejected=%t\n",bad==nil)
}
''', 'block=PUBLIC KEY\nroundtrip=true\ninvalid-rejected=true',
'PEM 是给 DER 二进制加上类型标签和 Base64 外壳的文本封装。这里先把 Ed25519 公钥编码为 PKIX，再写成 PUBLIC KEY 块；读取时同时验证块类型、尾随数据、DER 格式以及最终公钥具体类型。最后比较恢复后的公钥字节。仅解出 PEM 块并不表示里面的公钥数据一定有效。',
['PUBLIC KEY 与 PRIVATE KEY 的块内容和读取接口不同，不能只改标签。','ParsePKIXPublicKey 返回接口值，必须检查类型断言成功再使用。'],
'在一个正确 PEM 后追加另一个块，验证单公钥读取策略会拒绝它。','检查 pem.Decode 返回的 rest 是否仅含允许的空白；出现第二个块时返回明确错误。')

emit(209, r'''
package main
import("fmt";"hash/crc32")
func main(){
 chunks:=[][]byte{[]byte("sensor:"),[]byte("north:"),[]byte("21.5")}
 rolling:=uint32(0);all:=[]byte{}
 for _,chunk:=range chunks { rolling=crc32.Update(rolling,crc32.IEEETable,chunk);all=append(all,chunk...) }
 fmt.Printf("same=%t\n",rolling==crc32.ChecksumIEEE(all))
 all[len(all)-1]^=1;fmt.Printf("changed=%t\n",rolling!=crc32.ChecksumIEEE(all))
 fmt.Printf("empty=%d\n",crc32.ChecksumIEEE(nil))
}
''', 'same=true\nchanged=true\nempty=0',
'CRC32.Update 接收此前的校验和，因此可以沿分片连续更新，不需要为校验拼接整份大输入。示例额外拼接一份数据，仅用于与一次性 ChecksumIEEE 对照；改动最后一个字节后再次校验，结果发生变化。空输入的校验值也被明确展示。CRC 适合检测传输错误，不能代替密码学认证。',
['每个分片都从零开始计算再相加，不等于整条流的 CRC。','不同 CRC 多项式不能混用，编码端和验证端必须约定同一张表。'],
'插入一个空分片，检查最终 CRC 是否改变。','以原来的 rolling 调用 Update 并传入空切片，结果保持不变，再继续后续分片。')

emit(210, r'''
package main
import("crypto/sha256";"crypto/sha512";"fmt";"io";"strings")
func main(){
 input:="alpha\nbeta\n";small:=sha256.New();large:=sha512.New()
 copied,err:=io.Copy(io.MultiWriter(small,large),strings.NewReader(input));if err!=nil{panic(err)}
 expected:=sha256.Sum256([]byte(input))
 fmt.Printf("bytes=%d\nlengths=%d,%d\nsha256-match=%t\n",copied,len(small.Sum(nil)),len(large.Sum(nil)),fmt.Sprintf("%x",small.Sum(nil))==fmt.Sprintf("%x",expected))
}
''', 'bytes=11\nlengths=32,64\nsha256-match=true',
'MultiWriter 将每次写入交给两个哈希状态，所以源输入只读一遍即可同时得到 SHA256 和 SHA512。Copy 返回实际消费字节数，Sum(nil) 取出当前摘要而不清空哈希状态。示例核对两个摘要长度，再将流式 SHA256 与一次性计算对照。这种组合可用于离线导出时兼容不同清单格式。',
['Sum 不会重置状态，复用同一个哈希对象计算新文件前应调用 Reset。','MultiWriter 中任一目标写入失败会停止当前复制，不能忽略 Copy 的错误。'],
'复制完成后再次调用 Sum，并验证取摘要不会改变其内容。','保存第一次 Sum 的结果，再调用一次 Sum；比较两份字节并检查长度仍一致。')
