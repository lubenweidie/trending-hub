"""百度热搜采集器"""
from .base import fetch_with_retry, TrendItem, HEADERS

def collect_baidu():
    url = "https://top.baidu.com/api/board?platform=wise&tab=realtime"
    headers = {**HEADERS, 'Referer': 'https://top.baidu.com/'}
    resp = fetch_with_retry(url, headers=headers)
    data = resp.json()
    items = []
    for card in data.get("data", {}).get("cards", []):
        for content_wrapper in card.get("content", []):
            for entry in content_wrapper.get("content", []):
                word = entry.get("word", "")
                if not word or entry.get("isTop"):
                    continue
                items.append(TrendItem(
                    title=word,
                    url=entry.get("url", f"https://www.baidu.com/s?wd={word}"),
                    platform="百度",
                    hot_score=entry.get("hotScore", 0),
                ))
    return items[:20]
