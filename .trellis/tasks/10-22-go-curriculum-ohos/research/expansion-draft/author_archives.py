"""T211-T220: bounded in-memory compression and envelope formats."""
from author_second_half import emit

emit(211, r'''
package main
import("bytes";"compress/gzip";"fmt";"io")
func main(){
 input:=[]byte("first\nsecond\n");var compressed bytes.Buffer
 writer:=gzip.NewWriter(&compressed)
 if _,err:=writer.Write(input);err!=nil{panic(err)}
 if err:=writer.Close();err!=nil{panic(err)}
 reader,err:=gzip.NewReader(bytes.NewReader(compressed.Bytes()));if err!=nil{panic(err)}
 restored,err:=io.ReadAll(reader);if err!=nil{panic(err)};if err=reader.Close();err!=nil{panic(err)}
 fmt.Printf("roundtrip=%t\nlines=%d\n",bytes.Equal(input,restored),bytes.Count(restored,[]byte{'\n'}))
 truncated:=compressed.Bytes()[:compressed.Len()-3];broken,err:=gzip.NewReader(bytes.NewReader(truncated));if err!=nil{panic(err)}
 _,err=io.ReadAll(broken);broken.Close();fmt.Printf("missing-trailer=%t\n",err!=nil)
}
''', 'roundtrip=true\nlines=2\nmissing-trailer=true',
'Gzip 写入器会缓存压缩状态，Close 写入最后的压缩数据和校验尾部。只有关闭成功后，内存缓冲才是一份完整封装。解压时必须读取到末尾才能检查尾部完整性，示例删除最后三个字节后，NewReader 仍可能成功，但 ReadAll 报错。正常路径还核对全部原文和行数，防止仅验证压缩器能被创建。',
['Flush 不等于 Close，刷新不能代替最终尾部。','只创建解压读取器而不读完正文，会漏掉尾部截断和校验错误。'],
'将输入改成空日志，验证压缩和解压仍成功且行数为零。','保留 Close 和 ReadAll 检查；gzip 空流不是零字节文件，但解压结果应为空切片。')

emit(212, r'''
package main
import("bytes";"compress/zlib";"fmt";"io";"strings")
func compress(text string) []byte {var out bytes.Buffer;w:=zlib.NewWriter(&out);if _,err:=io.WriteString(w,text);err!=nil{panic(err)};if err:=w.Close();err!=nil{panic(err)};return out.Bytes()}
func decode(data []byte,budget int64)(string,error){
 r,err:=zlib.NewReader(bytes.NewReader(data));if err!=nil{return "",err};defer r.Close()
 text,err:=io.ReadAll(io.LimitReader(r,budget+1));if err!=nil{return "",err};if int64(len(text))>budget{return "",fmt.Errorf("expanded data over budget")};return string(text),nil
}
func main(){
 text,err:=decode(compress("small"),8);fmt.Printf("small=%s valid=%t\n",text,err==nil)
 _,err=decode(compress(strings.Repeat("a",1000)),8);fmt.Printf("expanded-rejected=%t\n",err!=nil)
 text,err=decode(compress("12345678"),8);fmt.Printf("exact-limit=%t\n",err==nil&&len(text)==8)
}
''', 'small=small valid=true\nexpanded-rejected=true\nexact-limit=true',
'压缩文件的输入大小无法代表解压后的内存成本。decode 只允许读取预算加一字节，用额外字节区分恰好达到上限和实际超量；超限时丢弃结果并返回错误。三个输入分别覆盖小载荷、大量重复内容和恰好八字节。这个限制约束解压输出，压缩输入与处理时间在真实应用中也应另设预算。',
['只用 LimitReader 的 budget 字节并判断无错误，会把超量输入误当成恰好上限。','预算必须非负且不能在加一时溢出，公共接口应先验证参数。'],
'让 decode 拒绝负预算，并增加 budget=0 的空数据测试。','参数小于零立即返回错误；零预算可接受空明文，但只要探测到一个字节就拒绝。')

