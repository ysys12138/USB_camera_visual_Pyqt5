from datetime import datetime
import os
import sys
from pathlib import Path

import cv2
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, Qt

from app_config import get_config
from windows.signals import screenshot_signals


class CameraThread(QThread):
    frame_ready = pyqtSignal(QImage)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.cap = None
        self.running = False
        self.device_index = 0
        self.width = 640
        self.height = 480

    def run(self):
        retry_delay = 200  # ms
        max_retries = 10

        for attempt in range(max_retries):
            try:
                self.cap = cv2.VideoCapture(self.device_index, cv2.CAP_DSHOW)  # Windows专用更稳定
            except Exception as e:
                msg = f"创建摄像头失败: {e}"
                print(msg)
                self.error_occurred.emit(msg)
                break

            if not self.cap.isOpened():
                print(f"摄像头打开失败，尝试第 {attempt + 1} 次...")
                self.msleep(retry_delay)
                continue

            # 设置参数（减少带宽）
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, 15)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 最小缓冲区

            self.running = True
            while self.running:
                if not self.cap.isOpened():
                    break

                ret, frame = self.cap.read()
                if ret:
                    rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb_image.shape
                    bytes_per_line = ch * w
                    qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                    self.frame_ready.emit(qt_image)
                    self.msleep(30)  # 控制帧率，防止过载
                else:
                    print("读取帧失败，尝试重启...")
                    break

            self.cleanup()
            if not self.running:
                break

        if not self.running:
            return

        self.error_occurred.emit("无法连接到摄像头，请检查设备是否插入。")

    def cleanup(self):
        """安全释放摄像头"""
        if self.cap is not None:
            try:
                self.cap.release()
                self.cap = None
            except Exception as e:
                print("释放摄像头异常:", e)

    def stop(self):
        self.running = False
        self.wait(1000)  # 等待最多1秒
        self.cleanup()


class CameraWidget(QWidget):
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):  # 防止重复初始化
        if self._initialized:
            print("already")
            return
        super().__init__()
        self.setWindowTitle("USB摄像头视频显示（热插拔优化版）")
        self.setGeometry(100, 100, 800, 600)

        # UI组件
        self.video_label = QLabel("等待摄像头启动...")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black; color: white; font-size: 16px;")
        self.video_label.setMinimumSize(240, 180)

        self.start_button = QPushButton("开启摄像头")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #999999;
                color: white;
                border-radius: 6px;
                font-size:15px;
                padding: 10px 10px
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        self.screenshot_button = QPushButton("采集图像")
        self.screenshot_button.setStyleSheet("""
            QPushButton {
                background-color: #444444;
                color: white;
                border-radius: 6px;
                font-size:15px;
                padding: 10px 10px
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        self.screenshot_button.setEnabled(False)

        # 布局
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.start_button)
        btn_layout.addWidget(self.screenshot_button)

        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        # 成员变量
        self.thread = None
        self.current_pixmap = None

        # 信号连接
        self.start_button.clicked.connect(self.start_camera)
        self.screenshot_button.clicked.connect(self.take_screenshot)

        # 定时检测摄像头是否可用（用于热插拔检测）
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_camera_health)
        self.timer.start(2000)  # 每2秒检查一次

        # 初始启动
        self.start_camera()

    def start_camera(self):
        if self.thread and self.thread.isRunning():
            self.show_message("摄像头正在运行中，请勿重复开启。")
            return

        self.start_button.setEnabled(False)
        self.video_label.setText("正在启动摄像头...")

        self.thread = CameraThread()
        self.thread.frame_ready.connect(self.update_frame)
        self.thread.error_occurred.connect(self.handle_error)
        self.thread.finished.connect(self.on_thread_finished)
        self.thread.start()

        self.screenshot_button.setEnabled(True)

    def update_frame(self, image):
        try:
            # 转为 pixmap 并复制一份（避免共享内存）
            pixmap = QPixmap.fromImage(image).copy()  # .copy() 很重要
            if pixmap.isNull():
                return

            self.current_pixmap = pixmap

            scaled_pixmap = self.current_pixmap.scaled(
                self.video_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.video_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print("更新帧失败:", e)

    def handle_error(self, message):
        self.video_label.setText(f"错误：{message}")
        self.show_message(message, error=True)

    def on_thread_finished(self):
        self.start_button.setEnabled(True)

    def check_camera_health(self):
        """简单健康检查（可扩展为实际设备存在性检测）"""
        pass  # 当前依赖线程内部逻辑自动重试

    def take_screenshot(self):
        """自动保存截图到本地 screenshots/ 目录，无需弹窗"""
        self.screenshot_button.setEnabled(False)  # 防重复点击

        try:
            # 检查是否有可用图像
            if not hasattr(self, 'current_pixmap') or self.current_pixmap is None:
                print("没有可截图的画面")
                return

            pixmap = self.current_pixmap.copy()
            if pixmap.isNull():
                print("pixmap 无效")
                return

            # 创建保存目录
            dir = get_config('screenshot_dir', '')

            # 生成文件名：screenshot_20250405_123015.png
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = dir + f"/screenshot_{timestamp}.png"

            # 保存
            success = pixmap.save(filename, "PNG")
            if success:
                print(f"✅ 截图已保存：{filename}")
                screenshot_signals.take_screenshot.emit(f"✅ 截图已保存：{filename}")
                screenshot_signals.sc_refresh.emit(filename)
                # 可选：显示一个短暂提示（非模态）
                self.video_label.setText(f"已保存截图\n{os.path.basename(filename)}")
                # 2秒后恢复显示画面
                QTimer.singleShot(2000, self.restore_video_display)
            else:
                screenshot_signals.take_screenshot.emit(f"截图保存失败！")
                print("❌ 保存失败")

        except Exception as e:
            import traceback
            print("【截图异常】", traceback.format_exc())

        finally:
            self.screenshot_button.setEnabled(True)

    def restore_video_display(self):
        """恢复视频显示（清除文字提示）"""
        if self.current_pixmap and not self.current_pixmap.isNull():
            scaled = self.current_pixmap.scaled(
                self.video_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.video_label.setPixmap(scaled)

    def show_message(self, text, error=True):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("提示" if not error else "错误")
        msg_box.setText(text)
        msg_box.setStyleSheet(

            """
            background-color: #FFFFFF;
            color: #27ae60; 
            padding: 15px;
            font-size: 14px;
            line-height: 1.5;
            """
        )
        msg_box.setIcon(QMessageBox.Warning if error else QMessageBox.Information)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

    def closeEvent(self, event):
        if self.thread and self.thread.isRunning():
            self.thread.stop()
        event.accept()
