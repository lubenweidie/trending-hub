"""热点主题筛选与保存 —— 不在此阶段做 AI 扩写，扩写统一在发布时由 ENRICH_PROMPT 完成"""
import config_loader  # noqa: E402,F401
import random
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict

OUTPUT_DIR = Path("output/articles")
PUBLISHED_DIR = OUTPUT_DIR / "published"

# G25: 命名常量替代魔法数字
MIN_TITLE_LENGTH = 5
MAX_TITLE_LENGTH = 80
EMPTY_SUMMARY_MARKER = "暂无详细信息"


def _published_source_urls() -> set:
    urls: set[str] = set()
    if not PUBLISHED_DIR.exists():
        return urls
    for f in PUBLISHED_DIR.glob("*/*.md"):
        text = f.read_text(encoding="utf-8")
        m = re.search(r'原文：\[.*?\]\((https?://[^)]+)\)', text)
        if m:
            urls.add(m.group(1))
    return urls


def _extract_url(topic: Dict) -> str:
    return topic.get("source_url") or topic.get("url", "")


def select_best_items(topics: List[Dict], max_count: int = 2) -> List[Dict]:
    published_urls = _published_source_urls()
    # 按平台分组，每个平台取摘要最长的一条，保证来源多样性
    platform_best: dict[str, tuple[int, Dict]] = {}
    for topic in topics:
        summary = topic.get("summary", "")
        title = topic.get("title", "")
        if not summary or summary == EMPTY_SUMMARY_MARKER:
            continue
        if len(title) < MIN_TITLE_LENGTH or len(title) > MAX_TITLE_LENGTH:
            continue
        url = _extract_url(topic)
        if url and url in published_urls:
            continue
        platform = topic.get("platform", "unknown")
        score = len(summary)
        if platform not in platform_best or score > platform_best[platform][0]:
            platform_best[platform] = (score, topic)

    diverse_pool = [topic for _, topic in platform_best.values()]
    if not diverse_pool:
        return []

    selected = random.sample(diverse_pool, min(max_count, len(diverse_pool)))
    if len(selected) == 1 and len(diverse_pool) > 1:
        picked = selected[0]
        platforms = [t.get('platform','?') for t in diverse_pool]
        print(f"[TopicSaver] 平台分层筛选: 候选平台 {platforms} → 随机选中: {picked.get('platform','')} · {picked['title'][:30]}...")
    return selected


def save_topic(topic: Dict, index: int) -> str:
    title = topic.get("title", "无标题")
    summary = topic.get("summary", "")
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    safe_title = re.sub(r'[\\/:*?"<>|]', '', title)[:30].strip()
    slug = f"{safe_title}-{ts}"
    article_dir = OUTPUT_DIR / slug
    article_dir.mkdir(parents=True, exist_ok=True)
    source_url = _extract_url(topic)

    md_content = f"""# {title}

> 来源：{topic.get('platform', '')} | 原文：[{topic.get('title', '')}]({source_url})
> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}
> 摘要：{summary}

（发布时基于源内容 AI 扩写）
"""
    (article_dir / f"{slug}.md").write_text(md_content, encoding="utf-8")
    print(f"[TopicSaver] 已保存: {slug}")
    return slug


def save_topics(topics: List[Dict], daily_limit: int = 2) -> List[str]:
    print(f"[TopicSaver] 从 {len(topics)} 条热点中筛选 {daily_limit} 条...")
    selected = select_best_items(topics, daily_limit)

    if not selected:
        print("[TopicSaver] 无适合扩写的热点，跳过")
        return []

    print(f"[TopicSaver] 选中 {len(selected)} 条，保存主题...")
    slugs = []
    for i, topic in enumerate(selected):
        print(f"[TopicSaver]   ({i+1}/{len(selected)}) {topic['title'][:40]}...")
        slug = save_topic(topic, i + 1)
        slugs.append(slug)

    print(f"[TopicSaver] 完成：保存 {len(slugs)} 个主题")
    return slugs
