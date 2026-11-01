"""T231-T240: explicit worker ownership and deterministic observations."""
from author_second_half import emit

emit(231, r'''
package main
import("fmt";"sort";"sync")
type Job struct{Index,Value int};type Result struct{Index,Value int}
func main(){
 input:=[]int{2,3,4,5};jobs:=make(chan Job,len(input));results:=make(chan Result,len(input))
 for i,value:=range input{jobs<-Job{i,value}};close(jobs)
 var workers sync.WaitGroup
 for n:=0;n<2;n++{workers.Add(1);go func(){defer workers.Done();for job:=range jobs{results<-Result{job.Index,job.Value*job.Value}}}()}
 workers.Wait();close(results);ordered:=[]Result{};for result:=range results{ordered=append(ordered,result)}
 sort.Slice(ordered,func(i,j int)bool{return ordered[i].Index<ordered[j].Index});values:=[]int{};for _,result:=range ordered{values=append(values,result.Value)}
 fmt.Printf("ordered=%v\n",values)
}
''', 'ordered=[4 9 16 25]',
'任务附带输入下标，两个 worker 可以自由完成计算，收集端再按下标恢复输入顺序。结果通道容量等于任务数，因此主协程先等待 worker 退出不会堵塞发送。WaitGroup 的 Add 在启动前执行，全部 worker 完成后才关闭结果通道。并行完成顺序与最终展示顺序是两个独立问题，不能依赖调度恰好按输入发生。',
['无缓冲结果通道若在主协程 Wait 时无人接收，会造成死锁。','循环变量需要明确传递或复制，不能靠偶然调度读取正确任务。'],
'把结果通道改为无缓冲，同时保持无死锁和输入顺序。','启动唯一收尾协程等待 workers 后 close(results)，主协程同时 range 接收，最后仍按 Index 排序。')

emit(232, r'''
package main
import("fmt";"sync";"sync/atomic")
func main(){
 gate:=make(chan struct{},2);var workers sync.WaitGroup;var active,peak,completed int32
 for i:=0;i<6;i++{workers.Add(1);go func(){defer workers.Done();gate<-struct{}{};current:=atomic.AddInt32(&active,1)
  for{old:=atomic.LoadInt32(&peak);if current<=old||atomic.CompareAndSwapInt32(&peak,old,current){break}}
  atomic.AddInt32(&completed,1);atomic.AddInt32(&active,-1);<-gate
 }()};workers.Wait()
 fmt.Printf("completed=%d\npeak-bounded=%t\nactive=%d\n",completed,peak>=1&&peak<=2,active)
}
''', 'completed=6\npeak-bounded=true\nactive=0',
'容量为二的通道作为并发闸门，拿到槽位后才进入受限区域，结束前归还槽位。原子计数跟踪当前数量、峰值和完成数，比较交换循环只在新值更大时更新峰值。调度可能让实际峰值是一或二，因此断言的是不超过上限而非虚构固定并发顺序。Wait 后 active 为零证明所有受限工作已退出。',
['只限制结果缓冲大小不会限制正在执行的工作数。','获取槽位之后的错误或 panic 路径也必须归还槽位，真实任务通常需要 defer。'],
'把闸门封装成 runLimited 函数，并用 defer 归还槽位。','进入后立即登记 defer，再执行用户任务；WaitGroup.Done 也应由 worker 最外层 defer 执行。')

