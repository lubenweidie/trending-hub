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
                direct_url = entry.get("url", "").strip()
                # 百度 API 返回的 url 经常仍是 m.baidu.com 搜索页，不是真文章直链
                is_search_page = any(kw in direct_url for kw in (
                    "m.baidu.com/s?", "baidu.com/s?wd=", "baidu.com/s?word=",
                    "baidu.com/s?tn=", "baidu.com/s?rtt="
                )) if direct_url else True
                if is_search_page:
                    direct_url = ""
                items.append(TrendItem(
                    title=word,
                    url=direct_url or f"https://m.baidu.com/s?word={word}",
                    platform="百度",
                    hot_score=entry.get("hotScore", 0),
                    raw_data={"desc": entry.get("desc", ""), "img": entry.get("img", ""), "has_direct_url": bool(direct_url)},
                ))
    return items[:20]
