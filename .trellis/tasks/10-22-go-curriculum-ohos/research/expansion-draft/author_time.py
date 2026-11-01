"""Author T171-T180 fixed-input time and logical-scheduling drafts."""
from author_common import lesson

lesson(171, "时区与同一时刻", ["time.Parse", "RFC3339", "time.Equal", "FixedZone"],
       "解析带偏移的时间，转换 UTC，并验证不同时区文本表示同一时刻。",
       "RFC3339 文本同时给出本地钟面与 UTC 偏移，09:30+08:00 和 01:30Z 表示同一瞬间。Equal 比较时刻，不能用格式化文本相等来判断。转换到固定西五区会落在前一天，提醒日期也随时区变化。FixedZone 只有固定偏移，不包含地区夏令时规则；需要地区历史规则时应使用已提供的时区数据库。",
       ["钟面字符串相同不保证时刻相同，偏移必须一起解析。", "固定偏移时区不能替代有夏令时的地区时区。"],
       "计算两条带不同偏移日志的真实先后顺序，禁止直接比较原字符串。",
       "分别 time.Parse 为 Time，再用 Before、After 或 Equal；展示 UTC 格式便于人工核对，但排序依据保持为 Time。",
       r'''
       package main
       import ("fmt"; "time")

       func mustTime(text string)time.Time { value,err:=time.Parse(time.RFC3339,text);if err!=nil { panic(err) };return value }
       func main() {
           east:=mustTime("2026-03-12T09:30:00+08:00");utc:=mustTime("2026-03-12T01:30:00Z")
           fmt.Printf("utc=%s equal=%t\n",east.UTC().Format(time.RFC3339),east.Equal(utc))
           west:=east.In(time.FixedZone("WEST",-5*60*60));fmt.Printf("west=%s\n",west.Format(time.RFC3339))
       }
       ''', "utc=2026-03-12T01:30:00Z equal=true\nwest=2026-03-11T20:30:00-05:00")

lesson(172, "UTC 时间桶聚合", ["time.Truncate", "UTC 归一", "空桶", "排序聚合"],
       "把乱序事件归入十五分钟 UTC 桶，稳定输出空桶与非空桶并拒绝范围外事件。",
       "先将事件转换成 UTC，再以十五分钟 Truncate 得到桶起点，避免不同偏移文本落入不同键。预先生成查询范围内全部桶，所以没有事件的 09:45 也会输出零。范围使用左闭右开，10:00 属于范围外而不是最后一桶。桶键排序后同时输出计数与金额总和，乱序输入不会改变结果。",
       ["只输出 map 中实际出现的键会丢掉空桶。", "范围终点是否包含必须明确，否则边界事件可能被重复统计。"],
       "为桶增加平均值，并让空桶显示空值而不是零除错误。",
       "仅在 Count>0 时计算 Sum/Count，空桶输出单独的缺失标记；保留原始计数与总和，便于再次聚合。",
       r'''
       package main
       import ("fmt"; "sort"; "time")

       type Bucket struct { Count int; Sum int }
       func parse(text string)time.Time { value,err:=time.Parse(time.RFC3339,text);if err!=nil { panic(err) };return value }
       func main() {
           start:=parse("2026-03-12T09:00:00Z");end:=start.Add(time.Hour);buckets:=map[time.Time]Bucket{}
           for at:=start;at.Before(end);at=at.Add(15*time.Minute) { buckets[at]=Bucket{} }
           rejected:=0
           for _,event:=range []struct{Text string;Value int}{{"2026-03-12T09:34:00Z",3},{"2026-03-12T09:03:00Z",2},{"2026-03-12T09:29:00Z",4},{"2026-03-12T17:03:00+08:00",5},{"2026-03-12T10:00:00Z",9}} {
               at:=parse(event.Text).UTC();if at.Before(start)||!at.Before(end) { rejected++;continue };key:=at.Truncate(15*time.Minute);bucket:=buckets[key];bucket.Count++;bucket.Sum+=event.Value;buckets[key]=bucket
           }
           keys:=[]time.Time{};for key:=range buckets { keys=append(keys,key) };sort.Slice(keys,func(i,j int)bool{return keys[i].Before(keys[j])})
           for _,key:=range keys { bucket:=buckets[key];fmt.Printf("%s count=%d sum=%d\n",key.Format("15:04"),bucket.Count,bucket.Sum) };fmt.Printf("rejected=%d\n",rejected)
       }
       ''', "09:00 count=2 sum=7\n09:15 count=1 sum=4\n09:30 count=1 sum=3\n09:45 count=0 sum=0\nrejected=1")