emit(233, r'''
package main
import("fmt";"sync")
type Call struct{Done chan struct{};Value string}
type Group struct{mu sync.Mutex;calls map[string]*Call;joined chan struct{}}
func(g *Group)Do(key string,load func()string)string{
 g.mu.Lock();if existing:=g.calls[key];existing!=nil{g.mu.Unlock();g.joined<-struct{}{};<-existing.Done;return existing.Value}
 call:=&Call{Done:make(chan struct{})};g.calls[key]=call;g.mu.Unlock()
 call.Value=load();g.mu.Lock();delete(g.calls,key);close(call.Done);g.mu.Unlock();return call.Value
}
func main(){
 group:=&Group{calls:map[string]*Call{},joined:make(chan struct{},5)};started:=make(chan struct{});release:=make(chan struct{});results:=make(chan string,6);loads:=0
 for i:=0;i<6;i++{go func(){results<-group.Do("catalog",func()string{loads++;close(started);<-release;return "ready"})}()}
 <-started;for i:=0;i<5;i++{<-group.joined};close(release)
 matches:=0;for i:=0;i<6;i++{if <-results=="ready"{matches++}}
 fmt.Printf("loads=%d\nmatched=%d\n",loads,matches)
}
''', 'loads=1\nmatched=6',
'调用表用键关联进行中的装载。首个请求创建完成通道并执行 load，后续请求等同一通道关闭后读取结果；完成时删除表项，所以它合并重叠请求而不是永久缓存。测试用 joined 和 release 精确保证五个等待者已加入，再放行装载，避免靠 Sleep 猜测调度。通道关闭建立结果写入与等待者读取之间的同步关系。',
['必须在结果字段写好之后关闭完成通道，否则等待者可能读到零值。','装载 panic 或提前返回也要解除等待并清理表项，生产实现需完整异常收尾。'],
'为 Call 增加 Err，合并一次失败装载并让所有等待者看到同一错误。','保存 value 和 err 后统一关闭 Done；等待者读两个字段，失败完成同样删除进行中表项。')

emit(234, r'''
package main
import("fmt";"sort";"sync")
func main(){
 var mu sync.Mutex;cond:=sync.NewCond(&mu);ready:=0;start:=false;results:=make(chan int,3)
 for id:=1;id<=3;id++{go func(id int){mu.Lock();ready++;cond.Broadcast();for !start{cond.Wait()};mu.Unlock();results<-id*10}(id)}
 mu.Lock();for ready<3{cond.Wait()};start=true;cond.Broadcast();mu.Unlock()
 values:=[]int{};for i:=0;i<3;i++{values=append(values,<-results)};sort.Ints(values)
 fmt.Printf("ready=%d\nresults=%v\n",ready,values)
}
''', 'ready=3\nresults=[10 20 30]',
'Cond 把等待与受锁保护的条件联系起来。每个成员登记就绪后等待 start，主协程也在循环中等待 ready 达到三，再设置条件并广播。Wait 会暂时释放锁，被唤醒后重新取得锁，所以所有判断都必须写成循环。结果另经通道收集并排序，不让线程调度顺序污染断言。',
['只调用 Broadcast 而不改变条件，会让等待者醒来后继续等待。','必须先持有 Cond 使用的锁再调用 Wait，且唤醒后重新检查条件。'],
'加入第四个成员，只修改成员总数，保持同一屏障逻辑。','把 total 常量用于启动次数、ready 条件和结果接收次数；不要把三处边界分开写死。')

emit(235, r'''
package main
import("context";"fmt";"sync")
func main(){
 ctx,cancel:=context.WithCancel(context.Background());defer cancel();numbers:=make(chan int);squares:=make(chan int);var stages sync.WaitGroup;stages.Add(2)
 go func(){defer stages.Done();defer close(numbers);for n:=1;;n++{select{case numbers<-n:case <-ctx.Done():return}}}()
 go func(){defer stages.Done();defer close(squares);for{select{case <-ctx.Done():return;case n,ok:=<-numbers:if !ok{return};select{case squares<-n*n:case <-ctx.Done():return}}}}()
 consumed:=[]int{};for len(consumed)<3{consumed=append(consumed,<-squares)};cancel();stages.Wait()
 fmt.Printf("consumed=%v\nstages-exited=true\n",consumed)
}
''', 'consumed=[1 4 9]\nstages-exited=true',
'流水线的每个潜在阻塞发送和接收都同时监听取消。消费者拿到前三个平方后主动 cancel，再 Wait 所有阶段，确认上游没有遗留阻塞发送。通道只由产生该通道的阶段关闭，消费者不越权关闭上游通道。这里输出前三项确定，但取消后阶段可能在停止前多做少量准备，因此不声称精确处理总次数。',
['只在循环顶端检查取消，随后无条件发送仍可能永久阻塞。','消费者关闭生产者仍在发送的通道会触发 panic。'],
'让第二阶段在收到负数时返回错误并取消整条流水线。','添加容量为一的错误通道保存首个错误；错误阶段调用 cancel，主协程等待全部 stages 后再报告错误。')

