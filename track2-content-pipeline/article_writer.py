"""热点主题筛选与保存 —— 不在此阶段做 AI 扩写，扩写统一在发布时由 ENRICH_PROMPT 完成"""
import config_loader  # noqa: E402,F401
import random
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict

OUTPUT_DIR = Path("output/articles")
PUBLISHED_DIR = OUTPUT_DIR / "published"

MIN_TITLE_LENGTH = 5
MAX_TITLE_LENGTH = 80

# 话题类型权重 — 数据驱动 + 内容矩阵多元化
TOPIC_WEIGHTS = {
    # 一级：政策民生 — 百家号验证最高阅读量（1586阅读）
    "政策": 12, "法规": 12, "国务院": 12, "官方": 10, "政府": 10, "通知": 9,
    "民生": 10, "医保": 10, "养老": 10, "住房": 10, "补贴": 10, "教育": 8,
    # 二级：经济钱袋子
    "经济": 8, "楼市": 8, "房贷": 8, "就业": 8, "工资": 8, "物价": 8,
    "汽车": 6, "新能源": 6, "消费": 6, "股市": 5, "理财": 5,
    # 三级：社会科技
    "社会": 6, "科技": 5, "AI": 5, "人工智能": 5, "安全": 5, "环境": 5, "健康": 5,
    # 四级：娱乐八卦 — 数据验证有稳定流量（林俊杰17阅读/芒果12阅读）
    "娱乐": 4, "明星": 4, "综艺": 3, "电影": 3, "音乐": 3, "八卦": 3,
    # 三级半：奇闻趣事 — 数据验证（欧洲50度19阅读/山姆跑路13阅读/国台办笑场24阅读）
    "奇闻": 10, "趣事": 9, "离谱": 8, "震惊": 7, "奇葩": 8, "笑场": 8,
    "争议": 7, "翻车": 7, "删": 5, "闹剧": 6, "真相": 6,
    # 六级：体育游戏
    "体育": 3, "比赛": 3, "游戏": 2, "电竞": 2,
}

# 低价值惩罚 — 仅针对纯水标题，不是普通娱乐
LOW_VALUE_PATTERNS = ["整容", "医美翻车", "网红塌房"]

# 来源平台可信度权重
PLATFORM_CREDIBILITY = {
    "people_rm": 10, "xinhuanet": 10,  # 新华网/人民日报 = 权威来源
    "baidu": 5, "weibo": 2, "zhihu": 1,
}

# 发布平台权重修饰器（乘法，叠加在 TOPIC_WEIGHTS 上）
# 百家号：政策民生/经济提权，娱乐/奇闻降权
# 今日头条：娱乐/奇闻提权，政策降权
PLATFORM_WEIGHT_MODIFIERS = {
    "baijiahao": {
        "政策": 1.5, "法规": 1.5, "国务院": 1.5, "官方": 1.3, "政府": 1.3, "通知": 1.3,
        "民生": 1.3, "医保": 1.3, "养老": 1.3, "住房": 1.3, "补贴": 1.3, "教育": 1.2,
        "经济": 1.3, "楼市": 1.3, "房贷": 1.3, "就业": 1.3, "工资": 1.3, "物价": 1.3,
        "娱乐": 0.5, "明星": 0.5, "综艺": 0.5, "电影": 0.5, "音乐": 0.5, "八卦": 0.4,
        "奇闻": 0.6, "趣事": 0.6, "离谱": 0.5, "震惊": 0.6, "奇葩": 0.5, "笑场": 0.5,
        "争议": 0.7, "翻车": 0.7, "闹剧": 0.6,
    },
    "toutiao": {
        "娱乐": 2.5, "明星": 2.5, "综艺": 2.0, "电影": 2.0, "音乐": 2.0, "八卦": 2.5,
        "奇闻": 2.0, "趣事": 2.0, "离谱": 1.8, "震惊": 1.8, "奇葩": 1.8, "笑场": 1.8,
        "争议": 1.5, "翻车": 1.5, "闹剧": 1.5, "真相": 1.3,
        "政策": 0.3, "法规": 0.3, "国务院": 0.3, "官方": 0.35, "政府": 0.35, "通知": 0.35,
        "民生": 0.4, "医保": 0.4, "养老": 0.4, "住房": 0.4, "补贴": 0.35, "教育": 0.5,
        "经济": 0.5, "楼市": 0.5, "房贷": 0.5, "就业": 0.5, "工资": 0.5, "物价": 0.5,
    },
}


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


