"""Author T151-T160 collection and graph drafts."""
from author_common import lesson

lesson(151, "LRU 缓存淘汰", ["container/list", "索引映射", "最近使用策略"],
       "实现容量二的缓存，命中提升热度，更新既有项并淘汰最久未使用键。",
       "链表前端表示最近使用，map 将键定位到链表元素，命中与更新都移动到前端。新增后若超容量，只移除尾部并同步删除 map 项。程序先访问 a，再插入 c，验证 b 被淘汰；再次更新 a 不会增加元素数量。这个缓存只约束项数且没有并发保护，若共享给多个 goroutine，需要在完整操作周围统一同步。",
       ["只删链表不删索引会留下已淘汰的幽灵命中。", "更新已有键应复用元素，重复插入会造成同键多节点。"],
       "增加 Delete 方法，并让删除不存在键返回 false。",
       "先查 map，存在时从链表 Remove 并 delete map，返回 true；不存在时不改变链表顺序。",
       r'''
       package main
       import ("container/list"; "fmt")

       type Entry struct { Key string; Value int }
       type Cache struct { Capacity int; Order *list.List; Entries map[string]*list.Element }
       func newCache(capacity int) *Cache {
           if capacity < 1 { panic("invalid capacity") }
           return &Cache{capacity, list.New(), map[string]*list.Element{}}
       }
       func (c *Cache) Get(key string) (int, bool) {
           element, ok := c.Entries[key]; if !ok { return 0, false }
           c.Order.MoveToFront(element); return element.Value.(Entry).Value, true
       }
       func (c *Cache) Put(key string, value int) {
           if element, ok := c.Entries[key]; ok {
               element.Value = Entry{key, value}; c.Order.MoveToFront(element); return
           }
           c.Entries[key] = c.Order.PushFront(Entry{key, value})
           if c.Order.Len() > c.Capacity {
               last := c.Order.Back(); delete(c.Entries, last.Value.(Entry).Key); c.Order.Remove(last)
           }
       }
       func (c *Cache) Keys() []string {
           keys := []string{}
           for element := c.Order.Front(); element != nil; element = element.Next() { keys = append(keys, element.Value.(Entry).Key) }
           return keys
       }
       func main() {
           cache := newCache(2); cache.Put("a", 1); cache.Put("b", 2)
           value, ok := cache.Get("a"); fmt.Printf("hit=%d found=%t\n", value, ok)
           cache.Put("c", 3); _, ok = cache.Get("b")
           fmt.Printf("b-evicted=%t order=%v\n", !ok, cache.Keys())
           cache.Put("a", 10); value, _ = cache.Get("a")
           fmt.Printf("updated=%d order=%v\n", value, cache.Keys())
       }
       ''', "hit=1 found=true\nb-evicted=true order=[c a]\nupdated=10 order=[a c]")

lesson(152, "优先级任务队列", ["container/heap", "heap.Fix", "元素索引", "并列规则"],
       "按截止时间和序号执行任务，并在队列中调整一个任务的优先级。",
       "任务保存自己在堆中的索引，Swap 每次交换都更新索引。修改 Due 后调用 heap.Fix，只修复受影响位置，不需要重建整个队列。相同截止时间用 Seq 决胜，执行顺序可重复。Pop 清除底层引用并将 Index 设为负一，防止外部把已取出的任务当作仍在队列中更新。生产更新接口还应检查索引与对象身份。",
       ["Swap 忘记更新索引会让 Fix 修改错误的任务。", "直接更改优先级而不调用 Fix 会破坏堆不变量。"],
       "封装 Update，拒绝更新 Index 为负一的已出队任务。",
       "检查索引范围以及 queue[index] 是否正是传入指针，通过后设置 Due 并调用 heap.Fix；已取出对象返回错误。",
       r'''
       package main
       import ("container/heap"; "fmt")

       type Task struct { Name string; Due int; Seq int; Index int }
       type Tasks []*Task
       func (q Tasks) Len() int { return len(q) }
       func (q Tasks) Less(i, j int) bool { if q[i].Due != q[j].Due { return q[i].Due < q[j].Due }; return q[i].Seq < q[j].Seq }
       func (q Tasks) Swap(i, j int) { q[i], q[j] = q[j], q[i]; q[i].Index = i; q[j].Index = j }
       func (q *Tasks) Push(value interface{}) { task := value.(*Task); task.Index = len(*q); *q = append(*q, task) }
       func (q *Tasks) Pop() interface{} { old := *q; task := old[len(old)-1]; old[len(old)-1] = nil; *q = old[:len(old)-1]; task.Index = -1; return task }
       func main() {
           queue := &Tasks{}
           first := &Task{Name:"A", Due:5, Seq:1}
           heap.Push(queue, first); heap.Push(queue, &Task{Name:"B", Due:3, Seq:2}); heap.Push(queue, &Task{Name:"C", Due:3, Seq:3})
           first.Due = 2; heap.Fix(queue, first.Index)
           for queue.Len() > 0 { task := heap.Pop(queue).(*Task); fmt.Printf("%s@%d\n", task.Name, task.Due) }
           fmt.Printf("removed-index=%d\n", first.Index)
       }
       ''', "A@2\nB@3\nC@3\nremoved-index=-1")

