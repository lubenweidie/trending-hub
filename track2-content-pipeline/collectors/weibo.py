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
