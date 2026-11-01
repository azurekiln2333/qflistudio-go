"""Author T191-T200 configuration and CLI drafts without invoking a shell."""
from author_common import lesson

lesson(191, "独立 FlagSet 子命令", ["flag.FlagSet", "ContinueOnError", "捕获诊断", "子命令"],
       "分别解析 import 与 export 子命令，把错误写到私有缓冲并返回而不退出进程。",
       "每次调用建立独立 FlagSet 并使用 ContinueOnError，避免污染全局标志或让解析错误结束应用。诊断通过 SetOutput 写入 bytes.Buffer，业务结果与错误分开返回。import 要求 source，export 的 limit 必须为正，未知命令与多余位置参数都明确失败。示例传入固定参数切片，只演示解析，不执行导入或启动 shell。",
       ["默认全局 flag 可能退出进程或积累重复定义，不适合可重复嵌入调用。", "参数类型解析成功后仍需验证 source 非空、limit 为正等业务条件。"],
       "增加 export 的 format 标志，仅允许 json 或 csv。",
       "在 export 专属 FlagSet 注册字符串，Parse 成功后用 switch 校验允许值，不把未知格式自动改成默认值。",
       r'''
       package main
       import ("bytes"; "flag"; "fmt")

       func execute(arguments []string)(string,string,error) {
           if len(arguments)==0{return "","",fmt.Errorf("missing command")};var diagnostics bytes.Buffer
           flags:=flag.NewFlagSet(arguments[0],flag.ContinueOnError);flags.SetOutput(&diagnostics)
           source:="";limit:=0
           switch arguments[0]{case "import":flags.StringVar(&source,"source","","source file");case "export":flags.IntVar(&limit,"limit",10,"record limit");default:return "","",fmt.Errorf("unknown command")}
           if err:=flags.Parse(arguments[1:]);err!=nil{return "",diagnostics.String(),err};if flags.NArg()!=0{return "",diagnostics.String(),fmt.Errorf("unexpected positional arguments")}
           if arguments[0]=="import"{if source==""{return "","",fmt.Errorf("missing source")};return "import source="+source,"",nil}
           if limit<1{return "","",fmt.Errorf("invalid limit")};return fmt.Sprintf("export limit=%d",limit),"",nil
       }
       func main(){for _,arguments:=range [][]string{{"import","-source","notes.json"},{"export","-limit","3"}}{result,_,err:=execute(arguments);if err!=nil{panic(err)};fmt.Println(result)};_,diagnostics,err:=execute([]string{"export","-limit","no"});fmt.Printf("parse-error=%t captured=%t\n",err!=nil,len(diagnostics)>0);_,_,err=execute([]string{"delete"});fmt.Printf("unknown=%t\n",err!=nil)}
       ''', "import source=notes.json\nexport limit=3\nparse-error=true captured=true\nunknown=true")

lesson(192, "环境键值快照", ["strings.Cut", "strconv.Atoi", "重复键", "默认值"],
       "从显式环境切片读取配置，按后值覆盖规则处理重复键并拒绝坏端口。",
       "环境输入作为普通切片传入，解析过程既不读取也不修改宿主环境。Cut 只按第一个等号拆分，所以标签中的 a=b 可以完整保留。重复键采用后出现者覆盖，缺失端口使用默认八零八零；存在但为空或不是合法整数则返回错误，不能混同于缺失。端口最后验证一到六五五三五的业务范围。",
       ["Split 后只取第二项会截断值中的等号。", "缺失与显式空值不同，不能都默默使用默认配置。"],
       "为重复键改成报错策略，同时给出重复键名。",
       "写入快照 map 前检查键是否已存在，若存在返回包含键名的错误；保持每项只在第一个等号分隔。",
       r'''
       package main
       import ("fmt"; "strconv"; "strings")

       type Config struct{Port int;Label string}
       func load(environment []string)(Config,error){values:=map[string]string{};for _,entry:=range environment{key,value,ok:=strings.Cut(entry,"=");if !ok||key==""{return Config{},fmt.Errorf("bad environment entry")};values[key]=value};cfg:=Config{Port:8080,Label:"default"};if value,exists:=values["APP_PORT"];exists{port,err:=strconv.Atoi(value);if err!=nil||port<1||port>65535{return Config{},fmt.Errorf("invalid port")};cfg.Port=port};if value,exists:=values["APP_LABEL"];exists{cfg.Label=value};return cfg,nil}
       func main(){cfg,err:=load([]string{"APP_PORT=9000","APP_LABEL=a=b","APP_PORT=9100"});if err!=nil{panic(err)};defaults,err:=load(nil);if err!=nil{panic(err)};fmt.Printf("port=%d label=%s default=%d\n",cfg.Port,cfg.Label,defaults.Port);_,err=load([]string{"APP_PORT=no"});fmt.Printf("bad-integer=%t\n",err!=nil)}
       ''', "port=9100 label=a=b default=8080\nbad-integer=true")

