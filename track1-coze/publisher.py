"""Coze API 发布器 — 自动创建/更新/发布 Bot"""
import json
import sys
import time
import requests
from typing import Optional, Dict, Any
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from config import (
    COZE_API_BASE, COZE_API_KEY, COZE_WORKSPACE_ID,
    load_products, save_products, get_prompt
)


class CozePublisher:
    """Coze 平台 Bot 发布器"""

    def __init__(self, api_key: str = "", workspace_id: str = ""):
        self.api_key = api_key or COZE_API_KEY
        self.workspace_id = workspace_id or COZE_WORKSPACE_ID
        self.base_url = COZE_API_BASE
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    def _post(self, path: str, body: dict, timeout: int = 30) -> dict:
        """统一 POST 请求"""
        url = f"{self.base_url}{path}"
        resp = self.session.post(url, json=body, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"Coze API error: {data.get('msg', 'unknown')} (code={data.get('code')})")
        return data.get("data", {})

    def _get(self, path: str, params: dict = None, timeout: int = 30) -> dict:
        """统一 GET 请求"""
        url = f"{self.base_url}{path}"
        resp = self.session.get(url, params=params or {}, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"Coze API error: {data.get('msg', 'unknown')} (code={data.get('code')})")
        return data.get("data", {})

    def create_bot(self, product: dict) -> str:
        """从商品配置创建 Coze Bot，返回 bot_id"""
        cfg = product["coze_config"]
        body = {
            "space_id": self.workspace_id,
            "name": cfg["bot_name"],
            "description": cfg["bot_description"],
            "icon_file_id": cfg.get("icon"),
            "model_id": cfg.get("model", "doubao-pro-32k"),
            "prompt_info": {
                "prompt": get_prompt(product["id"]) or "",
            }
        }
        data = self._post("/v1/bot/create", body)
        bot_id = data["bot_id"]
        return bot_id

    def update_bot(self, bot_id: str, product: dict) -> None:
        """更新已有 Bot 的配置"""
        cfg = product["coze_config"]
        body = {
            "bot_id": bot_id,
            "space_id": self.workspace_id,
            "name": cfg["bot_name"],
            "description": cfg["bot_description"],
            "prompt_info": {
                "prompt": get_prompt(product["id"]) or "",
            }
        }
        self._post("/v1/bot/update", body)

    def publish_bot(self, bot_id: str) -> str:
        """发布 Bot 并获取分享链接"""
        data = self._post("/v1/bot/publish", {
            "bot_id": bot_id,
            "connector_ids": [1024],  # 1024 = Coze 商店
        })
        # 发布是异步的，轮询等待
        publish_id = data.get("publish_id", "")
        for _ in range(30):
            status_data = self._get("/v1/bot/publish_status", {
                "bot_id": bot_id,
                "publish_id": publish_id,
            })
            if status_data.get("status") == "published":
                break
            time.sleep(2)

        bot_data = self._get("/v1/bot/get_detail", {"bot_id": bot_id})
        return bot_data.get("bot_url", "")

    def get_bot_status(self, bot_id: str) -> dict:
        """查询 Bot 状态"""
        return self._get("/v1/bot/get_detail", {"bot_id": bot_id})

    def publish_product(self, product_id: str) -> Dict[str, Any]:
        """一键发布：创建/更新 Bot + 发布"""
        products = load_products()
        product = next((p for p in products["products"] if p["id"] == product_id), None)
        if not product:
            raise ValueError(f"产品 {product_id} 不存在")

        coze_bot_id = product.get("coze_bot_id")
        if coze_bot_id:
            print(f"[更新] 更新已有 Bot: {coze_bot_id}")
            self.update_bot(coze_bot_id, product)
        else:
            print(f"[创建] 创建新 Bot: {product['name']}")
            coze_bot_id = self.create_bot(product)
            product["coze_bot_id"] = coze_bot_id

        print(f"[发布] 发布 Bot: {coze_bot_id}")
        bot_url = self.publish_bot(coze_bot_id)

        product["coze_bot_url"] = bot_url
        product["coze_bot_published_at"] = time.strftime("%Y-%m-%d %H:%M")
        product["coze_status"] = "published"
        save_products(products)

        return {
            "product_id": product_id,
            "bot_id": coze_bot_id,
            "bot_url": bot_url,
            "status": "published",
        }

    def publish_all(self) -> list:
        """批量发布全部未上架产品"""
        products = load_products()
        results = []
        for p in products["products"]:
            if p.get("coze_status") != "published":
                try:
                    result = self.publish_product(p["id"])
                    results.append(result)
                    print(f"[OK] {p['name']} → {result['bot_url']}")
                except Exception as e:
                    print(f"[FAIL] {p['name']}: {e}")
                    results.append({"product_id": p["id"], "status": "failed", "error": str(e)})
            else:
                print(f"[SKIP] {p['name']} 已发布")
        return results


def main():
    import sys
    if not COZE_API_KEY:
        print("请设置环境变量 COZE_API_KEY")
        print("获取方式: https://www.coze.cn/open/oauth/personal_token")
        sys.exit(1)

    publisher = CozePublisher()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"

    if cmd == "publish":
        pid = sys.argv[2] if len(sys.argv) > 2 else None
        if pid:
            result = publisher.publish_product(pid)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("用法: python publisher.py publish <product_id>")
            print("可用产品ID:")
            for p in load_products()["products"]:
                print(f"  {p['id']} — {p['name']}")

    elif cmd == "publish-all":
        results = publisher.publish_all()
        ok = sum(1 for r in results if r.get("status") == "published")
        fail = sum(1 for r in results if r.get("status") == "failed")
        print(f"\n总计: {len(results)} | 成功: {ok} | 失败: {fail}")

    elif cmd == "status":
        pid = sys.argv[2] if len(sys.argv) > 2 else None
        if pid:
            product = next(
                (p for p in load_products()["products"] if p["id"] == pid), None
            )
            if not product:
                print(f"产品 {pid} 不存在")
                return
            if product.get("coze_bot_id"):
                detail = publisher.get_bot_status(product["coze_bot_id"])
                print(json.dumps(detail, ensure_ascii=False, indent=2))
            else:
                print(f"产品 {product['name']} 尚未创建 Coze Bot")

    elif cmd == "list":
        products = load_products()
        print(f"{'ID':<25} {'名称':<15} {'Coze状态':<12} {'闲鱼状态'}")
        print("-" * 70)
        for p in products["products"]:
            coze = p.get("coze_status", "未创建")
            xianyu = p.get("闲鱼上架状态", "待上架")
            print(f"{p['id']:<25} {p['name']:<15} {coze:<12} {xianyu}")

    else:
        print("命令: publish <id> | publish-all | status <id> | list")


if __name__ == "__main__":
    main()
