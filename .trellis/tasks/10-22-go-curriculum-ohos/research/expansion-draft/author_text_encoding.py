"""Author reviewed T121-T140 drafts; never write the bundled curriculum."""
from author_common import lesson


lesson(121, "统一混合换行", ["strings.ReplaceAll", "日志记录", "末行处理"],
       "统一 CRLF、CR 和 LF，保留没有结尾换行的最后一条日志。",
       "不同系统产生的日志可能混用三种行结束符。先把双字符 CRLF 替换成 LF，再替换单独的 CR，避免把一组 CRLF 拆成两个空行。只去掉表示文件结束的一枚空记录，不能对每行 TrimSpace，否则日志正文中的空格会丢失。空输入返回零条记录；没有换行结尾的 gamma 仍作为第三条记录保留。",
       ["先替换 CR 会让 CRLF 变成两个 LF，凭空增加记录。", "TrimSpace 会改变正文；不能用它代替精确处理最后一个换行。"],
       "增加输入 a\\n\\n，保留其中一条真实空日志，同时去掉结束符产生的空记录。",
       "现有实现只删除切片末尾一个空字符串，得到 [a 空字符串]；不要循环删除所有空项。",
       r'''
       package main

       import (
           "fmt"
           "strings"
       )

       func records(text string) []string {
           if text == "" { return nil }
           text = strings.ReplaceAll(text, "\r\n", "\n")
           text = strings.ReplaceAll(text, "\r", "\n")
           lines := strings.Split(text, "\n")
           if lines[len(lines)-1] == "" { lines = lines[:len(lines)-1] }
           return lines
       }

       func main() {
           lines := records("alpha\r\nbeta\rgamma")
           fmt.Printf("records=%d\n", len(lines))
           for i, line := range lines { fmt.Printf("%d:%s\n", i+1, line) }
           fmt.Printf("empty=%d trailing=%d\n", len(records("")), len(records("one\n")))
       }
       ''', "records=3\n1:alpha\n2:beta\n3:gamma\nempty=0 trailing=1")

lesson(122, "Unicode 标识清洗", ["unicode.IsLetter", "unicode.IsNumber", "rune", "strings.Builder"],
       "把含中文、空白和标点的标题清洗为稳定标识，合并分隔符。",
       "标识清洗按 Unicode 字符遍历，保留各语言字母和数字，并将字母转小写。pending 标记记录是否见过分隔符，只有遇到下一个有效字符才写入横线，因此不会生成首尾横线或连续横线。中文不是 ASCII，却仍是合法字母；全是标点的输入会得到空字符串，交给调用者决定是否拒绝。",
       ["按字节判断会拆开中文的 UTF-8 编码。", "这里采用 Unicode 小写映射，不宣称执行音译或 Unicode 规范化。"],
       "让调用者在清洗结果为空时返回错误，同时保持中文标题的结果。",
       "保留清洗函数，在包装函数中检查 result == 空字符串并返回 errors.New；不要用默认编号悄悄覆盖非法输入。",
       r'''
       package main

       import (
           "fmt"
           "strings"
           "unicode"
       )

       func identifier(text string) string {
           var out strings.Builder
           pending := false
           for _, r := range text {
               if unicode.IsLetter(r) || unicode.IsNumber(r) {
                   if pending && out.Len() > 0 { out.WriteByte('-') }
                   out.WriteRune(unicode.ToLower(r))
                   pending = false
               } else { pending = true }
           }
           return out.String()
       }

       func main() {
           fmt.Println(identifier("  Go 工具：离线 / 版本 2! "))
           fmt.Printf("merged=%s\n", identifier("A---B__C"))
           fmt.Printf("empty=%t\n", identifier(" !? ") == "")
       }
       ''', "go-工具-离线-版本-2\nmerged=a-b-c\nempty=true")

lesson(123, "日志字段脱敏", ["regexp.ReplaceAllStringFunc", "字段边界", "strings.Cut"],
       "只脱敏 email 与 token 字段，保留日志其余结构和普通消息。",
       "固定日志格式使用空白分隔的键值字段。正则要求目标键位于行首或空白之后，避免把 nottoken 当作 token；替换函数保留匹配中的前导分隔符，只将等号后的值改成星号。程序输出同时包含目标字段和普通 message、nottoken，证明替换范围受字段边界约束。此解析器不适用于带空格的引号值，不能把它当作通用日志格式解析器。",
       ["没有键边界的正则会误伤 nottoken 这样的普通字段。", "本例值不能包含空白；需要引号值时应换成完整的字段词法分析。"],
       "再脱敏 phone 字段，但不要改变 headphone 字段。",
       "将正则键分支改为 email|token|phone，保留行首或空白前缀，并加入 phone=123 headphone=ok 的测试。",
       r'''
       package main

       import (
           "fmt"
           "regexp"
           "strings"
       )

       func redact(line string) string {
           fields := regexp.MustCompile(`(^|[[:space:]])(email|token)=[^[:space:]]+`)
           return fields.ReplaceAllStringFunc(line, func(field string) string {
               key, _, _ := strings.Cut(field, "=")
               return key + "=***"
           })
       }

       func main() {
           fmt.Println(redact("10:00 INFO email=lin@example.test token=abc message=ready"))
           fmt.Println(redact("token=secret nottoken=visible message=email-help"))
       }
       ''', "10:00 INFO email=*** token=*** message=ready\ntoken=*** nottoken=visible message=email-help")