lesson(193, "多来源配置优先级", ["JSON 部分配置", "显式 false", "来源追踪", "覆盖顺序"],
       "按默认、文件、环境和命令行顺序覆盖配置，并记录每个最终字段的来源。",
       "各来源被转换为只包含实际提供字段的 JSON 对象，再通过同一个 apply 函数依次覆盖。字段是否存在由 RawMessage map 判断，所以命令行明确给出的 false 能覆盖文件中的 true，而未给出的 port 不会重置环境端口。每次成功赋值同步记录来源，最终可解释为何端口为九千、调试为 false。示例环境与命令行已经是固定解析输入，不访问宿主状态。",
       ["用零值判断字段是否提供会丢掉用户明确设置的 false。", "来源记录必须跟随成功赋值更新，解析失败不能先修改来源。"],
       "遍历全部配置来源并收集各层错误；失败层不得覆盖之前的有效值，后续有效层仍应生效。",
       "保留 apply 的候选副本提交方式，在来源循环中将失败记录为包含来源名的诊断并继续；全部来源处理后同时返回最终有效配置、来源映射和诊断列表。",
       r'''
       package main
       import ("encoding/json"; "fmt")

       type Config struct{Port int;Debug bool}
       func apply(cfg *Config,sources map[string]string,origin,text string)error{
           var fields map[string]json.RawMessage;if err:=json.Unmarshal([]byte(text),&fields);err!=nil{return err};candidate:=*cfg
           for name,raw:=range fields{switch name{case "port":if err:=json.Unmarshal(raw,&candidate.Port);err!=nil{return err};if candidate.Port<1||candidate.Port>65535{return fmt.Errorf("invalid port")};case "debug":if err:=json.Unmarshal(raw,&candidate.Debug);err!=nil{return err};default:return fmt.Errorf("unknown field")}}
           *cfg=candidate;for name:=range fields{sources[name]=origin};return nil
       }
       func main(){cfg:=Config{8080,false};sources:=map[string]string{"port":"default","debug":"default"};for _,layer:=range []struct{Name string;JSON string}{{"file",`{"port":7000,"debug":true}`},{"environment",`{"port":9000}`},{"cli",`{"debug":false}`}}{if err:=apply(&cfg,sources,layer.Name,layer.JSON);err!=nil{panic(err)}};fmt.Printf("port=%d source=%s\ndebug=%t source=%s\n",cfg.Port,sources["port"],cfg.Debug,sources["debug"])}
       ''', "port=9000 source=environment\ndebug=false source=cli")

