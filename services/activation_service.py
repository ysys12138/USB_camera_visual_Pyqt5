"""
激活服务 - 协调层
调用core处理业务，提供简洁接口
"""

import sys
from pathlib import Path


from app_config import ACTIVATION_STATE_FILE, MASTER_SECRET, ENABLE_ACTIVATION


from core.activation import ActivationCore, ActivationStatus, ActivationRecord
from datetime import datetime


class ActivationService:
    """激活服务"""

    def __init__(self):
        self.enabled = ENABLE_ACTIVATION
        self.core = ActivationCore(MASTER_SECRET)
        self.status = ActivationStatus()
        print(self.status)
        print(self.status.used_keys)

    # ========== 公开接口 ==========

    def check_activation(self) -> bool:
        """检查是否已激活"""
        print("1:"+str(self.status.load(ACTIVATION_STATE_FILE).is_activated))
        if not self.enabled:
            return True
        return self.status.load(ACTIVATION_STATE_FILE).is_activated

    def activate(self, key: str):
        """激活软件"""
        if not self.enabled:
            return True, "激活功能已禁用"

        # 验证格式
        valid, msg = self.core.validate_format(key)
        if not valid:
            return False, f"格式错误: {msg}"

        # 检查是否已使用
        if key in self.status.used_keys:
            return False, "该激活码已被使用"

        # 执行激活
        self.status.is_activated = True
        self.status.activation_record = ActivationRecord(key, datetime.now())
        self.status.used_keys.append(key)

        # 保存
        if self.status.save(ACTIVATION_STATE_FILE):
            return True, "激活成功"
        return False, "保存失败"

    def get_activation_info(self) -> dict:
        """获取激活信息"""
        if not self.check_activation():
            return {"activated": False}

        record = self.status.load(ACTIVATION_STATE_FILE).activation_record
        if record:
            return {
                "activated": True,
                "license_key": record.license_key,
                "activated_at": record.activated_at.strftime("%Y-%m-%d %H:%M")
            }
        return {"activated": True}

    def generate_key(self) -> str:
        """生成激活码"""
        if not self.enabled:
            return "DISABLED-XXXX-XXXX-XXXX"
        return self.core.generate_key()

    def reset(self) -> bool:
        """重置激活（测试用）"""
        self.status = ActivationStatus()
        if ACTIVATION_STATE_FILE.exists():
            try:
                ACTIVATION_STATE_FILE.unlink()
                return True
            except:
                pass
        return False