"""多源图片搜索与下载 —— 为文章提供配图和封面

支持源（按优先级自动降级，国内均可用）：
  1. Bing Image     — 搜索引擎，免费 1000次/月（需 Azure Key）
  2. 百度图片       — 国内免费，无需 Key，中文搜图最精准
  3. Pexels         — 高质量图库，免费 200次/小时
  4. Pixabay        — 免费 5000次/月
  5. Unsplash       — 免费 50次/小时

配置：在 ../apikeys.conf 中设置对应 API Key
"""
import config_loader  # noqa
import os
import requests
from pathlib import Path
from typing import Optional

# ============================================================
# Provider 注册表（按优先级排序）
# ============================================================

PROVIDERS = []


def register_provider(name, key_env, search_fn):
    """注册一个图片搜索源"""
    PROVIDERS.append({
        "name": name,
        "key_env": key_env,
        "search": search_fn,
    })


# ============================================================
# 1. Bing Image Search — 国内可用，时事新闻配图最佳
# ============================================================

def _search_bing(query: str, per_page: int) -> list[dict]:
    key = os.environ.get("BING_API_KEY", "")
    if not key:
        return []
    try:
        resp = requests.get(
            "https://api.bing.microsoft.com/v7.0/images/search",
            headers={"Ocp-Apim-Subscription-Key": key},
            params={"q": query, "count": per_page, "mkt": "zh-CN",
                    "size": "Large", "imageType": "Photo"},
            timeout=15
        )
        if resp.status_code != 200:
            return []
        results = []
        for img in resp.json().get("value", []):
            results.append({
                "url": img.get("contentUrl"),
                "photographer": img.get("hostPageDisplayUrl", ""),
                "alt": img.get("name", query),
                "width": img.get("width", 0),
                "height": img.get("height", 0),
            })
        return results
    except Exception:
        return []


# ============================================================
# 2. 百度图片 — 国内免费，无需 Key，中文搜图最精准
# ============================================================

def _search_baidu(query: str, per_page: int) -> list[dict]:
    try:
        # 国内访问百度需要先拿 cookie，否则反爬拦截
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })
        session.get("https://image.baidu.com/", timeout=10)

        resp = session.get(
            "https://image.baidu.com/search/acjson",
            params={
                "word": query, "pn": 0, "rn": min(per_page * 3, 30),
                "tn": "resultjson_com", "ipn": "rj",
            },
            headers={"Referer": "https://image.baidu.com/"},
            timeout=15
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        results = []
        for item in data.get("data", []):
            url = item.get("thumbURL") or item.get("middleURL") or item.get("objURL") or ""
            if not url:
                continue
            w = int(item.get("width", 0))
            h = int(item.get("height", 0))
            if w < 100 or h < 100:
                continue
            results.append({
                "url": url,
                "photographer": item.get("fromPageTitleEnc", ""),
                "alt": item.get("fromPageTitleEnc", query),
                "width": w,
                "height": h,
            })
        return results
    except Exception:
        return []


# ============================================================
# 3. Pexels
# ============================================================

def _search_pexels(query: str, per_page: int) -> list[dict]:
    key = os.environ.get("PEXELS_API_KEY", "")
    if not key:
        return []
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": key},
            params={"query": query, "per_page": per_page,
                    "size": "medium", "orientation": "landscape"},
            timeout=15
        )
        if resp.status_code != 200:
            return []
        results = []
        for photo in resp.json().get("photos", []):
            results.append({
                "url": photo["src"].get("large") or photo["src"].get("original"),
                "photographer": photo.get("photographer", ""),
                "alt": photo.get("alt", query),
                "width": photo.get("width", 0),
                "height": photo.get("height", 0),
            })
        return results
    except Exception:
        return []


# ============================================================
# 4. Pixabay
# ============================================================

def _search_pixabay(query: str, per_page: int) -> list[dict]:
    key = os.environ.get("PIXABAY_API_KEY", "")
    if not key:
        return []
    try:
        resp = requests.get(
            "https://pixabay.com/api/",
            params={"key": key, "q": query, "per_page": per_page,
                    "image_type": "photo", "orientation": "horizontal",
                    "min_width": 400, "lang": "zh"},
            timeout=15
        )
        if resp.status_code != 200:
            return []
        results = []
        for hit in resp.json().get("hits", []):
            results.append({
                "url": hit.get("largeImageURL") or hit.get("webformatURL"),
                "photographer": hit.get("user", ""),
                "alt": hit.get("tags", query),
                "width": hit.get("imageWidth", 0),
                "height": hit.get("imageHeight", 0),
            })
        return results
    except Exception:
        return []


# ============================================================
# 5. Unsplash
# ============================================================

def _search_unsplash(query: str, per_page: int) -> list[dict]:
    key = os.environ.get("UNSPLASH_ACCESS_KEY", "")
    if not key:
        return []
    try:
        resp = requests.get(
            "https://api.unsplash.com/search/photos",
            headers={"Authorization": f"Client-ID {key}"},
            params={"query": query, "per_page": per_page, "orientation": "landscape"},
            timeout=15
        )
        if resp.status_code != 200:
            return []
        results = []
        for photo in resp.json().get("results", []):
            results.append({
                "url": photo["urls"].get("regular") or photo["urls"].get("raw"),
                "photographer": photo["user"].get("name", ""),
                "alt": photo.get("alt_description") or photo.get("description") or query,
                "width": photo.get("width", 0),
                "height": photo.get("height", 0),
            })
        return results
    except Exception:
        return []