lesson(194, "受控变量展开", ["os.Expand", "映射回调", "缺失变量", "美元符转义"],
       "用显式变量表展开模板，区分缺失键、空值、转义美元符与普通文字。",
       "os.Expand 通过映射函数请求变量，回调从给定 map 查询而不读取环境。存在但为空的 EMPTY 合法，缺失键则被记录并让整次展开返回错误。双美元符对应特殊变量名美元，回调把它还原为普通美元字符，因此 $$5 显示为 $5。普通方括号文本保持不变；本例遵循 Expand 的变量语法，不宣称提供任意模板语言。",
       ["把缺失键和空字符串混在一起，会悄悄生成不完整路径。", "直接使用 ExpandEnv 会引入宿主环境依赖，失去显式输入的可重复性。"],
       "同一个缺失变量出现多次时，只在错误中列出一次。",
       "回调内部维护 missingSeen 集合，首次缺失才追加有序列表；仍然拒绝整次结果，不返回被截断的成功文本。",
       r'''
       package main
       import ("fmt"; "os"; "strings")

       func expand(text string,values map[string]string)(string,error){missing:=[]string{};result:=os.Expand(text,func(name string)string{if name=="$"{return "$"};value,ok:=values[name];if !ok{missing=append(missing,name)};return value});if len(missing)>0{return "",fmt.Errorf("missing variables: %s",strings.Join(missing,","))};return result,nil}
       func main(){values:=map[string]string{"ROOT":"docs","NAME":"guide","EMPTY":""};result,err:=expand(`${ROOT}/$NAME cost=$$5 empty=${EMPTY}`,values);if err!=nil{panic(err)};fmt.Printf("expanded=%s\n",result);_,err=expand(`${MISSING}`,values);fmt.Printf("missing=%t\n",err!=nil);plain,err:=expand("hello[world]",values);if err!=nil{panic(err)};fmt.Printf("plain=%s\n",plain)}
       ''', "expanded=docs/guide cost=$5 empty=\nmissing=true\nplain=hello[world]")

lesson(195, "INI 分节解析", ["bufio.Scanner", "分节状态", "重复键", "行号错误"],
       "解析带分节的键值配置，处理注释、空行、重复键与结构化行号错误。",
       "解析器维护当前分节，忽略空行与整行注释，键值用第一个等号拆分。节名和键都必须非空，分节之前不接受键，重复的节内键直接返回带行号错误。错误结构把 Line 与 Reason 分开，调用者不必解析格式化文本就能定位问题。这里不支持引号、转义或行尾注释，因此含分号的普通值不会被擅自截断。",
       ["INI 有多种方言，必须明确支持的注释和引号规则。", "重复键策略不能依赖 map 最终值，解析时就应选择覆盖或拒绝。"],
       "把当前允许重复声明节名的规则改为严格模式：第二次声明同名节时返回带当前行号的错误。",
       "在节名非空检查后判断 result 中是否已有该节；已有则返回 LineError，尚未出现才创建节内 map。键重复检查保持不变。",
       r'''
       package main
       import ("bufio"; "fmt"; "strings")

       type LineError struct{Line int;Reason string}
       func(e *LineError)Error()string{return fmt.Sprintf("line %d: %s",e.Line,e.Reason)}
       func parse(text string)(map[string]map[string]string,error){result:=map[string]map[string]string{};section:="";scanner:=bufio.NewScanner(strings.NewReader(text));line:=0;for scanner.Scan(){line++;row:=strings.TrimSpace(scanner.Text());if row==""||strings.HasPrefix(row,"#")||strings.HasPrefix(row,";"){continue};if strings.HasPrefix(row,"["){if !strings.HasSuffix(row,"]"){return nil,&LineError{line,"unclosed section"}};section=strings.TrimSpace(row[1:len(row)-1]);if section==""{return nil,&LineError{line,"empty section"}};if result[section]==nil{result[section]=map[string]string{}};continue};key,value,ok:=strings.Cut(row,"=");key=strings.TrimSpace(key);if !ok||key==""||section==""{return nil,&LineError{line,"invalid key-value"}};if _,exists:=result[section][key];exists{return nil,&LineError{line,"duplicate key"}};result[section][key]=strings.TrimSpace(value)};if err:=scanner.Err();err!=nil{return nil,err};return result,nil}
       func main(){cfg,err:=parse("# local\n[server]\nport=8080\n\n[ui]\ntheme=dark\n");if err!=nil{panic(err)};fmt.Printf("server.port=%s ui.theme=%s\n",cfg["server"]["port"],cfg["ui"]["theme"]);_,err=parse("[server]\nport=1\nport=2");problem,ok:=err.(*LineError);fmt.Printf("duplicate-line3=%t\n",ok&&problem.Line==3);_,err=parse("[server]\nport");problem,ok=err.(*LineError);fmt.Printf("malformed-line2=%t\n",ok&&problem.Line==2)}
       ''', "server.port=8080 ui.theme=dark\nduplicate-line3=true\nmalformed-line2=true")

