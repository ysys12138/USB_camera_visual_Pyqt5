"""
主窗口
"""
from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog, QPrinterInfo
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel,
    QPushButton, QHBoxLayout, QGroupBox, QFrame, QTextEdit, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, QDate, QRect, QUrl
from PyQt5.QtGui import QFont, QPainter, QPixmap, QDesktopServices, QTextOption, QFontMetrics, QColor
from pathlib import Path
import sys

import app_config
from windows.patient_list import PatientListWidget
from windows.camera import CameraWidget
from windows.template_dialog import TemplateDialog

from services.activation_service import ActivationService
from app_config import get_config

from windows.config_window import ConfigWindow
import windows.signals as signals
from windows.screenshot_gallery import ScreenshotGallery
from utils.path_utils import get_utils_dir

# ====== 防息屏功能 ======

from ctypes import windll, WINFUNCTYPE, c_uint

# Windows API: SetThreadExecutionState
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

# 加载 API 函数
try:
    SetThreadExecutionState = WINFUNCTYPE(c_uint, c_uint)(("SetThreadExecutionState", windll.kernel32))
except Exception as e:
    print(f"❌ 无法加载 SetThreadExecutionState: {e}")
    SetThreadExecutionState = None


class MainWindow(QMainWindow):
    """主窗口（激活后显示）"""

    def __init__(self, activation_key: str = None):
        super().__init__()
        self.activation_key = activation_key
        self.camera_preview_box = CameraWidget()
        self.gallery = ScreenshotGallery()
        self.left_layout = None
        self.setup_ui()
        self.current_mode = "normal"
        self.current_patient_record = None
        self.fullscreen_window = None
        self.set_keep_awake(True)

        signals.screenshot_signals.take_screenshot.connect(self.take_screenshot)

    def set_keep_awake(self, active=True):
        """
        保持系统清醒
        :param active: True = 启用防息屏；False = 恢复默认
        """
        if not SetThreadExecutionState:
            return

        try:
            if active:
                # 请求：系统和显示器保持开启
                SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)
                print("✅ 已启用防息屏")
            else:
                # 恢复默认行为
                SetThreadExecutionState(ES_CONTINUOUS)
                print("💤 已关闭防息屏")
        except Exception as e:
            print("防息屏设置失败:", e)

    def setup_ui(self):
        """设置界面"""
        self.setWindowTitle("医学影像工作站")
        self.setGeometry(100, 100, 1200, 700)  # 增大窗口
        self.setMinimumSize(get_config('window_width', 1000), get_config('window_height', 700))

        # 主垂直布局（上中下结构）
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # ============ 顶部：标题 ============
        title = QLabel("医学影像工作站")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; padding: 10px 0;")
        # main_layout.addWidget(title)

        # ============ 中部：左右布局 ============
        middle_widget = QWidget()
        middle_layout = QHBoxLayout(middle_widget)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(20)

        # ----- 左侧：激活信息 -----
        left_widget = QWidget()
        self.left_layout = QVBoxLayout(left_widget)
        self.left_layout.setContentsMargins(0, 0, 0, 0)

        if self.activation_key:
            info_box = QGroupBox("软件信息")
            info_layout = QVBoxLayout()

            info_label = QLabel(
                f"✅ 软件已激活\n"
                f"激活码: {self.activation_key}\n\n"
                f"版本: 1.0.0\n"
                f"状态: 正常运行"
            )
            info_label.setStyleSheet("""
                color: #27ae60; 
                padding: 15px;
                font-size: 14px;
                line-height: 1.5;
            """)
            info_label.setAlignment(Qt.AlignLeft)
            info_layout.addWidget(info_label)

            info_box.setLayout(info_layout)
            # self.left_layout.addWidget(info_box)

        # 摄像头预览区域（占左侧剩余空间）

        self.left_layout.addWidget(self.camera_preview_box, 1)  # 占满剩余空间
        self.left_layout.addWidget(self.gallery, 3)

        middle_layout.addWidget(left_widget, 2)  # 左侧占2/5

        # ----- 右侧：病人列表 -----
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        self.patient_list = PatientListWidget()
        self.patient_list.patient_selected.connect(self.on_patient_selected)
        self.patient_list.new_record_btn.clicked.connect(self.open_record_window)
        self.patient_list.edit_patient_requested.connect(self.edit_patient_record)
        right_layout.addWidget(self.patient_list, 1)  # 占满空间

        middle_layout.addWidget(right_widget, 3)  # 右侧占3/5

        main_layout.addWidget(middle_widget, 1)  # 中部占满空间

        # ============ 底部：功能按钮栏 ============
        bottom_widget = QWidget()
        bottom_widget.setFixedHeight(80)  # 固定高度
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(20, 10, 20, 10)
        bottom_layout.setSpacing(20)

        # 左侧功能组
        left_btn_group = QWidget()
        left_btn_layout = QHBoxLayout(left_btn_group)
        left_btn_layout.setContentsMargins(0, 0, 0, 0)
        left_btn_layout.setSpacing(15)

        self.fullscreen_btn = QPushButton("大屏模式")
        self.fullscreen_btn.setFixedSize(120, 40)
        self.fullscreen_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        self.fullscreen_btn.clicked.connect(lambda: self.set_display_mode("fullscreen"))
        left_btn_layout.addWidget(self.fullscreen_btn)

        left_btn_layout.addStretch()
        bottom_layout.addWidget(left_btn_group, 1)  # 左侧按钮组占2/3

        # 报告side组
        # ====== 侧边模块：报告编辑区 (Side Panel) ======
        side_panel = QWidget()
        side_layout = QVBoxLayout(side_panel)
        side_layout.setContentsMargins(10, 10, 10, 10)
        side_layout.setSpacing(10)

        btn_open_template = QPushButton("📝 选择模板")
        btn_open_template.clicked.connect(self.open_template_dialog)
        side_layout.addWidget(btn_open_template)

        # 标题
        title_label = QLabel("📝 报告编辑")
        title_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 14px;")
        side_layout.addWidget(title_label)

        # 文本编辑框（支持多行）
        self.report_edit = QTextEdit()
        self.report_edit.setPlaceholderText("从模板加载内容，或手动输入报告...")
        self.report_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 6px;
                padding: 8px;
                background-color: #f9f9f9;
                font: 14px;
            }
        """)
        side_layout.addWidget(self.report_edit, stretch=1)

        # 生成报告按钮
        self.generate_report_btn = QPushButton("📄 生成报告")
        self.generate_report_btn.setFixedHeight(40)
        self.generate_report_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        # 可连接后续逻辑（如导出PDF、打印等）
        self.generate_report_btn.clicked.connect(self.preview_report)

        side_layout.addWidget(self.generate_report_btn)

        middle_layout.addWidget(side_panel, 2)

        # 右侧功能组
        right_btn_group = QWidget()
        right_btn_layout = QHBoxLayout(right_btn_group)
        right_btn_layout.setContentsMargins(0, 0, 0, 0)
        right_btn_layout.setSpacing(15)

        # 报告功能按钮
        # self.new_report_btn = QPushButton("新建报告")
        # self.new_report_btn.setFixedSize(100, 40)
        # self.new_report_btn.setStyleSheet("""
        #     QPushButton {
        #         background-color: #e67e22;
        #         color: white;
        #         border-radius: 6px;
        #     }
        #     QPushButton:hover {
        #         background-color: #d35400;
        #     }
        # """)
        # right_btn_layout.addWidget(self.new_report_btn)

        # self.load_template_btn = QPushButton("加载模板")
        # self.load_template_btn.setFixedSize(100, 40)
        # self.load_template_btn.setStyleSheet("""
        #     QPushButton {
        #         background-color: #95a5a6;
        #         color: white;
        #         border-radius: 6px;
        #     }
        #     QPushButton:hover {
        #         background-color: #7f8c8d;
        #     }
        # """)
        # right_btn_layout.addWidget(self.load_template_btn)

        # 配置按钮
        self.config_btn = QPushButton("⚙️ 参数设置")
        self.config_btn.setFixedSize(100, 40)
        self.config_btn.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                color: white;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #2c3e50;
            }
        """)
        self.config_btn.clicked.connect(self.open_config_window)
        right_btn_layout.addWidget(self.config_btn)

        right_btn_layout.addStretch()
        bottom_layout.addWidget(right_btn_group, 1)  # 右侧按钮组占1/3

        main_layout.addWidget(bottom_widget)

        # 设置中心部件
        self.central = QWidget()
        self.central.setLayout(main_layout)
        self.setCentralWidget(self.central)
        self.showMaximized()

    # 模版
    def open_template_dialog(self):

        dialog = TemplateDialog(self)

        # 连接信号：接收选中的模板内容
        dialog.template_selected.connect(self.on_template_applied)

        dialog.exec_()

    def on_template_applied(self, content: str):
        """将选中的模板内容填入侧边报告编辑框"""
        self.report_edit.setPlainText(content)
        self.statusBar().showMessage("✅ 已加载模板内容到报告", 3000)

    # -------------切换大屏---------
    def set_display_mode(self, mode: str):
        """大屏显示"""

        self.hide()
        self.fullscreen_window = FullScreenWindow(
            camera_widget=self.camera_preview_box,
            sc_g=self.gallery,
            return_callback=self.return_normal,

        )
        self.fullscreen_window.show()

    def return_normal(self):

        self.left_layout.addWidget(self.camera_preview_box)
        self.left_layout.addWidget(self.gallery)
        self.showMaximized()
        self.activateWindow()

    def open_config_window(self):
        """打开配置窗口"""
        self.config_window = ConfigWindow(self)
        self.config_window.show()

    def open_record_window(self):
        """打开病历记录窗口"""
        from windows.record_window import RecordWindow
        self.record_window = RecordWindow(self)
        self.record_window.setPlist(self.patient_list)
        self.record_window.show()

    def on_patient_selected(self, record):
        """处理选中的病人"""
        patient = record['patient_info']
        exam = record['exam_info']

        # 显示选中信息（可以自定义显示方式）
        info_text = f"病人: {patient['name']}\n"
        info_text += f"检查单号：{exam['exam_code']}"
        info_text += f"检查时间: {exam['date']}"

        # 显示在状态栏或单独的标签上
        self.statusBar().showMessage(info_text)
        self.current_patient_record = record

    def edit_patient_record(self, record):
        """编辑病人记录"""
        from windows.record_window import RecordWindow

        # 创建编辑窗口，传入记录数据
        self.record_window = RecordWindow(self)
        self.record_window.setPlist(self.patient_list)
        self.record_window.load_record(record)  # 需要给RecordWindow添加load_record方法
        self.record_window.show()

    def take_screenshot(self, text):
        self.statusBar().showMessage(text)

    def preview_report(self):
        """打开打印预览对话框，支持 A4/A3 纸张设置与导出 PDF"""
        if not self.current_patient_record:
            QMessageBox.warning(self, "提示", "请先选择一位病人。")
            return

        record = self.current_patient_record
        patient = record['patient_info']
        exam = record['exam_info']
        name = patient.get('name', '未知')
        gender = patient.get('gender', '未指定')
        age = patient.get('age', '未知')
        exam_date = exam.get('date', '未知')
        exam_id = exam.get('exam_code', '未知')
        doctor = exam.get('doctor', '未知')
        app_doc = patient.get('appdoc', '未知')
        lnumber = patient.get('lnumber', '')
        mnumber = patient.get('mnumber', '')
        bnumber = patient.get('bnumber', '')
        equip_name = exam.get('equip_name', "")
        apartment = patient.get('apartment', "")
        report_text = self.report_edit.toPlainText().strip()

        if not report_text:
            QMessageBox.warning(self, "提示", "报告内容为空，请填写后再生成。")
            return

        image_paths = self.gallery.selected_thumbnail_path
        max_image = 6
        if not image_paths:
            QMessageBox.warning(self, "提示", "请先从缩略图中选择一张图像用于报告。")
            return
        if len(image_paths) > max_image:
            QMessageBox.warning(self, "提示", f"最多只能选择{max_image}张图片。")
            return

        # === 创建 QPrinter 并设置默认参数 ===
        printer = QPrinter(QPrinter.HighResolution)
        # printer.setResolution(300)  # 必须加！
        printer.setPageSize(QPrinter.A4)
        printer.setPageMargins(15, 20, 15, 20, QPrinter.Millimeter)
        printer.setColorMode(QPrinter.Color)
        printer.setCopyCount(1)
        printer.setCollateCopies(True)

        # === 创建预览对话框 ===
        preview = QPrintPreviewDialog(printer, self)
        preview.setWindowFlags(Qt.Window)  # 使用标准窗口样式
        preview.resize(1200, 800)  # 设置合理初始大小
        preview.setWindowTitle("打印预览")
        print("Paint engine:", printer.paintEngine().type())

        # === 连接绘图信号 ===
        def draw_preview(printer):
            painter = QPainter()
            if not painter.begin(printer):
                QMessageBox.critical(self, "错误", "无法启动打印引擎。")
                return

            # 复用你原有的绘制逻辑（精简封装）
            self._draw_report_content(
                painter=painter,
                printer=printer,
                name=name,
                gender=gender,
                age=age,
                exam_date=exam_date,
                exam_id=exam_id,
                doctor=doctor,
                lnumber=lnumber,
                mnumber=mnumber,
                bnumber=bnumber,
                equip_name=equip_name,
                app_doc=app_doc,
                report_text=report_text,
                image_paths=image_paths,
                apartment=apartment
            )
            painter.end()

        preview.paintRequested.connect(draw_preview)
        preview.exec_()  # 使用 exec_() 阻塞式显示

    def _draw_report_content(self, painter, printer, **data):
        """实际绘制报告内容（供 preview 和 future export 复用）"""
        pen = painter.pen()
        pen.setWidth(10)

        # --- 提取数据 ---
        name = data['name']
        gender = data['gender']
        age = data['age']
        exam_date = data['exam_date']
        exam_id = data['exam_id']
        doctor = data['doctor']
        app_doc = data['app_doc']
        lnumber = data['lnumber']
        mnumber = data['mnumber']
        bnumber = data['bnumber']
        equip_name = data['equip_name']
        report_text = data['report_text']
        image_paths = data['image_paths']
        apartment = data['apartment']

        # --- 字体设置 ---
        title_font = QFont("SimSun", 16, QFont.Bold)
        report_title_font = QFont("SimSun", 14, QFont.Bold)
        normal_font = QFont("SimSun", 11)
        small_font = QFont("SimSun", 9)
        body_font = QFont("SimSun", 10)

        # --- 获取页面宽度 ---
        rect_f = printer.pageRect()
        x = int(rect_f.x())
        y = int(rect_f.y())
        w = int(rect_f.width())
        h = int(rect_f.height())
        page_rect = QRect(x, y, w, h)
        painter.setWindow(page_rect)

        # 安全设置边距
        left_margin = 400
        right_margin = 400
        top_margin = 200
        bottom_margin = 50
        step = 130

        usable_width = page_rect.width()
        usable_height = page_rect.height() - top_margin - bottom_margin

        # logo图片
        logo_path = get_utils_dir() / "logo.jpeg"
        logo_pixmap = QPixmap(str(logo_path))
        print(str(logo_path))
        if not logo_pixmap.isNull():
            # 设置显示尺寸
            logo_width = 800
            logo_height = 800

            # 可选：缩放图片
            scaled_logo = logo_pixmap.scaled(
                logo_width,
                logo_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            # 指定绘制位置（例如：右上角）
            logo_x = left_margin + 500
            logo_y = top_margin  # 距顶部 10pt

            painter.drawPixmap(QRect(logo_x, logo_y, scaled_logo.width(), scaled_logo.height()), scaled_logo)
        # --- 医院标题 ---
        hospital_name = get_config('hospital_name', '某某医院')
        fm = QFontMetrics(title_font, painter.device())  # 绑定 device 更准确
        text_width = fm.horizontalAdvance(hospital_name)

        # 居中公式
        center_x = left_margin + (usable_width - text_width) / 2
        y = top_margin + fm.height()

        painter.setFont(title_font)
        painter.setPen(QColor("#2980b9"))
        painter.drawText(int(center_x), int(y), hospital_name)
        y += step

        # --- 报告标题 ---
        txt = get_config('report_title_txt', '医学影像报告')
        fm2 = QFontMetrics(report_title_font, painter.device())
        text_width2 = fm2.horizontalAdvance(txt)
        center_x = left_margin + (usable_width - text_width2) / 2
        painter.setFont(report_title_font)
        painter.setPen(Qt.black)
        painter.drawText(center_x, y, txt)
        y += step

        # --- 检查单号 ---
        painter.setFont(normal_font)
        painter.drawText(usable_width - right_margin * 2, y, f"检查号：{exam_id}")
        y += step

        # --- 分隔线 ---
        painter.setPen(pen)
        painter.drawLine(left_margin, y, usable_width + right_margin, y)
        y += step

        # --- 病人信息 ---
        painter.setFont(normal_font)
        painter.setPen(Qt.black)

        def draw_line(text):
            nonlocal y
            painter.drawText(left_margin, int(y), text)
            y += step

        def draw_lines(texts):
            nonlocal y
            x = 0
            for text in texts:
                painter.drawText(left_margin + x, int(y), text)
                x += 1000
            y += step

        draw_lines([f"姓名：{name}", f"性别：{gender}", f"年龄：{age}", f"住院号:{lnumber}"])
        draw_lines([f"门诊号：{mnumber}",f"病床号：{bnumber}", f"科室：{apartment}",f"申请医师：{app_doc}"])
        draw_lines([f"检查日期：{exam_date}",        f"检查设备：{equip_name}"])

        # --- 图像区域 ---
        img_y_start = y
        img_max_width = usable_width // 3  # 每张图最大宽度（三列）
        img_max_height = 750
        spacing = 25

        i = 0
        for img_path in image_paths:
            pixmap = QPixmap(str(img_path))
            if pixmap.isNull():
                continue

            scaled_pixmap = pixmap.scaled(
                1000, 750,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            col = i % 3
            row = i // 3

            img_x = left_margin + col * (img_max_width + spacing)
            img_y = img_y_start + row * (img_max_height + spacing)

            rect = QRect(img_x, img_y, scaled_pixmap.width(), scaled_pixmap.height())
            painter.drawPixmap(rect, scaled_pixmap)

            i += 1

        # 更新 y 到图片区底部
        if i > 0:
            rows = (i + 2) // 3  # 向上取整
            y = img_y_start + rows * (img_max_height + spacing)+20
        else:
            y = img_y_start + 20

        # === 报告正文 ===
        body_font = QFont("SimSun", 12)
        painter.setFont(body_font)
        metrics = QFontMetrics(body_font, painter.device())
        line_height = metrics.lineSpacing()

        text_option = QTextOption()
        text_option.setWrapMode(QTextOption.WordWrap)
        text_option.setAlignment(Qt.AlignTop)

        text_block_width = usable_width
        text_block_height = usable_height - bottom_margin

        text_rect = QRect(left_margin, int(y), text_block_width, text_block_height)
        painter.drawText(text_rect, Qt.TextWrapAnywhere, report_text)

        y = usable_height + step*4

        # --- 医师签名 ---
        signature_line = f"报告医师：{doctor}"
        painter.drawText(usable_width - right_margin * 2, y, signature_line)
        y += step
        painter.drawText(usable_width - right_margin * 2, y, "医师签字：")
        y += step
        # --- 底部分隔线 ---
        pen = painter.pen()
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawLine(left_margin, y, usable_width + right_margin, y)
        y += step

        # --- 免责声明 ---
        small_font = QFont("SimSun", 11)
        painter.setFont(small_font)
        disclaimer = "注：此报告仅做临床参考，不做任何证明。"
        painter.drawText(left_margin, y, disclaimer)
        y += step


class FullScreenWindow(QWidget):
    def __init__(self, camera_widget, sc_g, return_callback):
        super().__init__()
        self.camera_widget = camera_widget
        self.sc_g = sc_g
        self.setup_fullscreen_ui()
        self.return_callback = return_callback

    def setup_fullscreen_ui(self):
        # 设置大屏模式界面
        self.setWindowTitle("大屏模式")
        self.setStyleSheet("background: black;")

        # 主布局：上下结构
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ========================
        # 上半部分：左右布局（视频 + 缩略图）
        # ========================
        upper_widget = QWidget()
        upper_layout = QHBoxLayout(upper_widget)
        upper_layout.setContentsMargins(0, 0, 0, 0)
        upper_layout.setSpacing(2)

        # --- 左侧：摄像头画面 ---
        video_container = QWidget()
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)
        video_layout.addWidget(self.camera_widget)  # 确保 camera_widget 已正确转移
        video_container.setStyleSheet("background-color: #000; border-radius: 8px;")

        # --- 右侧：截图缩略图面板 ---
        thumbnail_container = QFrame()
        thumbnail_layout = QVBoxLayout(thumbnail_container)
        thumbnail_layout.setContentsMargins(0, 0, 0, 0)
        thumbnail_layout.addWidget(self.sc_g)

        thumbnail_container.setStyleSheet("""
            background-color: white;
            border-radius: 12px;
            border: 1px solid #ccc;
        """)

        # 添加到左右布局（比例 6 : 4）
        upper_layout.addWidget(video_container, 5)
        upper_layout.addWidget(thumbnail_container, 2)

        # ========================
        # 下半部分：控制栏（固定区域）
        # ========================
        control_bar = self.create_control_bar()
        control_bar.setFixedHeight(70)  # 固定高度
        control_bar.setStyleSheet("background-color: rgba(30, 30, 30, 220); padding: 5px;")

        # ========================
        # 组合进主布局
        # ========================
        main_layout.addWidget(upper_widget, 10)  # 上半部分占 5 份
        main_layout.addWidget(control_bar, 1)  # 控制栏占 1 份

        # 全屏显示
        self.showFullScreen()

    def create_control_bar(self):
        bar = QWidget()
        bar.setFixedHeight(30)
        bar.setStyleSheet("background-color: rgba(0, 100, 100, 200);")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()

        btn_exit = QPushButton("🔚 退出大屏")
        btn_exit.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        btn_exit.setFixedSize(120, 30)
        btn_exit.clicked.connect(self.exit_fullscreen)
        layout.addWidget(btn_exit)

        return bar

    def exit_fullscreen(self):
        """退出大屏并触发回调，让主窗口回收控件"""
        # 1. 从当前布局中移除（准备交还）
        parent_layout = self.camera_widget.parent().layout()
        if parent_layout:
            parent_layout.removeWidget(self.camera_widget)

        # 2. 关闭自己
        self.close()
        if self.return_callback:
            self.return_callback()
