"""
配置管理器 - 精简版
只管理你指定的几个配置项
"""

import json
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import sys

# 全局配置管理器实例
from app_config import USER_CONFIG_FILE
from utils.path_utils import get_data_dir

dir = get_data_dir()


@dataclass
class UserConfig:
    """用户配置数据类"""

    # 文件保存设置
    screenshot_dir: str = str(dir / "screenshots")
    report_dir: str = str(dir / "reports")

    # 元数据
    last_modified: str = ""
    version: str = "1.0"

    clean_day: int = 30
    max_p_number: int = 20
    hospital_name: str = "某某某"

    report_title_txt:str = '医学影像报告'


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_file: Path):
        self.config_file = config_file
        self.config = UserConfig()
        self.load()

    def load(self):
        """加载配置"""
        if not self.config_file.exists():
            return

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 只更新我们关心的字段
            for key in data:
                setattr(self.config, key, data[key])

        except Exception as e:
            print(f"[配置] 加载失败: {e}")

    def save(self):
        """保存配置"""
        try:
            self.config.last_modified = datetime.now().isoformat()
            self.config.version = "1.0"

            # 确保目录存在
            self.config_file.parent.mkdir(exist_ok=True)

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.config), f, indent=2)

            print(f"[配置] 保存成功: {self.config_file}")
            return True

        except Exception as e:
            print(f"[配置] 保存失败: {e}")
            return False

    def get_all(self):
        """获取所有配置"""
        return asdict(self.config)

    def update(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)


config_manager = ConfigManager(USER_CONFIG_FILE)
