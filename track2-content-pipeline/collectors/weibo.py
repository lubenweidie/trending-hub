"""微博热搜采集器"""
from .base import fetch_with_retry, TrendItem, HEADERS

def collect_weibo():
    url = "https://weibo.com/ajax/side/hotSearch"
    headers = {**HEADERS, 'Referer': 'https://weibo.com/', 'X-Requested-With': 'XMLHttpRequest'}
    resp = fetch_with_retry(url, headers=headers)
    data = resp.json()
    items = []
    for entry in data.get("data", {}).get("realtime", [])[:20]:
        word = entry.get("word", "")
        scheme = entry.get("scheme", "")
        url = scheme if scheme else f"https://s.weibo.com/weibo?q={word}"
        items.append(TrendItem(
            title=word,
            url=url,
            platform="微博",
            hot_score=entry.get("num", 0),
            raw_data={"note": entry.get("note", ""), "category": entry.get("category", "")},
        ))
    return items
