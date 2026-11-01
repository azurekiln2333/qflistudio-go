"""T241-T250: rendered and serialized offline representations."""
from author_second_half import emit

emit(241, r'''
package main
import("bytes";"fmt";"text/template")
type Item struct{Name string;Qty,Unit int};type Report struct{Items []Item;Total int}
func money(cents int)string{return fmt.Sprintf("%d.%02d",cents/100,cents%100)}
func main(){
 report:=Report{Items:[]Item{{"pen",2,139},{"pad",1,50}}};for _,item:=range report.Items{report.Total+=item.Qty*item.Unit}
 source:="{{range .Items}}{{.Name}} {{.Qty}} x {{money .Unit}}\n{{end}}total {{money .Total}}\n"
 t,err:=template.New("invoice").Funcs(template.FuncMap{"money":money}).Parse(source);if err!=nil{panic(err)}
 var out bytes.Buffer;if err=t.Execute(&out,report);err!=nil{panic(err)};fmt.Print(out.String())
}
''', 'pen 2 x 1.39\npad 1 x 0.50\ntotal 3.28',
'金额在计算阶段使用整数分，模板函数只负责展示成两位小数。Funcs 在 Parse 前注册 money，模板才能识别函数名。报表先计算总额，再将完整数据交给模板，避免把业务运算分散在展示字符串里。执行先写临时缓冲，确认成功后输出，可防止生成一半的报告被当成最终文件。',
['Funcs 在解析之后才注册，模板可能已经因未知函数而解析失败。','这里 money 只处理非负金额，负数的余数格式需要显式处理符号。'],
'支持退款金额 -139 分，输出 -1.39。','先单独处理负号，再格式化绝对金额；注意最小整数不能直接取负，应选择清晰的受限金额范围。')

emit(242, r'''
package main
import("bytes";"fmt";"html/template";"strings")
func main(){
 t,err:=template.New("message").Parse(`<p title="{{.}}">{{.}}</p>`);if err!=nil{panic(err)}
 var out bytes.Buffer;if err=t.Execute(&out,`<b>"x"</b>`);err!=nil{panic(err)}
 html:=out.String();fmt.Printf("escaped-tags=%t\nescaped-quotes=%t\nraw-tag-absent=%t\n",strings.Contains(html,"&lt;b&gt;"),strings.Contains(html,"&#34;"),!strings.Contains(html,"<b>"))
}
''', 'escaped-tags=true\nescaped-quotes=true\nraw-tag-absent=true',
'html/template 根据插入位置执行上下文相关转义，同一用户值同时进入正文和带引号属性。示例确认标签尖括号与引号被编码，原始 b 标签没有进入最终 HTML。模板字面量中的 p 标签属于开发者定义的结构，用户输入只是数据。不要为了显示方便把外部输入强制转换为 template.HTML。',
['text/template 不提供 HTML 上下文安全转义，不能直接替代 html/template。','将不可信内容标成 template.HTML 会绕过保护，重新引入脚本注入风险。'],
'将用户内容换成带 ampersand 的 A&B，检查最终包含 &amp;。','保持输入类型为普通 string，让模板负责转义；不要先手工转义导致双重编码。')

