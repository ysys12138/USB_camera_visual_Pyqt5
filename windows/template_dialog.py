from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QListWidget, QTextEdit, QPushButton,
    QLabel, QFileDialog, QMessageBox, QWidget
)
from PyQt5.QtCore import pyqtSignal
import os
import shutil
from utils.path_utils import get_templates_dir

TEMPLATE_DIR = get_templates_dir()

class TemplateDialog(QDialog):
    # 自定义信号：用户确认选择了某个模板内容
    template_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择或编辑模板")
        self.resize(800, 600)

        # 确保 templates 目录存在
        os.makedirs(TEMPLATE_DIR, exist_ok=True)

        self.current_file = None  # 当前选中的模板文件路径
        self.setup_ui()
        self.template_char = []
        self.load_templates()




    def setup_ui(self):
        main_layout = QHBoxLayout(self)  # 左右布局

        # ==== 左侧面板：模板列表 + 控制按钮 ====
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        list_label = QLabel("📄 模板列表")
        list_label.setStyleSheet("font-weight: bold; padding: 5px;")
        left_layout.addWidget(list_label)

        self.template_list = QListWidget()
        self.template_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 6px;
            }
            QListWidget::item {
                padding: 8px;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        self.template_list.itemClicked.connect(self.on_template_selected)
        left_layout.addWidget(self.template_list)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("新增")
        edit_btn = QPushButton("保存修改")
        delete_btn = QPushButton("删除")

        add_btn.clicked.connect(self.add_template)
        edit_btn.clicked.connect(self.edit_current_template)
        delete_btn.clicked.connect(self.delete_template)

        btn_layout.addWidget(add_btn)

        btn_layout.addWidget(delete_btn)
        left_layout.addLayout(btn_layout)

        # ==== 右侧：内容预览与编辑 ====
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("选中一个模板查看或编辑内容...\n新增时可输入新内容。")

        # ==== 底部按钮栏 ====
        bottom_bar = QVBoxLayout()
        confirm_btn = QPushButton("✅ 确认选择")
        cancel_btn = QPushButton("❌ 取消")

        confirm_btn.clicked.connect(self.confirm_selection)
        cancel_btn.clicked.connect(self.reject)  # 关闭对话框

        bottom_bar.addStretch()
        bottom_bar.addWidget(edit_btn)
        bottom_bar.addWidget(confirm_btn)
        bottom_bar.addWidget(cancel_btn)

        # ==== 组合主布局 ====
        main_layout.addWidget(left_widget, 1)
        main_layout.addWidget(self.content_edit, 3)

        # 添加到底部
        main_layout.addLayout(bottom_bar,1)

    def load_templates(self):
        """加载 templates/ 下的所有 .txt 文件作为模板"""
        self.template_list.clear()
        files = [f for f in os.listdir(TEMPLATE_DIR) if f.endswith('.txt')]
        for filename in files:
            self.template_list.addItem(filename[:-4])
            self.template_char.append(filename[:-4])

    def load_temp(self):
        self.template_list.clear()
        for filename in self.template_char:
            self.template_list.addItem(filename)


    def on_template_selected(self, item):
        """点击模板项：加载其内容到编辑区"""
        filename = item.text()+".txt"
        file_path = os.path.join(TEMPLATE_DIR, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.content_edit.setPlainText(content)
            self.current_file = file_path
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法读取模板：{e}")

    def add_template(self):
        """新增模板"""
        name, ok = QFileDialog.getSaveFileName(
            self,
            "保存新模板",
            os.path.join(TEMPLATE_DIR, "新模板.txt"),
            "文本文件 (*.txt)"
        )
        if not ok or not name:
            return

        if not name.endswith(".txt"):
            name += ".txt"

        # 写空文件
        try:
            with open(name, 'w', encoding='utf-8') as f:
                f.write("")
            self.current_file = name
            self.content_edit.setPlainText("")
            self.template_char.append(os.path.basename(name[:-4]))
            self.load_temp()
            # 自动选中新模板（找到最后一项）
            self.template_list.setCurrentRow(0)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法创建模板：{e}")

    def edit_current_template(self):
        """保存当前内容到选中的模板"""
        if not self.current_file:
            QMessageBox.warning(self, "提示", "请先选择一个模板进行编辑。")
            return

        content = self.content_edit.toPlainText()
        name = os.path.basename(self.current_file)[:-4]
        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(content)
            QMessageBox.information(self, "成功", "模板已保存！")
            self.template_char.remove(name)
            self.template_char.append(name)
            self.load_temp()  # 刷新排序
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败：{e}")

    def delete_template(self):
        """删除当前模板"""
        if not self.current_file:
            QMessageBox.warning(self, "提示", "请先选择一个模板。")
            return

        filename = os.path.basename(self.current_file)
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除模板 '{filename}' 吗？\n此操作不可恢复！"
        )
        if reply == QMessageBox.Yes:
            try:
                os.remove(self.current_file)
                self.current_file = None
                self.content_edit.clear()
                self.template_char.remove(filename[:-4])
                self.load_temp()
            except Exception as e:
                QMessageBox.critical(self, "删除失败", str(e))

    def confirm_selection(self):
        """确认选择：emit 内容并关闭"""
        content = self.content_edit.toPlainText().strip()
        if not content:
            reply = QMessageBox.question(
                self, "空内容",
                "当前模板内容为空，是否仍选择？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        self.template_selected.emit(content)  # ✅ 发送信号
        self.accept()  # 关闭对话框，返回 exec_() = 1

    def get_selected_content(self):
        """供外部调用获取结果（配合 exec_ 使用）"""
        if self.exec_() == QDialog.Accepted:
            return self.content_edit.toPlainText()
        return None