emit(213, r'''
package main
import("archive/tar";"bytes";"fmt";"io")
func main(){
 var archive bytes.Buffer;w:=tar.NewWriter(&archive)
 for _,item:=range []struct{name,text string}{{"notes.txt","skip"},{"docs/readme.txt","offline guide"}}{
  if err:=w.WriteHeader(&tar.Header{Name:item.name,Mode:0600,Size:int64(len(item.text)),Typeflag:tar.TypeReg});err!=nil{panic(err)}
  if _,err:=io.WriteString(w,item.text);err!=nil{panic(err)}
 };if err:=w.Close();err!=nil{panic(err)}
 r:=tar.NewReader(bytes.NewReader(archive.Bytes()));found:=""
 for {h,err:=r.Next();if err==io.EOF{break};if err!=nil{panic(err)}
  if h.Name!="docs/readme.txt"{continue};if h.Typeflag!=tar.TypeReg||h.Size>64{panic("invalid target")}
  data,err:=io.ReadAll(r);if err!=nil{panic(err)};found=string(data)
 }
 fmt.Printf("document=%s\nbytes=%d\n",found,len(found))
}
''', 'document=offline guide\nbytes=13',
'tar.Reader 按顺序呈现条目，每次 Next 会移动到下一条记录。程序跳过不相关文件，只在名字匹配、类型为普通文件且长度符合预算时读取目标正文。全过程留在内存，没有把条目路径直接写到磁盘。归档创建时必须声明准确的 Size，写入器据此组织后续头部和填充。',
['不能把目录、符号链接或设备条目当成普通文件读取并提取。','归档头中的名字属于输入数据，实际落盘还必须校验路径包含关系。'],
'增加 docs/readme.txt 缺失时的明确错误，而不是把空字符串当成合法空文档。','另设 found 布尔变量；允许目标内容长度为零，扫描结束后单独判断是否匹配过条目。')

emit(214, r'''
package main
import("archive/zip";"bytes";"fmt";"io";"sort")
func main(){
 var data bytes.Buffer;w:=zip.NewWriter(&data)
 for _,item:=range []struct{name,text string}{{"sales.csv","a,10\n"},{"stock.csv","a,3\n"}}{f,err:=w.Create(item.name);if err!=nil{panic(err)};if _,err=io.WriteString(f,item.text);err!=nil{panic(err)}}
 if err:=w.Close();err!=nil{panic(err)};r,err:=zip.NewReader(bytes.NewReader(data.Bytes()),int64(data.Len()));if err!=nil{panic(err)}
 rows:=[]string{};for _,file:=range r.File{f,err:=file.Open();if err!=nil{panic(err)};body,err:=io.ReadAll(f);f.Close();if err!=nil{panic(err)};rows=append(rows,fmt.Sprintf("%s:%d",file.Name,len(body)))}
 sort.Strings(rows);for _,row:=range rows{fmt.Println(row)}
 fmt.Printf("entries=%d\n",len(rows))
}
''', 'sales.csv:5\nstock.csv:4\nentries=2',
'ZIP 写入器在 Close 时补齐中央目录，所以必须先关闭才能创建读取器。两个报表分别通过 Create 建立条目，打开归档后逐项读取并核对实际解压字节数。输出先排序，使条目写入顺序不影响报告。每个 Open 返回的读取器都应及时关闭，不能把整个循环的清理都推迟到程序最后。',
['ZIP 总字节数不是所有明文的总字节数，不能用压缩长度验证报表内容长度。','未关闭写入器便读取归档，可能缺少中央目录而失败。'],
'将每个条目的明文限制为 16 字节。','用 LimitReader(f,17) 读取并检查长度是否超过 16，同时继续处理读取器关闭和错误。')

emit(215, r'''
package main
import("archive/zip";"fmt";"os";"path";"strings")
func safe(h *zip.FileHeader)bool{
 name:=h.Name
 if name==""||strings.Contains(name,"\\")||strings.Contains(name,":")||path.IsAbs(name)||h.Mode()&os.ModeSymlink!=0{return false}
 clean:=path.Clean(name);return clean!="."&&clean!=".."&&!strings.HasPrefix(clean,"../")
}
func main(){
 for _,name:=range []string{"docs/a.txt","../escape","/etc/file","C:/file","docs\\..\\escape"}{h:=&zip.FileHeader{Name:name};fmt.Printf("%s=%t\n",name,safe(h))}
 link:=&zip.FileHeader{Name:"docs/link"};link.SetMode(os.ModeSymlink|0600);fmt.Printf("symlink=%t\n",safe(link))
}
''', 'docs/a.txt=true\n../escape=false\n/etc/file=false\nC:/file=false\ndocs\\..\\escape=false\nsymlink=false',
'提取归档前先按归档的斜线路径规则校验条目。程序拒绝绝对路径、向上逃逸、Windows 驱动器形式、反斜线与符号链接，并接受普通子目录文件。这里仅验证头部，不进行落盘；真正写盘时仍要解析目标父目录的文件系统别名，防止目标目录中已有符号链接把写入引向外部。',
['字符串不含 ../ 并不代表安全，清洗后仍应检查向上逃逸和平台路径形式。','词法校验不能解决目标目录中已有符号链接造成的物理越界。'],
'将允许条目规范化后放进集合，拒绝两个不同名字映射到相同目标。','使用 path.Clean 的结果作键；a/../b 与 b 冲突时在任何写入前拒绝整个提取计划。')

