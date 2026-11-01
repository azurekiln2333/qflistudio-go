"""Author T161-T170 numerical and business-calculation drafts."""
from author_common import lesson

lesson(161, "整数分币与折扣", ["整数金额", "strconv.ParseInt", "基点", "四舍五入"],
       "用整数分表示金额，按逐项四舍五入规则计算折扣与税费。",
       "金额解析要求非负十进制、最多两位小数，并设置明确上限；计算过程中只使用整数分。百分之一基点为万分之一，roundRate 通过加五千再除一万实现非负数的半入舍入。先把折扣取整，再对折后金额计算税费，这个顺序是业务规则的一部分。12.35 的折扣为 1.24，折后 11.11 的税费为 0.92，最终 12.03。",
       ["整数计算仍可能溢出，所以解析上限必须与后续乘法预算配合。", "先算税再折扣或最后才统一舍入可能得到不同金额，必须固定规则。"],
       "支持退款负数，并明确负数恰好半分时的舍入方向。",
       "不要直接复用加五千公式处理负数；先定义远离零或银行家舍入规则，再对绝对值舍入并恢复符号，同时检查最小整数取绝对值的边界。",
       r'''
       package main
       import ("fmt"; "strconv"; "strings")

       func cents(text string)(int64,error) {
           parts:=strings.Split(text,".");if len(parts)>2 || parts[0]=="" { return 0,fmt.Errorf("invalid amount") }
           fraction:="00";if len(parts)==2 { if len(parts[1])<1 || len(parts[1])>2 { return 0,fmt.Errorf("invalid precision") };fraction=parts[1];if len(fraction)==1 { fraction+="0" } }
           for _,r:=range parts[0]+fraction { if r<'0'||r>'9' { return 0,fmt.Errorf("invalid digit") } }
           whole,err:=strconv.ParseInt(parts[0],10,64);if err!=nil || whole>1000000000 { return 0,fmt.Errorf("amount exceeds budget") }
           tail,err:=strconv.ParseInt(fraction,10,64);if err!=nil { return 0,err };return whole*100+tail,nil
       }
       func roundRate(amount,basisPoints int64)int64 { return (amount*basisPoints+5000)/10000 }
       func main() {
           base,err:=cents("12.35");if err!=nil { panic(err) };discount:=roundRate(base,1000);tax:=roundRate(base-discount,825)
           fmt.Printf("base=%d discount=%d tax=%d total=%d\n",base,discount,tax,base-discount+tax)
           _,err=cents("12.345");fmt.Printf("precision-rejected=%t\n",err!=nil)
           _,err=cents("-1.00");fmt.Printf("negative-rejected=%t\n",err!=nil)
       }
       ''', "base=1235 discount=124 tax=92 total=1203\nprecision-rejected=true\nnegative-rejected=true")

lesson(162, "精确分数分账", ["math/big.Rat", "有理数", "显示精度", "守恒"],
       "把十元均分三份，验证精确总和与两位小数显示总和的差别。",
       "Rat 用分子分母保存精确有理数，三份 10/3 相加仍精确等于十。FloatString(2) 只是为每份生成 3.33 的显示文本，三个显示数相加却是 9.99。显示舍入没有改变 Rat 本身，但真正支付时必须制定余分分配规则，不能把每份显示值当作总额守恒的证明。Rat 运算会修改接收者，累加使用独立 sum 避免改写 share。",
       ["FloatString 是显示转换，不能保证每项独立舍入后的总额守恒。", "big.Rat 的接收者是可变对象，复用错误会意外覆盖原值。"],
       "把实际一千分分配为三笔整数分，保证总和一千且任意两笔差不超过一分。",
       "先取商三百三十三和余数一，把多出的一分按固定账号顺序分给第一笔，结果为 334、333、333。",
       r'''
       package main
       import ("fmt"; "math/big")

       func main() {
           share:=big.NewRat(10,3);sum:=new(big.Rat)
           for i:=0;i<3;i++ { sum.Add(sum,share) }
           fmt.Printf("share=%s displayed=%s\n",share.RatString(),share.FloatString(2))
           fmt.Printf("exact-total=%s preserved=%t\n",sum.RatString(),sum.Cmp(big.NewRat(10,1))==0)
           fmt.Printf("displayed-total=%d.%02d\n",(333*3)/100,(333*3)%100)
       }
       ''', "share=10/3 displayed=3.33\nexact-total=10 preserved=true\ndisplayed-total=9.99")

