"""T251-T260: parsers with explicit lexical and state boundaries."""
from author_second_half import emit

emit(251, r'''
package main
import("fmt";"net/mail")
func main(){
 for _,input:=range []string{`Li Yu <li@example.test>`,`reader@example.test`,`bad@@example.test`}{address,err:=mail.ParseAddress(input);if err!=nil{fmt.Println("invalid");continue};fmt.Printf("name=%q address=%s\n",address.Name,address.Address)}
 list,err:=mail.ParseAddressList("a@example.test, B <b@example.test>");if err!=nil{panic(err)};fmt.Printf("list=%d\n",len(list))
}
''', 'name="Li Yu" address=li@example.test\nname="" address=reader@example.test\ninvalid\nlist=2',
'net/mail 按邮件地址语法区分显示名与真正的地址，不需要自己寻找最后一个尖括号或 at 字符。ParseAddress 读取单个地址，ParseAddressList 读取逗号分隔列表；示例还拒绝两个 at 的错误输入。语法解析不会连接邮件服务器，也不能证明邮箱存在或收件人拥有该地址，业务验证需要另行设计。',
['解析成功不代表地址可投递，更不证明邮箱归属。','显示名不能代替 Address 做身份比较，两个显示名可能对应不同邮箱。'],
'对联系人列表按 Address 去重，保留第一次出现的显示名。','用地址字符串作集合键；保留输入顺序，避免未经业务约定就更改邮箱本地部分的大小写。')

emit(252, r'''
package main
import("fmt";"net")
func main(){
 _,subnet,err:=net.ParseCIDR("192.0.2.0/24");if err!=nil{panic(err)}
 for _,text:=range []string{"192.0.2.0","192.0.2.255","192.0.3.1","not-ip"}{ip:=net.ParseIP(text);fmt.Printf("%s valid=%t member=%t\n",text,ip!=nil,ip!=nil&&subnet.Contains(ip))}
 ip:=net.ParseIP("2001:db8::1");_,v6,err:=net.ParseCIDR("2001:db8::/32");if err!=nil{panic(err)};fmt.Printf("ipv6=%t\n",v6.Contains(ip))
}
''', '192.0.2.0 valid=true member=true\n192.0.2.255 valid=true member=true\n192.0.3.1 valid=true member=false\nnot-ip valid=false member=false\nipv6=true',
'ParseCIDR 把地址范围解释为网络前缀，Contains 判断地址位是否属于此前缀。示例同时检查 IPv4 网段首尾、相邻网段、非法字符串和 IPv6 前缀。地址解析失败返回 nil，不能把它当有效零地址。Contains 表示集合包含关系，不负责传统 IPv4 网络地址与广播地址能否分配给主机的策略。',
['网段包含首尾地址，并不等于所有地址都适合用作主机地址。','字符串前缀匹配不等于 CIDR 匹配，地址应先解析为二进制。'],
'验证 IPv4 地址能否属于 IPv6 示例网段。','把 192.0.2.1 传给 v6.Contains，结果应为 false；保留对 ParseIP 返回值的检查。')

emit(253, r'''
package main
import("fmt";"net/url";"strings")
func allowed(text string)bool{
 u,err:=url.Parse(text);if err!=nil||u.Scheme!="https"||u.User!=nil||u.Opaque!=""{return false}
 host:=strings.ToLower(u.Hostname());if u.Port()!=""&&u.Port()!="443"{return false};return host=="example.test"||strings.HasSuffix(host,".example.test")
}
func main(){for _,text:=range []string{"https://api.example.test/a","http://example.test","https://user@example.test","https://example.test.evil","https://evil-example.test","https://example.test:8443"}{fmt.Printf("%s=%t\n",text,allowed(text))}}
''', 'https://api.example.test/a=true\nhttp://example.test=false\nhttps://user@example.test=false\nhttps://example.test.evil=false\nhttps://evil-example.test=false\nhttps://example.test:8443=false',
'URL 白名单必须依据解析后的 scheme、用户信息、主机和端口判断。主机允许 example.test 或点边界内的子域，避免把 evil-example.test 与 example.test.evil 当作同一域。示例拒绝非 HTTPS、内嵌凭据和非默认端口，仅做离线语法判断，不请求任何地址。DNS 解析与重定向后的目标验证属于另一个边界。',
['简单 Contains 或无点边界的 HasSuffix 会误接收伪造域名。','初始 URL 合法不保证服务器重定向的后续 URL 仍合法。'],
'拒绝末尾点形式的主机，或明确规范化为不带末尾点的形式。','先选定业务策略，再在 Hostname 后统一处理一次末尾点；对原始主机和规范化主机都增加测试。')