emit(243, r'''
package main
import("bytes";"fmt";"text/template")
type Row struct{Name string;Count int};type Report struct{Title string;Rows []Row}
func main(){
 source:=`{{define "header"}}REPORT {{.}}{{end}}{{define "row"}}{{.Name}}={{.Count}}{{end}}{{define "report"}}{{template "header" .Title}}:{{range .Rows}} [{{template "row" .}}]{{end}}{{end}}`
 t,err:=template.New("root").Parse(source);if err!=nil{panic(err)}
 for _,report:=range []Report{{"north",[]Row{{"books",3},{"pens",5}}},{"south",[]Row{{"books",2}}}}{var out bytes.Buffer;if err:=t.ExecuteTemplate(&out,"report",report);err!=nil{panic(err)};fmt.Println(out.String())}
}
''', 'REPORT north: [books=3] [pens=5]\nREPORT south: [books=2]',
'define 建立可重用的命名模板，template 调用把显式数据作为子模板的点值。header 接收标题字符串，row 接收一条记录，report 组合两者。解析一次后对两个数据集执行，展示结构共享而数据互不污染。ExecuteTemplate 指定入口，避免误执行只有定义而没有正文的根模板。',
['子模板的点值由调用参数决定，不会自动保留外层记录。','只定义命名模板后调用根 Execute，可能得到空输出而不是预期报表。'],
'为没有 Rows 的报表输出 [empty]。','在 range 中加入 else 分支，该分支只在切片为空时执行，其他模板无需修改。')

emit(244, r'''
package main
import("bytes";"fmt";"text/template")
func render(t *template.Template,data map[string]string)(string,error){var buffer bytes.Buffer;if err:=t.Execute(&buffer,data);err!=nil{return "",err};return buffer.String(),nil}
func main(){
 t,err:=template.New("profile").Option("missingkey=error").Parse("name={{.name}} role={{.role}}");if err!=nil{panic(err)}
 full,err:=render(t,map[string]string{"name":"Li","role":"reader"});if err!=nil{panic(err)};fmt.Println(full)
 partial,err:=render(t,map[string]string{"name":"Yu"});fmt.Printf("missing-rejected=%t\npartial-published=%t\n",err!=nil,partial!="")
}
''', 'name=Li role=reader\nmissing-rejected=true\npartial-published=false',
'missingkey=error 把缺字段从悄悄输出占位内容变成显式失败。模板执行可能在发现缺键之前已经写出部分文本，所以 render 使用局部缓冲，并仅在完整成功时返回字符串。第一份资料生成完整报告，第二份缺少 role 被拒绝且没有发布半成品。这适合配置导出或报表字段不能缺失的场景。',
['Execute 返回错误时，目标 Writer 可能已收到部分内容，错误并不自动回滚输出。','missingkey 主要约束 map 键访问，不代替所有业务字段校验。'],
'保留上一份成功报告，在下一次渲染失败时不覆盖它。','用临时字符串接收 render 结果；只有 err 为 nil 时再更新当前报告变量。')

emit(245, r'''
package main
import("encoding/json";"fmt";"strings")
type Account struct{Name,Token string}
func(a Account)MarshalJSON()([]byte,error){type View struct{Name string `json:"name"`;Token string `json:"token"`};masked:="***";if len(a.Token)>=4{masked+=a.Token[len(a.Token)-4:]};return json.Marshal(View{a.Name,masked})}
func main(){
 account:=Account{"Li","secret-1234"};wire,err:=json.Marshal(account);if err!=nil{panic(err)}
 fmt.Println(string(wire));fmt.Printf("memory-intact=%t\nsecret-absent=%t\n",account.Token=="secret-1234",!strings.Contains(string(wire),"secret-"))
}
''', '{"name":"Li","token":"***1234"}\nmemory-intact=true\nsecret-absent=true',
'MarshalJSON 为外部序列化提供单独的脱敏视图，不直接改写内存中的账号。内部 View 类型没有 Account 的方法，因此对 View 调用 json.Marshal 不会递归进入自身。示例仅保留令牌最后四个字节，并检查原始值仍完整且前缀未泄露。脱敏策略必须由业务决定，最后四位也未必适合所有秘密。',
['在 MarshalJSON 内再次序列化同一 Account 会无限递归。','按字节取后缀只适用于这里的 ASCII 令牌，普通 Unicode 文本可能被截断。'],
'不保留短于四字节令牌的任何原文，并加入空令牌案例。','保持短令牌统一输出 ***，为空值另定是否省略字段的策略，避免错误暴露完整短秘密。')

