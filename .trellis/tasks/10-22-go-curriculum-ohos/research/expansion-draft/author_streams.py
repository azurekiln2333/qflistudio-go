"""Author T141-T150 byte-stream drafts from the reviewed roadmap."""
from author_common import lesson

lesson(141, "长度前缀消息", ["encoding/binary", "io.ReadFull", "帧预算"],
       "编码两帧消息，逐帧读取，并在分配载荷前拒绝截断和超预算长度。",
       "每帧用两个大端字节保存载荷长度。ReadFull 保证头和载荷必须完整，正常流结束与只剩半个头不同。读取长度后先与八字节业务预算比较，再分配载荷，避免直接相信输入长度。示例正常读出 cat 与 go，同时检查过大的头和载荷不足这两条失败路径。这里的十六位长度只是传输上限，不能代替更小的业务预算。",
       ["普通 Read 可能只返回部分数据，不能一次调用就假定读满。", "按不可信长度先分配再检查，会失去资源预算的作用。"],
       "增加零长度心跳帧，并将它与流结束区分。",
       "长度为零时返回非 nil 的空载荷和 nil 错误；只有读取下一个完整帧头之前遇到 io.EOF 才结束循环。",
       r'''
       package main
       import ("bytes"; "encoding/binary"; "fmt"; "io")

       func writeFrame(out *bytes.Buffer, text string) {
           var header [2]byte
           binary.BigEndian.PutUint16(header[:], uint16(len(text)))
           out.Write(header[:]); out.WriteString(text)
       }
       func readFrame(reader io.Reader) ([]byte, error) {
           var header [2]byte
           if _, err := io.ReadFull(reader, header[:]); err != nil { return nil, err }
           length := int(binary.BigEndian.Uint16(header[:]))
           if length > 8 { return nil, fmt.Errorf("frame over budget") }
           payload := make([]byte, length)
           _, err := io.ReadFull(reader, payload)
           return payload, err
       }
       func main() {
           var wire bytes.Buffer
           writeFrame(&wire, "cat"); writeFrame(&wire, "go")
           frames := []string{}
           for {
               payload, err := readFrame(&wire)
               if err == io.EOF { break }
               if err != nil { panic(err) }
               frames = append(frames, string(payload))
           }
           fmt.Printf("frames=%v\n", frames)
           _, err := readFrame(bytes.NewReader([]byte{0, 9}))
           fmt.Printf("oversized=%t\n", err != nil)
           _, err = readFrame(bytes.NewReader([]byte{0, 3, 'x'}))
           fmt.Printf("truncated=%t\n", err == io.ErrUnexpectedEOF)
       }
       ''', "frames=[cat go]\noversized=true\ntruncated=true")

lesson(142, "固定容量环形日志", ["环形槽", "覆盖策略", "快照隔离", "bytes.Buffer"],
       "只保存最后三条记录，覆盖最旧项，按时间顺序导出独立快照。",
       "next 指向下一次写入位置，count 最大增长到容量，快照起点由 next-count 回绕得到。写入四条后 a 被覆盖，随后写入 e 又覆盖 b。Snapshot 返回新的切片，修改它不会污染日志内部槽位；bytes.Buffer 负责按顺序生成导出文本。固定容量约束的是记录条数，单条记录仍需另设字节预算。",
       ["直接返回内部切片会让调用者修改日志内容。", "环形存储顺序不是时间顺序，导出时必须从最旧槽位开始。"],
       "增加每条记录最多十六字节的限制，拒绝超限写入且不推进 next。",
       "在修改任何槽位之前检查 len(record)，失败直接返回错误；对中文这是字节限制，应在接口说明中明确。",
       r'''
       package main
       import ("bytes"; "fmt")

       type Ring struct { slots []string; next int; count int }
       func newRing(capacity int) *Ring {
           if capacity <= 0 { panic("capacity must be positive") }
           return &Ring{slots: make([]string, capacity)}
       }
       func (r *Ring) Add(record string) {
           r.slots[r.next] = record
           r.next = (r.next+1)%len(r.slots)
           if r.count < len(r.slots) { r.count++ }
       }
       func (r *Ring) Snapshot() []string {
           result := make([]string, r.count)
           start := (r.next-r.count+len(r.slots))%len(r.slots)
           for i := range result { result[i] = r.slots[(start+i)%len(r.slots)] }
           return result
       }
       func (r *Ring) Text() string {
           var out bytes.Buffer
           for i, record := range r.Snapshot() {
               if i > 0 { out.WriteByte('\n') }; out.WriteString(record)
           }
           return out.String()
       }
       func main() {
           ring := newRing(3)
           for _, record := range []string{"a", "b", "c", "d"} { ring.Add(record) }
           fmt.Printf("recent=%v\n", ring.Snapshot())
           snapshot := ring.Snapshot(); snapshot[0] = "changed"
           fmt.Printf("isolated=%t\n", ring.Snapshot()[0] == "b")
           ring.Add("e")
           fmt.Printf("export=%q\n", ring.Text())
       }
       ''', 'recent=[b c d]\nisolated=true\nexport="c\\nd\\ne"')

