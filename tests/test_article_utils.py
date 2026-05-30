"""article_utils.py 测试：文章解析 + 归档"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from article_utils import parse_article, archive_article


def test_parse_article_basic():
    """基本 Markdown 解析"""
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / "test.md"
        p.write_text("# 测试标题\n\n这是正文第一段。\n\n这是正文第二段。", encoding="utf-8")
        result = parse_article(p)
        assert result["title"] == "测试标题"
        assert "正文第一段" in result["content"]


def test_parse_article_with_metadata():
    """带元数据行的 Markdown"""
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / "test.md"
        p.write_text(
            "# 标题\n"
            "> 来源：微博\n"
            "> 原文：[链接](https://example.com)\n"
            "\n"
            "正文内容开始\n",
            encoding="utf-8"
        )
        result = parse_article(p)
        assert result["title"] == "标题"
        assert "正文内容开始" in result["content"]
        # 元数据行（> 开头）不应出现在正文中
        assert "来源：微博" not in result["content"]


def test_parse_article_no_title():
    """无标题时用默认值"""
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / "test.md"
        p.write_text("只有正文没有标题", encoding="utf-8")
        result = parse_article(p)
        assert result["title"] == "无标题"


def test_parse_article_empty():
    """空文件"""
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / "test.md"
        p.write_text("", encoding="utf-8")
        result = parse_article(p)
        assert result["title"] == "无标题"
        assert result["content"] == ""


def test_archive_article():
    """归档目录正确移入 published/"""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "articles"
        article_dir = output_dir / "20260529_1200-测试标题"
        article_dir.mkdir(parents=True)
        article_file = article_dir / "20260529_1200-测试标题.md"
        article_file.write_text("# 测试", encoding="utf-8")

        archive_article(article_file, "toutiao", output_dir)

        archived = output_dir / "published" / "20260529_1200-测试标题-toutiao"
        assert archived.exists()
        assert (archived / "20260529_1200-测试标题.md").exists()


def test_archive_article_overwrite_existing():
    """已存在归档可覆盖"""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "articles"
        article_dir = output_dir / "20260529_1200-测试"
        article_dir.mkdir(parents=True)
        article_file = article_dir / "20260529_1200-测试.md"
        article_file.write_text("# 测试", encoding="utf-8")

        # 先创建一个同名归档
        existing = output_dir / "published" / "20260529_1200-测试-toutiao"
        existing.mkdir(parents=True)
        (existing / "old.md").write_text("old")

        archive_article(article_file, "toutiao", output_dir)
        assert existing.exists()
        assert not (existing / "old.md").exists()  # 旧内容被覆盖