lesson(124, "词频 Top N 与并列规则", ["bufio.Scanner", "词频映射", "sort.Slice", "稳定并列规则"],
       "统计多行文档的词频，按次数降序、单词字典序处理并列并取前三名。",
       "Scanner 使用 ScanWords 把文档按空白拆词，统一小写后累加计数，再将 map 转成可排序的记录切片。比较器首先比较次数，次数相同时比较单词，因此 map 的遍历顺序不会影响结果。输入刻意让 alpha 和 gamma 次数相同，输出验证字典序决胜；N 超过词数时自动收缩，N 为零时不访问首项。标点归一化不属于此处的空白词元规则。",
       ["直接从 map 取前三项没有确定顺序。", "比较器缺少次数相同时的规则，会让并列结果不稳定。"],
       "支持负数 N 并将其作为错误返回，而不是触发切片越界。",
       "让 top 接受 N 后先判断 N < 0 并返回错误；保留 N==0 的空结果，不把负值自动改成零。",
       r'''
       package main

       import (
           "bufio"
           "fmt"
           "sort"
           "strings"
       )

       type Word struct { Text string; Count int }

       func top(text string, n int) []Word {
           counts := map[string]int{}
           scanner := bufio.NewScanner(strings.NewReader(text))
           scanner.Split(bufio.ScanWords)
           for scanner.Scan() { counts[strings.ToLower(scanner.Text())]++ }
           if err := scanner.Err(); err != nil { panic(err) }
           words := make([]Word, 0, len(counts))
           for word, count := range counts { words = append(words, Word{word, count}) }
           sort.Slice(words, func(i, j int) bool {
               if words[i].Count != words[j].Count { return words[i].Count > words[j].Count }
               return words[i].Text < words[j].Text
           })
           if n > len(words) { n = len(words) }
           return words[:n]
       }

       func main() {
           text := "Beta alpha beta\ngamma ALPHA gamma beta delta"
           for _, word := range top(text, 3) { fmt.Printf("%s=%d\n", word.Text, word.Count) }
           fmt.Printf("zero=%d all=%d\n", len(top(text, 0)), len(top(text, 99)))
       }
       ''', "beta=3\nalpha=2\ngamma=2\nzero=0 all=4")

lesson(125, "带引号键值解析", ["词法扫描", "strconv.Unquote", "转义状态", "错误边界"],
       "解析含空格与转义的 key=value 配置，并明确报告未闭合引号。",
       "解析器每次消费一个键和一个值。引号值用 escaped 状态跳过被反斜杠保护的字符，找到真正的结束引号后交给 strconv.Unquote 处理转义；普通值消费到下一个空白。引号后必须是空白或输入结尾，防止错误地接受 name=\"Lin\"junk。最后单独 ParseBool，词法正确与值的业务类型正确是两个不同检查。重复键在此采用后值覆盖策略。",
       ["只查找下一个双引号会把转义引号误当作结束位置。", "Unquote 成功不意味着 enabled 是合法布尔值，还需 ParseBool。"],
       "改为拒绝重复键，并返回重复键名。",
       "在 result[key]=value 前用 _, exists := result[key] 检查；若已存在就返回 fmt.Errorf，避免静默覆盖。",
       r'''
       package main

       import (
           "fmt"
           "strconv"
           "strings"
       )

       func parse(text string) (map[string]string, error) {
           result := map[string]string{}
           for text = strings.TrimSpace(text); text != ""; text = strings.TrimSpace(text) {
               eq := strings.IndexByte(text, '=')
               if eq < 1 { return nil, fmt.Errorf("missing key or equals") }
               key := strings.TrimSpace(text[:eq])
               text = strings.TrimSpace(text[eq+1:])
               if text == "" { return nil, fmt.Errorf("missing value for %s", key) }
               value := ""
               if text[0] == '"' {
                   end, escaped := -1, false
                   for i := 1; i < len(text); i++ {
                       if escaped { escaped = false; continue }
                       if text[i] == '\\' { escaped = true; continue }
                       if text[i] == '"' { end = i; break }
                   }
                   if end < 0 { return nil, fmt.Errorf("unclosed quote") }
                   var err error
                   value, err = strconv.Unquote(text[:end+1])
                   if err != nil { return nil, err }
                   text = text[end+1:]
                   if text != "" && !strings.ContainsAny(text[:1], " \t\r\n") {
                       return nil, fmt.Errorf("missing field separator")
                   }
               } else {
                   end := strings.IndexAny(text, " \t\r\n")
                   if end < 0 { end = len(text) }
                   value, text = text[:end], text[end:]
               }
               result[key] = value
           }
           return result, nil
       }

       func main() {
           values, err := parse(`name="Li Yu" enabled=true note="say \"hi\""`)
           if err != nil { panic(err) }
           enabled, err := strconv.ParseBool(values["enabled"])
           if err != nil { panic(err) }
           fmt.Printf("name=%s enabled=%t note=%s\n", values["name"], enabled, values["note"])
           _, err = parse(`name="unfinished`)
           fmt.Printf("unclosed=%t\n", err != nil)
           _, err = parse(`name="Lin"junk`)
           fmt.Printf("missing-separator=%t\n", err != nil)
       }
       ''', 'name=Li Yu enabled=true note=say "hi"\nunclosed=true\nmissing-separator=true')