emit(246, r'''
package main
import("encoding/json";"fmt")
type Status int
const(Pending Status=iota;Ready)
func(s Status)MarshalText()([]byte,error){switch s{case Pending:return []byte("pending"),nil;case Ready:return []byte("ready"),nil};return nil,fmt.Errorf("unknown status")}
func(s *Status)UnmarshalText(text []byte)error{var next Status;switch string(text){case "pending":next=Pending;case "ready":next=Ready;default:return fmt.Errorf("invalid status")};*s=next;return nil}
func main(){
 wire,err:=json.Marshal(Ready);if err!=nil{panic(err)};fmt.Printf("wire=%s\n",wire)
 var status Status;if err=json.Unmarshal([]byte(`"ready"`),&status);err!=nil{panic(err)};fmt.Printf("roundtrip=%t\n",status==Ready)
 err=json.Unmarshal([]byte(`"deleted"`),&status);fmt.Printf("invalid=%t unchanged=%t\n",err!=nil,status==Ready)
}
''', 'wire="ready"\nroundtrip=true\ninvalid=true unchanged=true',
'文本编解码接口将内部整数枚举转换成稳定字符串协议，JSON 也能使用这些方法。UnmarshalText 先检查输入，再一次性写入接收者，因此坏状态不会破坏原来的 Ready。MarshalText 同样拒绝未知内部枚举，避免把错误整数悄悄输出。对外字符串可长期稳定，内部常量编号则无需成为协议的一部分。',
['解析失败前先修改接收者，会让调用方收到错误同时丢失先前有效值。','枚举新增值时要同步编码和解码两个方向，不能只改常量列表。'],
'新增 paused 状态，并增加三种状态的往返检查。','在两个 switch 中都加入 paused 分支，再遍历全部合法枚举，Marshal 后 Unmarshal 比较原值。')

emit(247, r'''
package main
import("fmt";"strings";"unicode/utf8")
func cell(text string,width int)string{runes:=[]rune(text);if len(runes)>width{runes=runes[:width]};out:=string(runes);return out+strings.Repeat(" ",width-utf8.RuneCountInString(out))}
func main(){for _,text:=range []string{"Go","离线工具","A😀BC"}{value:=cell(text,3);fmt.Printf("|%s| runes=%d\n",value,utf8.RuneCountInString(value))}}
''', '|Go | runes=3\n|离线工| runes=3\n|A😀B| runes=3',
'普通字符串下标按字节工作，直接截前三字节可能切断中文或表情。cell 先转换成 rune 切片，再按三个码点截断并填充空格，输出核对码点数始终为三。这里的列宽只是码点预算：中文、表情、组合字符在终端中的实际显示宽度不同，不能把它宣称为视觉等宽表格。',
['rune 个数不等于字节数，也不等于用户感知字符或终端显示宽度。','负宽度或极大宽度应在公共接口处拒绝，避免切片 panic 或大量填充。'],
'让 cell 对零宽度返回空字符串，对负宽度返回错误。','先验证 width，再进行转换和填充；使用独立测试覆盖中文、空字符串和负数。')

