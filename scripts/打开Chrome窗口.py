"""打开所有 Chrome Profile 窗口，确保 opencli 能连接"""
import subprocess
import json
import os
import time
from pathlib import Path

CHROME_EXE = os.path.expandvars(
    r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"
)
ALT_CHROME = os.path.expandvars(
    r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
)
USER_DATA = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")


def find_chrome() -> str:
    for p in [CHROME_EXE, ALT_CHROME]:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("找不到 Chrome，请检查安装路径")


def list_profiles() -> dict:
    """读取 Chrome Local State，返回 {目录名: 显示名}"""
    local_state = Path(USER_DATA) / "Local State"
    if not local_state.exists():
        return {}
    data = json.loads(local_state.read_text(encoding="utf-8"))
    return data.get("profile", {}).get("info_cache", {})


def main():
    chrome = find_chrome()
    profiles = list_profiles()

    if not profiles:
        print("未找到 Chrome Profile")
        return

    opened = 0
    for dir_name, info in profiles.items():
        name = info.get("name", dir_name)
        # Chrome profile 目录结构：Default 或 Profile N
        profile_dir = Path(USER_DATA) / dir_name
        if not profile_dir.exists():
            continue

        print(f"  打开: {name} ({dir_name})")
        subprocess.Popen(
            [chrome, f"--profile-directory={dir_name}"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        opened += 1
        time.sleep(0.5)  # 错开启动，避免资源竞争

    print(f"\n已打开 {opened} 个 Chrome 窗口，等待扩展连接...")
    time.sleep(3)

    # 检查 daemon 状态
    r = subprocess.run(
        "opencli daemon status", shell=True,
        capture_output=True, encoding="utf-8", errors="replace"
    )
    if "running" not in (r.stdout or ""):
        print("启动 opencli daemon...")
        subprocess.run("opencli daemon restart", shell=True, capture_output=True)
        time.sleep(2)

    r = subprocess.run(
        "opencli profile list", shell=True,
        capture_output=True, encoding="utf-8", errors="replace"
    )
    print(f"\n已连接 Profile:\n{r.stdout}")


if __name__ == "__main__":
    main()
