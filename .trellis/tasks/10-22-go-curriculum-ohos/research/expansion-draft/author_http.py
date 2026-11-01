"""T221-T230: HTTP and URL protocols without network listeners."""
from author_second_half import emit

emit(221, r'''
package main
import("fmt";"net/http";"net/http/httptest")
func handler(w http.ResponseWriter,r *http.Request){
 if r.URL.Path!="/health"{http.NotFound(w,r);return}
 if r.Method!=http.MethodGet{w.Header().Set("Allow","GET");http.Error(w,"method",http.StatusMethodNotAllowed);return}
 w.Header().Set("Content-Type","text/plain");w.Write([]byte("ready"))
}
func main(){for _,item:=range []struct{method,path string}{{"GET","/health"},{"POST","/health"},{"GET","/missing"}}{
 r:=httptest.NewRequest(item.method,item.path,nil);w:=httptest.NewRecorder();handler(w,r);fmt.Printf("%s %s=%d allow=%q\n",item.method,item.path,w.Code,w.Header().Get("Allow"))
}}
''', 'GET /health=200 allow=""\nPOST /health=405 allow="GET"\nGET /missing=404 allow=""',
'Handler 接口可以直接接收内存请求，Recorder 收集状态、头部和正文，不需要监听端口。路由先判断资源路径，再判断允许的方法，因此未知路径是 404，已知资源的方法错误是 405，并附带 Allow。健康检查成功时写入 ready。这样的测试隔离了协议逻辑，不把网络连通性混入路由验证。',
['资源不存在和方法不允许应分别报告，错误的检查顺序会混淆两者。','开始写正文后再改变状态码或头部通常已经太晚。'],
'允许 HEAD 请求并确保它不写正文。','在方法检查中接受 GET 和 HEAD；设置相同头部后，仅 GET 调用 Write。')

emit(222, r'''
package main
import("encoding/json";"fmt";"io";"mime";"net/http";"net/http/httptest";"strings")
type Input struct{Name string `json:"name"`}
func post(w http.ResponseWriter,r *http.Request){
 media,_,err:=mime.ParseMediaType(r.Header.Get("Content-Type"));if err!=nil||media!="application/json"{http.Error(w,"media",415);return}
 decoder:=json.NewDecoder(http.MaxBytesReader(w,r.Body,128));decoder.DisallowUnknownFields();var input Input
 if err=decoder.Decode(&input);err!=nil{http.Error(w,"json",400);return};var tail interface{}
 if decoder.Decode(&tail)!=io.EOF||input.Name==""{http.Error(w,"payload",400);return}
 w.Header().Set("Content-Type","application/json");json.NewEncoder(w).Encode(input)
}
func main(){for _,item:=range []struct{media,body string}{{"application/json",`{"name":"Li"}`},{"application/json",`{"name":"Li","admin":true}`},{"application/json",`{"name":"Li"}{}`},{"text/plain",`{"name":"Li"}`}}{
 r:=httptest.NewRequest("POST","/profile",strings.NewReader(item.body));r.Header.Set("Content-Type",item.media);w:=httptest.NewRecorder();post(w,r);fmt.Println(w.Code)
}}
''', '200\n400\n400\n415',
'严格 JSON 入口先解析媒体类型，再对有大小限制的请求体解码。DisallowUnknownFields 拒绝拼写错误或未授权字段，第二次 Decode 必须得到 EOF，防止第一份合法对象后夹带另一份值。成功时返回 JSON，错误媒体类型使用 415，内容问题使用 400。所有请求由 Recorder 驱动，输入没有任何远程依赖。',
['一次 Decode 成功不代表整个请求体只有一个 JSON 值。','结构解码成功不代表字段满足业务约束，空名字仍需拒绝。'],
'为 name 增加最多 20 个 Unicode 字符的限制。','使用 utf8.RuneCountInString 而非 len 统计字符数；将失败与其他业务验证统一返回 400。')

