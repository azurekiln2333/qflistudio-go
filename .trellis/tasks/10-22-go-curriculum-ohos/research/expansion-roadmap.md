# Go expansion roadmap: T121–T280

160 distinct offline programs, grouped by concrete tasks. Every addition includes a runnable source file, an explanatory lesson, pitfalls, an exercise and deterministic expected output. Tutorial and example may share their own program; no cross-topic constant/title-only variants. Each implementation must include the behavior and error boundaries below.

All new displayed snippets use package main and keep inputs inside the program or declared fixtures. No remote downloads, shell execution or external HTTP services. Cryptographic operations use fresh randomness but assert stable verification outcomes rather than random bytes. Concurrency asserts sorted/ordered results and uses explicit synchronization. Clock-dependent examples receive a fixed logical clock.

Status: coordinator reviewed and approved for draft authoring (2026-10-23, main session). Authoring starts after the repaired original host baseline passes all 364 cases. Drafts stay under `research/expansion-draft`; publishing additions into bundled catalogs also requires the original 364-case OHOS gate. Host results do not establish OHOS support.

## 文本与日志

| ID | Topic | Observable behavior | Standard library |
|---|---|---|---|
| T121 | 统一混合换行 | 把 CRLF、CR 与 LF 日志统一为逐行记录，保留末行无换行的内容 | strings |
| T122 | Unicode 标识清洗 | 将含中文、空白和标点的标题变为稳定标识，合并分隔符并保留字母数字 | unicode, strings |
| T123 | 日志字段脱敏 | 仅隐藏日志中的 email 与 token 字段，保留时间、级别和消息结构 | regexp, strings |
| T124 | 词频 Top N 与并列规则 | 统计多行文档词频，按次数降序、词字典序处理并列，取前三名 | bufio, sort, strings |
| T125 | 带引号键值解析 | 解析 name="Li Yu" enabled=true 一类配置并报告未闭合引号 | strings, strconv |
| T126 | 最长公共前后缀 | 对文件版本名计算公共前后缀，避免切断 UTF-8 中文字符 | strings, unicode/utf8 |
| T127 | 逐行差异定位 | 对比两份文本，输出新增、删除及改变的行号和内容 | bufio, strings |
| T128 | 扫描器长行预算 | 设置最大行长，分别处理合法长行与超出预算输入并显式报告错误 | bufio, strings |
| T129 | 多模式替换优先级 | 用单次 Replacer 同时转义日志分隔符，验证新生成文本不会被二次替换 | strings |
| T130 | 词边界倒排索引 | 为三篇本地文档建立去重词到文档 ID 索引，求两个词的交集 | unicode, sort |
## 编码与结构化数据

| ID | Topic | Observable behavior | Standard library |
|---|---|---|---|
| T131 | 十六进制校验输入 | 解析分组十六进制字节，拒绝奇数长度和非法字符，输出规范字节串 | encoding/hex |
| T132 | Base32 人工核对编号 | 生成无填充批次编号并验证解码往返与大小写输入策略 | encoding/base32 |
| T133 | URL 安全 Base64 游标 | 编码分页游标结构，验证非法游标和下一页位置 | encoding/base64, encoding/json |
| T134 | 严格 JSON 配置 | 拒绝未知字段与尾随第二个 JSON 值，保留有字段缺失时的默认值 | encoding/json |
| T135 | JSON 多态消息 | 先读取 kind 再用 RawMessage 解码两类载荷，拒绝未知事件类型 | encoding/json |
| T136 | JSON 部分更新的三态 | 区分字段缺失、null 与实际值，对用户资料应用部分更新 | encoding/json |
| T137 | CSV 账单汇总 | 按表头索引读取含引号的账单，拒绝坏金额并汇总有效行 | encoding/csv, strconv |
| T138 | CSV 安全导出 | 导出含逗号、双引号和换行的地址簿，再读回验证字段不变 | encoding/csv, strings |
| T139 | XML 库存与属性 | 读取 XML 属性及嵌套项目，修改低库存项目并重新编码 | encoding/xml |
| T140 | Gob 快照兼容读取 | 在内存中写入状态快照，用新增字段的结构读取并验证零值兼容 | encoding/gob, bytes |
## 字节流与资源预算