emit(216, r'''
package main
import("archive/tar";"bytes";"fmt";"io";"sort")
func main(){
 var data bytes.Buffer;w:=tar.NewWriter(&data)
 for _,h:=range []*tar.Header{{Name:"docs/",Mode:0755,Typeflag:tar.TypeDir},{Name:"docs/run.sh",Mode:0750,Size:3,Typeflag:tar.TypeReg}}{
  if err:=w.WriteHeader(h);err!=nil{panic(err)};if h.Size>0{if _,err:=w.Write([]byte("go\n"));err!=nil{panic(err)}}
 };if err:=w.Close();err!=nil{panic(err)}
 r:=tar.NewReader(bytes.NewReader(data.Bytes()));rows:=[]string{}
 for {h,err:=r.Next();if err==io.EOF{break};if err!=nil{panic(err)};kind:="file";if h.Typeflag==tar.TypeDir{kind="dir"};rows=append(rows,fmt.Sprintf("%s %s %04o %d",h.Name,kind,h.Mode,h.Size))}
 sort.Strings(rows);for _,row:=range rows{fmt.Println(row)}
}
''', 'docs/ dir 0755 0\ndocs/run.sh file 0750 3',
'tar.Header 保存文件类型、权限位和明文大小。示例创建一个目录和一个可执行脚本，再只遍历头部生成清单；Next 会跳过尚未消费的正文。权限使用八进制显示，避免把 0750 与十进制 750 混淆。报告描述归档中声明的元数据，不代表这些权限已经应用到当前系统。',
['目录条目不应按普通文件写入 Size 字节的正文。','归档权限来自输入，真实提取程序需要过滤特殊权限位并采用本机安全策略。'],
'清单增加可执行标记，只要任意执行位被设置就输出 executable=true。','检查 h.Mode&0111 != 0；目录的搜索权限与普通文件的可执行语义需要在界面中区分。')

emit(217, r'''
package main
import("bytes";"fmt";"io";"mime/multipart")
func main(){
 var wire bytes.Buffer;w:=multipart.NewWriter(&wire);if err:=w.SetBoundary("qfli-boundary");err!=nil{panic(err)}
 if err:=w.WriteField("owner","Li");err!=nil{panic(err)};file,err:=w.CreateFormFile("upload","notes.txt");if err!=nil{panic(err)};if _,err=io.WriteString(file,"line1\n");err!=nil{panic(err)}
 if err=w.Close();err!=nil{panic(err)};r:=multipart.NewReader(&wire,w.Boundary())
 for {part,err:=r.NextPart();if err==io.EOF{break};if err!=nil{panic(err)};body,err:=io.ReadAll(part);if err!=nil{panic(err)};part.Close();fmt.Printf("field=%s file=%q body=%q\n",part.FormName(),part.FileName(),string(body))}
}
''', 'field=owner file="" body="Li"\nfield=upload file="notes.txt" body="line1\\n"',
'Multipart 在一个消息中封装多个带头部的 part。写入器生成普通 owner 字段和文件 upload 字段，Close 写出结束边界；读取器按同一 boundary 逐项解码。通过 FormName 和 FileName 可以区分字段与上传文件，而正文仍按流读取。整个示例只处理内存字节，不创建 HTTP 服务也不写上传文件到磁盘。',
['边界必须与 Content-Type 中声明的一致，不能随意猜测或省略关闭写入器。','上传文件名是不可信元数据，不能直接拼进落盘路径。'],
'为每个 part 增加 32 字节预算，并拒绝超过三个 part 的消息。','用预算加一字节探测正文超量，并在循环开始增加 part 计数；两项限制都在保存正文前检查。')

