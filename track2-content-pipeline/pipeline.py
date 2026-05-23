"""内容管线主入口：采集 -> 过滤 -> AI摘要 -> 生成 -> 校验"""
import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from collectors.run_all import run_all
from processor import filter_trends, check_budget, summarize_items, AI_ENABLED
from builder import build_index


def main():
    print("=" * 50)
    print("  内容自动化管线")
    print("=" * 50)

    # Step 1: 采集
    print("\n[1/5] 采集热榜数据...")
    results = run_all()

    # Step 2: 合并 + 去重 + 过滤
    print("\n[2/5] 去重过滤...")
    all_items = []
    for platform, items in results.items():
        for item in items:
            d = item.__dict__ if hasattr(item, '__dict__') else item
            if not d.get("platform"):
                d["platform"] = platform
            all_items.append(d)
    filtered = filter_trends(all_items)
    print(f"  原始 {len(all_items)} 条 -> 过滤后 {len(filtered)} 条")

    # Step 3: AI 摘要
    print("\n[3/5] AI 摘要生成...")
    budget_ok = check_budget()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if budget_ok and AI_ENABLED:
        filtered = summarize_items(filtered)
    else:
        if not budget_ok:
            print("  预算不足，跳过 AI 摘要")
        elif not AI_ENABLED:
            print("  未配置 API Key，跳过 AI 摘要")
        for it in filtered:
            it["summary"] = it.get("summary", "")
            it["source_url"] = it.get("url", "")
            it["generated_at"] = now

    # 确保每个条目有必需字段
    for it in filtered:
        it["source_url"] = it.get("source_url") or it.get("url", "")
        it["generated_at"] = it.get("generated_at") or now

    # Step 4: 生成 HTML
    print("\n[4/5] 生成 HTML...")
    build_index(filtered)

    # Step 5: 校验
    print("\n[5/5] 校验 HTML...")
    import subprocess
    result = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "validate_output.py")],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        sys.exit(1)

    print("\n[OK] 管线执行完成")


if __name__ == "__main__":
    main()
