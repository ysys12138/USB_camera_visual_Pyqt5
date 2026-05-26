"""
配置窗口 - 精简版
只包含你要求的几个配置项
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox,
    QSpinBox, QGroupBox, QFormLayout, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.config_manager import config_manager
import windows.signals as signals
from utils.path_utils import get_data_dir


class ConfigWindow(QMainWindow):
    """配置窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        """设置界面"""
        self.setWindowTitle("参数配置")
        self.setFixedSize(1000, 800)

        # 中心部件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        title = QLabel("参数配置")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        # 文件保存设置组
        file_group = QGroupBox("文件保存")
        file_layout = QFormLayout()
        file_layout.setSpacing(10)

        # 清除文件时间
        set_group = QGroupBox("其它设置")
        set_layout = QFormLayout()
        self.clean_time_input = QSpinBox()
        self.clean_time_input.setRange(30, 999999)
        set_layout.addRow("清理长时间未更新的病人信息（天）:", self.clean_time_input)
        self.max_p_number_input = QSpinBox()
        self.max_p_number_input.setRange(1, 50)
        set_layout.addRow("最多显示多少张照片:", self.max_p_number_input)
        # 医院名称
        self.hospital_name_input = QLineEdit()
        set_layout.addRow("医院名称：", self.hospital_name_input)
        self.report_title_txt = QLineEdit()
        set_layout.addRow("报告名称：", self.report_title_txt)
        set_group.setLayout(set_layout)
        layout.addWidget(set_group)

        # 截图目录
        screenshot_layout = QHBoxLayout()
        self.screenshot_dir_input = QLineEdit()
        screenshot_layout.addWidget(self.screenshot_dir_input)

        self.screenshot_btn = QPushButton("浏览...")
        self.screenshot_btn.clicked.connect(self.browse_screenshot_dir)
        screenshot_layout.addWidget(self.screenshot_btn)
        file_layout.addRow("截图目录:", screenshot_layout)

        # 报告目录
        report_layout = QHBoxLayout()
        self.report_dir_input = QLineEdit()
        report_layout.addWidget(self.report_dir_input)

        self.report_btn = QPushButton("浏览...")
        self.report_btn.clicked.connect(self.browse_report_dir)
        report_layout.addWidget(self.report_btn)
        file_layout.addRow("报告目录:", report_layout)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # 按钮区域
        btn_layout = QHBoxLayout()

        self.save_btn = QPushButton("保存")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.save_btn.clicked.connect(self.save_config)
        btn_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.cancel_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def load_config(self):
        """加载当前配置到界面"""
        config = config_manager.get_all()

        # 文件目录
        self.screenshot_dir_input.setText(config.get('screenshot_dir'))
        self.report_dir_input.setText(config.get('report_dir'))

        # 清理日期
        self.clean_time_input.setValue(config.get('clean_day'))
        self.max_p_number_input.setValue(config.get('max_p_number'))
        # 医院名称
        self.hospital_name_input.setText(config.get('hospital_name'))

        self.report_title_txt.setText(config.get('report_title_txt'))

    def browse_screenshot_dir(self):
        """浏览截图目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择截图保存目录",
            self.screenshot_dir_input.text()
        )
        if dir_path:
            self.screenshot_dir_input.setText(dir_path)

    def browse_report_dir(self):
        """浏览报告目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择报告保存目录",
            self.report_dir_input.text()
        )
        if dir_path:
            self.report_dir_input.setText(dir_path)

    def save_config(self):
        """保存配置"""
        # 收集界面上的值
        config_updates = {
            'screenshot_dir': self.screenshot_dir_input.text().strip(),
            'report_dir': self.report_dir_input.text().strip(),
            'clean_day': self.clean_time_input.value(),
            'max_p_number': self.max_p_number_input.value(),
            'hospital_name': self.hospital_name_input.text().strip(),
            'report_title_txt':self.report_title_txt.text().strip()
        }

        # 验证目录
        from pathlib import Path
        screenshot_dir = config_updates['screenshot_dir']
        report_dir = config_updates['report_dir']

        if screenshot_dir:
            try:
                Path(screenshot_dir).mkdir(exist_ok=True)
            except Exception as e:
                QMessageBox.warning(self, "警告", f"截图目录无效: {e}")
                return

        if report_dir:
            try:
                Path(report_dir).mkdir(exist_ok=True)
            except Exception as e:
                QMessageBox.warning(self, "警告", f"报告目录无效: {e}")
                return

        # 更新配置
        config_manager.update(**config_updates)

        # 保存到文件
        if config_manager.save():
            QMessageBox.information(self, "成功", "配置保存成功！")
            signals.config_signals.config_updated.emit()
            self.close()
        else:
            QMessageBox.critical(self, "错误", "配置保存失败")