emit(223, r'''
package main
import("context";"fmt";"net/http";"net/http/httptest")
type requestKey struct{}
func identify(next http.Handler)http.Handler{
 counter:=0
 return http.HandlerFunc(func(w http.ResponseWriter,r *http.Request){id:=r.Header.Get("X-Request-ID");if id==""{counter++;id=fmt.Sprintf("local-%d",counter)};w.Header().Set("X-Request-ID",id);next.ServeHTTP(w,r.WithContext(context.WithValue(r.Context(),requestKey{},id)))})
}
func main(){
 app:=identify(http.HandlerFunc(func(w http.ResponseWriter,r *http.Request){id,ok:=r.Context().Value(requestKey{}).(string);if !ok{panic("missing ID")};fmt.Fprint(w,id)}))
 for _,id:=range []string{"provided-7",""}{r:=httptest.NewRequest("GET","/",nil);if id!=""{r.Header.Set("X-Request-ID",id)};w:=httptest.NewRecorder();app.ServeHTTP(w,r);fmt.Printf("header=%s body=%s\n",w.Header().Get("X-Request-ID"),w.Body.String())}
}
''', 'header=provided-7 body=provided-7\nheader=local-1 body=local-1',
'中间件将请求标识放进 context，再把带新 context 的请求交给下一层，同时回写响应头。调用方提供标识时沿用它，缺失时使用确定性本地序号，便于本例断言。上下文键使用专用类型，避免与其他库的字符串键冲突。演示顺序执行；若服务并发处理，请把计数器换成原子操作或锁保护。',
['WithContext 返回新请求，忽略返回值会让后续处理器看不到标识。','示例闭包计数器仅适用于这里的顺序调用，直接用于并发服务会产生数据竞争。'],
'限制传入标识只含 ASCII 字母数字和横线且不超过 40 字节。','校验通过才沿用，否则生成新标识；不要直接把未校验头部写进日志。')

emit(224, r'''
package main
import("crypto/sha256";"fmt";"net/http";"net/http/httptest")
func main(){
 body:=[]byte("offline catalog");sum:=sha256.Sum256(body);etag:=fmt.Sprintf("\"%x\"",sum[:8])
 app:=http.HandlerFunc(func(w http.ResponseWriter,r *http.Request){w.Header().Set("ETag",etag);if r.Header.Get("If-None-Match")==etag{w.WriteHeader(http.StatusNotModified);return};w.Write(body)})
 for _,match:=range []bool{false,true}{r:=httptest.NewRequest("GET","/catalog",nil);if match{r.Header.Set("If-None-Match",etag)};w:=httptest.NewRecorder();app.ServeHTTP(w,r);fmt.Printf("match=%t status=%d bytes=%d\n",match,w.Code,w.Body.Len())}
}
''', 'match=false status=200 bytes=15\nmatch=true status=304 bytes=0',
'ETag 代表资源版本，客户端通过 If-None-Match 表示已有副本。示例按正文摘要生成带引号标签，匹配时写 304 后立即返回，不发送正文；不匹配时返回完整资源。这里处理单个强标签的精确匹配，实际 HTTP 缓存协议还包含标签列表、弱标签和星号条件，扩展时应明确支持范围。',
['304 响应不能再写完整正文，否则失去条件请求的意义。','标签必须随资源内容变化，固定常量不能可靠表示版本。'],
'修改资源正文后重新计算标签，验证旧标签收到 200。','创建新 body 与对应摘要，将旧 If-None-Match 传给处理器；断言新标签不同且返回新正文。')

emit(225, r'''
package main
import("fmt";"net/http";"net/http/httptest";"strings";"time")
func main(){
 r:=httptest.NewRequest("GET","/data.txt",nil);r.Header.Set("Range","bytes=1-3");w:=httptest.NewRecorder()
 http.ServeContent(w,r,"data.txt",time.Unix(0,0),strings.NewReader("abcdef"))
 fmt.Printf("status=%d\nrange=%s\nbody=%s\n",w.Code,w.Header().Get("Content-Range"),w.Body.String())
 r=httptest.NewRequest("GET","/data.txt",nil);r.Header.Set("Range","bytes=99-100");w=httptest.NewRecorder();http.ServeContent(w,r,"data.txt",time.Unix(0,0),strings.NewReader("abcdef"));fmt.Printf("invalid=%d\n",w.Code)
}
''', 'status=206\nrange=bytes 1-3/6\nbody=bcd\ninvalid=416',
'ServeContent 从可寻址内容读取器实现范围请求。bytes=1-3 使用包含两端的零基字节下标，所以返回 bcd、206 状态和总长度为六的 Content-Range。第二个请求超出资源长度，得到 416。固定修改时间和内存内容避免时钟及外部文件变化影响结果，整个交互没有开启网络端口。',
['HTTP Range 的下标按字节计算，不能直接当作 Unicode 字符下标。','范围终点包含在结果中，与 Go 切片的半开区间不同。'],
'增加后缀范围 bytes=-2，检查返回最后两个字节。','保持资源不变，发送后缀请求；期望状态 206、正文 ef、范围 bytes 4-5/6。')