lesson(143, "串联分片流", ["io.MultiReader", "增量读取", "n 与 err"],
       "把头部与多个分片串成一个读取流，用小缓冲逐步核对完整内容。",
       "MultiReader 依次消费各 Reader，让调用者不必先拼接全部字节。空分片不会生成额外数据，三个字节的小缓冲让完整内容跨多次读取。循环先处理 n 个有效字节，再检查错误，因为 Reader 可以同时返回数据和 EOF。最终的十四字节由四字节头、三字节中间段和七字节尾段组成，输出顺序与各分片定义一致。",
       ["收到 EOF 时仍应先处理同次调用返回的有效字节。", "MultiReader 只负责串联，不会替应用验证消息长度或内容边界。"],
       "在读取过程中比较固定预期字节，发现第一个不同位置立即报错。",
       "维护已消费偏移，对每次 n 字节检查是否超出预期以及逐字节相等；EOF 时再确认偏移等于总长度。",
       r'''
       package main
       import ("fmt"; "io"; "strings")

       func main() {
           reader := io.MultiReader(strings.NewReader(""), strings.NewReader("HDR:"), strings.NewReader("go "), strings.NewReader("offline"), strings.NewReader(""))
           var output strings.Builder
           buffer := make([]byte, 3)
           for {
               n, err := reader.Read(buffer)
               if n > 0 { output.Write(buffer[:n]) }
               if err == io.EOF { break }
               if err != nil { panic(err) }
           }
           fmt.Printf("combined=%s\n", output.String())
           fmt.Printf("bytes=%d\n", output.Len())
           fmt.Printf("empty-fragments=%t\n", output.String() == "HDR:go offline")
       }
       ''', "combined=HDR:go offline\nbytes=14\nempty-fragments=true")

lesson(144, "边复制边计算摘要", ["io.TeeReader", "crypto/sha256", "流式校验"],
       "在复制内容时同时计算摘要，只从原始流读取一次。",
       "TeeReader 将每次读出的字节同步写入摘要器，同时把相同字节交给 Copy。包装 Reader 累计实际读取字节数，证明源数据只消费了七字节，而没有为了摘要再读一遍。复制结束后，将流式摘要与固定原始数据的一次性摘要比较，并检查副本内容。TeeWriter 写入失败会成为读取错误，因此 Copy 的错误必须处理。",
       ["先读完整流算摘要再尝试复制，第二次读取通常只会得到 EOF。", "TeeReader 的旁路写入也是执行的一部分，错误不能忽略。"],
       "让旁路 Writer 在三字节后返回错误，验证复制不会继续报告完整成功。",
       "实现有剩余预算的 Writer，写入超过预算时返回部分计数和错误；检查 Copy 的 err 与实际复制长度，而非只看目标非空。",
       r'''
       package main
       import ("bytes"; "crypto/sha256"; "fmt"; "io"; "strings")

       type CountReader struct { Inner io.Reader; Bytes int }
       func (r *CountReader) Read(buffer []byte) (int, error) {
           n, err := r.Inner.Read(buffer); r.Bytes += n; return n, err
       }
       func main() {
           source := &CountReader{Inner: strings.NewReader("offline")}
           digest := sha256.New()
           var copy bytes.Buffer
           n, err := io.Copy(&copy, io.TeeReader(source, digest))
           if err != nil { panic(err) }
           expected := sha256.Sum256([]byte("offline"))
           fmt.Printf("copied=%d source-bytes=%d\n", n, source.Bytes)
           fmt.Printf("digest=%t content=%s\n", bytes.Equal(digest.Sum(nil), expected[:]), copy.String())
       }
       ''', "copied=7 source-bytes=7\ndigest=true content=offline")

