# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

采集多平台热榜 → 热点筛选（综合评分，按平台权重，每平台 N 篇）→ AI 摘要（仅对已选）→ AI 扩写 → 配图 → 多账号独立 Chrome session 并发发布（今日头条、百家号）。支持定时自动化运行。

> **涉及 opencli/bat/发布器/采集器 的修改，必须先加载 `/opencli-script` skill。**

## 项目结构

```
track2-content-pipeline/
  pipeline.py          ← 管线主入口（采集→过滤→选文→HTML→校验）
  publish.py           ← 一键发布（管线 + 多平台并发发布）
  quick_publish.py     ← 快捷发布（跳过采集，直接发布已有文章）
  article_utils.py     ← 跨层共享工具（parse_article）
  article_writer.py    ← 热点筛选 + AI摘要 + 去重
  builder.py           ← HTML 生成
  validate_output.py   ← HTML 校验
  config_loader.py     ← 配置加载（import 时自动执行）
  processor.py         ← AI 处理层（去重、摘要、预算控制）
  image_search.py      ← 多源图片搜索
  scripts/             ← bat 启动脚本（定时、发布、管理）
  config/              ← 配置文件（apikeys, schedule, accounts）
  services/            ← 辅助服务（通知、账号轮换、追踪、数据分析）
  collectors/          ← 热榜采集（5 个活跃：微博、知乎、百度、新华网、人民日报）
  publishers/          ← 发布器（头条、百家号）+ 提示词 + JS 工具
  output/articles/     ← 文章 + 归档
  logs/                ← 发布日志
```

## 核心文件

| 文件 | 作用 |
|------|------|
| `pipeline.py` | 管线主入口：采集→过滤→选文+摘要→HTML→校验（5步）。通过 `--article-limit`、`--target-platforms`、`--platform-account-counts` 命令行参数接收配置（环境变量兜底）。始终以子进程运行 |
| `publish.py` | 一键发布入口。`--publish` 发布，否则存草稿。模块级 `_publish_one()` 含重试+错误追踪→通知。`_finalize_publish_success()` 处理发布后操作（截图+Word+归档+追踪）。`TeeLogger` 双写控制台+日志 |
| `quick_publish.py` | 快捷发布 — 跳过采集，直接发布已有文章到指定平台。`-f` 指定文章，`--publish` 发布，`--dry-run` 预览 |
| `article_utils.py` | 跨层共享工具：`parse_article()` 解析 markdown、`archive_article()` 归档到 published/。不依赖 publishers/services/collectors |
| `article_writer.py` | 热点筛选（综合评分 + 平台权重修饰器）+ 每平台 N 篇加权随机不重复 + 选后批量 AI 摘要 + 去重 |
| `builder.py` | Jinja2 HTML 生成：渲染热榜聚合页 |
| `validate_output.py` | BeautifulSoup HTML 校验：检查 `<title>` 和 `<h1>` 标签 |
| `config_loader.py` | 从 `config/apikeys.conf` 加载配置到 `os.environ`。import 时自动执行 `load_config()`（`_CONFIG_LOADED` 标志保证幂等），环境变量优先级更高 |
| `processor.py` | AI 处理层：`filter_trends()` 去重、`summarize_batch()` 批量摘要、`check_budget()` 预算控制（¥150/月，¥120 告警）。`_is_ai_enabled()` 惰性检查 API Key（避免导入时副作用） |
| `image_search.py` | 多源图片搜索（百度中文标题 → 英文关键词兜底 Bing/Pexels/Pixabay/Unsplash） |
| `publishers/__init__.py` | 发布器注册中心：`REGISTRY` 字典映射平台名 → 发布器类，新增平台只需注册一行 |
| `publishers/base.py` | 发布器基类：opencli 封装、`_enrich_article()`（源提取+AI扩写+配图）、`prepare_editor()`（串行绑定 session→profile）、`publish()`（主流程骨架）、图文穿插、`stop_daemon()` |
| `publishers/toutiao.py` | 今日头条发布器（mp.toutiao.com）。按钮点击走 React fiber `_rc`。草稿验证自动保存后返回 True。发布模式 3 步按钮 → 后台验证 |
| `publishers/baijiahao.py` | 百家号发布器。封面弹窗多策略处理（`_rc` + `setTimeout click` + `force remove`）。发布后页面跳转确认 + 后台验证（3次重试，检测审核中状态） |
| `publishers/browser_utils.py` | 共享 JS：`REACT_CLICK_JS`（`_rc`）、`FIND_EL_JS`（`_f`）、`IMG_EXTRACT_JS` |
| `publishers/image_server.py` | 本地 HTTP 图片服务（端口 18900-18909），CORS 全开，用于绕过浏览器混合内容限制 |
| `publishers/prompts/` | AI 提示词：`title.txt`、`article.txt`、`__init__.py` 自动组装 `ENRICH_PROMPT` |
| `services/readback.py` | 回读分析：抓取后台文章数据，CSV 累计合并（仅统计已发布状态） |