emit(226, r'''
package main
import("fmt";"mime";"strconv";"strings")
func choose(accept string)string{
 best:="";quality:=0.0
 for _,part:=range strings.Split(accept,","){media,params,err:=mime.ParseMediaType(strings.TrimSpace(part));if err!=nil{continue};q:=1.0;if value,ok:=params["q"];ok{q,err=strconv.ParseFloat(value,64);if err!=nil||q<0||q>1{continue}}
  if media!="text/plain"&&media!="application/json"{continue};if q>quality{best=media;quality=q}
 };return best
}
func main(){for _,input:=range []string{"application/json;q=0.4, text/plain;q=0.9","text/plain;q=0, application/json;q=0","text/plain;q=bad, application/json"}{fmt.Printf("selected=%q\n",choose(input))}}
''', 'selected="text/plain"\nselected=""\nselected="application/json"',
'Accept 中的 q 表示可接受格式的相对权重，缺省值是一，零表示拒绝。示例仅支持明确的 text/plain 和 application/json，逐项解析参数并选择最高正权重；权重相同保留先出现的格式。坏权重和不支持类型被跳过，没有可接受项时返回空结果。它是范围明确的教学协商器，尚未实现通配符和完整 HTTP 优先级规则。',
['q=0 不能当成缺省权重，它明确表示不可接受。','按字符串包含 json 做判断会忽略权重、参数格式和不支持媒体类型。'],
'让空选择在 HTTP 处理器中转换成 406 状态。','调用 choose 后检查空字符串；非空才设置对应 Content-Type 并输出资源。')

emit(227, r'''
package main
import("fmt";"net/http";"net/http/httptest")
func main(){
 w:=httptest.NewRecorder();http.SetCookie(w,&http.Cookie{Name:"session",Value:"local-42",Path:"/",HttpOnly:true,Secure:true,SameSite:http.SameSiteLaxMode})
 response:=w.Result();defer response.Body.Close();cookies:=response.Cookies();if len(cookies)!=1{panic("cookie count")};cookie:=cookies[0]
 fmt.Printf("httponly=%t secure=%t lax=%t\n",cookie.HttpOnly,cookie.Secure,cookie.SameSite==http.SameSiteLaxMode)
 r:=httptest.NewRequest("GET","https://example.test/",nil);r.AddCookie(cookie);read,err:=r.Cookie("session");if err!=nil{panic(err)};fmt.Printf("request-value=%s\n",read.Value)
 _,err=r.Cookie("missing");fmt.Printf("missing=%t\n",err==http.ErrNoCookie)
}
''', 'httponly=true secure=true lax=true\nrequest-value=local-42\nmissing=true',
'Set-Cookie 携带服务器设置的属性，后续 Cookie 请求头只回传名字和值。程序先解析响应中的 HttpOnly、Secure 和 SameSite，再通过 AddCookie 构造本地请求并读回值。读取不存在的键返回 ErrNoCookie。Recorder 和手工请求不会执行浏览器的 Cookie 策略，本例验证协议字段往返，不等于浏览器行为验收。',
['请求 Cookie 头不会回传 HttpOnly 等属性，不能在请求端据此判断原设置。','Secure 依赖真实浏览器和 HTTPS 发送策略，内存 AddCookie 不会自动实施这些约束。'],
'增加另一个偏好 Cookie，并按名字逐个读取。','为响应分别调用 SetCookie；解析得到两个 Cookie 后逐个 AddCookie，避免把整条 Set-Cookie 当成一个值。')