lesson(126, "最长公共前后缀", ["strings.HasPrefix", "strings.HasSuffix", "rune 边界", "utf8.ValidString"],
       "计算多个版本文件名的公共前缀和后缀，避免切断中文字符。",
       "先用第一个文件名初始化候选前后缀，然后逐个缩短，直到所有名称都匹配。候选通过 rune 切片缩短，保证每次都移除完整字符；最后用 utf8.ValidString 验证结果。前后缀独立计算，短输入时它们可能重叠，不能直接据此切割中间部分。零个名称有明确定义，返回两个空字符串。",
       ["按字节每次减一可能留下半个中文字符。", "独立求出的前后缀可能重叠；用来提取中间文本前必须检查长度。"],
       "增加只有一个名称的输入，并说明前后缀为什么都等于完整名称。",
       "候选来自第一个名称，没有其他名称触发缩短，因此两者都保持原值；若业务要求不重叠，应另外定义截断策略。",
       r'''
       package main

       import (
           "fmt"
           "strings"
           "unicode/utf8"
       )

       func common(names []string) (string, string) {
           if len(names) == 0 { return "", "" }
           prefix, suffix := []rune(names[0]), []rune(names[0])
           for _, name := range names[1:] {
               for !strings.HasPrefix(name, string(prefix)) { prefix = prefix[:len(prefix)-1] }
               for !strings.HasSuffix(name, string(suffix)) { suffix = suffix[1:] }
           }
           return string(prefix), string(suffix)
       }

       func main() {
           prefix, suffix := common([]string{"报告-2024.csv", "报告-2025.csv", "报告-2026.csv"})
           fmt.Printf("prefix=%s suffix=%s\n", prefix, suffix)
           fmt.Printf("utf8=%t\n", utf8.ValidString(prefix) && utf8.ValidString(suffix))
           a, b := common(nil)
           fmt.Printf("empty=%t\n", a == "" && b == "")
       }
       ''', "prefix=报告-202 suffix=.csv\nutf8=true\nempty=true")

lesson(127, "逐行差异定位", ["bufio.Scanner", "最长公共子序列", "编辑脚本", "行号映射"],
       "对比两份文本，输出新增、删除与改变的内容及其原始行号。",
       "动态规划表保存从每一对行位置开始的最长公共子序列长度。回溯时相同行同时前进，不同则选择保留更多公共行的删除或新增操作；并列时固定先删除，结果便可重复。相邻的一次删除和一次新增合并显示为改变，但保留两份文件各自的行号。这里比较整行，时间和空间为行数乘积，适合小配置与短日志。",
       ["把两份文件相同行号直接比较，会把插入之后的所有行误报为改变。", "矩阵空间随两份文本行数的乘积增长，不能无预算用于巨大文件。"],
       "在分配矩阵前增加两份文本的行数乘积预算，超过预算返回错误。",
       "读取行数后先检查 len(old) 和 len(new)，用除法避免乘法溢出，再允许分配 (n+1)*(m+1) 单元。",
       r'''
       package main

       import (
           "bufio"
           "fmt"
           "strings"
       )

       func lines(text string) []string {
           result := []string{}
           scan := bufio.NewScanner(strings.NewReader(text))
           for scan.Scan() { result = append(result, scan.Text()) }
           if err := scan.Err(); err != nil { panic(err) }
           return result
       }

       type Edit struct { Kind string; Old int; New int; Text string }

       func diff(a, b []string) []Edit {
           table := make([][]int, len(a)+1)
           for i := range table { table[i] = make([]int, len(b)+1) }
           for i := len(a)-1; i >= 0; i-- {
               for j := len(b)-1; j >= 0; j-- {
                   if a[i] == b[j] { table[i][j] = table[i+1][j+1]+1
                   } else if table[i+1][j] >= table[i][j+1] { table[i][j] = table[i+1][j]
                   } else { table[i][j] = table[i][j+1] }
               }
           }
           edits := []Edit{}
           i, j := 0, 0
           for i < len(a) || j < len(b) {
               if i < len(a) && j < len(b) && a[i] == b[j] { i++; j++; continue }
               if i < len(a) && (j == len(b) || table[i+1][j] >= table[i][j+1]) {
                   edits = append(edits, Edit{"delete", i+1, j+1, a[i]}); i++
               } else { edits = append(edits, Edit{"add", i+1, j+1, b[j]}); j++ }
           }
           return edits
       }

       func main() {
           edits := diff(lines("alpha\nbeta\ngamma\ndelta\nobsolete"), lines("alpha\nBETA\ngamma\nomega\ndelta"))
           for i := 0; i < len(edits); i++ {
               edit := edits[i]
               if edit.Kind == "delete" && i+1 < len(edits) && edits[i+1].Kind == "add" {
                   next := edits[i+1]
                   fmt.Printf("change old:%d new:%d %s -> %s\n", edit.Old, next.New, edit.Text, next.Text)
                   i++
               } else if edit.Kind == "delete" { fmt.Printf("delete old:%d %s\n", edit.Old, edit.Text)
               } else { fmt.Printf("add new:%d %s\n", edit.New, edit.Text) }
           }
       }
       ''', "change old:2 new:2 beta -> BETA\nadd new:4 omega\ndelete old:5 obsolete")

lesson(128, "扫描器长行预算", ["bufio.Scanner.Buffer", "资源预算", "Scanner.Err"],
       "给逐行读取设置明确长度上限，区分可接受的长行与超预算输入。",
       "Scanner 默认限制并不等于业务预算。这里提供容量为四的初始缓冲，设置最大 token 缓冲为十二字节；九字节的长行可扩容读入，而十四字节的行触发错误。每次循环结束都检查 Err，不能把停止扫描自动当作输入正常结束。最大缓冲还需要容纳行分隔符，因此不要把该参数直接宣传为精确的正文字符数限制。",
       ["Buffer 的初始切片容量若已经大于业务上限，可能让较长 token 无需扩容就被接受。", "Scanner 停止既可能是 EOF，也可能是超长错误；必须检查 Err。"],
       "按 UTF-8 字符数限制每行最多五个字符，并保持字节读取预算。",
       "先用 Scanner 的字节上限约束内存，Scan 成功后用 utf8.RuneCountInString 检查字符数；两个预算分别报告，不混淆字节和字符。",
       r'''
       package main

       import (
           "bufio"
           "fmt"
           "strings"
       )

       func inspect(text string) (int, int, error) {
           scanner := bufio.NewScanner(strings.NewReader(text))
           scanner.Buffer(make([]byte, 4), 12)
           count, longest := 0, 0
           for scanner.Scan() {
               count++
               if len(scanner.Text()) > longest { longest = len(scanner.Text()) }
           }
           return count, longest, scanner.Err()
       }

       func main() {
           count, longest, err := inspect("short\n" + strings.Repeat("x", 9) + "\n")
           if err != nil { panic(err) }
           fmt.Printf("lines=%d longest=%d\n", count, longest)
           _, _, err = inspect(strings.Repeat("x", 14))
           fmt.Printf("oversized=%t\n", err != nil)
       }
       ''', "lines=2 longest=9\noversized=true")

