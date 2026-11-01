"""T261-T270: byte-level protocols, bounded decoding and bit sets."""
from author_second_half import emit

emit(261, r'''
package main
import("encoding/binary";"fmt";"hash/crc32")
func encode(payload []byte)[]byte{if len(payload)>1024{panic("payload budget")};frame:=make([]byte,3+len(payload)+4);frame[0]=1;binary.BigEndian.PutUint16(frame[1:3],uint16(len(payload)));copy(frame[3:],payload);binary.BigEndian.PutUint32(frame[len(frame)-4:],crc32.ChecksumIEEE(frame[:len(frame)-4]));return frame}
func decode(frame []byte)(string,error){if len(frame)<7||frame[0]!=1{return "",fmt.Errorf("version/header")};size:=int(binary.BigEndian.Uint16(frame[1:3]));if size>1024||len(frame)!=3+size+4{return "",fmt.Errorf("size")};want:=binary.BigEndian.Uint32(frame[len(frame)-4:]);if crc32.ChecksumIEEE(frame[:len(frame)-4])!=want{return "",fmt.Errorf("checksum")};return string(frame[3:3+size]),nil}
func main(){wire:=encode([]byte("hello"));text,err:=decode(wire);if err!=nil{panic(err)};fmt.Printf("payload=%s\n",text);bad:=append([]byte(nil),wire...);bad[0]=2;_,err=decode(bad);fmt.Printf("version-rejected=%t\n",err!=nil);wire[3]^=1;_,err=decode(wire);fmt.Printf("tampered=%t\n",err!=nil)}
''', 'payload=hello\nversion-rejected=true\ntampered=true',
'帧由一字节版本、两字节大端长度、载荷和四字节 CRC 构成。解码先检查最小头与版本，再核对预算和完整长度，最后验证覆盖头部与载荷的 CRC。只有全部检查通过才返回正文。复制的坏版本帧和被修改的载荷分别触发不同失败边界；CRC 只检测变化，不提供攻击者身份认证。',
['不校验完整帧长度会漏掉截断或附加数据，不能直接按声明长度切片。','CRC 不是 HMAC，恶意修改者能重算合法校验码。'],
'给 decode 增加尾部附加一个零字节的测试。','现有精确长度条件应拒绝该输入；如果要处理连续帧，需要另写返回 consumed 字节数的流解析接口。')

emit(262, r'''
package main
import("encoding/binary";"fmt")
func pack(enabled bool,scale,value uint16)(uint16,error){if scale>7||value>4095{return 0,fmt.Errorf("field overflow")};word:=scale<<12|value;if enabled{word|=1<<15};return word,nil}
func main(){word,err:=pack(true,3,1234);if err!=nil{panic(err)};var bytes [2]byte;binary.BigEndian.PutUint16(bytes[:],word);restored:=binary.BigEndian.Uint16(bytes[:]);enabled:=restored&(1<<15)!=0;scale:=(restored>>12)&7;value:=restored&0x0fff;again,err:=pack(enabled,scale,value);if err!=nil{panic(err)};fmt.Printf("enabled=%t range=%d value=%d\nwire=%x\nroundtrip=%t\n",enabled,scale,value,bytes,again==word);_,err=pack(false,8,0);fmt.Printf("overflow=%t\n",err!=nil)}
''', 'enabled=true range=3 value=1234\nwire=b4d2\nroundtrip=true\noverflow=true',
'十六位字使用最高位表示开关、接着三位表示量程、低十二位表示数值。pack 在移位之前拒绝字段超限，解码用移位和掩码隔离字段，再重新打包验证位模式一致。binary.BigEndian 明确线上的字节顺序，因此结果不依赖本机处理器字节序。位字段协议必须写清每一位的归属。',
['移位后不做掩码可能把邻近标志位混入数值。','把超范围值直接截断会静默修改业务数据，应在打包前拒绝。'],
'把开关设为 false、量程七、数值 4095，验证所有边界。','检查最高位清零，其余十五位应全为一；再测试数值 4096 被拒绝。')

