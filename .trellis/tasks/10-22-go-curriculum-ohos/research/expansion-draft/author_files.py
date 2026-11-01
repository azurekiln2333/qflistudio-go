"""Author T181-T190 file and virtual-filesystem drafts."""
from author_common import lesson

lesson(181, "项目路径约束", ["path.Clean", "相对路径", "词法边界"],
       "清洗项目相对路径并拒绝绝对路径、根目录与越界路径，明确词法检查边界。",
       "本协议使用斜线分隔的项目路径，先拒绝绝对路径与反斜杠，再 Clean 折叠冗余段。清洗后为点、双点或以 ../ 开头的路径不指向有效项目文件。notes 内的正常回退可接受，跨出根目录则拒绝。这是词法规则，无法识别符号链接实际指向；真实写文件还需要解析父目录并检查最终归属，不能把 Clean 当作完整文件系统安全保证。",
       ["直接检查字符串是否含双点会误伤合法文件名，也可能漏掉清洗后的越界。", "词法包含关系无法防止目录中的符号链接指向项目外。"],
       "允许普通文件名 notes..txt，继续拒绝 ../notes.txt，并说明差别。",
       "对 Clean 后的完整路径段判断越界，notes..txt 只是单个名称；不要用 Contains(双点) 作为拒绝条件。",
       r'''
       package main
       import ("fmt"; "path"; "strings")

       func projectPath(input string)(string,error) {
           if input=="" || path.IsAbs(input) || strings.Contains(input,`\`) { return "",fmt.Errorf("invalid relative path") }
           clean:=path.Clean(input)
           if clean=="." || clean==".." || strings.HasPrefix(clean,"../") { return "",fmt.Errorf("outside project") };return clean,nil
       }
       func main() {
           clean,err:=projectPath("docs/../notes/main.go");if err!=nil { panic(err) };fmt.Printf("clean=%s\n",clean)
           for _,input:=range []string{"../secret","/tmp/x",`dir\file`} { _,err:=projectPath(input);fmt.Printf("rejected=%t\n",err!=nil) }
       }
       ''', "clean=notes/main.go\nrejected=true\nrejected=true\nrejected=true")

lesson(182, "内存配置文件树", ["testing/fstest.MapFS", "fs.Sub", "fs.ReadFile", "JSON 配置"],
       "从内存文件树读取默认与子目录配置，并识别不存在的文件。",
       "MapFS 提供与真实文件系统相同的 fs.FS 读取接口，适合离线夹具。默认配置从根读取，开发配置通过 fs.Sub 建立子树视图，然后仍以 config.json 读取；调用者无需知道底层来自磁盘还是内存。缺失文件使用 errors.Is 与 fs.ErrNotExist 分类。这里分别读取两份完整配置，不把零值默认等同于字段级覆盖策略。",
       ["fs.FS 路径使用斜线且不能以斜线开头，与平台绝对路径不同。", "Sub 改变视图根，之后的路径不应再次包含原子目录前缀。"],
       "再加入测试配置子树，并用同一个 load 函数读取。",
       "添加 profiles/test/config.json，fs.Sub 选择 profiles/test 后调用 load(sub,config.json)，不要为每个环境复制解析函数。",
       r'''
       package main
       import ("encoding/json"; "errors"; "fmt"; "io/fs"; "testing/fstest")

       type Config struct { Port int `json:"port"` }
       func load(tree fs.FS,name string)(Config,error) { var cfg Config;data,err:=fs.ReadFile(tree,name);if err!=nil{return cfg,err};err=json.Unmarshal(data,&cfg);return cfg,err }
       func main() {
           tree:=fstest.MapFS{"defaults.json":&fstest.MapFile{Data:[]byte(`{"port":8080}`)},"profiles/dev/config.json":&fstest.MapFile{Data:[]byte(`{"port":9090}`)}}
           defaults,err:=load(tree,"defaults.json");if err!=nil{panic(err)};sub,err:=fs.Sub(tree,"profiles/dev");if err!=nil{panic(err)};dev,err:=load(sub,"config.json");if err!=nil{panic(err)}
           fmt.Printf("default=%d dev=%d\n",defaults.Port,dev.Port);_,err=load(sub,"missing.json");fmt.Printf("missing=%t\n",errors.Is(err,fs.ErrNotExist))
       }
       ''', "default=8080 dev=9090\nmissing=true")