emit(228, r'''
package main
import("fmt";"net/url";"sort")
func main(){
 input,err:=url.ParseQuery("tag=offline&secret=x&page=2&tag=go");if err!=nil{panic(err)}
 allowed:=map[string]bool{"tag":true,"page":true};clean:=url.Values{};dropped:=0
 for key,values:=range input{if !allowed[key]{dropped++;continue};copyValues:=append([]string(nil),values...);sort.Strings(copyValues);clean[key]=copyValues}
 fmt.Printf("query=%s\ndropped-keys=%d\ntag-count=%d\n",clean.Encode(),dropped,len(clean["tag"]))
 _,err=url.ParseQuery("name=%ZZ");fmt.Printf("invalid-escape=%t\n",err!=nil)
}
''', 'query=page=2&tag=go&tag=offline\ndropped-keys=1\ntag-count=2\ninvalid-escape=true',
'ParseQuery 将同名参数保留为值切片，白名单过滤只复制允许键。为让签名输入或缓存键稳定，程序同时排序每个键下的值，Encode 再按键排序生成规范查询串。示例保留两个 tag 并删除 secret，还检测非法百分号转义。排序值是本例的业务决定，若参数顺序有意义就应保留原序。',
['Values.Get 只返回第一个值，不能用于需要保留重复参数的规范化。','对值排序会改变顺序敏感协议的语义，应先确认业务约定。'],
'限制 tag 最多三个值，重复相同 tag 只保留一个。','排序后线性去重，再检查去重后的长度；不要悄悄截断超额参数。')

emit(229, r'''
package main
import("fmt";"net/url")
func main(){
 base,err:=url.Parse("https://example.test/docs/guide/?lang=en");if err!=nil{panic(err)}
 for _,text:=range []string{"../api.html","?lang=zh","#usage","/assets/a.png"}{ref,err:=url.Parse(text);if err!=nil{panic(err)};resolved:=base.ResolveReference(ref);fmt.Printf("%s -> %s\n",text,resolved.String())}
 fmt.Printf("base-unchanged=%t\n",base.RawQuery=="lang=en")
}
''', '../api.html -> https://example.test/docs/api.html\n?lang=zh -> https://example.test/docs/guide/?lang=zh\n#usage -> https://example.test/docs/guide/?lang=en#usage\n/assets/a.png -> https://example.test/assets/a.png\nbase-unchanged=true',
'ResolveReference 按 URL 规则合并相对引用，而不是按文件路径简单拼接。基准路径以斜线结尾，明确代表目录；上级引用先退出该目录，单独查询只更新查询部分，片段引用保留原查询，斜线开头从站点根路径开始。示例检查基准 URL 未被修改。example.test 只作为语法数据，程序没有发起任何网络请求。',
['基准 URL 末尾是否有斜线会影响它被视为文件还是目录。','相对引用也可能以双斜线更换主机，处理用户链接时应验证最终主机。'],
'去掉基准 URL 路径末尾的斜线，再比较 api.html 的结果。','目录基准 /docs/guide/ 得到 /docs/guide/api.html；无末尾斜线的 /docs/guide 被视为文件位置，得到 /docs/api.html。')

emit(230, r'''
package main
import("bufio";"fmt";"io";"net/http";"strings")
func main(){
 wire:="HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nTrailer: X-Total\r\n\r\n3\r\ngo!\r\n2\r\nok\r\n0\r\nX-Total: 5\r\n\r\n"
 r,err:=http.ReadResponse(bufio.NewReader(strings.NewReader(wire)),nil);if err!=nil{panic(err)}
 before:=r.Trailer.Get("X-Total");body,err:=io.ReadAll(r.Body);r.Body.Close();if err!=nil{panic(err)}
 fmt.Printf("status=%d\nbody=%s\ntrailer-before=%q\ntrailer-after=%s\n",r.StatusCode,body,before,r.Trailer.Get("X-Total"))
}
''', 'status=200\nbody=go!ok\ntrailer-before=""\ntrailer-after=5',
'ReadResponse 解析完整 HTTP/1.1 报文，Body 自动移除 chunked 的长度行和分隔符。Trailer 的字段名先声明在头部，真正值要读到正文末尾才可用。示例在读取前后分别取 X-Total，证明尾部数据的时机。分块长度以十六进制表示，不能把它当作正文内容。',
['未读到 EOF 就使用 Trailer，可能只看到空值。','Body 需要关闭，且 ReadAll 的错误必须检查，不能把截断报文当成成功。'],
'将一个分块声明长度改得比实际数据更大，确认读取正文时报错。','保持 HTTP 头合法，仅破坏 chunk 长度；区分 ReadResponse 的头部错误和 ReadAll 的分块解析错误。')