lesson(196, "配置交叉字段校验", ["聚合错误", "TLS 关联约束", "time.Duration"],
       "一次返回端口、超时与 TLS 证书路径之间的全部配置约束错误。",
       "Validate 为各独立约束追加诊断而不是遇到第一个错误就退出，让用户一次修复整组问题。检查顺序固定，输出也固定；开启 TLS 要求证书和私钥路径同时存在，关闭时不允许残留路径。该层只检查配置关系，不声称路径存在或证书内容有效，后续 I/O 和密码校验仍需各自执行。",
       ["只返回第一个问题会导致用户反复修改和重试。", "路径字符串非空不证明文件存在或证书合法，不能混淆验证层次。"],
       "为每个诊断增加字段名与错误码，让界面能够定位相关输入框。",
       "将 []string 改为 []Issue，包含 Field、Code、Message；TLS 关联错误可使用字段组或明确指向缺失的 keyPath。",
       r'''
       package main
       import ("fmt"; "strings"; "time")

       type Config struct{Port int;Timeout time.Duration;TLS bool;Certificate string;Key string}
       func validate(cfg Config)[]string{issues:=[]string{};if cfg.Port<1||cfg.Port>65535{issues=append(issues,"port must be 1..65535")};if cfg.Timeout<=0{issues=append(issues,"timeout must be positive")};if cfg.TLS&&(cfg.Certificate==""||cfg.Key==""){issues=append(issues,"tls requires certificate and key")};if !cfg.TLS&&(cfg.Certificate!=""||cfg.Key!=""){issues=append(issues,"tls paths require tls enabled")};return issues}
       func main(){bad:=Config{Port:70000,TLS:true,Certificate:"cert.pem"};fmt.Printf("errors=%s\n",strings.Join(validate(bad)," | "));good:=Config{443,2*time.Second,true,"cert.pem","key.pem"};fmt.Printf("valid=%t\n",len(validate(good))==0)}
       ''', "errors=port must be 1..65535 | timeout must be positive | tls requires certificate and key\nvalid=true")

lesson(197, "表格对齐输出", ["text/tabwriter", "列宽", "Flush", "固定输出"],
       "用 TabWriter 输出不同长度字段的表格，核对列对齐和 Flush 后可见性。",
       "TabWriter 使用制表分隔的逻辑列计算统一宽度，再用空格填充。最长名称 notebook 长八，列后保留两空格，所以数量列从索引十开始。缓冲在 Flush 后成为完整文本，程序不仅展示表格，也检查表头与各行数量字段的起点一致。这里使用 ASCII 字段；终端中宽字符的实际显示宽度需要单独处理。",
       ["原始制表符的显示宽度取决于终端，TabWriter 可生成明确空格列。", "Unicode 字符数不等于终端显示格数，不能直接推广 ASCII 对齐结论。"],
       "增加橡皮 eraser 一行，保持数量列仍在索引十。",
       "新名称长度六未超过 notebook 的八，所以最大列宽不变；Flush 后检查新行数字位置依然为十。",
       r'''
       package main
       import ("bytes"; "fmt"; "strings"; "text/tabwriter")

       func main(){var buffer bytes.Buffer;writer:=tabwriter.NewWriter(&buffer,0,4,2,' ',0);if _,err:=writer.Write([]byte("name\tqty\npen\t2\nnotebook\t12\n"));err!=nil{panic(err)};fmt.Printf("before=%d\n",buffer.Len());if err:=writer.Flush();err!=nil{panic(err)};fmt.Print(buffer.String());rows:=strings.Split(strings.TrimSuffix(buffer.String(),"\n"),"\n");aligned:=strings.Index(rows[0],"qty")==10&&strings.Index(rows[1],"2")==10&&strings.Index(rows[2],"12")==10;fmt.Printf("quantity-column=%t\n",aligned)}
       ''', "before=0\nname      qty\npen       2\nnotebook  12\nquantity-column=true")