# ============================================================
# 注册 Provider（按优先级）
# ============================================================

register_provider("Bing", "BING_API_KEY", _search_bing)
register_provider("Baidu", None, _search_baidu)
register_provider("Pexels", "PEXELS_API_KEY", _search_pexels)
register_provider("Pixabay", "PIXABAY_API_KEY", _search_pixabay)
register_provider("Unsplash", "UNSPLASH_ACCESS_KEY", _search_unsplash)


# ============================================================
# 公共接口
# ============================================================

def search_images(query: str, per_page: int = 3) -> list[dict]:
    """多源降级搜索：按优先级依次尝试，首个返回结果即停止"""
    for p in PROVIDERS:
        key_env = p["key_env"]
        if key_env is not None:
            key = os.environ.get(key_env, "")
            if not key:
                continue
        print(f"  [{p['name']}] 搜索: {query[:40]}...")
        results = p["search"](query, per_page)
        if results:
            print(f"  [{p['name']}] [OK] 找到 {len(results)} 张")
            return results
        print(f"  [{p['name']}] 无结果，尝试下一源...")
    return []


def download_image(url: str, save_path: Path) -> Optional[Path]:
    """下载单张图片，返回保存路径"""
    try:
        resp = requests.get(url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        if resp.status_code == 200 and len(resp.content) > 1024:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_bytes(resp.content)
            print(f"  已下载: {save_path.name} ({len(resp.content)} bytes)")
            return save_path
        else:
            print(f"  下载失败 {url[:80]}: HTTP {resp.status_code}")
            return None
    except Exception as e:
        print(f"  下载异常 {url[:80]}: {e}")
        return None


def get_images_for_article(title: str, slug: str, output_dir: Path, count: int = 3, fallback_query: str = "") -> dict:
    """为文章搜索并下载图片，返回 {cover: Path|None, inline: [Path, ...]}

    title: 主搜索词（中文标题，优先用百度搜）
    fallback_query: 英文兜底搜索词（给 Pexels/Pixabay 等英文图库用）
    """
    has_any_key = any(
        p["key_env"] is None or os.environ.get(p["key_env"], "")
        for p in PROVIDERS
    )
    if not has_any_key:
        print("[ImageSearch] 未配置任何图片搜索 API Key，跳过配图")
        return {"cover": None, "inline": []}

    images = []

    # 策略：优先用中文标题搜百度（国内新闻配图最精准），
    #       百度无结果再用英文关键词搜英文图库
    cn_query = title[:50].strip() if title else ""
    if cn_query:
        print(f"  先搜百度(中文标题): {cn_query}")
        baidu_prov = [p for p in PROVIDERS if p["name"] == "Baidu"]
        for p in baidu_prov:
            if p["key_env"] is not None:
                continue
            results = p["search"](cn_query, per_page=max(count, 5))
            if results:
                print(f"  [Baidu] [OK] 找到 {len(results)} 张")
                images = results
                break
        if not images:
            # 中文标题太长可能搜不到，缩短再试
            short_cn = " ".join(cn_query.split()[:4]) if cn_query else ""
            if short_cn and short_cn != cn_query:
                print(f"  百度精简重试: {short_cn}")
                for p in baidu_prov:
                    if p["key_env"] is not None:
                        continue
                    results = p["search"](short_cn, per_page=max(count, 5))
                    if results:
                        print(f"  [Baidu] [OK] 找到 {len(results)} 张")
                        images = results
                        break

    # 百度无结果 → 英文图库兜底
    if not images and fallback_query:
        fb = fallback_query[:50]
        print(f"  英文图库兜底: {fb}")
        images = search_images(fb, per_page=max(count, 5))

    # 最终兜底
    if not images and cn_query:
        images = search_images(cn_query, per_page=max(count, 5))

    if not images:
        return {"cover": None, "inline": []}

    img_dir = output_dir
    # 清理旧图片，避免残留（仅删除图片文件，不碰 .md / .txt）
    if img_dir.exists():
        for old_file in img_dir.iterdir():
            if old_file.is_file() and old_file.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                old_file.unlink()
    img_dir.mkdir(parents=True, exist_ok=True)

    cover_path = None
    inline_paths = []
    seen_urls = set()
    needed_inline = count - 1  # count 包含封面，减1是配图数量

    for img in images[:count * 3]:  # 多取一些，留出去重余量
        url = img["url"]
        if not url:
            continue
        # 去重：同一URL（忽略query参数）不重复下载
        normalized = url.lower().split("?")[0]
        if normalized in seen_urls:
            continue
        seen_urls.add(normalized)

        ext = ".jpg"
        if ".png" in normalized:
            ext = ".png"
        elif ".webp" in normalized:
            ext = ".webp"

        if cover_path is None:
            fname = f"cover{ext}"
        else:
            fname = f"img_{len(inline_paths):02d}{ext}"

        save_path = download_image(url, img_dir / fname)
        if save_path:
            if cover_path is None:
                cover_path = save_path
            else:
                inline_paths.append(save_path)
                if len(inline_paths) >= needed_inline:
                    break

    return {"cover": cover_path, "inline": inline_paths}
