"""从 apikeys.conf 加载配置到 os.environ，所有模块应在读取环境变量前调用 load_config()

配置文件格式（支持 # 注释和分区）：
    # 注释行
    KEY = value
    KEY = value  # 行尾注释
"""
import os
import re
from pathlib import Path

_CONFIG_LOADED = False
# 优先使用本地目录的配置文件，不存在则回退到父目录
HERE = Path(__file__).parent.resolve()
LOCAL_CONFIG = HERE / "config" / "apikeys.conf"
PARENT_CONFIG = HERE.parent / "apikeys.conf"
CONFIG_PATH = LOCAL_CONFIG if LOCAL_CONFIG.exists() else PARENT_CONFIG


def load_config(config_path: Path = None):
    """加载 .conf 配置文件到 os.environ，只会执行一次"""
    global _CONFIG_LOADED
    if _CONFIG_LOADED:
        return
    _CONFIG_LOADED = True

    path = config_path or CONFIG_PATH
    if not path.exists():
        print(f"[Config] 配置文件不存在: {path}")
        return

    try:
        text = path.read_text(encoding="utf-8")
        count = 0
        for line in text.splitlines():
            # 去掉行尾注释和首尾空白
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # 去掉行内注释（# 后面的内容），但要保留值
            # 匹配 KEY = VALUE 格式
            m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$', stripped)
            if not m:
                continue

            key = m.group(1)
            value = m.group(2).strip()

            # 如果值末尾有行尾注释，切掉
            # 但不能误切 URL 中的 #，所以只在值不以 http 开头时处理
            if not value.startswith("http"):
                comment_pos = value.find(" #")
                if comment_pos == -1:
                    comment_pos = value.find("\t#")
                if comment_pos > 0:
                    value = value[:comment_pos].strip()
            # 对于 URL 类型的值，找最后一个空格后的 #
            if value.startswith("http"):
                # 简单处理：如果 URL 后面有空格和 #，说明是注释
                space_hash = value.rfind(" #")
                if space_hash > 0 and value[:space_hash].startswith("http"):
                    value = value[:space_hash].strip()

            if value and not os.environ.get(key):
                os.environ[key] = value
                count += 1

        print(f"[Config] 已加载 {count} 项配置: {path}")
    except Exception as e:
        print(f"[Config] 加载失败: {e}")


# 自动加载（被导入时执行）
load_config()
