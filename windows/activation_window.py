"""
激活窗口
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox,
    QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


from services.activation_service import ActivationService
from app_config import (ACTIVATION_WINDOW_WIDTH,
                        ACTIVATION_WINDOW_HEIGHT)


class ActivationWindow(QMainWindow):
    """激活窗口"""

    activation_success = pyqtSignal(str)  # 激活成功信号

    def __init__(self):
        super().__init__()
        self.service = ActivationService()
        self.setup_ui()
        self.update_display()

    def setup_ui(self):
        """设置界面"""
        self.setWindowTitle("软件激活")
        self.setFixedSize(ACTIVATION_WINDOW_WIDTH, ACTIVATION_WINDOW_HEIGHT)

        # 中心部件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        # 标题
        title = QLabel("软件激活")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)

        # 说明
        desc = QLabel("请输入激活码完成软件激活")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(desc)

        # 输入框
        input_layout = QVBoxLayout()
        input_label = QLabel("激活码:")
        input_label.setStyleSheet("font-weight: bold;")
        input_layout.addWidget(input_label)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("例如: X7B9-2K4F-H8J3-M5N1")
        self.key_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        input_layout.addWidget(self.key_input)
        layout.addLayout(input_layout)

        # 按钮
        btn_layout = QHBoxLayout()

        self.activate_btn = QPushButton("激活")
        self.activate_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 25px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.activate_btn.clicked.connect(self.on_activate)
        btn_layout.addWidget(self.activate_btn)

        # 测试按钮（开发用）
        self.test_btn = QPushButton("测试码")
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
            }
        """)
        self.test_btn.clicked.connect(self.generate_test_key)
        #btn_layout.addWidget(self.test_btn)

        layout.addLayout(btn_layout)

        # 状态显示
        status_label = QLabel("状态信息:")
        status_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(status_label)

        self.status_display = QTextEdit()
        self.status_display.setReadOnly(True)
        self.status_display.setMaximumHeight(80)
        self.status_display.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ecf0f1;
                border-radius: 4px;
                padding: 8px;
                background-color: #f8f9fa;
            }
        """)
        layout.addWidget(self.status_display)

    def update_display(self):
        """更新显示"""
        activated = self.service.check_activation()

        if activated:
            info = self.service.get_activation_info()
            if info.get('activated'):
                self.status_display.setText(
                    f"✅ 软件已激活\n"
                    f"激活码: {info.get('license_key', '未知')}\n"
                    f"激活时间: {info.get('activated_at', '未知')}"
                )
                self.key_input.setEnabled(False)
                self.activate_btn.setEnabled(False)
                self.activate_btn.setText("已激活")
        else:
            self.status_display.setText("❌ 软件未激活\n请输入激活码完成激活")

    def on_activate(self):
        """激活按钮点击"""
        key = self.key_input.text().strip()

        if not key:
            QMessageBox.warning(self, "提示", "请输入激活码")
            return

        # 调用服务激活
        success, message = self.service.activate(key)

        if success:
            QMessageBox.information(self, "成功", message)
            self.update_display()
            # 发送成功信号，主程序会处理窗口切换
            self.activation_success.emit(key)
        else:
            QMessageBox.critical(self, "失败", message)

    def generate_test_key(self):
        """生成测试激活码"""
        test_key = self.service.generate_key()
        self.key_input.setText(test_key)
        current_text = self.status_display.toPlainText()
        self.status_display.setText(f"{current_text}\n\n测试码: {test_key}")