## 常用命令

```bash
# 发布（管线 + 多平台）
python publish.py -p toutiao,baijiahao --publish     # 正式发布
python publish.py -p toutiao                          # 草稿模式（默认）

# 快捷发布（跳过采集）
python quick_publish.py toutiao                       # 发布最新文章到头条
python quick_publish.py toutiao -f output/articles/xxx/xxx.md  # 指定文章
python quick_publish.py toutiao,baijiahao --publish   # 多平台立即发布

# 单独跑管线（不发布）
python pipeline.py

# 测试
python -m pytest tests/ -v                            # 运行全部测试
python -m pytest tests/test_article_writer.py -v      # 单文件

# 回读数据分析
python services/readback.py -p toutiao,baijiahao      # 抓取全平台数据，保存 CSV
python services/readback.py -p toutiao -n 20           # 头条 TOP 20
python services/readback.py --no-save                  # 只看不存
```

**VSCode：** `Ctrl+Shift+B` 运行一键发布。

## 信息源（Collectors）

| 平台 | API/来源 | 备注 |
|------|----------|------|
| 微博 | `weibo.com/ajax/side/hotSearch` | |
| 知乎 | `zhihu.com/api/v3/feed/topstory/hot-lists/total` | 需 Cookie，opencli browser fetch 超时时返回空 |
| 百度 | `top.baidu.com/api/board?platform=wise&tab=realtime` | |
| 新华网 | `www.news.cn/` 首页 HTML，正则提取 `c.html` 链接 | |
| 人民日报 | `www.people.com.cn/` 首页 HTML | 须显式设 `resp.encoding = "utf-8"`，跳过 tv/ent/homea/leaders/www 域名 |

`collectors/run_all.py` 串行调用，单个失败不阻断。

## 热点筛选器（article_writer.py）

`_score_topic(topic, target_platform)` 综合评分，`target_platform` 为空时使用通用权重：

1. **话题类型权重** — 政策/民生（+8~12），奇闻趣事（+5~10），经济（+5~8），社会/科技（+5~6），娱乐八卦（+3~4），体育/游戏（+2~3）— 叠加 `PLATFORM_WEIGHT_MODIFIERS` 平台修饰器（乘法）
2. **标题吸引力** — 身份认同钩子 +8、含数字 +3、疑问句式 +3、利益/风险暗示 +5
3. **来源可信度** — 新华网/人民日报 +10，百度 +5，微博 +2，知乎 +1（头条对权威来源降权至 40%）
4. **低价值惩罚** — 仅针对特定模式（整容、医美翻车、网红塌房）-15

**平台权重修饰器**（`PLATFORM_WEIGHT_MODIFIERS`）：
- 百家号：政策/民生/经济 ×1.3~1.5，娱乐/奇闻 ×0.4~0.7
- 今日头条：娱乐/奇闻 ×1.8~2.5，政策/民生/经济 ×0.3~0.5

**流程**：先评分选文（仅用标题，无需 AI），再对已选条目批量调用 AI 摘要（节省 ~95% token）。分平台模式时每平台选 N 篇（N = 该平台账号数），加权随机无放回抽取。`PLATFORM_ACCOUNT_COUNTS` 环境变量控制每平台数量（如 `baijiahao:2,toutiao:1`）。

## 配置

### config/apikeys.conf（主配置）

关键配置项：
- `ARTICLE_LIMIT` — 仅 `python pipeline.py` 单独运行时生效；一键发布时被账号数覆盖
- `ARTICLES_PER_ACCOUNT` — 每账号每平台每天发几篇，默认 1（配合多次启动自然累加）
- `PUBLISH_MODE` — 1=存草稿，2=立即发布
- `DEEPSEEK_API_KEY` — AI 摘要 + 扩写
- `RETRY_COUNT` / `RETRY_DELAY` — 发布失败重试
- `MAX_CONCURRENCY` — 并发发布上限（控制同时打开的 Chrome 窗口数 + API 并发，推荐 3~8）
- `SMTP_*` — QQ 邮箱通知（端口 465 SSL）
- `NOTIFY_WEBHOOK` — Webhook 通知（可选）
- 图片搜索 Key（BING_API_KEY、PEXELS_API_KEY 等）— 按优先级自动降级