lesson(183, "Glob 与确定性列表", ["fs.Glob", "fs.WalkDir", "目录深度", "模式错误"],
       "按模式查找文档，比较单层通配和递归遍历，并处理非法匹配模式。",
       "docs/*.md 只匹配 docs 下这一层，星号不会跨越斜线，所以嵌套目录中的 c.md 不会进入 Glob 结果。递归列表则使用 WalkDir 检查文件后缀，并排序输出全部匹配项。两种工具解决不同查询，不应该把 glob 星号误当作递归搜索。非法方括号模式返回错误，不能与没有匹配项混为一谈。",
       ["Glob 的星号不跨目录分隔符，不等价于递归查找。", "没有匹配与模式语法错误是两种结果，应分别处理。"],
       "让递归查询忽略隐藏目录，但保留普通目录内的隐藏文件。",
       "在 WalkDir 回调中仅对 IsDir 且名称以点开头的节点返回 SkipDir；先排除根点，文件节点继续应用后缀规则。",
       r'''
       package main
       import ("fmt"; "io/fs"; "sort"; "strings"; "testing/fstest")

       func main() {
           tree:=fstest.MapFS{"docs/a.md":&fstest.MapFile{},"docs/b.txt":&fstest.MapFile{},"docs/nested/c.md":&fstest.MapFile{},"readme.md":&fstest.MapFile{}}
           direct,err:=fs.Glob(tree,"docs/*.md");if err!=nil{panic(err)};recursive:=[]string{}
           err=fs.WalkDir(tree,"docs",func(name string,entry fs.DirEntry,err error)error{if err!=nil{return err};if !entry.IsDir()&&strings.HasSuffix(name,".md"){recursive=append(recursive,name)};return nil});if err!=nil{panic(err)};sort.Strings(recursive)
           fmt.Printf("glob=%v\nrecursive=%v\n",direct,recursive);_,err=fs.Glob(tree,"[");fmt.Printf("bad-pattern=%t\n",err!=nil)
       }
       ''', "glob=[docs/a.md]\nrecursive=[docs/a.md docs/nested/c.md]\nbad-pattern=true")

lesson(184, "遍历时跳过目录", ["fs.WalkDir", "fs.SkipDir", "DirEntry.Info", "文件统计"],
       "遍历虚拟源码树时跳过 cache 子树，统计其余 Go 源文件数和字节数。",
       "WalkDir 回调先处理传入错误，只有确认节点是名为 cache 的目录时才返回 SkipDir。源文件通过后缀过滤，再读取 Info 的 Size，最终不把缓存中的大文件计入统计。SkipDir 对文件节点的含义不同，因此目录判断不可省略。样本正文只作为字节夹具，不执行其中内容，三字节与五字节两项共八字节。",
       ["对普通文件返回 SkipDir 可能跳过同目录后续项，并非只忽略该文件。", "忽略回调收到的错误会把不完整遍历伪装成完整统计。"],
       "把跳过目录名单扩展为 cache 与 vendor，并保留文件名 vendor.go。",
       "先检查 entry.IsDir，再查集合中的 entry.Name；普通文件 vendor.go 不应命中目录名单。",
       r'''
       package main
       import ("fmt"; "io/fs"; "strings"; "testing/fstest")

       func main() {
           tree:=fstest.MapFS{"src/main.go":&fstest.MapFile{Data:[]byte("abc")},"src/lib/util.go":&fstest.MapFile{Data:[]byte("12345")},"src/cache/old.go":&fstest.MapFile{Data:[]byte(strings.Repeat("x",100))},"notes.md":&fstest.MapFile{Data:[]byte("notes")}}
           files:=0;var bytes int64
           err:=fs.WalkDir(tree,".",func(name string,entry fs.DirEntry,err error)error{
               if err!=nil{return err};if entry.IsDir(){if entry.Name()=="cache"{return fs.SkipDir};return nil};if !strings.HasSuffix(name,".go"){return nil}
               info,err:=entry.Info();if err!=nil{return err};files++;bytes+=info.Size();return nil
           });if err!=nil{panic(err)};fmt.Printf("files=%d bytes=%d\n",files,bytes)
       }
       ''', "files=2 bytes=8")