lesson(153, "流式 Top K", ["小根堆", "有限空间", "订单排序", "并列选择"],
       "在固定三项空间内保留最大订单，并以稳定规则输出最终结果。",
       "小根堆根部保存当前最差的保留项，新订单只有比根部更好才替换。金额相同采用 ID 字典序较小优先，堆内因此让较大的 ID 更差；最终输出则按金额降序、ID 升序排序。算法在读取六条订单期间最多保存三条，所需空间与总输入长度无关。这个全序同时定义选择与展示，避免两阶段并列规则矛盾。",
       ["Top K 最大值需要保留最差项在根部，不是直接维护最大堆。", "堆中的并列优先级与最终排序必须一致，否则边界订单选择不稳定。"],
       "支持 K 为零并立即返回空结果，拒绝负数 K。",
       "在建堆和访问根节点前检查 K：负数返回错误，零返回空切片，正数才进入流式维护。",
       r'''
       package main
       import ("container/heap"; "fmt"; "sort")

       type Order struct { ID string; Amount int }
       type Orders []Order
       func (h Orders) Len() int { return len(h) }
       func (h Orders) Less(i, j int) bool { if h[i].Amount != h[j].Amount { return h[i].Amount < h[j].Amount }; return h[i].ID > h[j].ID }
       func (h Orders) Swap(i, j int) { h[i], h[j] = h[j], h[i] }
       func (h *Orders) Push(value interface{}) { *h = append(*h, value.(Order)) }
       func (h *Orders) Pop() interface{} { old := *h; value := old[len(old)-1]; *h = old[:len(old)-1]; return value }
       func main() {
           best := &Orders{}
           for _, order := range []Order{{"A",40},{"B",10},{"C",50},{"D",50},{"E",30},{"F",60}} {
               if best.Len() < 3 { heap.Push(best, order); continue }
               worst := (*best)[0]
               if order.Amount > worst.Amount || (order.Amount == worst.Amount && order.ID < worst.ID) { (*best)[0] = order; heap.Fix(best, 0) }
           }
           result := append([]Order(nil), (*best)...)
           sort.Slice(result, func(i,j int) bool { if result[i].Amount != result[j].Amount { return result[i].Amount > result[j].Amount }; return result[i].ID < result[j].ID })
           fmt.Printf("kept=%d\n", len(result))
           for _, order := range result { fmt.Printf("%s=%d\n", order.ID, order.Amount) }
       }
       ''', "kept=3\nF=60\nC=50\nD=50")

