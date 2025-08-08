from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt
from utils.net_monitor import NetworkMonitor

class HUDOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(0, 0, 200, 100)
        
        self.layout = QVBoxLayout()
        self.network_label = QLabel("الشبكة: غير معروف")
        self.status_label = QLabel("الحالة: غير معروف")
        self.layout.addWidget(self.network_label)
        self.layout.addWidget(self.status_label)
        self.setLayout(self.layout)
        
        self.network_monitor = NetworkMonitor()
        self.network_monitor.status_changed.connect(self.update_status)
        
    def update_status(self, ssid, status):
        self.network_label.setText(f"الشبكة: {ssid}")
        self.status_label.setText(f"الحالة: {status}")
        if status == "encrypted":
            self.status_label.setStyleSheet("color: green")
        elif status == "connected":
            self.status_label.setStyleSheet("color: yellow")
        else:
            self.status_label.setStyleSheet("color: red")