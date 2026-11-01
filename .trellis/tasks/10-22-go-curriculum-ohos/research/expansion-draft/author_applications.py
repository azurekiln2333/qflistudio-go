"""T271-T280: composed offline applications with real state and failures."""
from author_second_half import emit

emit(271, r'''
package main
import("encoding/csv";"fmt";"sort";"strconv";"strings")
func ledger(text string)(map[string]int,map[string]bool){rows,err:=csv.NewReader(strings.NewReader(text)).ReadAll();if err!=nil{panic(err)};values:=map[string]int{};duplicates:=map[string]bool{};for _,row:=range rows[1:]{if len(row)!=2{panic("bad columns")};amount,err:=strconv.Atoi(row[1]);if err!=nil{panic(err)};if _,exists:=values[row[0]];exists{duplicates[row[0]]=true}else{values[row[0]]=amount}};return values,duplicates}
func main(){left,ld:=ledger("id,cents\nt1,100\nt2,200\nt3,300\n");right,rd:=ledger("id,cents\nt1,110\nt2,200\nt2,200\nt4,400\n");set:=map[string]bool{};for id:=range left{set[id]=true};for id:=range right{set[id]=true};ids:=[]string{};for id:=range set{ids=append(ids,id)};sort.Strings(ids)
 for _,id:=range ids{a,hasA:=left[id];b,hasB:=right[id];if ld[id]{fmt.Printf("%s duplicate-left\n",id)};if rd[id]{fmt.Printf("%s duplicate-right\n",id)};switch{case !hasA:fmt.Printf("%s missing-left\n",id);case !hasB:fmt.Printf("%s missing-right\n",id);case a!=b:fmt.Printf("%s mismatch=%d/%d\n",id,a,b)}}
}
''', 't1 mismatch=100/110\nt2 duplicate-right\nt3 missing-right\nt4 missing-left',
'本例从两段内存 CSV 文本加载账本，按交易 ID 对应逐笔记录，不涉及文件读写。加载时先保留第一笔并记录重复 ID，比较时取两边键集合的并集，按 ID 排序报告金额不符、重复和缺失。金额统一用整数分，避免浮点格式差异掩盖实际金额问题。示例刻意让重复记录金额相同，证明仅看汇总仍会漏掉结构错误。',
['把重复 ID 直接覆盖会丢失重复交易证据。','两份账本总额相同也可能有不同的缺失或错账，不能只比较总和。'],
'对同一 ID 的重复金额不一致单独报告冲突。','加载函数除重复集合外记录第一次金额与冲突标记，避免覆盖原始值，再按稳定 ID 顺序展示。')

emit(272, r'''
package main
import("container/heap";"fmt";"sort")
type Names []string
func(h Names)Len()int{return len(h)};func(h Names)Less(i,j int)bool{return h[i]<h[j]};func(h Names)Swap(i,j int){h[i],h[j]=h[j],h[i]};func(h *Names)Push(v interface{}){*h=append(*h,v.(string))};func(h *Names)Pop()interface{}{old:=*h;last:=old[len(old)-1];*h=old[:len(old)-1];return last}
func plan(deps map[string][]string)([]string,[]string){degree:=map[string]int{};next:=map[string][]string{};for name,inputs:=range deps{if _,ok:=degree[name];!ok{degree[name]=0};for _,input:=range inputs{degree[name]++;if _,ok:=degree[input];!ok{degree[input]=0};next[input]=append(next[input],name)}};ready:=&Names{};heap.Init(ready);for name,n:=range degree{if n==0{heap.Push(ready,name)}};order:=[]string{};for ready.Len()>0{name:=heap.Pop(ready).(string);order=append(order,name);for _,dependent:=range next[name]{degree[dependent]--;if degree[dependent]==0{heap.Push(ready,dependent)}}};remaining:=[]string{};for name,n:=range degree{if n>0{remaining=append(remaining,name)}};sort.Strings(remaining);return order,remaining}
func main(){order,cycle:=plan(map[string][]string{"parse":{},"compile":{"parse"},"test":{"compile"},"link":{"compile"}});fmt.Printf("order=%v remaining=%v\n",order,cycle);_,cycle=plan(map[string][]string{"a":{"b"},"b":{"a"}});fmt.Printf("cycle=%v\n",cycle)}
''', 'order=[parse compile link test] remaining=[]\ncycle=[a b]',
'Kahn 拓扑排序维护每个节点尚未完成的依赖数，零依赖节点放进字典序小根堆。每取出一个构建项，就降低它后继节点的计数；新就绪节点再次入堆，所以同一依赖图始终生成同一计划。最终剩余正计数节点表示被环阻塞的部分，可能包含环外但依赖环的节点，并非精确环路径。',
['边的方向必须从依赖项指向使用它的节点，反向会产生相反构建顺序。','剩余节点集合不能直接宣称为一条闭环路径，定位环还需要 DFS 或强连通分量。'],
'拒绝一个节点依赖列表中的重复依赖。','为每个节点建立临时依赖集合，在增加 degree 前检查重复；不要悄悄重复计数。')

