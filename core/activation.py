"""
激活核心模块 - 合并数据和逻辑
包含数据模型和核心算法
"""

import json
import hashlib
import secrets
import string
import re
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List, Tuple
from .encryption import StateEncryptor
import base64
import os

STATE_ENCRYPTION_KEY = base64.b64encode(
    os.getenv(
        "APP_STATE_KEY",
        "my-secret-state-key-32-bytes-long!!"
    ).encode().ljust(32, b'!')[:32]
).decode()

# ==================== 数据模型 ====================
@dataclass
class ActivationRecord:
    """激活记录"""
    license_key: str
    activated_at: datetime

    def to_dict(self):
        return {
            'license_key': self.license_key,
            'activated_at': self.activated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data):
        activated_at = data['activated_at']
        if isinstance(activated_at, str):
            activated_at = datetime.fromisoformat(activated_at)
        return cls(data['license_key'], activated_at)


@dataclass
class ActivationStatus:
    """激活状态"""

    is_activated: bool = False
    activation_record: Optional[ActivationRecord] = None
    used_keys: List[str] = field(default_factory=list)
    encryptor = StateEncryptor(STATE_ENCRYPTION_KEY)

    def save(self, filepath: Path):
        """保存到文件"""
        data = {
            'is_activated': self.is_activated,
            'used_keys': self.used_keys
        }
        if self.activation_record:
            data['activation_record'] = self.activation_record.to_dict()

        try:
            self.encryptor.save_encrypted(data, filepath)
            return True
        except:
            return False

    @classmethod
    def load(cls,filepath:Path):
        """从文件加载（自动解密）"""

        status = cls()
        data = status.encryptor.load_encrypted(filepath)
        if not data:
            return status  # 文件不存在或解密失败

        status.is_activated = data.get('is_activated', False)
        status.used_keys = data.get('used_keys', [])

        if data.get('activation_record'):

            status.activation_record = ActivationRecord.from_dict(
                data['activation_record']
            )

        return status



# ==================== 核心算法 ====================
class ActivationCore:
    """激活核心算法"""

    def __init__(self, master_secret: bytes, charset: str = None):
        self.master_secret = master_secret
        self.charset = charset or self._default_charset()

    @staticmethod
    def _default_charset():
        """默认字符集（去易混淆字符）"""
        letters = ''.join(c for c in string.ascii_uppercase if c not in 'IO')
        digits = ''.join(c for c in string.digits if c not in '01')
        return letters + digits

    def generate_key(self) -> str:
        """生成激活码"""
        # 生成随机部分
        random_part = ''.join(secrets.choice(self.charset) for _ in range(12))

        # 计算校验和
        checksum = self._calc_checksum(random_part)
        full_key = random_part + checksum

        # 格式化
        return '-'.join(full_key[i:i+4] for i in range(0, 16, 4))

    def _calc_checksum(self, data: str) -> str:
        """计算4位校验和"""
        hash_bytes = hashlib.sha256(data.encode()).digest()
        hash_int = int.from_bytes(hash_bytes[:4], byteorder='big')

        checksum = ''
        for _ in range(4):
            hash_int, idx = divmod(hash_int, len(self.charset))
            checksum = self.charset[idx] + checksum
        return checksum

    def validate_format(self, key: str) -> Tuple[bool, str]:
        """验证激活码格式"""
        # 清理输入
        clean = key.replace('-', '').replace(' ', '').upper()

        # 检查长度
        if len(clean) != 16:
            return False, "长度应为16位字符"

        # 检查字符
        invalid = set(clean) - set(self.charset)
        if invalid:
            return False, f"无效字符: {''.join(invalid)}"

        # 检查校验和
        data_part = clean[:12]
        checksum_part = clean[12:]
        expected = self._calc_checksum(data_part)

        if not secrets.compare_digest(checksum_part, expected):
            return False, "校验和错误"

        return True, "格式正确"

    def normalize_key(self, key: str) -> str:
        """标准化激活码格式"""
        clean = re.sub(r'[^A-Z0-9]', '', key.upper())
        if len(clean) == 16:
            return '-'.join(clean[i:i+4] for i in range(0, 16, 4))
        return key.upper()