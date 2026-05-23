"""AI处理层：去重→过滤→摘要→改写"""
import json
import os
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# 成本控制
COST_LOG = Path("logs/daily_tokens.json")
MONTHLY_BUDGET_YUAN = 150
ALERT_THRESHOLD_YUAN = 120
TOKEN_PRICE = 0.001 / 1000  # ¥1/百万token

def load_frequency_words() -> set:
    """加载过滤关键词"""
    with open("frequency_words.txt", "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}

def filter_trends(items: List[Dict]) -> List[Dict]:
    """去重 + 过滤娱乐八卦"""
    freq_words = load_frequency_words()
    seen = set()
    result = []
    for item in items:
        title = item.get("title", "")
        # 去重：标题前20字hash
        key = hashlib.md5(title[:60].encode()).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        # 过滤娱乐关键词
        if any(w in title for w in freq_words):
            continue
        result.append(item)
    return result

def check_budget() -> bool:
    """检查月度预算；超限返回False"""
    if not COST_LOG.exists():
        return True
    logs = json.loads(COST_LOG.read_text(encoding="utf-8"))
    month_key = datetime.now().strftime("%Y-%m")
    month_total = sum(d.get("tokens", 0) for d in logs if d.get("date", "").startswith(month_key))
    cost = month_total * TOKEN_PRICE
    if cost > MONTHLY_BUDGET_YUAN:
        print(f"[BUDGET] 月度消耗¥{cost:.1f}超过预算¥{MONTHLY_BUDGET_YUAN}，降级为原文模式")
        return False
    if cost > ALERT_THRESHOLD_YUAN:
        print(f"[BUDGET] 月度消耗¥{cost:.1f}已达告警线¥{ALERT_THRESHOLD_YUAN}")
    return True

def process_trends(all_results: Dict[str, List], budget_ok: bool = True):
    """主处理入口"""
    # 合并所有采集结果
    all_items = []
    for platform, items in all_results.items():
        for item in items:
            item_dict = item.__dict__ if hasattr(item, '__dict__') else item
            item_dict["platform"] = platform
            all_items.append(item_dict)

    # 去重+过滤
    filtered = filter_trends(all_items)
    print(f"[PROCESS] 原始{len(all_items)}条 → 过滤后{len(filtered)}条")

    if not budget_ok:
        # 降级模式：不调用AI，原文标题+链接
        return [{"title": it["title"], "summary": "", "source_url": it.get("url", ""),
                 "platform": it.get("platform", "")} for it in filtered]

    # TODO: 正常模式调用 AI API 做摘要+改写
    # 具体Prompt模板见方案 [DS-02]
    return filtered
