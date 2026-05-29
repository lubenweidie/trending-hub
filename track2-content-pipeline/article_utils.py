"""文章通用工具 — 跨层共享，不依赖 publishers/services/collectors"""
import shutil
from pathlib import Path


def parse_article(filepath: Path) -> dict:
    """从 markdown 文件解析标题和正文"""
    text = filepath.read_text(encoding="utf-8")
    lines = text.strip().split("\n")
    title = ""
    content_start = 0
    for i, line in enumerate(lines):
        if line.startswith("# ") and not title:
            title = line[2:].strip()
        if not line.startswith("#") and line.strip() and not line.startswith("> "):
            content_start = i
            break
    content = "\n".join(lines[content_start:]).strip() if content_start else ""
    return {"title": title or "无标题", "content": content}


def archive_article(article_file: Path, platform: str, output_dir: Path) -> None:
    """归档文章目录到 output_dir/published/，追加平台后缀后移入"""
    article_dir = article_file.parent
    new_name = f"{article_dir.name}-{platform}"
    new_path = article_dir.parent / new_name
    article_dir.rename(new_path)
    article_dir = new_path
    published_dir = output_dir / "published"
    published_dir.mkdir(exist_ok=True)
    archived = published_dir / article_dir.name
    if archived.exists():
        shutil.rmtree(str(archived))
    shutil.move(str(article_dir), str(archived))
    print(f"[归档] {archived.name}")