emit(254, r'''
package main
import("fmt";"strings")
func hostname(text string)bool{
 if text==""||len(text)>253{return false}
 for _,label:=range strings.Split(text,"."){if len(label)==0||len(label)>63||label[0]=='-'||label[len(label)-1]=='-'{return false};for _,c:=range label{if !(c>='a'&&c<='z'||c>='A'&&c<='Z'||c>='0'&&c<='9'||c=='-'){return false}}};return true
}
func main(){for _,text:=range []string{"api.example.test","-bad.test","a..test","中文.test",strings.Repeat("a",64)+".test"}{fmt.Printf("valid=%t\n",hostname(text))}}
''', 'valid=true\nvalid=false\nvalid=false\nvalid=false\nvalid=false',
'这份校验器明确只接受不带末尾点的 ASCII 主机名，逐标签检查一到六十三字节、首尾不能是横线、内部只含字母数字或横线。它也限制完整长度并拒绝空标签。中文名称需要先经过协议规定的国际化域名转换，不能直接放宽成任意 Unicode 字母。校验不进行 DNS 查询，因此结果描述语法而不是主机存在性。',
['unicode.IsLetter 会接受大量非 ASCII 字母，不符合本例的 ASCII 主机名协议。','主机名、DNS 通用标签和服务记录名的语法边界不同，不能到处复用同一校验器。'],
'支持一个合法的末尾点，但继续拒绝连续两个点。','先只移除最后一个点，再执行现有标签检查；a.. 仍会留下空标签并被拒绝。')

emit(255, r'''
package main
import("fmt";"sort";"strconv";"strings")
type Version struct{Raw string;Parts [3]int;Pre []string}
func number(text string)(int,error){if text==""||len(text)>1&&text[0]=='0'{return 0,fmt.Errorf("bad number")};for _,c:=range text{if c<'0'||c>'9'{return 0,fmt.Errorf("bad digit")}};return strconv.Atoi(text)}
func parse(text string)(Version,error){v:=Version{Raw:text};parts:=strings.SplitN(text,"-",2);core:=strings.Split(parts[0],".");if len(core)!=3{return v,fmt.Errorf("need three parts")};for i,part:=range core{n,err:=number(part);if err!=nil{return v,err};v.Parts[i]=n};if len(parts)==2{v.Pre=strings.Split(parts[1],".");for _,id:=range v.Pre{if id==""{return v,fmt.Errorf("empty prerelease")};numeric:=true;for _,c:=range id{if !(c>='0'&&c<='9'||c>='a'&&c<='z'||c>='A'&&c<='Z'||c=='-'){return v,fmt.Errorf("bad prerelease")};if c<'0'||c>'9'{numeric=false}};if numeric{if _,err:=number(id);err!=nil{return v,err}}}};return v,nil}
func less(a,b Version)bool{for i:=0;i<3;i++{if a.Parts[i]!=b.Parts[i]{return a.Parts[i]<b.Parts[i]}};if len(a.Pre)==0{return false};if len(b.Pre)==0{return true};for i:=0;i<len(a.Pre)&&i<len(b.Pre);i++{x,y:=a.Pre[i],b.Pre[i];if x==y{continue};nx,ex:=strconv.Atoi(x);ny,ey:=strconv.Atoi(y);if ex==nil&&ey==nil{return nx<ny};if ex==nil{return true};if ey==nil{return false};return x<y};return len(a.Pre)<len(b.Pre)}
func main(){versions:=[]Version{};for _,text:=range []string{"2.0.0","2.0.0-rc.10","1.9.0","2.0.0-alpha.1","2.0.0-rc.2"}{v,err:=parse(text);if err!=nil{panic(err)};versions=append(versions,v)};sort.SliceStable(versions,func(i,j int)bool{return less(versions[i],versions[j])});for _,v:=range versions{fmt.Println(v.Raw)};_,err:=parse("1.02.0");fmt.Printf("invalid=%t\n",err!=nil)}
''', '1.9.0\n2.0.0-alpha.1\n2.0.0-rc.2\n2.0.0-rc.10\n2.0.0\ninvalid=true',
'版本比较先按三段整数，再比较预发布标识；正式版优先级高于相同核心版本的预发布。预发布中的数字按数值比较，因此 rc.2 早于 rc.10，数字标识也排在文字标识之前。解析拒绝空段、数字前导零和坏字符；本例范围不包含构建元数据，并限制数字可表示为本机 int。稳定排序让相同优先级保留输入顺序。',
['按整个字符串排序会把 10 排在 2 前面，无法表达版本优先级。','构建元数据不参与语义版本优先级，若扩展支持加号后缀，应在比较时剔除。'],
'支持 +build.7 后缀，但让它不影响已有版本排序。','先分离并校验构建标识，保留 Raw 用于展示，只把核心与预发布字段交给 less。')

