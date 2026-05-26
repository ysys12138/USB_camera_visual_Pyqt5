import json
import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel,
    QGridLayout, QFrame, QPushButton, QTextEdit, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QDesktopServices, QPainter, QColor, QFont
from pathlib import Path
import windows.signals as signals
from app_config import get_config
from utils.path_utils import get_data_dir

history_file = str(get_data_dir()/"history.json")
class ScreenshotGallery(QWidget):
    """
    简洁双列缩略图展示面板：每行两张，点击打开原图
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.screenshot_dir = Path(get_config('screenshot_dir', ''))
        self.max_preview = 2  # 最多显示20张
        self.max_p_number = get_config('max_p_number', 20)
        self.setup_ui()
        self.char_thumb = []
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.global_note_history = [str(item) for item in data if item]
                    else:
                        self.global_note_history = []
            except Exception as e:
                print(f"⚠️ 加载备注历史失败: {e}")
                self.global_note_history = [" "]
        else:
            self.global_note_history = [" "]
        self.image_notes = {}  # {img_path: "备注内容"}
        self.all_note_combos = []
        self.selected_thumbnail_path = []
        self.load_thumbnails()



        signals.screenshot_signals.sc_refresh.connect(self.add_to_char)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("采集的图像")
        title.setStyleSheet("font-weight: bold; color: red; padding: 5px 0;")
        layout.addWidget(title)

        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea { border: none; }
            QScrollBar:vertical {
                width: 8px;
                background: #f0f0f0;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #bbb;
                border-radius: 4px;
            }
        """)

        # 内容容器（使用网格布局）
        self.content_widget = QWidget()
        self.grid_layout = QGridLayout(self.content_widget)
        self.grid_layout.setContentsMargins(4, 4, 4, 4)
        self.grid_layout.setSpacing(6)  # 项之间留白

        scroll_area.setWidget(self.content_widget)
        layout.addWidget(scroll_area)

        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setFixedHeight(25)
        refresh_btn.clicked.connect(self.refresh)
        refresh_btn.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                background-color: #ecf0f1;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #bdc3c7;
            }
        """)
        layout.addWidget(refresh_btn)

    def load_thumbnails(self):
        """加载最近的截图，每行两个"""
        self.clear_thumbnails()

        if not self.screenshot_dir.exists():
            return
        png_files = sorted(
            self.screenshot_dir.glob("*.png"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        if not png_files:
            return

        row, col = 0, 0
        for img_path in png_files[:self.max_p_number]:
            thumb = self.create_thumbnail(img_path)
            self.grid_layout.addWidget(thumb, row, col)
            self.char_thumb.append(thumb)

            col += 1
            if col > 2:  # 每行最多两个
                col = 0
                row += 1

    def create_thumbnail(self, img_path):
        """创建单个缩略图控件 + 备注输入框"""
        # 主容器：垂直布局（图片 + 备注）
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # --- 缩略图框架 ---
        frame = QFrame()
        frame.setFixedSize(160, 120)  # 保持宽高比（约 4:3），为下方留空间
        self.update_frame_style(frame, selected=img_path in self.selected_thumbnail_path)

        img_layout = QVBoxLayout(frame)
        img_layout.setContentsMargins(2, 2, 2, 2)

        label = QLabel()
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("background: #fafafa; border-radius: 6px;")

        pixmap = QPixmap(str(img_path))
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                140, 100,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            label.setPixmap(scaled)
        else:
            label.setText("❌")
        img_layout.addWidget(label)

        # 添加图像到主布局
        layout.addWidget(frame)

        # --- 备注输入框 ---
        note_combo = QComboBox()
        note_combo.setEditable(True)
        note_combo.setInsertPolicy(QComboBox.NoInsert)  # 我们手动控制插入
        note_combo.setMaxCount(20)
        note_combo.setFont(QFont("SimSun", 9))
        note_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 4px;
                background-color: #f9f9f9;
                font-size: 12px;
            }
            QComboBox:focus {
                border: 1px solid #3498db;
                background-color: white;
            }
        """)

        # === 加载当前全局历史到该 combo ===
        def refresh_combo_items():
            current_text = note_combo.currentText()  # 保留当前显示文本
            note_combo.clear()
            for item in self.global_note_history:
                note_combo.addItem(item)
            # 尽量恢复当前值（如果已被清空）
            if current_text and current_text not in self.global_note_history:
                # 可选：临时加入当前编辑内容为第一项？或者不加也行
                pass
            # 如果当前文本是有效选择项，尝试设回去
            index = note_combo.findText(current_text)
            if index >= 0:
                note_combo.setCurrentIndex(index)
            else:
                note_combo.setEditText(current_text)

        # 初始加载全局历史
        refresh_combo_items()

        # 记录这个 combo 到全局列表（用于后续广播刷新）
        self.all_note_combos.append(note_combo)

        # === 恢复当前图片的备注 ===
        if hasattr(self, 'image_notes') and img_path in self.image_notes:
            note_combo.setCurrentText(self.image_notes[img_path])

        # === 回车处理函数（核心）===
        def on_return_pressed():
            current_text = note_combo.currentText().strip()
            if not current_text:
                return

            # 1. 更新当前图片的备注
            self.image_notes[img_path] = current_text

            # 2. 更新全局历史（去重 + 插入顶部）
            if current_text in self.global_note_history:
                self.global_note_history.remove(current_text)
            self.global_note_history.append(current_text)
            self.global_note_history = self.global_note_history[:35]  # 限制长度

            # 3. 【关键】广播刷新：让所有已存在的 note_combo 都更新下拉列表
            for cb in self.all_note_combos:
                if cb != note_combo:  # 排除自己（也可以包含，统一处理）
                    #cb.blockSignals(True)  # 防止触发信号风暴
                    prev_text = cb.currentText()
                    cb.clear()
                    for item in self.global_note_history:
                        cb.addItem(item)
                    # # 尝试保持原来输入的内容（如果是手动输入的）
                    if prev_text:
                        idx = cb.findText(prev_text)
                        if idx >= 0:
                            cb.setCurrentIndex(idx)
                        else:
                            cb.setEditText(prev_text)
                    #cb.blockSignals(False)

            # 自己也要刷新吗？不需要，因为 history 已经变了，但 combo 的 items 不影响当前使用
            # 只有下次打开下拉框时才需要新数据 —— 所以下面这句不是必须，但我们为了视觉一致也可刷新
            refresh_combo_items()  # 确保自己也完全同步（尤其防止被 clear 后丢失）
            try:
                with open(history_file, 'w', encoding='utf-8') as f:
                    json.dump(self.global_note_history, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"⚠️ 保存备注历史失败: {e}")

        # 绑定事件
        note_combo.lineEdit().returnPressed.connect(on_return_pressed)

        # 可选：点击已有项也保存到当前图片
        def on_activated(index):
            text = note_combo.itemText(index).strip()
            if text:
                self.image_notes[img_path] = text

        note_combo.activated.connect(on_activated)

        # === 绑定点击事件：切换选中状态 ===
        def on_click():
            if img_path in self.selected_thumbnail_path:
                # 已选中 → 取消
                self.selected_thumbnail_path.remove(img_path)
            else:
                # 未选中 → 添加
                self.selected_thumbnail_path.append(img_path)

            # 更新样式
            self.update_frame_style(frame, selected=img_path in self.selected_thumbnail_path)
            print(f"✅ 当前选中图片: {len(self.selected_thumbnail_path)} 张")

        # 将事件绑定到整个容器区域
        container.mousePressEvent = lambda e: on_click()
        frame.mousePressEvent = lambda e: on_click()  # 优先响应
        label.mousePressEvent = lambda e: on_click()
        layout.addWidget(note_combo)
        return container  # 返回完整组件



    def update_frame_style(self, frame, selected):
        """动态设置缩略图边框样式"""
        if selected:
            frame.setStyleSheet("""
                QFrame {
                    background-color: red;
                    border: 2px solid #3498db;
                    border-radius: 8px;
                    border-color:red;
                }
            """)
        else:
            frame.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                }
                QFrame:hover {
                    border: 1px solid red;
                }
            """)

    def clear_thumbnails(self):
        """清除所有缩略图"""
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def add_to_char(self, pathstr):
        self.max_p_number = get_config('max_p_number', 20)
        if len(self.char_thumb) >= self.max_p_number:
            self.grid_layout.removeWidget(self.char_thumb.pop(0))
        self.char_thumb.append(self.create_thumbnail(pathstr))
        self.refresh()

    def refresh(self):
        """手动刷新缩略图列表"""
        if not self.char_thumb:
            self.load_thumbnails()
        else:
            row, col = 0, 0
            for thumb in self.char_thumb:
                self.grid_layout.addWidget(thumb, row, col)
                col += 1
                if col > 2:  # 每行最多两个
                    col = 0
                    row += 1

