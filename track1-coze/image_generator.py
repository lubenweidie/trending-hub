"""商品主图自动生成器 — Pillow 渲染

为每个产品生成 5 张标准化闲鱼商品图：
  图1: 封面 (大标题+价格+卖点)
  图2: 功能列表 (核心能力展示)
  图3: 使用步骤 (1-2-3操作图解)
  图4: 版本对比 (标准版 vs 进阶版)
  图5: 行动号召 (下单引导)

使用: python image_generator.py generate <product_id>
      python image_generator.py generate-all
"""
import json
import sys
import math
from pathlib import Path
from datetime import datetime
from typing import Optional

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("请安装 Pillow: pip install Pillow")
    sys.exit(1)

HERE = Path(__file__).parent
SIZE = 800  # 1:1 正方形


def load_products():
    with open(HERE / "products.json", "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# 字体与颜色
# ============================================================

def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """获取字体，优先系统字体，fallback 到 PIL 默认"""
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",       # 微软雅黑
        "C:/Windows/Fonts/msyhbd.ttc",     # 微软雅黑粗体
        "C:/Windows/Fonts/simhei.ttf",     # 黑体
        "C:/Windows/Fonts/simsun.ttc",     # 宋体
    ]
    for path in candidates:
        if bold and "msyhbd" not in path.lower() and "bold" not in path.lower():
            continue
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


FONT_TITLE = lambda s: get_font(s, bold=True)
FONT_BODY = lambda s: get_font(s)
FONT_SMALL = lambda s: get_font(s)


# 配色方案
COLORS = {
    "bg": (18, 22, 33),         # 深色背景
    "card": (30, 35, 48),       # 卡片
    "primary": (59, 130, 246),  # 蓝色
    "accent": (245, 158, 11),   # 橙色
    "green": (34, 197, 94),     # 绿色
    "white": (255, 255, 255),
    "gray": (148, 163, 184),
    "red": (239, 68, 68),
    "border": (51, 65, 85),
}


def draw_rounded_rect(draw, xy, radius, fill):
    """画圆角矩形"""
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


def draw_centered_text(draw, text, y, font, fill=COLORS["white"], max_width=700):
    """居中文字"""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (SIZE - tw) // 2
    draw.text((x, y), text, font=font, fill=fill)
    return y + (bbox[3] - bbox[0])


def draw_wrapped_text(draw, text, y, font, fill=COLORS["gray"],
                      max_width=680, line_spacing=8):
    """自动换行文字，返回结束 y 坐标"""
    words = text
    # 中文字符按字数换行
    lines = []
    current = ""
    for ch in text:
        current += ch
        bbox = draw.textbbox((0, 0), current, font=font)
        if bbox[2] - bbox[0] > max_width:
            lines.append(current[:-1])
            current = ch
    if current:
        lines.append(current)

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (SIZE - tw) // 2
        draw.text((x, y), line, font=font, fill=fill)
        y += (bbox[3] - bbox[0]) + line_spacing
    return y


# ============================================================
# 各图模板
# ============================================================

