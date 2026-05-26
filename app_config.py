import os
import json
import sys
from pathlib import Path
from typing import Final, Any, Optional
from utils.path_utils import get_data_dir



DATA_DIR: Final[Path] = get_data_dir()
DATA_DIR.mkdir(exist_ok=True)

USER_CONFIG_FILE: Final[Path] = DATA_DIR / "user_config.json"
ACTIVATION_STATE_FILE: Final[Path] = DATA_DIR / "activation_state_2.json"
MASTER_SECRET: Final[bytes] = os.getenv( "APP_MASTER_SECRET", "my-app-secret-key-2024@v1.0-change-me-in-production" ).encode()
ENABLE_ACTIVATION: Final[bool] = True # 是否启用激活系统 ENABLE_DEBUG_MODE: Final[bool] = False # 调试模式
USER_CONFIG_FILE: Final[Path] = DATA_DIR / "user_config.json"

ACTIVATION_WINDOW_WIDTH: Final[int] = 800
ACTIVATION_WINDOW_HEIGHT: Final[int] = 800
# 缓存配置，避免重复读文件
_config_cache: Optional[dict] = None
_config_timestamp: Optional[float] = None  # 用于检测文件是否被修改


def _load_config_from_file() -> dict:
    """从文件加载配置，失败返回空字典"""
    try:
        if USER_CONFIG_FILE.exists():
            with open(USER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"⚠️ 配置文件读取失败: {e}")
    return {}


def get_config(key: str, default: Any = None) -> Any:
    """
    获取配置项，带缓存和热更新
    - 如果文件被修改，自动重新加载
    """
    global _config_cache, _config_timestamp

    # 检查文件修改时间
    try:
        mtime = USER_CONFIG_FILE.stat().st_mtime
        if _config_cache is not None and _config_timestamp == mtime:
            # 文件未变，用缓存
            pass
        else:
            # 文件变了，重新加载
            _config_cache = _load_config_from_file()
            _config_timestamp = mtime
    except OSError:
        if _config_cache is None:
            _config_cache = _load_config_from_file()

    return _config_cache.get(key, default)


def reload_config():
    """强制重新加载配置"""
    global _config_cache, _config_timestamp
    _config_cache = _load_config_from_file()
    try:
        _config_timestamp = USER_CONFIG_FILE.stat().st_mtime
    except OSError:
        _config_timestamp = None


def save_config(updates: dict):
    """保存配置到文件，并更新缓存"""
    current = _load_config_from_file()
    current.update(updates)
    try:
        with open(USER_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(current, f, ensure_ascii=False, indent=4)
        # 更新缓存
        global _config_cache, _config_timestamp
        _config_cache = current
        try:
            _config_timestamp = USER_CONFIG_FILE.stat().st_mtime
        except OSError:
            pass
    except OSError as e:
        print(f"⚠️ 保存配置失败: {e}")