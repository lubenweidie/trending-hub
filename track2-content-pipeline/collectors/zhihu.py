"""知乎热榜采集器（需 Cookie）"""
import os
from .base import fetch_with_retry, TrendItem, HEADERS

def collect_zhihu():
    cookie = os.environ.get("ZHIHU_COOKIE", "")
    if not cookie:
        cookie_file = os.path.join(os.path.dirname(__file__), "..", ".zhihu_cookie")
        try:
            with open(cookie_file) as f:
                cookie = f.read().strip()
        except FileNotFoundError:
            pass
    if not cookie:
        return []

    url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=20"
    headers = {**HEADERS, 'Referer': 'https://www.zhihu.com/hot', 'Cookie': cookie}
    resp = fetch_with_retry(url, headers=headers)
    data = resp.json()
    items = []
    for entry in data.get("data", [])[:20]:
        target = entry.get("target", {})
        qid = target.get("id", "")
        items.append(TrendItem(
            title=target.get("title", ""),
            url=f"https://www.zhihu.com/question/{qid}" if qid else "",
            platform="知乎",
            hot_score=target.get("follower_count", 0),
        ))
    return items
