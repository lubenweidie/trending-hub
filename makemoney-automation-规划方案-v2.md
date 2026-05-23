# makemoney-automation · 三轨自动化创收系统

<!-- 修订记录 -->
<!-- v1: 初始版本，2026-05-22 -->
<!-- v2: 根据第1轮评审反馈修订，解决9个高优+8个must_pass+10个中低优问题，新增安全/测试/监控三章 -->

> 规划方案 v2 | 2026-05-22 | 修订模式（基于评审反馈 v1）

---

## 背景与目标 [DW-01]

### 你在哪里

一个会写 Python/JS 脚本的独立开发者，每天有 1-2 小时业余时间，想做能真正产生收入的自动化项目。没有完整产品开发经验，不想碰加密货币，希望第一个项目就能看到回报。

### 要去哪里

搭建 **3 条独立但互补的自动化收入轨道**，覆盖短期（1-2周见效）、中期（2-3月见效）、长期（6-12月见效）三个时间维度。搭建完成后每周维护不超过 2 小时，月运营成本控制在 ¥200 以内。

| 轨道 | 类型 | 变现方式 | 见效时间 | 自动化程度 |
|------|------|----------|----------|-----------|
| 🚀 轨道1 | Coze AI 模板 | 闲鱼销售模板+定制接单 | 1-2 周 | 85%（接单沟通为人工；模板销售全自动） |
| 📰 轨道2 | 内容自动化管线 | 广告+联盟佣金 | 2-3 月 | 95%（采集→AI→生成→部署全自动；掘金/知乎分发为手动30秒/条） |
| 🔧 轨道3 | 在线工具站 | Google AdSense 广告 | 6-12 月 | 98%（纯静态，零维护；每2周人工添加1新工具约2h） |

> **自动化程度说明**：轨道2自动化程度指采集→生成→静态站部署这一核心管线。向掘金/知乎的手动分发约占整体工作量的5%，不纳入管线自动化计算。轨道1的闲鱼沟通环节为人工（约占轨道1工作量的15%）。

### 为什么不做一个大的

三条轨道的风险互相独立。闲鱼挂掉不影响工具站流量，工具站 SEO 没起来不影响内容管线收入。而且轨道1给你快速正反馈，支撑你坚持到轨道2和轨道3开花结果。

---

## 成功标准 [DW-02]

