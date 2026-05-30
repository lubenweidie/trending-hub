"""主入口：串行调用所有采集器，互不阻断"""
import time
from typing import Dict, List
from .base import collect_with_fallback, TrendItem

# 延迟导入：单个采集器失败不影响其他导入
def _safe_import(module_name):
    try:
        return __import__(module_name, fromlist=['collect'])
    except ImportError:
        return None

def run_all() -> Dict[str, List[TrendItem]]:
    results = {}

    # 微博
    try:
        from . import weibo
        results["weibo"] = collect_with_fallback("weibo", weibo.collect_weibo)
    except Exception as e:
        print(f"[SKIP] weibo: {e}")
        results["weibo"] = []
    time.sleep(0.5)

    # 知乎
    try:
        from . import zhihu
        results["zhihu"] = collect_with_fallback("zhihu", zhihu.collect_zhihu)
    except Exception as e:
        print(f"[SKIP] zhihu: {e}")
        results["zhihu"] = []
    time.sleep(0.5)

    # 百度
    try:
        from . import baidu
        results["baidu"] = collect_with_fallback("baidu", baidu.collect_baidu)
    except Exception as e:
        print(f"[SKIP] baidu: {e}")
        results["baidu"] = []
    time.sleep(0.5)

    # 新华网
    try:
        from . import xinhuanet
        results["xinhuanet"] = collect_with_fallback("xinhuanet", xinhuanet.collect_xinhuanet)
    except Exception as e:
        print(f"[SKIP] xinhuanet: {e}")
        results["xinhuanet"] = []
    time.sleep(0.5)

    # 人民日报
    try:
        from . import people_rm
        results["people_rm"] = collect_with_fallback("people_rm", people_rm.collect_people_rm)
    except Exception as e:
        print(f"[SKIP] people_rm: {e}")
        results["people_rm"] = []

    total = sum(len(v) for v in results.values())
    print(f"\n[SUMMARY] 共采集 {total} 条热榜（{len(results)}个平台）")
    return results


if __name__ == "__main__":
    run_all()
