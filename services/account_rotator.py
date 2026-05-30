"""多账号轮换 — 通过 opencli profile 切换 Chrome 用户身份，每个平台多账号轮流发布

原理：
  opencli 通过 Browser Bridge 扩展连接 Chrome，每个 Chrome Profile 有独立 Cookie/Session。
  `opencli profile list` 可查看已连接的 profile（对应不同 Chrome 用户）。
  切换 profile = 切换登录账号，无需手动输密码。

配置格式（accounts.json，以写手分组）：
  {
    "写手A": {
      "opencli_profile": "ubz32tq7",    // Chrome Profile ID（opencli profile list 查看）
      "platforms": ["baijiahao", "toutiao"]
    },
    "写手B": {
      "opencli_profile": "profile_2_id",
      "platforms": ["baijiahao"]
    }
  }

说明：
  - 顶层 key = 写手名称
  - opencli_profile = Chrome Profile ID，空字符串 = 默认 Profile
  - platforms = 该写手在哪些平台有号
  - 同名写手出现在多个平台 = 同一个人、同一套 Cookie
  - 缺平台只打 warn 不拦截

操作步骤：
  1. Chrome 新建 Profile → 登录平台号 → 连 opencli 扩展
  2. opencli profile list 拿到 Profile ID
  3. 填入 accounts.json
"""
import json
import os
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).parent.parent
ACCOUNTS_FILE = HERE / "config" / "accounts.json"
STATE_FILE = HERE / "config" / "_account_state.json"


def load_accounts() -> dict:
    """加载账号配置，返回 {platform: [{name, opencli_profile}, ...]}

    accounts.json 以写手分组，此函数转换为内部平台优先格式：
      写手A: {profile, platforms: [baijiahao, toutiao]}
      → baijiahao: [{name: 写手A, opencli_profile: xxx}], toutiao: [{name: 写手A, ...}]
    """
    if not ACCOUNTS_FILE.exists():
        return {}
    raw = json.loads(ACCOUNTS_FILE.read_text(encoding="utf-8"))
    result = {}
    for writer_name, writer_cfg in raw.items():
        profile = writer_cfg.get("opencli_profile", "")
        platforms = writer_cfg.get("platforms", [])
        for plat in platforms:
            result.setdefault(plat, []).append({
                "name": writer_name,
                "opencli_profile": profile,
            })
    return result


def get_all_accounts(platform: str) -> list:
    """返回平台所有账号，至少返回一个空账号（使用默认 profile）"""
    accounts = load_accounts()
    platform_accounts = accounts.get(platform, [])
    if not platform_accounts:
        return [{"name": "默认", "opencli_profile": ""}]
    return list(platform_accounts)


def get_account_count(platform: str) -> int:
    """返回平台账号数量"""
    return len(get_all_accounts(platform))


def switch_profile(account: dict):
    """切换 opencli 到指定账号的 profile（全局操作，必须串行）"""
    profile = account.get("opencli_profile", "")
    if profile:
        subprocess.run(
            f"opencli profile use {profile}",
            shell=True, capture_output=True, text=True,
        )


def get_next_account(platform: str) -> dict | None:
    """获取下一个要使用的账号，推进轮换指针，并切换 opencli profile（保留兼容旧逻辑）"""
    accounts = load_accounts()
    platform_accounts = accounts.get(platform, [])
    if not platform_accounts:
        return None

    state = _load_state()
    idx = state.get(platform, 0) % len(platform_accounts)
    account = platform_accounts[idx]
    state[platform] = idx + 1
    _save_state(state)

    switch_profile(account)
    return account


def ensure_chrome_windows():
    """如果 opencli 没有已连接的 Profile，则打开所有 Chrome Profile 窗口"""
    r = subprocess.run(
        "opencli profile list", shell=True,
        capture_output=True, encoding="utf-8", errors="replace"
    )
    connected_count = (r.stdout or "").count(" — connected")
    if connected_count > 0:
        print(f"[Chrome] {connected_count} 个 Profile 已连接，无需打开窗口")
        return

    chrome_exe = os.path.expandvars(
        r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"
    )
    alt_chrome = os.path.expandvars(
        r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
    )
    for p in [chrome_exe, alt_chrome]:
        if os.path.isfile(p):
            chrome_exe = p
            break
    else:
        print("[Chrome] 找不到 Chrome，跳过")
        return

    user_data = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
    local_state = Path(user_data) / "Local State"
    if not local_state.exists():
        print("[Chrome] 找不到 Local State，跳过")
        return

    profiles = json.loads(local_state.read_text(encoding="utf-8"))
    info = profiles.get("profile", {}).get("info_cache", {})

    for dir_name in info:
        profile_dir = Path(user_data) / dir_name
        if not profile_dir.exists():
            continue
        name = info[dir_name].get("name", dir_name)
        print(f"[Chrome] 打开窗口: {name}")
        subprocess.Popen(
            [chrome_exe, f"--profile-directory={dir_name}"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        time.sleep(0.5)

    print("[Chrome] 等待扩展连接...")
    time.sleep(3)


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    return {}


def _save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
