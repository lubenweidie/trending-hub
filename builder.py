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
