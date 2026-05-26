"""快捷发布 — 跳过管线采集，直接发布已有文章到指定平台

用法:
  # 草稿模式发布最新文章到今日头条
  python quick_publish.py toutiao

  # 立即发布到多个平台
  python quick_publish.py toutiao,baijiahao --publish

  # 发布指定文章
  python quick_publish.py toutiao -f output/articles/20260526-01.md
"""
import config_loader  # noqa
import os, sys, argparse
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from publishers import REGISTRY
from publishers.base import BasePublisher


def main():
    parser = argparse.ArgumentParser(description="快捷发布到指定平台")
    parser.add_argument("platforms", help="目标平台（逗号分隔，如: toutiao,baijiahao）")
    parser.add_argument("-f", "--file", default="", help="指定文章路径（默认找最新）")
    parser.add_argument("--publish", action="store_true", help="立即发布（默认存草稿）")
    parser.add_argument("--dry-run", action="store_true", help="只显示文章信息，不发布")
    args = parser.parse_args()

    platforms = [p.strip() for p in args.platforms.split(",") if p.strip()]
    mode = "publish" if args.publish else "draft"

    # 找文章
    if args.file:
        article_file = Path(args.file)
    else:
        article_file = BasePublisher.find_latest_article(
            str(HERE / "output" / "articles"))

    if not article_file or not article_file.exists():
        print("[Exit] 没有找到文章")
        sys.exit(1)

    article = BasePublisher.parse_article(article_file)
    print(f"文章: {article['title'][:50]}")
    print(f"字数: {len(article['content'])}")
    print(f"模式: {'立即发布' if mode == 'publish' else '存草稿'}")
    print(f"平台: {', '.join(platforms)}")

    if args.dry_run:
        return

    for name in platforms:
        if name not in REGISTRY:
            print(f"[Skip] 未知平台: {name}")
            continue
        pub = REGISTRY[name]()
        ok = pub.publish(article_path=str(article_file), mode=mode)
        status = "成功" if ok else "失败"
        print(f"[{name}] {status}")

    # 归档（目录名加上发布平台）
    import shutil
    article_dir = article_file.parent
    publish_platform = "-".join(platforms)
    new_name = f"{article_dir.name}-{publish_platform}"
    new_path = article_dir.parent / new_name
    article_dir.rename(new_path)
    article_dir = new_path
    published_dir = HERE / "output" / "articles" / "published"
    published_dir.mkdir(exist_ok=True)
    archived = published_dir / article_dir.name
    if archived.exists():
        shutil.rmtree(str(archived))
    shutil.move(str(article_dir), str(archived))
    print(f"[归档] {archived.name}")


if __name__ == "__main__":
    main()
