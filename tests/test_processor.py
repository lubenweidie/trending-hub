"""processor.py 测试：去重 + 预算控制"""
import json
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from processor import filter_trends, check_budget, _is_ai_enabled


def test_filter_trends_dedup_exact_title():
    """完全相同的标题被去重"""
    items = [
        {"title": "GPT-5正式发布，多模态能力大幅提升"},
        {"title": "GPT-5正式发布，多模态能力大幅提升"},
    ]
    result = filter_trends(items)
    assert len(result) == 1


def test_filter_trends_dedup_similar_prefix():
    """标题前60字相同则去重（>60字标题共享前缀时命中）"""
    prefix = "国务院发布关于进一步优化营商环境促进经济高质量发展加强市场主体活力和创新能力的最新通知政策指导意见详情请查看具体实施细则"
    items = [
        {"title": prefix + "第一部分补充说明"},
        {"title": prefix + "第二部分全文下载"},
    ]
    result = filter_trends(items)
    assert len(result) == 1


def test_filter_trends_different_title_kept():
    """不同标题保留"""
    items = [
        {"title": "GPT-5正式发布"},
        {"title": "房价走势分析"},
    ]
    result = filter_trends(items)
    assert len(result) == 2


def test_filter_trends_empty():
    """空列表不报错"""
    assert filter_trends([]) == []


def test_check_budget_no_log():
    """无日志时返回 True"""
    import processor
    with tempfile.TemporaryDirectory() as tmp:
        log_file = Path(tmp) / "daily_tokens.json"
        original = processor.COST_LOG
        processor.COST_LOG = log_file
        try:
            assert check_budget() is True
        finally:
            processor.COST_LOG = original


def test_check_budget_under_alert():
    """预算低于告警线返回 True"""
    import processor
    with tempfile.TemporaryDirectory() as tmp:
        log_file = Path(tmp) / "daily_tokens.json"
        log_file.write_text(json.dumps(
            [{"date": "2026-05-01 08:00:00", "tokens": 1_000_000}]
        ), encoding="utf-8")
        original = processor.COST_LOG
        processor.COST_LOG = log_file
        try:
            assert check_budget() is True
        finally:
            processor.COST_LOG = original


def test_check_budget_over_budget():
    """超预算返回 False"""
    import processor
    with tempfile.TemporaryDirectory() as tmp:
        log_file = Path(tmp) / "daily_tokens.json"
        log_file.write_text(json.dumps(
            [{"date": "2026-05-01 08:00:00", "tokens": 200_000_000}]
        ), encoding="utf-8")
        original = processor.COST_LOG
        processor.COST_LOG = log_file
        try:
            assert check_budget() is False
        finally:
            processor.COST_LOG = original


def test_is_ai_enabled_no_key():
    """无 key 时返回 False"""
    import os
    from unittest.mock import patch
    with patch.dict(os.environ, {}, clear=True):
        with patch("os.environ.get", return_value=""):
            assert _is_ai_enabled() is False


def test_is_ai_enabled_with_key():
    """有 key 时返回 True"""
    import os
    from unittest.mock import patch
    with patch("os.environ.get", return_value="sk-xxxx"):
        assert _is_ai_enabled() is True
