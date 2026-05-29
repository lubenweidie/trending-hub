"""文章效果追踪 — 发表记录 + 定时回读数据"""
import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent.parent
TRACK_FILE = HERE / "output" / "articles" / "published" / "_track.json"


def add_entry(title: str, platform: str, article_dir: str):
    """发布成功后追加一条记录"""
    entry = {
        "title": title,
        "platform": platform,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dir": article_dir,
        "stats": None,
    }
    records = _load()
    records.append(entry)
    _save(records)


def _load() -> list:
    if TRACK_FILE.exists():
        try:
            return json.loads(TRACK_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    return []


def _save(records: list):
    TRACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    TRACK_FILE.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    # 查看已发表记录
    records = _load()
    if not records:
        print("暂无发表记录")
        sys.exit(0)

    print(f"{'时间':<20} {'平台':<10} {'标题':<30} {'数据'}")
    print("-" * 80)
    for r in records:
        stats = r.get("stats")
        stats_str = ""
        if stats:
            stats_str = f"阅读{stats.get('views','?')} 评论{stats.get('comments','?')}"
        print(f"{r['time']:<20} {r['platform']:<10} {r['title'][:28]:<30} {stats_str}")