`config_loader.py` 在 import 时自动加载，环境变量优先级更高。

### config/schedule.conf（定时任务时间）

```
格式: HH:MM 延迟分钟
8:00 15    → 每天 8:00，随机延迟 0~15 分钟
```

第二列为空时默认延迟 15 分钟。

### config/accounts.json（多账号轮换）

```json
{"toutiao": [{"name": "账号1", "opencli_profile": "profile-id"}], "baijiahao": [...]}
```

### 账号模型

**1 套 profile = 1 个人 = 1 个手机号**。一个人同时在百家号和头条各注册一个号。

```text
accounts.json 示例（2个人、2平台 = 4个任务）:
  baijiahao: [写手A(profile-1), 写手B(profile-2)]
  toutiao:   [写手A(profile-1), 写手B(profile-2)]

profile-1 → 百家号(写手A) + 头条(写手A)
profile-2 → 百家号(写手B) + 头条(写手B)
```

- 同一 `opencli_profile` 值出现在多个平台表示该人在多个平台有号
- 发布时按 `opencli_profile` 排序，同 profile 多平台任务相邻，减少重复切 profile 次数
- Profile 缺平台只 warn 不拦截：`[Warn] profile 'xxx' 未覆盖: toutiao，跳过对应平台`

## 发布流程（publish.py）

### 高层流程

1. `TeeLogger` 双写控制台 + `logs/publish_{ts}.log`（保留最近 30 个）
2. `_main_impl` → 文章数 = 总账号数 × `ARTICLES_PER_ACCOUNT`，设置 `TARGET_PLATFORMS` + `PLATFORM_ACCOUNT_COUNTS`
3. 管线（`pipeline.py`）→ 分平台选文（每平台 N 篇，N = 该平台账号数）
4. `publish_to_platforms` → 串行准备 + 并发发布 + 成功后 `_finalize_publish_success()`（截图+Word+归档+追踪）
5. 多余文章 → `_剩余/`，通知 → `stop_daemon()`

### 并发模型：独立 Chrome session

**关键设计**：`opencli browser {session} {cmd}` 命令携带 session ID，`eval`/`click` 操作是 session 隔离的。只有 `opencli profile use` 是全局操作，影响 `open` 时绑定哪个 Chrome profile。

```
准备阶段（串行，绑定 session → profile）
  switch_profile(profile-1) → prepare_editor() → session_A 绑定 profile-1
  switch_profile(profile-2) → prepare_editor() → session_B 绑定 profile-2
  ...

并发阶段（无锁，session 隔离，MAX_CONCURRENCY 控上限）
  ThreadPoolExecutor:
    Thread-1: session_A → _enrich_article() → fill_title → fill_content → 插图 → 封面 → 发布
    Thread-2: session_B → （同上，不冲突）
```

- `prepare_editor(title)` → `ensure_daemon()` + `open_editor()` + `fill_title()` + 设 `_editor_opened` 标志
- `publish()` → `_editor_opened` 为 True 时跳过 `open_editor()`，先调 `_enrich_article()`（源提取+AI扩写+配图）。**注意：`extract_source_content()` 会导航到源页面，`publish()` 在 `_enrich_article()` 之后会 `open(self.edit_url)` 回到编辑器**，否则后续 fill/click 全在源页面上执行
- `fill_title()` 始终执行（AI 扩写可能改标题）
- 发布成功后 `_finalize_publish_success()` 处理截图、Word 导出、归档、追踪记录

### Profile 校验

每个 profile 按 `opencli_profile` 分组，检查覆盖的目标平台。缺平台只打 warn，不拦截：

```
profile-1: {baijiahao, toutiao} → 全覆盖，正常
profile-2: {baijiahao}          → [Warn] 缺 toutiao，只发百家号
```

### 头条发布（3 步按钮流程 — `_rc` 走 React fiber）

1. `_check_content_declaration()` 勾选「引用AI」等声明复选框（草稿+发布都执行）
2. 点击「预览并发布」→ 等待「确认发布」按钮出现
3. 有「预览并定时发布」时先点它 →「确认发布」出现
4. 点击「确认发布」→ `_verify_published()` 去后台列表搜标题验证
5. `_real_click()` 用 `SetProcessDpiAwareness(2)` + `SendInput`（绝对坐标 0-65535 虚拟屏幕），修复 DPI 缩放偏差
6. 封面面板检测：8 个备选选择器 × 20 次轮询（10s） + 自动重试
7. `fill_content` 返回 bool，找不到编辑器返回 False