lesson(154, "最短跳数路径", ["广度优先搜索", "container/list", "父节点回溯"],
       "在无权站点图中寻找最少跳数路径，处理起点即终点和不可达站点。",
       "BFS 按距离逐层扩展，首次访问一个站点时记录父节点，因此到终点的回溯链具有最少边数。访问标记在入队时设置，避免多个邻居重复把同一站点加入队列。邻接表使用固定顺序，最短路径并列时结果也确定。无权图的最少边数与带权图最短距离不同，不能把此方法直接用于距离各异的道路。",
       ["出队时才标记访问会导致同一节点被重复入队。", "BFS 保证的是最少边数，不保证带权路线的最小总费用。"],
       "为结果同时返回跳数，并对不可达结果返回明确错误。",
       "路径成功时跳数为 len(path)-1；空路径返回不可达错误，起点等于终点的单节点路径返回零。",
       r'''
       package main
       import ("container/list"; "fmt")

       func route(graph map[string][]string, start, target string) []string {
           queue := list.New(); queue.PushBack(start)
           parent := map[string]string{start:""}
           for queue.Len() > 0 {
               element := queue.Front(); at := element.Value.(string); queue.Remove(element)
               if at == target {
                   path := []string{}
                   for node := target; node != ""; node = parent[node] { path = append(path, node) }
                   for left, right := 0, len(path)-1; left < right; left, right = left+1, right-1 { path[left], path[right] = path[right], path[left] }
                   return path
               }
               for _, next := range graph[at] { if _, seen := parent[next]; !seen { parent[next] = at; queue.PushBack(next) } }
           }
           return nil
       }
       func main() {
           graph := map[string][]string{"A":{"B","C"},"B":{"D"},"C":{"D","E"},"D":{"F"},"E":{"F"},"F":{}}
           path := route(graph,"A","F")
           fmt.Printf("path=%v hops=%d\n", path, len(path)-1)
           fmt.Printf("unreachable=%t same=%v\n", route(graph,"A","Z") == nil, route(graph,"A","A"))
       }
       ''', "path=[A B D F] hops=3\nunreachable=true same=[A]")

lesson(155, "依赖环定位", ["深度优先搜索", "三色标记", "路径栈", "确定性遍历"],
       "用 DFS 颜色与路径栈输出具体依赖闭环，并验证无环依赖图。",
       "白色节点尚未访问，灰色节点处于当前递归路径，黑色节点已经完成。只有遇到灰色邻居才构成环，路径栈及节点位置可截取具体闭环；遇到黑色节点表示共享依赖，不应误报。排序根节点和各邻居使首个环的选择稳定。例子输出 app→db→cache→app，另一组 build→parse→scan 则没有闭环。",
       ["把所有已访问节点都判为环，会误伤合法的共享依赖。", "没有排序的 map 遍历会让多个闭环时的报告顺序漂移。"],
       "为无环图输出一个合法构建顺序，保证依赖先于使用者。",
       "在 DFS 节点变黑时追加节点到结果，图边表示使用者指向依赖时该后序结果已满足依赖在前；检测到环则拒绝输出构建顺序。",
       r'''
       package main
       import ("fmt"; "sort")

       func cycle(graph map[string][]string) []string {
           colors := map[string]int{}; positions := map[string]int{}; stack := []string{}; result := []string{}
           nodes := map[string]bool{}
           for node, next := range graph { nodes[node]=true; for _, name := range next { nodes[name]=true } }
           keys := []string{}; for node := range nodes { keys=append(keys,node) }; sort.Strings(keys)
           var visit func(string) bool
           visit = func(node string) bool {
               colors[node]=1; positions[node]=len(stack); stack=append(stack,node)
               neighbors := append([]string(nil),graph[node]...); sort.Strings(neighbors)
               for _, next := range neighbors {
                   if colors[next]==1 { result=append([]string(nil),stack[positions[next]:]...); result=append(result,next); return true }
                   if colors[next]==0 && visit(next) { return true }
               }
               stack=stack[:len(stack)-1]; delete(positions,node); colors[node]=2; return false
           }
           for _, node := range keys { if colors[node]==0 && visit(node) { return result } }
           return nil
       }
       func main() {
           fmt.Printf("cycle=%v\n", cycle(map[string][]string{"app":{"db"},"db":{"cache"},"cache":{"app"}}))
           fmt.Printf("acyclic=%t\n", cycle(map[string][]string{"build":{"parse"},"parse":{"scan"},"scan":{}})==nil)
       }
       ''', "cycle=[app db cache app]\nacyclic=true")