emit(263, r'''
package main
import("encoding/binary";"fmt")
func encode(ids []uint64)[]byte{out:=[]byte{};previous:=uint64(0);for _,id:=range ids{if id<previous{panic("IDs not ordered")};var buffer [10]byte;n:=binary.PutUvarint(buffer[:],id-previous);out=append(out,buffer[:n]...);previous=id};return out}
func decode(wire []byte)([]uint64,error){ids:=[]uint64{};previous:=uint64(0);for len(wire)>0{delta,n:=binary.Uvarint(wire);if n<=0{return nil,fmt.Errorf("truncated or overflow varint")};if delta>^uint64(0)-previous{return nil,fmt.Errorf("ID overflow")};previous+=delta;ids=append(ids,previous);wire=wire[n:]};return ids,nil}
func main(){wire:=encode([]uint64{100,101,130,500});ids,err:=decode(wire);if err!=nil{panic(err)};fmt.Printf("ids=%v\nbytes=%d\n",ids,len(wire));_,err=decode(wire[:len(wire)-1]);fmt.Printf("truncated=%t\n",err!=nil)}
''', 'ids=[100 101 130 500]\nbytes=5\ntruncated=true',
'递增 ID 的差分通常远小于绝对值，用无符号 varint 能缩短存储。编码器保存前一个 ID，解码器累加差分恢复原序列。Uvarint 的 n 等于零表示输入不足，小于零表示编码溢出；两者都不能继续切片。即使差分本身有效，累加仍需检查 uint64 溢出。本例四个 ID 只占五字节。',
['无符号减法遇到倒序 ID 会下溢，编码前要验证单调性。','只检查 varint 本身的溢出，不检查累加结果，仍可能产生错误 ID。'],
'允许相邻重复 ID，并解释差分零如何编码。','保留 id<previous 的拒绝条件，重复值形成单字节零；解码后序列仍保持相同重复项。')

emit(264, r'''
package main
import("fmt";"strconv";"strings")
func parse(wire string)([]string,error){frames:=[]string{};for wire!=""{colon:=strings.IndexByte(wire,':');if colon<=0{return nil,fmt.Errorf("missing length")};prefix:=wire[:colon];if len(prefix)>1&&prefix[0]=='0'{return nil,fmt.Errorf("leading zero")};for _,c:=range prefix{if c<'0'||c>'9'{return nil,fmt.Errorf("bad length")}};n,err:=strconv.Atoi(prefix);if err!=nil||n>64{return nil,fmt.Errorf("length budget")};start:=colon+1;if n>=len(wire)-start||wire[start+n]!=','{return nil,fmt.Errorf("truncated or missing comma")};frames=append(frames,wire[start:start+n]);wire=wire[start+n+1:]};return frames,nil}
func main(){frames,err:=parse("3:cat,0:,6:中文,");if err!=nil{panic(err)};fmt.Printf("frames=%q\n",frames);for _,bad:=range []string{"4:cat,","3:cat;","03:cat,"}{_,err:=parse(bad);fmt.Printf("bad=%t\n",err!=nil)}}
''', 'frames=["cat" "" "中文"]\nbad=true\nbad=true\nbad=true',
'Netstring 用十进制字节长度、冒号、原始数据和逗号连接多条消息。长度使载荷可以包含分隔符或中文，零长度也有独立表示。解析器先限制长度，再验证数据后确实存在逗号，最后推进到下一帧。本例不允许长度前导零，避免同一消息存在多种可比较的文本编码。',
['中文的长度应按 UTF8 字节计算，不能把两个汉字声明成长度二。','只检查载荷够长而不检查末尾逗号，会接受错误帧边界。'],
'增加包含冒号与逗号的数据 a:b,c，验证长度五能正常解析。','构造 5:a:b,c,；解析依赖长度定位结束逗号，载荷中的标点无需转义。')

emit(265, r'''
package main
import("bytes";"fmt";"strings")
func encode(name string)([]byte,error){var out bytes.Buffer;for _,label:=range strings.Split(name,"."){if len(label)<1||len(label)>63{return nil,fmt.Errorf("label length")};for _,c:=range label{if c>127{return nil,fmt.Errorf("ASCII labels only")}};out.WriteByte(byte(len(label)));out.WriteString(label)};out.WriteByte(0);if out.Len()>255{return nil,fmt.Errorf("name too long")};return out.Bytes(),nil}
func decode(wire []byte)(string,error){labels:=[]string{};for len(wire)>0{n:=int(wire[0]);wire=wire[1:];if n==0{if len(wire)!=0{return "",fmt.Errorf("trailing data")};return strings.Join(labels,"."),nil};if n>63||len(wire)<n{return "",fmt.Errorf("bad label")};labels=append(labels,string(wire[:n]));wire=wire[n:]};return "",fmt.Errorf("missing root label")}
func main(){wire,err:=encode("www.example.test");if err!=nil{panic(err)};name,err:=decode(wire);if err!=nil{panic(err)};fmt.Printf("name=%s\nbytes=%d\n",name,len(wire));_,err=encode(strings.Repeat("a",64)+".test");fmt.Printf("long-label=%t\n",err!=nil);_,err=decode(wire[:len(wire)-1]);fmt.Printf("missing-root=%t\n",err!=nil)}
''', 'name=www.example.test\nbytes=18\nlong-label=true\nmissing-root=true',
'DNS 未压缩名字由每个标签的长度字节和内容组成，最后的零长度标签表示根。程序只处理离线 ASCII 标签编码，不发起查询，也不实现 DNS 压缩指针。单标签限制六十三字节，完整编码限制二百五十五字节；解码检查长度和终止根标签。它展示的是线格式，不应与一般主机名完整校验混为一谈。',
['DNS 标签长度字节的高位可用于压缩指针，本例遇到大于六十三的值直接拒绝。','完整 DNS 报文包含头部与其他字段，不能只把这个名字编码发送后期待得到正常响应。'],
'支持输入末尾的一个点，并保持编码结果相同。','编码前移除一个末尾点；不要把内部空标签或连续末尾点也自动吞掉。')

