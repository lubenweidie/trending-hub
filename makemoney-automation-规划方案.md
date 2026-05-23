# makemoney-automation · 三轨自动化创收系统

> 规划方案 v1 | 2026-05-22 | 自动模式生成

---

## 背景与目标 [DW-01]

### 你在哪里

一个会写 Python/JS 脚本的独立开发者，每天有 1-2 小时业余时间，想做能真正产生收入的自动化项目。没有完整产品开发经验，不想碰加密货币，希望第一个项目就能看到回报。

### 要去哪里

搭建 **3 条独立但互补的自动化收入轨道**，覆盖短期（1-2周见效）、中期（2-3月见效）、长期（6-12月见效）三个时间维度。搭建完成后每周维护不超过 2 小时，月运营成本控制在 ¥200 以内。

| 轨道 | 类型 | 变现方式 | 见效时间 | 自动化程度 |
|------|------|----------|----------|-----------|
| 🚀 轨道1 | Coze AI 模板 | 闲鱼销售模板+定制接单 | 1-2 周 | 85%（接单需人工沟通） |
| 📰 轨道2 | 内容自动化管线 | 广告+联盟佣金 | 2-3 月 | 95%（全自动采集→生成→发布） |
| 🔧 轨道3 | 在线工具站 | Google AdSense 广告 | 6-12 月 | 98%（纯静态，零维护） |

### 为什么不做一个大的

三条轨道的风险互相独立。闲鱼挂掉不影响工具站流量，工具站 SEO 没起来不影响内容管线收入。而且轨道1给你快速正反馈，支撑你坚持到轨道2和轨道3开花结果。

---

## 成功标准 [DW-02]