lesson(156, "带权路线规划", ["Dijkstra", "container/heap", "失效节点", "路径回溯"],
       "求配送图的最短距离，回溯路线并跳过堆中已失效的旧距离。",
       "每次从最小堆取当前最小距离，松弛出边并把改进后的距离再次入堆。无需在堆中查找旧项；旧项出队时若不等于 dist 中的最新值就跳过。固定图让 B 与 D 都发生距离改进，因此可观察两个失效项。Dijkstra 要求非负边，程序先遍历验证这一前提，再开始更新状态。生产长距离还需检查距离加法溢出。",
       ["带负权边时 Dijkstra 的贪心前提不成立，必须拒绝或改用其他算法。", "同一节点可能存在多个堆项，不能把每次出队都当作最新状态。"],
       "在计算候选距离前加入 int 溢出保护，并保持原图不变。",
       "已经保证边权非负后，检查 edge.Cost > MaxInt-current.Distance 则返回错误；图只读，拒绝后不修改调用方图结构。",
       r'''
       package main
       import ("container/heap"; "fmt")

       type Edge struct { To string; Cost int }
       type State struct { Node string; Distance int }
       type Frontier []State
       func (h Frontier) Len() int { return len(h) }
       func (h Frontier) Less(i,j int) bool { if h[i].Distance!=h[j].Distance { return h[i].Distance<h[j].Distance }; return h[i].Node<h[j].Node }
       func (h Frontier) Swap(i,j int) { h[i],h[j]=h[j],h[i] }
       func (h *Frontier) Push(value interface{}) { *h=append(*h,value.(State)) }
       func (h *Frontier) Pop() interface{} { old:=*h; value:=old[len(old)-1]; *h=old[:len(old)-1]; return value }
       func shortest(graph map[string][]Edge,start,target string) (int,[]string,int,error) {
           for _,edges:=range graph { for _,edge:=range edges { if edge.Cost<0 { return 0,nil,0,fmt.Errorf("negative edge") } } }
           distances:=map[string]int{start:0}; parent:=map[string]string{}; queue:=&Frontier{}; heap.Push(queue,State{start,0}); stale:=0
           for queue.Len()>0 {
               current:=heap.Pop(queue).(State)
               if current.Distance!=distances[current.Node] { stale++; continue }
               for _,edge:=range graph[current.Node] {
                   candidate:=current.Distance+edge.Cost; old,exists:=distances[edge.To]
                   if !exists || candidate<old { distances[edge.To]=candidate; parent[edge.To]=current.Node; heap.Push(queue,State{edge.To,candidate}) }
               }
           }
           distance,exists:=distances[target]; if !exists { return 0,nil,stale,fmt.Errorf("unreachable") }
           path:=[]string{}
           for node:=target;node!="";node=parent[node] { path=append(path,node) }
           for i,j:=0,len(path)-1;i<j;i,j=i+1,j-1 { path[i],path[j]=path[j],path[i] }
           return distance,path,stale,nil
       }
       func main() {
           graph:=map[string][]Edge{"A":{{"B",5},{"C",1}},"C":{{"B",2},{"D",8}},"B":{{"D",3}}}
           distance,path,stale,err:=shortest(graph,"A","D"); if err!=nil { panic(err) }
           fmt.Printf("distance=%d path=%v stale=%d\n",distance,path,stale)
           _,_,_,err=shortest(map[string][]Edge{"A":{{"B",-1}}},"A","B")
           fmt.Printf("negative-rejected=%t\n",err!=nil)
       }
       ''', "distance=6 path=[A C B D] stale=2\nnegative-rejected=true")

