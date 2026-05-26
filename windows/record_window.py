"""
病历记录窗口
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox,
    QComboBox, QFormLayout, QGroupBox, QTextEdit,
    QDateEdit, QSpinBox
)
from PyQt5.QtCore import Qt, QDate, QSettings
from PyQt5.QtGui import QFont
import json
from pathlib import Path
from datetime import datetime
from utils.path_utils import get_records_dir
from app_config import get_config


class RecordWindow(QMainWindow):
    """病历记录窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setPlist(self, patient_list):
        self.patient_list = patient_list

    def setup_ui(self):
        """设置界面"""
        self.setWindowTitle("登记病人")
        self.setMinimumSize(1000, 800)

        # 中心部件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        title = QLabel("登记病人")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)

        # 基本信息组
        basic_group = QGroupBox("病人信息")
        basic_layout = QFormLayout()
        basic_layout.setSpacing(10)

        # 病人类型
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["门诊", "急诊", "住院", "体检"])

        # 患者姓名（必填）
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("请输入患者姓名")
        self.patient_number_input = QLineEdit()
        row_layout0 = QHBoxLayout()
        row_layout0.addWidget(QLabel("病人类别*："))
        row_layout0.addWidget(self.gender_combo)
        row_layout0.addWidget(QLabel("病人编号"))
        row_layout0.addWidget(self.patient_number_input)
        row_layout0.addWidget(QLabel("姓名*："))
        row_layout0.addWidget(self.name_input)


        basic_layout.addRow(row_layout0)

        # 患者性别（必填）
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["男", "女"])

        # 患者年龄（必填）
        self.age_input = QSpinBox()
        self.age_input.setRange(0, 150)
        self.age_input.setValue(30)
        row_layout2 = QHBoxLayout()
        row_layout2.addWidget(QLabel("性别*："))
        row_layout2.addWidget(self.gender_combo)
        row_layout2.addWidget(QLabel("年龄*："))
        row_layout2.addWidget(self.age_input)
        row_layout2.addStretch()

        basic_layout.addRow(row_layout2)
        # 出生日期
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        #basic_layout.addRow("出生日期:", self.date_input)

        # 创建一个水平布局来容纳三个字段
        row_layout = QHBoxLayout()
        self.mnumber_input = QLineEdit()
        self.lnumber_input = QLineEdit()
        self.bnumber_input = QLineEdit()

        row_layout.addWidget(QLabel("门诊号:"))
        row_layout.addWidget(self.mnumber_input)

        row_layout.addWidget(QLabel("住院号:"))
        row_layout.addWidget(self.lnumber_input)

        row_layout.addWidget(QLabel("床位:"))
        row_layout.addWidget(self.bnumber_input)


        basic_layout.addRow(row_layout)

        self.apartment_combo = QComboBox()
        self.doc_combo = QComboBox()
        self.apartment_combo.addItems([
            "妇科", "其他"
        ])
        self.doc_combo.addItems([
            "张三", "李四"
        ])

        self.doc_combo.setEditable(True)  # 允许用户输入
        self.doc_combo.setInsertPolicy(QComboBox.InsertAtTop)  # 新项目插入到顶部（可选）
        self.load_app_doctors()
        self.doc_combo.setDuplicatesEnabled(False)  # 防止重复（但我们自己控制）

        # 连接信号：当输入内容改变或回车时触发
        self.doc_combo.editTextChanged.connect(self.on_doctor_name_edited)

        row_layout3 = QHBoxLayout()
        row_layout3.addWidget(QLabel("科室："))

        row_layout3.addWidget(self.apartment_combo)
        row_layout3.addWidget(QLabel("申请医师："))


        row_layout3.addWidget(self.doc_combo)
        row_layout3.addStretch()
        basic_layout.addRow(row_layout3)


        # 临床诊断
        self.analyze_input = QLineEdit()
        basic_layout.addRow("临床诊断:", self.analyze_input)

        self.phone_input = QLineEdit()
        self.addr_input = QLineEdit()
        row_layout2 = QHBoxLayout()
        row_layout2.addWidget(QLabel("电话"))
        row_layout2.addWidget(self.phone_input)
        row_layout2.addWidget(QLabel("地址"))
        row_layout2.addWidget(self.addr_input)

        basic_layout.addRow(row_layout2)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # 检查信息组
        exam_group = QGroupBox("检查信息")
        exam_layout = QFormLayout()
        exam_layout.setSpacing(10)

        # 检查类型
        self.equip_type_combo = QComboBox()
        self.equip_type_combo.addItems([
            "GI", "其他"
        ])
        exam_layout.addRow("设备类型:", self.equip_type_combo)

        # 检查项目（必填）
        self.equip_input = QComboBox()
        self.equip_input.addItems([
            "GI1", "其他"
        ])
        exam_layout.addRow("设备名称*:", self.equip_input)

        # 检查日期
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        exam_layout.addRow("检查日期:", self.date_input)
        # 检查号(必填
        self.examcode_input = QLineEdit()
        exam_layout.addRow("检查号*:", self.examcode_input)

        # 创建可编辑的下拉框
        self.doctor_input = QComboBox()
        self.doctor_input.setEditable(True)  # 允许用户输入
        self.doctor_input.setInsertPolicy(QComboBox.InsertAtTop)  # 新项目插入到顶部（可选）
        self.load_doctors()
        self.doctor_input.setDuplicatesEnabled(False)  # 防止重复（但我们自己控制）

        # 连接信号：当输入内容改变或回车时触发
        self.doctor_input.editTextChanged.connect(self.on_doctor_name_edited)

        # 添加到布局
        exam_layout.addRow("检查者:", self.doctor_input)

        exam_group.setLayout(exam_layout)
        layout.addWidget(exam_group)

        # 备注信息
        note_group = QGroupBox("备注")
        note_layout = QVBoxLayout()

        self.note_input = QTextEdit()
        self.note_input.setPlaceholderText("可在此输入其他备注信息...")
        self.note_input.setMaximumHeight(100)
        note_layout.addWidget(self.note_input)

        note_group.setLayout(note_layout)
        layout.addWidget(note_group)

        # 按钮区域
        btn_layout = QHBoxLayout()

        # 保存按钮
        self.save_btn = QPushButton("保存记录")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 25px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.save_btn.clicked.connect(self.save_record)
        btn_layout.addWidget(self.save_btn)

        # 清空按钮
        self.clear_btn = QPushButton("清空")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                padding: 10px 25px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        # self.clear_btn.clicked.connect(self.clear_form)
        # btn_layout.addWidget(self.clear_btn)

        # 取消按钮
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.cancel_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 状态提示
        self.status_label = QLabel("* 为必填项")
        self.status_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        layout.addWidget(self.status_label)

    def save_doctors(self):
        settings = QSettings("MyHospital", "MyApp")
        doctors = []
        for i in range(self.doctor_input.count()):
            doctors.append(self.doctor_input.itemText(i))
        settings.setValue("saved_doctors", doctors)

    def load_doctors(self):
        settings = QSettings("MyHospital", "MyApp")
        doctors = settings.value("saved_doctors", [])
        if doctors:
            self.doctor_input.clear()
            self.doctor_input.addItems(doctors)

    def load_app_doctors(self):
        settings = QSettings("MyHospital", "MyApp")
        doctors = settings.value("saved_doctors", [])
        if doctors:
            self.doc_combo.clear()
            self.doc_combo.addItems(doctors)

    def on_doctor_name_edited(self, text):
        """
        当用户编辑了医生姓名时，将有效的新名字添加到下拉列表中
        """
        text = text.strip()
        if not text:
            return

        # 检查是否已存在该项
        index = self.doctor_input.findText(text, Qt.MatchExactly)
        if index == -1:
            # 如果不存在，添加到下拉框
            self.doctor_input.addItem(text)
            # 可选：移动到顶部显示更明显
            self.doctor_input.model().sort(0)  # 按字母排序（可选）
        self.save_doctors()

    def validate_form(self):
        """验证表单"""
        errors = []

        # 检查必填项
        if not self.name_input.text().strip():
            errors.append("患者姓名不能为空")

        if not self.equip_input.currentText():
            errors.append("设备名称不能为空")
        if not self.age_input.text().strip():
            errors.append("年龄不能为空")
        if not self.examcode_input.text().strip():
            errors.append("检查号不能为空")

        return errors

    def save_record(self):
        """保存记录（支持新建和更新）"""
        # 验证
        errors = self.validate_form()
        if errors:
            QMessageBox.warning(self, "验证失败", "\n".join(errors))
            return

        # 收集数据
        record_data = {
            "patient_info": {
                "name": self.name_input.text().strip(),
                "gender": self.gender_combo.currentText(),
                "age": self.age_input.value(),
                "mnumber": self.mnumber_input.text().strip(),
                "lnumber": self.lnumber_input.text().strip(),
                "bnumber": self.bnumber_input.text().strip(),
                "analyze": self.analyze_input.text().strip(),
                "phone": self.phone_input.text().strip(),
                "addr":self.addr_input.text().strip(),
                "appdoc":self.doc_combo.currentText(),
                "apartment":self.apartment_combo.currentText()
            },
            "exam_info": {
                "date": self.date_input.date().toString("yyyy-MM-dd"),
                "equip_type": self.equip_type_combo.currentText(),
                "equip_name": self.equip_input.currentText(),
                "doctor": self.doctor_input.currentText(),
                "exam_code": self.examcode_input.text().strip(),
            },
            "note": self.note_input.toPlainText().strip(),
            "created_at": datetime.now().isoformat(),
        }

        # 如果是编辑现有记录，使用原ID；否则生成新ID
        if hasattr(self, 'original_record_id') and self.original_record_id:
            record_data['record_id'] = self.original_record_id
            record_data['updated_at'] = datetime.now().isoformat()

        else:
            record_data['record_id'] = f"REC{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 保存到文件
        if self.save_to_file(record_data):
            action = "更新" if hasattr(self, 'original_record_id') and self.original_record_id else "保存"
            QMessageBox.information(self, "成功", f"记录已{action}\nID: {record_data['record_id']}")
            if action == "更新":
                self.patient_list.remove_from_char(record_data, True)
            self.patient_list.add_to_char(record_data)
            self.patient_list.load_recent_patients()
            # self.clear_form()
        else:
            QMessageBox.critical(self, "错误", f"失败")

    def save_to_file(self, data):
        """保存到JSON文件"""
        try:
            # 创建保存目录
            save_dir = get_records_dir()
            save_dir.mkdir(parents=True, exist_ok=True)

            # 生成文件名
            filename = save_dir / f"{data['record_id']}.json"

            # 保存JSON
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"[记录] 已保存: {filename}")
            return True

        except Exception as e:
            print(f"[记录] 保存失败: {e}")
            return False

    # def clear_form(self):
    #     """清空表单"""
    #     self.name_input.clear()
    #     self.gender_combo.setCurrentIndex(0)
    #     self.age_input.setValue(30)
    #     self.date_input.setDate(QDate.currentDate())
    #     self.exam_type_combo.setCurrentIndex(0)
    #     self.part_input.clear()
    #     self.doctor_input.clear()
    #     self.note_input.clear()
    #
    #     # 焦点回到第一个输入框
    #     self.name_input.setFocus()

    def load_record(self, record):
        """加载现有记录到表单"""
        patient = record['patient_info']
        exam = record['exam_info']

        # 填充表单
        self.name_input.setText(patient.get('name', ''))

        # 设置性别
        gender = patient.get('gender', '男')
        index = self.gender_combo.findText(gender)
        if index >= 0:
            self.gender_combo.setCurrentIndex(index)

        self.age_input.setValue(patient.get('age', 30))

        # 设置日期
        exam_date = exam.get('date', '')
        if exam_date:
            date = QDate.fromString(exam_date, "yyyy-MM-dd")
            if date.isValid():
                self.date_input.setDate(date)

        # 设置仪器类型
        equip_type = exam.get('equip_type', '')
        index = self.equip_type_combo.findText(equip_type)
        if index >= 0:
            self.equip_type_combo.setCurrentIndex(index)

        equip_name = exam.get('equip_name','')
        index = self.equip_input.findText(equip_name)
        if index>=0:
            self.equip_input.setCurrentIndex(index)

        app_doc = patient.get('appdoc', '')
        index = self.doc_combo.findText(app_doc)
        if index >= 0:
            self.doc_combo.setCurrentIndex(index)

        doc_name = exam.get('doctor', '')
        index = self.doctor_input.findText(doc_name)
        if index >= 0:
            self.doctor_input.setCurrentIndex(index)


        self.note_input.setText(record.get('note', ''))
        self.examcode_input.setText(exam.get('exam_code', ''))
        self.bnumber_input.setText(patient.get('bnumber', ''))
        self.lnumber_input.setText(patient.get('lnumber', ''))
        self.mnumber_input.setText(patient.get('mnumber', ''))
        self.analyze_input.setText(patient.get('analyze', ''))

        # 保存原始记录ID，用于更新时识别
        self.original_record_id = record.get('record_id', '')
        self.record_file_path = get_records_dir()

        # 修改窗口标题
        self.setWindowTitle(f"编辑病历 - {patient.get('name', '')}")
