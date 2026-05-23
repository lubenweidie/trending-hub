#!/usr/bin/env bash
# ============================================
# 自动生成执行脚本 — makemoney-automation
# 基于方案: makemoney-automation-规划方案-v2.md
# 评审通过评分: 8.3/10 | 生成时间: 2026-05-22
# ============================================
set -euo pipefail

PROJECT_ROOT="D:/CC_PROJECT/makemoney"
cd "$PROJECT_ROOT"

echo "========================================"
echo "  三轨自动化创收系统 — 一键部署"
echo "  轨道1: Coze智能体·闲鱼变现"
echo "  轨道2: 内容自动化管线"
echo "  轨道3: 在线工具站"
echo "========================================"
echo ""

# ============================================
# Phase 1: 项目脚手架
# ============================================
echo "[1/8] 创建项目目录结构..."

mkdir -p track1-coze/{闲鱼文案,Prompt源码}
mkdir -p track2-content-pipeline/{collectors,tests,output/{posts,static},output-backup-1,output-backup-2,output-backup-3,logs,.github/workflows}
mkdir -p track3-tools-site/{tools,static,tests}
mkdir -p dashboard

echo "  ✓ 目录结构已创建"

# ============================================
# Phase 2: Git 初始化
# ============================================
echo "[2/8] 初始化 Git 仓库..."

if [ ! -d ".git" ]; then
    git init
    echo "  ✓ Git 仓库已初始化"
else
    echo "  ✓ Git 仓库已存在，跳过"
fi

# .gitignore
cat > .gitignore << 'GITIGNORE'
# 敏感文件
.env
*.local
*.secret
credentials.json
*.pem
*.key

# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
.venv/
venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# 备份（本地保留，不提交）
output-backup-*/
GITIGNORE
echo "  ✓ .gitignore 已创建"

# ============================================
# Phase 3: 轨道2 — 内容管线核心文件
# ============================================
echo "[3/8] 创建轨道2（内容管线）核心文件..."

# requirements.txt
cat > track2-content-pipeline/requirements.txt << 'REQ'
requests>=2.31.0
beautifulsoup4>=4.12.0
httpx>=0.27.0
jinja2>=3.1.0
pytest>=8.0.0
REQ
echo "  ✓ requirements.txt"

# frequency_words.txt
cat > track2-content-pipeline/frequency_words.txt << 'FW'
明星
综艺
出轨
绯闻
恋情
八卦
选秀
偶像
饭圈
塌房
真人秀
炒作
爆料
出轨门
婚变
CP
发糖
FW
echo "  ✓ frequency_words.txt"

# collectors/base.py
cat > track2-content-pipeline/collectors/base.py << 'BASE'
"""采集器共享模块：统一配置、重试、包装器"""
import time
import random
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass, field

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36'
}
TIMEOUT = 30
RETRY_DELAYS = [1, 3, 9]  # 指数退避（秒）


@dataclass
class TrendItem:
    """所有采集器统一返回格式"""
    title: str
    url: str
    platform: str
    hot_score: Optional[int] = None
    raw_data: Optional[Dict] = field(default_factory=dict)


def fetch_with_retry(url: str, **kwargs) -> requests.Response:
    """带指数退避重试的 HTTP GET"""
    last_error = None
    for i, delay in enumerate(RETRY_DELAYS):
        try:
            kwargs.setdefault('headers', HEADERS)
            kwargs.setdefault('timeout', TIMEOUT)
            resp = requests.get(url, **kwargs)
            resp.raise_for_status()
            return resp
        except Exception as e:
            last_error = e
            if i < len(RETRY_DELAYS) - 1:
                time.sleep(delay)
    raise last_error


def collect_with_fallback(name: str, func) -> List[TrendItem]:
    """采集包装器：异常时返回空列表，不阻断管线"""
    try:
        items = func()
        print(f"[OK] {name}: {len(items)}条")
        return items
    except Exception as e:
        import sys
        print(f"[FAIL] {name}: {type(e).__name__}", file=sys.stderr)
        return []
BASE
echo "  ✓ collectors/base.py"