lesson(157, "时间段合并", ["sort.Slice", "半开区间", "重叠与相接", "输入副本"],
       "合并重叠和首尾相接的预约区间，保留独立间隔并拒绝逆序端点。",
       "先复制并验证所有区间，再按起点和终点排序。新段的起点不大于上一段终点时，二者重叠或相接，扩展末段终点；否则追加独立段。半开区间 [start,end) 让端点含义明确，相接的预约可以合并成连续占用。复制输入避免排序悄悄改变调用方顺序，零长度和逆序区间在此均被拒绝。",
       ["只按原始顺序尝试合并会漏掉晚出现的早起点区间。", "直接排序参数切片会修改调用方数据，若要保留原顺序必须复制。"],
       "新增一个求空闲区间的函数，在固定工作范围 [0,15) 内输出未预约片段。",
       "先把预约裁剪并合并到工作范围，维护 cursor，遇到段起点大于 cursor 时输出空闲段，最后补上 cursor 到十五的剩余部分。",
       r'''
       package main
       import ("fmt"; "sort")

       type Interval struct { Start int; End int }
       func merge(input []Interval) ([]Interval,error) {
           intervals:=append([]Interval(nil),input...)
           for _,item:=range intervals { if item.Start>=item.End { return nil,fmt.Errorf("invalid interval") } }
           sort.Slice(intervals,func(i,j int)bool { if intervals[i].Start!=intervals[j].Start { return intervals[i].Start<intervals[j].Start }; return intervals[i].End<intervals[j].End })
           result:=[]Interval{}
           for _,item:=range intervals {
               if len(result)==0 || item.Start>result[len(result)-1].End { result=append(result,item); continue }
               if item.End>result[len(result)-1].End { result[len(result)-1].End=item.End }
           }
           return result,nil
       }
       func main() {
           input:=[]Interval{{5,7},{1,3},{3,4},{10,12},{6,8}}
           result,err:=merge(input);if err!=nil { panic(err) }
           for i,item:=range result { if i>0 { fmt.Print(" ") };fmt.Printf("[%d,%d)",item.Start,item.End) };fmt.Println()
           fmt.Printf("input-preserved=%t\n",input[0].Start==5)
           _,err=merge([]Interval{{4,2}});fmt.Printf("invalid=%t\n",err!=nil)
       }
       ''', "[1,4) [5,8) [10,12)\ninput-preserved=true\ninvalid=true")

lesson(158, "有序数据游标分页", ["sort.Search", "排他游标", "末页边界"],
       "用二分查找定位排他游标，处理游标不存在和最后一页为空的情况。",
       "排他游标表示只返回严格大于 after 的记录，Search 查找第一个满足该条件的位置，而不要求游标值真实存在。检查有序前提与页大小后，用剩余项数限制截取范围，避免越界。分页结果复制出来，不向调用方暴露原始切片的可写窗口。重复 ID 都会被同一个排他游标跳过，因此真实分页键应唯一或使用联合键。",
       ["查找大于等于会在下一页重复上一页最后一项。", "以非唯一字段作游标可能漏掉相同值记录，需要联合排序键。"],
       "为相同时间戳的记录加入 ID，按时间和 ID 的联合排他游标分页。",
       "比较器先比较时间，时间相同再比较唯一 ID；Search 使用严格大于该二元组的条件，排序与分页保持同一全序。",
       r'''
       package main
       import ("fmt"; "sort")

       func page(data []int,after,size int)([]int,bool,error) {
           if size<1 || size>100 || !sort.IntsAreSorted(data) { return nil,false,fmt.Errorf("invalid page request") }
           start:=sort.Search(len(data),func(i int)bool{return data[i]>after})
           count:=len(data)-start;if count>size { count=size };end:=start+count
           return append([]int{},data[start:end]...),end<len(data),nil
       }
       func main() {
           data:=[]int{10,20,30,40,50}
           for _,after:=range []int{25,40,50} {
               items,more,err:=page(data,after,2);if err!=nil { panic(err) }
               fmt.Printf("after%d=%v more=%t\n",after,items,more)
           }
       }
       ''', "after25=[30 40] more=true\nafter40=[50] more=false\nafter50=[] more=false")