def generate_cover(product: dict, save_path: Path):
    """图1: 封面 — 大标题 + 价格 + 核心卖点"""
    img = Image.new("RGB", (SIZE, SIZE), COLORS["bg"])
    draw = ImageDraw.Draw(img)

    name = product["name"]
    price = product["pricing"]["standard"]
    targets = product["target_users"][:2]

    # 顶部标签
    draw_rounded_rect(draw, (40, 40, 200, 80), 20, fill=COLORS["primary"])
    tag_text = product.get("category", "AI工具")
    bbox = draw.textbbox((0, 0), tag_text, font=FONT_BODY(28))
    tx = 120 - (bbox[2] - bbox[0]) // 2
    draw.text((tx, 52), tag_text, font=FONT_BODY(28), fill=COLORS["white"])

    # 主标题
    y = 160
    for line in [f"AI{name}", "Coze 智能体"]:
        bbox = draw.textbbox((0, 0), line, font=FONT_TITLE(64))
        x = (SIZE - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), line, font=FONT_TITLE(64), fill=COLORS["white"])
        y += 80

    # 分割线
    draw.line([(120, y+20), (680, y+20)], fill=COLORS["primary"], width=3)
    y += 50

    # 卖点
    selling_points = [
        f"一键导入即用 | 适合{targets[0]}、{targets[1]}",
        "AI 智能驱动 | 秒出专业结果",
        "Coze 官方平台 | 永久使用",
    ]
    for pt in selling_points:
        draw_centered_text(draw, pt, y, FONT_BODY(26), COLORS["gray"])
        y += 40

    # 价格区域
    y = 580
    draw_rounded_rect(draw, (150, y, 650, y+120), 24, fill=COLORS["card"])
    price_text = f"仅售 ¥{price}"
    bbox = draw.textbbox((0, 0), price_text, font=FONT_TITLE(48))
    px = (SIZE - (bbox[2] - bbox[0])) // 2
    draw.text((px, y+15), price_text, font=FONT_TITLE(48), fill=COLORS["accent"])

    prem_name = product["pricing"]["premium_name"]
    prem_price = product["pricing"]["premium"]
    sub_text = f"{prem_name} ¥{prem_price}（含深度定制）"
    bbox = draw.textbbox((0, 0), sub_text, font=FONT_SMALL(22))
    sx = (SIZE - (bbox[2] - bbox[0])) // 2
    draw.text((sx, y+75), sub_text, font=FONT_SMALL(22), fill=COLORS["gray"])

    # 底部水印
    draw_centered_text(draw, "拍下秒发 · 永久使用", SIZE-60, FONT_SMALL(20), COLORS["gray"])

    img.save(save_path, quality=95)


def generate_features(product: dict, save_path: Path, prompt_text: str = ""):
    """图2: 功能列表 — 核心能力展示"""
    img = Image.new("RGB", (SIZE, SIZE), COLORS["bg"])
    draw = ImageDraw.Draw(img)

    # 标题
    draw_centered_text(draw, "核心功能", 40, FONT_TITLE(44), COLORS["white"])

    # 从 prompt 提取功能点
    features = []
    if prompt_text:
        for line in prompt_text.split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or any(kw in line for kw in
                          ["分析", "识别", "生成", "输出", "格式", "评分", "建议"])):
                features.append(line.lstrip("123456789. ")[:40])

    if not features:
        features = [
            "AI 智能分析，秒出专业结果",
            "结构化输出，格式清晰易读",
            "一键导入 Coze，永久免费使用",
            "数据不上传第三方，隐私安全",
        ]

    y = 120
    for i, feat in enumerate(features[:6]):
        # 卡片
        card_y = y
        draw_rounded_rect(draw, (60, card_y, 740, card_y+75), 16, fill=COLORS["card"])

        # 序号
        num_text = f"{i+1:02d}"
        draw_rounded_rect(draw, (80, card_y+12, 130, card_y+63), 12, fill=COLORS["primary"])
        bbox = draw.textbbox((0, 0), num_text, font=FONT_TITLE(28))
        nx = 105 - (bbox[2] - bbox[0]) // 2
        draw.text((nx, card_y+18), num_text, font=FONT_TITLE(28), fill=COLORS["white"])

        # 功能文字
        draw.text((155, card_y+22), feat, font=FONT_BODY(26), fill=COLORS["white"])
        y += 100

    img.save(save_path, quality=95)