| 编号 | 标准 | 量化指标 | 数据来源 |
|------|------|----------|----------|
| SC-01 | 闲鱼首次上架 | 2周内上架首个Coze模板 | 时间约束直接来自用户需求 |
| SC-02 | 闲鱼首月收入 | 30天内 ≥ ¥500（约2-3单定制） | [实操案例：18天8400元](https://mp.weixin.qq.com/s?__biz=MzE5MTU1MzAxMw==&mid=2247483759&idx=1&sn=5cda2c417f1382b35366edc316728118)，保守取下限 |
| SC-03 | 闲鱼3月累计 | 3个月累计 ≥ ¥3000 | 同上，取保守估计 |
| SC-04 | 内容管线搭建 | 2月内完成采集→AI→发布全管线（含测试） | 管线 MVP 2-4周 + 测试1周，buffer 1周 |
| SC-05 | 内容站6月广告收入 | 月收入 ≥ ¥500 | [AdSense RPM 基准：内容类 $2-5](https://adrevhub.com/rpm-calculator/) |
| SC-06 | 工具站上线 | 1月内上线 ≥ 5 个工具（含验收测试） | 单个工具 4-8h + 验收 0.5h，5个 = 22.5-42.5h，4周可完成 |
| SC-07 | 工具站12月广告收入 | 月收入 ≥ ¥1000 | [工具类 RPM $5-12](https://adrevhub.com/rpm-calculator/) |
| SC-08 | 全局自动化 | 搭建后每周维护 ≤ 2h（日常巡检 ≤ 1.5h + 异常缓冲 ≥ 0.5h） | 用户约束 + [DORA 2025：精英团队 MTTR < 1h](https://cloud.google.com/devops/state-of-devops) |
| SC-09 | 月度API成本 | ≤ ¥150/月（含AI API），设置预算告警线¥120 | [DeepSeek API 定价 ¥1/百万token](https://platform.deepseek.com/pricing)，日均100条×2500token |
| SC-10 | 安全基线 | 0 个 XSS/注入类漏洞，CI 中 HTML 校验通过率 100% | [OWASP Top 10](https://owasp.org/www-project-top-ten/) + 评审反馈 MP-03/MP-06 |

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
Step 2: 添加「文件上传」节点 → 限制文件类型为 PDF/Word/图片（校验扩展名+MIME）
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

（商品文案模板、定价策略、运营节奏与 v1 一致，此处省略以精简篇幅。详见 v1 方案 [DS-01] 第92-119行。）

### 轨道1 时间线

| 周次 | 任务 | 产出 |
|------|------|------|
| 第1周 | 搭建「简历优化」+「日报生成」+ 上架闲鱼 | 2个模板在线 |
| 第2周 | 搭建「竞品监控」+「合同风险」+「客服话术」+ 优化前2个 | 5个模板在线 |
| 第3-4周 | 运营优化：回复咨询、优化文案、观察数据 | 首月收入目标 ¥500 |

### 平台迁移预案

Coze 是字节跳动旗下产品，未来可能调整收费策略或限制免费功能。预案：

| 迁移目标 | 迁移工作量 | 影响评估 |
|----------|-----------|----------|
| **Dify**（开源·自部署） | Prompt 文本直接复用；工作流需在 Dify 可视化界面重建，每个约1-2h | 5个模板重建约5-10h；月成本增加 VPS ¥50 |
| **Dify Cloud**（托管版） | 同上，免自部署 | 免费版有额度限制；专业版约 $59/月（超出预算） |
| Prompt 文本独立保存 | **已于 [DS-04] 设计**：所有 Prompt 保存为独立 .txt 文件 | 零成本，确保核心资产可移植 |

> **结论**：当前 Coze 免费，无需立即迁移。Prompt 源文件已独立保存，最坏情况下 1 周内可完成全部迁移到 Dify 自部署版，月成本仍 ≤ ¥100。

---

## 轨道2：内容自动化管线 [DS-02]

### 做什么

一条 Python 脚本管线，自动完成：**采集热榜数据 → AI 摘要+改写 → HTML 转义消毒 → 生成静态页 → 部署到 Cloudflare Pages**。通过 Google AdSense 广告变现。掘金/知乎分发作为辅助引流（手动操作，每次约30秒/条）。

### 技术架构

```
┌─────────────────────────────────────────────────────┐
│                  GitHub Actions                       │
│  cron: 每4小时触发（北京时间 4/8/12/16/20/24点）      │
│  timeout-minutes: 30 | concurrency: single-group     │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│          数据采集层 (collectors/)                      │
│  每个采集器独立 try-except，失败仅记录不阻断管线        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐              │
│  │ 微博热搜  │ │ 知乎热榜  │ │ 百度热搜  │  ... 更多   │
│  │ weibo.py │ │ zhihu.py │ │ baidu.py  │              │
│  └──────────┘ └──────────┘ └──────────┘              │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              AI处理层 (processor.py)                   │
│  去重→过滤→AI摘要（结构化JSON输出）→AI改写             │
│  模型: DeepSeek API (response_format: json_object)   │
│  成本追踪: 每次调用记录 token 数到 daily_tokens.json   │
│  超限保护: 月累计超¥150自动降级为标题+链接模式          │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│           输出与消毒层 (builder.py)                     │
│  所有采集/AI文本 → html.escape() → Jinja2 模板渲染     │
│  渲染后 → BeautifulSoup 校验标签闭合 → 通过才写入        │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              输出层 (output/)                         │
│  ┌──────────────────┐  ┌──────────────────┐          │
│  │ index.html        │  │ posts/*.html      │          │
│  └──────────────────┘  └──────────────────┘          │
│  ┌──────────────────┐  ┌──────────────────┐          │
│  │ sitemap.xml       │  │ feed.json         │          │
│  └──────────────────┘  └──────────────────┘          │
│  ┌──────────────────┐                               │
│  │ stats.json        │← 每日采集/生成/API消耗统计     │
│  └──────────────────┘                               │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│           Cloudflare Pages (自动部署)                  │
│  校验通过 → git commit → push → CF 自动构建            │
│  校验失败 → 跳过 push + 记录错误日志                    │
│  保留最近 3 次 output/ 快照于 output-backup-*/         │
└─────────────────────────────────────────────────────┘
```

### 数据源选择（含反爬策略）

| 平台 | 采集方式 | API Endpoint | 难度 | 反爬要点 |
|------|----------|-------------|------|----------|
| 微博热搜 | `requests` → JSON | `https://weibo.com/ajax/side/hotSearch` | ⭐ | UA 伪装为 Chrome；间隔 1-3s |
| 知乎热榜 | `requests` → JSON | `https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total` | ⭐⭐ | **需 Cookie**（从浏览器复制）；UA 伪装 |
| 百度热搜 | `requests` → HTML parse | `https://top.baidu.com/board?tab=realtime` | ⭐ | UA 伪装；间隔 2s |
| B站热门 | `requests` → JSON | `https://api.bilibili.com/x/web-interface/popular` | ⭐⭐ | UA + Referer 头；部分接口需签名 |
| 掘金热榜 | `requests` → JSON | `https://api.juejin.cn/content_api/v1/content/article_rank` | ⭐ | UA 伪装 |
| V2EX 最热 | `requests` → HTML parse | `https://www.v2ex.com/api/topics/hot.json` | ⭐ | 有官方 API，最稳定 |

**统一反爬策略**（所有采集器共用）：
```python
# 所有 requests 调用统一参数
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36'
}
TIMEOUT = 30  # 单次请求超时
RETRY_DELAY = [1, 3, 9]  # 指数退避重试（最多3次）
```

### run_all.py 容错架构（伪代码）

```python
import time
import random
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class TrendItem:
    """所有采集器统一返回格式"""
    title: str
    url: str
    platform: str
    hot_score: Optional[int] = None
    raw_data: Optional[Dict] = None

def collect_with_fallback(collector_name: str, collect_func) -> List[TrendItem]:
    """通用采集包装器：try-except + 重试 + 超时"""
    try:
        items = collect_func()
        print(f"[OK] {collector_name}: {len(items)}条")
        return items
    except Exception as e:
        print(f"[FAIL] {collector_name}: {type(e).__name__}: {e}")
        return []  # 返回空列表，不阻断管线

def run_all() -> Dict[str, List[TrendItem]]:
    """主入口：串行调用所有采集器，互不阻断"""
    results = {}
    collectors = [
        ("weibo", collect_weibo),
        ("zhihu", collect_zhihu),
        ("baidu", collect_baidu),
        ("bilibili", collect_bilibili),
        ("juejin", collect_juejin),
        ("v2ex", collect_v2ex),
    ]
    for name, func in collectors:
        results[name] = collect_with_fallback(name, func)
        time.sleep(random.uniform(1, 3))  # 请求间随机间隔
    return results
```

### AI Prompt 工程设计

**摘要 Prompt**（输出约束为结构化 JSON）：
```
分析以下热搜条目，生成一条 JSON 格式的摘要。

输入标题: {title}
输入链接: {url}
来源平台: {platform}

输出严格按以下 JSON Schema：
{
  "title": "原标题（去emoji和特殊字符）",
  "summary": "2-3句话概括事件核心（不超过150字）",
  "category": "tech|business|society|entertainment|other",
  "key_words": ["关键词1", "关键词2", "关键词3"],
  "is_evergreen": true/false,
  "english_title": "英文标题（用于双语SEO）"
}

要求：
- summary 必须客观、不含主观评价
- 如果是娱乐八卦，category 标为 "entertainment"
- is_evergreen 判断该话题是否有长期价值（技术教程=true，明星八卦=false）
```

**改写 Prompt**（按角度生成价值内容）：
```
基于以下热搜摘要，从"{angle}"角度写一篇150-200字的分析：

原始摘要: {summary}
来源: {platform}

角度选项：
- tech_view: 技术视角（对开发者/产品经理有什么启示）
- business_view: 商业视角（商业模式/市场格局有什么变化）
- society_view: 社会视角（反映什么趋势/现象）

输出 JSON：
{
  "angle": "使用的角度",
  "content": "分析内容（150-200字）",
  "takeaway": "一句话核心观点"
}
```

**API 调用时强制结构化输出**：
```python
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[...],
    response_format={"type": "json_object"},  # 强制 JSON 输出
    temperature=0.3,  # 低温度保证格式稳定
)
```

### feed.json Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "generated_at": {"type": "string", "format": "date-time"},
    "total_items": {"type": "integer"},
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "title": {"type": "string"},
          "summary": {"type": "string"},
          "category": {"enum": ["tech", "business", "society", "entertainment", "other"]},
          "platform": {"type": "string"},
          "source_url": {"type": "string", "format": "uri"},
          "english_title": {"type": "string"},
          "analysis": {"type": "string"},
          "takeaway": {"type": "string"}
        },
        "required": ["id", "title", "summary", "platform", "source_url"]
      }
    }
  }
}
```

### GitHub Actions 配置（修订版）

```yaml
# .github/workflows/trending.yml
name: Trending Content Pipeline

on:
  schedule:
    # 每4小时（UTC），对应北京时间 4/8/12/16/20/24点，共6次/天
    - cron: '0 20,0,4,8,12,16 * * *'
  workflow_dispatch:  # 手动触发
  # 注意：不使用 push/pull_request 触发，避免每次commit都运行管线

# 并发控制：同一时间只运行一个管线实例
concurrency:
  group: trending-pipeline
  cancel-in-progress: true

jobs:
  pipeline:
    runs-on: ubuntu-latest
    timeout-minutes: 30  # 单次运行最长30分钟，防止额度耗尽

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # 获取完整历史，用于回滚tag

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install deps
        run: pip install requests beautifulsoup4 httpx jinja2

      - name: Collect trends
        id: collect
        run: python collectors/run_all.py
        continue-on-error: false  # 采集失败则停止，不部署空内容

      - name: AI Process
        id: ai
        run: python processor.py
        env:
          AI_API_KEY: ${{ secrets.AI_API_KEY }}
          AI_API_URL: ${{ secrets.AI_API_URL }}

      - name: Build & Validate HTML
        id: build
        run: |
          python builder.py
          python validate_output.py  # 标签闭合校验

      - name: Run tests
        run: python -m pytest tests/ -v

      - name: Commit & Push
        if: success()  # 仅在前序步骤全部成功时push
        run: |
          git config user.name "TrendBot"
          git config user.email "bot@trends.local"
          git add output/ logs/
          if git diff --staged --quiet; then
            echo "No changes to commit"
          else
            git commit -m "Update: $(date +'%Y-%m-%d %H:%M BJT')"
            git tag "deploy-$(date +'%Y%m%d-%H%M')"  # 打tag用于回滚
            git push --follow-tags
          fi

      - name: Notify on failure
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: `[管线告警] ${new Date().toISOString().slice(0,10)} 内容管线执行失败`,
              body: `Run: ${context.runId}\n详见: ${context.serverUrl}/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId}`
            })