lesson(159, "并查集合并账号", ["并查集", "路径压缩", "共享标识", "稳定分组"],
       "通过共享邮箱合并账号，以路径压缩维护连通组并稳定导出分组。",
       "邮箱到首次拥有者的映射把共享关系转换为 Union 操作，Find 递归压缩父链，减少后续查询深度。合并时总让较小根作为代表，导出再对组内 ID 和根排序，结果不受 map 遍历影响。并查集能表达传递连通，但不会解释账号身份是否真实；真实合并还需要独立的邮箱所有权和冲突策略。",
       ["只合并直接共享邮箱的两项而不追踪传递关系，会漏掉间接连接。", "共享邮箱仅是本例的连接规则，不自动构成真实身份认证。"],
       "为每次 Union 保存触发合并的邮箱，支持解释两个账号为什么被归到同组。",
       "另建账号关系边列表，记录邮箱证据；并查集继续做快速连通查询，解释时在证据图上找路径，不依赖已压缩的父链。",
       r'''
       package main
       import ("fmt"; "sort")

       type Groups struct { Parent []int }
       func (g *Groups) Find(id int)int { if g.Parent[id]!=id { g.Parent[id]=g.Find(g.Parent[id]) };return g.Parent[id] }
       func (g *Groups) Union(a,b int) { a=g.Find(a);b=g.Find(b);if a>b { a,b=b,a };g.Parent[b]=a }
       func main() {
           accounts:=[][]string{{"a@local","shared@local"},{"b@local","shared@local"},{"c@local"},{"d@local","c@local"}}
           groups:=&Groups{Parent:make([]int,len(accounts))};for i:=range groups.Parent { groups.Parent[i]=i }
           owners:=map[string]int{}
           for id,emails:=range accounts { for _,email:=range emails { if previous,exists:=owners[email];exists { groups.Union(id,previous) } else { owners[email]=id } } }
           buckets:=map[int][]int{}
           for id:=range accounts { root:=groups.Find(id);buckets[root]=append(buckets[root],id+1) }
           roots:=[]int{};for root:=range buckets { roots=append(roots,root) };sort.Ints(roots)
           for _,root:=range roots { sort.Ints(buckets[root]);fmt.Printf("group=%v\n",buckets[root]) }
           fmt.Printf("shared=%t distinct=%t\n",groups.Find(0)==groups.Find(1),groups.Find(0)!=groups.Find(2))
       }
       ''', "group=[1 2]\ngroup=[3 4]\nshared=true distinct=true")

lesson(160, "前缀树补全", ["trie", "rune 键", "字典序遍历", "候选预算"],
       "建立 Unicode 单词前缀树，按字典序返回指定前缀的有限候选。",
       "每个节点保存 rune 到子节点的映射以及完整单词标记。查询先走到前缀节点，再递归收集后缀；每层排序子字符，保证结果的字典序。先收集当前完整词，因此 go 自己也属于 go 的补全结果。数量达到 limit 就停止递归，缺失前缀或非正上限返回空切片。Unicode 字符遍历避免把中文拆成无意义字节节点。",
       ["不排序子节点会使候选顺序随 map 变化。", "前缀本身可能是完整单词，不能只收集更长后缀。"],
       "为节点记录单词热度，改为返回热度最高的前三项并用单词字典序决胜。",
       "热度排序与字典序 DFS 不同，不能遇到前三项就停止；收集所有匹配词或维护带上界的搜索结构，再用明确的全序挑选结果。",
       r'''
       package main
       import ("fmt"; "sort")

       type Node struct { Children map[rune]*Node; End bool }
       func newNode()*Node { return &Node{Children:map[rune]*Node{}} }
       func (root *Node) Insert(word string) {
           node:=root;for _,r:=range word { if node.Children[r]==nil { node.Children[r]=newNode() };node=node.Children[r] };node.End=true
       }
       func (root *Node) Complete(prefix string,limit int)[]string {
           result:=[]string{};if limit<=0 { return result };node:=root
           for _,r:=range prefix { node=node.Children[r];if node==nil { return result } }
           var walk func(*Node,string)
           walk=func(at *Node,text string) {
               if len(result)>=limit { return };if at.End { result=append(result,text) }
               keys:=[]rune{};for r:=range at.Children { keys=append(keys,r) };sort.Slice(keys,func(i,j int)bool{return keys[i]<keys[j]})
               for _,r:=range keys { if len(result)>=limit { break };walk(at.Children[r],text+string(r)) }
           }
           walk(node,prefix);return result
       }
       func main() {
           root:=newNode();for _,word:=range []string{"gone","go","gopher","golang","猫咪","猫"} { root.Insert(word) }
           fmt.Printf("go=%v\n",root.Complete("go",3));fmt.Printf("猫=%v\n",root.Complete("猫",2));fmt.Printf("missing=%v\n",root.Complete("z",3))
       }
       ''', "go=[go golang gone]\n猫=[猫 猫咪]\nmissing=[]")