| 编号 | 标准 | 量化指标 | 数据来源 |
|------|------|----------|----------|
| SC-01 | 闲鱼首次上架 | 2周内上架首个Coze模板 | 时间约束直接来自用户需求 |
| SC-02 | 闲鱼首月收入 | 30天内 ≥ ¥500（约2-3单定制） | [实操案例：18天8400元、30天2.1万元](https://mp.weixin.qq.com/s?__biz=MzE5MTU1MzAxMw==&mid=2247483759&idx=1&sn=5cda2c417f1382b35366edc316728118)，保守取下限 |
| SC-03 | 闲鱼3月累计 | 3个月累计 ≥ ¥3000 | 同上，取保守估计 |
| SC-04 | 内容管线搭建 | 2月内完成采集→AI→发布全管线 | 参考 solo dev 标准：管线 MVP 2-4周，留1倍buffer |
| SC-05 | 内容站6月广告收入 | 月收入 ≥ ¥500 | [AdSense RPM 基准：内容类 $2-5](https://adrevhub.com/rpm-calculator/) |
| SC-06 | 工具站上线 | 1月内上线 ≥ 5 个工具 | 单个工具 4-8 小时，5个 = 20-40小时，4周可完成 |
| SC-07 | 工具站12月广告收入 | 月收入 ≥ ¥1000 | [工具类 RPM $5-12](https://adrevhub.com/rpm-calculator/) |
| SC-08 | 全局自动化 | 搭建后每周维护 ≤ 2 小时 | 用户约束 |

---

## 轨道1：Coze AI 模板 · 闲鱼变现 [DS-01]

### 做什么

在字节跳动旗下的 Coze（扣子）平台，用可视化拖拽搭建 3-5 个实用 AI 智能体。将智能体打包为「模板」在闲鱼上架销售（¥99-399/份），同时接定制单（¥200-900/单）。

### 为什么选这个

- **零成本**：Coze 免费使用，闲鱼发布免费
- **快见效**：搭建一个智能体只需 2-4 小时，当天可上架
- **验证过**：2025年多个案例证实可行（18天8400元、30天2.1万元）
- **信息差**：大量个人和商家有 AI 需求但不会/不想自己搭

### 选哪 5 个方向

根据闲鱼当前热门品类和你的技术特点：

| 序号 | 智能体 | 目标用户 | 卖点 | 搭建时间 |
|------|--------|----------|------|----------|
| 1 | **简历优化助手** | 求职者 | 上传简历→AI分析→输出优化版，一键排版 | 3h |
| 2 | **日报/周报生成器** | 职场人 | 输入关键词→自动生成结构化汇报 | 2h |
| 3 | **竞品监控器** | 电商卖家 | 输入竞品链接→自动采集价格/评价/活动 | 4h |
| 4 | **合同风险扫描** | 小企业主/自由职业者 | 上传合同→AI识别风险条款→给出修改建议 | 4h |
| 5 | **客服话术库** | 淘宝/拼多多客服 | 按场景分类→一键生成回复话术 | 2h |

### 怎么搭建（以「简历优化助手」为例）

```
Step 1: 登录 coze.cn → 创建 Bot → 选择「工作流」模式
Step 2: 添加「文件上传」节点 → 支持 PDF/Word/图片
Step 3: 添加「大模型」节点 → 编写 Prompt（见下方）
Step 4: 添加「文本处理」节点 → 格式化输出
Step 5: 测试 → 发布 → 选择「私有配置」（隐藏 Prompt）
```

**核心 Prompt 模板**：
```
你是一位资深HR和简历优化专家。请分析以下简历：
1. 识别 3 个最大的问题（结构/用词/成果量化）
2. 针对每个问题给出修改前后对比
3. 输出一份优化后的完整简历
4. 评分（1-10分）并说明改进空间

输出格式：Markdown，分区块展示。
```

### 怎么在闲鱼卖

**商品文案模板**：
```
标题：【AI简历优化】专业简历优化助手 | 一键分析+改写+评分 | 面试邀约率翻倍

正文：
💼 别再海投简历石沉大海了！
这个AI简历助手由专业HR Prompt驱动，能：
✅ 3秒诊断简历核心问题
✅ 逐条给出修改前后对比
✅ 自动输出优化版完整简历
✅ 综合评分+改进方向

📦 拍下即发Coze模板链接，导入即用
💰 模板版 ¥99（自助使用）
🛠️ 定制版 ¥299（我帮你优化到满意为止）

#简历优化 #求职 #AI工具 #面试
```

**定价策略**：
- 模板版 ¥99（自助导入使用）
- SOP文档版 ¥199（含搭建教程+Prompt源码）
- 定制版 ¥299-599（帮客户优化到满意）

**运营节奏**：
- 每天花 10 分钟回复闲鱼消息（可以用快捷回复模板）
- 每周花 20 分钟优化商品标题/标签/图片
- 定制单接到后，实际用 AI 辅助完成（20-40分钟/单）

### 轨道1 时间线

| 周次 | 任务 | 产出 |
|------|------|------|
| 第1周 | 搭建「简历优化」+「日报生成」+ 上架闲鱼 | 2个模板在线 |
| 第2周 | 搭建「竞品监控」+「合同风险」+「客服话术」+ 优化前2个 | 5个模板在线 |
| 第3-4周 | 运营优化：回复咨询、优化文案、观察数据 | 首月收入目标 ¥500 |

---

## 轨道2：内容自动化管线 [DS-02]

### 做什么

一条 Python 脚本管线，自动完成：**采集热榜数据 → AI 摘要+改写 → 生成 HTML 静态页 → 部署到 Cloudflare Pages → 同步分发到掘金/知乎**。通过 Google AdSense 广告和联盟佣金变现。

### 技术架构

```
┌─────────────────────────────────────────────────────┐
│                  GitHub Actions                       │
│  cron: 每4小时触发（北京时间 8/12/16/20/24点）        │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              数据采集层 (collectors/)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐              │
│  │ 微博热搜  │ │ 知乎热榜  │ │ 百度热搜  │  ... 更多   │
│  │ weibo.py │ │ zhihu.py │ │ baidu.py  │              │
│  └──────────┘ └──────────┘ └──────────┘              │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              AI处理层 (processor.py)                   │
│  去重 → 筛选（过滤娱乐八卦）→ AI摘要 → AI改写          │
│  模型: 智谱GLM-4.6 或 DeepSeek API                   │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              输出层 (output/)                         │
│  ┌──────────────────┐  ┌──────────────────┐          │
│  │ index.html        │  │ posts/*.html      │          │
│  │ (首页·最新热榜)   │  │ (详情页·单条聚合) │          │
│  └──────────────────┘  └──────────────────┘          │
│  ┌──────────────────┐  ┌──────────────────┐          │
│  │ sitemap.xml       │  │ feed.json         │          │
│  └──────────────────┘  └──────────────────┘          │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│           Cloudflare Pages (自动部署)                  │
│  GitHub Push → Cloudflare 自动构建 → 全球CDN          │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│          分发层 (可选·手动触发)                        │
│  掘金 / 知乎专栏 → 引流回主站                         │
└─────────────────────────────────────────────────────┘
```

### 数据源选择

| 平台 | 采集方式 | 难度 | 数据特点 |
|------|----------|------|----------|
| 微博热搜 | `requests` 直接请求 API | ⭐ | 娱乐八卦多，需关键词过滤 |
| 知乎热榜 | `requests` 抓取 JSON | ⭐ | 内容质量高，适合技术号 |
| 百度热搜 | `requests` 抓取页面 | ⭐ | 覆盖面广，大众化 |
| B站热门 | `requests` 请求 API | ⭐ | 视频趋势，可做视频推荐 |
| 掘金热榜 | `requests` 抓取 | ⭐ | 程序员向，技术类内容 |
| V2EX 最热 | `requests` 抓取 | ⭐ | 互联网/科技讨论 |

**全部使用 `requests` + API/JSON 接口**，不引入 Selenium/Playwright，保持轻量。

### AI 处理 Pipeline

```
热搜条目（原始）
    │
    ▼
去重：标题相似度 > 0.8 的合并
    │
    ▼
过滤：排除娱乐八卦类（关键词黑名单：明星/综艺/出轨/绯闻...）
    │
    ▼
摘要：AI 用 2-3 句话概括事件
    │
    ▼
改写：AI 从不同角度改写（技术解读/商业分析/社会观察）
    │
    ▼
排版：生成 HTML，含标题+摘要+来源链接+改写分析
```

**关键词过滤黑名单**（frequency_words.txt）：
```
明星 综艺 出轨 绯闻 恋情 八卦 选秀 偶像 饭圈 塌房
真人秀 炒作 爆料 出轨门 婚变 CP 发糖
```

### GitHub Actions 配置

```yaml
# .github/workflows/trending.yml
name: Trending Content Pipeline

on:
  schedule:
    - cron: '0 0,4,8,12,16 * * *'  # 每4小时（UTC），北京 +8
  workflow_dispatch:  # 手动触发

jobs:
  pipeline:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install deps
        run: pip install requests beautifulsoup4 httpx
      - name: Collect trends
        run: python collectors/run_all.py
      - name: AI Process
        run: python processor.py
        env:
          AI_API_KEY: ${{ secrets.AI_API_KEY }}
          AI_API_URL: ${{ secrets.AI_API_URL }}
      - name: Build HTML
        run: python builder.py
      - name: Commit & Push
        run: |
          git config user.name "TrendBot"
          git config user.email "bot@trends.local"
          git add output/
          git diff --staged --quiet || (git commit -m "Update: $(date +'%Y-%m-%d %H:%M')" && git push)
```

### 静态站结构

```
output/
├── index.html          # 首页：最新热榜聚合，每平台Top10
├── posts/
│   ├── 2026-05-22-1.html  # 详情页：单条热搜的完整分析
│   └── ...
├── archive.html        # 历史归档
├── sitemap.xml         # SEO 站点地图
├── ads.txt             # AdSense 授权文件
├── robots.txt
└── static/
    ├── style.css
    └── script.js
```

### AdSense 广告位布局

每页嵌入 3 个广告位：
- **顶部横幅**（标题下方，728×90）
- **内容中**（文章中间，336×280 矩形）
- **底部**（相关推荐下方，728×90）

### 轨道2 时间线

| 周次 | 任务 | 产出 |
|------|------|------|
| 第1周 | 搭建单个采集器（微博）+ AI处理 + HTML生成 | MVP管线跑通 |
| 第2周 | 接入全部6个数据源 + 关键词过滤 + 去重 | 完整数据管线 |
| 第3周 | 优化HTML模板 + SEO（sitemap、meta、结构化数据） | 可发布的静态站 |
| 第4周 | 部署Cloudflare Pages + 申请AdSense + 配置GitHub Actions | 全自动运行 |
| 第5-8周 | 持续优化内容质量、SEO、广告位 | 等待AdSense审核通过 |

---

## 轨道3：在线工具站 [DS-03]

### 做什么

一个纯前端的在线工具集合站，所有计算/处理在浏览器端完成（隐私卖点）。通过 SEO 长尾关键词获取流量，Google AdSense 变现。

### 选哪 8 个工具

按优先级排序（⭐ = 搜索量大，竞争低）：

| 序号 | 工具 | SEO关键词（月搜索量）| 开发时间 | 优先级 |
|------|------|---------------------|----------|--------|
| 1 | **JSON格式化/验证** | json formatter, json validator | 3h | ⭐⭐⭐ |
| 2 | **时间戳转换** | timestamp converter, unix timestamp | 2h | ⭐⭐⭐ |
| 3 | **Base64编解码** | base64 encode decode online | 2h | ⭐⭐⭐ |
| 4 | **图片压缩** | compress image online, reduce image size | 6h | ⭐⭐ |
| 5 | **URL编解码** | url encoder decoder | 1.5h | ⭐⭐ |
| 6 | **MD5/SHA哈希** | md5 generator, sha256 online | 2h | ⭐⭐ |
| 7 | **正则测试器** | regex tester online | 3h | ⭐ |
| 8 | **颜色转换** | hex to rgb, color converter | 2h | ⭐ |

### 核心卖点

> 🔒 **一切在浏览器中完成，文件不上传服务器。**
> 
> 这是区别于 Smallpdf/ILovePDF 等竞品的关键差异。隐私是 SEO 文章的核心论证点。

### 技术栈（极简）

```
工具站/
├── index.html           # 首页·工具导航
├── tools/
│   ├── json-formatter.html
│   ├── timestamp.html
│   ├── base64.html
│   ├── image-compress.html
│   ├── url-encode.html
│   ├── md5-hash.html
│   ├── regex-tester.html
│   └── color-convert.html
├── static/
│   ├── style.css         # Tailwind CSS CDN + 自定义
│   └── script.js         # 公共函数
├── sitemap.xml
├── ads.txt
├── robots.txt
└── _headers              # Cloudflare Pages 安全头
```

**不用框架**。每个工具是一个独立 HTML 文件，引入 Tailwind CSS CDN 即可。工具之间通过首页导航链接。

### 单工具模板

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JSON格式化 - 在线JSON格式化验证工具 | 浏览器端处理</title>
    <meta name="description" content="免费的在线JSON格式化工具，所有处理在浏览器端完成，数据不会上传到服务器。支持JSON格式化、压缩、验证。">
    <link rel="canonical" href="https://你的域名/tools/json-formatter.html">
    <script src="https://cdn.tailwindcss.com"></script>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-你的ID" crossorigin="anonymous"></script>
    <!-- JSON-LD 结构化数据 -->
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "WebApplication",
      "name": "JSON格式化工具",
      "url": "https://你的域名/tools/json-formatter.html",
      "description": "浏览器端JSON格式化工具，保护数据隐私",
      "applicationCategory": "UtilityApplication",
      "operatingSystem": "Any"
    }
    </script>
</head>
<body class="bg-gray-50 min-h-screen">
    <!-- 导航栏 -->
    <nav class="bg-white shadow-sm">...</nav>
    
    <!-- AdSense 顶部广告 -->
    <div class="max-w-4xl mx-auto px-4 pt-4">
        <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-你的ID" 
             data-ad-slot="123456" data-ad-format="auto" data-full-width-responsive="true"></ins>
        <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
    </div>
    
    <!-- 工具主体 -->
    <main class="max-w-4xl mx-auto px-4 py-8">
        <h1 class="text-3xl font-bold mb-2">JSON格式化工具</h1>
        <p class="text-gray-500 mb-6">所有处理在浏览器端完成，数据不会上传到服务器 🔒</p>
        
        <textarea id="input" class="w-full h-48 p-4 border rounded" placeholder="粘贴JSON..."></textarea>
        <div class="flex gap-2 my-4">
            <button onclick="format()" class="bg-blue-600 text-white px-4 py-2 rounded">格式化</button>
            <button onclick="compress()" class="bg-gray-600 text-white px-4 py-2 rounded">压缩</button>
            <button onclick="validate()" class="bg-green-600 text-white px-4 py-2 rounded">验证</button>
        </div>
        <pre id="output" class="bg-gray-100 p-4 rounded overflow-auto"></pre>
    </main>
    
    <!-- AdSense 底部广告 -->
    ...
    
    <script>
        function format() {
            try {
                const obj = JSON.parse(document.getElementById('input').value);
                document.getElementById('output').textContent = JSON.stringify(obj, null, 2);
            } catch(e) {
                document.getElementById('output').textContent = 'JSON 格式错误: ' + e.message;
            }
        }
        // ...更多函数
    </script>
</body>
</html>
```

### SEO 策略

**每个工具页面的 SEO 要素**：
1. **Title**: `{功能名} - 在线{中文描述}工具 | 浏览器端处理` — 含主关键词
2. **Meta Description**: 150字以内，含核心卖点（隐私）+ CTA
3. **H1**: 主关键词（如"JSON格式化工具"）
4. **Canonical URL**: 避免重复内容惩罚
5. **JSON-LD**: WebApplication 结构化数据
6. **Sitemap**: 所有工具页 + 首页 + 分类页

**关键 SEO 操作**：
- 在 Cloudflare 设置 `www → 非www` 301 重定向（Page Rules）
- 提交 sitemap 到 Google Search Console + 百度站长平台
- 每个工具页文本说明 ≥ 300 字（含"为什么选我们"、"常见问题"）

### 轨道3 时间线

| 周次 | 任务 | 产出 |
|------|------|------|
| 第1周 | 域名注册 + Cloudflare Pages 初始化 + 首页 | 基础设施就绪 |
| 第2周 | 完成前4个工具（JSON/时间戳/Base64/URL） | 4个工具上线 |
| 第3周 | 完成后4个工具（图片压缩/MD5/正则/颜色） + sitemap | 8个工具全部上线 |
| 第4周 | SEO优化 + Search Console提交 + AdSense申请 | 正式开始SEO积累 |
| 第5周起 | 等待SEO起量，每2周添加1个新工具 | 内容持续增长 |

---

## 项目目录结构 [DS-04]

```
makemoney/
├── .real-want-domains.json          # 领域进化数据
├── .real-want-preferences.json      # 用户偏好（后续自动生成）
├── makemoney-automation-prompt.json # 需求文档
├── makemoney-automation-规划方案.md  # 本文件
│
├── track1-coze/                     # 🚀 轨道1：Coze模板
│   ├── 闲鱼文案/
│   │   ├── 简历优化助手.md
│   │   ├── 日报生成器.md
│   │   ├── 竞品监控器.md
│   │   ├── 合同风险扫描.md
│   │   └── 客服话术库.md
│   ├── Prompt源码/
│   │   ├── 简历优化-prompt.txt
│   │   ├── 日报生成-prompt.txt
│   │   └── ...
│   └── SOP文档模板.md               # 高客单价文档模板
│
├── track2-content-pipeline/         # 📰 轨道2：内容管线
│   ├── collectors/
│   │   ├── run_all.py               # 主入口，协调所有采集器
│   │   ├── weibo.py                 # 微博热搜
│   │   ├── zhihu.py                 # 知乎热榜
│   │   ├── baidu.py                 # 百度热搜
│   │   ├── bilibili.py              # B站热门
│   │   ├── juejin.py                # 掘金热榜
│   │   └── v2ex.py                  # V2EX最热
│   ├── processor.py                 # AI处理：去重+过滤+摘要+改写
│   ├── builder.py                   # HTML生成器
│   ├── output/                      # 生成的静态站（被git追踪）
│   │   ├── index.html
│   │   ├── archive.html
│   │   ├── posts/
│   │   ├── sitemap.xml
│   │   ├── ads.txt
│   │   ├── robots.txt
│   │   └── static/
│   ├── frequency_words.txt          # 过滤关键词
│   ├── requirements.txt
│   └── .github/workflows/
│       └── trending.yml             # GitHub Actions 定时任务
│
├── track3-tools-site/               # 🔧 轨道3：在线工具站
│   ├── index.html                   # 首页·工具导航
│   ├── tools/
│   │   ├── json-formatter.html
│   │   ├── timestamp.html
│   │   ├── base64.html
│   │   ├── image-compress.html
│   │   ├── url-encode.html
│   │   ├── md5-hash.html
│   │   ├── regex-tester.html
│   │   └── color-convert.html
│   ├── static/
│   │   ├── style.css
│   │   └── script.js
│   ├── sitemap.xml
│   ├── ads.txt
│   ├── robots.txt
│   └── _headers                     # Cloudflare 安全头
│
└── dashboard/                       # 可选：数据看板
    └── stats.html                   # 统一的流量/收入看板（后期添加）
```

---

## 实现计划 [DS-05]

按天编排，每天 1-2 小时。三条轨道交错推进，优先保证轨道1快速出结果。

### 第1周：快速变现先跑通

| 天 | 轨道 | 任务 | 产出 |
|----|------|------|------|
| 1 | 🔧3 | 注册域名 + Cloudflare Pages 初始化 + GitHub 仓库 | 基础设施 |
| 2 | 🚀1 | Coze 搭建「简历优化助手」+ 写闲鱼文案 | 第1个模板 |
| 3 | 🚀1 | Coze 搭建「日报生成器」+ 上架闲鱼（2个商品） | 上架！ |
| 4 | 📰2 | 搭建微博采集器 → 测试跑通数据采集 | 第1个采集器 |
| 5 | 📰2 | AI 处理脚本（去重+过滤+摘要）+ 微博数据跑一遍 | 管线核心 |
| 6 | 🚀1 | 搭建「竞品监控器」+ 优化闲鱼商品标题/标签 | 第3个模板 |
| 7 | 🔧3 | 工具站首页 + JSON格式化工具 | 第1个工具 |

### 第2周：管线成型

| 天 | 轨道 | 任务 | 产出 |
|----|------|------|------|
| 8 | 📰2 | HTML 生成器（首页+详情页+归档）+ 样式 | 静态站成型 |
| 9 | 📰2 | 接入知乎 + 百度采集器 | 3个数据源 |
| 10 | 🚀1 | 搭建「合同风险」+「客服话术」+ 上架闲鱼 | 5个模板全部在线 |
| 11 | 🔧3 | 时间戳转换 + Base64编解码 + URL编解码 | 4个工具上线 |
| 12 | 📰2 | 接入B站 + 掘金 + V2EX采集器 | 6个数据源 |
| 13 | 📰2 | 配置 GitHub Actions + 测试自动运行 | 全自动管线 |
| 14 | 全局 | 复盘：轨道1收入数据、轨道2管线稳定性、轨道3进度 | 第2周总结 |

### 第3-4周：补齐与优化

| 天 | 轨道 | 任务 | 产出 |
|----|------|------|------|
| 15-16 | 🔧3 | 图片压缩 + MD5 + 正则 + 颜色转换 | 8个工具全部上线 |
| 17-18 | 📰2 | SEO优化（sitemap、meta、结构化数据、hreflang） | SEO就绪 |
| 19-20 | 🔧3 | 工具站 SEO + 提交 Search Console | 搜索引擎收录 |
| 21-22 | 📰2 | 部署 Cloudflare Pages + 域名绑定 + 301重定向 | 正式上线 |
| 23-24 | 🚀1 | 闲鱼运营优化 + 考虑上架 SOP 文档版 | 提升转化率 |
| 25-26 | 全局 | AdSense 申请 + ads.txt + 广告位嵌入 | 广告系统就绪 |
| 27-28 | 全局 | 整体测试 + Bug 修复 + 文档整理 | 搭建阶段收尾 |

### 第5周起：运维模式

- 🚀 轨道1：每天 10 分钟回闲鱼消息，每周 20 分钟优化文案
- 📰 轨道2：每周检查一次 GitHub Actions 运行日志，AI 输出质量抽查
- 🔧 轨道3：每 2 周添加 1 个新工具，监控 Search Console 数据
- 全局：每月初查看三条轨道的收入汇总

---

## 边界情况与异常处理 [DS-06]

### 轨道1：Coze/闲鱼

| 异常 | 处理 |
|------|------|
| Coze 平台政策变化（收费/限额） | 准备 Dify 作为备选平台（同样零代码）；Prompt 源码独立保存，可迁移 |
| 闲鱼商品被下架（违规判定） | 修改文案中可能触发审核的词（如"保证"、"100%"）；换号重发 |
| 定制单客户不满意 | 设置修改次数上限（2次免费修改）；退款底线（完成前可退50%） |
| 竞争加剧，销量下降 | 转向更细分的垂直领域（如"律师简历优化"而非通用简历）；SOP文档边际成本为零可降价 |
| Coze 服务宕机 | 不影响闲鱼销售（模板在客户自己空间运行）；定制单受影响需与客户沟通延迟 |

### 轨道2：内容管线

| 异常 | 处理 |
|------|------|
| 目标网站改版/反爬 | 每个采集器独立，单个失效不影响其他；GitHub Actions 失败时自动邮件通知 |
| AI API 调用失败（额度/限流） | 脚本内加重试逻辑（3次指数退避）；失败时用上一条缓存数据 |
| AI 生成内容质量差（事实错误） | 每条内容标注"AI生成，仅供参考"；来源链接保留，读者可核实原文 |
| GitHub Actions 执行超时（>6h） | 精简采集量（每平台Top20而非全部）；拆分工作流为并行job |
| Cloudflare Pages 部署失败 | GitHub Push 失败时 Actions 日志有明确错误；一般是 HTML 格式问题 |
| AdSense 审核不通过 | 先积累内容（≥30篇）+ 确保隐私页/关于页/联系页齐全；30天后重新申请 |
| 搜索流量不涨 | 检查 Search Console 是否有抓取错误；增加外链建设（掘金/知乎引流） |

### 轨道3：工具站

| 异常 | 处理 |
|------|------|
| 浏览器兼容性（Safari/iOS） | 每个工具上线前在 Chrome + Safari + 手机端各测一遍 |
| 大文件处理浏览器卡死 | 图片压缩设置文件大小上限（10MB）；大JSON用 Web Worker 后台处理 |
| AdSense 广告不展示 | 检查 ads.txt 是否在根目录、广告单元是否通过审核、是否有足够内容 |
| SEO 不收录/排名低 | 检查 robots.txt 未屏蔽、sitemap 已提交、页面加载速度（Cloudflare 已优化） |
| 某个工具没人用 | 保留（边际成本为零），但不再优化；新工具投入资源 |
| 域名被墙（国内访问不了） | 使用 .com 域名而非 .cn（免备案）；国内走 Cloudflare 中国网络 |

---

## 部署方案 [DS-07]

### 基础设施清单

| 资源 | 用途 | 成本 |
|------|------|------|
| 域名 ×1 | 工具站 + 内容站共用（子域名区分） | ¥50-80/年 |
| Cloudflare Pages ×2 | 工具站 + 内容站各一个项目 | 免费 |
| GitHub 仓库 ×1 | 代码托管 + Actions CI/CD | 免费 |
| Coze 账号 ×1 | 智能体搭建 | 免费 |
| 智谱/DeepSeek API | 内容管线 AI 处理 | ¥30-100/月 |
| 闲鱼账号 ×1 | 模板销售 | 免费 |

### 域名规划

```
主域名: example.com (或 example.net)
├── tools.example.com   → 轨道3：工具站
└── trends.example.com  → 轨道2：内容聚合站
```

### Cloudflare Pages 配置

**工具站**：
```
项目名: tools-site
构建命令: (无，纯静态)
输出目录: track3-tools-site/
分支: main
```

**内容聚合站**：
```
项目名: trends-site
构建命令: (无，纯静态，由 GitHub Actions 自动生成)
输出目录: track2-content-pipeline/output/
分支: main
```

**301 重定向**（Cloudflare Page Rules）：
```
www.tools.example.com/* → https://tools.example.com/$1 (301)
www.trends.example.com/* → https://trends.example.com/$1 (301)
```

### 成本核算

| 项目 | 月成本 |
|------|--------|
| 域名 | ¥5-7（年费分摊） |
| DeepSeek API | ¥30-50（假设日均处理200条热搜，每条约500 token） |
| Coze | ¥0 |
| Cloudflare Pages | ¥0 |
| GitHub | ¥0 |
| **合计** | **¥35-57/月** |

远低于 ¥200 预算上限。即使流量增长 10 倍，API 成本也仅增至 ¥300-500/月——届时广告收入已覆盖。

---

## 待定与风险 [DS-08]

### 待定问题

| 问题 | 影响 | 处理 |
|------|------|------|
| VPS可用性 | 中 | 无VPS则用GitHub Actions。如后续数据量大到Actions不够用（>2000分钟/月），再考虑买VPS（最低配¥50/月） |
| 工具站用户系统 | 低 | 初期不做。如后期有Pro版需求，用Firebase Auth（免费额度够用） |

### 风险矩阵

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| AdSense 审核不通过 | 中 | 高（轨道2+3收入归零） | 先堆内容质量，≥30篇原创再申请；备选国内广告联盟 |
| Coze 闲鱼市场饱和 | 中 | 中（轨道1收入下降） | 持续关注细分需求，转型SOP文档销售或企业定制 |
| AI 生成内容质量被Google降权 | 中 | 中 | 每条内容人工改标题+首段，保持"有人的味道" |
| 内容站被目标网站封IP | 低 | 低 | 多数据源冗余，单个被封不影响整体 |
| 域名被墙 | 低 | 高 | 使用海外域名+Cloudflare，不做敏感内容 |

---

## 评审策略 [RV-01]

- **评审模式**: parallel_merge
- **激活领域**: workflow, software
- **重点关注**:
  1. 三条轨道的实现细节是否足够具体可执行
  2. 成功标准的量化指标是否有来源支撑
  3. 异常处理是否覆盖了主要风险场景
  4. 时间线和资源估算是否合理
  5. 技术选型是否最轻量、最匹配用户技术栈
- **迭代次数上限**: 3
- **特别说明**: 本项目横跨「流程自动化」和「软件开发」两个领域，评审时请关注轨道间的协作和一致性，而非单独评审每条轨道。