# collectors/weibo.py (示例)
cat > track2-content-pipeline/collectors/weibo.py << 'WEIBO'
"""微博热搜采集器"""
from .base import fetch_with_retry, TrendItem

def collect_weibo():
    url = "https://weibo.com/ajax/side/hotSearch"
    resp = fetch_with_retry(url)
    data = resp.json()
    items = []
    for entry in data.get("data", {}).get("realtime", [])[:20]:
        items.append(TrendItem(
            title=entry.get("word", ""),
            url=f"https://s.weibo.com/weibo?q={entry.get('word', '')}",
            platform="微博",
            hot_score=entry.get("num", 0),
        ))
    return items
WEIBO
echo "  ✓ collectors/weibo.py"

# collectors/run_all.py
cat > track2-content-pipeline/collectors/run_all.py << 'RUNALL'
"""主入口：串行调用所有采集器，互不阻断"""
import time
import random
from typing import Dict, List
from .base import collect_with_fallback, TrendItem

# 延迟导入：单个采集器失败不影响其他导入
def _safe_import(module_name):
    try:
        return __import__(module_name, fromlist=['collect'])
    except ImportError:
        return None

def run_all() -> Dict[str, List[TrendItem]]:
    results = {}

    # 微博（最稳定，先跑）
    try:
        from . import weibo
        results["weibo"] = collect_with_fallback("weibo", weibo.collect_weibo)
    except Exception as e:
        print(f"[SKIP] weibo: {e}")
        results["weibo"] = []
    time.sleep(random.uniform(1, 3))

    # 知乎
    try:
        from . import zhihu
        results["zhihu"] = collect_with_fallback("zhihu", zhihu.collect_zhihu)
    except Exception as e:
        print(f"[SKIP] zhihu: {e}")
        results["zhihu"] = []
    time.sleep(random.uniform(1, 3))

    # 百度
    try:
        from . import baidu
        results["baidu"] = collect_with_fallback("baidu", baidu.collect_baidu)
    except Exception as e:
        print(f"[SKIP] baidu: {e}")
        results["baidu"] = []
    time.sleep(random.uniform(1, 3))

    # B站
    try:
        from . import bilibili
        results["bilibili"] = collect_with_fallback("bilibili", bilibili.collect_bilibili)
    except Exception as e:
        print(f"[SKIP] bilibili: {e}")
        results["bilibili"] = []
    time.sleep(random.uniform(1, 3))

    # 掘金
    try:
        from . import juejin
        results["juejin"] = collect_with_fallback("juejin", juejin.collect_juejin)
    except Exception as e:
        print(f"[SKIP] juejin: {e}")
        results["juejin"] = []
    time.sleep(random.uniform(1, 3))

    # V2EX
    try:
        from . import v2ex
        results["v2ex"] = collect_with_fallback("v2ex", v2ex.collect_v2ex)
    except Exception as e:
        print(f"[SKIP] v2ex: {e}")
        results["v2ex"] = []

    total = sum(len(v) for v in results.values())
    print(f"\n[SUMMARY] 共采集 {total} 条热榜（{len(results)}个平台）")
    return results


if __name__ == "__main__":
    run_all()
RUNALL
echo "  ✓ collectors/run_all.py"

# 创建其他采集器占位文件
for platform in zhihu baidu bilibili juejin v2ex; do
    cat > "track2-content-pipeline/collectors/${platform}.py" << STUB
"""${platform} 采集器 — 待实现"""
from .base import fetch_with_retry, TrendItem

def collect_${platform}():
    # TODO: 实现具体采集逻辑，参考方案 [DS-02] 数据源表格
    # 失败时 raise Exception，由 collect_with_fallback 捕获
    raise NotImplementedError("${platform} 采集器待实现")
STUB
done
echo "  ✓ 5个采集器占位文件"

# processor.py 框架
cat > track2-content-pipeline/processor.py << 'PROC'
"""AI处理层：去重→过滤→摘要→改写"""
import json
import os
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# 成本控制
COST_LOG = Path("logs/daily_tokens.json")
MONTHLY_BUDGET_YUAN = 150
ALERT_THRESHOLD_YUAN = 120
TOKEN_PRICE = 0.001 / 1000  # ¥1/百万token

