"""builder.py HTML转义测试"""
import sys
sys.path.insert(0, '..')
from html import escape

def test_html_escape_xss():
    """恶意标题被转义"""
    malicious = '<script>alert("XSS")</script>'
    escaped = escape(malicious)
    assert '<script>' not in escaped
    assert '&lt;script&gt;' in escaped

def test_normal_title_unchanged():
    """正常标题不被破坏"""
    normal = "GPT-5发布：AI能力再次跃升"
    escaped = escape(normal)
    assert "GPT-5" in escaped
    assert "&" not in escaped  # 无特殊字符则不变
