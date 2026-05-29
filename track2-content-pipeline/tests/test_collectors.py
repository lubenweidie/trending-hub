"""采集器测试"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from collectors.base import collect_with_fallback, TrendItem

def test_collector_failure_returns_empty():
    """采集器异常时返回空列表"""
    def broken_collector():
        raise ConnectionError("模拟网络故障")
    result = collect_with_fallback("mock_broken", broken_collector)
    assert result == []

def test_collector_success_returns_items():
    """正常采集返回TrendItem列表"""
    def ok_collector():
        return [TrendItem(title="测试", url="https://example.com", platform="test")]
    result = collect_with_fallback("mock_ok", ok_collector)
    assert len(result) == 1
    assert result[0].title == "测试"

def test_trend_item_fields():
    """TrendItem字段完整"""
    item = TrendItem(title="测试", url="https://example.com", platform="weibo")
    assert item.title == "测试"
    assert item.platform == "weibo"