lesson(173, "工作日日期推进", ["time.AddDate", "Weekday", "日历语义"],
       "从给定日期推进第三个工作日，跳过周末并保留钟面时间。",
       "工作日计算按日历日期前进，循环用 AddDate 增加一天，仅在周一到周五时减少剩余数量。起始日不计入，星期五一月三十日的第三个工作日是二月四日星期三。日历天与固定二十四小时不总相同，AddDate 保留所选地点下的日历语义。本例不包含法定节假日，负数量明确拒绝，零数量返回原时刻。",
       ["直接增加 days*24h 不表达跨时区夏令时边界的日历推进。", "是否计入起始日、是否排除节假日都必须作为业务规则写清。"],
       "增加固定节假日集合，遇到节假日也不消耗工作日名额。",
       "将日期按目标地点格式化为 YYYY-MM-DD，在周末检查之后查询假日集合；同一天即使同时命中周末和假日也只跳过一次。",
       r'''
       package main
       import ("fmt"; "time")

       func advance(start time.Time,days int)(time.Time,error) {
           if days<0 { return time.Time{},fmt.Errorf("negative workdays") };at:=start
           for days>0 { at=at.AddDate(0,0,1);if at.Weekday()!=time.Saturday && at.Weekday()!=time.Sunday { days-- } };return at,nil
       }
       func main() {
           start:=time.Date(2026,time.January,30,9,0,0,0,time.UTC);third,err:=advance(start,3);if err!=nil { panic(err) }
           fmt.Printf("start=%s %s\n",start.Format("2006-01-02"),start.Weekday().String());fmt.Printf("third=%s %s\n",third.Format("2006-01-02"),third.Weekday().String())
           zero,err:=advance(start,0);fmt.Printf("zero=%t\n",err==nil && zero.Equal(start));_,err=advance(start,-1);fmt.Printf("negative=%t\n",err!=nil)
       }
       ''', "start=2026-01-30 Friday\nthird=2026-02-04 Wednesday\nzero=true\nnegative=true")

lesson(174, "跨午夜区间拆分", ["time.Date", "自然日边界", "时长守恒"],
       "把跨午夜会话按自然日拆分，核对各段时长之和等于原始会话。",
       "每轮从当前游标构造下一自然日零点，取零点与总终点中较早者作为本段结束，再推进游标。会话 23:40 到次日 00:25 被分成二十分钟与二十五分钟。使用 time.Date 构造下一日而非增加固定二十四小时，保留日历边界含义。结束早于开始会失败，相等时产生零段；日期归属采用起点的地点。",
       ["跨午夜不意味着总时长必须超过二十四小时。", "按日期切分前必须固定地点，不同地点的午夜并非同一时刻。"],
       "增加恰好在午夜结束的输入，保证不生成次日零时长段。",
       "循环条件保持 cursor.Before(end)，上一段恰好到达 end 后直接结束；不要使用小于等于条件追加空段。",
       r'''
       package main
       import ("fmt"; "time")

       type Usage struct { Date string; Duration time.Duration }
       func split(start,end time.Time)([]Usage,error) {
           if end.Before(start) { return nil,fmt.Errorf("reversed interval") };end=end.In(start.Location());result:=[]Usage{}
           for cursor:=start;cursor.Before(end); {
               midnight:=time.Date(cursor.Year(),cursor.Month(),cursor.Day()+1,0,0,0,0,cursor.Location());stop:=midnight;if end.Before(stop) { stop=end }
               result=append(result,Usage{cursor.Format("2006-01-02"),stop.Sub(cursor)});cursor=stop
           };return result,nil
       }
       func main() {
           start:=time.Date(2026,time.March,12,23,40,0,0,time.UTC);end:=start.Add(45*time.Minute);parts,err:=split(start,end);if err!=nil { panic(err) }
           var total time.Duration;for _,part:=range parts { fmt.Printf("%s=%.0fm\n",part.Date,part.Duration.Minutes());total+=part.Duration }
           fmt.Printf("total=%.0fm preserved=%t\n",total.Minutes(),total==end.Sub(start));_,err=split(end,start);fmt.Printf("reversed=%t\n",err!=nil)
       }
       ''', "2026-03-12=20m\n2026-03-13=25m\ntotal=45m preserved=true\nreversed=true")