lesson(198, "简单参数词法分析", ["unicode.IsSpace", "引号状态", "转义", "空参数"],
       "解析含引号和转义的参数列表，只返回数组，保留空参数而不调用 shell。",
       "状态机区分普通、单引号、双引号与待转义状态。空引号需要 active 标记，否则空参数会被错误丢弃；单引号中的反斜杠保持字面值，普通与双引号环境中的反斜杠保护下一字符。结尾仍有引号或转义即报错。本例是明确定义的小型词法器，不实现变量展开、管道或任何命令执行，也不声称完全复刻系统 shell。",
       ["只按空白 Fields 会把带引号的一个参数拆成多个。", "没有 active 标记会把合法的空引号参数当作没有参数。"],
       "增加参数数量上限三十二和每个参数的字节上限，超限时返回错误。",
       "在追加字符前检查当前字节预算，在提交 token 前检查数量；失败返回整个解析错误，不返回可被误执行的部分数组。",
       r'''
       package main
       import ("fmt"; "strings"; "unicode")

       func split(text string)([]string,error){arguments:=[]string{};var word strings.Builder;quote:=rune(0);escaped:=false;active:=false
           for _,r:=range text{if escaped{word.WriteRune(r);escaped=false;active=true;continue};if quote=='\''{if r==quote{quote=0}else{word.WriteRune(r)};continue};if quote=='"'{if r=='\\'{escaped=true}else if r==quote{quote=0}else{word.WriteRune(r)};continue};if unicode.IsSpace(r){if active{arguments=append(arguments,word.String());word.Reset();active=false};continue};active=true;if r=='\''||r=='"'{quote=r}else if r=='\\'{escaped=true}else{word.WriteRune(r)}}
           if quote!=0||escaped{return nil,fmt.Errorf("unfinished quote or escape")};if active{arguments=append(arguments,word.String())};return arguments,nil}
       func main(){arguments,err:=split(`run --name "Li Yu" 'literal\path' "" back\ slash`);if err!=nil{panic(err)};fmt.Printf("tokens=%d\n%q\n",len(arguments),arguments);_,err=split(`run "unfinished`);fmt.Printf("unclosed=%t\n",err!=nil);_,err=split(`run trailing\`);fmt.Printf("dangling=%t\n",err!=nil)}
       ''', 'tokens=6\n["run" "--name" "Li Yu" "literal\\\\path" "" "back slash"]\nunclosed=true\ndangling=true')

lesson(199, "ANSI 控制序列清理", ["SGR", "字节状态机", "UTF-8 保留", "截断错误"],
       "删除 SGR 颜色序列，保留普通方括号与中文，并拒绝截断的颜色控制。",
       "清理器只识别 ESC、左方括号、数字或分号参数、m 组成的 SGR 序列。其他控制序列保持原样而不是被误删，普通中括号文本与 UTF-8 字节直接复制。结尾截断的候选序列返回错误，避免悄悄丢弃不确定内容。范围仅限常见数字 SGR，不宣称完整终端仿真或能过滤全部终端控制风险。",
       ["删除所有方括号内容会破坏正常文本。", "ANSI 不是只有颜色，清理 SGR 不等于清理所有终端控制序列。"],
       "在严格模式下拒绝所有非 SGR 的 ESC 序列，同时保留普通无 ESC 文本。",
       "发现 ESC 后如果不能完整解析为允许的 SGR 就返回错误，普通方括号仍按字节复制；不要把控制范围扩展成删除任意括号。",
       r'''
       package main
       import ("fmt"; "strings")

       func strip(text string)(string,error){var out strings.Builder;for i:=0;i<len(text);{if text[i]==27&&i+1<len(text)&&text[i+1]=='['{j:=i+2;for j<len(text)&&((text[j]>='0'&&text[j]<='9')||text[j]==';'){j++};if j==len(text){return "",fmt.Errorf("truncated SGR")};if text[j]=='m'{i=j+1;continue}};out.WriteByte(text[i]);i++};return out.String(),nil}
       func main(){clean,err:=strip("A [tag] \x1b[31m红色\x1b[0m B");if err!=nil{panic(err)};fmt.Println(clean);other:="\x1b[2J";preserved,err:=strip(other);fmt.Printf("other-preserved=%t\n",err==nil&&preserved==other);_,err=strip("\x1b[31");fmt.Printf("truncated=%t\n",err!=nil)}
       ''', "A [tag] 红色 B\nother-preserved=true\ntruncated=true")

