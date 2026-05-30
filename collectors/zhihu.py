"""知乎热榜采集器（需 Cookie，支持 HttpOnly 降级到浏览器 fetch）"""
import os
import json
import sys
import time
import subprocess
from pathlib import Path
from .base import fetch_with_retry, TrendItem, HEADERS

ZHIHU_API = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=20"
OPENCLI = str(Path.home() / "AppData" / "Roaming" / "npm" / "opencli.cmd")


def _load_cookie() -> str:
    cookie = os.environ.get("ZHIHU_COOKIE", "")
    if not cookie:
        cookie_file = os.path.join(os.path.dirname(__file__), "..", ".zhihu_cookie")
        try:
            with open(cookie_file) as f:
                cookie = f.read().strip()
        except FileNotFoundError:
            pass
    return cookie


def _sh_run(cmd: str, timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, shell=True, capture_output=True,
        encoding="utf-8", errors="replace", timeout=timeout
    )


def _fetch_via_browser() -> dict:
    """导航到知乎 → 在页面上下文中 fetch API（自动携带 HttpOnly Cookie）"""
    _sh_run(f"{OPENCLI} browser pub open https://www.zhihu.com/hot", timeout=15)
    time.sleep(2)
    js = "(async()=>{var r=await fetch('%s');return await r.text();})()" % ZHIHU_API
    js_escaped = js.replace('"', '\\"')
    r = _sh_run(f'{OPENCLI} browser pub eval "{js_escaped}"', timeout=30)
    if r.returncode != 0 or not r.stdout.strip():
        err_msg = (r.stderr or "")[:200].encode("ascii", errors="replace").decode("ascii")
        raise RuntimeError(f"opencli eval failed: {err_msg}")
    return json.loads(r.stdout.strip())


def collect_zhihu():
    cookie = _load_cookie()
    if not cookie:
        return []

    headers = {**HEADERS, "Referer": "https://www.zhihu.com/hot", "Cookie": cookie}

    data = None
    try:
        resp = fetch_with_retry(ZHIHU_API, headers=headers)
        data = resp.json()
    except Exception:
        pass

    if not data or not data.get("data"):
        try:
            data = _fetch_via_browser()
        except Exception as e:
            safe_msg = str(e).encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8", errors="replace")
            print(f"[ZHIHU] browser fetch failed: {safe_msg}")
            return []

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