lesson(145, "随机访问区间", ["io.SectionReader", "io.ReaderAt", "独立游标"],
       "从同一个 ReaderAt 创建独立区间，读取数据并验证区间边界与原始游标。",
       "SectionReader 给共享 ReaderAt 提供受限窗口，每个窗口有自己的顺序读取位置。第一个窗口得到 2345，第二个请求更长但底层只剩 789；ReadAll 将正常 EOF 视作成功。窗口的 ReadAt 不会改变底层 strings.Reader 的游标，越过窗口末尾则返回有效的部分字节和 EOF。边界检查既包括底层实际长度，也包括窗口声明长度。",
       ["ReadAt 跨越末尾可能同时返回部分数据和 EOF，不能丢掉 n。", "窗口长度大于剩余底层数据并不会凭空补零。"],
       "在读取窗口前验证 offset 与 length 非负，并拒绝整数相加溢出。",
       "分别检查 offset>=0、length>=0，再用 length > MaxInt64-offset 判断溢出；不要先算 offset+length 再判断结果。",
       r'''
       package main
       import ("fmt"; "io"; "strings")

       func main() {
           source := strings.NewReader("0123456789")
           first := io.NewSectionReader(source, 2, 4)
           second := io.NewSectionReader(source, 7, 8)
           a, err := io.ReadAll(first); if err != nil { panic(err) }
           b, err := io.ReadAll(second); if err != nil { panic(err) }
           position, err := source.Seek(0, io.SeekCurrent); if err != nil { panic(err) }
           fmt.Printf("first=%s second=%s cursor=%d\n", a, b, position)
           buffer := make([]byte, 2)
           n, err := first.ReadAt(buffer, 3)
           fmt.Printf("boundary=%t byte=%s\n", n == 1 && err == io.EOF, buffer[:n])
       }
       ''', "first=2345 second=789 cursor=0\nboundary=true byte=5")

lesson(146, "完整读取与截断分类", ["io.ReadFull", "io.EOF", "io.ErrUnexpectedEOF"],
       "区分完全没有下一条记录与记录只剩一部分，保留实际读取字节数。",
       "固定四字节记录用 ReadFull 读取。空流在尚未读到任何字节时返回 EOF，表示可以正常停止寻找下一条；只读到 ab 后结束则返回 UnexpectedEOF，说明已有记录被截断。完整 abcd 返回四字节和 nil。程序显式分类这三种情况，不会把任何错误都当成正常结束，也不会把不完整缓冲当成完整记录处理。",
       ["EOF 与 UnexpectedEOF 的恢复策略不同，不能统一吞掉。", "发生截断时缓冲尾部不是有效输入，只能使用 buffer[:n]。"],
       "把三条输入改成一个连续流，读取两条完整记录后报告最后半条。",
       "循环对同一 Reader 调用 ReadFull，nil 时处理完整记录，EOF 时正常退出，UnexpectedEOF 时输出 n 和有效前缀再停止。",
       r'''
       package main
       import ("bytes"; "fmt"; "io")

       func main() {
           for _, input := range []struct { Label string; Data string }{{"empty", ""}, {"partial", "ab"}, {"full", "abcd"}} {
               buffer := make([]byte, 4)
               n, err := io.ReadFull(bytes.NewReader([]byte(input.Data)), buffer)
               status := "complete"
               if err == io.EOF { status = "EOF"
               } else if err == io.ErrUnexpectedEOF { status = "UnexpectedEOF"
               } else if err != nil { panic(err) }
               fmt.Printf("%s:%s bytes=%d\n", input.Label, status, n)
           }
       }
       ''', "empty:EOF bytes=0\npartial:UnexpectedEOF bytes=2\nfull:complete bytes=4")