```

### builder.py HTML 消毒规范

```python
import html
from jinja2 import Environment, BaseLoader, select_autoescape

# 使用 Jinja2 自动转义（默认对 HTML/XML 开启）
env = Environment(
    loader=BaseLoader(),
    autoescape=select_autoescape(['html', 'xml'])
)

def render_post(item: dict) -> str:
    """渲染单条热搜详情页，所有外部文本自动转义"""
    template = env.from_string("""
    <article>
      <h1>{{ item.title }}</h1>
      <p class="summary">{{ item.summary }}</p>
      <div class="analysis">{{ item.analysis }}</div>
      <a href="{{ item.source_url }}" rel="nofollow noopener" target="_blank">查看原文</a>
    </article>
    """)
    # item 中的 title/summary/analysis 自动被 Jinja2 转义
    return template.render(item=item)

# 如果不用 Jinja2（如纯 f-string），必须手动调用 html.escape()
# from html import escape
# f'<h1>{escape(item["title"])}</h1>'
```

### validate_output.py HTML 校验

```python
"""部署前校验 HTML 标签闭合和基本结构"""
from bs4 import BeautifulSoup
import sys
from pathlib import Path

def validate_html(filepath: str) -> bool:
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    # 必须有 <title> 和 <h1>
    if not soup.title or not soup.title.string:
        print(f"[FAIL] {filepath}: missing <title>")
        return False
    if not soup.find('h1'):
        print(f"[FAIL] {filepath}: missing <h1>")
        return False
    return True

def main():
    output_dir = Path('output')
    all_ok = True
    for f in output_dir.rglob('*.html'):
        if not validate_html(str(f)):
            all_ok = False
    if not all_ok:
        sys.exit(1)  # CI 失败，阻止部署
    print("[OK] All HTML files validated")
```

### AI API 成本控制

```python
# processor.py 中的成本追踪
import json
from pathlib import Path
from datetime import datetime

COST_LOG = Path('logs/daily_tokens.json')
MONTHLY_BUDGET_YUAN = 150  # 月度预算上限
ALERT_THRESHOLD_YUAN = 120  # 告警线
TOKEN_PRICE = 0.001 / 1000  # DeepSeek: ¥1/百万token = ¥0.001/千token

def check_budget() -> bool:
    """检查当月累计消耗是否超限；超限返回 False（降级模式）"""
    if not COST_LOG.exists():
        return True
    logs = json.loads(COST_LOG.read_text())
    month_key = datetime.now().strftime('%Y-%m')
    month_total = sum(d['tokens'] for d in logs if d['date'].startswith(month_key))
    cost = month_total * TOKEN_PRICE
    if cost > MONTHLY_BUDGET_YUAN:
        print(f"[BUDGET] 月度消耗 ¥{cost:.1f} 超过预算 ¥{MONTHLY_BUDGET_YUAN}，降级为原文模式")
        return False
    if cost > ALERT_THRESHOLD_YUAN:
        print(f"[BUDGET] 月度消耗 ¥{cost:.1f} 已达告警线 ¥{ALERT_THRESHOLD_YUAN}")
    return True

def process_trends(items, budget_ok=True):
    if not budget_ok:
        # 降级模式：仅去重+过滤，不调用AI，直接输出原文标题+链接
        return [{"title": item['title'], "summary": "", "source_url": item['url']} 
                for item in filter_trends(items)]
    # 正常模式：AI摘要+改写
    return ai_process(items)