lesson(129, "多模式替换优先级", ["strings.NewReplacer", "单次替换", "重叠模式优先级"],
       "一次转义日志分隔符，验证新生成文本不会二次替换，并比较重叠模式顺序。",
       "NewReplacer 在原始输入上匹配，写出的替换结果不会再次参与匹配。竖线生成的反斜杠因此不会被反斜杠规则再次放大，和依次调用多次 ReplaceAll 的行为不同。模式重叠时，参数中较早的匹配优先；第二部分用 a 与 ab 展示这一点。如果业务要优先较长模式，应在规则表中明确排序，而不能假定 Replacer 自动选择最长项。",
       ["连续 ReplaceAll 会让前一轮生成的内容参与下一轮，改变转义层数。", "重叠模式按参数顺序决胜，并非自动最长匹配。"],
       "加入制表符转义，并说明为什么生成的反斜杠不会再匹配反斜杠规则。",
       "在同一个 NewReplacer 中加入制表符到反斜杠加 t 的规则；算法只消费原始输入，所以写出的反斜杠不会重新扫描。",
       r'''
       package main

       import (
           "fmt"
           "strings"
       )

       func main() {
           escape := strings.NewReplacer("|", `\|`, `\`, `\\`, "\n", `\n`)
           fmt.Printf("escaped=%s\n", escape.Replace("a|b\\c\nnext"))
           first := strings.NewReplacer("a", "1", "ab", "2")
           longest := strings.NewReplacer("ab", "2", "a", "1")
           fmt.Printf("first=%s\n", first.Replace("ab a"))
           fmt.Printf("longest=%s\n", longest.Replace("ab a"))
       }
       ''', "escaped=a\\|b\\\\c\\nnext\nfirst=1b 1\nlongest=2 1")

lesson(130, "词边界倒排索引", ["unicode", "倒排索引", "集合交集", "sort.Ints"],
       "为三篇离线文档建立去重词索引，并求多个查询词对应文档的交集。",
       "FieldsFunc 按非字母、非数字划分词元，小写归一后把文档 ID 写入集合。同一文档里重复出现 go 仍只产生一个索引成员。查询先遍历第一个词的候选文档，再要求每个后续词都包含该 ID，最后排序输出，保证确定性。查询缺失词返回空切片；零词查询也被定义为空结果，而不是所有文档。",
       ["把出现次数当作索引列表会重复返回同一文档。", "map 集合无稳定顺序，输出前应排序 ID。"],
       "增加三个词的 AND 查询，并保证某个词不存在时快速返回空结果。",
       "现有 query 已循环检查其余词，可直接传三个词；查询前检查每个词的集合是否为空，若为空立即返回空切片。",
       r'''
       package main

       import (
           "fmt"
           "sort"
           "strings"
           "unicode"
       )

       type Index map[string]map[int]bool

       func build(documents []string) Index {
           index := Index{}
           for i, document := range documents {
               words := strings.FieldsFunc(strings.ToLower(document), func(r rune) bool {
                   return !unicode.IsLetter(r) && !unicode.IsNumber(r)
               })
               for _, word := range words {
                   if index[word] == nil { index[word] = map[int]bool{} }
                   index[word][i+1] = true
               }
           }
           return index
       }

       func query(index Index, words ...string) []int {
           result := []int{}
           if len(words) == 0 { return result }
           for id := range index[strings.ToLower(words[0])] {
               found := true
               for _, word := range words[1:] {
                   if !index[strings.ToLower(word)][id] { found = false; break }
               }
               if found { result = append(result, id) }
           }
           sort.Ints(result)
           return result
       }

       func main() {
           index := build([]string{"Go local tools go", "Go offline docs", "local offline data"})
           fmt.Printf("go=%v\n", query(index, "go"))
           fmt.Printf("go+local=%v\n", query(index, "go", "local"))
           fmt.Printf("local+offline=%v\n", query(index, "local", "offline"))
           fmt.Printf("missing=%v\n", query(index, "absent"))
       }
       ''', "go=[1 2]\ngo+local=[1]\nlocal+offline=[3]\nmissing=[]")