lesson(185, "临时文件替换", ["os.CreateTemp", "os.Rename", "同目录替换", "清理"],
       "在同一临时目录写替代文件后 Rename，核对新内容、旧临时名消失与目录清理。",
       "替代文件与目标在同一目录，避免跨文件系统移动。先检查写入和关闭错误，再 Rename 到目标，之后读回新内容并确认替代名已不存在。目录由程序独立创建，最后显式清理且有 defer 兜底，输出不泄漏随机路径。成功重命名不等同于断电持久性保证；需要持久事务时还应研究平台相关的同步与恢复流程。",
       ["临时文件放在其他文件系统可能使 Rename 失败。", "忽略 Close 错误或把 Rename 成功当成断电持久性，会夸大写入保证。"],
       "让写替代文件的步骤失败时保留原目标内容，并验证目标仍为 old。",
       "将写入步骤封装为返回错误的函数，只有写入与关闭全部成功后才 Rename；注入写失败并读回目标确认未更改。",
       r'''
       package main
       import ("errors"; "fmt"; "os"; "path/filepath"; "strings")

       func main() {
           directory,err:=os.MkdirTemp("","qfli-replace-");if err!=nil{panic(err)};defer os.RemoveAll(directory)
           target:=filepath.Join(directory,"state.txt");if err:=os.WriteFile(target,[]byte("old\n"),0600);err!=nil{panic(err)}
           replacement,err:=os.CreateTemp(directory,"next-*");if err!=nil{panic(err)};name:=replacement.Name()
           if _,err:=replacement.WriteString("new\n");err!=nil{replacement.Close();panic(err)};if err:=replacement.Close();err!=nil{panic(err)}
           if err:=os.Rename(name,target);err!=nil{panic(err)};data,err:=os.ReadFile(target);if err!=nil{panic(err)};_,gone:=os.Stat(name)
           fmt.Printf("content=%s source-gone=%t\n",strings.TrimSuffix(string(data),"\n"),errors.Is(gone,os.ErrNotExist))
           if err:=os.RemoveAll(directory);err!=nil{panic(err)};_,err=os.Stat(directory);fmt.Printf("cleaned=%t\n",errors.Is(err,os.ErrNotExist))
       }
       ''', "content=new source-gone=true\ncleaned=true")

lesson(186, "目录树差异清单", ["fs.WalkDir", "内容快照", "bytes.Equal", "集合并集"],
       "比较两棵虚拟文件树，稳定列出新增、删除和内容修改文件。",
       "快照函数把每个文件路径映射到原始字节，忽略目录节点；对两份路径集合求并集再排序。只在新树出现是新增，只在旧树出现是删除，两边都有但字节不同是修改，相同内容不输出。这里按内容比较，不依赖修改时间，适合小型离线工程；大树应使用流式摘要和资源预算而非无界保留全部字节。",
       ["相同大小或时间戳不代表内容相同。", "不排序并集会让变更清单顺序不稳定。"],
       "把修改输出增加为 old-bytes 和 new-bytes，但不要把目录误作文件。",
       "在 modified 分支分别计算 len(before[name]) 与 len(after[name])；快照继续只收集非目录项。",
       r'''
       package main
       import ("bytes"; "fmt"; "io/fs"; "sort"; "testing/fstest")

       func snapshot(tree fs.FS)(map[string][]byte,error) {
           files:=map[string][]byte{}
           err:=fs.WalkDir(tree,".",func(name string,entry fs.DirEntry,err error)error{if err!=nil{return err};if entry.IsDir(){return nil};data,err:=fs.ReadFile(tree,name);if err!=nil{return err};files[name]=data;return nil});return files,err
       }
       func main() {
           before,err:=snapshot(fstest.MapFS{"keep.txt":&fstest.MapFile{Data:[]byte("same")},"change.txt":&fstest.MapFile{Data:[]byte("old")},"deleted.txt":&fstest.MapFile{Data:[]byte("gone")}});if err!=nil{panic(err)}
           after,err:=snapshot(fstest.MapFS{"keep.txt":&fstest.MapFile{Data:[]byte("same")},"change.txt":&fstest.MapFile{Data:[]byte("new")},"added.txt":&fstest.MapFile{Data:[]byte("hello")}});if err!=nil{panic(err)}
           union:=map[string]bool{};for name:=range before{union[name]=true};for name:=range after{union[name]=true};names:=[]string{};for name:=range union{names=append(names,name)};sort.Strings(names)
           for _,name:=range names { old,was:=before[name];current,is:=after[name];kind:="";if !was{kind="added"}else if !is{kind="deleted"}else if !bytes.Equal(old,current){kind="modified"};if kind!=""{fmt.Printf("%s %s\n",kind,name)} }
       }
       ''', "added added.txt\nmodified change.txt\ndeleted deleted.txt")