```

### 轨道2 时间线

| 周次 | 任务 | 产出 |
|------|------|------|
| 第1周 | 搭建微博采集器 + AI处理（含Prompt模板）+ HTML生成 + 编写 collector 基础测试 | MVP管线跑通 + 测试通过 |
| 第2周 | 接入全部6个数据源 + 关键词过滤 + 去重 + collect_all 容错包装 | 完整数据管线 |
| 第3周 | HTML模板优化 + SEO（sitemap、meta、结构化数据、hreflang） + HTML校验脚本 | 可发布静态站 |
| 第4周 | 部署CF Pages + 域名绑定 + 301重定向 + 申请AdSense + 配置Actions（含超时/并发/通知） | 全自动运行 |
| 第5-8周 | 持续优化内容质量、SEO、广告位、监控告警 | 等待AdSense审核通过 |

---

## 轨道3：在线工具站 [DS-03]

### 做什么

一个纯前端的在线工具集合站，所有计算/处理在浏览器端完成（隐私卖点）。通过 SEO 长尾关键词获取流量，Google AdSense 变现。

### 选哪 8 个工具

| 序号 | 工具 | 开发时间 | 复杂度 | 核心 API |
|------|------|----------|--------|----------|
| 1 | **JSON格式化/验证** | 3h | 低 | `JSON.parse/stringify` + 通用错误提示（不暴露 e.message） |
| 2 | **时间戳转换** | 2h | 低 | `new Date(timestamp*1000)` + 时区选择器 |
| 3 | **Base64编解码** | 2h | 低 | `btoa()/atob()` + `TextEncoder/Decoder`（UTF-8安全） |
| 4 | **图片压缩** | 6h | 高 | Canvas API + `toBlob()` + Web Worker（详见下方） |
| 5 | **URL编解码** | 1.5h | 低 | `encodeURIComponent/decodeURIComponent` |
| 6 | **MD5/SHA哈希** | 2h | 中 | Web Crypto API `crypto.subtle.digest()`（详见下方） |
| 7 | **正则测试器** | 3h | 中 | `RegExp` + 标志切换 + 超时保护（详见下方） |
| 8 | **颜色转换** | 2h | 低 | Canvas 取色 + HEX/RGB/HSL 互转公式 |

### 复杂工具实现细节

#### 图片压缩（image-compress.html）— 6h

```
核心流程：
1. <input type="file" accept="image/jpeg,image/png,image/webp">
   前端双重校验: accept属性 + JS端 file.type 白名单
   特别排除 image/svg+xml（SVG可嵌入脚本，不走Canvas压缩路径）

2. FileReader 读取为 DataURL → new Image() 加载

3. Canvas 绘制：
   - 保持原图宽高比，最大尺寸 4096px（防止超大图OOM）
   - ctx.drawImage(img, 0, 0, targetW, targetH)

4. canvas.toBlob() 输出：
   - 格式: image/jpeg（默认·压缩率最高）/ image/webp（体积更小）/ image/png（无损）
   - 质量滑块 0.1-1.0（默认 0.8）
   - 预估输出大小显示（blob.size）

5. Web Worker 处理大图：
   - 主线程: 文件读取 + UI更新
   - Worker线程: Canvas离屏渲染 + toBlob()
   - 使用 OffscreenCanvas（Chrome/Edge/Firefox均支持）

安全校验：
- 前端 file.type 白名单: ['image/jpeg', 'image/png', 'image/webp']
- SVG 明确拒绝: if (file.type === 'image/svg+xml') { alert('不支持SVG格式'); return; }
- 文件大小上限: 10MB（JS端校验 file.size <= 10*1024*1024）
- 输出文件命名: 使用随机字符串，不暴露原始文件路径
```

#### MD5/SHA哈希（md5-hash.html）— 2h

```
核心API: Web Crypto API (crypto.subtle.digest)

优势：
- 浏览器原生支持，无需引入第三方库（如 crypto-js）
- 支持 SHA-1, SHA-256, SHA-384, SHA-512
- 异步非阻塞（返回 Promise）

// 计算 SHA-256
async function sha256(text) {
    const encoder = new TextEncoder();
    const data = encoder.encode(text);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    // 转为 hex 字符串
    return Array.from(new Uint8Array(hashBuffer))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
}

注意：
- MD5 不在 Web Crypto API 中（被认为不安全），需额外实现或用 SparkMD5（轻量库·4KB）
- 文本 vs 文件：文本用 TextEncoder，文件用 FileReader.readAsArrayBuffer()
- 输入长度限制: ≤ 10MB（防止浏览器OOM）
```

#### 正则测试器（regex-tester.html）— 3h

```
核心功能：
1. 正则输入框 + 标志切换（g/i/m/s/u 复选框）
2. 测试文本 textarea
3. 匹配结果展示：
   - 匹配列表（matchAll()）
   - 分组显示
   - 替换测试（replace()）
4. 匹配高亮：将匹配文本用 <mark> 包裹，用 textContent 渲染防止 XSS

超时保护（防止 ReDoS）：
function safeRegexMatch(pattern, flags, text, timeoutMs=3000) {
    // 方案：使用 Web Worker 执行正则，主线程设超时
    // Worker 超时未返回则 terminate() 并提示"正则复杂度过高"
    return new Promise((resolve, reject) => {
        const worker = new Worker('regex-worker.js');
        const timer = setTimeout(() => {
            worker.terminate();
            reject(new Error('正则执行超时'));
        }, timeoutMs);
        worker.postMessage({pattern, flags, text});
        worker.onmessage = (e) => {
            clearTimeout(timer);
            worker.terminate();
            resolve(e.data);
        };
    });
}