emit(266, r'''
package main
import("bytes";"encoding/binary";"fmt")
type Unpacker struct{Pending []byte;Failed bool}
func(u *Unpacker)Feed(chunk []byte)([]string,error){if u.Failed{return nil,fmt.Errorf("failed state")};u.Pending=append(u.Pending,chunk...);frames:=[]string{};for len(u.Pending)>=2{n:=int(binary.BigEndian.Uint16(u.Pending[:2]));if n>32{u.Failed=true;return nil,fmt.Errorf("frame budget")};if len(u.Pending)<2+n{break};frames=append(frames,string(u.Pending[2:2+n]));u.Pending=u.Pending[2+n:]};return frames,nil}
func main(){var wire bytes.Buffer;for _,text:=range []string{"cat","go"}{var header [2]byte;binary.BigEndian.PutUint16(header[:],uint16(len(text)));wire.Write(header[:]);wire.WriteString(text)};all:=wire.Bytes();u:=&Unpacker{};result:=[]string{};for _,part:=range [][]byte{all[:1],all[1:4],all[4:6],all[6:]}{frames,err:=u.Feed(part);if err!=nil{panic(err)};result=append(result,frames...)};fmt.Printf("frames=%v\npending=%d\n",result,len(u.Pending));_,err:=u.Feed([]byte{0,33});fmt.Printf("oversize=%t\n",err!=nil)}
''', 'frames=[cat go]\npending=0\noversize=true',
'网络读取边界不等于消息边界。Unpacker 保存上次未完成的头或载荷，够两字节才能读取长度，够整帧才消费，然后继续检查同一块里的后续帧。固定分片刻意切开头部与正文，最终仍得到 cat 和 go。发现超预算帧后状态永久失败，调用方不能忽略错误继续沿不可信边界解包。',
['每次 Feed 只处理一帧会漏掉同一分片中并排的多帧。','只限制单帧长度还不够，公共接口应限制单次 chunk 和总待处理字节量。'],
'增加 Finish 方法，在流结束时拒绝非空 Pending。','当 Pending 非空时返回截断错误，空时成功；不要默默丢弃半个帧头。')

emit(267, r'''
package main
import("fmt";"math/bits")
type Slots struct{Used uint64;Capacity uint}
func(s *Slots)Allocate()(int,error){if s.Capacity==0||s.Capacity>64{return -1,fmt.Errorf("capacity")};mask:=^uint64(0);if s.Capacity<64{mask=(uint64(1)<<s.Capacity)-1};free:=^s.Used&mask;if free==0{return -1,fmt.Errorf("full")};index:=bits.TrailingZeros64(free);s.Used|=uint64(1)<<uint(index);return index,nil}
func(s *Slots)Release(index uint)error{if index>=s.Capacity||s.Used&(uint64(1)<<index)==0{return fmt.Errorf("not allocated")};s.Used &^=uint64(1)<<index;return nil}
func main(){s:=&Slots{Capacity:3};values:=[]int{};for i:=0;i<3;i++{slot,err:=s.Allocate();if err!=nil{panic(err)};values=append(values,slot)};_,err:=s.Allocate();fmt.Printf("slots=%v\nfull=%t\n",values,err!=nil);if err=s.Release(1);err!=nil{panic(err)};slot,err:=s.Allocate();if err!=nil{panic(err)};fmt.Printf("reused=%d\n",slot)}
''', 'slots=[0 1 2]\nfull=true\nreused=1',
'位图的一位表示一个槽位是否占用。取反后与容量掩码相交得到空闲位，TrailingZeros64 找到最小可用编号；分配设置该位，释放清除该位。三个槽填满时明确返回错误，释放一号后下一次会复用它。这个结构不带锁，仅适合单协程或外部已有锁的场景。',
['忘记与容量掩码相交会分配到业务范围以外的高位。','全满时调用 TrailingZeros64 会得到六十四，应先检查 free 是否为零。'],
'检测重复释放并保持位图不变。','现有 Release 的已分配检查应拒绝第二次释放；保存 Used 并比较错误前后没有变化。')