lesson(147, "受限读取防超量", ["io.LimitReader", "预算加一", "容量检查"],
       "用上限加一个字节检测超量输入，区分刚好达到预算与被静默截断。",
       "只读 max 字节无法判断输入刚好结束还是还有更多内容，因此本例读取 max+1 字节。长度超过 max 才返回超量错误，恰好四字节的 data 保持成功；零预算只接受空输入。预算本身先限制在零到一千零二十四之间，确保加一不溢出且不会允许无限内存读取。实际协议若还有后续消息，需自行决定是否消费或保留探测到的多余字节。",
       ["LimitReader 的 EOF 可能只是达到人为上限，不代表原始流结束。", "max+1 之前必须验证 max，避免整数溢出和不合理预算。"],
       "允许调用者区分预算参数错误和输入过大错误。",
       "定义两个独立哨兵错误，分别在参数检查和长度检查返回，用 errors.Is 在调用层分类。",
       r'''
       package main
       import ("fmt"; "io"; "strings")

       func readBudget(reader io.Reader, max int64) ([]byte, error) {
           if max < 0 || max > 1024 { return nil, fmt.Errorf("invalid budget") }
           data, err := io.ReadAll(io.LimitReader(reader, max+1))
           if err != nil { return nil, err }
           if int64(len(data)) > max { return nil, fmt.Errorf("input exceeds budget") }
           return data, nil
       }
       func main() {
           data, err := readBudget(strings.NewReader("data"), 4)
           if err != nil { panic(err) }; fmt.Printf("exact=%s\n", data)
           _, err = readBudget(strings.NewReader("extra"), 4)
           fmt.Printf("oversized=%t\n", err != nil)
           empty, err := readBudget(strings.NewReader(""), 0)
           fmt.Printf("zero=%d valid=%t\n", len(empty), err == nil)
       }
       ''', "exact=data\noversized=true\nzero=0 valid=true")

lesson(148, "复用缓冲复制", ["io.CopyBuffer", "接口快路径", "Writer 计数"],
       "使用固定三字节缓冲复制数据，统计写入次数并核对完整副本。",
       "CopyBuffer 允许调用者复用内存，但 ReaderFrom 或 WriterTo 快路径可能绕过提供的缓冲。这里的包装器仅暴露 Read 与 Write，确保示例实际使用三字节缓冲；十字节内容分成四次写入。计数 Writer 同时保存目标数据，最终检查字节数、写入次数与完整相等。真实调用通常应该保留快路径，这里隐藏它们是为了观察缓冲行为。",
       ["提供缓冲并不保证它一定被使用，接口快路径可能优先执行。", "零长度缓冲会使 CopyBuffer panic，应在复用前保证长度大于零。"],
       "把缓冲大小改为四，独立推导十字节内容需要几次 Write。",
       "由于包装器禁用快路径，读取分为四、四、二字节，因此应有三次成功 Write；同时继续检查总字节数十。",
       r'''
       package main
       import ("bytes"; "fmt"; "io")

       type PlainReader struct { Inner io.Reader }
       func (r *PlainReader) Read(data []byte) (int, error) { return r.Inner.Read(data) }
       type CountingWriter struct { Data bytes.Buffer; Calls int }
       func (w *CountingWriter) Write(data []byte) (int, error) {
           w.Calls++; return w.Data.Write(data)
       }
       func main() {
           source := []byte("abcdefghij")
           reader := &PlainReader{bytes.NewReader(source)}
           writer := &CountingWriter{}
           buffer := make([]byte, 3)
           n, err := io.CopyBuffer(writer, reader, buffer)
           if err != nil { panic(err) }
           fmt.Printf("copied=%d writes=%d equal=%t\n", n, writer.Calls, bytes.Equal(source, writer.Data.Bytes()))
       }
       ''', "copied=10 writes=4 equal=true")