emit(256, r'''
package main
import("fmt";"strconv")
func checkDigit(body string)(int,error){sum:=0;double:=true;for i:=len(body)-1;i>=0;i--{c:=body[i];if c<'0'||c>'9'{return 0,fmt.Errorf("ASCII digits only")};n:=int(c-'0');if double{n*=2;if n>9{n-=9}};sum+=n;double=!double};if body==""{return 0,fmt.Errorf("empty")};return (10-sum%10)%10,nil}
func valid(code string)bool{if len(code)<2{return false};digit,err:=checkDigit(code[:len(code)-1]);return err==nil&&code[len(code)-1]==byte('0'+digit)}
func main(){body:="7992739871";digit,err:=checkDigit(body);if err!=nil{panic(err)};full:=body+strconv.Itoa(digit);fmt.Printf("code=%s\nvalid=%t\ntampered=%t\n",full,valid(full),valid("79927398714"));_,err=checkDigit("12x");fmt.Printf("bad-input=%t\n",err!=nil)}
''', 'code=79927398713\nvalid=true\ntampered=false\nbad-input=true',
'Luhn 校验从校验位左边开始交替加倍，超过九的乘积减九，然后选择让总和为十倍数的最后一位。生成器只接受 ASCII 数字并拒绝空输入，验证器重新计算前缀的校验位。示例生成已知编号并拒绝一位变更。它用于发现常见录入错误，不提供抗伪造能力。',
['加倍起点取决于是否已经包含校验位，混淆会让奇偶长度结果错误。','Luhn 不是密码学认证，攻击者可以重新计算合法校验位。'],
'允许显示输入中的空格和横线，但拒绝其他标点。','在进入 checkDigit 前仅移除明确允许的显示分隔符，再对规范数字串执行现有检查。')

emit(257, r'''
package main
import("fmt";"strings";"unicode")
func isbn(text string)bool{var digits strings.Builder;for _,c:=range text{if c=='-'||unicode.IsSpace(c){continue};if c<'0'||c>'9'{return false};digits.WriteRune(c)};code:=digits.String();if len(code)!=13||!strings.HasPrefix(code,"978")&&!strings.HasPrefix(code,"979"){return false};sum:=0;for i:=0;i<len(code);i++{weight:=1;if i%2==1{weight=3};sum+=int(code[i]-'0')*weight};return sum%10==0}
func main(){for _,code:=range []string{"978-0-306-40615-7","9780306406158","978030640615","978 0 306 40615 7","4006381333931"}{fmt.Printf("valid=%t\n",isbn(code))}}
''', 'valid=true\nvalid=false\nvalid=false\nvalid=true\nvalid=false',
'ISBN13 去掉允许的显示分隔符后应恰好十三位，且以 978 或 979 开头。位置从左开始交替使用一和三的权重，包含校验位的加权总和必须能被十整除。示例比较带横线、带空格、坏校验位和错误长度，还拒绝校验和正确但前缀不属于 ISBN 的普通 EAN13。这里不验证 ISBN 注册组及出版社分段，也不证明图书已登记或库存确实存在。',
['不能用泛化的数字分类接受全角数字后再按 ASCII 字节相减。','ISBN10 使用另一套校验规则，不应把十位编号简单补零当成 ISBN13。'],
'返回规范化后的十三位编号及错误原因。','把解析与校验分开：先构造规范字符串，再分别报告字符、长度和校验和错误。')

emit(258, r'''
package main
import("fmt";"strings")
func fields(text string)([]string,error){result:=[]string{};var current strings.Builder;escaped:=false;for _,c:=range text{if escaped{if c!=';'&&c!='\\'{return nil,fmt.Errorf("bad escape")};current.WriteRune(c);escaped=false;continue};switch c{case '\\':escaped=true;case ';':result=append(result,current.String());current.Reset();default:current.WriteRune(c)}};if escaped{return nil,fmt.Errorf("trailing escape")};return append(result,current.String()),nil}
func main(){values,err:=fields(`a\;b;c\\d;`);if err!=nil{panic(err)};fmt.Printf("fields=%d\nfirst=%s\nsecond=%s\nempty-last=%t\n",len(values),values[0],values[1],values[2]=="");_,err=fields(`bad\x`);fmt.Printf("invalid=%t\n",err!=nil)}
''', 'fields=3\nfirst=a;b\nsecond=c\\d\nempty-last=true\ninvalid=true',
'状态机只有普通与转义两种状态。普通分号结束字段，反斜线让下一个分号或反斜线成为内容；其他转义和末尾悬空反斜线都被拒绝。循环按 rune 处理，中文不会被拆成残缺字节。最后总是追加当前字段，保留尾部分号所表达的空字段，而不是悄悄丢弃。',
['直接 strings.Split 无法区分字段分隔符与被转义的分号。','遇到输入结束时仍处于转义状态必须报错，不能自动吞掉最后一个字符。'],
'实现与 fields 对应的编码器，验证任意字段序列往返。','对每个字段先转义反斜线和分号，再用分号连接；测试空字段、中文和末尾反斜线。')