### 百家号发布（封面弹窗 + 多策略点击）

1. 点击「发布」→ 可能出现封面预览弹窗（无封面图时）
2. 封面弹窗处理：`_rc` → 200ms 后 native `.click()` + `dispatchEvent` 双管齐下
3. 弹窗未消失时：关闭按钮 → 遍历确定/确认/完成按钮 → 最后 `cm.remove()` 强制移除
4. 封面关闭后自动重新点击发布
5. 发布确认：URL 跳转（`edit`→`clue`）即成功，否则 `_verify_published()` 后台验证（3 次重试）
6. `fill_content` 追加模式使用 `insertAdjacentHTML('beforeend', html)` 替代 `execCommand('insertText')`（Lexical 编辑器不会拦截 DOM API）
7. `fill_content` 返回 bool，用正则 `len:(\d+)` 提取长度判断

## 文章目录结构（硬规则）

```
output/articles/
  {时间戳}-{标题}/                      ← 每篇文章独立文件夹
    {时间戳}-{标题}.md                  ← 文章
    {时间戳}-{标题}.docx                ← Word 存档（发布后生成）
    {时间戳}-{标题}.source.txt          ← 源内容（发布后清理）
    cover.jpg / img_00.jpg / img_01.jpg ← 配图
  published/
    {时间戳}-{标题}-{发布平台}/          ← 归档（发布后整个文件夹移入）
  _剩余/                                ← 多余文章
```

- 目录名 `{ts}-{safe_title}`，`ts` = `YYYYMMDD_HHMM`，`safe_title` = 去非法字符截断至 30 字
- `find_recent_articles` 按 mtime 降序返回最近 N 篇

## 图片策略（硬规则）

**不从源页面抓图。用百度/Bing 关键词搜索。**

流程：中文标题搜百度 → 英文关键词（AI 生成 `image_keywords`）搜 Bing/Pexels 兜底。

上传（chunk + DataTransfer，绕开 HTTP 服务器）：
- **不复用 HTTP 图片服务器**。混合内容（HTTPS 页面 fetch HTTP）被 Chrome 阻止
- PIL 预处理：缩放至 max 1200px，JPEG quality 75
- 正文图：base64 → 分 chunk（≤4000 字符/个）→ `window._imgChunks` → JS 组装 → File → ClipboardEvent paste
- 封面图：base64 → chunk → JS 组装 → File → DataTransfer → 注入 file input → 触发 React fiber `onChange`/`onFileChange`
- **封面最小尺寸**：头条 ≥672×462（推荐），百家号 ≥452×352（最低）。PIL 处理时不足则放大
- 上传后等 CDN（头条检查 `toutiao.com` CDN URL，百家号检查 `.bjh-image-container` 内 `<img>` src）

## 提示词结构

```
publishers/prompts/
  __init__.py   ← 组装 ENRICH_PROMPT = article.txt + title.txt
  title.txt     ← 标题五大钩子（刺激+威胁+身份+数字+反常）+ 组合技
  article.txt   ← 文章规则（老百姓视角、5类内容切换、图文结构、禁用词、引用规则、平台差异、反AI检测策略）
```

### 标题五大钩子（title.txt）

| 钩子 | 原理 | 示例 |
|------|------|------|
| **刺激** | 好奇心缺口 — "有你不知道的秘密" | 「导演的福利 你想象不到」 |
| **威胁** | 损失厌恶 — "不做X就会吃Y亏" | 「不申请就再也领不到了」 |
| **身份** | "这是在说我" — 精准点名群体 | 「有房贷的注意」 |
| **数字** | 数字比形容词有力100倍 | 「每月多还800块」 |
| **反常** | 跟常识不一样，让人想反驳 | 「国台办发言人笑场」 |

组合技叠加效果翻倍：「银行员工透露 有房贷的人都在偷偷做这件事 晚一天多花几百」（刺激+威胁+身份+数字）。

严禁词：震惊、曝光、揭秘、内幕、竟然、居然、速看、刚刚、紧急通知、央视报道、人民日报说、感叹号结尾、纯陈述句。

### 内容类型分类（article.txt）

