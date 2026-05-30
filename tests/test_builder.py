"""builder.py 测试：HTML 生成 + Jinja2 转义"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from builder import build_index


def test_build_index_generates_html():
    """生成带条目的 HTML"""
    items = [
        {
            "title": "测试新闻",
            "platform": "微博",
            "source_url": "https://example.com/news",
            "generated_at": "2026-05-29 12:00",
            "summary": "摘要内容",
        }
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        build_index(items, output_dir=tmpdir)
        html = (Path(tmpdir) / "index.html").read_text(encoding="utf-8")
        assert "测试新闻" in html
        assert "https://example.com/news" in html
        assert "微博" in html


def test_build_index_empty():
    """空列表生成空页面"""
    with tempfile.TemporaryDirectory() as tmpdir:
        build_index([], output_dir=tmpdir)
        html = (Path(tmpdir) / "index.html").read_text(encoding="utf-8")
        assert "<html" in html
        assert "<article>" not in html


def test_build_index_xss_escaped():
    """XSS 攻击被 Jinja2 自动转义"""
    items = [{
        "title": '<script>alert("xss")</script>',
        "platform": "test",
        "source_url": "https://example.com",
        "generated_at": "2026-05-29",
    }]
    with tempfile.TemporaryDirectory() as tmpdir:
        build_index(items, output_dir=tmpdir)
        html = (Path(tmpdir) / "index.html").read_text(encoding="utf-8")
        assert "<script>" not in html
        assert "&lt;script&gt;" in html
        assert "&#34;xss&#34;" in html  # Jinja2 一并转义引号
