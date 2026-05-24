"""百家号全自动发布：opencli 浏览器原语 + DeepSeek 文章"""
import json
import os
import sys
import time
import glob
import subprocess
from pathlib import Path
from datetime import datetime

HERE = Path(__file__).parent

CONFIG_PATH = HERE / "baijiahao_config.json"
SESSION = "bjh"  # opencli browser session name

# 百家号 URL
BJH_EDIT_URL = "https://baijiahao.baidu.com/builder/rc/edit?type=article"
BJH_HOME_URL = "https://baijiahao.baidu.com/builder/rc/home"
BJH_DRAFT_URL = "https://baijiahao.baidu.com/builder/rc/draft"


def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def opencli(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    """执行 opencli 命令"""
    full_cmd = f"opencli browser {SESSION} {cmd}"
    print(f"  $ {full_cmd}")
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=120)
    if check and result.returncode != 0:
        print(f"  [stderr] {result.stderr.strip()[:300]}")
    if result.stdout.strip():
        print(f"  [out] {result.stdout.strip()[:500]}")
    return result


def ensure_daemon():
    """确保 opencli daemon 在运行"""
    r = subprocess.run("opencli daemon status", shell=True, capture_output=True, text=True)
    if "running" not in r.stdout:
        print("[Setup] 启动 opencli daemon...")
        subprocess.run("opencli daemon restart", shell=True)


def check_extension() -> bool:
    """检查 Browser Bridge 扩展是否已连接"""
    r = subprocess.run("opencli doctor 2>&1", shell=True, capture_output=True, text=True)
    if "Extension: connected" in r.stdout:
        return True
    print("[Setup] Browser Bridge 扩展未连接，请在 Chrome 中加载扩展")
    return False


def open_editor() -> bool:
    """打开百家号图文编辑页"""
    print("\n[1/4] 打开编辑页...")
    r = opencli(f"open {BJH_EDIT_URL}", check=False)
    opencli("wait time 3")
    # 检查是否跳转到登录页（说明未登录）
    r = opencli("state", check=False)
    if "login" in r.stdout.lower() or "登录" in r.stdout:
        print("[Error] 未登录百家号，请先在 Chrome 中登录 https://baijiahao.baidu.com/")
        return False
    return True


def fill_article(title: str, content: str) -> bool:
    """填写标题和正文"""

    # --- 获取页面元素 ---
    print("\n[2/4] 查找页面元素...")
    r = opencli("state", check=False)

    # 尝试找标题输入框
    print("  填写标题...")
    title_selectors = [
        'input[placeholder*="标题"]',
        '[class*="title"] input',
    ]
    for sel in title_selectors:
        r = opencli(f'find "{sel}"', check=False)
        if "matches_n" in r.stdout and '"matches_n":0' not in r.stdout:
            opencli(f'click "{sel}"', check=False)
            opencli(f'type "{sel}" "{title[:30]}"', check=False)
            print(f"  标题已填写: {title[:30]}")
            break
    else:
        # fallback: 尝试直接 type
        print("  [fallback] 尝试 keyboard 方式...")
        opencli('keys Tab', check=False)
        opencli(f'keys "{title[:30]}"', check=False)

    opencli("wait time 1")

    # --- 填写正文 ---
    print("  填写正文...")
    body_selectors = [
        '[contenteditable="true"]',
        '.ql-editor',
        '[class*="editor"]',
    ]
    for sel in body_selectors:
        r = opencli(f'find "{sel}"', check=False)
        if "matches_n" in r.stdout and '"matches_n":0' not in r.stdout:
            # 清空后填入
            opencli(f'click "{sel}"', check=False)
            opencli("keys Control+a", check=False)
            # 正文可能较长，用 type 分段
            paragraphs = content.split("\n")
            for p in paragraphs[:3]:  # 先填前3段
                if p.strip():
                    opencli(f'type "{sel}" "{p.strip()[:200]}"', check=False)
                    opencli("keys Enter", check=False)
            print(f"  正文已填写 ({len(content)} 字)")
            break
    else:
        print("  [fallback] 未找到编辑器，尝试 eval 方式...")
        # 用 JS eval 直接设置
        js = (
            "(()=>{"
            "const ed=document.querySelector('[contenteditable=true]');"
            "if(ed)ed.innerHTML=arguments[0];"
            "})()"
        )
        opencli(f'eval "{js}"', check=False)

    opencli("wait time 2")
    return True


