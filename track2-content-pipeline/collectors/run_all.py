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

    # B站 — 已禁用
    results["bilibili"] = []

    # 掘金
    try:
        from . import juejin
        results["juejin"] = collect_with_fallback("juejin", juejin.collect_juejin)
    except Exception as e:
        print(f"[SKIP] juejin: {e}")
        results["juejin"] = []
    time.sleep(0.5)

    # V2EX
    try:
        from . import v2ex
        results["v2ex"] = collect_with_fallback("v2ex", v2ex.collect_v2ex)
    except Exception as e:
        print(f"[SKIP] v2ex: {e}")
        results["v2ex"] = []

    total = sum(len(v) for v in results.values())
    print(f"\n[SUMMARY] 共采集 {total} 条热榜（{len(results)}个平台）")
    return results


if __name__ == "__main__":
    run_all()