emit(236, r'''
package main
import("fmt";"sync";"sync/atomic")
type Config struct{Version int;Label string}
func main(){
 var current atomic.Value;current.Store(Config{1,"v1"});ready:=make(chan struct{});var readers sync.WaitGroup;var invalid int32
 for i:=0;i<4;i++{readers.Add(1);go func(){defer readers.Done();<-ready;for n:=0;n<100;n++{snapshot:=current.Load().(Config);if snapshot.Label!=fmt.Sprintf("v%d",snapshot.Version){atomic.AddInt32(&invalid,1)}}}()}
 close(ready);for version:=2;version<=20;version++{current.Store(Config{version,fmt.Sprintf("v%d",version)})};readers.Wait()
 final:=current.Load().(Config);fmt.Printf("invalid=%d\nfinal=%d:%s\n",invalid,final.Version,final.Label)
}
''', 'invalid=0\nfinal=20:v20',
'发布端构造完整 Config 值后一次 Store，读取者一次 Load 得到同一版本的字段组合。四个读者反复检查 Version 和 Label 的关联，最终版本固定为二十。示例使用只含值字段的结构，不共享可变 map 或切片。atomic.Value 保证发布原子性，却不会替你把内部引用指向的数据变成不可变。',
['同一个 atomic.Value 的 Store 必须保持具体类型一致，不能一会存 Config 一会存指针。','发布后修改其中的 map 或切片仍会造成共享数据竞争，应先深复制。'],
'在 Config 加入端口切片，并保证发布后不被外部修改。','构造快照时复制切片；读取接口也不要将可修改内部切片直接暴露给调用方。')

emit(237, r'''
package main
import("fmt";"sort";"sync")
func produce(values []int)<-chan int{out:=make(chan int);go func(){defer close(out);for _,value:=range values{out<-value}}();return out}
func merge(inputs ...<-chan int)<-chan int{
 out:=make(chan int);var workers sync.WaitGroup
 for _,input:=range inputs{workers.Add(1);go func(input <-chan int){defer workers.Done();for value:=range input{out<-value}}(input)}
 go func(){workers.Wait();close(out)}();return out
}
func main(){values:=[]int{};for value:=range merge(produce([]int{1,3}),produce([]int{2,4})){values=append(values,value)};sort.Ints(values);fmt.Printf("merged=%v\n",values)}
''', 'merged=[1 2 3 4]',
'扇入函数为每个输入启动转发者，所有转发者共享输出但不负责关闭它。唯一收尾协程等待 WaitGroup，再关闭输出，主协程才能安全 range 到结束。两个生产者各自关闭自己的通道。这个 merge 保留每条输入内部顺序，却不承诺跨输入顺序，所以最终断言前排序。',
['任意一个转发者提前关闭共享输出，其他转发者可能向已关闭通道发送。','若消费者提前停止读取，这个无取消版本会留下阻塞协程，扩展时需传播取消。'],
'让 merge 接受 context，并允许消费者读到两项后退出。','给转发发送增加 select 的 ctx.Done 分支；取消后等待全部转发者，再由唯一收尾方关闭输出。')

emit(238, r'''
package main
import("errors";"fmt";"sort";"sync")
type Result struct{Index int;Value int;Err error}
func main(){
 input:=[]int{4,-2,0,7};out:=make(chan Result,len(input));var workers sync.WaitGroup
 for index,value:=range input{workers.Add(1);go func(index,value int){defer workers.Done();r:=Result{Index:index,Value:value*2};if value<=0{r.Err=errors.New("must be positive")};out<-r}(index,value)}
 workers.Wait();close(out);rows:=[]Result{};for r:=range out{rows=append(rows,r)};sort.Slice(rows,func(i,j int)bool{return rows[i].Index<rows[j].Index})
 failures:=0;for _,r:=range rows{if r.Err!=nil{failures++;fmt.Printf("%d:error=%s\n",r.Index,r.Err)}else{fmt.Printf("%d:value=%d\n",r.Index,r.Value)}};fmt.Printf("failures=%d\n",failures)
}
''', '0:value=8\n1:error=must be positive\n2:error=must be positive\n3:value=14\nfailures=2',
'每个并行任务返回独立 Result，包含输入下标、计算值和错误。收集后按下标排列，成功和全部失败都被报告，而非遇到第一个错误就取消其他验证。结果通道容量足够容纳全部任务，所以等待完成后再收集不会死锁。这样的模式适合需要向用户一次展示整批问题的离线校验。',
['用共享 err 变量在多个协程中赋值会产生竞争并丢失部分错误。','错误结果中的 Value 不应被当作已验证的有效业务结果。'],
'把错误增加原始输入值与字段名，保持错误顺序稳定。','使用 fmt.Errorf 包含 index、value 和字段；仍按 Result.Index 排序后统一展示。')