| ID | Topic | Observable behavior | Standard library |
|---|---|---|---|
| T141 | 长度前缀消息 | 编码两帧消息，逐帧读取并拒绝截断及超预算长度 | encoding/binary, io |
| T142 | 固定容量环形日志 | 保存最后三条记录，覆盖最旧项并按时间顺序导出 | bytes |
| T143 | 串联分片流 | 用 MultiReader 合并头部与多个分片，边读边验证完整内容 | io, strings |
| T144 | 边复制边计算摘要 | 用 TeeReader 在不重复读取数据的前提下复制并校验摘要 | io, crypto/sha256 |
| T145 | 随机访问区间 | 用 SectionReader 从同一 ReaderAt 读取两个独立区间并检查边界 | io, strings |
| T146 | 完整读取与截断分类 | 区分空输入 EOF 与半条记录 UnexpectedEOF，输出可恢复处理结果 | io, bytes |
| T147 | 受限读取防超量 | 用预算加一字节探测过长输入，区分刚好上限与被截断数据 | io, strings |
| T148 | 复用缓冲复制 | 借助固定缓冲与计数 Writer 复制数据，验证字节数和内容 | io, bytes |
| T149 | 前瞻协议探测 | Peek 识别协议前缀后消费一条记录，证明前瞻不会丢失数据 | bufio, bytes |
| T150 | 批量写入与 Flush | 写入前后检查底层数据可见性，Flush 后核对完整批次 | bufio, bytes |
## 集合与图算法

| ID | Topic | Observable behavior | Standard library |
|---|---|---|---|
| T151 | LRU 缓存淘汰 | 实现容量为二的缓存，命中提升热度并断言淘汰最久未使用键 | container/list |
| T152 | 优先级任务队列 | 按截止时间及序号执行任务，支持调整一个任务的优先级 | container/heap |
| T153 | 流式 Top K | 用小根堆在有限空间保留最大三条订单，稳定输出结果 | container/heap |
| T154 | 最短跳数路径 | 用 BFS 在站点图找最少换乘路径，并处理不可达终点 | container/list |
| T155 | 依赖环定位 | 用 DFS 颜色与路径栈报告依赖闭环，验证无环图 | sort |
| T156 | 带权路线规划 | 用 Dijkstra 求配送最短距离并回溯路径，跳过失效堆节点 | container/heap |
| T157 | 时间段合并 | 合并重叠及首尾相接的预约区间，保留独立区间 | sort |
| T158 | 有序数据游标分页 | 用二分定位排他游标，处理不存在的游标和末页 | sort |
| T159 | 并查集合并账号 | 通过共享邮箱合并账号，进行路径压缩并稳定导出分组 | sort |
| T160 | 前缀树补全 | 建立单词 trie，按字典序输出某前缀的有限候选项 | sort |
## 数值与业务计算

| ID | Topic | Observable behavior | Standard library |
|---|---|---|---|
| T161 | 整数分币与折扣 | 用整数分表示金额，按明确舍入规则计算折扣和税费 | strconv |
| T162 | 精确分数分账 | 用 Rat 分摊三份费用，说明小数显示与精确总和的区别 | math/big |
| T163 | 大整数排列组合 | 计算超出 int64 的组合数，用乘除递推避免浮点误差 | math/big |
| T164 | 在线均值与方差 | 用 Welford 更新流式统计，并与已知数据核对样本方差 | math |
| T165 | 滑动窗口平均 | 用环形槽和运行和计算最近三个读数平均，处理窗口未满 | fmt |
| T166 | 百分位插值 | 排序延迟样本，线性插值计算 P50 和 P90 并验证单样本边界 | sort, math |
| T167 | 按区间直方图 | 为延迟数据分桶，明确端点包含规则并累计溢出桶 | sort |
| T168 | 库存多维聚合 | 按仓库和商品汇总数量，输出排序后的低库存清单 | sort |
| T169 | 有符号安全求和 | 在累加账目时检测 int64 正负溢出，保留错误发生前的总额 | math |
| T170 | 单位换算与量纲 | 解析 KB、MiB 和原始字节三种单位，拒绝未知后缀和负容量 | strconv, strings |
## 时间与调度