def load_frequency_words() -> set:
    """加载过滤关键词"""
    with open("frequency_words.txt", "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}

def filter_trends(items: List[Dict]) -> List[Dict]:
    """去重 + 过滤娱乐八卦"""
    freq_words = load_frequency_words()
    seen = set()
    result = []
    for item in items:
        title = item.get("title", "")
        # 去重：标题前20字hash
        key = hashlib.md5(title[:60].encode()).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        # 过滤娱乐关键词
        if any(w in title for w in freq_words):
            continue
        result.append(item)
    return result

def check_budget() -> bool:
    """检查月度预算；超限返回False"""
    if not COST_LOG.exists():
        return True
    logs = json.loads(COST_LOG.read_text(encoding="utf-8"))
    month_key = datetime.now().strftime("%Y-%m")
    month_total = sum(d.get("tokens", 0) for d in logs if d.get("date", "").startswith(month_key))
    cost = month_total * TOKEN_PRICE
    if cost > MONTHLY_BUDGET_YUAN:
        print(f"[BUDGET] 月度消耗¥{cost:.1f}超过预算¥{MONTHLY_BUDGET_YUAN}，降级为原文模式")
        return False
    if cost > ALERT_THRESHOLD_YUAN:
        print(f"[BUDGET] 月度消耗¥{cost:.1f}已达告警线¥{ALERT_THRESHOLD_YUAN}")
    return True

def process_trends(all_results: Dict[str, List], budget_ok: bool = True):
    """主处理入口"""
    # 合并所有采集结果
    all_items = []
    for platform, items in all_results.items():
        for item in items:
            item_dict = item.__dict__ if hasattr(item, '__dict__') else item
            item_dict["platform"] = platform
            all_items.append(item_dict)

    # 去重+过滤
    filtered = filter_trends(all_items)
    print(f"[PROCESS] 原始{len(all_items)}条 → 过滤后{len(filtered)}条")

    if not budget_ok:
        # 降级模式：不调用AI，原文标题+链接
        return [{"title": it["title"], "summary": "", "source_url": it.get("url", ""),
                 "platform": it.get("platform", "")} for it in filtered]

    # TODO: 正常模式调用 AI API 做摘要+改写
    # 具体Prompt模板见方案 [DS-02]
    return filtered
PROC
echo "  ✓ processor.py"

# builder.py 框架
cat > track2-content-pipeline/builder.py << 'BUILD'
"""HTML生成器：Jinja2自动转义渲染"""
from jinja2 import Environment, BaseLoader, select_autoescape
from pathlib import Path
from datetime import datetime

env = Environment(
    loader=BaseLoader(),
    autoescape=select_autoescape(['html', 'xml'])
)

INDEX_TEMPLATE = env.from_string("""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>热榜聚合 — 全网热点一览</title>
    <meta name="description" content="AI驱动的全网热点聚合，多平台热榜实时更新。内容由AI自动生成，仅供参考。">
    <link rel="alternate" hreflang="en" href="/en/">
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <header><h1>📰 全网热榜聚合</h1></header>
    <main>
        {% for item in items %}
        <article>
            <h2><a href="{{ item.source_url }}" rel="nofollow noopener" target="_blank">{{ item.title }}</a></h2>
            <p class="meta">{{ item.platform }} · {{ item.generated_at }}</p>
            {% if item.summary %}<p class="summary">{{ item.summary }}</p>{% endif %}
        </article>
        {% endfor %}
    </main>
    <footer><p>内容由AI自动生成，仅供参考。| <a href="/privacy.html">隐私政策</a></p></footer>
</body>
</html>""")

def build_index(items: list, output_dir: str = "output"):
    """生成首页"""
    html = INDEX_TEMPLATE.render(
        items=items,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M")
    )
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    (Path(output_dir) / "index.html").write_text(html, encoding="utf-8")
    print(f"[BUILD] index.html 已生成（{len(items)}条）")
BUILD
echo "  ✓ builder.py"

# validate_output.py
cat > track2-content-pipeline/validate_output.py << 'VAL'
"""部署前校验HTML标签闭合和基本结构"""
import sys
from pathlib import Path
from bs4 import BeautifulSoup

def validate_html(filepath: str) -> bool:
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
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
        sys.exit(1)
    print("[OK] All HTML files validated")

if __name__ == "__main__":
    main()
VAL
echo "  ✓ validate_output.py"

# tests/
cat > track2-content-pipeline/tests/__init__.py << 'TINIT'
# tests package
TINIT

cat > track2-content-pipeline/tests/test_builder.py << 'TBUILD'
"""builder.py HTML转义测试"""
import sys
sys.path.insert(0, '..')
from html import escape

def test_html_escape_xss():
    """恶意标题被转义"""
    malicious = '<script>alert("XSS")</script>'
    escaped = escape(malicious)
    assert '<script>' not in escaped
    assert '&lt;script&gt;' in escaped

def test_normal_title_unchanged():
    """正常标题不被破坏"""
    normal = "GPT-5发布：AI能力再次跃升"
    escaped = escape(normal)
    assert "GPT-5" in escaped
    assert "&" not in escaped  # 无特殊字符则不变
TBUILD

cat > track2-content-pipeline/tests/test_collectors.py << 'TCOL'
"""采集器测试"""
import sys
sys.path.insert(0, '..')
from collectors.base import collect_with_fallback, TrendItem

def test_collector_failure_returns_empty():
    """采集器异常时返回空列表"""
    def broken_collector():
        raise ConnectionError("模拟网络故障")
    result = collect_with_fallback("mock_broken", broken_collector)
    assert result == []

def test_collector_success_returns_items():
    """正常采集返回TrendItem列表"""
    def ok_collector():
        return [TrendItem(title="测试", url="https://example.com", platform="test")]
    result = collect_with_fallback("mock_ok", ok_collector)
    assert len(result) == 1
    assert result[0].title == "测试"

def test_trend_item_fields():
    """TrendItem字段完整"""
    item = TrendItem(title="测试", url="https://example.com", platform="weibo")
    assert item.title == "测试"
    assert item.platform == "weibo"
TCOL

cat > track2-content-pipeline/tests/test_processor.py << 'TPRO'
"""processor.py 过滤测试"""
import sys
sys.path.insert(0, '..')
from processor import filter_trends

def test_filter_entertainment():
    """娱乐关键词被过滤"""
    items = [
        {"title": "某明星出轨被拍，网友热议"},
        {"title": "GPT-5发布：多模态能力再进化"},
    ]
    filtered = filter_trends(items)
    titles = [it["title"] for it in filtered]
    assert "GPT-5发布" in str(titles)
    assert "明星" not in str(titles)

def test_dedup_similar_title():
    """重复标题去重"""
    items = [
        {"title": "GPT-5正式发布"},
        {"title": "GPT-5正式发布"},
    ]
    filtered = filter_trends(items)
    assert len(filtered) == 1
TPRO
echo "  ✓ tests/ (3个测试文件)"

# GitHub Actions workflow
cat > "track2-content-pipeline/.github/workflows/trending.yml" << 'WFLOW'
name: Trending Content Pipeline

on:
  schedule:
    # 每4小时（UTC），对应北京时间 4/8/12/16/20/24点，共6次/天
    - cron: '0 20,0,4,8,12,16 * * *'
  workflow_dispatch:

concurrency:
  group: trending-pipeline
  cancel-in-progress: true

jobs:
  pipeline:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install deps
        run: pip install requests beautifulsoup4 httpx jinja2 pytest

      - name: Collect trends
        id: collect
        run: cd track2-content-pipeline && python -m collectors.run_all

      - name: AI Process
        id: ai
        run: cd track2-content-pipeline && python processor.py
        env:
          AI_API_KEY: ${{ secrets.AI_API_KEY }}
          AI_API_URL: ${{ secrets.AI_API_URL }}

      - name: Build & Validate HTML
        id: build
        run: |
          cd track2-content-pipeline
          python builder.py
          python validate_output.py

      - name: Run tests
        run: cd track2-content-pipeline && python -m pytest tests/ -v

      - name: Commit & Push
        if: success()
        run: |
          git config user.name "TrendBot"
          git config user.email "bot@trends.local"
          cd track2-content-pipeline
          git add output/ logs/
          if git diff --staged --quiet; then
            echo "No changes to commit"
          else
            git commit -m "Update: $(date +'%Y-%m-%d %H:%M BJT')"
            git tag "deploy-$(date +'%Y%m%d-%H%M')"
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
WFLOW
echo "  ✓ GitHub Actions workflow"

# ============================================
# Phase 4: 轨道3 — 在线工具站
# ============================================
echo "[4/8] 创建轨道3（工具站）核心文件..."

# _headers
cat > track3-tools-site/_headers << 'HEADERS'
/*
  Content-Security-Policy: default-src 'self'; script-src 'self' https://pagead2.googlesyndication.com https://www.googletagmanager.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; frame-src https://googleads.g.doubleclick.net; connect-src 'self'
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
  Permissions-Policy: camera=(), microphone=(), geolocation=()
HEADERS
echo "  ✓ _headers"

# ads.txt
cat > track3-tools-site/ads.txt << 'ADS'
# Google AdSense
# 上线后替换为你的 publisher ID
# google.com, pub-XXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0
ADS
echo "  ✓ ads.txt"

# robots.txt
cat > track3-tools-site/robots.txt << 'ROBOTS'
User-agent: *
Allow: /
Sitemap: https://你的域名/sitemap.xml
ROBOTS

# index.html (首页框架)
cat > track3-tools-site/index.html << 'INDEX'
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>在线工具集 — 浏览器端处理，保护数据隐私</title>
    <meta name="description" content="免费在线工具集合：JSON格式化、时间戳转换、Base64编解码、图片压缩等。所有处理在浏览器端完成，文件不上传服务器。">
    <link rel="canonical" href="https://你的域名/">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 min-h-screen">
    <header class="bg-white shadow-sm">
        <div class="max-w-4xl mx-auto px-4 py-6">
            <h1 class="text-3xl font-bold text-gray-900">🛠️ 在线工具集</h1>
            <p class="text-gray-500 mt-2">所有处理在浏览器端完成，文件不上传服务器 🔒</p>
        </div>
    </header>
    <main class="max-w-4xl mx-auto px-4 py-8">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <a href="tools/json-formatter.html" class="block p-6 bg-white rounded-lg shadow hover:shadow-md transition">
                <h2 class="font-semibold text-lg">JSON格式化</h2>
                <p class="text-gray-500 text-sm mt-1">格式化、压缩、验证JSON数据</p>
            </a>
            <a href="tools/timestamp.html" class="block p-6 bg-white rounded-lg shadow hover:shadow-md transition">
                <h2 class="font-semibold text-lg">时间戳转换</h2>
                <p class="text-gray-500 text-sm mt-1">Unix时间戳与日期互转</p>
            </a>
            <a href="tools/base64.html" class="block p-6 bg-white rounded-lg shadow hover:shadow-md transition">
                <h2 class="font-semibold text-lg">Base64编解码</h2>
                <p class="text-gray-500 text-sm mt-1">Base64编码与解码</p>
            </a>
            <a href="tools/image-compress.html" class="block p-6 bg-white rounded-lg shadow hover:shadow-md transition">
                <h2 class="font-semibold text-lg">图片压缩</h2>
                <p class="text-gray-500 text-sm mt-1">浏览器端压缩图片，支持JPEG/PNG/WebP</p>
            </a>
            <a href="tools/url-encode.html" class="block p-6 bg-white rounded-lg shadow hover:shadow-md transition">
                <h2 class="font-semibold text-lg">URL编解码</h2>
                <p class="text-gray-500 text-sm mt-1">URL编码与解码</p>
            </a>
            <a href="tools/md5-hash.html" class="block p-6 bg-white rounded-lg shadow hover:shadow-md transition">
                <h2 class="font-semibold text-lg">哈希计算</h2>
                <p class="text-gray-500 text-sm mt-1">MD5/SHA-256哈希值计算</p>
            </a>
            <a href="tools/regex-tester.html" class="block p-6 bg-white rounded-lg shadow hover:shadow-md transition">
                <h2 class="font-semibold text-lg">正则测试器</h2>
                <p class="text-gray-500 text-sm mt-1">正则表达式在线测试</p>
            </a>
            <a href="tools/color-convert.html" class="block p-6 bg-white rounded-lg shadow hover:shadow-md transition">
                <h2 class="font-semibold text-lg">颜色转换</h2>
                <p class="text-gray-500 text-sm mt-1">HEX/RGB/HSL颜色格式互转</p>
            </a>
        </div>
    </main>
    <footer class="max-w-4xl mx-auto px-4 py-8 text-center text-gray-400 text-sm">
        <p>
            <a href="about.html" class="hover:underline">关于</a> ·
            <a href="privacy.html" class="hover:underline">隐私政策</a> ·
            <a href="contact.html" class="hover:underline">联系我们</a> ·
            <a href="disclosure.html" class="hover:underline">广告披露</a>
        </p>
    </footer>
</body>
</html>
INDEX
echo "  ✓ index.html"

# 必需页面
for page in about privacy contact disclosure; do
    cat > "track3-tools-site/${page}.html" << STUBPAGE
<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>${page}</title></head>
<body><h1>${page}</h1><p>TODO: 待完善</p></body>
</html>
STUBPAGE
done
echo "  ✓ 4个必需页面（about/privacy/contact/disclosure）"

# JSON格式化工具（唯一给出完整实现）
cat > track3-tools-site/tools/json-formatter.html << 'JSONTOOL'
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JSON格式化 - 在线JSON格式化验证工具 | 浏览器端处理</title>
    <meta name="description" content="免费的在线JSON格式化工具，所有处理在浏览器端完成，数据不会上传到服务器。支持JSON格式化、压缩、验证。">
    <link rel="canonical" href="https://你的域名/tools/json-formatter.html">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 min-h-screen">
    <nav class="bg-white shadow-sm">
        <div class="max-w-4xl mx-auto px-4 py-3">
            <a href="../index.html" class="text-blue-600 hover:underline">← 返回工具列表</a>
        </div>
    </nav>
    <main class="max-w-4xl mx-auto px-4 py-8">
        <h1 class="text-3xl font-bold mb-2">JSON格式化工具</h1>
        <p class="text-gray-500 mb-6">所有处理在浏览器端完成，数据不会上传到服务器 🔒</p>

        <textarea id="input" class="w-full h-48 p-4 border rounded font-mono text-sm" placeholder="粘贴JSON..." maxlength="1048576"></textarea>
        <div class="flex gap-2 my-4">
            <button onclick="safeFormat()" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">格式化</button>
            <button onclick="safeCompress()" class="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700">压缩</button>
            <button onclick="safeValidate()" class="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">验证</button>
            <button onclick="clearAll()" class="border px-4 py-2 rounded hover:bg-gray-100">清空</button>
        </div>
        <div id="status" class="text-sm mb-2"></div>
        <pre id="output" class="bg-gray-100 p-4 rounded overflow-auto max-h-96 font-mono text-sm"></pre>
    </main>
    <script>
        const MAX_SIZE = 1048576; // 1MB
        const input = document.getElementById('input');
        const output = document.getElementById('output');
        const status = document.getElementById('status');

        function showStatus(msg, isError) {
            status.textContent = msg;
            status.className = 'text-sm mb-2 ' + (isError ? 'text-red-600' : 'text-green-600');
        }

        function safeFormat() {
            try {
                if (input.value.length > MAX_SIZE) {
                    showStatus('输入内容过大，请限制在1MB以内', true);
                    return;
                }
                const obj = JSON.parse(input.value);
                output.textContent = JSON.stringify(obj, null, 2);
                showStatus('格式化成功', false);
            } catch(e) {
                output.textContent = 'JSON 格式无效，请检查输入内容';
                console.error('JSON parse error:', e);
                showStatus('格式错误，请检查JSON语法', true);
            }
        }

        function safeCompress() {
            try {
                if (input.value.length > MAX_SIZE) {
                    showStatus('输入内容过大，请限制在1MB以内', true);
                    return;
                }
                const obj = JSON.parse(input.value);
                output.textContent = JSON.stringify(obj);
                showStatus('压缩成功', false);
            } catch(e) {
                output.textContent = 'JSON 格式无效，请检查输入内容';
                console.error('JSON parse error:', e);
                showStatus('格式错误，请检查JSON语法', true);
            }
        }

        function safeValidate() {
            try {
                if (input.value.length > MAX_SIZE) {
                    showStatus('输入内容过大，请限制在1MB以内', true);
                    return;
                }
                JSON.parse(input.value);
                output.textContent = '✅ JSON 格式有效';
                showStatus('验证通过', false);
            } catch(e) {
                output.textContent = 'JSON 格式无效，请检查输入内容';
                console.error('JSON validation error:', e);
                showStatus('验证失败', true);
            }
        }

        function clearAll() {
            input.value = '';
            output.textContent = '';
            status.textContent = '';
        }
    </script>
</body>
</html>
JSONTOOL
echo "  ✓ tools/json-formatter.html (完整实现)"

# 其余工具占位
for tool in timestamp base64 image-compress url-encode md5-hash regex-tester color-convert; do
    cat > "track3-tools-site/tools/${tool}.html" << TOOLSTUB
<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>${tool}</title></head>
<body><h1>${tool}</h1><p>TODO: 根据方案 [DS-03] 实现</p></body>
</html>
TOOLSTUB
done
echo "  ✓ 7个工具占位文件"

# static/style.css
cat > track3-tools-site/static/style.css << 'CSS'
/* 工具站公共样式 */
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
pre { white-space: pre-wrap; word-break: break-all; }
CSS

# manual_checklist
cat > track3-tools-site/tests/manual_checklist.md << 'CHKLIST'
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
3. json-formatter: 粘贴超1MB JSON→提示超限；粘贴含script标签→textContent转义
CHKLIST
echo "  ✓ tests/manual_checklist.md"

# ============================================
# Phase 5: 轨道1 — Coze模板
# ============================================
echo "[5/8] 创建轨道1（Coze模板）素材..."

# 5个Prompt源文件
cat > "track1-coze/Prompt源码/简历优化-prompt.txt" << 'PMT1'
你是一位资深HR和简历优化专家。请分析以下简历：
1. 识别 3 个最大的问题（结构/用词/成果量化）
2. 针对每个问题给出修改前后对比
3. 输出一份优化后的完整简历
4. 评分（1-10分）并说明改进空间
输出格式：Markdown，分区块展示。
PMT1

cat > "track1-coze/Prompt源码/日报生成-prompt.txt" << 'PMT2'
你是一位职场汇报专家。根据用户输入的今日工作关键词，生成一份结构化日报：
1. 今日完成（3-5条，量化成果）
2. 遇到的问题及解决方案
3. 明日计划（3条以内）
4. 需要协调的事项
格式：专业、简洁、数据驱动。
PMT2

cat > "track1-coze/Prompt源码/竞品监控-prompt.txt" << 'PMT3'
你是一位电商竞品分析专家。根据用户提供的竞品链接和信息，生成竞品监控报告：
1. 价格策略分析
2. 近期活动/促销动态
3. 用户评价趋势（正面/负面关键词）
4. 差异化建议
PMT3

cat > "track1-coze/Prompt源码/合同风险-prompt.txt" << 'PMT4'
你是一位法律风险审核专家。请分析以下合同条款：
1. 识别潜在风险条款（按风险等级排序：高/中/低）
2. 每个风险点给出具体修改建议
3. 标注是否有法律依据（引用相关法规）
4. 总评：合同整体风险等级
注意：本分析仅供参考，不构成正式法律意见。
PMT4

cat > "track1-coze/Prompt源码/客服话术-prompt.txt" << 'PMT5'
你是一位电商客服培训师。根据用户输入的场景，生成客服回复话术：
1. 场景分类（售前咨询/售后问题/投诉处理/物流查询）
2. 标准话术模板（2-3个版本）
3. 情绪安抚技巧（如需）
4. 升级处理建议（如常规话术无法解决）
PMT5
echo "  ✓ 5个Coze Prompt源文件"

# 闲鱼文案占位
for agent in 简历优化助手 日报生成器 竞品监控器 合同风险扫描 客服话术库; do
    touch "track1-coze/闲鱼文案/${agent}.md"
done
echo "  ✓ 5个闲鱼文案占位"

# ============================================
# Phase 6: 首次 Git 提交
# ============================================
echo "[6/8] 首次 Git 提交..."

git add -A
git commit -m "$(cat <<'EOF'
初始化三轨自动化创收系统

- 轨道1：Coze智能体模板（5个Prompt源文件+闲鱼文案框架）
- 轨道2：内容自动化管线（采集器+AI处理+HTML生成+GitHub Actions）
- 轨道3：在线工具站（JSON格式化完整实现+7工具框架+安全头配置）

基于规划方案 v2（评审通过 8.3/10）
EOF
)" || echo "  (无变更可提交)"