lesson(131, "十六进制校验输入", ["encoding/hex", "字节表示", "输入校验"],
       "解析空白分组的十六进制字节，拒绝奇数长度和非法字符并输出规范形式。",
       "输入先通过 Fields 去掉分组空白，再交给 hex.DecodeString。十六进制中的每两个字符表示一个字节，奇数长度无法组成完整字节；长度正确但出现 z 也必须失败。EncodeToString 为合法结果生成统一的小写形式，避免把原始输入的大小写或分组格式当作规范数据。这里只允许空白分组，不会偷偷忽略冒号等未声明字符。",
       ["不能用删除所有非十六进制字符的方法校验，它会把损坏输入变成另一份合法数据。", "奇数长度与非法字符是不同错误，二者都不能只返回空切片表示成功。"],
       "允许可选的 0x 前缀，同时继续拒绝字节之间的冒号。",
       "对 TrimSpace 后的整体输入只调用一次 TrimPrefix 去掉 0x，再沿用 Fields 和 DecodeString；不要对中间每个字段随意去前缀。",
       r'''
       package main

       import (
           "encoding/hex"
           "fmt"
           "strings"
       )

       func decode(text string) ([]byte, error) {
           return hex.DecodeString(strings.Join(strings.Fields(text), ""))
       }

       func main() {
           data, err := decode("0A ff\t10")
           if err != nil { panic(err) }
           fmt.Printf("bytes=%s length=%d\n", hex.EncodeToString(data), len(data))
           _, err = decode("abc")
           fmt.Printf("odd-rejected=%t\n", err != nil)
           _, err = decode("00 zz")
           fmt.Printf("invalid-rejected=%t\n", err != nil)
       }
       ''', "bytes=0aff10 length=3\nodd-rejected=true\ninvalid-rejected=true")

lesson(132, "Base32 人工核对编号", ["encoding/base32", "NoPadding", "大小写策略"],
       "生成无填充的批次编号，验证解码往返并明确小写输入的处理规则。",
       "Base32 将字节映射为较小的字符集合，适合展示和手工核对。这里选用标准字母表并关闭填充，固定批次标识 foo 对应 MZXW6。解码器的大小写规则不能靠猜测：原始小写输入被拒绝，面向人工输入的包装层可以显式转成大写后再解码。大小写归一化是产品策略，编码本身并不提供校验和或防篡改能力。",
       ["无填充编码必须使用同样的 NoPadding 解码器。", "Base32 只是编码，不是加密；编号中的原始内容可以恢复。"],
       "在编号后增加短校验码，并在转大写后先验证校验码再解码。",
       "先定义校验码算法和覆盖范围，例如对规范大写编码计算 CRC；校验失败返回错误，不把 CRC 当作身份认证。",
       r'''
       package main

       import (
           "encoding/base32"
           "fmt"
           "strings"
       )

       func main() {
           codec := base32.StdEncoding.WithPadding(base32.NoPadding)
           id := codec.EncodeToString([]byte("foo"))
           restored, err := codec.DecodeString(id)
           if err != nil { panic(err) }
           fmt.Printf("id=%s restored=%s\n", id, restored)
           lower := strings.ToLower(id)
           _, err = codec.DecodeString(lower)
           fmt.Printf("lower-rejected=%t\n", err != nil)
           normalized, err := codec.DecodeString(strings.ToUpper(lower))
           fmt.Printf("normalized=%t\n", err == nil && string(normalized) == "foo")
       }
       ''', "id=MZXW6 restored=foo\nlower-rejected=true\nnormalized=true")

lesson(133, "URL 安全 Base64 游标", ["encoding/base64", "encoding/json", "分页游标", "边界校验"],
       "把分页位置编码为 URL 安全游标，读取下一页并拒绝非法或负数位置。",
       "游标用 JSON 保存 offset 与 limit，再通过 RawURLEncoding 生成无需填充的 URL 安全字符串。读取时按相反顺序解码，并把结构校验放在切片操作之前。有效游标读取 c、d 两项，下一页位置为四；损坏编码与负偏移分别被拒绝。游标不包含签名，服务端若依赖它做权限判断还需要认证，不能因为内容经过 Base64 就信任它。",
       ["Base64 解码成功不代表 JSON 和分页范围合法。", "切片上界计算必须在验证 offset 与 limit 后进行，避免越界或溢出。"],
       "当剩余数据少于 limit 时返回剩余项，并用空游标表示结束。",
       "先计算 remaining := len(items)-offset，再取 min(limit, remaining)，只有 end < len(items) 时生成下一游标；避免先计算可能溢出的 offset+limit。",
       r'''
       package main

       import (
           "encoding/base64"
           "encoding/json"
           "fmt"
       )

       type Cursor struct { Offset int `json:"offset"`; Limit int `json:"limit"` }

       func encode(cursor Cursor) string {
           data, err := json.Marshal(cursor)
           if err != nil { panic(err) }
           return base64.RawURLEncoding.EncodeToString(data)
       }

       func decode(text string) (Cursor, error) {
           var cursor Cursor
           data, err := base64.RawURLEncoding.DecodeString(text)
           if err != nil { return cursor, err }
           if err := json.Unmarshal(data, &cursor); err != nil { return cursor, err }
           if cursor.Offset < 0 || cursor.Limit < 1 || cursor.Limit > 50 {
               return cursor, fmt.Errorf("invalid cursor bounds")
           }
           return cursor, nil
       }

       func page(items []string, cursor Cursor) ([]string, string, error) {
           if cursor.Offset < 0 || cursor.Offset > len(items) || cursor.Limit < 1 || cursor.Limit > 50 {
               return nil, "", fmt.Errorf("invalid page bounds")
           }
           count := len(items)-cursor.Offset
           if count > cursor.Limit { count = cursor.Limit }
           end := cursor.Offset+count
           next := ""
           if end < len(items) { next = encode(Cursor{end, cursor.Limit}) }
           return items[cursor.Offset:end], next, nil
       }

       func main() {
           cursor, err := decode(encode(Cursor{2, 2}))
           if err != nil { panic(err) }
           items, next, err := page([]string{"a", "b", "c", "d", "e"}, cursor)
           if err != nil { panic(err) }
           nextCursor, err := decode(next)
           if err != nil { panic(err) }
           fmt.Printf("page=%v next=%d\n", items, nextCursor.Offset)
           _, err = decode("*")
           fmt.Printf("invalid=%t\n", err != nil)
           _, err = decode(encode(Cursor{-1, 2}))
           fmt.Printf("negative=%t\n", err != nil)
       }
       ''', "page=[c d] next=4\ninvalid=true\nnegative=true")