lesson(163, "大整数排列组合", ["math/big.Int", "组合数递推", "精确除法"],
       "计算超出 int64 的组合数，以逐步乘除递推保持精确整数结果。",
       "C(n,k) 可通过每一步乘 n-k+i 再除 i 递推，结果始终为整数；利用 k 与 n-k 对称减少循环。big.Int 避免固定宽度溢出，也避免先转浮点造成精度损失。程序计算 C(70,35)，并验证它无法放入 int64；C(0,0) 为一，k 大于 n 则明确报错。任意精度不等于无限资源，外部输入仍需限制 n。",
       ["用 float64 计算后转整数无法恢复已经丢失的低位。", "大整数操作会改变接收者，循环中要注意中间值别名。"],
       "为 n 增加一万的上限，并在开始分配和循环之前返回预算错误。",
       "参数校验先检查 n 的非负性与最大值，再检查 0<=k<=n，最后应用对称性；不要等到大整数已增长后才拒绝。",
       r'''
       package main
       import ("fmt"; "math/big")

       func choose(n,k int)(*big.Int,error) {
           if n<0 || k<0 || k>n { return nil,fmt.Errorf("invalid combination") }
           if k>n-k { k=n-k };result:=big.NewInt(1)
           for i:=1;i<=k;i++ { result.Mul(result,big.NewInt(int64(n-k+i)));result.Quo(result,big.NewInt(int64(i))) }
           return result,nil
       }
       func main() {
           value,err:=choose(70,35);if err!=nil { panic(err) };fmt.Printf("C70,35=%s\n",value.String());fmt.Printf("fits-int64=%t\n",value.IsInt64())
           boundary,err:=choose(0,0);if err!=nil { panic(err) };fmt.Printf("C0,0=%s\n",boundary.String())
           _,err=choose(3,4);fmt.Printf("invalid=%t\n",err!=nil)
       }
       ''', "C70,35=112186277816662845432\nfits-int64=false\nC0,0=1\ninvalid=true")

lesson(164, "在线均值与方差", ["Welford", "样本方差", "math.Abs", "流式统计"],
       "逐条更新均值与样本方差，并和可独立推导的固定数据核对。",
       "Welford 每次保存数量、均值和相对均值的平方偏差总和，不必保存完整历史，也避免直接用平方和减均值平方的严重抵消。八个样本的均值为五，偏差平方和为三十二，因此样本方差为 32/7；总体方差则会除以八。少于两个样本时样本方差没有定义，函数用布尔值显式报告。",
       ["样本方差分母为 n-1，不能与总体方差混用。", "浮点结果不应随意用精确相等比较，要依据量级选容差。"],
       "同时提供总体方差，并分别定义空输入和单样本的行为。",
       "总体方差在 n>0 时返回 M2/n，单样本为零；n==0 返回未定义标记。样本方差继续要求 n>=2。",
       r'''
       package main
       import ("fmt"; "math")

       type Stats struct { Count int; Mean float64; M2 float64 }
       func (s *Stats) Add(value float64) { s.Count++;delta:=value-s.Mean;s.Mean+=delta/float64(s.Count);s.M2+=delta*(value-s.Mean) }
       func (s Stats) Variance()(float64,bool) { if s.Count<2 { return 0,false };return s.M2/float64(s.Count-1),true }
       func main() {
           stats:=Stats{};for _,value:=range []float64{2,4,4,4,5,5,7,9} { stats.Add(value) };variance,ok:=stats.Variance()
           fmt.Printf("count=%d mean=%.2f sample-variance=%.4f\n",stats.Count,stats.Mean,variance)
           fmt.Printf("verified=%t\n",ok && math.Abs(variance-32.0/7)<1e-12)
           single:=Stats{};single.Add(9);_,ok=single.Variance();fmt.Printf("single-defined=%t\n",ok)
       }
       ''', "count=8 mean=5.00 sample-variance=4.5714\nverified=true\nsingle-defined=false")

