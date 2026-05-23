"""processor.py 过滤测试"""
import sys
sys.path.insert(0, '..')
from processor import filter_trends

def test_filter_entertainment():
    """娱乐关键词被过滤"""
    items = [
        {"title": "某明星出轨被拍，网友热议"},
        {"title": "GPT-5发布：多模态能力再进化"},
    ]
    filtered = filter_trends(items)
    titles = [it["title"] for it in filtered]
    assert "GPT-5发布" in str(titles)
    assert "明星" not in str(titles)

def test_dedup_similar_title():
    """重复标题去重"""
    items = [
        {"title": "GPT-5正式发布"},
        {"title": "GPT-5正式发布"},
    ]
    filtered = filter_trends(items)
    assert len(filtered) == 1
