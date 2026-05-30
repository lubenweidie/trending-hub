"""采集器共享模块：统一配置、重试、包装器"""
import time
import random
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass, field

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
}
TIMEOUT = 30
RETRY_DELAYS = [1, 3, 9]  # 指数退避（秒）


@dataclass
class TrendItem:
    """所有采集器统一返回格式"""
    title: str
    url: str
    platform: str
    hot_score: Optional[int] = None
    raw_data: Optional[Dict] = field(default_factory=dict)


def fetch_with_retry(url: str, **kwargs) -> requests.Response:
    """带指数退避重试的 HTTP GET"""
    last_error = None
    for i, delay in enumerate(RETRY_DELAYS):
        try:
            kwargs.setdefault('headers', HEADERS)
            kwargs.setdefault('timeout', TIMEOUT)
            resp = requests.get(url, **kwargs)
            resp.raise_for_status()
            return resp
        except Exception as e:
            last_error = e
            if i < len(RETRY_DELAYS) - 1:
                time.sleep(delay)
    raise last_error


def collect_with_fallback(name: str, func) -> List[TrendItem]:
    """采集包装器：异常时返回空列表，不阻断管线"""
    try:
        items = func()
        print(f"[OK] {name}: {len(items)}条")
        return items
    except Exception as e:
        import sys
        print(f"[FAIL] {name}: {type(e).__name__}", file=sys.stderr)
        return []
