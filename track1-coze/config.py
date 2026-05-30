"""轨道1配置管理 — Coze + 闲鱼 商品上架自动化"""
import json
import os
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).parent
PRODUCTS_FILE = BASE_DIR / "products.json"

# Coze API 配置（通过环境变量注入，不硬编码密钥）
COZE_API_BASE = os.getenv("COZE_API_BASE", "https://api.coze.cn")
COZE_API_KEY = os.getenv("COZE_API_KEY", "")
COZE_WORKSPACE_ID = os.getenv("COZE_WORKSPACE_ID", "")

# DeepSeek API 配置（用于文案生成/优化）
DS_API_KEY = os.getenv("DS_API_KEY", "")
DS_API_BASE = os.getenv("DS_API_BASE", "https://api.deepseek.com")

# 文件路径
PROMPT_DIR = BASE_DIR / "Prompt源码"
COPY_DIR = BASE_DIR / "闲鱼文案"
STATUS_FILE = BASE_DIR / "status.json"


def load_products() -> dict:
    """加载商品配置"""
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_products(data: dict) -> None:
    """保存商品配置"""
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_status() -> dict:
    """加载上架状态"""
    if STATUS_FILE.exists():
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_status(status: dict) -> None:
    """保存上架状态"""
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)


def get_prompt(product_id: str) -> Optional[str]:
    """读取指定产品的 Prompt 源码"""
    products = load_products()
    for p in products["products"]:
        if p["id"] == product_id:
            prompt_path = BASE_DIR / p["prompt_file"]
            if prompt_path.exists():
                return prompt_path.read_text(encoding="utf-8")
    return None


def get_copy(product_id: str) -> Optional[str]:
    """读取指定产品的闲鱼文案"""
    products = load_products()
    for p in products["products"]:
        if p["id"] == product_id:
            copy_path = BASE_DIR / p["copy_file"]
            if copy_path.exists():
                return copy_path.read_text(encoding="utf-8")
    return None