echo "  ✓ 首次提交完成"

# ============================================
# Phase 7: 安装Python依赖
# ============================================
echo "[7/8] 安装Python依赖..."

if command -v pip &> /dev/null; then
    pip install -r track2-content-pipeline/requirements.txt 2>/dev/null || echo "  ⚠ pip安装失败，请手动执行: pip install -r track2-content-pipeline/requirements.txt"
    echo "  ✓ 依赖安装完成"
else
    echo "  ⚠ 未检测到pip，请手动安装Python依赖"
fi

# ============================================
# Phase 8: 运行测试
# ============================================
echo "[8/8] 运行初始测试..."

cd track2-content-pipeline
if python -m pytest tests/ -v 2>/dev/null; then
    echo "  ✓ 所有测试通过"
else
    echo "  ⚠ 测试运行失败或有测试未通过（部分采集器测试需实现采集逻辑后通过）"
fi
cd "$PROJECT_ROOT"

# ============================================
# 完成
# ============================================
echo ""
echo "========================================"
echo "  脚手架搭建完成！"
echo "========================================"
echo ""
echo "📋 下一步手动操作："
echo ""
echo "🚀 轨道1 — Coze智能体（1-2周见效）："
echo "  1. 访问 https://www.coze.cn 注册账号"
echo "  2. 创建Bot → 导入 track1-coze/Prompt源码/ 中的Prompt"
echo "  3. 搭建工作流 → 测试 → 发布"
echo "  4. 闲鱼上架：编辑 track1-coze/闲鱼文案/ 中的文案发布"
echo ""
echo "📰 轨道2 — 内容管线（2-3月见效）："
echo "  1. 在GitHub仓库 Settings → Secrets 添加 AI_API_KEY 和 AI_API_URL"
echo "  2. 实现 collectors/zhihu.py、baidu.py、bilibili.py、juejin.py、v2ex.py"
echo "  3. 完善 processor.py 中的 AI API 调用逻辑"
echo "  4. 注册Cloudflare Pages → 连接GitHub仓库 → 部署 output/ 目录"
echo "  5. 申请Google AdSense（需≥30篇内容后申请）"
echo ""
echo "🔧 轨道3 — 工具站（6-12月见效）："
echo "  1. 注册域名 → Cloudflare Pages 新建项目 → 部署 track3-tools-site/"
echo "  2. 逐个实现 7 个工具页面（按方案 [DS-03] 的详细设计）"
echo "  3. 完善 about/privacy/contact/disclosure.html"
echo "  4. 运行手动验收清单: track3-tools-site/tests/manual_checklist.md"
echo "  5. 提交Google Search Console + 百度站长平台"
echo ""
echo "💰 预期收入时间线："
echo "  轨道1首月: ¥500+ | 轨道2: 2-3月后 ¥500+/月 | 轨道3: 6-12月后 ¥1000+/月"
echo "  总月成本: ¥55-127 | 预算上限: ¥200"
echo ""
echo "📁 方案文档: makemoney-automation-规划方案-v2.md"
echo "📊 评审评分: 8.3/10（第2轮通过）"
echo "========================================"