def _score_topic(topic: Dict, target_platform: str = "") -> int:
    """综合评分：话题类型权重 + 标题吸引力 + 来源可信度
    target_platform: 目标发布平台（baijiahao/toutiao），影响权重修饰"""
    title = topic.get("title", "")
    summary = topic.get("summary", "")
    src_platform = topic.get("platform", "unknown")

    score = 0

    # 1. 话题类型权重 — 基于关键词匹配，叠加平台修饰
    combined = title + summary
    modifiers = PLATFORM_WEIGHT_MODIFIERS.get(target_platform, {})
    for keyword, weight in TOPIC_WEIGHTS.items():
        if keyword in combined:
            modifier = modifiers.get(keyword, 1.0)
            score += int(weight * modifier)

    # 2. 标题吸引力加分
    # 身份认同钩子：点名具体群体
    identity_groups = ["司机", "外卖", "快递", "医生", "教师", "学生", "家长", "老人",
                       "农民", "工人", "程序员", "创业", "打工", "毕业生", "应届",
                       "网约车", "租房", "买房", "有车", "炒股", "理财"]
    for group in identity_groups:
        if group in title:
            score += 8
            break

    # 标题含数字加分
    if re.search(r'\d+', title):
        score += 3
    # 标题含疑问加分
    if any(kw in title for kw in ["？", "?", "吗", "如何", "怎么", "怎样", "什么", "为何"]):
        score += 3
    # 标题暗示利益/风险
    if any(kw in title for kw in ["钱", "赚", "亏", "省", "赔偿", "补偿", "罚款", "免费",
                                   "涨价", "降价", "福利", "补贴", "红包"]):
        score += 5

    # 3. 来源可信度（头条降低权威来源加分，鼓励内容多样化）
    cred = PLATFORM_CREDIBILITY.get(src_platform, 0)
    if target_platform == "toutiao" and src_platform in ("people_rm", "xinhuanet"):
        cred = int(cred * 0.4)  # 权威来源在头条只保留40%加分
    score += cred

    # 4. 惩罚：仅对真正低价值话题（整容塌房等）
    for pat in LOW_VALUE_PATTERNS:
        if pat in title:
            score -= 15
            break

    return score


def select_best_items(topics: List[Dict], max_count: int = 2, target_platform: str = "") -> List[Dict]:
    """按综合评分筛选最佳热点，target_platform 为空时使用通用权重"""
    published_urls = _published_source_urls()

    # Step 1: 过滤 + 评分
    scored = []
    for topic in topics:
        title = topic.get("title", "")
        if len(title) < MIN_TITLE_LENGTH or len(title) > MAX_TITLE_LENGTH:
            continue
        url = _extract_url(topic)
        if url and url in published_urls:
            continue

        score = _score_topic(topic, target_platform)
        scored.append((score, topic))

    if not scored:
        return []

    # Step 2: 按评分降序
    scored.sort(key=lambda x: x[0], reverse=True)

    # Step 3: 全量竞争 — 不分平台，纯按评分排序
    print(f"[TopicSaver] 评分 TOP{min(10, len(scored))}:")
    for i, (s, t) in enumerate(scored[:10]):
        print(f"  {i+1}. [{t.get('platform','?')} {s}分] {t['title'][:50]}")

    # Step 4: 从前 N+4 个中加权随机（高分更高概率，保留一定随机性）
    pool_size = min(max_count + 4, len(scored))
    pool = scored[:pool_size]
    if pool_size <= max_count:
        selected = [t for _, t in pool]
    else:
        weights = [s + 1 for s, _ in pool]
        chosen = random.choices(list(range(pool_size)), weights=weights, k=max_count)
        seen = set()
        selected = []
        for idx in chosen:
            if idx not in seen:
                seen.add(idx)
                selected.append(pool[idx][1])
        for _, t in pool:
            if len(selected) >= max_count:
                break
            if t not in selected:
                selected.append(t)

    for i, t in enumerate(selected):
        print(f"[TopicSaver]   #{i+1} {t.get('platform','')} · {t['title'][:40]} (评分: {_score_topic(t, target_platform)})")

    return selected


def save_topic(topic: Dict, index: int) -> str:
    title = topic.get("title", "无标题")
    summary = topic.get("summary", "")
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    safe_title = re.sub(r'[\\/:*?"<>|]', '', title)[:30].strip()
    slug = f"{ts}-{safe_title}"
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


def save_topics(topics: List[Dict], daily_limit: int = 2, target_platforms: list = None,
                per_platform_count: dict = None) -> List[str]:
    if target_platforms:
        return _save_topics_per_platform(topics, target_platforms, per_platform_count)
    return _save_topics_generic(topics, daily_limit)