lesson(165, "滑动窗口平均", ["环形窗口", "运行和", "预热期"],
       "用固定三个槽位与运行和计算最近读数平均，正确处理窗口尚未填满。",
       "写入新值前，若窗口已满就减掉将被覆盖的旧值；尚未满时只增加有效数量。平均值除以 Count，因此第一个与第二个样本不会被尚未写入的零槽稀释。读数 10、20、30、50 的最后窗口为 20、30、50，平均为 100/3。每次更新的时间固定，但整数运行和仍受 int64 范围限制。",
       ["预热期始终除以容量会低估前几个平均值。", "覆盖旧槽前忘记从运行和扣除旧值，会变成累计平均而非滑动平均。"],
       "返回当前最旧到最新的窗口内容，并验证复制结果不能修改内部状态。",
       "按 (Next-Count+容量)%容量 找起点，复制 Count 个值到新切片；调用者修改副本后重新读取窗口应保持不变。",
       r'''
       package main
       import "fmt"

       type Window struct { Values []int64; Next int; Count int; Sum int64 }
       func newWindow(size int)*Window { if size<=0 { panic("invalid window") };return &Window{Values:make([]int64,size)} }
       func (w *Window) Add(value int64)float64 {
           if w.Count==len(w.Values) { w.Sum-=w.Values[w.Next] } else { w.Count++ }
           w.Values[w.Next]=value;w.Sum+=value;w.Next=(w.Next+1)%len(w.Values)
           return float64(w.Sum)/float64(w.Count)
       }
       func main() {
           window:=newWindow(3)
           for _,value:=range []int64{10,20,30,50} { average:=window.Add(value);fmt.Printf("value=%d average=%.1f count=%d\n",value,average,window.Count) }
       }
       ''', "value=10 average=10.0 count=1\nvalue=20 average=15.0 count=2\nvalue=30 average=20.0 count=3\nvalue=50 average=33.3 count=3")

lesson(166, "百分位插值", ["sort.Float64s", "线性插值", "百分位定义", "NaN 校验"],
       "对延迟样本排序，用明确的线性插值定义计算 P50 与 P90，并验证单样本边界。",
       "本例采用位置 p*(n-1) 的百分位定义，向下和向上取整后在两个样本间线性插值。五个等间距样本的 P50 为三十，P90 位置为 3.6，因此结果为四十六。百分位有多种合法定义，报告中必须写清规则。程序拒绝空输入、越界 p、NaN 和无穷样本，并在副本上排序以保护调用方顺序。",
       ["不同百分位定义可能给出不同 P90，不能只写一个指标名。", "NaN 会破坏普通大小比较的排序前提，必须先校验。"],
       "增加 P0 与 P100 的检查，证明它们分别等于最小值和最大值。",
       "对相同样本分别传 p=0 和 p=1，索引变为零与 n-1，插值两端重合，结果应是十和五十。",
       r'''
       package main
       import ("fmt"; "math"; "sort")

       func percentile(input []float64,p float64)(float64,error) {
           if len(input)==0 || math.IsNaN(p) || p<0 || p>1 { return 0,fmt.Errorf("invalid percentile") }
           data:=append([]float64(nil),input...);for _,v:=range data { if math.IsNaN(v)||math.IsInf(v,0) { return 0,fmt.Errorf("nonfinite sample") } };sort.Float64s(data)
           position:=p*float64(len(data)-1);low:=int(math.Floor(position));high:=int(math.Ceil(position));return data[low]+(data[high]-data[low])*(position-float64(low)),nil
       }
       func main() {
           data:=[]float64{50,10,40,20,30};p50,err:=percentile(data,.5);if err!=nil { panic(err) };p90,err:=percentile(data,.9);if err!=nil { panic(err) }
           single,err:=percentile([]float64{7},.9);if err!=nil { panic(err) };fmt.Printf("p50=%.1f p90=%.1f single=%.1f\n",p50,p90,single)
           _,err=percentile(data,1.1);fmt.Printf("invalid=%t\n",err!=nil);_,err=percentile([]float64{math.NaN()},.5);fmt.Printf("nan-rejected=%t\n",err!=nil)
       }
       ''', "p50=30.0 p90=46.0 single=7.0\ninvalid=true\nnan-rejected=true")

