"""百家号文章扩写模块：热点摘要 → 300-500字原创文章"""
import json
import os
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = os.environ.get("AI_API_URL") or "https://api.deepseek.com/v1/chat/completions"
AI_ENABLED = bool(DEEPSEEK_API_KEY)
OUTPUT_DIR = Path("output/articles")

ARTICLE_PROMPT = """你是一位专业的自媒体作者。请根据以下热点信息，撰写一篇300-500字的原创短文，适合发布在百家号等内容平台。

要求：
1. 标题要有吸引力但不过度夸张（15-25字），与原标题有差异化
2. 正文结构：开篇引入背景（1-2句）→ 核心内容陈述（3-4句）→ 补充细节或影响（1-2句）→ 收尾
3. 语言客观、事实性，不煽动情绪、不标题党
4. 必须是原创表达，不要直接复制任何来源的原句
5. 不添加个人评论，只陈述事实

热点信息：
标题：{title}
摘要：{summary}
来源平台：{platform}

返回JSON格式：
{{"title": "改写后的标题", "content": "正文内容（纯文本，用\\n分段）"}}
"""


def select_best_items(items: List[Dict], max_count: int = 2) -> List[Dict]:
    candidates = []
    for item in items:
        summary = item.get("summary", "")
        title = item.get("title", "")
        if not summary or summary == "暂无详细信息":
            continue
        if len(title) < 5 or len(title) > 80:
            continue
        score = len(summary)
        candidates.append((score, item))
    candidates.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in candidates[:max_count]]


def write_article(item: Dict) -> Dict | None:
    if not AI_ENABLED:
        return None

    prompt = ARTICLE_PROMPT.format(
        title=item.get("title", ""),
        summary=item.get("summary", ""),
        platform=item.get("platform", "")
    )

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个专业的自媒体内容创作者，擅长撰写原创、客观的热点文章。"},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 800,
        "temperature": 0.7,
        "response_format": {"type": "json_object"}
    }

    for attempt in range(3):
        try:
            resp = requests.post(
                DEEPSEEK_API_URL,
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=90
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)
            if resp.status_code == 429:
                print(f"[ArticleWriter] 速率限制，等待 {(attempt+1)*10}s...")
                time.sleep((attempt + 1) * 10)
                continue
            print(f"[ArticleWriter] API错误 {resp.status_code}: {resp.text[:200]}")
            if attempt < 2:
                time.sleep(3)
        except Exception as e:
            print(f"[ArticleWriter] 请求异常: {e}")
            if attempt < 2:
                time.sleep(5)
    return None


def save_article(article: Dict, index: int, source_item: Dict):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    title = article.get("title", "无标题")
    content = article.get("content", "")

    date_str = datetime.now().strftime("%Y%m%d")
    slug = f"{date_str}-{index:02d}"

    md_content = f"""# {title}

> 来源：{source_item.get('platform', '')} | 原文：[{source_item.get('title', '')}]({source_item.get('source_url', '')})
> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}

{content}
"""
    (OUTPUT_DIR / f"{slug}.md").write_text(md_content, encoding="utf-8")

    txt_path = OUTPUT_DIR / f"{slug}.txt"
    txt_path.write_text(f"{title}\n\n{content}", encoding="utf-8")

    print(f"[ArticleWriter] 已保存: {slug}")
    return slug


def generate_articles(items: List[Dict], daily_limit: int = 2) -> List[str]:
    if not AI_ENABLED:
        print("[ArticleWriter] 未配置 AI API Key，跳过文章生成")
        return []

    print(f"[ArticleWriter] 从 {len(items)} 条热点中筛选 {daily_limit} 条...")
    selected = select_best_items(items, daily_limit)

    if not selected:
        print("[ArticleWriter] 无适合扩写的热点，跳过")
        return []

    print(f"[ArticleWriter] 选中 {len(selected)} 条，开始扩写...")

    slugs = []
    for i, item in enumerate(selected):
        print(f"[ArticleWriter]   ({i+1}/{len(selected)}) {item['title'][:40]}...")
        article = write_article(item)
        if article:
            slug = save_article(article, i + 1, item)
            slugs.append(slug)
        else:
            print(f"[ArticleWriter]   扩写失败，跳过")
        if i < len(selected) - 1:
            time.sleep(1)

    print(f"[ArticleWriter] 完成：生成 {len(slugs)} 篇文章")
    return slugs
