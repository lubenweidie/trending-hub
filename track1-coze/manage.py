"""轨道1 商品上架管理系统（Coze全自动 + 闲鱼安全半自动）

命令一览:
  python manage.py list                    查看所有商品状态
  python manage.py status <id>             查看单个商品详情
  python manage.py coze publish <id>       全自动发布Bot到Coze (API)
  python manage.py coze publish-all        批量全自动发布所有Bot
  python manage.py coze status <id>        查看Bot状态
  python manage.py copy generate <id>      AI生成闲鱼文案
  python manage.py copy optimize <id>      AI优化闲鱼文案
  python manage.py copy preview <id>       预览闲鱼文案
  python manage.py copy generate-all       批量生成所有文案
  python manage.py xianyu api setup        导入闲鱼Cookie（一次导入，持久复用·纯HTTP）
  python manage.py xianyu api test         测试闲鱼API连接
  python manage.py xianyu api publish <id> 通过MTOP API直接发布到闲鱼（纯HTTP·零浏览器）
  python manage.py xianyu api js <id>     生成浏览器Console JS发布代码（绕过cookie问题）
  python manage.py xianyu package <id>     生成闲鱼素材包(文案+图片+手机页)
  python manage.py xianyu package-all      批量生成所有素材包
  python manage.py xianyu mark <id> <状态>  标记闲鱼上架状态
  python manage.py xianyu quickguide       打印闲鱼APP快速上架指南
  python manage.py images <id>             自动生成5张商品主图
  python manage.py images-all              批量生成所有商品主图
  python manage.py onestep <id>            一键: Coze+图片+闲鱼(API优先·自动回退素材包)
  python manage.py dashboard               查看收入仪表盘概览

安全说明:
  - Coze 发布: 纯 API 调用，零封号风险
  - 闲鱼 MTOP API: 纯 HTTP 请求（模拟APP行为），无浏览器/CDP痕迹
  - 闲鱼素材包: 仅生成文案+图片，不触碰浏览器/APP，零风控
"""
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

# Windows console encoding fix
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from config import (
    BASE_DIR, load_products, save_products, load_status, save_status,
    get_prompt
)


def cmd_list():
    """列出所有商品及其状态"""
    products = load_products()
    print(f"\n{'ID':<24} {'名称':<15} {'Coze':<10} {'闲鱼':<10} {'价格'}")
    print("-" * 80)
    for p in products["products"]:
        coze_s = p.get("coze_status", "未创建")
        xy_s = p.get("闲鱼上架状态", "待上架")
        price = f"¥{p['pricing']['standard']}/{p['pricing']['premium']}"
        print(f"{p['id']:<24} {p['name']:<15} {coze_s:<10} {xy_s:<10} {price}")

    # 统计
    total = len(products["products"])
    published = sum(1 for p in products["products"] if p.get("coze_status") == "published")
    listed = sum(1 for p in products["products"] if p.get("闲鱼上架状态") == "已上架")
    print(f"\n总计: {total} | Coze已发布: {published} | 闲鱼已上架: {listed}")
    print(f"预估总销售额（全部售出1份标准版）: ¥{sum(p['pricing']['standard'] for p in products['products'])}")


def cmd_status(product_id: str):
    """查看单个商品完整信息"""
    products = load_products()
    product = next((p for p in products["products"] if p["id"] == product_id), None)
    if not product:
        print(f"产品 {product_id} 不存在")
        print("可用ID: " + ", ".join(p["id"] for p in products["products"]))
        return

    print(f"\n{'='*60}")
    print(f"  {product['name']} ({product['id']})")
    print(f"{'='*60}")
    print(f"分类:     {product['category']}")
    print(f"目标用户: {', '.join(product['target_users'])}")
    print(f"搭建时间: {product['build_time_hours']}h")
    print(f"定价:     标准版 ¥{product['pricing']['standard']} | {product['pricing']['premium_name']} ¥{product['pricing']['premium']}")
    print(f"Coze状态: {product.get('coze_status', '未创建')}")
    if product.get("coze_bot_id"):
        print(f"Coze Bot: {product['coze_bot_id']}")
    if product.get("coze_bot_url"):
        print(f"Bot链接:  {product['coze_bot_url']}")
    print(f"闲鱼状态: {product.get('闲鱼上架状态', '待上架')}")
    if product.get("闲鱼_url"):
        print(f"闲鱼链接: {product['闲鱼_url']}")
    print(f"\nPrompt文件: {product['prompt_file']}")
    print(f"文案文件:   {product['copy_file']}")

    # 检查文件状态
    prompt_path = BASE_DIR / product["prompt_file"]
    copy_path = BASE_DIR / product["copy_file"]
    print(f"\n文件状态:")
    print(f"  Prompt: {'✓ 已就绪' if prompt_path.exists() else '✗ 缺失'} ({prompt_path.stat().st_size if prompt_path.exists() else 0} bytes)")
    print(f"  闲鱼文案: {'✓ 已就绪' if copy_path.exists() else '✗ 缺失'} ({copy_path.stat().st_size if copy_path.exists() else 0} bytes)")


