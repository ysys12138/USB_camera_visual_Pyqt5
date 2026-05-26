
import os
import sys
from pathlib import Path

def is_frozen():
    """判断是否是打包后的环境"""
    return getattr(sys, 'frozen', False)

def get_root_dir():
    """获取项目根目录（开发模式下为当前目录，打包后为 exe 所在目录）"""
    if is_frozen():
        # 打包后：exe 所在目录
        return Path(sys.executable).parent
    else:
        # 开发模式：main.py 的上级目录
        return Path(__file__).parent.parent

def get_data_dir():
    """获取 data 目录路径（始终在程序同级目录下）"""
    root = get_root_dir()
    data_path = root / "data"
    data_path.mkdir(exist_ok=True)  # 自动创建
    return data_path

def get_templates_dir():
    return get_data_dir() / "templates"

def get_screenshots_dir():
    ret = get_data_dir() / "screenshots"
    ret.mkdir(exist_ok=True)  # 自动创建
    return ret

def get_records_dir():
    ret = get_data_dir() / "records"
    ret.mkdir(exist_ok=True)  # 自动创建
    return ret

def get_utils_dir():
    return get_root_dir()/"utils"