emit(273, r'''
package main
import("container/heap";"fmt";"sort")
type Booking struct{ID string;Start,End int};type Room struct{End,ID int};type Active []Room
func(h Active)Len()int{return len(h)};func(h Active)Less(i,j int)bool{if h[i].End!=h[j].End{return h[i].End<h[j].End};return h[i].ID<h[j].ID};func(h Active)Swap(i,j int){h[i],h[j]=h[j],h[i]};func(h *Active)Push(v interface{}){*h=append(*h,v.(Room))};func(h *Active)Pop()interface{}{old:=*h;v:=old[len(old)-1];*h=old[:len(old)-1];return v}
func main(){bookings:=[]Booking{{"A",0,30},{"B",5,10},{"C",10,20},{"D",30,40}};sort.SliceStable(bookings,func(i,j int)bool{return bookings[i].Start<bookings[j].Start});active:=&Active{};heap.Init(active);rooms:=0
 for _,booking:=range bookings{if booking.Start>=booking.End{panic("bad interval")};room:=0;if active.Len()>0&&(*active)[0].End<=booking.Start{room=heap.Pop(active).(Room).ID}else{rooms++;room=rooms};heap.Push(active,Room{booking.End,room});fmt.Printf("%s=room%d\n",booking.ID,room)};fmt.Printf("rooms=%d\n",rooms)
}
''', 'A=room1\nB=room2\nC=room2\nD=room2\nrooms=2',
'按开始时间处理预约，堆顶保存最早结束的房间。如果它已经结束就复用，否则才新增房间。B 在十分钟结束，C 恰好十分钟开始，因此二者可复用；这依赖左闭右开的预约区间约定。房间结束时间相同再按编号比较，保证结果稳定。算法最小化房间总数，不承诺每次挑编号最小的空房。',
['结束等于下一场开始应视为可复用还是冲突，必须先约定区间端点语义。','只按房间编号选择而忽略结束时间，可能错误复用仍被占用的房间。'],
'增加同开始时刻的预约，以 ID 作为排序次关键字。','在 sort 比较中先比 Start，再比 ID；相同时间输入顺序变化也得到稳定分配。')

emit(274, r'''
package main
import("crypto/sha256";"encoding/json";"fmt";"os";"path/filepath";"sort")
type Entry struct{Name string `json:"name"`;Size int `json:"size"`;Digest string `json:"sha256"`}
func digest(text string)string{sum:=sha256.Sum256([]byte(text));return fmt.Sprintf("%x",sum)}
func main(){directory,err:=os.MkdirTemp("","qfli-package-");if err!=nil{panic(err)};defer os.RemoveAll(directory)
 for name,text:=range map[string]string{"ok.txt":"ok","changed.txt":"NEW!"}{if err=os.WriteFile(filepath.Join(directory,name),[]byte(text),0600);err!=nil{panic(err)}}
 manifest:=[]Entry{{"ok.txt",2,digest("ok")},{"changed.txt",3,digest("old")},{"missing.txt",1,digest("x")}};wire,err:=json.Marshal(manifest);if err!=nil{panic(err)};manifestPath:=filepath.Join(directory,"manifest.json");if err=os.WriteFile(manifestPath,wire,0600);err!=nil{panic(err)};wire,err=os.ReadFile(manifestPath);if err!=nil{panic(err)};var decoded []Entry;if err=json.Unmarshal(wire,&decoded);err!=nil{panic(err)};issues:=[]string{}
 for _,item:=range decoded{if item.Name=="."||item.Name==".."||filepath.Base(item.Name)!=item.Name{issues=append(issues,item.Name+":name");continue};data,err:=os.ReadFile(filepath.Join(directory,item.Name));if os.IsNotExist(err){issues=append(issues,item.Name+":missing");continue};if err!=nil{issues=append(issues,item.Name+":read");continue};if len(data)!=item.Size{issues=append(issues,item.Name+":size")};if digest(string(data))!=item.Digest{issues=append(issues,item.Name+":digest")}}
 sort.Strings(issues);for _,issue:=range issues{fmt.Println(issue)};fmt.Printf("issues=%d\n",len(issues))
}
''', 'changed.txt:digest\nchanged.txt:size\nmissing.txt:missing\nissues=3',
'程序在独占临时目录实际写入 JSON 清单和两个包文件，再从磁盘读取清单并逐文件验证存在性、字节长度和 SHA256。长度错误不妨碍继续检查摘要，因此同一损坏文件能报告两个问题；缺失文件则不计算虚构内容的摘要，其他读取错误单独归类。所有问题收集后排序，结束时清理目录。本例只允许无子目录的文件名，文件与目录都由程序自身创建；读取外部已有目录还需防止符号链接越界，清单本身也需要可信来源。',
['发现首个问题就返回会让用户多轮修复，批量检查应聚合独立错误。','简单文件名检查不能防止已有符号链接越界，本例独占目录的前提不可省略。'],
'拒绝 JSON 清单中的重复 Name，避免同一文件出现互相冲突元数据。','解析后先建立 Name 集合；重复即记录清单结构错误，在验证内容之前给出明确结果。')

