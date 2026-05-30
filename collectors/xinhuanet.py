"""新华网采集器 — 从首页提取要闻"""
import re
from .base import fetch_with_retry, TrendItem, HEADERS


def _extract_title(html, url):
    """从 <a> 标签内部提取文字标题"""
    idx = html.find(url)
    if idx < 0:
        return ""
    before = html[:idx]
    a_start = before.rfind("<a ")
    if a_start < 0:
        return ""
    tag_end = html.find(">", a_start)
    if tag_end < 0:
        return ""
    a_close = html.find("</a>", tag_end)
    if a_close < 0:
        return ""
    inner = html[tag_end + 1:a_close]
    title = re.sub(r"<[^>]+>", "", inner).strip()
    title = re.sub(r"\s+", " ", title)
    return title


def collect_xinhuanet():
    url = "https://www.news.cn/"
    headers = {**HEADERS, "Referer": "https://www.news.cn/"}
    resp = fetch_with_retry(url, headers=headers)
    html = resp.text

    article_urls = re.findall(
        r"https?://www\.news\.cn/\w+/\d+/[\w-]+/c\.html", html
    )
    seen = set()
    items = []
    for article_url in article_urls:
        if article_url in seen:
            continue
        seen.add(article_url)
        title = _extract_title(html, article_url)
        if len(title) < 4:
            continue
        items.append(TrendItem(
            title=title,
            url=article_url,
            platform="新华网",
        ))
        if len(items) >= 20:
            break
    return items
