"""
状态文件加密
使用 cryptography 库
"""

import base64
import json
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class StateEncryptor:
    """状态加密器"""

    def __init__(self, key_base64: str):
        """
        初始化

        Args:
            key_base64: base64编码的密钥
        """
        # 从base64解码密钥
        key = base64.b64decode(key_base64)

        # 使用PBKDF2派生固定格式的密钥
        salt = b'usb_camera_tool_salt'  # 固定salt（简单场景够用）
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        # 生成Fernet需要的密钥
        self.key = base64.urlsafe_b64encode(kdf.derive(key))
        self.cipher = Fernet(self.key)

    def encrypt_data(self, data: dict) -> str:
        """加密数据"""
        json_str = json.dumps(data, ensure_ascii=False)
        encrypted = self.cipher.encrypt(json_str.encode())
        return encrypted.decode('utf-8')

    def decrypt_data(self, encrypted_str: str) -> dict:
        """解密数据"""
        try:
            decrypted = self.cipher.decrypt(encrypted_str.encode())
            return json.loads(decrypted.decode('utf-8'))
        except Exception:
            # 解密失败返回空字典
            return {}

    def save_encrypted(self, data: dict, filepath: Path) -> bool:
        """保存加密数据到文件"""
        try:
            encrypted = self.encrypt_data(data)
            filepath.parent.mkdir(exist_ok=True)
            filepath.write_text(encrypted, encoding='utf-8')
            return True
        except Exception as e:
            print(f"[加密保存失败] {e}")
            return False

    def load_encrypted(self, filepath: Path) -> dict:
        """从文件加载并解密"""
        if not filepath.exists():
            return {}

        try:
            encrypted = filepath.read_text(encoding='utf-8')
            return self.decrypt_data(encrypted)
        except Exception as e:
            print(f"[解密加载失败] {e}")
            return {}