emit(248, r'''
package main
import("bufio";"bytes";"encoding/json";"fmt")
type Row struct{ID int `json:"id"`;Value string `json:"value"`}
func main(){
 var source bytes.Buffer;encoder:=json.NewEncoder(&source);for _,row:=range []Row{{1,"a"},{2,"b"}}{if err:=encoder.Encode(row);err!=nil{panic(err)}}
 source.WriteString("{broken}\n");if err:=encoder.Encode(Row{3,"c"});err!=nil{panic(err)}
 scanner:=bufio.NewScanner(&source);line:=0;valid:=0
 for scanner.Scan(){line++;var row Row;if err:=json.Unmarshal(scanner.Bytes(),&row);err!=nil{fmt.Printf("line=%d invalid\n",line);continue};valid++;fmt.Printf("id=%d value=%s\n",row.ID,row.Value)}
 if err:=scanner.Err();err!=nil{panic(err)};fmt.Printf("valid=%d\n",valid)
}
''', 'id=1 value=a\nid=2 value=b\nline=3 invalid\nid=3 value=c\nvalid=3',
'JSON Lines 约定每一物理行是一个完整 JSON 值。Encoder.Encode 自动追加换行，扫描器按行解码，某一行损坏时可记录行号并继续后面的独立记录。示例在两条正常记录后插入坏行，仍成功读取最后一条。每行大小要符合 Scanner 的预算，大文件的总行数也应根据业务限制。',
['把多行格式化 JSON 当作 JSON Lines 会让每个物理行都不是完整对象。','Scanner 结束后忽略 Err，会把超长行或输入错误误认为正常 EOF。'],
'用 DisallowUnknownFields 检查每行，同时拒绝同一行中的第二个 JSON 值。','对每行新建 Decoder，严格解码一次后再次 Decode 检查 EOF，行间仍独立恢复。')

emit(249, r'''
package main
import("fmt";"strings")
func escape(text string)string{r:=strings.NewReplacer("\\","\\\\","|","\\|","\r\n","<br>","\n","<br>","\r","<br>");return r.Replace(text)}
func main(){
 fmt.Println("| name | notes |");fmt.Println("| --- | --- |")
 for _,row:=range [][2]string{{"A|B",`C:\docs`},{"中文","first\nsecond"}}{fmt.Printf("| %s | %s |\n",escape(row[0]),escape(row[1]))}
}
''', '| name | notes |\n| --- | --- |\n| A\\|B | C:\\\\docs |\n| 中文 | first<br>second |',
'Markdown 表格把管道符当成列分隔符，所以字段中的管道符和反斜线要分别转义，物理换行也需要转换。Replacer 一次扫描原始输入，新生成的反斜线不会再次被后续替换扩张。示例同时保留 Windows 路径、中文和多行备注。不同 Markdown 渲染器对内联 HTML 支持有差异，导出协议需明确允许 br。',
['连续多次 ReplaceAll 的顺序不当会把刚插入的转义字符再次处理。','本例转义的是表格分隔语法，不是通用 HTML 消毒器。'],
'禁止字段内原始 HTML，而仅保留生成器自己的 br。','先对原始字段执行 html.EscapeString，再处理表格语法和换行；不要把生成的 br 再整体转义。')

emit(250, r'''
package main
import("fmt";"strings")
func progress(done,total,width int)string{
 if width<=0{return "[]"};if total<=0{return "["+strings.Repeat("-",width)+"] n/a"};if done<0{done=0};if done>total{done=total}
 filled:=int(float64(done)/float64(total)*float64(width));return fmt.Sprintf("[%s%s] %d/%d",strings.Repeat("#",filled),strings.Repeat("-",width-filled),done,total)
}
func main(){for _,pair:=range [][2]int{{0,8},{3,8},{10,8},{-2,8},{0,0}}{fmt.Println(progress(pair[0],pair[1],8))}}
''', '[--------] 0/8\n[###-----] 3/8\n[########] 8/8\n[--------] 0/8\n[--------] n/a',
'进度条是一个纯函数，不依赖光标控制、实际时间或输出设备。先处理无总量和越界输入，再把完成比例映射到固定八格，已完成数量向下取整。超额完成被限制到总量，负数归零，总量为零显示未知而不是除零。浮点比例适合这里的小计数，极大精确整数场景应另设范围或采用防溢出整数算法。',
['直接 done*width 可能整数溢出，不能只在乘法之后检查结果。','总量为零可能表示未知任务数，不能自动宣称已经完成百分之百。'],
'增加百分数文本，并保持零总量仍显示 n/a。','只在 total>0 分支计算比例，使用明确舍入规则格式化百分比，先完成边界归一化。')
