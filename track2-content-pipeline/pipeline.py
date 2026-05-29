"""内容管线主入口：采集 -> 过滤 -> 选文+摘要 -> 保存主题 -> 校验

可通过命令行参数或环境变量传入配置（命令行优先）：
  python pipeline.py --article-limit 4 --target-platforms baijiahao,toutiao --platform-account-counts baijiahao:2,toutiao:2
"""
import config_loader  # noqa: E402,F401
import argparse
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

from collectors.run_all import run_all
from processor import filter_trends, check_budget
from builder import build_index
from article_writer import save_topics


def _parse_args():
    p = argparse.ArgumentParser(description="内容管线")
    p.add_argument("--article-limit", type=int, default=0, help="生成文章数（0=跳过）")
    p.add_argument("--target-platforms", default="", help="目标平台（逗号分隔）")
    p.add_argument("--platform-account-counts", default="",
                   help="每平台数量（如 baijiahao:2,toutiao:1）")
    return p.parse_args()


def main():
    args = _parse_args()

    # 命令行参数优先，环境变量兜底
    article_limit = args.article_limit or int(os.environ.get("ARTICLE_LIMIT", "0"))
    target_platforms_str = args.target_platforms or os.environ.get("TARGET_PLATFORMS", "")
    counts_str = args.platform_account_counts or os.environ.get("PLATFORM_ACCOUNT_COUNTS", "")

    target_platforms = [p.strip() for p in target_platforms_str.split(",") if p.strip()] if target_platforms_str else None
    per_platform_count: dict[str, int] = {}
    if counts_str:
        for item in counts_str.split(","):
            parts = item.strip().split(":")
            if len(parts) == 2:
                per_platform_count[parts[0]] = int(parts[1])

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

    # 确保每个条目有必需字段
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    for it in filtered:
        it["source_url"] = it.get("source_url") or it.get("url", "")
        it["generated_at"] = it.get("generated_at") or now

    # Step 3: 选文 + AI 摘要（选后摘要，节省 ~95% token）
    print("\n[3/5] 选文 + AI 摘要...")
    budget_ok = check_budget()

    if article_limit > 0:
        if target_platforms:
            total_accounts = sum(per_platform_count.values()) if per_platform_count else len(target_platforms)
            print(f"  分平台选文（{', '.join(target_platforms)}，共{total_accounts}篇）...")
            save_topics(filtered, target_platforms=target_platforms,
                       per_platform_count=per_platform_count or None)
        else:
            print(f"  通用选文（每日{article_limit}篇）...")
            save_topics(filtered, daily_limit=article_limit)
    else:
        print("  ARTICLE_LIMIT=0，跳过")

    # Step 4: 生成 HTML
    print("\n[4/5] 生成 HTML...")
    build_index(filtered)

    # Step 5: 校验
    print("\n[5/5] 校验 HTML...")
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