lesson(134, "严格 JSON 配置", ["json.Decoder", "DisallowUnknownFields", "默认值", "尾随输入"],
       "严格读取配置，拒绝未知字段和尾随第二个 JSON 值，并保留缺失字段的默认值。",
       "解码前初始化默认配置，JSON 中未出现的字段保持原值，而显式 false 会覆盖 true。DisallowUnknownFields 阻止拼错字段被静默忽略；首次 Decode 成功之后还要再次解码并要求 io.EOF，才能拒绝两个相邻 JSON 对象。默认值、结构校验与完整输入校验分别解决不同问题，不能只完成其中一步。",
       ["把 false 视作缺失会覆盖用户明确关闭的选项。", "第一次 Decode 成功后输入仍可能有第二个值，必须检查 EOF。"],
       "增加 timeout 必须大于零且不超过六十秒的业务约束。",
       "在两次解码检查全部成功之后验证 Timeout 范围；这样未知字段或尾随内容不会被业务检查掩盖。",
       r'''
       package main

       import (
           "encoding/json"
           "fmt"
           "io"
           "strings"
       )

       type Config struct { Name string `json:"name"`; Timeout int `json:"timeout"`; Enabled bool `json:"enabled"` }

       func load(text string) (Config, error) {
           cfg := Config{Name: "default", Timeout: 3, Enabled: true}
           decoder := json.NewDecoder(strings.NewReader(text))
           decoder.DisallowUnknownFields()
           if err := decoder.Decode(&cfg); err != nil { return cfg, err }
           var extra interface{}
           if err := decoder.Decode(&extra); err != io.EOF {
               if err == nil { err = fmt.Errorf("second JSON value") }
               return cfg, err
           }
           return cfg, nil
       }

       func main() {
           cfg, err := load(`{"name":"local","enabled":false}`)
           if err != nil { panic(err) }
           fmt.Printf("name=%s timeout=%d enabled=%t\n", cfg.Name, cfg.Timeout, cfg.Enabled)
           _, err = load(`{"timeuot":8}`)
           fmt.Printf("unknown=%t\n", err != nil)
           _, err = load(`{} {}`)
           fmt.Printf("trailing=%t\n", err != nil)
       }
       ''', "name=local timeout=3 enabled=false\nunknown=true\ntrailing=true")

lesson(135, "JSON 多态消息", ["json.RawMessage", "事件判别", "分阶段解码"],
       "先读取事件类型，再解码对应载荷，拒绝未知类型和字段类型错误。",
       "消息外层先解码 kind 和 RawMessage，不急于猜测 payload 的结构。switch 根据 kind 选择用户或配额结构，再进行第二次解码和必要字段检查。两种事件可共享外层协议，但各自有明确的载荷契约；未知 kind 直接报错，配额数字被写成字符串也不会混过去。这个结构比 map[string]interface{} 的反复类型断言更清晰。",
       ["RawMessage 保存原始 JSON 字节，不能直接把它当作已验证的业务对象。", "未知事件类型不应悄悄走默认成功分支。"],
       "新增 rename 事件，要求同时包含非空 old 与 new 字段。",
       "在 switch 添加专属结构和分支，Unmarshal 成功后分别检查两个字段；不要让它复用仅检查 name 的用户分支。",
       r'''
       package main

       import (
           "encoding/json"
           "fmt"
       )

       type Envelope struct { Kind string `json:"kind"`; Payload json.RawMessage `json:"payload"` }

       func describe(text string) (string, error) {
           var event Envelope
           if err := json.Unmarshal([]byte(text), &event); err != nil { return "", err }
           switch event.Kind {
           case "user":
               var user struct { Name string `json:"name"` }
               if err := json.Unmarshal(event.Payload, &user); err != nil { return "", err }
               if user.Name == "" { return "", fmt.Errorf("missing name") }
               return "user="+user.Name, nil
           case "quota":
               var quota struct { Limit int `json:"limit"` }
               if err := json.Unmarshal(event.Payload, &quota); err != nil { return "", err }
               if quota.Limit < 1 { return "", fmt.Errorf("invalid limit") }
               return fmt.Sprintf("limit=%d", quota.Limit), nil
           default:
               return "", fmt.Errorf("unknown kind %q", event.Kind)
           }
       }

       func main() {
           for _, input := range []string{`{"kind":"user","payload":{"name":"Lin"}}`, `{"kind":"quota","payload":{"limit":8}}`} {
               line, err := describe(input)
               if err != nil { panic(err) }
               fmt.Println(line)
           }
           _, err := describe(`{"kind":"future","payload":{}}`)
           fmt.Printf("unknown=%t\n", err != nil)
           _, err = describe(`{"kind":"quota","payload":{"limit":"bad"}}`)
           fmt.Printf("bad-payload=%t\n", err != nil)
       }
       ''', "user=Lin\nlimit=8\nunknown=true\nbad-payload=true")

