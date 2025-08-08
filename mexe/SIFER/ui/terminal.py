from PyQt5.QtWidgets import QMainWindow, QTextEdit
from PyQt5.QtCore import Qt
import datetime

class TerminalWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("S.I.F.E.R Terminal")
        self.setGeometry(100, 100, 800, 600)
        
        self.text_area = QTextEdit(self)
        self.text_area.setReadOnly(True)
        self.setCentralWidget(self.text_area)
        
    def log_message(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.text_area.append(f"[{timestamp}] {message}")