| ID | Topic | Observable behavior | Standard library |
|---|---|---|---|
| T171 | 时区与同一时刻 | 解析带偏移 RFC3339 时间，转 UTC 并验证不同时区表示同一时刻 | time |
| T172 | UTC 时间桶聚合 | 把乱序事件按十五分钟 UTC 桶汇总，稳定输出空桶与非空桶 | time, sort |
| T173 | 工作日日期推进 | 按日历日期跳过周末计算第三个工作日，避免把天数当固定小时 | time |
| T174 | 跨午夜区间拆分 | 将一个会话拆为两个自然日的使用量，验证总时长守恒 | time |
| T175 | 可预测指数退避 | 计算带上限的重试等待序列，避免乘法溢出并输出累计预算 | time |
| T176 | 逻辑时钟 TTL 缓存 | 向缓存显式传入 now，验证到期边界和清理过程而不实际等待 | time, sort |
| T177 | 每日定点计划 | 从给定 now 求下一个每日执行时刻，处理当天已过的情况 | time |
| T178 | 日期严格校验 | 往返格式化检查非法日期与闰年边界，避免静默修正日期 | time |
| T179 | 计费时长向上取整 | 将多次使用时长按十五分钟计费，区分每段取整与总时长取整 | time |
| T180 | 多来源日志归并 | 以时间和来源序号归并三条已排序日志流，保持稳定顺序 | time, container/heap |
## 文件与虚拟文件系统

| ID | Topic | Observable behavior | Standard library |
|---|---|---|---|
| T181 | 项目路径约束 | 清洗相对路径并拒绝绝对路径和越界路径，说明词法校验边界 | path, strings |
| T182 | 内存配置文件树 | 用 MapFS 加载默认配置与子目录配置，处理不存在文件 | testing/fstest, io/fs |
| T183 | Glob 与确定性列表 | 按模式查找文档，解释单层通配与递归遍历差别 | testing/fstest, io/fs |
| T184 | 遍历时跳过目录 | WalkDir 忽略缓存目录，统计其余源文件数与总字节数 | testing/fstest, io/fs |
| T185 | 临时文件替换 | 在同一临时目录写入替代文件并 Rename，核对新内容与清理 | os, path/filepath |
| T186 | 目录树差异清单 | 对比两棵虚拟文件树的新增、删除和修改文件 | testing/fstest, io/fs, sort |
| T187 | 重复文件内容索引 | 按内容摘要将不同路径文件分组，输出重复组并排除唯一文件 | crypto/sha256, sort |
| T188 | 相对路径重定位 | 计算文档链接相对路径，验证移动根目录后链接目标一致 | path/filepath |
| T189 | 文件扩展名路由 | 按最后一个扩展名分类文件，处理点文件、多后缀和大小写 | path, strings |
| T190 | 文件权限位解释 | 从 FileMode 提取读写执行和目录标记，输出可读权限摘要 | io/fs |
## 配置与命令行

| ID | Topic | Observable behavior | Standard library |
|---|---|---|---|
| T191 | 独立 FlagSet 子命令 | 解析 import/export 两个子命令，错误返回到缓冲而不退出进程 | flag, bytes |
| T192 | 环境键值快照 | 从给定环境切片读取配置，处理重复键、坏整数与默认值 | strings, strconv |
| T193 | 多来源配置优先级 | 按默认、文件、环境、命令行顺序覆盖，并输出最终来源记录 | encoding/json |
| T194 | 受控变量展开 | 用映射函数展开模板变量，区分缺失键、转义美元符和普通文字 | os, strings |
| T195 | INI 分节解析 | 解析分节键值，处理注释、空行、重复键及行号错误 | bufio, strings |
| T196 | 配置交叉字段校验 | 聚合端口、超时和 TLS 路径间的约束错误，一次返回全部问题 | fmt, strings |
| T197 | 表格对齐输出 | 用 TabWriter 输出含不同长度字段的表格，核对列对齐与 Flush | text/tabwriter, bytes |
| T198 | 简单参数词法分析 | 解析带引号和转义的参数列表，仅构造参数数组而不调用 shell | unicode |
| T199 | ANSI 控制序列清理 | 用状态机删除 SGR 颜色序列，保留普通方括号文本与中文 | strings |
| T200 | 配置补丁与未知键 | 将白名单 JSON patch 应用到现有配置，拒绝未知键且保证失败无修改 | encoding/json, sort |
## 摘要与密码基础