lesson(167, "按区间直方图", ["sort.Search", "半开分桶", "溢出桶", "无效读数"],
       "为延迟读数分桶，明确上界不包含的规则，并独立统计负数拒绝和溢出桶。",
       "每个上界定义一个左闭右开桶，Search 找第一个严格大于读数的上界，所以恰好十进入第二桶，恰好一百进入溢出桶。先确认边界严格递增且为正，随后负读数被计入 rejected，其余每条恰好进入一个桶。固定输入覆盖每个端点附近，四个桶均为两条，可以独立核对计数守恒。",
       ["使用大于等于查找会改变端点归属，指标解释也随之变化。", "边界未排序或重复会破坏二分前提，应在接收数据前验证。"],
       "将普通桶计数转换为累计桶，并同时保留原始非累计计数。",
       "复制 counts 到新切片，对新切片做前缀和；不要就地覆盖原始计数，溢出桶的累计值应等于有效样本总数。",
       r'''
       package main
       import ("fmt"; "sort")

       func histogram(values,bounds []int)([]int,int,error) {
           for i,bound:=range bounds { if bound<=0 || (i>0 && bound<=bounds[i-1]) { return nil,0,fmt.Errorf("invalid bounds") } }
           counts:=make([]int,len(bounds)+1);rejected:=0
           for _,value:=range values { if value<0 { rejected++;continue };bucket:=sort.Search(len(bounds),func(i int)bool{return value<bounds[i]});counts[bucket]++ }
           return counts,rejected,nil
       }
       func main() {
           counts,rejected,err:=histogram([]int{0,9,10,49,50,99,100,150,-1},[]int{10,50,100});if err!=nil { panic(err) }
           fmt.Printf("under10=%d under50=%d under100=%d overflow=%d\n",counts[0],counts[1],counts[2],counts[3]);fmt.Printf("negative-rejected=%d\n",rejected)
       }
       ''', "under10=2 under50=2 under100=2 overflow=2\nnegative-rejected=1")

lesson(168, "库存多维聚合", ["结构体 map 键", "分组求和", "排序低库存清单"],
       "按仓库和商品组成联合键汇总库存，稳定输出低库存项。",
       "同一商品在不同仓库属于不同库存，因此用可比较的结构体作为联合 map 键。先验证并汇总所有非负数量，再筛选少于四件的项，最后按仓库和商品排序输出。两笔 A 仓 pen 会合为三件，B 仓 pen 保持一件。输入验证与聚合分开后，可以进一步加上溢出、单位和重复流水 ID 的业务检查。",
       ["只用商品作为键会把不同仓库错误合并。", "map 输出顺序不固定，低库存通知应先排序再发送或展示。"],
       "为不同商品配置各自的低库存阈值，缺少配置时返回错误。",
       "先确认每个出现的商品在阈值表中存在，再比较聚合量；不要把 map 缺失产生的零值当作合法阈值。",
       r'''
       package main
       import ("fmt"; "sort")

       type Key struct { Warehouse string; Product string }
       type Stock struct { Key Key; Quantity int }
       func aggregate(rows []Stock)(map[Key]int,error) {
           totals:=map[Key]int{}
           for _,row:=range rows { if row.Quantity<0 { return nil,fmt.Errorf("negative inventory") };totals[row.Key]+=row.Quantity };return totals,nil
       }
       func main() {
           totals,err:=aggregate([]Stock{{Key{"A","pen"},2},{Key{"A","pen"},1},{Key{"A","book"},9},{Key{"B","pen"},1},{Key{"B","book"},2}});if err!=nil { panic(err) }
           low:=[]Key{};for key,quantity:=range totals { if quantity<4 { low=append(low,key) } }
           sort.Slice(low,func(i,j int)bool{if low[i].Warehouse!=low[j].Warehouse{return low[i].Warehouse<low[j].Warehouse};return low[i].Product<low[j].Product})
           for _,key:=range low { fmt.Printf("%s/%s=%d\n",key.Warehouse,key.Product,totals[key]) }
       }
       ''', "A/pen=3\nB/book=2\nB/pen=1")

