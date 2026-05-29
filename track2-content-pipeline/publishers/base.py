"""发布器基类 — 定义发布流程骨架 + 公共工具"""
import config_loader  # noqa
import json
import os
import re
import sys
import time
import glob
import requests
import subprocess
from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod
from urllib.parse import quote

from .prompts import ENRICH_PROMPT
from .browser_utils import IMG_EXTRACT_JS, FIND_EL_JS
from .image_server import start_image_server

HERE = Path(__file__).parent.parent
OUTPUT_DIR = HERE / "output" / "articles"

MIN_SOURCE_CONTENT = 50
MIN_ARTICLE_CONTENT = 200
MIN_IMAGE_BYTES = 1024


class BasePublisher(ABC):
    """发布器基类 — 子类实现各平台特定操作"""

    platform_name: str = ""
    edit_url: str = ""

    def __init__(self, account_suffix: str = ""):
        import os as _os
        from datetime import datetime as _dt
        import threading as _th
        tag = account_suffix or _th.get_ident()
        self._session = f"{self.platform_name}-{tag}-{_os.getpid()}-{_dt.now().strftime('%H%M%S')}"
        self._account_name = ""
        self._editor_opened = False

    # ============================================================
    # 抽象方法 — 子类必须实现
    # ============================================================

    @abstractmethod
    def open_editor(self) -> bool:
        """打开并初始化编辑器，返回 True 表示就绪"""
        ...

    @abstractmethod
    def fill_title(self, title: str):
        """填写标题"""
        ...

    @abstractmethod
    def fill_content(self, content: str, clear_first: bool = True):
        """填写正文，clear_first=False 时追加而不清空"""
        ...

    @abstractmethod
    def insert_images_to_editor(self, image_paths: list):
        """在编辑器中插入图片"""
        ...

    @abstractmethod
    def set_cover_image(self, cover_path) -> bool:
        """设置封面图，返回 True 表示成功"""
        ...

    @abstractmethod
    def click_publish(self, mode: str = "draft") -> bool:
        """点击发布/存草稿按钮，返回 True 表示操作成功"""
        ...

    # ============================================================
    # opencli 命令封装
    # ============================================================

    def get_publish_mode(self) -> str:
        mode_num = int(os.environ.get("PUBLISH_MODE", "1"))
        return "publish" if mode_num == 2 else "draft"

    def sh_run(self, cmd: str, timeout: int = 180) -> subprocess.CompletedProcess:
        return subprocess.run(
            cmd, shell=True, capture_output=True,
            encoding="utf-8", errors="replace", timeout=timeout
        )

    def _shell_quote_win(self, s: str) -> str:
        return f'"{s.replace(chr(34), chr(92)+chr(34))}"'

    def opencli(self, cmd: str, check: bool = True, cmd_extra: str = "",
                noisy: bool = True, timeout: int = 180) -> subprocess.CompletedProcess:
        if noisy:
            print(f"  $ {cmd}")
        if cmd_extra:
            full_cmd = f"opencli browser {self._session} {cmd} {self._shell_quote_win(cmd_extra)}"
        else:
            full_cmd = f"opencli browser {self._session} {cmd}"
        r = self.sh_run(full_cmd, timeout=timeout)
        if check and r.returncode != 0:
            err = (r.stderr or "").strip()[:300]
            if err:
                print(f"  [stderr] {err}")
        out = (r.stdout or "").strip()
        if out and noisy:
            try:
                print(f"  [out] {out[:300]}")
            except UnicodeEncodeError:
                print(f"  [out] {out[:300].encode('ascii', errors='replace').decode('ascii')}")
        return r

    def ensure_daemon(self):
        r = self.sh_run("opencli daemon status")
        if "running" not in (r.stdout or ""):
            print("[Setup] 启动 opencli daemon...")
            self.sh_run("opencli daemon restart")
            time.sleep(2)

    @staticmethod
    def stop_daemon():
        """关闭 opencli daemon，释放 Chrome 浏览器"""
        r = subprocess.run("opencli daemon status", shell=True, capture_output=True, encoding="utf-8", errors="replace")
        if "running" in (r.stdout or ""):
            print("[Cleanup] 关闭 opencli daemon...")
            subprocess.run("opencli daemon stop", shell=True, capture_output=True, timeout=10)

    def check_extension(self) -> bool:
        r = self.sh_run("opencli doctor")
        if "Extension: connected" in (r.stdout or ""):
            return True
        print("[Setup] Browser Bridge 扩展未连接，请在 Chrome 中加载扩展")
        return False

    # ============================================================
    # 图片服务（封装浏览器工具模块）
    # ============================================================

    def _start_image_server(self, root_dir: Path) -> int:
        return start_image_server(root_dir)

    # ============================================================
    # 文章解析（静态方法，不依赖实例状态）
    # ============================================================

    @staticmethod
    def find_latest_article(source_dir: str = "") -> Path | None:
        d = source_dir or str(OUTPUT_DIR)
        pattern = os.path.join(d, "*", "*.md")
        files = glob.glob(pattern)
        return Path(max(files, key=os.path.getmtime)) if files else None

    @staticmethod
    def find_recent_articles(source_dir: str = "", count: int = 2) -> list:
        d = source_dir or str(OUTPUT_DIR)
        pattern = os.path.join(d, "*", "*.md")
        files = glob.glob(pattern)
        files.sort(key=os.path.getmtime, reverse=True)
        return [Path(f) for f in files[:count]]

    @staticmethod
    def parse_article(filepath: Path) -> dict:
        from article_utils import parse_article
        return parse_article(filepath)

    @staticmethod
    def parse_source_url(article_path: Path) -> str:
        if not article_path.exists():
            return ""
        text = article_path.read_text(encoding="utf-8")
        m = re.search(r'原文：\[.*?\]\((https?://[^)]+)\)', text)
        return m.group(1) if m else ""

    @staticmethod
    def parse_source_platform(article_path: Path) -> str:
        if not article_path.exists():
            return ""
        text = article_path.read_text(encoding="utf-8")
        m = re.search(r'来源：(\S+)', text)
        return m.group(1) if m else ""

    @staticmethod
    def parse_summary(article_path: Path) -> str:
        if not article_path.exists():
            return ""
        text = article_path.read_text(encoding="utf-8")
        m = re.search(r'> 摘要：(.+)', text)
        return m.group(1).strip() if m else ""

    @staticmethod
    def _save_enriched_article(article_path: Path, article: dict):
        if not article_path.exists():
            return
        old = article_path.read_text(encoding="utf-8")
        new_content = article.get("content", "")
        if "（发布时基于源内容 AI 扩写）" in old:
            old = old.replace("（发布时基于源内容 AI 扩写）", new_content)
        elif new_content not in old:
            old += f"\n\n{new_content}"
        old_title_m = re.search(r'^# (.+)$', old, re.MULTILINE)
        if old_title_m and old_title_m.group(1) != article.get("title", ""):
            old = old.replace(old_title_m.group(1), article.get("title", ""), 1)
        article_path.write_text(old, encoding="utf-8")
        print(f"  [保存] 文章已回写: {article_path.name}")

    @staticmethod
    def find_article_images(article_path: Path) -> dict:
        slug = article_path.stem
        img_dir = article_path.parent
        if not img_dir.exists():
            return {"cover": None, "inline": []}

        cover = None
        inline = []
        for f in sorted(img_dir.iterdir()):
            if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                if f.stem == "cover":
                    cover = f
                else:
                    inline.append(f)
        return {"cover": cover, "inline": inline}

    # ============================================================
    # 源页面内容提取 + 图片采集
    # ============================================================

    def _try_click_first_result(self):
        js = (
            "(function(){"
            "var all=document.querySelectorAll('a[href]');"
            "var candidates=[];"
            "for(var i=0;i<all.length;i++){"
            "var h=all[i].href;"
            "if(!h||h.indexOf('http')!==0)continue;"
            "if(h.indexOf('baidu.com')!==-1)continue;"
            "if(h.indexOf('s?wd=')!==-1||h.indexOf('s?word=')!==-1||h.indexOf('s?tn=')!==-1)continue;"
            "if(h.indexOf('passport')!==-1||h.indexOf('login')!==-1)continue;"
            "if(h.indexOf('regagreement')!==-1||h.indexOf('register')!==-1||h.indexOf('sso')!==-1)continue;"
            "var text=(all[i].textContent||'').trim();"
            "var score=text.length;"
            "var p=all[i].closest('h1,h2,h3,h4,h5');"
            "if(p)score+=50;"
            "candidates.push({url:h,score:score,text:text.substring(0,60)});"
            "}"
            "candidates.sort(function(a,b){return b.score-a.score;});"
            "if(candidates.length>0){"
            "var best=candidates[0].url;"
            "for(var j=0;j<all.length;j++){"
            "if(all[j].href===best){all[j].click();return'clicked:'+best.substring(0,80);}"
            "}"
            "}"
            "return'no_link';"
            "})()"
        )
        r = self.opencli("eval", check=False, cmd_extra=js)
        result = (r.stdout or "").strip()
        return "clicked" in result

    def extract_source_content(self, source_url: str, max_chars: int = 4000) -> str:
        if not source_url:
            return ""
        print(f"\n[提取] 提取源页面正文...")

        # 搜索/列表页直接跳过 open（容易超时且内容无意义），用摘要兜底
        is_listing = any(kw in source_url for kw in (
            "s?word=", "s?wd=", "s?tn=", "m.baidu.com/s?", "/weibo?", "s.weibo.com/weibo"))
        if is_listing:
            print(f"  搜索/列表页，跳过源页面提取，将使用摘要扩写")
            return ""

        self.opencli(f"open {source_url}", check=False, timeout=60)
        time.sleep(4)

        r = self.opencli(f"extract --chunk-size {max_chars}", check=False, timeout=60)
        content = (r.stdout or "").strip()
        if content:
            lines = content.split("\n")
            cleaned = [l for l in lines if not l.startswith("{") and not l.startswith("[out]")]
            content = "\n".join(cleaned).strip()
        print(f"  提取到 {len(content)} 字符" if content else f"  提取失败或无内容")
        return content[:max_chars]

    def collect_images_from_source(self, source_url: str, save_dir: Path, max_images: int = 2) -> list:
        if not source_url:
            return []
        save_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n[图片] 采集配图...")
        print(f"  源 URL: {source_url[:80]}...")
        self.opencli(f"open {source_url}", check=False, timeout=60)
        print(f"  等待页面渲染...")
        for wait_i in range(15):
            time.sleep(1.5)
            r = self.opencli("eval", check=False, noisy=False,
                             cmd_extra="(()=>{return document.querySelectorAll('img').length+','+document.readyState;})()")
            out = (r.stdout or "").strip()
            parts = out.split(",")
            img_count = int(parts[0]) if parts and parts[0].isdigit() else 0
            if img_count > 0 and len(parts) > 1 and parts[1] == "complete":
                break
            if wait_i == 0 or wait_i % 3 == 0:
                print(f"  等待中... ({img_count}张图, {parts[1] if len(parts)>1 else '?'})")
        r = self.opencli("eval", check=False, cmd_extra=IMG_EXTRACT_JS)
        try:
            images = json.loads(r.stdout.strip()) if r.stdout.strip() else []
        except json.JSONDecodeError:
            images = []
        print(f"  找到 {len(images)} 张候选图片")
        if not images:
            return []
        downloaded = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0",
            "Referer": quote(source_url, safe=':/?=&%#'),
        }
        for i, img in enumerate(images[:max_images]):
            src = img["src"]
            if src.startswith("//"):
                src = "https:" + src
            src = quote(src, safe=':/?=&%#')
            w, h = img["w"], img["h"]
            print(f"  下载 ({w}x{h}): {src[:100]}...")
            try:
                resp = requests.get(src, headers=headers, timeout=30)
                if resp.status_code == 200 and len(resp.content) > MIN_IMAGE_BYTES:
                    ext = ".jpg"
                    if ".png" in src.lower():
                        ext = ".png"
                    elif ".webp" in src.lower():
                        ext = ".webp"
                    fname = f"img_{i+1:02d}{ext}"
                    fpath = save_dir / fname
                    fpath.write_bytes(resp.content)
                    if ext == ".webp":
                        try:
                            from PIL import Image
                            im = Image.open(fpath)
                            png_path = save_dir / f"img_{i+1:02d}.png"
                            im.save(png_path, "PNG")
                            fpath.unlink()
                            fpath = png_path
                            fname = f"img_{i+1:02d}.png"
                            print(f"  已转换: {fname} ({len(resp.content)}→{fpath.stat().st_size} bytes)")
                        except Exception as e:
                            print(f"  转换失败: {e}, 保留原格式")
                    else:
                        print(f"  已保存: {fname} ({len(resp.content)} bytes)")
                    downloaded.append(fpath)
            except Exception as e:
                print(f"  下载失败: {e}")
        return downloaded

    # ============================================================
    # AI 扩写
    # ============================================================

    def enrich_article_with_source(self, article: dict, source_content: str) -> dict | None:
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not api_key or not source_content or len(source_content) < MIN_SOURCE_CONTENT:
            if source_content and len(source_content) < MIN_SOURCE_CONTENT:
                print("[扩写] 源内容太少，跳过扩写")
            return None
        print(f"\n[扩写] 基于源内容重新生成文章...")
        prompt = ENRICH_PROMPT.format(
            title=article.get("title", ""),
            platform=article.get("platform", ""),
            source_content=source_content[:3500]
        )
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一个资深的百家号内容创作者，擅长撰写有深度、结构清晰的热点分析文章。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 2500,
            "temperature": 0.7,
            "response_format": {"type": "json_object"}
        }
        api_url = os.environ.get("AI_API_URL") or "https://api.deepseek.com/v1/chat/completions"
        for attempt in range(2):
            try:
                time.sleep(0.5)
                resp = requests.post(api_url, headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }, json=payload, timeout=120)
                if resp.status_code == 200:
                    data = resp.json()
                    result = json.loads(data["choices"][0]["message"]["content"])
                    new_title = result.get("title", article["title"])
                    new_content = result.get("content", article["content"])
                    image_keywords = result.get("image_keywords", "")
                    print(f"  新标题: {new_title[:40]}")
                    print(f"  新正文字数: {len(new_content)}")
                    if image_keywords:
                        print(f"  配图关键词: {image_keywords}")
                    return {"title": new_title, "content": new_content, "image_keywords": image_keywords}
                if resp.status_code == 429:
                    time.sleep(15)
                    continue
                print(f"  [扩写] API错误 {resp.status_code}")
            except Exception as e:
                print(f"  [扩写] 异常: {e}")
                if attempt < 1:
                    time.sleep(5)
        return None

    # ============================================================
    # 主发布流程
    # ============================================================

    def _enrich_article(self, article: dict, article_file: Path) -> tuple[Path | None, list]:
        """Step 0: 源内容提取 + AI扩写 + 配图。返回 (cover_path, inline_images)。
        cover_image 为 None 表示扩写失败。"""
        source_url = self.parse_source_url(article_file)
        platform = self.parse_source_platform(article_file)

        pre_images = self.find_article_images(article_file)
        cover_image = pre_images["cover"]
        images = list(pre_images["inline"])
        enriched = None

        # AI 扩写
        if source_url and len(article.get("content", "")) < MIN_ARTICLE_CONTENT:
            source_content = self.extract_source_content(source_url)
            if source_content and len(source_content) >= MIN_SOURCE_CONTENT:
                source_file = article_file.with_suffix(".source.txt")
                source_file.write_text(source_content, encoding="utf-8")
                print(f"  [源内容] 已保存: {source_file.name} ({len(source_content)} 字)")
            if not source_content or len(source_content) < MIN_SOURCE_CONTENT:
                summary = self.parse_summary(article_file)
                if summary:
                    print(f"\n[扩写] 源页面提取失败，改用摘要 ({len(summary)} 字)")
                    source_content = f"【原始资料】\n这是关于「{article['title']}」的一则新闻报道，来自{platform}平台。\n\n核心事实：{summary}\n\n请基于以上核心事实进行客观改写，保留关键信息，用自己的语言重新组织表达。"
            if source_content and len(source_content) >= MIN_SOURCE_CONTENT:
                article["platform"] = platform
                enriched = self.enrich_article_with_source(article, source_content)
                if enriched:
                    article.update(enriched)
                    self._save_enriched_article(article_file, article)
            else:
                print(f"\n[扩写] 无可用素材（源页面+摘要均为空），跳过扩写")

        if "发布时基于源内容 AI 扩写" in article.get("content", ""):
            print(f"[{self.platform_name}] 扩写失败，正文仍为占位符，终止发布")
            return None, []

        # 配图
        if not pre_images["cover"] and not pre_images["inline"] and not images:
            keywords = enriched.get("image_keywords", "") if (enriched and isinstance(enriched, dict)) else ""
            print(f"\n[配图] 百度/Bing搜图: {article.get('title', '')[:30]}")
            from image_search import get_images_for_article
            result = get_images_for_article(
                article.get("title", "")[:30], article_file.stem, article_file.parent,
                count=3, fallback_query=keywords)
            if result["cover"]:
                cover_image = result["cover"]
            images = list(result["inline"])

        if pre_images["cover"] or pre_images["inline"]:
            print(f"\n[配图] 使用预下载图片: 封面={'有' if cover_image else '无'}, 配图{len(images)}张")

        return cover_image, images

    def prepare_editor(self, title: str = "") -> bool:
        """串行准备：切 profile 后立即绑定 session 到当前 Chrome profile。
        之后 fill_content / insert_images / click_publish 等 session 隔离命令可并行。"""
        self.ensure_daemon()
        if not self.open_editor():
            return False
        if title:
            self.fill_title(title)
        self._editor_opened = True
        return True

    def publish(self, article_path: str = None, mode: str = None):
        if mode is None:
            mode = self.get_publish_mode()
        print(f"\n{'=' * 55}")
        print(f"  发布到 {self.platform_name}")
        print(f"{'=' * 55}")

        self.ensure_daemon()

        if article_path:
            article_file = Path(article_path)
        else:
            article_file = self.find_latest_article(str(OUTPUT_DIR))

        if not article_file or not article_file.exists():
            print(f"[{self.platform_name}] 没有文章，跳过")
            return False

        article = self.parse_article(article_file)

        if f"> 已发布：{self.platform_name}" in article_file.read_text(encoding="utf-8"):
            print(f"[{self.platform_name}] 已发布过此平台，跳过")
            return False

        print(f"\n文章: {article['title'][:40]}")
        print(f"正文字数: {len(article['content'])}")
        print(f"发布模式: {'立即发布' if mode == 'publish' else '存草稿'}")

        # Step 0: 源内容提取 + AI扩写 + 配图
        cover_image, images = self._enrich_article(article, article_file)
        if cover_image is None:
            return False  # 扩写失败
        if article.get("content", "") == "":
            print(f"[{self.platform_name}] 正文为空，终止发布")
            return False

        # _enrich_article 中的 extract_source_content 会导航到源页面。
        # 编辑器已打开时，必须回到编辑器页面，否则后续 fill/click 全在源页面上执行。
        if self._editor_opened:
            self.opencli(f"open {self.edit_url}", check=False, timeout=60)
            time.sleep(3)

        # Step 1-5: 编辑器 → 标题 → 正文(图文穿插) → 封面 → 发布
        if self._editor_opened:
            print(f"[{self.platform_name}] 编辑器已就绪（串行准备阶段已打开）")
        else:
            self.ensure_daemon()
            if not self.open_editor():
                print(f"[{self.platform_name}] 编辑器打开失败")
                return False

        self.fill_title(article["title"])

        # 图文穿插：按 [IMG] 标记拆分，文字和图片交替插入
        raw_content = article["content"]
        segments = raw_content.split("[IMG]")
        segments = [s.strip() for s in segments if s.strip()]

        inline_images = [img for img in images if img != cover_image]
        if len(inline_images) < len(images):
            print(f"\n[去重] 已跳过封面图，正文配图 {len(inline_images)} 张")

        has_markers = "[IMG]" in raw_content
        if has_markers and inline_images:
            print(f"\n[图文] 穿插模式: {len(segments)}段文字 + {len(inline_images)}张图")
            img_idx = 0
            for i, seg in enumerate(segments):
                # 第一段清空编辑器，后续段追加以保留之前插入的图片
                is_first = (i == 0)
                ok = self.fill_content(seg, clear_first=is_first)
                if not ok:
                    print(f"  [WARN] 第{i+1}段内容填充失败，继续后续段落...")
                time.sleep(0.5)
                # 最后一段文字后不插图片
                if img_idx < len(inline_images) and i < len(segments) - 1:
                    print(f"  [图文] 插入第{img_idx+1}张图片")
                    self.insert_images_to_editor([inline_images[img_idx]])
                    img_idx += 1
                    time.sleep(1)
            # 剩余的图片插在文末
            while img_idx < len(inline_images):
                print(f"  [图文] 文末追加第{img_idx+1}张图片")
                self.insert_images_to_editor([inline_images[img_idx]])
                img_idx += 1
                time.sleep(1)
        else:
            ok = self.fill_content(raw_content)
            if not ok:
                print(f"  [WARN] 正文填充失败，继续流程...")
            self.insert_images_to_editor(inline_images)

        if cover_image and cover_image.exists():
            print(f"\n[封面] 设置封面图: {cover_image.name}")
            self.set_cover_image(cover_image)
        elif images and not cover_image:
            print(f"\n[封面] 无独立封面，用首张配图作为封面")
            self.set_cover_image(images[0])
            cover_image = images[0]

        time.sleep(2)
        self._verify_content(article)

        published = self.click_publish(mode)

        if published:
            self._mark_published(article_file)
            print(f"[{self.platform_name}] 发布完成")
        else:
            print(f"[{self.platform_name}] 发布未完成（按钮未找到或操作失败）")
        return published

    def _mark_published(self, article_path: Path):
        if not article_path.exists():
            return
        text = article_path.read_text(encoding="utf-8")
        tag = f"> 已发布：{self.platform_name}"
        if tag in text:
            return
        lines = text.split("\n")
        last_meta = -1
        for i, line in enumerate(lines):
            if line.startswith("> "):
                last_meta = i
        if last_meta >= 0:
            lines.insert(last_meta + 1, tag)
            article_path.write_text("\n".join(lines), encoding="utf-8")

    def _verify_content(self, article: dict):
        """延迟回读验证标题与正文（子类可覆盖）"""
        pass

    def screenshot(self, save_dir: Path):
        """截取当前页面截图，保存到指定目录"""
        try:
            path = save_dir / "screenshot.png"
            self.opencli(f"screenshot {self._shell_quote_win(str(path))}", check=False, timeout=30)
            print(f"[截图] 已保存: {path.name}")
        except Exception as e:
            print(f"[截图] 失败: {e}")