| ID | Topic | Observable behavior | Standard library |
|---|---|---|---|
| T201 | 摘要清单验证 | 验证两个离线文件的摘要清单，分别报告匹配和被修改文件 | crypto/sha256, encoding/hex |
| T202 | HMAC 消息认证 | 为消息生成标签，验证正确消息并拒绝修改后的内容 | crypto/hmac, crypto/sha256 |
| T203 | 定长令牌比较 | 先校验长度再比较固定字节令牌，展示错误输入和有效输入 | crypto/subtle |
| T204 | AES GCM 往返和篡改 | 每次生成新 nonce，往返验证消息并确认篡改密文会认证失败 | crypto/aes, crypto/cipher, crypto/rand |
| T205 | Ed25519 签名校验 | 生成临时密钥，签名本地清单并验证原文与篡改文 | crypto/ed25519, crypto/rand |
| T206 | ECDSA 摘要签名 | 对 SHA256 摘要进行 ASN1 签名与验证，拒绝另一摘要 | crypto/ecdsa, crypto/elliptic, crypto/rand |
| T207 | 密钥协商一致性 | 两方生成临时 P256 密钥，独立推导共享秘密并比较一致性 | crypto/ecdh, crypto/rand, bytes |
| T208 | 公钥 PEM 往返 | 编码和读取公钥 PEM，检查块类型并验证恢复后的公钥 | crypto/ed25519, crypto/x509, encoding/pem |
| T209 | CRC32 分片校验 | 分片更新校验和并与一次性校验对比，演示一个字节变化的检测 | hash/crc32 |
| T210 | 流式多摘要 | 用 MultiWriter 一次消费输入同时计算两类摘要并验证长度与一致性 | hash, crypto/sha256, crypto/sha512, io |
## 压缩与封装

| ID | Topic | Observable behavior | Standard library |
|---|---|---|---|
| T211 | Gzip 日志封装 | 压缩多行日志并解压，检查关闭写入器后的完整尾部与内容 | compress/gzip, bytes, io |
| T212 | Zlib 解压预算 | 对压缩输入限制解压后字节数，拒绝超预算载荷 | compress/zlib, io |
| T213 | Tar 选择性提取 | 遍历内存归档，只读取目标文档并核对条目类型和长度 | archive/tar, bytes, io |
| T214 | Zip 报表归档 | 创建含两个报表的 zip，读取所有条目并稳定输出摘要 | archive/zip, bytes, io |
| T215 | 归档路径验证 | 在提取前验证条目路径，拒绝越界、绝对路径与符号链接 | archive/zip, path, strings |
| T216 | Tar 元数据清单 | 从归档头读取权限和大小，跳过目录内容并生成稳定清单 | archive/tar, sort |
| T217 | 内存 Multipart 表单 | 构造含文本与文件的表单，逐 part 解码并核对文件内容 | mime/multipart, bytes, io |
| T218 | MIME 媒体类型参数 | 解析带引号参数和字符集的媒体类型，规范重组并处理非法输入 | mime |
| T219 | 流式 Base64 编解码 | 跨多次 Write 编码并关闭刷新尾块，再以 Reader 解码 | encoding/base64, io, bytes |
| T220 | Quoted Printable 文本 | 解码软换行和转义字节，再编码 UTF-8 邮件片段并验证往返 | mime/quotedprintable, io, strings |
## 本地 HTTP 与 URL