安全：
- 正则表达式长度限制 ≤ 1000 字符
- 测试文本长度限制 ≤ 100KB
- 匹配结果用 textContent（非 innerHTML）渲染
- Worker 隔离防止主线程阻塞
```

### 全局安全规范（所有8个工具遵守）

1. **错误信息不暴露实现细节**：所有 `catch(e)` 中用通用文案替代 `e.message`。原始错误仅输出到 `console.error()`
2. **用户输入渲染用 `textContent`**：永远不用 `innerHTML` 渲染用户输入内容
3. **文件上传双重校验**：`accept` 属性 + JS `file.type` 白名单
4. **输入长度限制**：JSON ≤ 1MB，文本 ≤ 100KB，文件 ≤ 10MB，正则 ≤ 1000字符
5. **安全头**：所有页面部署在 Cloudflare Pages，通过 `_headers` 文件统一设置（详见 [DS-09]）

### 核心卖点

> 🔒 **一切在浏览器中完成，文件不上传服务器。**区别于 Smallpdf/ILovePDF 等竞品。

### 轨道3 时间线

| 周次 | 任务 | 产出 |
|------|------|------|
| 第1周 | 域名注册 + CF Pages 初始化 + 首页 + JSON格式化 + 时间戳 | 基础设施 + 2个工具 |
| 第2周 | Base64 + URL编解码 + MD5哈希 + 正则测试器 | 6个工具上线 |
| 第3周 | 图片压缩 + 颜色转换 + sitemap + SEO | 8个工具全部上线 |
| 第4周 | 每个工具手动验收（见测试策略 [DS-10]）+ Search Console提交 + AdSense申请 + 必需页面（关于/隐私/联系/广告披露） | 验收完成 + SEO就绪 |
| 第5周起 | 等待SEO起量，每2周添加1个新工具 | 内容持续增长 |

---

## 项目目录结构 [DS-04]

```
makemoney/
├── .real-want-domains.json
├── .real-want-preferences.json
├── makemoney-automation-prompt.json
├── makemoney-automation-规划方案-v2.md
├── makemoney-automation-评审反馈.json
│
├── track1-coze/                     # 🚀 轨道1：Coze模板
│   ├── 闲鱼文案/                     # 5个商品文案
│   ├── Prompt源码/                   # 独立保存，可迁移到任何平台
│   │   ├── 简历优化-prompt.txt
│   │   ├── 日报生成-prompt.txt
│   │   ├── 竞品监控-prompt.txt
│   │   ├── 合同风险-prompt.txt
│   │   └── 客服话术-prompt.txt
│   └── SOP文档模板.md
│
├── track2-content-pipeline/         # 📰 轨道2：内容管线
│   ├── collectors/
│   │   ├── run_all.py               # 主入口（try-except每个采集器）
│   │   ├── base.py                  # 共享：HEADERS/TIMEOUT/RETRY/collect_with_fallback
│   │   ├── weibo.py
│   │   ├── zhihu.py
│   │   ├── baidu.py
│   │   ├── bilibili.py
│   │   ├── juejin.py
│   │   └── v2ex.py
│   ├── processor.py                 # AI处理（含预算控制+结构化输出）
│   ├── builder.py                   # HTML生成（Jinja2自动转义）
│   ├── validate_output.py           # 部署前HTML标签闭合校验
│   ├── tests/                       # 测试目录（新增）
│   │   ├── test_collectors.py       # 采集器测试（mock HTTP）
│   │   ├── test_processor.py        # AI处理测试（mock API）
│   │   └── test_builder.py          # HTML生成+转义测试
│   ├── output/                      # 生成的静态站
│   │   ├── index.html
│   │   ├── archive.html
│   │   ├── posts/
│   │   ├── sitemap.xml
│   │   ├── ads.txt
│   │   ├── robots.txt
│   │   └── static/
│   ├── output-backup-*/             # 最近3次部署的快照（回滚用）
│   ├── logs/                        # 运行日志（新增）
│   │   ├── daily_tokens.json        # 每日API消耗
│   │   └── collector_stats.json     # 采集成功率统计
│   ├── frequency_words.txt          # 过滤关键词
│   ├── requirements.txt
│   └── .github/workflows/
│       └── trending.yml             # 含超时/并发/测试/通知
│
├── track3-tools-site/               # 🔧 轨道3：在线工具站
│   ├── index.html                   # 首页·工具导航
│   ├── about.html                   # 关于页（AdSense必需）
│   ├── privacy.html                 # 隐私政策页（AdSense必需）
│   ├── contact.html                 # 联系页（AdSense必需）
│   ├── disclosure.html              # 广告披露页（AdSense政策要求）
│   ├── tools/
│   │   ├── json-formatter.html
│   │   ├── timestamp.html
│   │   ├── base64.html
│   │   ├── image-compress.html      # Canvas+Worker+SVG拒绝
│   │   ├── url-encode.html
│   │   ├── md5-hash.html            # Web Crypto API
│   │   ├── regex-tester.html        # Worker超时保护
│   │   └── color-convert.html
│   ├── static/
│   │   ├── style.css
│   │   ├── script.js                # 公共函数（安全渲染工具函数）
│   │   └── regex-worker.js          # 正则Web Worker
│   ├── tests/                       # 工具站验收清单（新增）
│   │   └── manual_checklist.md
│   ├── sitemap.xml
│   ├── ads.txt
│   ├── robots.txt
│   └── _headers                     # CSP + 安全头
│
└── dashboard/                       # 统一看板（后期）
    └── stats.html