lesson(149, "前瞻协议探测", ["bufio.Reader.Peek", "缓冲读取", "协议识别"],
       "前瞻四字节识别本地记录协议，再读取整条记录验证前瞻没有丢失内容。",
       "Peek 返回缓冲中的前缀但不推进读取位置。识别 LOG| 后，ReadString 仍能读出带完整前缀的记录，证明探测没有消费数据。未知前缀返回业务错误，过短输入则保留 Peek 的读取错误。Peek 返回的切片只在后续读操作之前有效，若要持久保存探测字节必须复制。",
       ["Peek 得到的切片由缓冲器拥有，后续读取可能覆盖它。", "用 Read 代替 Peek 探测后若不回放前缀，会丢失消息起始字节。"],
       "同时识别 BIN|，并让调用者根据协议选择不同记录读取器。",
       "switch string(prefix) 返回协议枚举，仍然不消费前缀；由各协议解析器显式验证并消费自己的头部。",
       r'''
       package main
       import ("bufio"; "bytes"; "fmt"; "strings")

       func protocol(reader *bufio.Reader) (string, error) {
           prefix, err := reader.Peek(4)
           if err != nil { return "", err }
           if !bytes.Equal(prefix, []byte("LOG|")) { return "", fmt.Errorf("unknown prefix") }
           return "LOG", nil
       }
       func main() {
           reader := bufio.NewReader(strings.NewReader("LOG|ready\n"))
           kind, err := protocol(reader); if err != nil { panic(err) }
           record, err := reader.ReadString('\n'); if err != nil { panic(err) }
           fmt.Printf("protocol=%s record=%s", kind, record)
           _, err = protocol(bufio.NewReader(strings.NewReader("BIN!data")))
           fmt.Printf("unknown=%t\n", err != nil)
       }
       ''', "protocol=LOG record=LOG|ready\nunknown=true")

lesson(150, "批量写入与 Flush", ["bufio.Writer", "可见性", "Flush", "错误处理"],
       "观察批量写入在 Flush 前后的底层可见性，并验证重复 Flush 不重复写数据。",
       "两条短记录先进入三十二字节缓冲，底层 bytes.Buffer 仍为空，而 Buffered 为十一。Flush 把缓存内容写到底层，之后再 Flush 不会重复追加。缓冲只能推迟写入，不能消除写入错误，所以每次 WriteString 与 Flush 都检查返回值。若内容超过缓冲容量，数据可能在显式 Flush 前就下沉；本例固定短输入以清楚展示这一阶段。",
       ["WriteString 成功可能只写进缓冲，不代表目标已经收到数据。", "不能假定所有数据都等到 Flush 才可见，大写入可能触发自动下沉。"],
       "用总是返回错误的底层 Writer，验证错误在首次 Flush 出现并被后续 Flush 保留。",
       "实现 Write 返回零和固定错误，写入小于缓冲容量的数据，再连续调用两次 Flush；分别用 errors.Is 检查相同错误。",
       r'''
       package main
       import ("bufio"; "bytes"; "fmt")

       func main() {
           var destination bytes.Buffer
           writer := bufio.NewWriterSize(&destination, 32)
           if _, err := writer.WriteString("alpha\n"); err != nil { panic(err) }
           if _, err := writer.WriteString("beta\n"); err != nil { panic(err) }
           fmt.Printf("before=%d buffered=%d\n", destination.Len(), writer.Buffered())
           if err := writer.Flush(); err != nil { panic(err) }
           fmt.Printf("after=%d content=%q\n", destination.Len(), destination.String())
           before := destination.Len()
           err := writer.Flush()
           fmt.Printf("second-flush=%t\n", err == nil && destination.Len() == before)
       }
       ''', 'before=0 buffered=11\nafter=11 content="alpha\\nbeta\\n"\nsecond-flush=true')