lesson(136, "JSON 部分更新的三态", ["json.RawMessage", "缺失与 null", "指针", "原子更新"],
       "区分字段缺失、null 与实际字符串，对用户昵称执行部分更新。",
       "普通字符串指针无法独立描述字段是否出现在补丁中，因此先将补丁解码为 RawMessage 映射。查不到键表示保持原值，null 表示清除指针，字符串表示赋新值。先把新值成功解码到局部变量再修改资料，错误输入不会破坏旧昵称。示例连续展示三种合法状态，并用数字值验证类型错误的拒绝路径。",
       ["缺失字段与显式 null 语义不同，不能都当作空字符串。", "在完成类型检查前修改资料，会让失败补丁留下部分状态。"],
       "支持同时更新 nickname 和 city，并保证任一字段错误时两个字段都不变。",
       "先复制资料为 candidate，在 candidate 上验证和更新所有字段，全部成功后一次赋回原资料；注意指针指向的可变对象也需按需要复制。",
       r'''
       package main

       import (
           "bytes"
           "encoding/json"
           "fmt"
       )

       type Profile struct { Nickname *string }

       func apply(profile *Profile, text string) error {
           var fields map[string]json.RawMessage
           if err := json.Unmarshal([]byte(text), &fields); err != nil { return err }
           raw, exists := fields["nickname"]
           if !exists { return nil }
           if bytes.Equal(bytes.TrimSpace(raw), []byte("null")) { profile.Nickname = nil; return nil }
           var name string
           if err := json.Unmarshal(raw, &name); err != nil { return err }
           profile.Nickname = &name
           return nil
       }

       func display(profile Profile) string {
           if profile.Nickname == nil { return "<unset>" }
           return *profile.Nickname
       }

       func main() {
           initial := "Li"
           profile := Profile{&initial}
           for _, step := range []struct { Label string; Patch string }{
               {"missing", `{}`}, {"null", `{"nickname":null}`}, {"value", `{"nickname":"Yu"}`},
           } {
               if err := apply(&profile, step.Patch); err != nil { panic(err) }
               fmt.Printf("%s=%s\n", step.Label, display(profile))
           }
           err := apply(&profile, `{"nickname":42}`)
           fmt.Printf("bad-type=%t preserved=%s\n", err != nil, display(profile))
       }
       ''', "missing=Li\nnull=<unset>\nvalue=Yu\nbad-type=true preserved=Yu")

lesson(137, "CSV 账单汇总", ["encoding/csv", "表头索引", "strconv.ParseInt", "整数金额"],
       "按表头定位账单列，拒绝坏金额并汇总有效行，金额使用整数分。",
       "CSV 的列顺序不应隐藏在数字下标里。先读取表头并建立索引，确认 quantity 与 cents 都存在，再逐行读取。整数分避免浮点舍入，解析失败或负值的行计入 rejected，CSV 结构错误则使整次读取失败。固定输入包括带逗号的商品名和坏金额，因此能同时验证格式解析与数据规则。乘积与总额在真实系统中还应加入溢出边界。",
       ["不能用 strings.Split 解析 CSV，带引号的逗号属于字段内容。", "金额使用浮点数会引入舍入问题；本例用整数分，但生产数据仍需溢出检查。"],
       "增加单行金额与总额的溢出检查，错误行计入 rejected。",
       "对非负数先验证 cents <= MaxInt64/quantity，再验证 subtotal <= MaxInt64-total；quantity 为零时单独处理。",
       r'''
       package main

       import (
           "encoding/csv"
           "fmt"
           "io"
           "strconv"
           "strings"
       )

       func total(text string) (int64, int, int, error) {
           reader := csv.NewReader(strings.NewReader(text))
           header, err := reader.Read()
           if err != nil { return 0, 0, 0, err }
           columns := map[string]int{}
           for i, name := range header { columns[name] = i }
           quantity, hasQuantity := columns["quantity"]
           cents, hasCents := columns["cents"]
           if !hasQuantity || !hasCents { return 0, 0, 0, fmt.Errorf("missing required header") }
           var sum int64
           valid, rejected := 0, 0
           for {
               row, err := reader.Read()
               if err == io.EOF { break }
               if err != nil { return 0, valid, rejected, err }
               count, countErr := strconv.ParseInt(row[quantity], 10, 64)
               price, priceErr := strconv.ParseInt(row[cents], 10, 64)
               if countErr != nil || priceErr != nil || count < 0 || price < 0 { rejected++; continue }
               sum += count*price
               valid++
           }
           return sum, valid, rejected, nil
       }

       func main() {
           sum, valid, rejected, err := total("quantity,item,cents\n2,\"tea, green\",250\n1,cake,225\n1,invalid,oops\n")
           if err != nil { panic(err) }
           fmt.Printf("valid=%d rejected=%d total-cents=%d\n", valid, rejected, sum)
           _, _, _, err = total("item,cents\ntea,250\n")
           fmt.Printf("missing-header=%t\n", err != nil)
       }
       ''', "valid=2 rejected=1 total-cents=725\nmissing-header=true")

lesson(138, "CSV 安全导出", ["csv.Writer", "引号转义", "多行字段", "往返验证"],
       "导出含逗号、双引号和换行的地址簿，再读回验证字段内容完全一致。",
       "CSV Writer 负责决定哪些字段需要引号，并把字段内部的双引号写成两个双引号。字段换行属于一条记录的内容，不能按文本行数计算联系人数量。程序把三行逻辑记录写到内存后重新解析，逐字段对比，并单独检查双引号和换行是否保留。这里的安全指 CSV 格式保持；若交给电子表格软件打开，还要另行制定公式前缀处理策略。",
       ["自己拼接逗号和引号容易破坏嵌套引号及多行字段。", "格式正确不等于防电子表格公式执行；本例不把 CSV 转义当作公式防护。"],
       "导出前识别以等号开头的地址字段，并按明确的电子表格策略添加前缀。",
       "在业务层生成单独的表格导出副本，对危险前缀应用选定策略，再由 csv.Writer 处理格式；保留原始数据，说明该策略会改变单元格文本。",
       r'''
       package main

       import (
           "bytes"
           "encoding/csv"
           "fmt"
           "strings"
       )

       func main() {
           records := [][]string{{"name", "address"}, {"Lin", "East, Road"}, {"Yu", "\"Suite\" 3\nFloor 2"}}
           var buffer bytes.Buffer
           writer := csv.NewWriter(&buffer)
           if err := writer.WriteAll(records); err != nil { panic(err) }
           decoded, err := csv.NewReader(strings.NewReader(buffer.String())).ReadAll()
           if err != nil { panic(err) }
           equal := len(decoded) == len(records)
           if equal {
               for i, row := range records {
                   if len(decoded[i]) != len(row) { equal = false; break }
                   for j, value := range row { if decoded[i][j] != value { equal = false } }
               }
           }
           fmt.Printf("rows=%d roundtrip=%t\n", len(decoded)-1, equal)
           fmt.Printf("quotes-doubled=%t\n", strings.Contains(buffer.String(), `""Suite""`))
           fmt.Printf("line-preserved=%t\n", decoded[2][1] == "\"Suite\" 3\nFloor 2")
       }
       ''', "rows=2 roundtrip=true\nquotes-doubled=true\nline-preserved=true")