def generate_steps(product: dict, save_path: Path):
    """图3: 使用步骤 — 1-2-3 操作"""
    img = Image.new("RGB", (SIZE, SIZE), COLORS["bg"])
    draw = ImageDraw.Draw(img)

    draw_centered_text(draw, "三步开始使用", 40, FONT_TITLE(44), COLORS["white"])

    steps = [
        ("1", "注册 Coze", "coze.cn 免费注册账号\n手机号/微信一键登录"),
        ("2", "导入模板", "接收模板文件\n一键导入你的 Coze 空间"),
        ("3", "开始使用", "上传/输入你的内容\nAI 秒出专业结果"),
    ]

    y = 130
    for num, title, desc in steps:
        # 左侧大数字
        bbox = draw.textbbox((0, 0), num, font=FONT_TITLE(72))
        draw.text((80, y+10), num, font=FONT_TITLE(72), fill=COLORS["primary"])

        # 标题
        draw.text((220, y+10), title, font=FONT_TITLE(32), fill=COLORS["white"])

        # 描述
        for j, dline in enumerate(desc.split("\n")):
            draw.text((220, y+55 + j*32), dline, font=FONT_SMALL(22), fill=COLORS["gray"])

        # 连接线 (除最后一项)
        if num != "3":
            draw.line([(116, y+120), (116, y+170)], fill=COLORS["border"], width=2)

        y += 170

    draw_centered_text(draw, "从导入到使用，不到 1 分钟", SIZE-80, FONT_SMALL(22), COLORS["gray"])
    img.save(save_path, quality=95)


def generate_compare(product: dict, save_path: Path):
    """图4: 版本对比 — 标准版 vs 进阶版"""
    img = Image.new("RGB", (SIZE, SIZE), COLORS["bg"])
    draw = ImageDraw.Draw(img)

    draw_centered_text(draw, "版本对比", 40, FONT_TITLE(44), COLORS["white"])

    std_name = "标准版"
    std_price = product["pricing"]["standard"]
    prem_name = product["pricing"]["premium_name"]
    prem_price = product["pricing"]["premium"]

    # 标准版卡片
    card_y = 120
    draw_rounded_rect(draw, (40, card_y, 380, card_y+400), 20, fill=COLORS["card"])
    draw_rounded_rect(draw, (40, card_y, 380, card_y+80), 20, fill=COLORS["primary"])

    std_label = f"{std_name}"
    draw_centered_text(draw, std_label, card_y+15, FONT_TITLE(32), COLORS["white"])
    draw_centered_text(draw, f"¥{std_price}", card_y+50, FONT_SMALL(22), COLORS["white"])

    std_items = [
        ("smart", "智能体模板文件"),
        ("smart", "一键导入 Coze"),
        ("smart", "永久使用"),
        ("smart", "使用指导"),
        ("close", "深度定制优化"),
        ("close", "行业专属 Prompt"),
        ("close", "1v1 咨询"),
    ]
    item_y = card_y + 110
    for icon, text in std_items:
        symbol = "[✓]" if icon == "smart" else "[×]"
        color = COLORS["green"] if icon == "smart" else COLORS["gray"]
        draw.text((60, item_y), symbol, font=FONT_SMALL(22), fill=color)
        draw.text((110, item_y), text, font=FONT_SMALL(22), fill=COLORS["gray"])
        item_y += 36

    # 进阶版卡片
    draw_rounded_rect(draw, (420, card_y, 760, card_y+400), 20, fill=COLORS["card"])
    draw_rounded_rect(draw, (420, card_y, 760, card_y+80), 20, fill=COLORS["accent"])
    draw_centered_text(draw, f"{prem_name}", card_y+15, FONT_TITLE(28), COLORS["white"])
    draw_centered_text(draw, f"¥{prem_price}", card_y+50, FONT_SMALL(22), COLORS["white"])

    prem_items = [
        ("smart", "标准版全部内容"),
        ("smart", "行业深度定制"),
        ("smart", "专属 Prompt 优化"),
        ("smart", "多次免费修改"),
        ("smart", "1v1 使用指导"),
        ("smart", "优先技术支持"),
        ("smart", "后续更新免费"),
    ]
    item_y = card_y + 110
    for icon, text in prem_items:
        draw.text((440, item_y), "[✓]", font=FONT_SMALL(22), fill=COLORS["green"])
        draw.text((490, item_y), text, font=FONT_SMALL(22), fill=COLORS["white"])
        item_y += 36

    # 推荐标签
    draw_rounded_rect(draw, (280, 560, 520, 610), 16, fill=COLORS["accent"])
    draw_centered_text(draw, "推荐选择进阶版", 568, FONT_BODY(26), COLORS["white"])

    img.save(save_path, quality=95)