lesson(187, "重复文件内容索引", ["crypto/sha256", "摘要分组", "稳定路径列表"],
       "按内容摘要对不同路径分组，只输出重复候选组并排除唯一文件。",
       "文件名和扩展名不同也可能包含相同字节，所以索引用 SHA-256 摘要作为键。每个组内先排序路径，再按第一条路径排序各重复组，输出便可重复。固定输入有两个重复组与一个独立文件，证明唯一项被排除。摘要匹配适合筛选候选；如果下一步会删除文件，应再按字节确认并征求明确授权，本例只输出索引。",
       ["路径不同不能证明内容不同，按文件名分组会漏掉重复内容。", "摘要匹配不是删除许可，破坏性去重前还应确认原始内容和用户选择。"],
       "输出重复候选组可节约的总字节数，但继续保留所有文件。",
       "对每组确认所有字节相等后计算 单文件大小*(组数-1)，加入溢出检查，只报告潜在节约量，不执行删除。",
       r'''
       package main
       import ("crypto/sha256"; "fmt"; "sort")

       func main() {
           files:=map[string][]byte{"a.txt":[]byte("same"),"nested/b.txt":[]byte("same"),"unique.txt":[]byte("unique"),"c.bin":[]byte("other"),"d.bin":[]byte("other")}
           index:=map[[32]byte][]string{};for name,data:=range files { digest:=sha256.Sum256(data);index[digest]=append(index[digest],name) }
           groups:=[][]string{};for _,names:=range index { if len(names)>1 { sort.Strings(names);groups=append(groups,names) } };sort.Slice(groups,func(i,j int)bool{return groups[i][0]<groups[j][0]})
           for _,names:=range groups { fmt.Printf("duplicate=%v\n",names) };fmt.Printf("groups=%d\n",len(groups))
       }
       ''', "duplicate=[a.txt nested/b.txt]\nduplicate=[c.bin d.bin]\ngroups=2")

lesson(188, "相对路径重定位", ["filepath.Rel", "filepath.Join", "根目录移动", "ToSlash"],
       "计算文档到资源的相对链接，移动工程根目录后验证链接仍指向同一相对目标。",
       "链接以来源文件所在目录为基准，而不是工程根。Rel 从 docs/guides 到 docs/images 得到 ../images/logo.svg，移动根目录后仍能由新来源目录重建正确目标。输出使用 ToSlash 统一展示，内部计算保留平台路径规则。这个例子只研究词法重定位，不打开文件，也不将相等路径字符串等同于符号链接解析后的对象身份。",
       ["以来源文件路径而非其目录作为 Rel 基准，会多出一级回退。", "展示斜线统一与实际路径计算是两件事，不能用字符串替换代替 Join/Rel。"],
       "把目标移动到另一个子目录，重新计算链接并证明旧链接不再指向新目标。",
       "构造新的目标相对位置，先用旧链接 Join 得到旧位置并比较为 false，再调用 Rel 生成新链接后验证为 true。",
       r'''
       package main
       import ("fmt"; "path/filepath"; "strings")

       func main() {
           oldRoot:="workspace-old";source:=filepath.Join(oldRoot,"docs","guides","start.md");target:=filepath.Join(oldRoot,"docs","images","logo.svg")
           relative,err:=filepath.Rel(filepath.Dir(source),target);if err!=nil{panic(err)};newRoot:="workspace-new";newSource:=filepath.Join(newRoot,"docs","guides","start.md")
           resolved:=filepath.Clean(filepath.Join(filepath.Dir(newSource),relative));expected:=filepath.Join(newRoot,"docs","images","logo.svg")
           contained,err:=filepath.Rel(newRoot,resolved);if err!=nil{panic(err)};inside:=contained!=".."&&!strings.HasPrefix(contained,".."+string(filepath.Separator))&&!filepath.IsAbs(contained)
           fmt.Printf("link=%s\nrebased=%t inside=%t\n",filepath.ToSlash(relative),resolved==expected,inside)
       }
       ''', "link=../images/logo.svg\nrebased=true inside=true")

