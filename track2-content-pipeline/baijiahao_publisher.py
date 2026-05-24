"""百家号图文发布：Playwright 账号密码登录 + Cookie 持久化 + 自动发布"""
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


def generate_cookie(cookie_file: str, account: dict):
    """使用账号密码登录百家号，自动检测完成并保存 Cookie"""
    from playwright.sync_api import sync_playwright

    phone = account.get("phone", "")
    password = account.get("password", "")

    if not phone or not password or phone.startswith("在此填写"):
        print("[Login] 请先在 baijiahao_config.json 中填写手机号和密码")
        print("[Login] 转用备用方案：打开浏览器手动登录...")
        return _generate_cookie_manual(cookie_file)

    print("\n" + "=" * 50)
    print("  使用账号密码登录百家号...")
    print(f"  手机号: {phone[:3]}****{phone[-4:]}")
    print("=" * 50 + "\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(locale="zh-CN")
        page = context.new_page()
        page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)

        # --- 切换到账号密码登录 ---
        try:
            # 百家号使用百度统一登录页，有多个tab
            # 可能的切换方式：点击"账号登录" / "密码登录" / "短信登录"之外的tab
            tabs_to_try = [
                "text=账号登录",
                "text=密码登录",
                "text=账号密码登录",
                "[data-type='password']",
                ".pass-tab-account",
                ".tab-item:has-text('账号')",
            ]
            for selector in tabs_to_try:
                try:
                    el = page.query_selector(selector)
                    if el and el.is_visible():
                        el.click()
                        print(f"[Login] 切换到密码登录")
                        page.wait_for_timeout(1000)
                        break
                except:
                    continue
        except Exception as e:
            print(f"[Login] 切换登录方式跳过: {e}")

        page.wait_for_timeout(1000)

        # --- 填写手机号 ---
        phone_selectors = [
            'input[placeholder*="手机"]',
            'input[placeholder*="账号"]',
            'input[placeholder*="用户名"]',
            'input[name="phone"]',
            'input[name="account"]',
            'input[name="userName"]',
            'input[type="text"]',
        ]
        phone_filled = False
        for sel in phone_selectors:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    el.click()
                    el.fill("")
                    el.fill(phone)
                    phone_filled = True
                    print(f"[Login] 已填写手机号")
                    break
            except:
                continue

        if not phone_filled:
            print("[Login] 未找到手机号输入框，尝试手动...")

        page.wait_for_timeout(500)

        # --- 填写密码 ---
        pwd_selectors = [
            'input[placeholder*="密码"]',
            'input[name="password"]',
            'input[type="password"]',
        ]
        for sel in pwd_selectors:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    el.click()
                    el.fill("")
                    el.fill(password)
                    print(f"[Login] 已填写密码")
                    break
            except:
                continue

        page.wait_for_timeout(500)

        # --- 点击登录 ---
        login_btn_selectors = [
            "button:text('登录')",
            "button:text('登 录')",
            "input[value='登录']",
            "[class*='login'] button",
            ".pass-button-submit",
        ]
        for sel in login_btn_selectors:
            try:
                btn = page.query_selector(sel)
                if btn and btn.is_visible():
                    btn.click()
                    print("[Login] 已点击登录按钮")
                    break
            except:
                continue

        # --- 自动检测登录结果 ---
        max_wait = 120  # 最长等2分钟（含可能的验证码时间）
        captcha_detected = False
        for i in range(max_wait):
            time.sleep(1)
            current_url = page.url

            # 检测是否登录成功
            if ("/builder/rc/home" in current_url or "/builder/rc/" in current_url) \
                    and "login" not in current_url:
                print(f"\n[Login] 登录成功！（{i+1}s）")
                break

            # 检测验证码/滑块
            if not captcha_detected:
                captcha_indicators = [
                    "验证码",
                    "滑块",
                    "请点击",
                    "拖动",
                    "安全验证",
                    "passMod",
                    "captcha",
                    "spider",
                ]
                try:
                    page_text = page.content()
                    for indicator in captcha_indicators:
                        if indicator.lower() in page_text.lower():
                            print(f"\n[Login] 检测到可能的验证码，请在浏览器中手动完成...")
                            captcha_detected = True
                            break
                except:
                    pass
        else:
            print("\n[Login] 等待超时，保存当前 Cookie（可能为已登录状态）...")

        context.storage_state(path=cookie_file)
        print(f"[Login] Cookie 已保存到: {cookie_file}")
        browser.close()


def _generate_cookie_manual(cookie_file: str):
    """备用方案：打开浏览器让用户手动登录"""
    from playwright.sync_api import sync_playwright

    print("\n" + "=" * 50)
    print("  手动登录模式：请在浏览器中自行登录")
    print("  登录成功后程序会自动检测并保存 Cookie")
    print("=" * 50 + "\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(locale="zh-CN")
        page = context.new_page()
        page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
        print("[Login] 已打开登录页...")

        max_wait = 300
        for i in range(max_wait):
            time.sleep(1)
            current_url = page.url
            if ("/builder/rc/home" in current_url or "/builder/rc/" in current_url) \
                    and "login" not in current_url:
                print(f"\n[Login] 检测到登录成功！（{i+1}s）")
                break
        else:
            print("\n[Login] 等待超时，保存当前 Cookie...")

        context.storage_state(path=cookie_file)
        print(f"[Login] Cookie 已保存到: {cookie_file}")
        browser.close()


def ensure_auth(cookie_file: str, account: dict = None):
    """确保已登录：Cookie 有效则复用，否则用账号密码登录"""
    if os.path.exists(cookie_file) and cookie_auth(cookie_file):
        return True

    print("[Auth] Cookie 不存在或已失效，使用账号密码登录...")
    generate_cookie(cookie_file, account or {})
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
    account = cfg.get("account", {})
    ensure_auth(cookie_file, account)

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
    parser.add_argument("--login", action="store_true", help="强制重新登录（删除旧Cookie）")
    args = parser.parse_args()

    cookie_file = get_cookie_path()

    if args.login and os.path.exists(cookie_file):
        os.remove(cookie_file)
        print("[Login] 已删除旧 Cookie，准备重新登录")

    run(article_path=args.file, mode=args.mode, cookie_file=cookie_file)