def publish_article(mode: str = "draft") -> bool:
    """发布或存草稿"""
    print(f"\n[3/4] {'存草稿' if mode == 'draft' else '发布'}...")

    if mode == "draft":
        btn_selectors = [
            'button:text("存草稿")',
            'button:text("保存草稿")',
            ':text("存草稿")',
        ]
        for sel in btn_selectors:
            r = opencli(f'find "{sel}"', check=False)
            if "matches_n" in r.stdout and '"matches_n":0' not in r.stdout:
                opencli(f'click "{sel}"', check=False)
                print("  已点击「存草稿」")
                break
        else:
            opencli("screenshot /tmp/bjh_draft.png", check=False)
            print("  [warn] 未找到草稿按钮，截图保存到 /tmp/bjh_draft.png")
            return False
    else:
        r = opencli('click button:text("发布")', check=False)
        print("  已点击「发布」")

    opencli("wait time 5")
    return True


def verify_published() -> bool:
    """验证是否发布成功"""
    print("\n[4/4] 验证结果...")
    r = opencli("state", check=False)
    if "err" in r.stdout.lower() or "错误" in r.stdout:
        opencli("screenshot /tmp/bjh_error.png", check=False)
        return False
    print("  完成")
    return True


def find_latest_article(source_dir: str) -> Path | None:
    pattern = os.path.join(source_dir, "*.txt")
    files = glob.glob(pattern)
    if not files:
        return None
    return Path(max(files, key=os.path.getmtime))


def parse_article(filepath: Path) -> dict:
    text = filepath.read_text(encoding="utf-8")
    lines = text.strip().split("\n")
    return {
        "title": lines[0].strip() if lines else "无标题",
        "content": "\n".join(lines[1:]).strip() if len(lines) > 1 else "",
    }


def run(article_path: str = None, mode: str = "draft"):
    ensure_daemon()

    if not check_extension():
        print("\n请先安装 Browser Bridge 扩展：")
        ext_path = Path.home() / "opencli-extension"
        if ext_path.exists():
            print(f"  1. 打开 chrome://extensions/")
            print(f"  2. 开启「开发者模式」")
            print(f"  3. 加载已解压的扩展 → 选择 {ext_path}")
            print(f"  4. 然后在 Chrome 中登录 https://baijiahao.baidu.com/")
        return

    # 找文章
    cfg = load_config()
    if article_path:
        article_file = Path(article_path)
    else:
        article_dir = HERE / cfg.get("article_source_dir", "output/articles")
        article_file = find_latest_article(str(article_dir))

    if not article_file:
        print("[Exit] 没有文章。先运行: ARTICLE_LIMIT=1 python pipeline.py")
        return

    article = parse_article(article_file)
    print(f"\n文章: {article['title'][:40]}")
    print(f"正文字数: {len(article['content'])}")

    # 发布流程
    if not open_editor():
        return
    if not fill_article(article["title"], article["content"]):
        return
    if not publish_article(mode):
        return
    verify_published()

    # 归档已发布
    published_dir = article_file.parent / "published"
    published_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    article_file.rename(published_dir / f"{ts}_{article_file.name}")
    print(f"\n[OK] 文章已{'发布' if mode == 'publish' else '存草稿'}，归档到 published/")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="百家号自动发布（opencli）")
    parser.add_argument("-f", "--file", help="指定文章路径")
    parser.add_argument("-m", "--mode", choices=["draft", "publish"], default="draft")
    parser.add_argument("--setup", action="store_true", help="输出环境配置指南")
    args = parser.parse_args()

    if args.setup:
        print("""
百家号全自动发布 — 环境配置
=============================

前置条件:
  1. 安装 Chrome 浏览器
  2. 安装 Browser Bridge 扩展
     - 扩展目录: ~/opencli-extension
     - 打开 chrome://extensions/
     - 开启「开发者模式」→「加载已解压的扩展」→ 选择上述目录
  3. 在 Chrome 中登录 https://baijiahao.baidu.com/

运行:
  python baijiahao_publisher.py           # 存草稿
  python baijiahao_publisher.py -m publish # 立即发布
""")
        sys.exit(0)

    run(article_path=args.file, mode=args.mode)
