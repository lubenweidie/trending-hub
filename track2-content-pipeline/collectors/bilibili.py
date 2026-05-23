"""B站热门采集器"""
from .base import fetch_with_retry, TrendItem, HEADERS

def collect_bilibili():
    url = "https://api.bilibili.com/x/web-interface/popular?ps=20"
    headers = {**HEADERS, 'Referer': 'https://www.bilibili.com/'}
    resp = fetch_with_retry(url, headers=headers)
    data = resp.json()
    items = []
    for entry in data.get("data", {}).get("list", [])[:20]:
        items.append(TrendItem(
            title=entry.get("title", ""),
            url=f"https://www.bilibili.com/video/{entry.get('bvid', '')}",
            platform="B站",
            hot_score=entry.get("stat", {}).get("view", 0),
        ))
    return items
