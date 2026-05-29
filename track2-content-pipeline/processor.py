"""AI处理层：去重→过滤→摘要→改写"""
import json
import os
import hashlib
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# 成本控制
COST_LOG = Path("logs/daily_tokens.json")
MONTHLY_BUDGET_YUAN = 150
ALERT_THRESHOLD_YUAN = 120
TOKEN_PRICE = 0.001 / 1000  # ¥1/百万token

# DeepSeek API 配置
DEEPSEEK_API_URL = os.environ.get("AI_API_URL") or "https://api.deepseek.com/v1/chat/completions"


def _is_ai_enabled() -> bool:
    return bool(os.environ.get("DEEPSEEK_API_KEY", ""))

BATCH_SUMMARIZE_PROMPT = """你是一个热点新闻摘要助手。以下是从不同平台采集的热点话题列表。
请为每个话题写一段客观、信息丰富的摘要（50-100字），说明事件的核心事实、关键数据和背景。
只陈述已知事实，不要猜测、不要标题党、不要煽动情绪。
如果话题信息不足以判断内容，写"暂无详细信息"。

返回格式（JSON对象）：
{"results": [{"title": "原标题", "summary": "你的摘要"}, ...]}

热点列表：
"""

def filter_trends(items: List[Dict]) -> List[Dict]:
    """去重"""
    seen = set()
    result = []
    for item in items:
        title = item.get("title", "")
        # 去重：标题前20字hash
        key = hashlib.md5(title[:60].encode()).hexdigest()
        if key in seen:
            continue
        seen.add(key)
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

def log_tokens(tokens: int):
    """记录单次消耗"""
    COST_LOG.parent.mkdir(parents=True, exist_ok=True)
    logs = []
    if COST_LOG.exists():
        logs = json.loads(COST_LOG.read_text(encoding="utf-8"))
    logs.append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tokens": tokens
    })
    COST_LOG.write_text(json.dumps(logs, ensure_ascii=False, indent=2), encoding="utf-8")


def summarize_batch(items: List[Dict]) -> Dict[str, str]:
    """批量调用 DeepSeek API 生成摘要，返回 {title: summary} 映射"""
    if not _is_ai_enabled() or not items:
        return {}

    # 构建批量请求
    titles = [it["title"] for it in items]
    titles_json = json.dumps(titles, ensure_ascii=False)

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个专业的新闻摘要助手。请严格按JSON格式返回结果。"},
            {"role": "user", "content": BATCH_SUMMARIZE_PROMPT + titles_json}
        ],
        "max_tokens": 150 * len(items),  # 每条约150 token，确保50-100字中文摘要
        "temperature": 0.3,
        "response_format": {"type": "json_object"}
    }

    for attempt in range(3):
        try:
            resp = requests.post(
                DEEPSEEK_API_URL,
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=90
            )
            if resp.status_code == 200:
                data = resp.json()
                usage = data.get("usage", {}).get("total_tokens", 0)
                log_tokens(usage)

                content = data["choices"][0]["message"]["content"]
                result_obj = json.loads(content)
                result_list = result_obj.get("results", [])
                return {r["title"]: r.get("summary", "") for r in result_list if "title" in r}

            if resp.status_code == 429:
                print(f"[AI] 速率限制，等待 {(attempt+1)*10}s...")
                time.sleep((attempt + 1) * 10)
                continue

            print(f"[AI] API错误 {resp.status_code}: {resp.text[:200]}")
            if attempt < 2:
                time.sleep(3)

        except Exception as e:
            print(f"[AI] 请求异常: {e}")
            if attempt < 2:
                time.sleep(5)

    return {}


def summarize_items(items: List[Dict], batch_size: int = 10) -> List[Dict]:
    """为条目列表添加 AI 摘要，分批处理"""
    if not _is_ai_enabled():
        print("[AI] 未配置 DEEPSEEK_API_KEY，跳过摘要生成")
        return items

    print(f"[AI] 开始为 {len(items)} 条生成摘要...")
    result = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        summaries = summarize_batch(batch)
        for item in batch:
            item = dict(item)
            item["summary"] = summaries.get(item["title"], "")
            result.append(item)
        if i + batch_size < len(items):
            time.sleep(1)  # 批次间短暂休息
        print(f"[AI] 进度: {min(i + batch_size, len(items))}/{len(items)}")

    print(f"[AI] 摘要生成完成")
    return result
