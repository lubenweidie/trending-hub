"""闲鱼文案生成器 — 基于 DeepSeek API 自动生成/优化商品文案"""
import json
import sys
from pathlib import Path
from typing import Optional
from openai import OpenAI

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from config import DS_API_KEY, DS_API_BASE, load_products, get_prompt, BASE_DIR

# DeepSeek API 兼容 OpenAI SDK
_client = None


def get_client() -> Optional[OpenAI]:
    if not DS_API_KEY:
        return None
    global _client
    if _client is None:
        _client = OpenAI(api_key=DS_API_KEY, base_url=DS_API_BASE)
    return _client


SYSTEM_PROMPT = """你是一位闲鱼电商文案专家，擅长写出高转化率的闲鱼商品文案。

闲鱼文案特点：
1. 标题要含搜索关键词，30字以内，抓眼球
2. 用emoji但不过度，每段1-2个
3. 突出"痛点→解决方案"逻辑
4. 价格对比让用户觉得"占便宜"
5. 结尾要有明确的行动号召

输出格式：标准Markdown，包含 #标题、价格表格、商品详情、标签建议。"""


def generate_copy(product_id: str, optimize: bool = False) -> str:
    """为指定产品生成闲鱼文案"""
    client = get_client()
    if not client:
        raise RuntimeError("请设置环境变量 DS_API_KEY")

    products = load_products()
    product = next((p for p in products["products"] if p["id"] == product_id), None)
    if not product:
        raise ValueError(f"产品 {product_id} 不存在")

    prompt_text = get_prompt(product_id) or ""
    existing_copy = ""
    copy_path = BASE_DIR / product["copy_file"]
    if optimize and copy_path.exists():
        existing_copy = copy_path.read_text(encoding="utf-8")

    user_prompt = f"""请为以下Coze AI智能体撰写闲鱼商品文案：

产品名称：{product['name']}
分类：{product['category']}
目标用户：{', '.join(product['target_users'])}
价格：标准版 ¥{product['pricing']['standard']}，{product['pricing']['premium_name']} ¥{product['pricing']['premium']}
智能体Prompt：
---
{prompt_text}
---
"""

    if optimize and existing_copy:
        user_prompt += f"""
请基于以下现有文案进行优化（改进标题SEO、丰富卖点、增加转化率）：

现有文案：
---
{existing_copy}
---
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=3000,
    )

    content = response.choices[0].message.content
    return content


def generate_all(optimize: bool = False) -> dict:
    """为所有产品生成文案"""
    products = load_products()
    results = {}
    for p in products["products"]:
        try:
            copy = generate_copy(p["id"], optimize=optimize)
            copy_path = BASE_DIR / p["copy_file"]
            copy_path.write_text(copy, encoding="utf-8")
            results[p["id"]] = {"status": "ok", "file": str(copy_path)}
            print(f"[OK] {p['name']} → {copy_path}")
        except Exception as e:
            results[p["id"]] = {"status": "failed", "error": str(e)}
            print(f"[FAIL] {p['name']}: {e}")
    return results


def preview_copy(product_id: str) -> str:
    """预览产品文案"""
    products = load_products()
    product = next((p for p in products["products"] if p["id"] == product_id), None)
    if not product:
        raise ValueError(f"产品 {product_id} 不存在")

    copy_path = BASE_DIR / product["copy_file"]
    if copy_path.exists():
        return copy_path.read_text(encoding="utf-8")
    return f"文案文件不存在: {copy_path}"


def main():
    if not DS_API_KEY:
        print("请设置环境变量 DS_API_KEY")
        print("获取方式: https://platform.deepseek.com/api_keys")
        sys.exit(1)

    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "generate":
        pid = sys.argv[2] if len(sys.argv) > 2 else None
        if pid:
            copy = generate_copy(pid)
            print(copy)
            # 询问是否保存
            save = input("\n保存到文件？[y/N] ").strip().lower()
            if save == "y":
                products = load_products()
                product = next((p for p in products["products"] if p["id"] == pid), None)
                if product:
                    copy_path = BASE_DIR / product["copy_file"]
                    copy_path.write_text(copy, encoding="utf-8")
                    print(f"已保存: {copy_path}")
        else:
            print("用法: python generate_copy.py generate <product_id>")

    elif cmd == "optimize":
        pid = sys.argv[2] if len(sys.argv) > 2 else None
        if pid:
            copy = generate_copy(pid, optimize=True)
            print(copy)
        else:
            print("用法: python generate_copy.py optimize <product_id>")

    elif cmd == "generate-all":
        generate_all()

    elif cmd == "optimize-all":
        generate_all(optimize=True)

    elif cmd == "preview":
        pid = sys.argv[2] if len(sys.argv) > 2 else None
        if pid:
            print(preview_copy(pid))
        else:
            for p in load_products()["products"]:
                print(f"\n{'='*60}")
                print(f"  {p['name']} ({p['id']})")
                print(f"{'='*60}")
                print(preview_copy(p["id"])[:500])
                print("...")

    else:
        print("命令: generate <id> | optimize <id> | generate-all | optimize-all | preview [id]")


if __name__ == "__main__":
    main()