emit(239, r'''
package main
import("context";"fmt")
type Request struct{Delta int;Reply chan int;Context context.Context}
func main(){
 requests:=make(chan Request);done:=make(chan struct{})
 go func(){defer close(done);balance:=0;for request:=range requests{if request.Context.Err()!=nil{continue};balance+=request.Delta;request.Reply<-balance}}()
 ask:=func(ctx context.Context,delta int)(int,bool){if ctx.Err()!=nil{return 0,false};reply:=make(chan int,1);select{case requests<-Request{delta,reply,ctx}:case <-ctx.Done():return 0,false};select{case value:=<-reply:return value,true;case <-ctx.Done():return 0,false}}
 first,_:=ask(context.Background(),5);ctx,cancel:=context.WithCancel(context.Background());cancel();_,accepted:=ask(ctx,100);last,_:=ask(context.Background(),2)
 close(requests);<-done;fmt.Printf("first=%d\ncancelled-accepted=%t\nfinal=%d\n",first,accepted,last)
}
''', 'first=5\ncancelled-accepted=false\nfinal=7',
'actor 协程独占 balance，外部通过请求通道提交增量，每个请求拥有独立的一格响应通道。预先取消的请求不会进入队列，正常请求依次得到五和七。回复缓冲保证调用方在请求已提交后放弃等待时，actor 仍能完成回复而不阻塞。示例只保证预取消不修改状态；提交后取消可能已经执行，不能承诺事务回滚。',
['调用方取消等待不代表已经提交的请求被撤销，需要明确协议语义。','响应通道无缓冲时，已取消调用方不再接收会堵住 actor。'],
'加入只读查询请求，不改变 balance。','在 Request 增加操作类型，由 actor 对 query 直接回复当前余额，对 add 才执行 Delta。')

emit(240, r'''
package main
import("fmt";"sync")
type Service struct{once sync.Once;value string;err error;attempts int}
func(s *Service)Get()(string,error){s.once.Do(func(){s.attempts++;s.err=fmt.Errorf("local config missing")});return s.value,s.err}
func main(){
 service:=&Service{};var callers sync.WaitGroup;errors:=make(chan string,4)
 for i:=0;i<4;i++{callers.Add(1);go func(){defer callers.Done();_,err:=service.Get();if err!=nil{errors<-err.Error()}}()};callers.Wait();close(errors)
 count:=0;same:=true;for message:=range errors{count++;same=same&&message=="local config missing"}
 fmt.Printf("attempts=%d\nerrors=%d\nsame=%t\n",service.attempts,count,same)
}
''', 'attempts=1\nerrors=4\nsame=true',
'Once 只执行初始化闭包一次，并让其他调用等待初始化结束。结构把成功值与错误一起保留，所以初始化失败后所有调用得到同一错误，而不是重新尝试。四个并发调用的错误通过通道汇总，Wait 后检查尝试次数为一。若业务要求失败后重试，就需要另一套状态机，不能假设 Once 自动重置。',
['Once 的初始化失败也算已经执行，后续 Do 不会自动重试。','只保存成功值、不保存错误，会让后续调用误认为零值是有效初始化结果。'],
'把初始化改成从给定字节配置解码，分别创建成功和失败的 Service。','每个 Service 保留自己的 once、value 和 err；对两个实例分别检查只执行一次和结果稳定。')
