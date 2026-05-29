"""多账号轮换 — 通过 opencli profile 切换 Chrome 用户身份，每个平台多账号轮流发布

原理：
  opencli 通过 Browser Bridge 扩展连接 Chrome，每个 Chrome Profile 有独立 Cookie/Session。
  `opencli profile list` 可查看已连接的 profile（对应不同 Chrome 用户）。
  切换 profile = 切换登录账号，无需手动输密码。

配置方式：
  1. 在 Chrome 中为每个账号创建独立 Profile（chrome://settings/ → 管理个人资料）
  2. 每个 Profile 登录对应平台
  3. 运行 `opencli profile list` 查看各 Profile 的 contextId 或别名
  4. 填写 accounts.json
"""
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).parent.parent
ACCOUNTS_FILE = HERE / "config" / "accounts.json"
STATE_FILE = HERE / "config" / "_account_state.json"


def load_accounts() -> dict:
    """加载账号配置 {platform: [{name, opencli_profile}, ...]}"""
    if ACCOUNTS_FILE.exists():
        return json.loads(ACCOUNTS_FILE.read_text(encoding="utf-8"))
    return {}


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
            ["opencli", "profile", "use", profile],
            capture_output=True, text=True,
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


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    return {}


def _save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
