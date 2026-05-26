"""
病人列表组件
"""
import os
import time

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QListWidget, QListWidgetItem,
    QFrame, QScrollArea, QGroupBox, QFormLayout, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from app_config import get_config
from utils.path_utils import get_records_dir


class PatientListWidget(QWidget):
    """病人列表组件"""

    patient_selected = pyqtSignal(dict)  # 选中病人时发出信号
    edit_patient_requested = pyqtSignal(dict)  # 请求编辑病人信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_records = []  # 所有记录缓存
        self.char_records = []
        self.setup_ui()
        self.load_recent_patients()

    def setup_ui(self):
        """设置界面"""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 标题
        title = QLabel("病人列表")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        # 搜索区域
        search_group = QGroupBox("搜索")
        search_layout = QFormLayout()
        search_layout.setSpacing(8)

        # 病人姓名搜索
        self.name_search_input = QLineEdit()
        self.name_search_input.setPlaceholderText("输入病人姓名...")
        search_layout.addRow("病人姓名:", self.name_search_input)

        # 医生搜索
        self.doctor_search_input = QLineEdit()
        self.doctor_search_input.setPlaceholderText("输入医生姓名...")
        search_layout.addRow("检查医生:", self.doctor_search_input)

        search_group.setLayout(search_layout)
        layout.addWidget(search_group)

        # 搜索按钮
        search_btn_layout = QHBoxLayout()

        self.search_btn = QPushButton("搜索")
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 6px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.search_btn.clicked.connect(self.search_patients)
        search_btn_layout.addWidget(self.search_btn)

        self.clear_btn = QPushButton("清空")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 6px 15px;
                border-radius: 4px;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_search)
        search_btn_layout.addWidget(self.clear_btn)

        search_btn_layout.addStretch()
        layout.addLayout(search_btn_layout)

        # 列表标题
        list_header = QLabel("最近病人")
        list_header.setStyleSheet("color: #7f8c8d; font-weight: bold; margin-top: 10px;")
        layout.addWidget(list_header)

        # ============ 新增：当前病人信息 ============
        self.current_patient_group = QGroupBox("当前病人")
        current_patient_layout = QVBoxLayout()

        self.current_patient_label = QLabel("未选择病人")
        self.current_patient_label.setStyleSheet("""
            QLabel {
                color: #0;
                padding: 5px;
                font-size: 15px;
                min-height: 20px;
            }
        """)
        self.current_patient_label.setWordWrap(True)
        current_patient_layout.addWidget(self.current_patient_label)

        # 修改病人按钮（初始禁用）
        self.edit_btn = QPushButton("修改病人信息")
        self.edit_btn.setEnabled(False)
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
            QPushButton:hover:!disabled {
                background-color: #2980b9;
            }
        """)
        self.edit_btn.clicked.connect(self.on_edit_patient)
        current_patient_layout.addWidget(self.edit_btn)

        self.current_patient_group.setLayout(current_patient_layout)
        layout.addWidget(self.current_patient_group)

        # 病人列表
        self.patient_list = QListWidget()
        self.patient_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QListWidget::item:hover {
            }
        """)
        self.patient_list.itemClicked.connect(self.on_patient_selected)
        layout.addWidget(self.patient_list, 1)  # 1表示占满剩余空间

        # 底部按钮
        bottom_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.refresh_btn.clicked.connect(self.clear_search)
        bottom_layout.addWidget(self.refresh_btn)

        self.new_record_btn = QPushButton("新建")
        self.new_record_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        bottom_layout.addWidget(self.new_record_btn)
        #清理病人信息
        self.clean_btn = QPushButton("一键清理")
        self.clean_btn.setStyleSheet("""
            QPushButton {
                background-color: #000000;
                color: white;
                padding: 8px 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.clean_btn.clicked.connect(self.clean_data)
        #bottom_layout.addWidget(self.clean_btn)


        #删除病人
        self.delete_record_btn = QPushButton("删除病人")
        self.delete_record_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        current_patient_layout.addWidget(self.delete_record_btn)
        self.delete_record_btn.clicked.connect(self.delete_patient)
        bottom_layout.addStretch()
        layout.addLayout(bottom_layout)

    def update_current_patient(self, record):
        """更新当前病人显示"""
        if not record:
            self.current_patient_label.setText("未选择病人")
            self.edit_btn.setEnabled(False)
            return

        patient = record['patient_info']
        exam = record['exam_info']

        # 格式化显示信息
        info_text = f"{patient['name']}\t性别：{patient['gender']} \t年龄： {patient['age']}岁\t申请医师:{patient['appdoc']}\t检查单号：{exam['exam_code']}"
        print(21)
        info_text += f"\t检查日期: {exam['date']}\t"
        print(22)
        info_text += f"检查仪器: {exam['equip_name']}\t"
        if exam.get('doctor'):
            info_text += f" 检查者: {exam['doctor']}"
        print(23)
        self.current_patient_label.setText(info_text)
        self.edit_btn.setEnabled(True)

        # 保存当前选中的记录，供编辑时使用
        self.current_record = record

    def delete_old_files(self,folder_path, days):
        """
        删除 folder_path 中修改时间早于 days 天前的所有文件。
        """
        now = time.time()
        cutoff = now - (days *86400)  # 86400 秒 = 1 天

        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                file_mtime = os.path.getmtime(file_path)
                if file_mtime < cutoff:
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")


    def load_all_records(self):
        """加载所有记录"""
        self.all_records = []
        records_dir = get_records_dir()

        if not records_dir.exists():
            return

        for json_file in records_dir.glob("REC*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    record = json.load(f)
                    # 确保有所有必需的字段
                    if all(key in record for key in ['patient_info', 'exam_info', 'record_id']):
                        record['file_path'] = str(json_file)
                        self.all_records.append(record)

            except:
                continue


        # 按创建时间倒序排序
        self.all_records.sort(key=lambda x: x.get('created_at', ''), reverse=False)
        #print(self.all_records)
        self.char_records=self.all_records[-5:]
        #print(self.char_records)

    #添加到缓存的记录
    def add_to_char(self, record):
        self.all_records.append(record)
        self.char_records=self.all_records[-5:]
    def remove_from_char(self, record, vg):
        if vg:#更新时使用模糊删除
            for r in self.all_records:
                if r["record_id"]==record['record_id']:
                    self.all_records.remove(r)
        else:
            self.all_records.remove(record)
        self.char_records=self.all_records[-5:]

    def clean_data(self):
        reply = QMessageBox.warning(None, "Warning",
                                    "确定要清理病人信息吗？此操作会永久从磁盘删除病人信息！无法撤回！删除天数："+str(get_config('clean_day',30)),
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            records_dir = get_records_dir()
            days = get_config('clean_day', 30)
            self.delete_old_files(records_dir,days)
            self.load_all_records()
            self.load_recent_patients()


    def load_recent_patients(self, count=5):
        """加载最近病人（默认5个）"""
        if self.char_records==[]:
            self.load_all_records()
        self.display_patients(self.char_records[:5][::-1])


    def display_patients(self, records: List[Dict]):
        """显示病人列表"""
        self.patient_list.clear()

        for record in records:
            patient = record['patient_info']
            exam = record['exam_info']

            # 创建列表项文本
            item_text = f"{patient['name']} ({patient['gender']}, {patient['age']}岁)\n"
            item_text += f"检查单号: {exam['exam_code']} - 日期：{exam['date']}\n"
            item_text += f"检查者: {exam['doctor'] if exam['doctor'] else '未指定'}"

            # 创建列表项
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, record)  # 存储完整记录数据
            self.patient_list.addItem(item)

    def search_patients(self):
        """搜索病人"""
        name_keyword = self.name_search_input.text().strip().lower()
        doctor_keyword = self.doctor_search_input.text().strip().lower()

        if not name_keyword and not doctor_keyword:
            self.load_recent_patients()
            return

        filtered_records = []
        for record in self.all_records:
            patient = record['patient_info']
            exam = record['exam_info']

            # 匹配病人姓名
            name_match = name_keyword in patient.get('name', '').lower()

            # 匹配医生姓名
            doctor_match = doctor_keyword in exam.get('doctor', '').lower()

            # 根据搜索条件筛选
            if name_keyword and doctor_keyword:
                # 两个条件都要满足
                if name_match and doctor_match:
                    filtered_records.append(record)
            elif name_keyword:
                # 只按姓名搜索
                if name_match:
                    filtered_records.append(record)
            elif doctor_keyword:
                # 只按医生搜索
                if doctor_match:
                    filtered_records.append(record)

        self.display_patients(filtered_records)

    def clear_search(self):
        """清空搜索"""
        self.name_search_input.clear()
        self.doctor_search_input.clear()
        self.load_recent_patients()

    def on_edit_patient(self):
        """编辑当前病人"""
        if hasattr(self, 'current_record') and self.current_record:
            # 发射编辑信号，包含完整记录数据
            self.edit_patient_requested.emit(self.current_record)
            self.update_current_patient(None)

    def on_patient_selected(self, item):
        """病人被选中"""
        record = item.data(Qt.UserRole)
        if record:
            self.update_current_patient(record)
            self.patient_selected.emit(record)

    def delete_patient(self):

        records_dir = get_records_dir()
        if hasattr(self, 'current_record') and self.current_record:
            self.update_current_patient(None)

            record_id = self.current_record['record_id']+".json"
            record_dir = records_dir.joinpath(record_id)
            reply = QMessageBox.warning(None, "Warning", "确定要删除病人"+self.current_record['patient_info']['name']+"吗？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                os.remove(record_dir)
                self.remove_from_char(self.current_record,False)
                self.load_recent_patients()