lesson(175, "可预测指数退避", ["time.Duration", "饱和增长", "重试预算"],
       "计算带上限的退避序列，预防翻倍溢出，并输出累计等待预算。",
       "退避计划在内存中计算，不真正 Sleep。每次写入当前延迟后，先比较 cap/2，再决定翻倍或直接饱和到 cap，避免先翻倍产生整数溢出。固定参数得到 100、200、400、750、750、750 毫秒，总预算 2.95 秒。确定性计划适合测试；真实分布式重试通常还需要抖动与取消，但不能用随机输出替代本例的规则验证。",
       ["先乘二再与上限比较可能已经溢出。", "单次上限不等于累计预算；尝试次数同样需要限制。"],
       "加入两秒累计预算，下一次等待会超预算时停止生成。",
       "在追加前比较 delay>budget-total，避免 total+delay 先溢出；被拒绝的等待不计入次数和总和。",
       r'''
       package main
       import ("fmt"; "time")

       func plan(base,cap time.Duration,count int)([]time.Duration,error) {
           if base<=0 || cap<base || count<0 || count>100 { return nil,fmt.Errorf("invalid retry plan") };result:=[]time.Duration{};delay:=base
           for i:=0;i<count;i++ { result=append(result,delay);if delay>cap/2 { delay=cap } else { delay*=2 } };return result,nil
       }
       func main() {
           delays,err:=plan(100*time.Millisecond,750*time.Millisecond,6);if err!=nil { panic(err) };var total time.Duration;for _,delay:=range delays { total+=delay }
           fmt.Printf("delays=%v\ntotal=%s\n",delays,total.String());_,err=plan(0,time.Second,2);fmt.Printf("invalid=%t\n",err!=nil)
       }
       ''', "delays=[100ms 200ms 400ms 750ms 750ms 750ms]\ntotal=2.95s\ninvalid=true")

lesson(176, "逻辑时钟 TTL 缓存", ["显式时钟", "到期边界", "time.Before", "清理"],
       "显式传入 now 验证 TTL 到期与清理，无需任何真实等待。",
       "缓存条目保存过期时刻，每次 Get 都由调用者传入 now。只有 now 严格早于 Expires 才命中，所以恰好到期时已经失效。Get 不自动删除，Purge 负责清理并报告数量，这让读取语义与回收行为可以分别测试。程序用固定逻辑时钟推进五分钟和十分钟，输出稳定而且不受机器运行速度影响。",
       ["使用小于等于作为有效条件会把到期瞬间错误算作命中。", "测试中依靠 Sleep 等到过期容易慢且不稳定，应该注入时钟。"],
       "支持续期，但已经过期的键不能被续活。",
       "Renew 先调用同一到期条件检查当前有效性，通过后才用传入 now 与正 TTL 设置新 Expires；失效键返回 false。",
       r'''
       package main
       import ("fmt"; "sort"; "time")

       type Entry struct { Value int; Expires time.Time }
       type Cache map[string]Entry
       func (c Cache) Put(key string,value int,now time.Time,ttl time.Duration) { if ttl<=0 { panic("invalid ttl") };c[key]=Entry{value,now.Add(ttl)} }
       func (c Cache) Get(key string,now time.Time)(int,bool) { entry,ok:=c[key];if !ok || !now.Before(entry.Expires) { return 0,false };return entry.Value,true }
       func (c Cache) Purge(now time.Time)int { removed:=0;for key,entry:=range c { if !now.Before(entry.Expires) { delete(c,key);removed++ } };return removed }
       func (c Cache) Keys()[]string { keys:=[]string{};for key:=range c { keys=append(keys,key) };sort.Strings(keys);return keys }
       func main() {
           now:=time.Date(2026,time.March,12,9,0,0,0,time.UTC);cache:=Cache{};cache.Put("a",1,now,5*time.Minute);cache.Put("b",2,now,10*time.Minute)
           value,found:=cache.Get("a",now.Add(4*time.Minute));fmt.Printf("early=%d found=%t\n",value,found)
           _,found=cache.Get("a",now.Add(5*time.Minute));fmt.Printf("at-expiry=%t\n",found)
           removed:=cache.Purge(now.Add(5*time.Minute));fmt.Printf("purged=%d remaining=%v\n",removed,cache.Keys())
           removed=cache.Purge(now.Add(10*time.Minute));fmt.Printf("final=%d remaining=%v\n",removed,cache.Keys())
       }
       ''', "early=1 found=true\nat-expiry=false\npurged=1 remaining=[b]\nfinal=1 remaining=[]")