lesson(139, "XML 库存与属性", ["encoding/xml", "属性标签", "嵌套路径", "结构化更新"],
       "读取 XML 属性与嵌套库存，补充低库存项目并重新编码验证。",
       "结构体标签分别描述 sku 属性、quantity 子元素和 items>item 嵌套路径，数据转换无需手工拼接 XML 字符串。程序只将少于五件的商品补到五件，记录修改数量后 Marshal，再解码确认库存不变。坏库存文本无法解析成整数，会返回错误。未展示在结构中的 XML 内容可能被丢弃，所以这种读取再写出适用于受控协议，而不是任意文档的无损编辑。",
       ["属性与子元素需要不同标签，sku,attr 不能写成普通元素。", "结构化往返只保留已建模字段，不能保证保留原文注释、空白和未知节点。"],
       "拒绝重复 sku，并保证整份库存验证成功后再开始补货。",
       "解码后先遍历并用 map 检查空 sku、重复 sku 和负库存；全部通过后再执行第二遍补货，避免错误数据的部分更新。",
       r'''
       package main

       import (
           "encoding/xml"
           "fmt"
       )

       type Item struct { SKU string `xml:"sku,attr"`; Quantity int `xml:"quantity"` }
       type Inventory struct { XMLName xml.Name `xml:"inventory"`; Items []Item `xml:"items>item"` }

       func main() {
           input := `<inventory><items><item sku="A"><quantity>1</quantity></item><item sku="B"><quantity>7</quantity></item></items></inventory>`
           var inventory Inventory
           if err := xml.Unmarshal([]byte(input), &inventory); err != nil { panic(err) }
           changed := 0
           for i := range inventory.Items {
               if inventory.Items[i].Quantity < 5 { inventory.Items[i].Quantity = 5; changed++ }
           }
           encoded, err := xml.Marshal(inventory)
           if err != nil { panic(err) }
           var restored Inventory
           if err := xml.Unmarshal(encoded, &restored); err != nil { panic(err) }
           fmt.Printf("restocked=%d\n", changed)
           fmt.Printf("%s=%d %s=%d\n", restored.Items[0].SKU, restored.Items[0].Quantity, restored.Items[1].SKU, restored.Items[1].Quantity)
           fmt.Printf("roundtrip=%t\n", len(restored.Items) == 2 && restored.Items[0].Quantity == 5 && restored.Items[1].Quantity == 7)
           err = xml.Unmarshal([]byte(`<inventory><items><item sku="C"><quantity>many</quantity></item></items></inventory>`), &restored)
           fmt.Printf("bad-stock=%t\n", err != nil)
       }
       ''', "restocked=1\nA=5 B=7\nroundtrip=true\nbad-stock=true")

lesson(140, "Gob 快照兼容读取", ["encoding/gob", "字段兼容", "零值", "截断检测"],
       "写入旧版状态快照，用增加字段的新结构读取并验证零值兼容和截断错误。",
       "Gob 根据导出字段名匹配结构，不要求发送端和接收端使用相同 Go 类型名。旧快照包含 Name 和 Count，新结构增加 Note；读取后已有字段还原，缺失的新字段保持零值。程序也对截断字节流尝试解码，确认损坏输入返回错误。兼容不意味着任意字段类型变更都可接受，也不应把 Gob 当作可直接解码不可信海量输入的无限制格式。",
       ["未导出字段不参与 Gob 编码，不能依靠它保存私有状态。", "新增兼容字段与改变既有字段类型不同；后者可能解码失败。"],
       "把新结构的 Count 改成字符串，验证旧快照解码会失败并保留错误信息。",
       "定义另一个接收结构并对同一份独立 bytes.Reader 解码，检查 err != nil；不要复用已经消费完的 Decoder 来测试类型兼容。",
       r'''
       package main

       import (
           "bytes"
           "encoding/gob"
           "fmt"
       )

       type OldState struct { Name string; Count int }
       type NewState struct { Name string; Count int; Note string }

       func main() {
           var buffer bytes.Buffer
           if err := gob.NewEncoder(&buffer).Encode(OldState{"queue", 3}); err != nil { panic(err) }
           snapshot := append([]byte(nil), buffer.Bytes()...)
           var restored NewState
           if err := gob.NewDecoder(bytes.NewReader(snapshot)).Decode(&restored); err != nil { panic(err) }
           fmt.Printf("name=%s count=%d\n", restored.Name, restored.Count)
           fmt.Printf("new-field-empty=%t\n", restored.Note == "")
           var damaged NewState
           err := gob.NewDecoder(bytes.NewReader(snapshot[:len(snapshot)/2])).Decode(&damaged)
           fmt.Printf("truncated=%t\n", err != nil)
       }
       ''', "name=queue count=3\nnew-field-empty=true\ntruncated=true")
