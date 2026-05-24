"""百家号图文发布：Playwright 扫码登录 + Cookie 持久化 + 自动发布"""
import json
import os
import sys
import time
import glob
from pathlib import Path
from datetime import datetime

HERE = Path(__file__).parent

# 配置
CONFIG_PATH = HERE / "baijiahao_config.json"

# 百家号关键 URL
LOGIN_URL = "https://baijiahao.baidu.com/builder/theme/bjh/login"
HOME_URL = "https://baijiahao.baidu.com/builder/rc/home"
EDIT_URL = "https://baijiahao.baidu.com/builder/rc/edit"
ARTICLE_URL = "https://baijiahao.baidu.com/builder/rc/edit?type=article"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_cookie_path():
    cfg = load_config()
    cookie_file = HERE / cfg["cookie_file"]
    cookie_file.parent.mkdir(parents=True, exist_ok=True)
    return str(cookie_file.absolute())


def ensure_playwright():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[安装] 正在安装 playwright...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("[OK] Playwright + Chromium 安装完成")


def cookie_auth(cookie_file: str) -> bool:
    """检查已保存的 Cookie 是否仍有效"""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context(storage_state=cookie_file)
            page = context.new_page()
            page.goto(HOME_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(5000)

            # 如果页面上有"注册/登录百家号"，说明 cookie 已失效
            login_el = page.query_selector("a:has-text('注册/登录百家号'), button:has-text('登录')")
            if login_el and login_el.is_visible():
                print("[Auth] Cookie 已失效，需要重新登录")
                return False
            print("[Auth] Cookie 有效")
            return True
        except Exception as e:
            print(f"[Auth] 验证异常: {e}")
            return False
        finally:
            browser.close()


def generate_cookie(cookie_file: str):
    """打开浏览器，等待用户扫码登录，自动检测完成并保存 Cookie"""
    from playwright.sync_api import sync_playwright

    print("\n" + "=" * 50)
    print("  请在打开的浏览器中完成扫码登录")
    print("  用百度 App 扫描页面上的二维码")
    print("  登录成功后会自动检测并保存 Cookie")
    print("=" * 50 + "\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(locale="zh-CN")
        page = context.new_page()
        page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
        print("[Login] 已打开登录页，请扫码...")

        # 轮询检测登录状态：最长等 5 分钟
        max_wait = 300
        for i in range(max_wait):
            time.sleep(1)
            current_url = page.url
            # 登录成功后通常会跳转到创作者主页
            if "/builder/rc/home" in current_url or "/builder/rc/" in current_url:
                if "login" not in current_url:
                    print(f"\n[Login] 检测到登录成功！（{i+1}s）")
                    break
            # 备用：检查页面是否去掉了登录按钮
            try:
                login_btn = page.query_selector("a:has-text('注册/登录')")
                if not login_btn or not login_btn.is_visible():
                    page.goto(HOME_URL, wait_until="domcontentloaded", timeout=10000)
                    page.wait_for_timeout(3000)
                    if "/builder/rc/home" in page.url and "login" not in page.url:
                        print(f"\n[Login] 检测到登录成功！（{i+1}s）")
                        break
            except:
                pass
        else:
            print("\n[Login] 等待超时，尝试保存当前 Cookie...")

        context.storage_state(path=cookie_file)
        print(f"[Login] Cookie 已保存到: {cookie_file}")
        browser.close()


def ensure_auth(cookie_file: str):
    """确保已登录：Cookie 有效则复用，否则引导扫码"""
    if os.path.exists(cookie_file) and cookie_auth(cookie_file):
        return True

    print("[Auth] 需要登录百家号")
    generate_cookie(cookie_file)
    return True


def find_latest_article(source_dir: str) -> Path | None:
    """从 output/articles/ 找最新的一篇 txt 文章"""
    pattern = os.path.join(source_dir, "*.txt")
    files = glob.glob(pattern)
    if not files:
        print("[Publisher] 未找到待发布文章")
        return None
    latest = max(files, key=os.path.getmtime)
    return Path(latest)


def parse_article_file(filepath: Path) -> dict:
    """解析文章 txt 文件，提取标题和正文"""
    text = filepath.read_text(encoding="utf-8")
    lines = text.strip().split("\n")
    title = lines[0].strip() if lines else "无标题"
    content = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
    return {"title": title, "content": content}


def publish_article(title: str, content: str, mode: str = "draft",
                    cookie_file: str = None) -> bool:
    """使用 Playwright 发布一篇图文到百家号"""
    from playwright.sync_api import sync_playwright

    print(f"[Publish] 标题: {title[:40]}...")
    print(f"[Publish] 正文: {len(content)} 字")
    print(f"[Publish] 模式: {'草稿' if mode == 'draft' else '立即发布'}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        try:
            context = browser.new_context(
                storage_state=cookie_file,
                locale="zh-CN",
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()

            # 打开图文编辑页
            print("[Publish] 打开编辑页...")
            page.goto(ARTICLE_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)

            # --- 填写标题 ---
            title_input = page.query_selector(
                'input[placeholder*="标题"], '
                'textarea[placeholder*="标题"], '
                '[class*="title"] input, '
                '[class*="title"] textarea'
            )
            if title_input:
                title_input.click()
                title_input.fill("")
                title_input.fill(title[:30])
                print("[Publish] 标题已填写")
            else:
                # fallback: 使用 keyboard 输入
                print("[Publish] 未找到标题输入框，尝试 keyboard...")
                page.keyboard.press("Tab")
                page.keyboard.insert_text(title[:30])

            page.wait_for_timeout(1000)

            # --- 填写正文 ---
            body_el = page.query_selector(
                '[contenteditable="true"], '
                '.ql-editor, '
                '[class*="editor"] [contenteditable], '
                'iframe[class*="editor"]'
            )
            if body_el:
                body_el.click()
                page.keyboard.press("Control+a")
                page.keyboard.insert_text(content)
                print("[Publish] 正文已填写")
            else:
                print("[Publish] 未找到正文编辑区，尝试点击后输入...")
                page.mouse.click(640, 400)
                page.wait_for_timeout(500)
                page.keyboard.press("Control+a")
                page.keyboard.insert_text(content)

            page.wait_for_timeout(2000)

            # --- 发布/存草稿 ---
            if mode == "draft":
                draft_btn = page.query_selector(
                    "button:text('存草稿'), "
                    "button:text('保存草稿'), "
                    "span:text('存草稿'), "
                    "[class*='draft'] button"
                )
                if draft_btn:
                    draft_btn.click()
                    print("[Publish] 已点击「存草稿」")
                else:
                    print("[Publish] 未找到草稿按钮，等待 10s 后继续...")
                    page.wait_for_timeout(10000)
            else:
                publish_btn = page.query_selector(
                    "button:text('发布'), "
                    "button:text('立即发布'), "
                    "span:text('发布')"
                )
                if publish_btn:
                    publish_btn.click()
                    print("[Publish] 已点击「发布」")
                else:
                    print("[Publish] 未找到发布按钮，等待 10s 后继续...")
                    page.wait_for_timeout(10000)

            page.wait_for_timeout(5000)

            # 检查是否安全验证
            captcha = page.query_selector(
                "div:text('安全验证'), "
                ".passMod_dialog-container"
            )
            if captcha and captcha.is_visible():
                print("[Publish] 出现安全验证，等待 15s...")
                page.wait_for_timeout(15000)

            # 保存最新的 cookie
            context.storage_state(path=cookie_file)
            print("[Publish] Cookie 已更新")

            return True

        except Exception as e:
            print(f"[Publish] 发布异常: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            browser.close()


def run(article_path: str = None, mode: str = None, cookie_file: str = None):
    """
    主入口：
    1. 确保已登录（复用 Cookie 或扫码）
    2. 找到待发布文章
    3. 发布到百家号
    """
    ensure_playwright()

    if cookie_file is None:
        cookie_file = get_cookie_path()

    cfg = load_config()
    if mode is None:
        mode = cfg["publish"]["mode"]

    # Step 1: 登录
    print("\n[1/3] 验证登录状态...")
    ensure_auth(cookie_file)

    # Step 2: 找文章
    print("\n[2/3] 查找待发布文章...")
    if article_path:
        article_file = Path(article_path)
    else:
        article_dir = HERE / cfg["article_source_dir"]
        article_file = find_latest_article(str(article_dir))

    if not article_file:
        print("[Exit] 没有找到文章。先生成文章：ARTICLE_LIMIT=1 python pipeline.py")
        return

    article = parse_article_file(article_file)
    if not article["content"]:
        print("[Exit] 文章正文为空")
        return

    # Step 3: 发布
    print("\n[3/3] 发布文章...")
    success = publish_article(
        title=article["title"],
        content=article["content"],
        mode=mode,
        cookie_file=cookie_file
    )

    if success:
        # 标记已发布
        published_dir = article_file.parent / "published"
        published_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        new_name = f"{timestamp}_{article_file.name}"
        article_file.rename(published_dir / new_name)
        print(f"[OK] 已发布，文件移至 published/{new_name}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="百家号自动发布")
    parser.add_argument("-f", "--file", help="指定文章文件路径（不指定则用最新一篇）")
    parser.add_argument("-m", "--mode", choices=["draft", "publish"], default="draft",
                        help="发布模式：draft=存草稿, publish=立即发布")
    parser.add_argument("--login", action="store_true", help="强制重新扫码登录")
    args = parser.parse_args()

    cookie_file = get_cookie_path()

    if args.login and os.path.exists(cookie_file):
        os.remove(cookie_file)
        print("[Login] 已删除旧 Cookie，准备重新登录")

    run(article_path=args.file, mode=args.mode, cookie_file=cookie_file)
