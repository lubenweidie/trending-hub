"""内容管线主入口：采集 -> 过滤 -> 生成 -> 校验"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from collectors.run_all import run_all
from processor import filter_trends, check_budget
from builder import build_index


def main():
    print("=" * 50)
    print("  内容自动化管线")
    print("=" * 50)

    # Step 1: 采集
    print("\n[1/4] 采集热榜数据...")
    results = run_all()

    # Step 2: 合并 + 去重 + 过滤
    print("\n[2/4] 去重过滤...")
    all_items = []
    for platform, items in results.items():
        for item in items:
            d = item.__dict__ if hasattr(item, '__dict__') else item
            if not d.get("platform"):
                d["platform"] = platform
            all_items.append(d)
    filtered = filter_trends(all_items)
    print(f"  原始 {len(all_items)} 条 -> 过滤后 {len(filtered)} 条")

    # Step 3: 生成 HTML
    print("\n[3/4] 生成 HTML...")
    budget_ok = check_budget()
    if not budget_ok:
        for it in filtered:
            it["summary"] = ""
            it["source_url"] = it.get("url", "")
            it["generated_at"] = ""
    else:
        for it in filtered:
            it["source_url"] = it.get("url", "")
            it["generated_at"] = ""
            if not it.get("summary"):
                it["summary"] = ""

    build_index(filtered)

    # Step 4: 校验
    print("\n[4/4] 校验 HTML...")
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
