"""
核心业务逻辑层
只包含算法和纯逻辑，不依赖UI或文件系统
"""

from .activation import ActivationCore
from .activation import ActivationRecord
from .config_manager import UserConfig
from .encryption import StateEncryptor

__all__ = [
    'ActivationCore',
    'ActivationRecord',
    'UserConfig',
    'StateEncryptor'
]