emit(275, r'''
package main
import("fmt";"sort";"strings")
type Order struct{Department,State string;Cents int};type Total struct{Count,Cents int}
func main(){orders:=[]Order{{"North","paid",1200},{"south","paid",900},{"north","draft",300},{"NORTH","paid",700},{"south","paid",100}};groups:=map[string]Total{}
 for _,order:=range orders{if order.State!="paid"||order.Cents<500{continue};key:=strings.ToLower(order.Department);total:=groups[key];total.Count++;total.Cents+=order.Cents;groups[key]=total}
 names:=[]string{};for name:=range groups{names=append(names,name)};sort.Strings(names);for _,name:=range names{total:=groups[name];fmt.Printf("%s count=%d cents=%d\n",name,total.Count,total.Cents)}
}
''', 'north count=2 cents=1900\nsouth count=1 cents=900',
'这份内存查询器先筛选已支付且达到金额门槛的订单，再规范化部门名并分组汇总，最后排序展示。不同大小写部门归到同组，草稿单和小额单都不计入。筛选、分组、排序三个步骤各有清晰职责，便于将来替换成来自 CSV 或 JSON 的离线记录。金额采用整数分，聚合仍需根据实际规模设置溢出保护。',
['先汇总再按单笔金额条件筛选会改变业务语义。','map 遍历顺序不稳定，报表输出前必须排序键。'],
'在汇总结果中按金额降序排序，金额相同按部门名升序。','把 map 转成带 Department 的结果切片，使用明确的两级比较器，而不是依赖已有键顺序。')

emit(276, r'''
package main
import("encoding/json";"fmt")
type Event struct{Kind string `json:"kind"`;Amount int `json:"amount"`};type State struct{Open bool;Balance int}
func apply(state State,event Event)(State,error){next:=state;switch event.Kind{case "open":if state.Open{return state,fmt.Errorf("already open")};next.Open=true;case "credit","debit":if !state.Open||event.Amount<=0{return state,fmt.Errorf("invalid amount/state")};if event.Kind=="credit"{next.Balance+=event.Amount}else{if event.Amount>state.Balance{return state,fmt.Errorf("insufficient funds")};next.Balance-=event.Amount};default:return state,fmt.Errorf("unknown event")};return next,nil}
func main(){var events []Event;if err:=json.Unmarshal([]byte(`[{"kind":"open"},{"kind":"credit","amount":100},{"kind":"debit","amount":30},{"kind":"debit","amount":90},{"kind":"other"}]`),&events);err!=nil{panic(err)};state:=State{};for index,event:=range events{next,err:=apply(state,event);if err!=nil{fmt.Printf("event%d rejected balance=%d\n",index,state.Balance);continue};state=next};fmt.Printf("final=%d\n",state.Balance)}
''', 'event3 rejected balance=70\nevent4 rejected balance=70\nfinal=70',
'事件重放把当前状态和一个事件交给纯 apply 函数，先在副本上检查并修改，成功才提交。开户、入账和扣款依次得到余额七十，超额扣款和未知事件被拒绝，之前有效状态保留。示例选择记录坏事件后继续扫描，这是一种明确的导入策略；正式事件日志通常还要定义损坏日志是否立即终止。',
['在检查余额前先扣款再返回错误，会破坏重放确定性。','事件顺序属于业务数据，不能为了输出排序而重排入账和扣款事件。'],
'为事件增加序号，拒绝重复或不连续序号。','在 State 增加最后已应用序号；只有事件验证和状态更新都成功后才推进，明确失败事件的恢复策略。')

