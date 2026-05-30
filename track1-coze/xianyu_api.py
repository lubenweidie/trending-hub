"""闲鱼 MTOP API 纯 HTTP 客户端

零浏览器、零 CDP、零 JS eval — 纯 Python requests。
一次导出 Cookie → 持久复用 → 全自动上架。

使用:
  python xianyu_api.py setup          导出Cookie（从浏览器复制）
  python xianyu_api.py test           测试连接（验证Cookie是否有效）
  python xianyu_api.py publish <id>   发布商品
"""
import hashlib
import json
import os
import re
import sys
import time
import uuid
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
COOKIE_FILE = HERE / ".xianyu_cookie"
API_BASE = "https://h5api.m.taobao.com/h5"
APP_KEY = "12574478"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36"


def load_products():
    with open(HERE / "products.json", "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# Cookie 管理
# ============================================================

def save_cookie(cookie_str: str):
    """保存 Cookie 到文件"""
    COOKIE_FILE.write_text(cookie_str.strip(), encoding="utf-8")
    # 提取 _m_h5_tk token seed
    m = re.search(r'_m_h5_tk=([^_;]+)', cookie_str)
    if m:
        token = m.group(1).split("_")[0]
        print(f"[OK] Cookie 已保存 (token: {token[:16]}...)")
    else:
        print("[WARN] Cookie 中未找到 _m_h5_tk，MTOP 签名可能失败")


def load_cookie() -> str:
    """加载 Cookie"""
    if COOKIE_FILE.exists():
        return COOKIE_FILE.read_text(encoding="utf-8").strip()
    return ""


def get_token_seed() -> Optional[str]:
    """从 Cookie 提取 MTOP token seed (用于签名)"""
    cookie = load_cookie()
    m = re.search(r'_m_h5_tk=([^_;]+)', cookie)
    if m:
        return m.group(1).split("_")[0]
    return None


# ============================================================
# MTOP 签名与请求
# ============================================================

def mtop_sign(token_seed: str, data: str = "{}") -> tuple:
    """MTOP H5 签名算法

    签名串: token + "&" + timestamp + "&" + appKey + "&" + data
    签名: MD5(签名串)
    返回: (timestamp, sign_hash)
    """
    timestamp = str(int(time.time() * 1000))
    sign_str = f"{token_seed}&{timestamp}&{APP_KEY}&{data}"
    sign_hash = hashlib.md5(sign_str.encode()).hexdigest()
    return timestamp, sign_hash


def mtop_request(api: str, version: str = "1.0",
                 data: dict = None, method: str = "GET") -> dict:
    """发送 MTOP API 请求"""
    token_seed = get_token_seed()
    if not token_seed:
        raise RuntimeError("未找到 MTOP token，请先执行 setup 导入 Cookie")

    cookie = load_cookie()
    if not cookie:
        raise RuntimeError("未加载 Cookie，请先执行 setup 导入 Cookie")

    data_str = json.dumps(data or {}, ensure_ascii=False, separators=(",", ":"))
    timestamp, sign = mtop_sign(token_seed, data_str)

    url = f"{API_BASE}/{api}/{version}/"
    params = {
        "jsv": "2.7.3",
        "appKey": APP_KEY,
        "t": timestamp,
        "sign": sign,
        "api": api,
        "v": version,
        "type": "originaljson",
        "dataType": "json",
    }

    if method == "POST":
        params["data"] = data_str

    headers = {
        "User-Agent": USER_AGENT,
        "Referer": "https://www.goofish.com/",
        "Origin": "https://www.goofish.com",
        "Cookie": cookie,
    }

    if method == "POST":
        resp = requests.post(url, params=params, headers=headers, timeout=30)
    else:
        resp = requests.get(url, params=params, headers=headers, timeout=30)

    resp.raise_for_status()
    result = resp.json()

    # 检查 MTOP 级别错误
    ret = result.get("ret", [])
    if ret and "SUCCESS" not in str(ret):
        error_msg = str(ret)
        # Session 过期
        if "SESSION_EXPIRED" in error_msg or "TOKEN_EXPIRED" in error_msg:
            raise RuntimeError(
                "Cookie 已过期，请重新获取。\n"
                "1. 打开 Chrome 访问 https://www.goofish.com/ 并登录\n"
                "2. F12 → Application → Cookies → 复制所有 Cookie\n"
                "3. 运行: python xianyu_api.py setup"
            )
        raise RuntimeError(f"MTOP API 错误: {error_msg}")

    return result.get("data", {})


# ============================================================
# 闲鱼发布 API
# ============================================================

def publish_item(product_data: dict) -> dict:
    """发布商品到闲鱼（PC Web 版 API）

    product_data 字段:
      - title: 标题 (必填)
      - description: 描述 (必填)
      - price: 价格 (必填，单位: 分)
      - categoryId: 类目ID (必填)
      - images: 图片URL列表 (必填，最多9张)
      - location: 地址信息 {province, city, district}
      - freight: 运费模板 {"type": "free"|"post"}
      - condition: 成色 1=全新 2=几乎全新 3=轻微使用
    """
    # PC Web 版需要额外字段
    if "uniqueCode" not in product_data:
        product_data["uniqueCode"] = uuid.uuid4().hex[:32]
    if "bizcode" not in product_data:
        product_data["bizcode"] = "pcMainPublish"
    if "publishScene" not in product_data:
        product_data["publishScene"] = "pcMainPublish"

    api = "mtop.idle.pc.idleitem.publish"
    return mtop_request(api, "1.0", product_data, method="POST")


def get_categories(parent_id: str = "0") -> list:
    """获取闲鱼类目列表"""
    api = "mtop.idle.pc.idleitem.category"
    data = mtop_request(api, "1.0", {"parentId": parent_id})
    return data if isinstance(data, list) else data.get("categoryList", [])


def get_user_info() -> dict:
    """获取当前登录用户信息（测试 Cookie 是否有效）"""
    api = "mtop.idle.web.user.page.nav"
    return mtop_request(api, "1.0", {})


# ============================================================
# 从商品配置构建发布数据
# ============================================================

# 闲鱼虚拟商品默认类目ID（虚拟商品 > 其他虚拟商品）
DEFAULT_VIRTUAL_CATEGORY_ID = "50025969"


def build_publish_data(product_id: str) -> dict:
    """从 products.json + 文案构建闲鱼发布数据结构"""
    products = load_products()
    product = next((p for p in products["products"] if p["id"] == product_id), None)
    if not product:
        raise ValueError(f"产品不存在: {product_id}")

    # 读文案提取标题和描述
    from xianyu_publisher import extract_listing_info
    info = extract_listing_info(product)

    title = info["title"]
    price_yuan = info["price"]
    description = info["description"]

    # 截断标题到闲鱼限制（30字/60字节）
    if len(title) > 60:
        title = title[:57] + "..."

    # 尝试从 exports 目录自动获取图片
    images = product.get("xianyu_images", [])
    if not images:
        img_dir = HERE / "exports" / product_id / "images"
        if img_dir.exists():
            images = [str(p.absolute()) for p in sorted(img_dir.glob("*.png"))[:9]]

    category_id = product.get("xianyu_category_id", "")
    if not category_id:
        # 虚拟商品默认类目
        category_id = products.get("闲鱼_config", {}).get(
            "default_category_id", DEFAULT_VIRTUAL_CATEGORY_ID
        )

    return {
        "title": title,
        "price": int(price_yuan * 100),  # 转成分
        "description": description[:5000],
        "categoryId": category_id,
        "images": images,
        "condition": product.get("xianyu_condition", 1),  # 1=全新
        "freight": product.get("xianyu_freight", {"type": "free"}),
        "location": product.get("xianyu_location", {
            "province": "广东",
            "city": "深圳",
            "district": "南山区",
        }),
        "itemType": "virtual",
        # PC 版发布必需的额外字段
        "itemTypeStr": "b",
        "quantity": "1",
        "freebies": False,
        "simpleItem": "true",
    }


# ============================================================
# 命令行
# ============================================================

def cmd_setup():
    """交互式导入 Cookie"""
    print("\n" + "=" * 55)
    print("  闲鱼 Cookie 导入")
    print("=" * 55)
    print()
    print("请按以下步骤获取 Cookie：")
    print()
    print("  1. 打开 Chrome → 访问 https://www.goofish.com/")
    print("  2. 扫码/密码登录你的闲鱼账号")
    print("  3. F12 打开开发者工具 → Application 标签")
    print("  4. 左侧 Cookies → https://www.goofish.com")
    print("  5. 复制所有 Cookie（选中全部 → 右键 Copy）")
    print()
    print("或者从浏览器地址栏运行:")
    print('  javascript:copy(document.cookie)')
    print()

    cookie_str = input("粘贴 Cookie 字符串: ").strip()
    if not cookie_str:
        print("[取消] 未输入")
        return

    save_cookie(cookie_str)

    # 测试连接
    print("\n测试连接...")
    try:
        user = get_user_info()
        display_name = ""
        if isinstance(user, dict):
            display_name = user.get("displayName", user.get("nick", ""))
        if display_name:
            print(f"[OK] 连接成功！当前用户: {display_name}")
        else:
            print(f"[OK] 连接成功！")
    except Exception as e:
        print(f"[FAIL] 连接失败: {e}")
        print("Cookie 可能已过期或格式不正确，请重试")


def cmd_test():
    """测试 Cookie 是否有效"""
    if not load_cookie():
        print("未找到 Cookie，请先运行: python xianyu_api.py setup")
        return
    print("测试 MTOP 连接...")
    try:
        user = get_user_info()
        print(f"[OK] Cookie 有效！")
        if isinstance(user, dict):
            print(json.dumps(user, ensure_ascii=False, indent=2)[:500])
    except Exception as e:
        print(f"[FAIL] {e}")


def cmd_publish(product_id: str):
    """通过 API 发布商品"""
    if not load_cookie():
        print("未找到 Cookie，请先运行: python xianyu_api.py setup")
        return

    print(f"\n{'=' * 55}")
    print(f"  API 发布: {product_id}")
    print(f"{'=' * 55}")

    try:
        data = build_publish_data(product_id)
        print(f"  标题: {data['title'][:50]}")
        print(f"  价格: ¥{data['price']/100:.2f}")
        print(f"  描述: {len(data['description'])} 字")

        result = publish_item(data)
        print(f"\n[OK] 发布成功！")
        print(json.dumps(result, ensure_ascii=False, indent=2)[:500])

        # 更新 products.json
        products = load_products()
        for p in products["products"]:
            if p["id"] == product_id:
                p["闲鱼上架状态"] = "已上架"
                p["闲鱼上架时间"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                if isinstance(result, dict):
                    p["闲鱼_item_id"] = result.get("itemId", "")
        with open(HERE / "products.json", "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"\n[FAIL] 发布失败: {e}")


def cmd_js(product_id: str):
    """生成浏览器 Console JS 发布代码（用浏览器自身 session，无需 cookie）"""
    try:
        data = build_publish_data(product_id)
    except Exception as e:
        print(f"[FAIL] 构建发布数据失败: {e}")
        return

    # 移除 images 字段（图片需要先上传获取URL后再填入）
    images = data.pop("images", [])

    js_code = f"""// 闲鱼 MTOP PC 发布: {data['title'][:40]}
// 复制整段代码 → 在 goofish.com 控制台粘贴 → 回车执行

(function() {{
  // 生成 uniqueCode
  var uniqueCode = crypto.randomUUID ? crypto.randomUUID().replace(/-/g, '') : 'xxxxxxxxxxxx4xxxyxxxxxxxxxxxxxxx'.replace(/[xy]/g, function(c) {{ var r = Math.random()*16|0, v = c === 'x' ? r : (r&0x3|0x8); return v.toString(16); }});

  var publishData = {json.dumps(data, ensure_ascii=False)};
  publishData.uniqueCode = uniqueCode;
  publishData.bizcode = 'pcMainPublish';
  publishData.publishScene = 'pcMainPublish';

  console.log('正在发布: ' + publishData.title);
  console.log('uniqueCode: ' + uniqueCode);

  window.lib.mtop.request({{
    api: 'mtop.idle.pc.idleitem.publish',
    v: '1.0',
    data: publishData
  }}).then(function(res) {{
    var ret = res.ret || [];
    if (ret[0] && ret[0].indexOf('SUCCESS') === 0) {{
      console.log('===== 发布成功! =====');
      console.log('itemId:', res.data && res.data.itemId);
      console.log(JSON.stringify(res, null, 2));
    }} else {{
      console.log('===== 发布失败 =====');
      console.log('ret:', JSON.stringify(ret));
      console.log('完整响应:', JSON.stringify(res, null, 2));
    }}
  }}).catch(function(e) {{
    console.error('===== 请求异常 =====');
    console.error('ret:', JSON.stringify(e.ret || e));
    console.error('message:', e.message || '');
    console.error('完整:', JSON.stringify(e, null, 2));
  }});
}})();
"""

    print(f"\n{'=' * 55}")
    print(f"  浏览器 Console JS 发布: {product_id}")
    print(f"{'=' * 55}")
    print(f"  标题: {data['title'][:50]}")
    print(f"  价格: ¥{data['price']/100:.2f}")
    print(f"  描述: {len(data['description'])} 字")

    if images:
        print(f"\n  [注意] 需要先在浏览器端上传 {len(images)} 张图片")
        print(f"  图片路径: exports/{product_id}/images/")
        print(f"  图片URL获取后，需手动填入 images 数组")

    print(f"\n{'─' * 55}")
    print("  请按以下步骤操作：")
    print(f"  1. 打开 Chrome → https://www.goofish.com/ 并登录")
    print(f"  2. F12 → Console 控制台")
    print(f"  3. 粘贴下方 JS 代码 → 回车")
    print(f"{'─' * 55}\n")
    print(js_code)

    # 同时写入文件
    js_path = HERE / "exports" / product_id / "publish.js"
    js_path.parent.mkdir(parents=True, exist_ok=True)
    js_path.write_text(js_code, encoding="utf-8")
    print(f"\n[JS代码已保存: {js_path}]")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n可用命令:")
        print("  setup            导入Cookie（从浏览器复制一次，持久复用）")
        print("  test             测试Cookie是否有效")
        print("  publish <id>     通过API发布商品")
        print("  js <id>          生成浏览器Console JS发布代码")
        return

    cmd = sys.argv[1]

    if cmd == "setup":
        cmd_setup()
    elif cmd == "test":
        cmd_test()
    elif cmd == "publish":
        pid = sys.argv[2] if len(sys.argv) > 2 else None
        if pid:
            cmd_publish(pid)
        else:
            print("用法: python xianyu_api.py publish <product_id>")
    elif cmd == "js":
        pid = sys.argv[2] if len(sys.argv) > 2 else None
        if pid:
            cmd_js(pid)
        else:
            print("用法: python xianyu_api.py js <product_id>")
    else:
        print(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()