lesson(189, "文件扩展名路由", ["path.Ext", "大小写归一", "点文件", "多后缀"],
       "按最后一个扩展名分类文件，明确点文件、多后缀和大小写规则。",
       "先取 Base 排除目录前缀，再对只有一个前导点的名称定义 dotfile 类别，避免把 .gitignore 当作普通扩展名。其他名称使用最后一个 Ext 并转小写，archive.tar.gz 因最后扩展名为 gz 归入压缩类，而 .config.json 仍归 JSON。扩展名路由只是命名规则，不证明文件真实内容类型，也不授权执行文件。",
       ["多后缀文件的最后一个扩展名不等于整个格式链。", "扩展名是可修改的名称信息，不能替代内容校验。"],
       "单独识别 tar.gz，同时保持普通 .gz 的类别。",
       "先对小写 Base 检查完整 .tar.gz 后缀，再走一般 Ext 分支；更具体规则应先于通用规则。",
       r'''
       package main
       import ("fmt"; "path"; "strings")

       func category(name string)string {
           base:=path.Base(name);if strings.HasPrefix(base,".")&&strings.Count(base,".")==1{return "dotfile"}
           switch strings.ToLower(path.Ext(base)){case ".go":return "go";case ".json":return "json";case ".gz",".zip":return "compressed";case "":return "plain";default:return "unknown"}
       }
       func main(){for _,name:=range []string{"main.GO","archive.tar.gz",".gitignore",".config.json","README","name."}{fmt.Printf("%s=%s\n",name,category(name))}}
       ''', "main.GO=go\narchive.tar.gz=compressed\n.gitignore=dotfile\n.config.json=json\nREADME=plain\nname.=unknown")

lesson(190, "文件权限位解释", ["fs.FileMode", "Perm", "目录位", "特殊模式位"],
       "把 FileMode 的读写执行位转换为可读摘要，并单独解释目录与 setuid 标志。",
       "Perm 只保留最低九个普通权限位，按所有者、组与其他人的 rwx 顺序转成文本。ModeDir 和 ModeSetuid 位于另一组模式标志中，需要独立检查，不能混进九位权限。示例使用内存中的模式值演示解释，不修改真实文件权限；实际访问还会受平台、ACL 和当前身份影响，摘要不是一次访问许可判定。",
       ["把目录与 setuid 标志当成普通权限低位会产生错误摘要。", "权限元数据不完整决定真实访问结果，平台和 ACL 仍有影响。"],
       "增加 sticky 标志显示，但保持九位 rwx 文本不变。",
       "通过 mode&fs.ModeSticky!=0 单独输出 sticky 布尔值；Perm 的九位计算继续只处理普通权限。",
       r'''
       package main
       import ("fmt"; "io/fs")

       func permissions(mode fs.FileMode)string {
           result:=[]byte("---------");symbols:="rwxrwxrwx"
           for i:=0;i<9;i++ { if mode.Perm()&(1<<uint(8-i))!=0 { result[i]=symbols[i] } };return string(result)
       }
       func main(){for _,item:=range []struct{Name string;Mode fs.FileMode}{{"file",0640},{"directory",fs.ModeDir|0750},{"special",fs.ModeSetuid|0755}}{fmt.Printf("%s perms=%s dir=%t setuid=%t\n",item.Name,permissions(item.Mode),item.Mode&fs.ModeDir!=0,item.Mode&fs.ModeSetuid!=0)}}
       ''', "file perms=rw-r----- dir=false setuid=false\ndirectory perms=rwxr-x--- dir=true setuid=false\nspecial perms=rwxr-xr-x dir=false setuid=true")