emit(268, r'''
package main
import("fmt";"math/bits")
func names(set uint64)[]string{all:=[]string{"read","write","export","admin"};out:=[]string{};for i,name:=range all{if set&(uint64(1)<<uint(i))!=0{out=append(out,name)}};return out}
func main(){user:=uint64(1<<0|1<<1|1<<2);policy:=uint64(1<<0|1<<2|1<<3);intersection:=user&policy;union:=user|policy;removed:=user&^policy;fmt.Printf("allowed=%v\nunion-count=%d\nremoved=%v\n",names(intersection),bits.OnesCount64(union),names(removed));grant:=intersection&^(uint64(1)<<2);fmt.Printf("after-revoke=%v\n",names(grant))}
''', 'allowed=[read export]\nunion-count=4\nremoved=[write]\nafter-revoke=[read]',
'权限集合可以把每个明确编号的权限映射成一个位。与得到共同授权，或得到并集，&^ 得到左侧存在但右侧没有的权限。名称按固定位序导出，因此展示顺序稳定；撤销 export 只清除对应位。位图适合固定小集合，不适合任意增长且缺少版本管理的权限协议。',
['Go 的 &^ 是按位清除，不应误写成布尔非或算术减法。','权限位编号一旦用于持久化协议，重新排列名称会改变已有数据语义。'],
'为未知高位增加拒绝逻辑，不把它们静默忽略。','定义 knownMask=(1<<4)-1；输入&^knownMask 非零时返回未知权限错误。')

emit(269, r'''
package main
import("encoding/binary";"fmt";"math")
func roundtrip(value float64)(float64,[]byte){wire:=make([]byte,8);binary.BigEndian.PutUint64(wire,math.Float64bits(value));return math.Float64frombits(binary.BigEndian.Uint64(wire)),wire}
func main(){for _,value:=range []float64{1.5,math.Copysign(0,-1)}{restored,wire:=roundtrip(value);fmt.Printf("wire=%x same-bits=%t negative=%t\n",wire,math.Float64bits(value)==math.Float64bits(restored),math.Signbit(restored))}}
''', 'wire=3ff8000000000000 same-bits=true negative=false\nwire=8000000000000000 same-bits=true negative=true',
'Float64bits 暴露 IEEE754 的六十四位表示，再用固定大端字节序写入八字节协议。恢复时先还原整数位模式，再调用 Float64frombits。示例特别覆盖负零：它与正零数值相等，但符号位不同，因此往返检查应比较位模式。对于 NaN，普通相等比较也无法表达位级保存要求。',
['把 float64 直接转换成 uint64 是数值转换，不是取得 IEEE754 位模式。','浮点相等不能区分正零和负零，也不能用于验证 NaN 的逐位往返。'],
'加入正无穷和一个自定义 NaN 位模式。','使用 math.Inf 和 Float64frombits 构造输入，始终以 Float64bits 比较恢复结果，另外检查 IsInf 或 IsNaN。')

emit(270, r'''
package main
import("encoding/binary";"fmt")
func zigzag(value int64)uint64{return uint64(value<<1)^uint64(value>>63)}
func restore(value uint64)int64{return int64(value>>1)^-int64(value&1)}
func main(){for _,value:=range []int64{0,-1,1,-2,2,-9223372036854775808,9223372036854775807}{encoded:=zigzag(value);var buffer [10]byte;n:=binary.PutUvarint(buffer[:],encoded);read,size:=binary.Uvarint(buffer[:n]);fmt.Printf("%d zigzag=%d bytes=%d same=%t\n",value,encoded,n,size==n&&restore(read)==value)}}
''', '0 zigzag=0 bytes=1 same=true\n-1 zigzag=1 bytes=1 same=true\n1 zigzag=2 bytes=1 same=true\n-2 zigzag=3 bytes=1 same=true\n2 zigzag=4 bytes=1 same=true\n-9223372036854775808 zigzag=18446744073709551615 bytes=10 same=true\n9223372036854775807 zigzag=18446744073709551614 bytes=10 same=true',
'ZigZag 把零附近的正负整数交错映射为小无符号整数，再用 Uvarint 编码，使小负数也只占一个字节。恢复公式由最低位决定符号，再右移还原绝对大小。示例既覆盖零附近，也覆盖 int64 两端，核对 varint 消费长度和原值一致。它改变表示方式，不是加密或通用压缩器。',
['直接把负 int64 转成 uint64 会得到很大的无符号数，失去小负数的空间收益。','恢复时的移位必须对无符号编码值进行，不能混入错误的符号扩展。'],
'对 -100 到 100 全部整数检查往返，并统计平均编码字节数。','循环每个整数进行 PutUvarint/Uvarint 和 restore，累计 n；明确平均值的取整与展示规则。')
