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


def sh_run(cmd: str, timeout: int = 120) -> subprocess.CompletedProcess:
    """执行 shell 命令，强制 UTF-8 编码"""
    return subprocess.run(
        cmd, shell=True, capture_output=True,
        encoding="utf-8", errors="replace",
        timeout=timeout
    )


def opencli(cmd: str, check: bool = True, cmd_extra: str = "") -> subprocess.CompletedProcess:
    """执行 opencli browser 命令"""
    if cmd_extra:
        full_cmd = f"opencli browser {SESSION} {cmd} {cmd_extra}"
    else:
        full_cmd = f"opencli browser {SESSION} {cmd}"
    print(f"  $ opencli browser {SESSION} {cmd}")
    result = sh_run(full_cmd)
    if check and result.returncode != 0:
        err = (result.stderr or "").strip()[:300]
        if err:
            print(f"  [stderr] {err}")
    out = (result.stdout or "").strip()
    if out:
        print(f"  [out] {out[:500]}")
    return result


def ensure_daemon():
    """确保 opencli daemon 在运行"""
    r = sh_run("opencli daemon status")
    if "running" not in (r.stdout or ""):
        print("[Setup] 启动 opencli daemon...")
        sh_run("opencli daemon restart")


def check_extension() -> bool:
    """检查 Browser Bridge 扩展是否已连接"""
    r = sh_run("opencli doctor")
    if "Extension: connected" in (r.stdout or ""):
        return True
    print("[Setup] Browser Bridge 扩展未连接，请在 Chrome 中加载扩展")
    return False


def open_editor() -> bool:
    """打开百家号图文编辑页并初始化编辑器"""
    print("\n[1/4] 打开编辑页...")
    opencli(f"open {BJH_EDIT_URL}", check=False)
    opencli("wait time 3")

    # 检查是否跳转到登录页
    r = opencli("state", check=False)
    stdout = (r.stdout or "").lower()
    if "login" in stdout or "登录" in stdout:
        print("[Error] 未登录百家号，请先在 Chrome 中登录 https://baijiahao.baidu.com/")
        return False

    # 点击侧边栏"图文"以初始化编辑器
    print("  初始化编辑器...")
    opencli("eval", check=False,
            cmd_extra='(()=>{var els=document.querySelectorAll("*");'
                      'for(var i=0;i<els.length;i++){var e=els[i];'
                      'if(e.innerText==="图文"&&e.children.length===0){e.click();return"clicked"}}'
                      'return"not found"})()')
    opencli("wait time 3")
    return True


def fill_article(title: str, content: str) -> bool:
    """填写标题和正文"""
    print("\n[2/4] 填写内容...")

    # 标题：第一个 text input
    print(f"  标题: {title[:30]}")
    opencli('click input[type="text"]', check=False)
    opencli(f'fill input[type="text"] "{title[:30]}"', check=False)

    opencli("wait time 1")

    # 正文：contenteditable div
    print(f"  正文: {len(content)} 字")
    opencli('click [contenteditable="true"]', check=False)
    opencli("keys Control+a", check=False)
    # 分段填入
    for p in content.split("\n")[:5]:
        if p.strip():
            opencli(f'type [contenteditable="true"] "{p.strip()[:300]}"', check=False)
            opencli("keys Enter", check=False)
    print("  内容已填写")

    opencli("wait time 2")
    return True


def publish_article(mode: str = "draft") -> bool:
    """发布或存草稿"""
    print(f"\n[3/4] {'存草稿' if mode == 'draft' else '发布'}...")

    btn_text = "存草稿" if mode == "draft" else "发布"
    js_click = (
        f'Array.from(document.querySelectorAll("button"))'
        f'.find(b=>b.innerText.trim()==="{btn_text}").click();'
        f'"clicked {btn_text}"'
    )
    opencli("eval", check=False, cmd_extra=js_click)

    opencli("wait time 5")
    print(f"  已点击「{btn_text}」")
    return True


def verify_published() -> bool:
    """验证结果"""
    print("\n[4/4] 验证...")
    r = opencli("state", check=False)
    out_lower = (r.stdout or "").lower()
    if "err" in out_lower or "错误" in out_lower:
        opencli("screenshot /tmp/bjh_error.png", check=False)
        print("  可能有错误，截图已保存")
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
