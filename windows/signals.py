# signals.py
from PyQt5.QtCore import pyqtSignal, QObject


class ConfigSignals(QObject):
    config_updated = pyqtSignal()  # 当配置更新时发射


class screenshotSignals(QObject):
    take_screenshot = pyqtSignal(str)
    sc_refresh = pyqtSignal(str)


# 全局唯一实例
config_signals = ConfigSignals()
screenshot_signals = screenshotSignals()
