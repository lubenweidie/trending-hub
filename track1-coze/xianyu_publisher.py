"""闲鱼上架素材打包器 — 安全模式（零浏览器自动化）

原理：生成"复制即用"的闲鱼APP上架素材，用户只需在手机上粘贴+选图+发布。
Coze 端全自动，闲鱼端30秒/个，不触发阿里风控。

使用方式:
  python xianyu_publisher.py package resume-optimizer   # 单个打包
  python xianyu_publisher.py package-all                # 批量打包
  python xianyu_publisher.py quickguide                 # 打印快速上架指南
"""
import json
import re
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
PACKAGE_DIR = HERE / "exports"


def load_products() -> dict:
    with open(HERE / "products.json", "r", encoding="utf-8") as f:
        return json.load(f)


def save_products(data: dict):
    with open(HERE / "products.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def extract_listing_info(product: dict) -> dict:
    """从商品配置+文案中提取闲鱼发布所需的所有信息"""
    copy_path = HERE / product["copy_file"]
    copy_text = ""
    if copy_path.exists():
        copy_text = copy_path.read_text(encoding="utf-8")

    # 提取标题
    title = ""
    m = re.search(r'```\n(.+?)\n```', copy_text)
    if m:
        title = m.group(1).strip()
    if not title:
        m = re.search(r'【(.+?)】', copy_text)
        if m:
            title = m.group(1).strip()
    if not title:
        title = f"AI{product['name']} Coze智能体模板 一键导入即用"

    # 提取标签
    tags = []
    m = re.search(r'`(.+?)`', copy_text)
    if m:
        tags = [t.strip() for t in m.group(1).split("` `") if t.strip()]

    # 构造闲鱼风格描述（纯文本，不用 markdown）
    description = build_xianyu_description(product, copy_text)

    return {
        "title": title,
        "price": product["pricing"]["standard"],
        "premium_price": product["pricing"]["premium"],
        "premium_name": product["pricing"]["premium_name"],
        "description": description,
        "tags": tags,
        "bot_name": product.get("coze_config", {}).get("bot_name", product["name"]),
    }


def build_xianyu_description(product: dict, copy_md: str) -> str:
    """将 markdown 文案转为闲鱼 APP 友好的纯文本描述"""
    # 提取关键信息块
    name = product["name"]
    category = product["category"]
    targets = "、".join(product["target_users"])
    std_price = product["pricing"]["standard"]
    prem_price = product["pricing"]["premium"]
    prem_name = product["pricing"]["premium_name"]
    prompt = ""
    prompt_path = HERE / product["prompt_file"]
    if prompt_path.exists():
        prompt = prompt_path.read_text(encoding="utf-8").strip()[:200] + "..."

    # 从 copy_md 提取 emoji 标记的功能列表
    features = []
    for line in copy_md.split("\n"):
        if line.strip().startswith("✅"):
            features.append(line.strip())

    desc = f"""【{name}】Coze AI 智能体模板

📌 适用人群：{targets}
📂 分类：{category}

━━━━━━ 功能介绍 ━━━━━━
"""
    if features:
        for f in features:
            desc += f + "\n"
    else:
        desc += f"""本智能体基于 Coze（扣子）平台搭建，导入即用。
核心能力：
{prompt}
"""

    desc += f"""
━━━━━━ 版本与价格 ━━━━━━
🔹 标准版：¥{std_price}
   → 智能体模板文件，一键导入你的 Coze 账号，永久使用

🔹 {prem_name}：¥{prem_price}
   → 标准版全部内容 + 深度定制优化

━━━━━━ 使用方式 ━━━━━━
1️⃣ 在应用商店下载"扣子"APP 或访问 coze.cn 注册（免费）
2️⃣ 收到模板文件后一键导入
3️⃣ 按说明输入内容，秒出结果

━━━━━━ 买家必读 ━━━━━━
⚠️ 本商品为虚拟商品，售出不退不换
📱 需要自行注册 Coze 账号（完全免费）
🔒 在你自己账号下运行，数据不上传第三方
💬 使用问题随时问我，看到必回

💡 下单后秒发货！如未及时回复请稍等，24h内必发。
"""
    return desc


def build_app_guide(info: dict) -> str:
    """生成闲鱼 APP 上架逐步骤操作指南"""
    return f"""
╔══════════════════════════════════════════════╗
║  闲鱼 APP 上架指南（约30秒完成）              ║
╠══════════════════════════════════════════════╣

📱 第1步：打开闲鱼APP → 底部中间 [+] 按钮
       → 「卖闲置」→「发布闲置」

📱 第2步：上传图片（5张，按顺序）
       图1-封面：Canva做，大字标题+价格
       图2-截图：Coze Bot对话界面
       图3-展示：核心功能list
       图4-教程：使用步骤123
       图5-对比：版本VS进阶版
       （图做好了放 exports/<产品名>/images/ 里）

📱 第3步：填写以下信息

       【标题】（复制下面这行）：
       {info['title']}

       【分类】：虚拟商品 → 其他虚拟商品

       【价格】：¥{info['price']}

       【运费】：无需物流（虚拟商品）

       【标签】（最多5个）：
       {'  '.join(['#' + t for t in info.get('tags', [])[:5]])}

📱 第4步：在「商品描述」里粘贴下面的内容
       （下面的内容已写入 package/description.txt，
        方便手机端复制，可以QQ/微信发给自己）

📱 第5步：设置自动回复：
       「你好！这个是Coze AI智能体模板，
       购买后发你导入文件，在你的Coze账号
       里用，永久有效～标准版¥{info['price']}，
       {info['premium_name']}¥{info['premium_price']}。拍下秒发！」

📱 第6步：点击右上角「发布」

╚══════════════════════════════════════════════╝
"""


def package_product(product_id: str) -> Optional[Path]:
    """为单个商品生成完整上架素材包"""
    products = load_products()
    product = next((p for p in products["products"] if p["id"] == product_id), None)
    if not product:
        print(f"产品不存在: {product_id}")
        print(f"可用ID: {', '.join(p['id'] for p in products['products'])}")
        return None

    info = extract_listing_info(product)
    pkg = PACKAGE_DIR / product_id
    pkg.mkdir(parents=True, exist_ok=True)

    # 1. listing.json — 结构化数据，程序可读
    listing = {
        "product_id": product_id,
        "name": product["name"],
        "packaged_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "title": info["title"],
        "price": info["price"],
        "premium_price": info["premium_price"],
        "premium_name": info["premium_name"],
        "category": "虚拟商品 > 其他虚拟商品",
        "shipping": "无需物流",
        "tags": info["tags"][:5],
        "auto_reply": f"你好！这个是Coze AI智能体模板，购买后发你导入文件，在你的Coze账号里用，永久有效～标准版¥{info['price']}，{info['premium_name']}¥{info['premium_price']}。拍下秒发！",
        "coze_bot_url": product.get("coze_bot_url", ""),
    }
    (pkg / "listing.json").write_text(
        json.dumps(listing, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 2. description.txt — 纯文本描述，方便手机复制
    (pkg / "description.txt").write_text(info["description"], encoding="utf-8")

    # 3. title.txt — 标题单独文件，方便复制
    (pkg / "title.txt").write_text(info["title"], encoding="utf-8")

    # 4. prompt.txt — Bot Prompt 备份
    prompt_path = HERE / product["prompt_file"]
    if prompt_path.exists():
        import shutil
        shutil.copy(prompt_path, pkg / "prompt.txt")

    # 5. copy.md — 完整文案
    copy_path = HERE / product["copy_file"]
    if copy_path.exists():
        import shutil
        shutil.copy(copy_path, pkg / "copy.md")

    # 6. APP上架指南.txt — 逐步骤指引
    guide = build_app_guide(info)
    (pkg / "APP上架指南.txt").write_text(guide, encoding="utf-8")

    # 7. 自动生成图片
    (pkg / "images").mkdir(exist_ok=True)
    try:
        from image_generator import generate_product_images
        generate_product_images(product_id)
    except ImportError:
        print("  [提示] Pillow 未安装，跳过自动生成图片 (pip install Pillow)")
    except Exception as e:
        print(f"  [图片] 自动生成失败: {e}")

    # 8. checklist
    checklist = f"""# {product['name']} · 上架检查清单

## 发布前
- [ ] Coze Bot 已创建并测试（3轮以上）
- [ ] Bot 已发布，有分享链接
- [ ] 5张主图已准备好（存于 images/ 目录）
- [ ] 标题、描述、价格、标签已确认

## 发布时
- [ ] 5张图按顺序上传
- [ ] 标题复制 title.txt 中的内容
- [ ] 分类选「虚拟商品 > 其他虚拟商品」
- [ ] 价格填 ¥{info['price']}（如需双版本在描述中说明）
- [ ] 运费选「无需物流」
- [ ] 描述复制 description.txt 中的内容
- [ ] 标签添加（最多5个）
- [ ] 自动回复已设置

## 发布后
- [ ] 搜索标题关键词确认能搜到
- [ ] 检查图片顺序和清晰度
- [ ] 发一条消息测试自动回复
- [ ] 运行: python manage.py xianyu mark {product_id} 已上架

---
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    (pkg / "checklist.md").write_text(checklist, encoding="utf-8")

    # 9. 生成手机一键复制页面
    try:
        from mobile_copy_page import generate_page
        generate_page(product_id)
    except Exception as e:
        print(f"  [手机页] 生成失败: {e}")

    print(f"\n{'=' * 55}")
    print(f"  素材包: {product['name']}")
    print(f"{'=' * 55}")
    print(f"  {pkg}/")
    print(f"    ├── index.html          (手机一键复制页面)")
    print(f"    ├── listing.json        (结构化发布参数)")
    print(f"    ├── title.txt           (标题 → 复制到闲鱼)")
    print(f"    ├── description.txt     (描述 → 复制到闲鱼)")
    print(f"    ├── prompt.txt          (Bot Prompt 备份)")
    print(f"    ├── copy.md             (完整文案)")
    print(f"    ├── APP上架指南.txt      (逐步骤操作指南)")
    print(f"    ├── checklist.md        (上架检查清单)")
    print(f"    └── images/             (5张主图)")
    print(f"         ├── 01_cover.png")
    print(f"         ├── 02_features.png")
    print(f"         ├── 03_steps.png")
    print(f"         ├── 04_compare.png")
    print(f"         └── 05_cta.png")
    print(f"\n  📱 用手机打开: exports/{product_id}/index.html")

    return pkg


def package_all():
    """批量打包所有待上架商品"""
    products = load_products()
    for p in products["products"]:
        package_product(p["id"])
        print()

    print(f"\n全部素材包已生成: {PACKAGE_DIR}/")
    print(f"找到对应产品目录，打开 APP上架指南.txt 开始上架")


def print_quickguide():
    """打印通用快速上架指南"""
    print("""
╔══════════════════════════════════════════╗
║  闲鱼上架 · 30秒快速操作卡               ║
╠══════════════════════════════════════════╣

1. 打开闲鱼APP → [+] → 卖闲置
2. 上传 5 张图
3. 粘贴标题（从 exports/<产品>/title.txt 复制）
4. 分类: 虚拟商品 > 其他虚拟商品
5. 价格: 填标准版价格
6. 运费: 无需物流
7. 粘贴描述（从 exports/<产品>/description.txt 复制）
8. 加标签: 点「添加标签」选 Coze智能体、AI工具等
9. 设置自动回复（复制 exports/<产品>/listing.json 里的 auto_reply）
10. 点击发布 ✓

💡 提示: 把 title.txt 和 description.txt 的内容
   通过QQ/微信"文件传输助手"发给自己，
   在手机上直接复制粘贴，最方便。

╚══════════════════════════════════════════╝
""")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n可用命令:")
        print("  package <id>    为指定产品生成上架素材包")
        print("  package-all     批量生成所有产品素材包")
        print("  quickguide      打印快速上架指南")
        return

    cmd = sys.argv[1]

    if cmd == "package":
        pid = sys.argv[2] if len(sys.argv) > 2 else None
        if pid:
            package_product(pid)
        else:
            print("用法: python xianyu_publisher.py package <product_id>")
            print("可用ID: " + ", ".join(p["id"] for p in load_products()["products"]))
    elif cmd == "package-all":
        package_all()
    elif cmd == "quickguide":
        print_quickguide()
    else:
        print(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()
