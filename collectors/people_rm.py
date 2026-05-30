"""人民日报采集器 — 从首页提取要闻"""
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


def collect_people_rm():
    url = "http://www.people.com.cn/"
    headers = {**HEADERS, "Referer": "http://www.people.com.cn/"}
    resp = fetch_with_retry(url, headers=headers)
    resp.encoding = "utf-8"
    html = resp.text

    article_urls = re.findall(
        r"https?://\w+\.people\.com\.cn/n1/\d{4}/\d{4}/[^\"]+\.html", html
    )
    skip_domains = {"tv", "ent", "homea", "leaders", "www"}
    seen = set()
    items = []
    for article_url in article_urls:
        if article_url in seen:
            continue
        seen.add(article_url)
        domain = article_url.split("//")[1].split(".")[0]
        if domain in skip_domains:
            continue
        title = _extract_title(html, article_url)
        if len(title) < 4:
            continue
        items.append(TrendItem(
            title=title,
            url=article_url,
            platform="人民日报",
        ))
        if len(items) >= 20:
            break
    return items