lesson(177, "每日定点计划", ["time.Date", "AddDate", "严格未来时刻"],
       "从固定 now 求下一次每日执行时刻，处理当天未到、已过与恰好相等三种情况。",
       "先在 now 的地点构造今天的目标钟面；若候选不严格晚于 now，就按日历增加一天。这里定义下一次必须在未来，因此恰好九点时不会立即重复执行今天的九点任务。使用 AddDate 保留日历计划语义，输入小时分钟分别验证范围。地区夏令时可能让某些钟面缺失或重复，实际调度器还需明确对应策略。",
       ["恰好等于目标时刻是否立即执行必须有明确规则。", "直接加二十四小时不能完整表达地区时区的每日钟面计划。"],
       "改成允许恰好等于 now 的候选，保持其他场景结果不变。",
       "将 !candidate.After(now) 改为 candidate.Before(now)，并新增相等场景断言，说明这是业务规则变化而非格式调整。",
       r'''
       package main
       import ("fmt"; "time")

       func next(now time.Time,hour,minute int)(time.Time,error) {
           if hour<0 || hour>23 || minute<0 || minute>59 { return time.Time{},fmt.Errorf("invalid daily clock") }
           candidate:=time.Date(now.Year(),now.Month(),now.Day(),hour,minute,0,0,now.Location());if !candidate.After(now) { candidate=candidate.AddDate(0,0,1) };return candidate,nil
       }
       func main() {
           for _,item:=range []struct{Label string;Hour int}{{"before",8},{"after",10},{"equal",9}} {
               now:=time.Date(2026,time.March,12,item.Hour,0,0,0,time.UTC);candidate,err:=next(now,9,0);if err!=nil { panic(err) };fmt.Printf("%s=%s\n",item.Label,candidate.Format(time.RFC3339))
           }
       }
       ''', "before=2026-03-12T09:00:00Z\nafter=2026-03-13T09:00:00Z\nequal=2026-03-13T09:00:00Z")

lesson(178, "日期严格校验", ["time.Parse", "规范往返", "闰年", "Date 归一化"],
       "严格验证日期与格式，区分闰年合法日期和 Date 构造时的自动归一化。",
       "Parse 会验证月份的实际日数，随后 Format 与原输入往返相等保证规范补零格式。闰年二月二十九日可接受，非闰年同日必须拒绝。与此不同，time.Date 被设计为规范化越界字段，二零二五年二月二十九日会得到三月一日，不能拿构造成功当作原输入合法的证明。程序同时展示两条路径，避免日历校验被静默修正替代。",
       ["time.Date 会归一化越界日期，不是用户输入校验器。", "能解析不总代表符合产品要求的规范文本，必要时做往返检查。"],
       "允许用户输入不补零日期，但保存时统一为规范格式，并保留解析错误。",
       "明确新增可接受布局，逐个尝试解析；成功后输出唯一的 2006-01-02 格式，仍拒绝二月三十等实际不存在日期。",
       r'''
       package main
       import ("fmt"; "time")

       func strict(text string)(time.Time,error) {
           value,err:=time.Parse("2006-01-02",text);if err!=nil { return time.Time{},err }
           if value.Format("2006-01-02")!=text { return time.Time{},fmt.Errorf("noncanonical date") };return value,nil
       }
       func main() {
           leap,err:=strict("2024-02-29");if err!=nil { panic(err) };fmt.Printf("leap=%s\n",leap.Format("2006-01-02"))
           normalized:=time.Date(2025,time.February,29,0,0,0,0,time.UTC);_,err=strict("2025-02-29");fmt.Printf("normalized=%s rejected=%t\n",normalized.Format("2006-01-02"),err!=nil)
           _,err=strict("2026-04-31");fmt.Printf("april-rejected=%t\n",err!=nil);_,err=strict("2026-4-01");fmt.Printf("nonpadded-rejected=%t\n",err!=nil)
       }
       ''', "leap=2024-02-29\nnormalized=2025-03-01 rejected=true\napril-rejected=true\nnonpadded-rejected=true")