emit(277, r'''
package main
import("fmt")
type Change struct{Item string;Delta int}
func transact(stock map[string]int,changes []Change)error{next:=map[string]int{};for item,value:=range stock{next[item]=value};for _,change:=range changes{value,exists:=next[change.Item];if !exists{return fmt.Errorf("unknown item")};value+=change.Delta;if value<0{return fmt.Errorf("negative stock")};next[change.Item]=value};for item,value:=range next{stock[item]=value};return nil}
func main(){stock:=map[string]int{"pen":10,"pad":4};err:=transact(stock,[]Change{{"pen",-3},{"pad",-9}});fmt.Printf("failed=%t pen=%d pad=%d\n",err!=nil,stock["pen"],stock["pad"]);err=transact(stock,[]Change{{"pen",-3},{"pad",2}});fmt.Printf("committed=%t pen=%d pad=%d\n",err==nil,stock["pen"],stock["pad"])}
''', 'failed=true pen=10 pad=4\ncommitted=true pen=7 pad=6',
'事务先复制库存表，在副本上逐步执行变更，全部通过后才写回原表。第一批先减少笔再让便笺变负，整批失败后两个库存仍为原值；第二批合法才同时提交。这是单协程内存级原子业务操作，不是数据库持久事务。若库存值包含切片或指针，浅复制 map 仍会共享内部可变数据。',
['直接在原表逐项修改，后面的失败不会自动撤销前面的成功修改。','当前实现没有并发隔离，多个协程同时调用仍需同一把锁或 actor 所有权。'],
'增加一个新商品的创建操作，并保证失败时不会留下它。','让 Change 显式区分 create 与 adjust，在 next 副本中验证存在性并处理，最终统一提交新增键。')

emit(278, r'''
package main
import("fmt";"math";"time")
type Bucket struct{Capacity,Tokens,PerSecond float64;Last time.Time}
func(b *Bucket)Allow(now time.Time)bool{if now.Before(b.Last){return false};b.Tokens=math.Min(b.Capacity,b.Tokens+now.Sub(b.Last).Seconds()*b.PerSecond);b.Last=now;if b.Tokens<1{return false};b.Tokens--;return true}
func main(){start:=time.Date(2026,10,23,0,0,0,0,time.UTC);b:=&Bucket{Capacity:2,Tokens:2,PerSecond:1,Last:start};for _,offset:=range []time.Duration{0,0,0,500*time.Millisecond,time.Second,time.Second,3*time.Second}{fmt.Printf("t=%4.1f allow=%t\n",offset.Seconds(),b.Allow(start.Add(offset)))};fmt.Printf("clock-backwards=%t\n",b.Allow(start))}
''', 't= 0.0 allow=true\nt= 0.0 allow=true\nt= 0.0 allow=false\nt= 0.5 allow=false\nt= 1.0 allow=true\nt= 1.0 allow=false\nt= 3.0 allow=true\nclock-backwards=false',
'令牌桶把突发容量与长期补充速率分开。每次调用显式传入逻辑时间，先按经过秒数补充并限制到容量，再判断能否扣除一枚令牌。连续三次零时刻请求只能通过两个，半秒不足一枚，一秒恢复一次机会。即使请求被拒绝，已补充余额和 Last 也要保留；时钟倒退直接拒绝且不修改状态。',
['每次拒绝都把令牌归零，会丢失不足一枚的累计补充。','并发请求必须同步更新 Tokens 和 Last，两个字段分开修改会破坏限流。'],
'让每个请求携带 cost，且 cost 大于容量时明确拒绝。','在更新前验证 cost>0 且 cost<=Capacity；足额后一次性扣除 cost，继续保留小数余额。')