| ID | Topic | Observable behavior | Standard library |
|---|---|---|---|
| T221 | 内存路由与方法约束 | 直接对 Handler 发送本地请求，区分合法 GET、404 和 405 | net/http, net/http/httptest |
| T222 | 严格 JSON POST | 验证请求媒体类型、未知字段和响应状态，完全使用内存 Recorder | net/http, net/http/httptest, encoding/json |
| T223 | 请求标识中间件 | 从请求头取 ID 或确定性创建 ID，传入 context 并回写响应头 | net/http, net/http/httptest |
| T224 | 条件请求 ETag | 生成资源 ETag，验证匹配返回 304 且不写响应体 | net/http, net/http/httptest, crypto/sha256 |
| T225 | 字节范围响应 | 用 ServeContent 响应一个单范围请求，检查 206、Content-Range 与载荷 | net/http, net/http/httptest, strings |
| T226 | 内容协商权重 | 解析 Accept 的 q 参数，选择可提供格式并处理 q=0 | mime, strconv, sort |
| T227 | Cookie 属性往返 | 设置 HttpOnly、SameSite Cookie，再构造请求读回值 | net/http, net/http/httptest |
| T228 | 查询参数规范化 | 按允许键筛选查询参数，保留重复值并生成稳定查询串 | net/url, sort |
| T229 | 相对 URL 解析 | 以目录 URL 为基准解析相对链接，比较路径、查询和片段变化 | net/url |
| T230 | HTTP 响应报文读取 | 读取内存 chunked 响应，验证解码正文与 trailer 字段 | net/http, bufio, strings |
## 并发与所有权

| ID | Topic | Observable behavior | Standard library |
|---|---|---|---|
| T231 | 有序并行转换 | 多个 worker 处理索引化任务，收集后按输入顺序输出结果 | sync, sort |
| T232 | 有界并发闸门 | 用缓冲通道限制并发，验证所有任务完成且峰值不超过上限 | sync, sync/atomic |
| T233 | 同键请求合并 | 在自实现调用表中合并并发相同键请求，断言实际装载仅一次 | sync |
| T234 | 条件变量屏障 | 用 Cond 等待所有成员就绪，再广播启动并收集确定结果 | sync |
| T235 | 流水线取消传播 | 达到固定消费数量时取消上游，等待所有阶段退出并打印已消费值 | context, sync |
| T236 | 只读快照发布 | 发布不可变配置快照，多个读者始终看到一个完整版本 | sync/atomic |
| T237 | 扇入关闭协调 | 合并两个生产者输出，唯一收尾方在 Wait 后关闭结果通道 | sync, sort |
| T238 | 任务结果与错误聚合 | 并行校验记录，按输入序号汇总成功结果和全部错误 | sync, errors, sort |
| T239 | 请求响应通道 | 用每请求独立响应通道实现本地 actor，验证状态更新和取消请求 | context |
| T240 | 一次性初始化结果 | 用 Once 共享可失败初始化结果，验证多次调用不会重复初始化 | sync |
## 模板与展示协议

| ID | Topic | Observable behavior | Standard library |
|---|---|---|---|
| T241 | 模板金额辅助函数 | 注册分币格式化 FuncMap，渲染订单明细与总价 | text/template, bytes |
| T242 | HTML 自动转义 | 渲染含标签的用户输入，验证正文与属性上下文的自动转义 | html/template, bytes |
| T243 | 模板块复用 | 定义并复用页头和行模板，以不同数据生成两份报告 | text/template, bytes |
| T244 | 模板缺失键策略 | 设置 missingkey=error，比较完整记录与缺字段记录的执行结果 | text/template, bytes |
| T245 | 自定义 JSON 脱敏视图 | 用 MarshalJSON 输出遮盖后的账号视图，同时保留内存原值 | encoding/json |
| T246 | 枚举文本协议 | 为状态枚举实现 TextMarshaler/TextUnmarshaler，验证合法与非法值 | encoding, encoding/json |
| T247 | 固定列宽 Unicode 表格 | 按 rune 个数截断并填充离线摘要表，明确 rune 数并非显示宽度 | unicode/utf8, strings |
| T248 | JSON Lines 报表 | 逐行编码和解码不同记录，报告损坏行而继续处理后续行 | encoding/json, bytes |
| T249 | Markdown 表格转义 | 为含管道符、反斜线和换行的字段生成合法 Markdown 表格 | strings |
| T250 | 进度条纯函数 | 将已完成量和总量转换为固定宽度进度条，处理越界与零总量 | strings, strconv |
## 校验与状态机