emit(218, r'''
package main
import("fmt";"mime")
func main(){
 media,params,err:=mime.ParseMediaType(`Text/Plain; charset=utf-8; title="QFLI report"`);if err!=nil{panic(err)}
 fmt.Printf("type=%s\ntitle=%s\nnormalized=%s\n",media,params["title"],mime.FormatMediaType(media,params))
 _,_,err=mime.ParseMediaType("text/plain; charset");fmt.Printf("invalid=%t\n",err!=nil)
}
''', 'type=text/plain\ntitle=QFLI report\nnormalized=text/plain; charset=utf-8; title="QFLI report"\ninvalid=true',
'媒体类型的参数可能包含空格、引号和分号，不能简单按空格拆分。ParseMediaType 规范化主类型并返回参数映射，FormatMediaType 根据需要补上引号，生成稳定字符串。示例读取带空格标题，再处理缺少参数值的错误输入。字符集名是协议声明，这个解析过程不会自动把正文转码。',
['对 Content-Type 直接做字符串相等比较会错误拒绝大小写或合法参数形式。','解析出 charset 并不代表正文已按该字符集解码。'],
'添加 filename 参数 a;b.txt 并验证格式化后还能正确读回。','把参数放入映射交给 FormatMediaType；再 ParseMediaType，检查 filename 保留分号而没有被拆成新参数。')

emit(219, r'''
package main
import("bytes";"encoding/base64";"fmt";"io")
func main(){
 var wire bytes.Buffer;w:=base64.NewEncoder(base64.StdEncoding,&wire)
 for _,chunk:=range []string{"g","o",":","42"}{if _,err:=io.WriteString(w,chunk);err!=nil{panic(err)}}
 fmt.Printf("before=%s\n",wire.String());if err:=w.Close();err!=nil{panic(err)}
 fmt.Printf("after=%s\n",wire.String());decoded,err:=io.ReadAll(base64.NewDecoder(base64.StdEncoding,bytes.NewReader(wire.Bytes())));if err!=nil{panic(err)}
 fmt.Printf("roundtrip=%t\n",string(decoded)=="go:42")
}
''', 'before=Z286\nafter=Z286NDI=\nroundtrip=true',
'Base64 每三个输入字节形成一组，流式编码器会保留不足一组的尾部。程序把五字节消息拆成四次写入，关闭前底层只能看到完整三字节对应的编码，Close 后才出现含填充的尾块。解码器作为 Reader 消费整份编码并还原消息。分片边界可以任意变化，但最终结果必须等同一次性编码。',
['未关闭编码器会丢失最后一到两个输入字节的编码。','标准 Base64 与 URL 安全编码的字母表、填充约定可能不同，双方必须一致。'],
'将输入分片改成每次一个字节，断言最终编码保持不变。','逐字节调用 Write；Close 后仍应得到 Z286NDI=，然后使用相同 StdEncoding 解码。')

emit(220, r'''
package main
import("bytes";"fmt";"io";"mime/quotedprintable";"strings")
func main(){
 decoded,err:=io.ReadAll(quotedprintable.NewReader(strings.NewReader("Subject=3A hello=\r\nworld=21")));if err!=nil{panic(err)}
 fmt.Printf("decoded=%s\n",decoded)
 original:=[]byte("你好=go");var wire bytes.Buffer;w:=quotedprintable.NewWriter(&wire);if _,err=w.Write(original);err!=nil{panic(err)};if err=w.Close();err!=nil{panic(err)}
 restored,err:=io.ReadAll(quotedprintable.NewReader(&wire));if err!=nil{panic(err)};fmt.Printf("utf8-roundtrip=%t\n",bytes.Equal(restored,original))
}
''', 'decoded=Subject: helloworld!\nutf8-roundtrip=true',
'Quoted Printable 以 =HH 表示字节，并用等号紧接 CRLF 表示软换行。第一段数据里的软换行不属于正文，所以解码后 hello 与 world 相连。第二段把中文和等号按 UTF8 字节编码再解码，核对完整字节一致。这是 MIME 传输编码，不能与 URL 百分号编码或 HTML 实体混用。',
['软换行会被移除，真实正文换行不能随意写成等号加 CRLF。','编解码按字节操作，不会自动决定邮件头或正文使用的字符集。'],
'在原始正文中加入真实 CRLF，验证它与软换行有不同结果。','分别解码 a\r\nb 和 a=\r\nb，前者保留换行，后者变成 ab。')