lesson(169, "有符号安全求和", ["int64 溢出", "math.MaxInt64", "部分结果", "错误位置"],
       "累加正负账目时预先检测溢出，返回错误项位置与此前已确认的总额。",
       "有符号整数溢出不会自动成为 Go 错误，所以相加前必须检查。正数用 total>MaxInt64-value 判断上溢，负数用 total<MinInt64-value 判断下溢，这两次阈值运算自身保持在范围内。发现错误时返回此前总额和零起始项索引，不先执行错误加法。示例覆盖普通混合账目、最大值再加一与最小值再减一。",
       ["先相加再比较可能已经溢出，错误值不能作为可靠依据。", "正负值的安全阈值不同，不能用绝对值统一处理 MinInt64。"],
       "在错误中加入当前值，并让调用者用 errors.As 读取结构化位置。",
       "定义包含 Index、Value、Total 的错误结构和 Error 方法，在检查失败时返回指针；调用者用 errors.As 提取，不解析错误字符串。",
       r'''
       package main
       import ("fmt"; "math")

       func sum(values []int64)(int64,int,error) {
           var total int64
           for i,value:=range values {
               if (value>0 && total>math.MaxInt64-value)||(value<0 && total<math.MinInt64-value) { return total,i,fmt.Errorf("sum overflow") }
               total+=value
           };return total,-1,nil
       }
       func main() {
           total,_,err:=sum([]int64{100,-30,20});if err!=nil { panic(err) };fmt.Printf("ok=%d\n",total)
           total,index,err:=sum([]int64{math.MaxInt64-2,2,1});fmt.Printf("positive=%d index=%d rejected=%t\n",total,index,err!=nil)
           total,index,err=sum([]int64{math.MinInt64+1,-1,-1});fmt.Printf("negative=%d index=%d rejected=%t\n",total,index,err!=nil)
       }
       ''', "ok=90\npositive=9223372036854775807 index=2 rejected=true\nnegative=-9223372036854775808 index=2 rejected=true")

lesson(170, "单位换算与量纲", ["strconv.ParseUint", "十进制与二进制单位", "乘法溢出"],
       "解析 KB、MiB 与原始字节，拒绝未知单位、负容量和换算溢出。",
       "KB 在本协议中固定为一千字节，MiB 为一百零二十四平方字节；无后缀表示原始字节。先按明确后缀选择倍率，再解析非负整数，通过 value>最大值/倍率 预检乘法。大小写和单位集合是协议的一部分，MB 不会被猜测成某种近似单位。这样容量配置的数值与量纲一起受到校验。",
       ["KB 与 KiB 含义不同，不能在界面和存储中混用。", "ParseUint 成功后乘倍率仍可能溢出，必须单独预检。"],
       "增加 KiB，保持 KB 的十进制定义不变，并测试两个单位不同。",
       "在后缀分支加入 KiB 倍率一千零二十四，2KB 应为二千而 2KiB 为二千零四十八；继续用同一除法检查乘法预算。",
       r'''
       package main
       import ("fmt"; "strconv"; "strings")

       func capacity(text string)(uint64,error) {
           text=strings.TrimSpace(text);factor:=uint64(1)
           if strings.HasSuffix(text,"MiB") { factor=1<<20;text=strings.TrimSuffix(text,"MiB")
           } else if strings.HasSuffix(text,"KB") { factor=1000;text=strings.TrimSuffix(text,"KB") }
           value,err:=strconv.ParseUint(strings.TrimSpace(text),10,64);if err!=nil { return 0,err }
           const maximum uint64=1<<63-1
           if value>maximum/factor { return 0,fmt.Errorf("capacity overflow") };return value*factor,nil
       }
       func main() {
           for _,input:=range []string{"2KB","2MiB","512"} { value,err:=capacity(input);if err!=nil { panic(err) };fmt.Printf("%s=%d\n",input,value) }
           _,err:=capacity("3MB");fmt.Printf("unknown=%t\n",err!=nil);_,err=capacity("-1KB");fmt.Printf("negative=%t\n",err!=nil);_,err=capacity("9223372036854775807MiB");fmt.Printf("overflow=%t\n",err!=nil)
       }
       ''', "2KB=2000\n2MiB=2097152\n512=512\nunknown=true\nnegative=true\noverflow=true")