def cmd_coze_publish(product_id: str):
    """发布单个Bot到Coze"""
    from publisher import CozePublisher
    if not os.getenv("COZE_API_KEY"):
        print("请先设置环境变量 COZE_API_KEY")
        print("获取: https://www.coze.cn/open/oauth/personal_token")
        return
    pub = CozePublisher()
    result = pub.publish_product(product_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_coze_publish_all():
    """批量发布"""
    from publisher import CozePublisher
    if not os.getenv("COZE_API_KEY"):
        print("请先设置环境变量 COZE_API_KEY")
        return
    pub = CozePublisher()
    results = pub.publish_all()
    ok = sum(1 for r in results if r.get("status") == "published")
    print(f"\n发布完成: {ok}/{len(results)} 成功")


def cmd_coze_status(product_id: str):
    """查看Coze Bot状态"""
    from publisher import CozePublisher
    if not os.getenv("COZE_API_KEY"):
        print("请先设置环境变量 COZE_API_KEY")
        return
    pub = CozePublisher()
    products = load_products()
    product = next((p for p in products["products"] if p["id"] == product_id), None)
    if not product:
        print(f"产品 {product_id} 不存在")
        return
    bot_id = product.get("coze_bot_id")
    if not bot_id:
        print(f"{product['name']}: 尚未创建Coze Bot")
        return
    detail = pub.get_bot_status(bot_id)
    print(json.dumps(detail, ensure_ascii=False, indent=2))


def cmd_copy_generate(product_id: str):
    """AI生成闲鱼文案"""
    from generate_copy import generate_copy
    copy = generate_copy(product_id)
    products = load_products()
    product = next((p for p in products["products"] if p["id"] == product_id), None)
    if product:
        copy_path = BASE_DIR / product["copy_file"]
        copy_path.write_text(copy, encoding="utf-8")
        print(f"已保存: {copy_path}")
    print(copy)


def cmd_copy_optimize(product_id: str):
    """AI优化闲鱼文案"""
    from generate_copy import generate_copy
    copy = generate_copy(product_id, optimize=True)
    products = load_products()
    product = next((p for p in products["products"] if p["id"] == product_id), None)
    if product:
        copy_path = BASE_DIR / product["copy_file"]
        copy_path.write_text(copy, encoding="utf-8")
        print(f"已保存: {copy_path}")
    print(copy)


def cmd_copy_preview(product_id: Optional[str] = None):
    """预览闲鱼文案"""
    from generate_copy import preview_copy
    if product_id:
        print(preview_copy(product_id))
    else:
        for p in load_products()["products"]:
            print(f"\n{'='*60}")
            print(f"  {p['name']} ({p['id']})")
            print(f"{'='*60}")
            content = preview_copy(p["id"])
            print(content[:400] + "..." if len(content) > 400 else content)


def cmd_copy_generate_all():
    """批量生成"""
    from generate_copy import generate_all
    generate_all()


def cmd_xianyu_mark(product_id: str, status: str):
    """标记闲鱼上架状态"""
    valid_statuses = ["待上架", "已上架", "已下架", "审核中", "已售出"]
    if status not in valid_statuses:
        print(f"有效状态: {', '.join(valid_statuses)}")
        return
    products = load_products()
    product = next((p for p in products["products"] if p["id"] == product_id), None)
    if not product:
        print(f"产品 {product_id} 不存在")
        return
    product["闲鱼上架状态"] = status
    if status == "已上架":
        product["闲鱼上架时间"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    save_products(products)
    print(f"{product['name']} → 闲鱼状态: {status}")


def cmd_dashboard():
    """收入仪表盘概览"""
    products = load_products()
    total = len(products["products"])
    coze_ok = sum(1 for p in products["products"] if p.get("coze_status") == "published")
    xy_ok = sum(1 for p in products["products"] if p.get("闲鱼上架状态") == "已上架")

    std_total = sum(p["pricing"]["standard"] for p in products["products"])
    prem_total = sum(p["pricing"]["premium"] for p in products["products"])

    print(f"""
╔══════════════════════════════════════════╗
║      🚀 轨道1 · Coze模板 销售看板        ║
╠══════════════════════════════════════════╣
║ 产品总数:        {total:>4}                    ║
║ Coze已发布:      {coze_ok:>4}                    ║
║ 闲鱼已上架:      {xy_ok:>4}                    ║
╠══════════════════════════════════════════╣
║ 收入预估（全售标准版1份）:               ║
║   标准版总计:   ¥{std_total:>6}                  ║
║   进阶版总计:   ¥{prem_total:>6}                  ║
║   全售最高:     ¥{std_total + prem_total:>6}                  ║
╠══════════════════════════════════════════╣
║ 定制单（¥200-900/单）:                   ║
║   月目标5单*¥500 = ¥2500                 ║
║   年化 = ¥30,000                         ║
╚══════════════════════════════════════════╝
""")


def cmd_xianyu_package(product_id: str = None):
    """生成闲鱼上架素材包"""
    if not product_id:
        print("用法: manage.py xianyu package <product_id>")
        print("可用ID: " + ", ".join(p["id"] for p in load_products()["products"]))
        return
    from xianyu_publisher import package_product
    package_product(product_id)


def cmd_xianyu_package_all():
    """批量生成全部素材包"""
    from xianyu_publisher import package_all
    package_all()


def cmd_xianyu_quickguide():
    """打印闲鱼快速上架指南"""
    from xianyu_publisher import print_quickguide
    print_quickguide()


def cmd_xianyu_api_setup():
    """导入闲鱼Cookie（交互式）"""
    from xianyu_api import cmd_setup
    cmd_setup()


def cmd_xianyu_api_test():
    """测试闲鱼API连接"""
    from xianyu_api import cmd_test
    cmd_test()


def cmd_xianyu_api_publish(product_id: str):
    """通过MTOP HTTP API直接发布到闲鱼"""
    from xianyu_api import cmd_publish
    cmd_publish(product_id)


def cmd_xianyu_api_js(product_id: str):
    """生成浏览器Console JS发布代码（绕过cookie过期问题）"""
    from xianyu_api import cmd_js
    cmd_js(product_id)


def cmd_images(product_id: str = None):
    """自动生成商品主图"""
    if not product_id:
        print("用法: manage.py images <product_id>")
        print("可用ID: " + ", ".join(p["id"] for p in load_products()["products"]))
        return
    from image_generator import generate_product_images
    generate_product_images(product_id)


def cmd_images_all():
    """批量生成所有商品主图"""
    from image_generator import generate_all
    generate_all()


def cmd_onestep(product_id: str):
    """一键全自动: Coze发布 + 图片生成 + 闲鱼发布(API优先·自动回退)"""
    print(f"\n{'=' * 60}")
    print(f"  一键发布: {product_id}")
    print(f"{'=' * 60}")

    # Step 1: Coze 全自动发布 (API)
    print(f"\n>>> 步骤 1/3: Coze Bot 发布 [全自动·API]")
    try:
        cmd_coze_publish(product_id)
    except Exception as e:
        print(f"[Coze] 发布失败: {e}")
        if input("继续后续步骤？[y/N] ").strip().lower() != "y":
            return

    # Step 2: 自动生成主图
    print(f"\n>>> 步骤 2/3: 生成商品主图 [Pillow]")
    try:
        from image_generator import generate_product_images
        generate_product_images(product_id)
    except ImportError:
        print("  [跳过] 请安装 Pillow: pip install Pillow")
    except Exception as e:
        print(f"  [图片] 生成失败: {e}")

    # Step 3: 闲鱼发布 — 优先 HTTP API，无 Cookie 则回退素材包
    print(f"\n>>> 步骤 3/3: 闲鱼发布")
    from xianyu_api import load_cookie
    if load_cookie():
        print("  Cookie 已配置，尝试 MTOP API 直发...")
        try:
            from xianyu_api import cmd_publish
            cmd_publish(product_id)
            print(f"\n{'=' * 60}")
            print(f"  全自动发布完成!")
            print(f"  Coze: 已发布 ✓")
            print(f"  闲鱼: API 已发布 ✓")
            print(f"{'=' * 60}")
            return
        except Exception as e:
            print(f"  [API] 发布失败: {e}")
            print("  → 试试浏览器 Console JS 模式...")

    # 尝试 JS Console 模式（用浏览器自己的 session）
    print(f"\n  [浏览器 Console JS 模式]")
    print(f"  API 不可用，但可以用浏览器 session 一键发布：")
    from xianyu_api import cmd_js
    cmd_js(product_id)
    print(f"\n  📋 复制上面的 JS 代码 → goofish.com 控制台 → 回车")

    # 同时生成素材包作为备用
    from xianyu_publisher import package_product
    pkg = package_product(product_id)
    from mobile_copy_page import generate_page
    generate_page(product_id)

    if pkg:
        print(f"\n{'=' * 60}")
        print(f"  完成! (素材包模式)")
        print(f"  Coze: 已发布 ✓")
        print(f"  主图: exports/{product_id}/images/ (5张)")
        print(f"  文案: exports/{product_id}/*.txt")
        print(f"  手机: exports/{product_id}/index.html")
        print(f"  📱 用手机打开 index.html → 一键复制 → 闲鱼发布")
        print(f"{'=' * 60}")

    print(f"\n[完成] {product_id} 全自动流程结束")


def print_help():
    print(__doc__)


def main():
    if len(sys.argv) < 2:
        print_help()
        return

    cmd = sys.argv[1]

    if cmd == "list":
        cmd_list()
    elif cmd == "status":
        cmd_status(sys.argv[2]) if len(sys.argv) > 2 else print_help()
    elif cmd == "dashboard":
        cmd_dashboard()
    elif cmd == "coze":
        sub = sys.argv[2] if len(sys.argv) > 2 else ""
        if sub == "publish":
            cmd_coze_publish(sys.argv[3]) if len(sys.argv) > 3 else print("用法: manage.py coze publish <id>")
        elif sub == "publish-all":
            cmd_coze_publish_all()
        elif sub == "status":
            cmd_coze_status(sys.argv[3]) if len(sys.argv) > 3 else print("用法: manage.py coze status <id>")
        else:
            print_help()
    elif cmd == "copy":
        sub = sys.argv[2] if len(sys.argv) > 2 else ""
        if sub == "generate":
            cmd_copy_generate(sys.argv[3]) if len(sys.argv) > 3 else print("用法: manage.py copy generate <id>")
        elif sub == "optimize":
            cmd_copy_optimize(sys.argv[3]) if len(sys.argv) > 3 else print("用法: manage.py copy optimize <id>")
        elif sub == "preview":
            cmd_copy_preview(sys.argv[3] if len(sys.argv) > 3 else None)
        elif sub == "generate-all":
            cmd_copy_generate_all()
        else:
            print_help()
    elif cmd == "xianyu":
        sub = sys.argv[2] if len(sys.argv) > 2 else ""
        if sub == "api":
            api_cmd = sys.argv[3] if len(sys.argv) > 3 else ""
            if api_cmd == "setup":
                cmd_xianyu_api_setup()
            elif api_cmd == "test":
                cmd_xianyu_api_test()
            elif api_cmd == "publish":
                if len(sys.argv) > 4:
                    cmd_xianyu_api_publish(sys.argv[4])
                else:
                    print("用法: manage.py xianyu api publish <product_id>")
            elif api_cmd == "js":
                if len(sys.argv) > 4:
                    cmd_xianyu_api_js(sys.argv[4])
                else:
                    print("用法: manage.py xianyu api js <product_id>")
            else:
                print("用法: manage.py xianyu api <setup|test|publish|js>")
        elif sub == "package":
            cmd_xianyu_package(sys.argv[3] if len(sys.argv) > 3 else None)
        elif sub == "package-all":
            cmd_xianyu_package_all()
        elif sub == "mark":
            cmd_xianyu_mark(sys.argv[3], sys.argv[4]) if len(sys.argv) > 4 else print("用法: manage.py xianyu mark <id> <状态>")
        elif sub == "quickguide":
            cmd_xianyu_quickguide()
        else:
            print_help()
    elif cmd == "onestep":
        pid = sys.argv[2] if len(sys.argv) > 2 else None
        if pid:
            cmd_onestep(pid)
        else:
            print("用法: manage.py onestep <product_id>")
    elif cmd == "images":
        pid = sys.argv[2] if len(sys.argv) > 2 else None
        if pid:
            cmd_images(pid)
        else:
            print("用法: manage.py images <product_id>")
    elif cmd == "images-all":
        cmd_images_all()
    else:
        print_help()


if __name__ == "__main__":
    main()