def generate_cta(product: dict, save_path: Path):
    """图5: 行动号召 — 下单引导 + 售后保障"""
    img = Image.new("RGB", (SIZE, SIZE), COLORS["bg"])
    draw = ImageDraw.Draw(img)

    name = product["name"]
    price = product["pricing"]["standard"]

    draw_centered_text(draw, "为什么选择我们？", 40, FONT_TITLE(44), COLORS["white"])

    guarantees = [
        ("logo-coze", "Coze 官方平台", "字节跳动旗下，稳定可靠"),
        ("shield", "隐私安全", "在你自己的空间运行\n数据不上传第三方"),
        ("flash", "秒级交付", "拍下立即发货\n24h 内必响应"),
        ("refresh", "永久使用", "一次购买终身使用\n不限次数"),
    ]

    y = 130
    for icon, title, desc in guarantees:
        draw_rounded_rect(draw, (60, y, 370, y+130), 16, fill=COLORS["card"])
        draw.text((80, y+15), title, font=FONT_TITLE(28), fill=COLORS["white"])
        for j, dline in enumerate(desc.split("\n")):
            draw.text((80, y+55 + j*28), dline, font=FONT_SMALL(20), fill=COLORS["gray"])

        if icon == "logo-coze":
            draw_rounded_rect(draw, (400, y, 740, y+130), 16, fill=COLORS["card"])
            draw_rounded_rect(draw, (435, y+15, 475, y+55), 12, fill=COLORS["primary"])
            draw_rounded_rect(draw, (480, y+15, 520, y+55), 12, fill=COLORS["accent"])
            draw_rounded_rect(draw, (525, y+15, 565, y+55), 12, fill=COLORS["green"])
            draw.text((420, y+65), "Coze 官方认证 · 稳定运行", font=FONT_SMALL(22), fill=COLORS["gray"])
            y += 160
        else:
            y += 160

    # 底部 CTA
    y = 610
    draw_rounded_rect(draw, (120, y, 680, y+100), 24, fill=COLORS["primary"])
    cta_text = f"下单即发 · ¥{price} 起"
    bbox = draw.textbbox((0, 0), cta_text, font=FONT_TITLE(40))
    cx = (SIZE - (bbox[2] - bbox[0])) // 2
    draw.text((cx, y+25), cta_text, font=FONT_TITLE(40), fill=COLORS["white"])

    img.save(save_path, quality=95)


# ============================================================
# 主入口
# ============================================================

def generate_product_images(product_id: str) -> Optional[Path]:
    """为单个产品生成全部 5 张图"""
    products = load_products()
    product = next((p for p in products["products"] if p["id"] == product_id), None)
    if not product:
        print(f"产品不存在: {product_id}")
        return None

    out_dir = HERE / "exports" / product_id / "images"
    out_dir.mkdir(parents=True, exist_ok=True)

    prompt_path = HERE / product["prompt_file"]
    prompt_text = ""
    if prompt_path.exists():
        prompt_text = prompt_path.read_text(encoding="utf-8")

    print(f"\n生成图片: {product['name']}")

    generators = [
        (generate_cover, "01_cover.png"),
        (generate_features, "02_features.png"),
        (generate_steps, "03_steps.png"),
        (generate_compare, "04_compare.png"),
        (generate_cta, "05_cta.png"),
    ]

    for gen_func, fname in generators:
        path = out_dir / fname
        try:
            if gen_func == generate_features:
                gen_func(product, path, prompt_text)
            else:
                gen_func(product, path)
            print(f"  ✓ {fname}")
        except Exception as e:
            print(f"  ✗ {fname}: {e}")

    print(f"图片目录: {out_dir}")
    return out_dir


def generate_all():
    """批量生成所有产品图片"""
    products = load_products()
    for p in products["products"]:
        generate_product_images(p["id"])


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "generate":
        pid = sys.argv[2] if len(sys.argv) > 2 else None
        if pid:
            generate_product_images(pid)
        else:
            print("用法: python image_generator.py generate <product_id>")
    elif cmd == "generate-all":
        generate_all()
    else:
        print(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()