emit(259, r'''
package main
import("fmt")
type Opening struct{Rune rune;Offset int}
func brackets(text string)(int,error){stack:=[]Opening{};pairs:=map[rune]rune{')':'(',']':'[','}':'{'};for offset,c:=range text{switch c{case '(', '[', '{':stack=append(stack,Opening{c,offset});case ')',']','}':if len(stack)==0||stack[len(stack)-1].Rune!=pairs[c]{return offset,fmt.Errorf("mismatch")};stack=stack[:len(stack)-1]}};if len(stack)>0{return stack[len(stack)-1].Offset,fmt.Errorf("unclosed")};return -1,nil}
func main(){_,err:=brackets("中{a+[b*(c)]}");fmt.Printf("nested-valid=%t\n",err==nil);offset,err:=brackets("中(a]");fmt.Printf("mismatch=%t byte-offset=%d\n",err!=nil,offset);offset,err=brackets("abc(");fmt.Printf("unclosed=%t byte-offset=%d\n",err!=nil,offset)}
''', 'nested-valid=true\nmismatch=true byte-offset=5\nunclosed=true byte-offset=3',
'栈保存尚未匹配的开括号以及它们在原文中的字节偏移。遇到闭括号时只能匹配栈顶，类型不符或空栈立即返回首个冲突位置，结束后还有开括号则报告未关闭位置。range 的 offset 是 UTF8 字节偏移，因此中文后的错误位置为五。这是纯括号文本规则，不识别代码字符串、注释或转义语法。',
['只统计每种括号数量无法发现 ([)] 这种交叉嵌套。','字节偏移、rune 序号与编辑器 UTF16 偏移不同，导航时必须转换。'],
'把输出位置转换成一基行号和 UTF16 列号。','在错误字节偏移之前遍历原文，遇换行推进行号；普通 BMP rune 占一列，补充平面 rune 占两个 UTF16 单元。')

emit(260, r'''
package main
import("bytes";"fmt";"unicode/utf8")
type Decoder struct{Pending []byte;Failed bool}
func(d *Decoder)Feed(chunk []byte,final bool)(string,error){if d.Failed{return "",fmt.Errorf("decoder failed")};d.Pending=append(d.Pending,chunk...);var out bytes.Buffer;for len(d.Pending)>0&&utf8.FullRune(d.Pending){r,size:=utf8.DecodeRune(d.Pending);if r==utf8.RuneError&&size==1{d.Failed=true;return "",fmt.Errorf("invalid UTF8")};out.WriteRune(r);d.Pending=d.Pending[size:]};if final&&len(d.Pending)>0{d.Failed=true;return "",fmt.Errorf("incomplete UTF8")};return out.String(),nil}
func main(){
 input:=[]byte("中😀Go");decoder:=&Decoder{};text:="";for i,part:=range [][]byte{input[:2],input[2:5],input[5:]}{piece,err:=decoder.Feed(part,i==2);if err!=nil{panic(err)};text+=piece};fmt.Printf("text=%s runes=%d\n",text,utf8.RuneCountInString(text))
 bad:=&Decoder{};_,err:=bad.Feed([]byte{0xff},true);fmt.Printf("invalid=%t\n",err!=nil);short:=&Decoder{};_,err=short.Feed([]byte{0xe4,0xb8},true);fmt.Printf("incomplete=%t\n",err!=nil)
}
''', 'text=中😀Go runes=4\ninvalid=true\nincomplete=true',
'字节分片可能在中文或四字节表情中间切开，不能分别把每片直接转成字符串。Decoder 保留尚不完整的后缀，FullRune 表示已有足够字节判断下一个 rune；DecodeRune 返回 RuneError 且大小为一时才是坏编码，合法的替换字符本身不应误拒。最后一片仍有残留则报告截断，失败后不继续复用该状态。',
['FullRune 对已足够确认的坏字节也返回 true，仍必须检查 DecodeRune 的结果。','把每个 chunk 独立转换或清洗，会在跨块字符边界丢失信息。'],
'加入合法 U+FFFD 字符的分片往返，证明它不是错误输入。','用该字符的三字节 UTF8 编码跨块输入；DecodeRune 返回大小为三，必须被正常接受。')
