"""
程序主入口 - 修复版
确保激活成功后能正确跳转到主窗口
"""

import sys
import os
from pathlib import Path

print("🔍 当前工作目录:", os.getcwd())
print("📦 Python 路径 (sys.path):")
for p in sys.path:
    print(f"  {p}")

# 检查 app_config.py 是否存在
config_path = Path(__file__).parent / "app_config.py"
print("📄 app_config.py 存在吗？", config_path.exists(), f"({config_path})")

# 尝试导入
try:
    import app_config

    print("✅ 成功导入 config，__file__ =", getattr(app_config, '__file__', 'unknown'))
except Exception as e:
    print("❌ 导入失败:", type(e).__name__, str(e))

if getattr(sys, 'frozen', False):
    # 打包后：exe 所在目录就是“项目根”
    ROOT_DIR = Path(sys.executable).parent
else:
    # 开发模式：main.py 的上级目录是项目根
    ROOT_DIR = Path(__file__).resolve().parent

# 将项目根目录加入 Python 路径
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
import app_config

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from services.activation_service import ActivationService
from windows.activation_window import ActivationWindow
from windows.main_window import MainWindow


class AppController:
    """应用程序控制器（单例模式）"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.app = QApplication(sys.argv)
            self.service = ActivationService()
            self.current_window = None
            self.initialized = True

    def start(self):
        """启动应用程序"""
        print("启动 USB摄像头工具...")

        # 检查激活状态并显示对应窗口
        self.show_appropriate_window()

        # 运行应用
        return self.app.exec_()

    def show_appropriate_window(self):
        """根据激活状态显示对应窗口"""
        if self.service.check_activation():
            # 已激活，直接显示主窗口
            info = self.service.get_activation_info()
            print(info)
            activation_key = info.get('license_key', '未知')
            self.show_main_window(activation_key)
        else:
            # 未激活，显示激活窗口
            self.show_activation_window()

    def show_activation_window(self):
        """显示激活窗口"""
        # 如果当前有窗口，先关闭
        if self.current_window:
            self.current_window.close()

        self.activation_window = ActivationWindow()
        self.activation_window.activation_success.connect(self.on_activation_success)
        self.activation_window.show()
        self.current_window = self.activation_window

    def show_main_window(self, activation_key: str = ""):
        """显示主窗口"""
        # 如果当前有窗口，先关闭
        if self.current_window:
            self.current_window.close()

        self.main_window = MainWindow(activation_key)
        self.main_window.show()
        self.current_window = self.main_window

    def on_activation_success(self, activation_key: str):
        """激活成功回调"""
        print(f"激活成功，跳转到主窗口...")

        # 使用QTimer延迟显示主窗口，确保事件循环正常
        QTimer.singleShot(100, lambda: self.show_main_window(activation_key))


# main.py


def main():
    """主函数"""
    # 创建应用控制器
    controller = AppController()

    # 启动应用
    sys.exit(controller.start())


if __name__ == "__main__":
    main()