lesson(200, "配置补丁与未知键", ["json.RawMessage", "白名单", "失败无修改", "排序变更键"],
       "应用白名单 JSON 配置补丁，拒绝未知键并保证任何失败都不修改原配置。",
       "补丁先解码为原始字段映射，再排序键列表并在所有未知键检查通过后修改候选副本。字段类型与范围也在副本上验证，全部成功才一次赋回配置。这样即使 name 已成功解析而 port 随后失败，原资料也不受影响。返回排序后的变更键便于稳定展示；本例是字段替换协议，不自称实现完整 JSON Patch 标准。",
       ["直接在原配置上逐项解码会在后续字段失败时留下部分更新。", "白名单字段补丁与标准 JSON Patch 操作数组是不同协议，需要明确接口。"],
       "加入只读 version 字段，补丁尝试修改时返回专门错误且保持配置不变。",
       "在未知键/只读键预检阶段识别 version，返回只读错误；不要先给候选赋版本再忽略，因为调用者需要明确知道请求未被接受。",
       r'''
       package main
       import ("encoding/json"; "fmt"; "sort"; "strings")

       type Config struct{Name string;Port int;Tags []string}
       func patch(cfg *Config,text string)([]string,error){var fields map[string]json.RawMessage;if err:=json.Unmarshal([]byte(text),&fields);err!=nil{return nil,err};keys:=[]string{};for key:=range fields{keys=append(keys,key)};sort.Strings(keys);for _,key:=range keys{if key!="name"&&key!="port"&&key!="tags"{return nil,fmt.Errorf("unknown key %s",key)}};candidate:=*cfg;candidate.Tags=append([]string(nil),cfg.Tags...);for _,key:=range keys{raw:=fields[key];switch key{case "name":if err:=json.Unmarshal(raw,&candidate.Name);err!=nil{return nil,err};if strings.TrimSpace(candidate.Name)==""{return nil,fmt.Errorf("empty name")};case "port":if err:=json.Unmarshal(raw,&candidate.Port);err!=nil{return nil,err};if candidate.Port<1||candidate.Port>65535{return nil,fmt.Errorf("invalid port")};case "tags":if err:=json.Unmarshal(raw,&candidate.Tags);err!=nil{return nil,err}}};*cfg=candidate;return keys,nil}
       func main(){cfg:=Config{"local",8080,[]string{"old"}};keys,err:=patch(&cfg,`{"port":9090,"name":"dev"}`);if err!=nil{panic(err)};fmt.Printf("name=%s port=%d changed=%v\n",cfg.Name,cfg.Port,keys);_,err=patch(&cfg,`{"name":"broken","unknown":1}`);fmt.Printf("unknown=%t preserved=%t\n",err!=nil,cfg.Name=="dev"&&cfg.Port==9090);_,err=patch(&cfg,`{"name":"changed","port":"bad"}`);fmt.Printf("bad-type=%t preserved=%t\n",err!=nil,cfg.Name=="dev"&&cfg.Port==9090)}
       ''', "name=dev port=9090 changed=[name port]\nunknown=true preserved=true\nbad-type=true preserved=true")