- **A类（政策民生）**：可操作步骤 + 来源引用 + 严肃通俗平衡 → 百家号主力
- **B类（经济商业）**：钱包关系 + 具体数字 + 干货话痨风格
- **C类（奇闻趣事）**：突出"奇"在哪 + 轻松幽默 + 不强求方法
- **D类（娱乐八卦）**：态度鲜明 + 网友评论 + 朋友聊八卦语气
- **E类（科技数码）**：大白话解释 + 使用建议 + 接地气科普
- A/B 类必须含可操作获利/避坑方法；C/D 类观点鲜明即可

**数据分析验证：**
- 百家号流量远大于头条，是主力平台
- 政策解读类在百家号表现最好（最高 1586 阅读）
- 奇闻趣事/娱乐八卦有稳定流量，适合内容矩阵多元化

## 依赖层级

从底层到上层，上层可依赖下层，反之不行：

```
article_utils.py          ← 零依赖，任何层可引用
config_loader.py          ← 仅依赖 os/pathlib
collectors/               ← 采集层，依赖 config
processor.py              ← AI 处理层
article_writer.py         ← 选文层，依赖 article_utils + processor
builder.py                ← HTML 生成层
publishers/browser_utils  ← JS 工具层
publishers/image_server   ← 图片服务层
publishers/base.py        ← 发布器基类（依赖 browser_utils + image_server）
publishers/toutiao|baijiahao ← 平台发布器（依赖 base）
pipeline.py               ← 管线编排（子进程运行）
publish.py                ← 顶层入口（调用 pipeline + publishers）
```

- `publishers/__init__.py` 定义 `REGISTRY` 为唯一入口，外部通过 `REGISTRY[name]` 获取发布器类
- `article_utils.py` 解决跨层引用（`article_writer` 和 `publish` 都需 `parse_article`，但不该互相依赖）
- `_is_ai_enabled()` 改为惰性函数调用，避免模块导入时 API Key 尚未加载

## 去重

`article_writer.py` 扫描 `published/` 下所有 `*/*.md`，提取源 URL，相同 URL 直接跳过。

## Services

| 服务 | 作用 |
|------|------|
| `services/notifier.py` | 发布结果 + SMTP 邮件通知 + Webhook 推送。`RunResult` 线程安全，汇总多账号并发结果（含失败原因）。`add_platform(name, title, ok, error="")` 支持失败详情 |
| `services/account_rotator.py` | 多账号管理：`get_all_accounts(plat)` 返回全账号、`switch_profile(acc)` 切换 opencli profile、`get_next_account(plat)` 轮换（旧接口保留） |
| `services/tracker.py` | 发布追踪：记录标题、平台、时间到 `output/articles/published/_track.json` |
| `services/readback.py` | 回读分析：打开后台 + 分页翻页 + 正则解析，CSV 累计合并（仅"已发布"状态）。平台注册表 `PLATFORMS` 可扩展 |

## 脚本（scripts/）

| 脚本 | 作用 |
|------|------|
| `一键发布.bat` | 启动 Chrome → `publish.py`。`SCHEDULED=1` 时 Chrome 最小化且不暂停 |
| `_随机延时.bat` | 随机延迟 0~N 分钟 → 调用 `一键发布.bat` |
| `管理定时任务.bat` | [1]同步(先清旧任务再建新任务) [2]查看(直查系统) [3]删除(查所有 `一键发布-*`) |

**bat 文件硬规则：必须 UTF-8 with BOM + CRLF 换行。** Edit/Write 后用 Python 验证 BOM 和 CRLF。

## 定时任务

Windows 任务计划程序 + `_随机延时.bat`。`管理定时任务.bat` 同步 `config/schedule.conf`（需管理员权限）。SYNC 先清后建保证系统任务与配置一致。

## 源内容提取

- 搜索/列表页（`s?word=`、`s?wd=`、`/weibo?`）**先判断再 open**，避免超时
- 搜索页直接返回空，让上层用 AI 摘要替代
- 源内容提取失败时，用 AI 摘要作为 fallback 进行扩写

## 调试 opencli

标准流程：
1. 写独立诊断脚本隔离失败步骤（每个步骤一个 eval，返回唯一标签）
2. 在失败点 dump DOM 状态（检查 `offsetParent`、modal 层级、元素可见性）
3. 每个 try/catch 加唯一错误标签
4. 最小化修改 + 单独验证

## 已知问题

- **`extract_source_content()` 导航后未回编辑器（已修复）** — `_enrich_article()` 会导航到源页面提取内容，`publish()` 在 `_enrich_article()` 之后执行 `open(self.edit_url)` 回到编辑器，否则后续 fill/click 全在源页面上操作（noel / no_content_el）