| ID | Topic | Observable behavior | Standard library |
|---|---|---|---|
| T251 | 邮件地址解析 | 解析显示名和邮箱，保留规范地址并拒绝不完整输入 | net/mail |
| T252 | IP 与网段归属 | 解析 IPv4/IPv6 地址与 CIDR，验证边界和非法字符串 | net |
| T253 | 离线 URL 白名单 | 拒绝非 https、用户信息及非允许主机，避免主机后缀误判 | net/url, strings |
| T254 | 主机名词法校验 | 仅校验 ASCII 主机标签长度、连字符位置与字符集，不做 DNS 查询 | strings, unicode |
| T255 | 语义版本排序 | 比较主次补丁与预发布标识，稳定排序并拒绝坏版本 | strconv, strings, sort |
| T256 | Luhn 校验与生成 | 计算数字串校验位，验证合法号码并拒绝单字节改动 | unicode |
| T257 | ISBN13 校验 | 忽略显示分隔符计算 ISBN13 加权校验，识别长度和校验错误 | unicode |
| T258 | 带转义字段状态机 | 解析用分号分隔且支持反斜线转义的记录，检测悬空转义 | strings |
| T259 | 括号配对与错误位置 | 用栈检查多类括号嵌套，并返回首个错误字节位置 | fmt |
| T260 | 分片 UTF8 解码 | 接收在中文字符中间切分的字节块，保留未完成字节并拒绝非法序列 | unicode/utf8, bytes |
## 二进制协议与位图

| ID | Topic | Observable behavior | Standard library |
|---|---|---|---|
| T261 | 带 CRC 的二进制帧 | 组装版本、长度、载荷与校验码，拒绝坏版本和篡改帧 | encoding/binary, hash/crc32 |
| T262 | 传感器位字段 | 从 uint16 帧提取标志、量程和数值，并验证重新打包一致 | encoding/binary |
| T263 | 差分 Varint 压缩 | 对递增事件 ID 存储差分，逐项解码还原并处理截断 | encoding/binary |
| T264 | Netstring 消息解析 | 解析 length:data, 格式的连续消息，验证长度与结尾逗号 | strconv, strings |
| T265 | DNS 标签编码 | 将域名编码为标签长度序列，仅做离线格式处理并拒绝超长标签 | bytes, strings |
| T266 | 分片帧解包器 | 把随机切分的长度帧喂给解包器，缓存半帧并输出多帧 | encoding/binary, bytes |
| T267 | 位图空闲槽分配 | 用 uint64 位图申请、释放资源槽，检测用尽并重用空槽 | math/bits |
| T268 | 位集合交并差 | 以位集合表达权限，计算交并差并列出最终授权项 | math/bits |
| T269 | IEEE754 字节往返 | 以固定字节序编码浮点数，验证普通值和负零的位模式 | math, encoding/binary |
| T270 | 有符号 ZigZag 编码 | 将正负小整数映射无符号 varint，验证边界值往返 | encoding/binary |
## 综合离线应用

| ID | Topic | Observable behavior | Standard library |
|---|---|---|---|
| T271 | 账本对账器 | 按交易 ID 对比两份账本，输出缺失、重复与金额不一致记录 | encoding/csv, sort |
| T272 | 依赖构建顺序 | 用拓扑排序与字典序队列生成稳定构建计划，并报告剩余环节点 | container/heap |
| T273 | 会议室分配 | 按结束时间复用会议室，输出每个预约的房间和最少房间数 | container/heap, sort |
| T274 | 包清单完整性检查 | 读取包文件清单并校验文件存在、长度和摘要，聚合全部错误 | encoding/json, crypto/sha256 |
| T275 | 本地记录查询器 | 实现过滤、分组与排序的查询步骤，对订单输出部门统计 | sort, strings |
| T276 | 事件溯源余额 | 依序重放开户、入账、扣款事件，拒绝非法事件且保留此前状态 | encoding/json |
| T277 | 内存事务回滚 | 在副本上执行多步库存变更，遇到负库存回滚全部操作 | fmt |
| T278 | 逻辑时钟令牌桶 | 用显式 now 更新令牌余额，验证突发、补充与拒绝而不实际睡眠 | time, math |
| T279 | 批处理检查点恢复 | 按批保存已完成偏移，模拟失败后从检查点恢复且避免重复提交 | encoding/json |
| T280 | 中缀表达式计算器 | 用操作符栈处理括号与优先级，报告除零及不完整表达式 | strconv, unicode |