emit(279, r'''
package main
import("encoding/json";"fmt")
type Checkpoint struct{Next int `json:"next"`}
func main(){records:=[]string{"A","B","C","D","E"};committed:=[]string{};checkpoint:=Checkpoint{};wire:=[]byte{};failOnce:=true
 for checkpoint.Next<len(records){start:=checkpoint.Next;end:=start+2;if end>len(records){end=len(records)};pending:=append([]string(nil),records[start:end]...)
  if start==2&&failOnce{failOnce=false;fmt.Printf("failed-at=%d\n",start);if err:=json.Unmarshal(wire,&checkpoint);err!=nil{panic(err)};continue}
  committed=append(committed,pending...);checkpoint.Next=end;var err error;wire,err=json.Marshal(checkpoint);if err!=nil{panic(err)}
 }
 fmt.Printf("committed=%v\ncheckpoint=%s\n",committed,wire)
}
''', 'failed-at=2\ncommitted=[A B C D E]\ncheckpoint={"next":5}',
'批处理把未提交批次先放在 pending 中，模拟第二批在提交前失败，再从已保存 Next 偏移恢复。只有批次成功提交才推进并序列化检查点，因此恢复不会重复追加已完成的 A、B。示例是在同一内存进程中的教学模拟，真实崩溃恢复必须保证提交与检查点原子关联，或以稳定任务 ID 实现幂等。',
['先推进检查点再提交数据，崩溃后会永久漏掉该批次。','提交与保存检查点之间发生真实崩溃仍可能重复，需要事务或幂等写入，单个 JSON 文件不自动提供 exactly-once。'],
'用记录 ID 集合让重复提交同一批也不会新增重复结果。','提交时先检查稳定 ID 是否已存在，仅追加新记录；检查点只用于加速定位，不能替代幂等约束。')

emit(280, r'''
package main
import("fmt";"strconv";"unicode")
func precedence(op rune)int{if op=='+'||op=='-'{return 1};if op=='*'||op=='/'{return 2};return 0}
func evaluate(text string)(int,error){values:=[]int{};ops:=[]rune{};apply:=func()error{if len(values)<2||len(ops)==0{return fmt.Errorf("missing operand")};op:=ops[len(ops)-1];ops=ops[:len(ops)-1];a,b:=values[len(values)-2],values[len(values)-1];values=values[:len(values)-2];switch op{case '+':values=append(values,a+b);case '-':values=append(values,a-b);case '*':values=append(values,a*b);case '/':if b==0{return fmt.Errorf("division by zero")};values=append(values,a/b);default:return fmt.Errorf("bad operator")};return nil}
 chars:=[]rune(text);expectValue:=true
 for i:=0;i<len(chars);{c:=chars[i];if unicode.IsSpace(c){i++;continue};if c>='0'&&c<='9'{if !expectValue{return 0,fmt.Errorf("missing operator")};start:=i;for i<len(chars)&&chars[i]>='0'&&chars[i]<='9'{i++};n,err:=strconv.Atoi(string(chars[start:i]));if err!=nil{return 0,err};values=append(values,n);expectValue=false;continue};if c=='('{if !expectValue{return 0,fmt.Errorf("missing operator")};ops=append(ops,c);i++;continue};if c==')'{if expectValue{return 0,fmt.Errorf("empty group")};for len(ops)>0&&ops[len(ops)-1]!='('{if err:=apply();err!=nil{return 0,err}};if len(ops)==0{return 0,fmt.Errorf("unmatched close")};ops=ops[:len(ops)-1];i++;continue};if precedence(c)==0||expectValue{return 0,fmt.Errorf("bad token")};for len(ops)>0&&precedence(ops[len(ops)-1])>=precedence(c){if err:=apply();err!=nil{return 0,err}};ops=append(ops,c);expectValue=true;i++}
 if expectValue{return 0,fmt.Errorf("incomplete")};for len(ops)>0{if ops[len(ops)-1]=='('{return 0,fmt.Errorf("unmatched open")};if err:=apply();err!=nil{return 0,err}};if len(values)!=1{return 0,fmt.Errorf("bad expression")};return values[0],nil
}
func main(){for _,expression:=range []string{"2 + 3 * (4 - 1)","18 / 3 / 2","4/(2-2)","1 +"}{value,err:=evaluate(expression);if err!=nil{fmt.Printf("%s -> error\n",expression)}else{fmt.Printf("%s -> %d\n",expression,value)}}}
''', '2 + 3 * (4 - 1) -> 11\n18 / 3 / 2 -> 3\n4/(2-2) -> error\n1 + -> error',
'计算器维护数值栈和运算符栈。遇到更低或相同优先级的二元运算符时先归约栈顶，保证乘除优先以及同优先级左结合；括号作为归约边界。expectValue 区分当前应该出现数字还是运算符，因此拒绝尾部运算符和缺操作数。示例还检测除零。本范围只接受非负整数字面量和二元算术，不实现一元负号，整数运算采用 Go 的本机 int 规则。',
['减法和除法的操作数顺序必须是倒数第二个值 op 最后一个值，不能反过来。','本机 int 的中间算术可能溢出，生产计算器需要边界检查或 math/big。'],
'为一元负号加入独立优先级，支持 -(2+3)*4。','当 expectValue 为 true 且遇到减号时压入单目操作符；归约时只弹一个数值，不能简单改写所有减号。')