lesson(179, "计费时长向上取整", ["time.Duration", "商与余数", "分段计费", "溢出保护"],
       "把使用时长按十五分钟计费，比较逐段取整与总时长取整并拒绝负数。",
       "向上取整通过整数商与非零余数实现，避免 duration+unit-1 可能发生的加法溢出。再检查块数乘单价单位是否超出 Duration 范围。三段一分钟、十四分钟、十六分钟逐段计费共六十分钟，先合并三十一分钟再计费则为四十五分钟。两种规则都可实现，但应在合同和界面中明确采用哪一种。",
       ["分段取整之和不等于先求和再取整。", "常见加 unit-1 的公式在接近整数上限时会溢出。"],
       "在累加多段使用时长前检测总时长溢出，不接受负段。",
       "每段先验证非负，再检查 duration>MaxDuration-total；全部通过后才相加并调用计费函数。",
       r'''
       package main
       import ("fmt"; "time")

       func charge(duration,unit time.Duration)(time.Duration,error) {
           if duration<0 || unit<=0 { return 0,fmt.Errorf("invalid duration") };blocks:=duration/unit;if duration%unit!=0 { blocks++ }
           const maximum time.Duration=1<<63-1
           if blocks>maximum/unit { return 0,fmt.Errorf("charge overflow") };return blocks*unit,nil
       }
       func main() {
           var separate,total time.Duration
           for _,duration:=range []time.Duration{time.Minute,14*time.Minute,16*time.Minute} { cost,err:=charge(duration,15*time.Minute);if err!=nil { panic(err) };separate+=cost;total+=duration }
           combined,err:=charge(total,15*time.Minute);if err!=nil { panic(err) };fmt.Printf("separate-minutes=%.0f combined-minutes=%.0f\n",separate.Minutes(),combined.Minutes())
           zero,err:=charge(0,15*time.Minute);if err!=nil { panic(err) };fmt.Printf("zero=%d\n",zero);_,err=charge(-time.Second,15*time.Minute);fmt.Printf("negative-rejected=%t\n",err!=nil)
       }
       ''', "separate-minutes=60 combined-minutes=45\nzero=0\nnegative-rejected=true")

lesson(180, "多来源日志归并", ["container/heap", "time.Before", "多路归并", "稳定并列"],
       "归并三条已排序日志流，以时间、来源序号和来源内位置保持稳定顺序。",
       "堆中只保留每条流当前一项，取出后才补入该来源下一项，空间与来源数成正比。比较器先按时刻，再按来源编号，最后按来源内索引，因此相同时刻仍有稳定全序。开始归并前逐流验证单调排序，避免把错误前提带入算法。所有时间来自固定输入，既不依赖当前时钟，也不依赖实际并发调度。",
       ["多路归并要求各输入流本身已经排序，不能静默接受乱序流。", "相同时间戳需要额外决胜字段，否则日志顺序不确定。"],
       "增加第四条空流，证明它不影响其他来源顺序且不会访问首项越界。",
       "初始化只把 len(stream)>0 的来源加入堆，已有的补入逻辑继续检查 next<len(stream)，空来源无需特殊占位项。",
       r'''
       package main
       import ("container/heap"; "fmt"; "time")

       type Event struct { At time.Time; Text string }
       type Cursor struct { Event Event; Source int; Index int }
       type Queue []Cursor
       func (q Queue)Len()int{return len(q)}
       func (q Queue)Less(i,j int)bool { if !q[i].Event.At.Equal(q[j].Event.At) { return q[i].Event.At.Before(q[j].Event.At) };if q[i].Source!=q[j].Source { return q[i].Source<q[j].Source };return q[i].Index<q[j].Index }
       func (q Queue)Swap(i,j int){q[i],q[j]=q[j],q[i]}
       func (q *Queue)Push(value interface{}){*q=append(*q,value.(Cursor))}
       func (q *Queue)Pop()interface{}{old:=*q;value:=old[len(old)-1];*q=old[:len(old)-1];return value}
       func merge(streams [][]Event)([]Cursor,error) {
           queue:=&Queue{}
           for source,stream:=range streams { for i:=1;i<len(stream);i++ { if stream[i].At.Before(stream[i-1].At) { return nil,fmt.Errorf("unsorted stream") } };if len(stream)>0 { heap.Push(queue,Cursor{stream[0],source,0}) } }
           result:=[]Cursor{}
           for queue.Len()>0 { current:=heap.Pop(queue).(Cursor);result=append(result,current);next:=current.Index+1;if next<len(streams[current.Source]) { heap.Push(queue,Cursor{streams[current.Source][next],current.Source,next}) } };return result,nil
       }
       func main() {
           base:=time.Date(2026,time.March,12,10,0,0,0,time.UTC)
           streams:=[][]Event{{{base,"a0"},{base.Add(2*time.Minute),"a1"}},{{base,"b0"},{base.Add(time.Minute),"b1"}},{{base.Add(time.Minute),"c0"},{base.Add(2*time.Minute),"c1"}}}
           result,err:=merge(streams);if err!=nil { panic(err) };for _,item:=range result { fmt.Printf("%s source=%d %s\n",item.Event.At.Format("15:04"),item.Source,item.Event.Text) }
       }
       ''', "10:00 source=0 a0\n10:00 source=1 b0\n10:01 source=1 b1\n10:01 source=2 c0\n10:02 source=0 a1\n10:02 source=2 c1")