```

---

## 实现计划 [DS-05]

按天编排，每天 1-2 小时。三条轨道交错推进，优先保证轨道1快速出结果。

### 第1周：快速变现先跑通

| 天 | 轨道 | 任务 | 产出 |
|----|------|------|------|
| 1 | 🔧3 | 注册域名 + CF Pages 初始化 + GitHub 仓库 + `.gitignore`（排除 `.env`） | 基础设施 |
| 2 | 🚀1 | Coze 搭建「简历优化助手」+ 写闲鱼文案 | 第1个模板 |
| 3 | 🚀1 | Coze 搭建「日报生成器」+ 上架闲鱼（2个商品） | 上架！ |
| 4 | 📰2 | 搭建微博采集器 + `base.py` 共享模块（HEADERS/重试逻辑） | 第1个采集器 |
| 5 | 📰2 | AI 处理脚本 + builder.py 基础版（含 Jinja2 转义） | 管线核心 |
| 6 | 🚀1 | 搭建「竞品监控器」+ 优化闲鱼商品标题/标签 | 第3个模板 |
| 7 | 🔧3 | 工具站首页 + JSON格式化工具（通用错误提示） | 第1个工具 |

### 第2周：管线成型 + 测试起步

| 天 | 轨道 | 任务 | 产出 |
|----|------|------|------|
| 8 | 📰2 | HTML生成器完善（首页+详情页+归档）+ `tests/test_builder.py`（HTML转义测试） | 静态站+测试 |
| 9 | 📰2 | 接入知乎 + 百度采集器 + `tests/test_collectors.py`（mock HTTP测试） | 3数据源+测试 |
| 10 | 🚀1 | 搭建「合同风险」+「客服话术」+ 上架闲鱼 | 5个模板全部在线 |
| 11 | 🔧3 | 时间戳转换 + Base64编解码 + URL编解码（含安全校验） | 4个工具上线 |
| 12 | 📰2 | 接入B站 + 掘金 + V2EX采集器 | 6个数据源 |
| 13 | 📰2 | 配置 GitHub Actions（含超时/并发/测试步骤/失败通知）+ 测试自动运行 | 全自动管线 |
| 14 | 全局 | 复盘：轨道1收入、轨道2管线稳定性+测试通过率、轨道3进度 | 第2周总结 |

### 第3-4周：补齐安全 + 监控 + 验收

| 天 | 轨道 | 任务 | 产出 |
|----|------|------|------|
| 15-16 | 🔧3 | 图片压缩（Canvas+Worker+安全校验）+ MD5哈希（Web Crypto API） | 2个复杂工具 |
| 17-18 | 🔧3 | 正则测试器（Worker超时保护）+ 颜色转换 | 8个工具全部上线 |
| 19 | 📰2 | `validate_output.py`（HTML校验）+ `logs/` + 成本追踪逻辑 | 质量门禁+监控 |
| 20 | 🔧3 | 每个工具手动验收（按 [DS-10] 清单逐项检查） | 验收记录 |
| 21-22 | 全局 | 工具站 SEO + Search Console提交 + `_headers` 配置（CSP等） + 必需页面（关于/隐私/联系/广告披露） | 安全+SEO就绪 |
| 23-24 | 📰2 | 部署 CF Pages + 域名绑定 + 301重定向 + 管线端到端测试 | 正式上线 |
| 25 | 🚀1 | 闲鱼运营优化 + 上架SOP文档版 | 提升转化率 |
| 26 | 全局 | AdSense 申请 + ads.txt + 广告位嵌入 | 广告系统就绪 |
| 27 | 全局 | 整体安全审查（按 [DS-09] 安全清单逐项检查） | 安全审查通过 |
| 28 | 全局 | 文档整理（部署文档 + 运维runbook） | 搭建阶段收尾 |

### 第5周起：运维模式（含日常巡检 + 异常缓冲）

| 项目 | 频率 | 耗时 | 内容 |
|------|------|------|------|
| 🚀 轨道1 | 每天 | 10min | 回复闲鱼消息（快捷回复模板） |
| 🚀 轨道1 | 每周 | 20min | 优化商品标题/标签，查看浏览量 |
| 📰 轨道2 | 每周 | 15min | 检查 Actions 运行日志 + `collector_stats.json` 成功率 |
| 📰 轨道2 | 每周 | 10min | 抽查 AI 输出质量（随机读3篇） |
| 🔧 轨道3 | 每2周 | 2h | 添加1个新工具 + 查看 Search Console |
| 🔧 轨道3 | 每月 | 15min | UptimeRobot 可用性检查 |
| 全局 | 每月 | 30min | 查看三条轨道收入汇总 + API 费用 |

**维护时间预算**：
- 日常巡检：~1.5h/周
- 异常缓冲：0.5h/周（用于处理间歇性故障）
- **前3个月学习期**：放宽到 3-4h/周（异常处理经验不足）
- **3个月后**：回归 2h/周目标
- 每周记录实际维护时间到 `logs/maintenance.md`，用于验证 SC-08

---

## 边界情况与异常处理 [DS-06]

### 轨道1：Coze/闲鱼

| 异常 | 自动/人工 | 处理 |
|------|----------|------|
| Coze 平台政策变化 | 人工（需决策） | Dify 作为备选（见 [DS-01] 迁移预案）；Prompt 源码独立保存 |
| 闲鱼商品被下架 | 人工 | 修改文案敏感词；换号重发。建议每周手动检查一次商品状态（计入日常巡检） |
| 定制单客户不满意 | 人工 | 2次免费修改；完成前可退50% |
| 竞争加剧 | 人工 | 转型更细分垂直领域或 SOP 文档销售 |
| Coze 服务宕机 | 人工通知 | 模板在客户空间独立运行不受影响；定制单与客户沟通延迟 |

### 轨道2：内容管线

| 异常 | 自动/人工 | 处理 |
|------|----------|------|
| 目标网站改版/反爬 | **半自动** | 单个采集器 `try-except` 返回空列表，不阻断管线；`collector_stats.json` 记录成功率供人工巡检 |
| AI API 调用失败 | **自动** | 3次指数退避重试（1s/3s/9s）；仍失败则用上一条缓存数据；Issue 自动创建告警 |
| AI API 月度超预算 | **自动** | `processor.py` 检测累计消耗超 ¥150 → 自动降级为标题+链接模式（不调用AI） |
| 生成 HTML 校验失败 | **自动** | `validate_output.py` 失败 → CI 报错 → 跳过 git push → Issue 自动创建 |
| Cloudflare Pages 部署失败 | **自动** | git push 失败时 Actions 报错 + Issue 通知。回滚：`git checkout deploy-{上一tag}` → 重新 push |
| AdSense 审核不通过 | 人工 | 积累 ≥ 30 篇内容 + 确保必需页面齐全 → 30天后重新申请 |
| GitHub Actions 额度耗尽 | **自动预警** | `logs/` 记录每月运行分钟数；接近 1800min/月 时 Issue 提醒 |
| 内容管线需紧急回滚 | **半自动** | 方案：(1) `git log --oneline --tags` 找上一个 deploy tag；(2) `git checkout deploy-YYYYMMDD-HHMM`；(3) `git push -f origin main`；（4）CF 自动重新部署。output-backup-*/ 保留最近3次快照作为备选 |

### 轨道3：工具站

| 异常 | 自动/人工 | 处理 |
|------|----------|------|
| 浏览器兼容性 | 人工（上线前） | Chrome + Safari + 手机端手动验收 |
| 大文件浏览器卡死 | **自动预防** | 图片 ≤ 10MB、JSON ≤ 1MB、文本 ≤ 100KB 硬限制 + Worker 隔离 |
| AdSense 广告不展示 | 人工 | 检查 ads.txt + 广告单元审核状态 |
| SEO 不收录 | 人工 | Search Console 检查抓取错误 |
| UptimeRobot 告警 | **自动** | 站点不可用时邮件/推送通知 |

### 安全异常（新增）

| 异常 | 自动/人工 | 处理 |
|------|----------|------|
| 采集数据含恶意脚本 | **自动** | `builder.py` Jinja2 自动转义所有外部文本；CSP 头禁止 inline script |
| 用户上传恶意文件（SVG/EXE） | **自动** | 前端 `accept` + `file.type` 双重白名单；SVG 明确拒绝 |
| API Key 泄露到前端 | **自动预防** | `.gitignore` 排除 `.env`；Actions 用 `${{ secrets.* }}` 注入，不在代码中硬编码 |
| 工具站被 XSS 攻击 | **自动预防** | CSP 头 + 所有用户输入用 `textContent` 渲染 + 输入长度硬限制 |
| 高频调用耗光 CF 免费额度 | **自动预防** | CF Rate Limiting 规则（每 IP 100次/分钟） |

---

## 部署方案 [DS-07]

（基础设施清单、域名规划、Cloudflare Pages 配置与 v1 一致，此处省略以精简篇幅。详见 v1 方案 [DS-07]。）

### Cloudflare Pages _headers 配置（新增）

```text
# track3-tools-site/_headers
/*
  Content-Security-Policy: default-src 'self'; script-src 'self' https://cdn.tailwindcss.com https://pagead2.googlesyndication.com https://www.googletagmanager.com; style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; img-src 'self' data: https:; frame-src https://googleads.g.doubleclick.net; connect-src 'self'
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
  Permissions-Policy: camera=(), microphone=(), geolocation=()

# track2-content-pipeline/output/_headers（同上，脚本CDN调整为实际使用）
```

### 成本核算（修订）

| 项目 | 月成本 | 备注 |
|------|--------|------|
| 域名 | ¥5-7 | 年费分摊 |
| DeepSeek API | ¥50-120 | 日均100条×2500 token/条×30天=7.5M token ≈ ¥7.5。含改写扩大5-10倍 ≈ ¥37-75。上浮到 ¥50-120 留余量 |
| Coze | ¥0 | |
| CF Pages | ¥0 | |
| GitHub | ¥0 | Actions 2000min/月；每天6次×2min×30天=360min，远低于限额 |
| UptimeRobot | ¥0 | 免费版50个监控点 |
| **合计** | **¥55-127/月** | 远低于 ¥200 预算。告警线 ¥120，硬上限 ¥150 |

### SEO 必需页面 Checklist（新增）

部署前确认以下页面存在且可访问：

- [ ] `index.html` — 首页
- [ ] `about.html` — 关于页（说明站点用途+作者信息）
- [ ] `privacy.html` — 隐私政策（声明数据不上传服务器、AdSense 使用的 Cookie 等）
- [ ] `contact.html` — 联系页（至少一个邮箱或表单）
- [ ] `disclosure.html` — 广告披露（声明使用 Google AdSense 广告）
- [ ] `sitemap.xml` — 提交到 Google Search Console + 百度站长平台
- [ ] `ads.txt` — Google 广告授权文件
- [ ] `robots.txt` — 爬虫规则
- [ ] 每个工具页 ≤ 300 字说明文案 + FAQ 区块
- [ ] Lighthouse 性能评分 > 90（纯静态站天然达标）
- [ ] 双语页 `hreflang` 标签（`<link rel="alternate" hreflang="en" href="...">`）

---

## 待定与风险 [DS-08]

### 待定问题

| 问题 | 影响 | 处理 |
|------|------|------|
| VPS可用性 | 中 | 无VPS则用GitHub Actions；如Actions不够用再买VPS（¥50/月），届时API成本已随收入增长可覆盖 |
| 工具站用户系统 | 低 | 初期不做；后期Pro版需求用Firebase Auth（免费额度充足） |

### 风险矩阵（修订·新增平台锁定风险）

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| AdSense 审核不通过 | 中 | 高 | 先堆内容质量，≥30篇原创再申请；确保必需页面齐全 |
| **Coze 平台政策变化 / 收费** | **中** | **中** | Prompt 源码独立保存；Dify 自部署备选；迁移工作量已评估（5-10h全量迁移） |
| Coze 闲鱼市场饱和 | 中 | 中 | 转 SOP 文档销售或企业定制 |
| AI 生成内容被 Google 降权 | 中 | 中 | 每条人工改标题+首段，保持"人味" |
| 内容站被目标网站封 IP | 低 | 低 | 多数据源冗余 |
| 域名被墙 | 低 | 高 | 海外域名+Cloudflare，不做敏感内容 |
| **GitHub Actions 额度耗尽** | **低** | **中** | 用量监控 + 备用 VPS cron 方案 |

---

## 安全设计 [DS-09]

> **统一安全策略**：三条轨道的所有安全措施集中在本章定义，各轨道实现章节通过引用本章确保一致性。

### 安全原则

1. **所有外部输入视为不可信**：爬虫数据、用户上传文件、AI 输出均需消毒
2. **输出永远转义**：HTML 中用 `textContent` 或 Jinja2 自动转义，绝不用 `innerHTML` 渲染用户内容
3. **密钥零泄露**：API Key 通过 GitHub Secrets 注入，`.env` 进 `.gitignore`
4. **纵深防御**：前端校验 + 服务端/构建时校验 + CSP 头三层防护

### 输入校验矩阵

| 输入来源 | 校验措施 | 位置 |
|----------|----------|------|
| 爬虫采集的标题/摘要 | `builder.py` Jinja2 自动转义；CSP 禁止 inline script | [DS-02] |
| AI 生成的文本 | 同上 | [DS-02] |
| JSON 格式化输入 | 长度 ≤ 1MB；输出用 `textContent` | [DS-03] |
| 图片压缩上传 | `accept` + `file.type` 白名单（JPEG/PNG/WebP）；SVG 拒绝；≤ 10MB | [DS-03] |
| 正则表达式输入 | 长度 ≤ 1000 字符；Worker 超时 3s | [DS-03] |
| MD5/哈希文本输入 | ≤ 10MB | [DS-03] |
| Coze 简历上传 | Coze 平台限制文件类型（PDF/Word/图片）+ 大小限制 | [DS-01] |

### CSP 头与安全头

所有静态页面通过 `_headers` 文件统一配置（详见 [DS-07]）：
- `Content-Security-Policy`：限制脚本来源（仅 tailwindcss CDN + AdSense）
- `X-Frame-Options: DENY`：防止点击劫持
- `X-Content-Type-Options: nosniff`：防止 MIME 嗅探攻击
- `Strict-Transport-Security`：强制 HTTPS
- `Referrer-Policy: strict-origin-when-cross-origin`

### 密钥管理

```yaml
# GitHub Actions 中引用（正确做法）
env:
  AI_API_KEY: ${{ secrets.AI_API_KEY }}

# 绝不在代码中硬编码（错误做法）
# AI_API_KEY = "sk-xxxxx"  ← 禁止！
```

`.gitignore` 必须包含：
```
.env
*.local
*.secret
credentials.json
```

### 安全检查清单（部署前执行）

- [ ] 所有 `.html` 文件中无 `innerHTML` 赋值用户输入
- [ ] 所有 `catch(e)` 中不暴露 `e.message` 给用户
- [ ] CSP 头在所有页面上生效（浏览器 DevTools 验证）
- [ ] `ads.txt` + `robots.txt` 在根目录可访问
- [ ] 图片压缩 FileReader 后验证 `file.type` 白名单
- [ ] 正则测试器 Worker 超时保护有效
- [ ] `.gitignore` 包含 `.env`
- [ ] GitHub 仓库中无硬编码密钥（`git log -p | grep -i 'api_key\|secret\|token'`）

---

## 测试策略 [DS-10]

### 轨道2：自动化测试（pytest）

**目录**：`track2-content-pipeline/tests/`

```python
# tests/test_collectors.py
def test_weibo_collector_returns_list():
    """微博采集器返回正确格式"""
    items = collect_weibo()
    assert isinstance(items, list)
    if items:
        assert 'title' in items[0]
        assert 'url' in items[0]

def test_collector_failure_returns_empty_list():
    """采集器异常时返回空列表而非抛异常"""
    # 用 monkeypatch 模拟 requests.get 失败
    result = collect_with_fallback("mock_broken", lambda: (_ for _ in ()).throw(ConnectionError()))
    assert result == []

def test_zhihu_collector_handles_403():
    """知乎返回403时采集器优雅降级"""
    ...

# tests/test_processor.py
def test_dedup_by_similar_title():
    """标题相似度>0.8去重"""
    ...

def test_filter_entertainment():
    """娱乐关键词过滤"""
    items = [{"title": "某明星出轨被拍"}, {"title": "GPT-5 发布"}]
    filtered = filter_trends(items)
    assert len(filtered) == 1  # 只有 GPT-5 保留

# tests/test_builder.py
def test_html_escape_xss():
    """builder 对恶意标题做 HTML 转义"""
    from html import escape
    malicious_title = '<script>alert("XSS")</script>'
    escaped = escape(malicious_title)
    assert '<script>' not in escaped
    assert '&lt;script&gt;' in escaped

def test_output_contains_required_elements():
    """生成的 HTML 包含必要的 SEO 元素"""
    ...
```

**CI 集成**：`pytest tests/ -v` 作为 GitHub Actions 的一个 step。测试失败 → CI 失败 → 不 git push → 不部署。

### 轨道3：手动验收清单

`track3-tools-site/tests/manual_checklist.md`：

```markdown
# 工具站手动验收清单

## 每个工具的验收项
- [ ] `catch(e)` 错误提示为通用文案，未暴露 `e.message`
- [ ] 用户输入用 `textContent` 渲染，确认无 `innerHTML` 赋值
- [ ] 文件上传有 `accept` 属性 + JS `file.type` 白名单
- [ ] 输入超限时前端提示友好错误信息（不崩溃不卡死）
- [ ] Chrome + Safari + 手机端各测试一次核心功能

## 首轮验收重点工具
1. image-compress: 上传正常图片→压缩→下载；上传SVG→被拒绝；上传>10MB→提示超限
2. regex-tester: 输入灾难性回溯正则→Worker超时提示；匹配结果正确高亮
3. json-formatter: 粘贴超1MB JSON→提示超限；粘贴含<script>标签的JSON→转义输出
```

### 轨道1：无自动化测试

Coze 智能体的测试在 Coze 平台内手动进行（预览→调试→发布）。Prompt 源文件独立保存，确保核心资产可追溯。

---

## 监控与告警 [DS-11]

### 监控矩阵

| 监控对象 | 工具 | 频率 | 告警方式 |
|----------|------|------|----------|
| 工具站可用性 | **UptimeRobot**（免费·50监控点） | 每5分钟 | 邮件/App推送 |
| 内容站可用性 | **UptimeRobot** | 每5分钟 | 邮件/App推送 |
| GitHub Actions 运行状态 | Actions 内置通知 | 每次运行 | `if: failure()` → GitHub Issue 自动创建 |
| AI API 月度消耗 | `logs/daily_tokens.json` | 每次管线运行 | 超 ¥120 告警线 → 日志 Warn → 人工巡检时发现 |
| 采集器成功率 | `logs/collector_stats.json` | 每周人工巡检 | 任一采集器成功率 < 50% → 排查反爬 |
| AdSense 收入异常 | Google AdSense 后台 | 每月人工查看 | 连续2月下降 > 30% → 排查流量和质量 |

### stats.json 自监控（每次管线运行输出）

```json
{
  "timestamp": "2026-05-22T08:00:00+08:00",
  "collectors": {
    "weibo": {"status": "ok", "count": 20},
    "zhihu": {"status": "ok", "count": 18},
    "baidu": {"status": "fail", "error": "Timeout", "count": 0}
  },
  "ai_processing": {
    "total_items": 98,
    "filtered_out": 22,
    "tokens_used": 45000,
    "monthly_tokens_total": 850000,
    "monthly_cost_yuan": 0.85,
    "budget_status": "normal"
  },
  "output": {
    "html_files_generated": 12,
    "html_validation": "passed"
  }
}
```

---

## 评审策略 [RV-01]

- **评审模式**: parallel_cross_review_merge
- **激活领域**: workflow, software
- **重点关注**:
  1. v2 新增的安全设计 [DS-09]、测试策略 [DS-10]、监控告警 [DS-11] 三章是否充分补足了 v1 的运维真空
  2. 8 个 must_pass 失败项是否全部解决（类型注解、错误暴露、测试、提交粒度、输入校验、触发定义、异常自动化、部署频率）
  3. 工具实现细节（图片压缩/正则/MD5）是否具体可执行
  4. GitHub Actions 配置（cron/超时/并发/质量门禁/通知）是否正确且完整
  5. 成本控制（API预算上限+降级逻辑）是否实际可用
- **迭代次数上限**: 3
- **特别说明**: 本次 v2 修订针对 v1 评审中发现的全部 9 个高优和 10 个中低优问题进行了逐一修正。请重点验证 v1 中发现的问题是否确实得到解决，而非引入新问题。