def _save_topics_generic(topics: List[Dict], daily_limit: int = 2) -> List[str]:
    """通用模式：无平台区分，统一评分"""
    print(f"[TopicSaver] 从 {len(topics)} 条热点中筛选 {daily_limit} 条...")
    selected = select_best_items(topics, daily_limit)
    if selected:
        _summarize_selected(selected)
    return _do_save(selected)


def _save_topics_per_platform(topics: List[Dict], platforms: list,
                              per_platform_count: dict = None) -> List[str]:
    """按平台分选：每平台选 N 篇（N = 该平台账号数），用各自权重修饰器"""
    if per_platform_count is None:
        per_platform_count = {p: 1 for p in platforms}
    total = sum(per_platform_count.values())
    print(f"[TopicSaver] 分平台选文: {', '.join(platforms)}（共{total}篇）")
    slugs = []
    used_urls = set()

    for plat in platforms:
        count = per_platform_count.get(plat, 1)
        plat_label = {"baijiahao": "百家号", "toutiao": "今日头条"}.get(plat, plat)
        print(f"\n[TopicSaver] --- {plat_label} ({plat}) ×{count}篇 ---")

        published_urls = _published_source_urls() | used_urls

        scored = []
        for topic in topics:
            title = topic.get("title", "")
            if len(title) < MIN_TITLE_LENGTH or len(title) > MAX_TITLE_LENGTH:
                continue
            url = _extract_url(topic)
            if url and url in published_urls:
                continue
            score = _score_topic(topic, plat)
            scored.append((score, topic))

        if not scored:
            print(f"[TopicSaver] {plat_label} 无合适热点")
            continue

        scored.sort(key=lambda x: x[0], reverse=True)
        top_n = min(10, len(scored))
        print(f"[TopicSaver] {plat_label} TOP{top_n}:")
        for i, (s, t) in enumerate(scored[:top_n]):
            print(f"  {i+1}. [{t.get('platform','?')} {s}分] {t['title'][:50]}")

        # 加权随机选 N 篇（不重复）
        selected = []
        pool = list(scored)
        for _ in range(min(count, len(pool))):
            if not pool:
                break
            pool_size = min(5 + len(selected), len(pool))
            candidates = pool[:pool_size]
            weights = [s + 1 for s, _ in candidates]
            idx = random.choices(list(range(len(candidates))), weights=weights, k=1)[0]
            chosen = candidates.pop(idx)[1]
            # 重建 pool（去掉选中项）
            pool = [(s, t) for s, t in pool if t != chosen]
            best_url = _extract_url(chosen)
            if best_url:
                used_urls.add(best_url)
            selected.append(chosen)

        for i, t in enumerate(selected):
            print(f"[TopicSaver]   #{plat_label}{i+1}: {t.get('platform','')} · {t['title'][:40]} (评分: {_score_topic(t, plat)})")
            slug = save_topic(t, len(slugs) + 1)
            slugs.append(slug)

    # 对选中的全部条目批量生成摘要（选后摘要，节省 token）
    selected_topics = []
    for slug in slugs:
        article_dir = OUTPUT_DIR / slug
        md_files = list(article_dir.glob("*.md"))
        if md_files:
            from article_utils import parse_article
            article = parse_article(md_files[0])
            selected_topics.append({"title": article["title"], "slug": slug})

    if selected_topics:
        _summarize_selected(selected_topics)

    return slugs


def _summarize_selected(selected: List[Dict]):
    """对已选中的条目调用 AI 生成摘要，回写到 markdown 文件"""
    titles = [t["title"] for t in selected]
    print(f"[TopicSaver] 为 {len(titles)} 条选中热点生成摘要...")
    from processor import summarize_batch
    summaries = summarize_batch([{"title": t} for t in titles])
    for item in selected:
        summary = summaries.get(item["title"], "")
        if not summary or summary == "暂无详细信息":
            continue
        slug = item["slug"]
        article_dir = OUTPUT_DIR / slug
        for md_file in article_dir.glob("*.md"):
            text = md_file.read_text(encoding="utf-8")
            if "> 摘要：" in text:
                text = re.sub(r'> 摘要：.*', f'> 摘要：{summary}', text)
            else:
                text = text.replace(
                    "（发布时基于源内容 AI 扩写）",
                    f"> 摘要：{summary}\n\n（发布时基于源内容 AI 扩写）"
                )
            md_file.write_text(text, encoding="utf-8")
            print(f"[TopicSaver]   摘要已回写: {slug[:40]}")


def _do_save(selected: List[Dict]) -> List[str]:
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
