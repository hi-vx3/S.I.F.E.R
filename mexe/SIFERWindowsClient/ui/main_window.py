from PyQt5.QtWidgets import (QMainWindow, QTextEdit, QVBoxLayout, QHBoxLayout,
                             QGridLayout, QWidget, QLabel, QStatusBar, QProgressBar,
                             QTableWidget, QTableWidgetItem, QPushButton, QComboBox,
                             QFrame, QSplitter, QTabWidget, QMessageBox, QFileDialog,
                             QGroupBox, QScrollArea)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QPixmap, QPalette, QColor, QIcon, QMovie
from datetime import datetime
import logging
import psutil
import socket
import subprocess
import json
import os
import time

logging.basicConfig(filename="main_window.log", level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

class SystemMonitorThread(QThread):
    """خيط مراقبة النظام"""
    ram_updated = pyqtSignal(dict)
    network_updated = pyqtSignal(list)
    cpu_updated = pyqtSignal(float)
   
    def run(self):
        while True:
            try:
                # مراقبة الرامات
                memory = psutil.virtual_memory()
                ram_data = {
                    'percent': memory.percent,
                    'used': memory.used // (1024**3),  # GB
                    'total': memory.total // (1024**3),  # GB
                    'available': memory.available // (1024**3)  # GB
                }
                self.ram_updated.emit(ram_data)
               
                # مراقبة المعالج
                cpu_percent = psutil.cpu_percent(interval=1)
                self.cpu_updated.emit(cpu_percent)
               
                # مراقبة الشبكة
                connections = []
                try:
                    for conn in psutil.net_connections(kind='inet'):
                        if conn.status == 'ESTABLISHED':
                            local_addr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "N/A"
                            remote_addr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A"
                            connections.append({
                                'local': local_addr,
                                'remote': remote_addr,
                                'status': conn.status,
                                'pid': conn.pid or 'N/A'
                            })
                except:
                    pass
               
                self.network_updated.emit(connections)
                self.msleep(2000)  # تحديث كل ثانيتين
               
            except Exception as e:
                logging.error(f"خطأ في SystemMonitorThread: {str(e)}")
                self.msleep(5000)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            self.connection_status = False
            self.ram_history = []
            self.cpu_history = []
            self.log_messages = []
            self.ws_client = None
            self.last_ram_warning = 0  # وقت آخر تحذير للرامات
            self.last_cpu_warning = 0  # وقت آخر تحذير للمعالج
            self.setup_ui()
            self.setup_system_monitor()
            self.setup_timers()
            self.apply_sifer_theme()
           
        except Exception as e:
            error_msg = f"خطأ في تهيئة MainWindow: {str(e)}"
            logging.error(error_msg)
            print(error_msg)
   
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("S.I.F.E.R - Surveillance Interface For Enhanced Response")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 800)
       
        # الأداة الرئيسية
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
       
        # التخطيط الرئيسي
        main_layout = QHBoxLayout(main_widget)
       
        # الجانب الأيسر - معلومات النظام
        left_panel = self.create_left_panel()
       
        # الجانب الأيمن - السجلات والشبكة
        right_panel = self.create_right_panel()
       
        # إضافة الألواح للتخطيط الرئيسي
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
       
        main_layout.addWidget(splitter)
       
        # شريط الحالة
        self.setup_status_bar()
       
    def create_left_panel(self):
        """إنشاء اللوح الأيسر"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
       
        # عنوان S.I.F.E.R
        title_label = QLabel("S.I.F.E.R")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(title_label)
       
        # subtitle
        subtitle_label = QLabel("Surveillance Interface For Enhanced Response")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(subtitle_label)
       
        # حالة الاتصال
        connection_group = QGroupBox("حالة الاتصال")
        connection_layout = QVBoxLayout(connection_group)
       
        self.connection_label = QLabel("حالة الاتصال: غير متصل")
        self.connection_label.setObjectName("connectionLabel")
        self.connection_label.setAlignment(Qt.AlignCenter)
        connection_layout.addWidget(self.connection_label)
       
        # زر إعادة الاتصال
        self.reconnect_btn = QPushButton("إعادة الاتصال")
        self.reconnect_btn.setObjectName("reconnectBtn")
        self.reconnect_btn.clicked.connect(self.reconnect_to_server)
        connection_layout.addWidget(self.reconnect_btn)
       
        left_layout.addWidget(connection_group)
       
        # معلومات النظام
        system_group = QGroupBox("مراقبة النظام")
        system_layout = QVBoxLayout(system_group)
       
        # استخدام الرامات
        ram_frame = QFrame()
        ram_layout = QVBoxLayout(ram_frame)
       
        self.ram_label = QLabel("استخدام الذاكرة (RAM)")
        self.ram_label.setObjectName("sectionLabel")
        ram_layout.addWidget(self.ram_label)
       
        self.ram_progress = QProgressBar()
        self.ram_progress.setObjectName("ramProgress")
        self.ram_progress.setRange(0, 100)
        ram_layout.addWidget(self.ram_progress)
       
        self.ram_details = QLabel("0 GB / 0 GB (0%)")
        self.ram_details.setObjectName("detailsLabel")
        ram_layout.addWidget(self.ram_details)
       
        system_layout.addWidget(ram_frame)
       
        # استخدام المعالج
        cpu_frame = QFrame()
        cpu_layout = QVBoxLayout(cpu_frame)
       
        self.cpu_label = QLabel("استخدام المعالج (CPU)")
        self.cpu_label.setObjectName("sectionLabel")
        cpu_layout.addWidget(self.cpu_label)
       
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setObjectName("cpuProgress")
        self.cpu_progress.setRange(0, 100)
        cpu_layout.addWidget(self.cpu_progress)
       
        self.cpu_details = QLabel("0%")
        self.cpu_details.setObjectName("detailsLabel")
        cpu_layout.addWidget(self.cpu_details)
       
        system_layout.addWidget(cpu_frame)
       
        # معلومات الشبكة
        network_info_frame = QFrame()
        network_info_layout = QVBoxLayout(network_info_frame)
       
        self.network_info_label = QLabel("معلومات الشبكة")
        self.network_info_label.setObjectName("sectionLabel")
        network_info_layout.addWidget(self.network_info_label)
       
        self.ip_label = QLabel("IP: جاري الحصول...")
        self.ip_label.setObjectName("detailsLabel")
        network_info_layout.addWidget(self.ip_label)
       
        self.wifi_label = QLabel("شبكة Wi-Fi: جاري الفحص...")
        self.wifi_label.setObjectName("detailsLabel")
        network_info_layout.addWidget(self.wifi_label)
       
        system_layout.addWidget(network_info_frame)
       
        left_layout.addWidget(system_group)
       
        # إضافة مساحة مرنة
        left_layout.addStretch()
       
        return left_widget
   
    def create_right_panel(self):
        """إنشاء اللوح الأيمن"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
       
        # تبويبات
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("mainTabs")
       
        # تبويب السجل
        log_tab = self.create_log_tab()
        self.tab_widget.addTab(log_tab, "سجل الأنشطة")
       
        # تبويب اتصالات الشبكة
        network_tab = self.create_network_tab()
        self.tab_widget.addTab(network_tab, "اتصالات الشبكة")
       
        # تبويب الإحصائيات
        stats_tab = self.create_stats_tab()
        self.tab_widget.addTab(stats_tab, "الإحصائيات")
       
        right_layout.addWidget(self.tab_widget)
       
        return right_widget
   
    def create_log_tab(self):
        """إنشاء تبويب السجل"""
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
       
        # أدوات التحكم بالسجل
        log_controls = QHBoxLayout()
       
        # فلتر السجل
        self.log_filter = QComboBox()
        self.log_filter.setObjectName("logFilter")
        self.log_filter.addItems(["جميع الرسائل", "المعلومات", "التحذيرات", "الأخطاء"])
        self.log_filter.currentTextChanged.connect(self.filter_log_messages)
        log_controls.addWidget(QLabel("تصفية:"))
        log_controls.addWidget(self.log_filter)
       
        log_controls.addStretch()
       
        # زر مسح السجل
        clear_btn = QPushButton("مسح السجل")
        clear_btn.setObjectName("clearBtn")
        clear_btn.clicked.connect(self.clear_log)
        log_controls.addWidget(clear_btn)
       
        # زر حفظ السجل
        save_btn = QPushButton("حفظ السجل")
        save_btn.setObjectName("saveBtn")
        save_btn.clicked.connect(self.save_log)
        log_controls.addWidget(save_btn)
       
        log_layout.addLayout(log_controls)
       
        # منطقة النصوص للسجل
        self.text_area = QTextEdit()
        self.text_area.setObjectName("logTextArea")
        self.text_area.setReadOnly(True)
        log_layout.addWidget(self.text_area)
       
        return log_widget
   
    def create_network_tab(self):
        """إنشاء تبويب اتصالات الشبكة"""
        network_widget = QWidget()
        network_layout = QVBoxLayout(network_widget)
       
        # جدول اتصالات الشبكة
        self.network_table = QTableWidget()
        self.network_table.setObjectName("networkTable")
        self.network_table.setColumnCount(4)
        self.network_table.setHorizontalHeaderLabels(["العنوان المحلي", "العنوان البعيد", "الحالة", "معرف العملية"])
       
        # تحسين عرض الجدول
        header = self.network_table.horizontalHeader()
        header.setStretchLastSection(True)
       
        network_layout.addWidget(self.network_table)
       
        return network_widget
   
    def create_stats_tab(self):
        """إنشاء تبويب الإحصائيات"""
        stats_widget = QWidget()
        stats_layout = QGridLayout(stats_widget)
       
        # إحصائيات عامة
        self.stats_labels = {}
       
        stats_items = [
            ("وقت التشغيل:", "uptime"),
            ("العمليات النشطة:", "processes"),
            ("استخدام القرص:", "disk"),
            ("درجة الحرارة:", "temperature"),
            ("البيانات المرسلة:", "bytes_sent"),
            ("البيانات المستلمة:", "bytes_recv")
        ]
       
        for i, (label, key) in enumerate(stats_items):
            row, col = i // 2, (i % 2) * 2
           
            label_widget = QLabel(label)
            label_widget.setObjectName("statsLabel")
            stats_layout.addWidget(label_widget, row, col)
           
            value_widget = QLabel("جاري التحميل...")
            value_widget.setObjectName("statsValue")
            self.stats_labels[key] = value_widget
            stats_layout.addWidget(value_widget, row, col + 1)
       
        return stats_widget
   
    def setup_status_bar(self):
        """إعداد شريط الحالة"""
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
       
        # حالة الاتصال في شريط الحالة
        self.status_connection = QLabel("غير متصل")
        self.status_connection.setObjectName("statusConnection")
        self.statusBar.addPermanentWidget(self.status_connection)
       
        # وقت آخر تحديث
        self.status_time = QLabel()
        self.statusBar.addPermanentWidget(self.status_time)
       
        self.statusBar.showMessage("جاري تهيئة النظام...")
   
    def setup_system_monitor(self):
        """إعداد مراقب النظام"""
        self.system_thread = SystemMonitorThread()
        self.system_thread.ram_updated.connect(self.update_ram_info)
        self.system_thread.network_updated.connect(self.update_network_table)
        self.system_thread.cpu_updated.connect(self.update_cpu_info)
        self.system_thread.start()
   
    def setup_timers(self):
        """إعداد المؤقتات"""
        # مؤقت تحديث الوقت
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)
       
        # مؤقت تحديث معلومات الشبكة
        self.network_info_timer = QTimer()
        self.network_info_timer.timeout.connect(self.update_network_info)
        self.network_info_timer.start(5000)
       
        # مؤقت تحديث الإحصائيات
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(3000)
   
    def apply_sifer_theme(self):
        """تطبيق نمط S.I.F.E.R"""
        style = """
        QMainWindow {
            background-color: #0B0B0B;
            color: #E5E5E5;
        }
       
        #titleLabel {
            font-family: 'Orbitron', monospace;
            font-size: 28px;
            font-weight: bold;
            color: #FF0033;
            text-align: center;
            padding: 10px;
            border: 2px solid #FF0033;
            border-radius: 10px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                       stop:0 rgba(255,0,51,0.1),
                                       stop:1 rgba(0,255,255,0.1));
        }
       
        #subtitleLabel {
            font-size: 12px;
            color: #2E2E2E;
            font-style: italic;
            padding: 5px;
        }
       
        #connectionLabel {
            font-size: 16px;
            font-weight: bold;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
        }
       
        QGroupBox {
            font-weight: bold;
            border: 2px solid #2E2E2E;
            border-radius: 10px;
            margin: 5px;
            padding-top: 10px;
            background-color: rgba(46, 46, 46, 0.3);
        }
       
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #00FFFF;
        }
       
        #sectionLabel {
            font-size: 14px;
            font-weight: bold;
            color: #00FFFF;
            padding: 5px;
        }
       
        #detailsLabel {
            font-size: 12px;
            color: #E5E5E5;
            padding: 2px 5px;
        }
       
        #ramProgress, #cpuProgress {
            height: 20px;
            border: 1px solid #2E2E2E;
            border-radius: 10px;
            text-align: center;
        }
       
        #ramProgress::chunk {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                       stop:0 #00FF88, stop:0.5 #FFB300, stop:1 #FF0033);
            border-radius: 9px;
        }
       
        #cpuProgress::chunk {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                       stop:0 #00FFFF, stop:0.5 #FFB300, stop:1 #FF0033);
            border-radius: 9px;
        }
       
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                       stop:0 #FF0033, stop:1 #B30000);
            color: #E5E5E5;
            border: 1px solid #FF0033;
            border-radius: 5px;
            padding: 8px 16px;
            font-weight: bold;
        }
       
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                       stop:0 #FF3366, stop:1 #CC0033);
            box-shadow: 0 0 10px rgba(255, 0, 51, 0.5);
        }
       
        QPushButton:pressed {
            background: #B30000;
        }
       
        QTabWidget::pane {
            border: 1px solid #2E2E2E;
            background-color: rgba(11, 11, 11, 0.8);
        }
       
        QTabBar::tab {
            background: rgba(46, 46, 46, 0.5);
            color: #E5E5E5;
            padding: 8px 16px;
            border: 1px solid #2E2E2E;
        }
       
        QTabBar::tab:selected {
            background: rgba(0, 255, 255, 0.2);
            color: #00FFFF;
            border-bottom: 2px solid #00FFFF;
        }
       
        QTabBar::tab:hover {
            background: rgba(255, 0, 51, 0.2);
        }
       
        #logTextArea {
            background-color: rgba(46, 46, 46, 0.9);
            border: 1px solid #00FF88;
            border-radius: 5px;
            padding: 5px;
            font-family: 'Consolas', monospace;
            color: #E5E5E5;
        }
       
        #networkTable {
            background-color: rgba(46, 46, 46, 0.9);
            alternate-background-color: rgba(70, 70, 70, 0.5);
            border: 1px solid #2E2E2E;
            gridline-color: #2E2E2E;
        }
       
        #networkTable::item {
            padding: 5px;
            color: #E5E5E5;
        }
       
        #networkTable::item:selected {
            background-color: rgba(0, 255, 255, 0.3);
        }
       
        QHeaderView::section {
            background-color: #2E2E2E;
            color: #00FFFF;
            padding: 5px;
            border: 1px solid #1E1E1E;
            font-weight: bold;
        }
       
        QComboBox {
            background-color: rgba(46, 46, 46, 0.9);
            border: 1px solid #2E2E2E;
            border-radius: 3px;
            padding: 5px;
            color: #E5E5E5;
        }
       
        QComboBox::drop-down {
            border: none;
        }
       
        QComboBox::down-arrow {
            image: none;
            border: 1px solid #00FFFF;
            width: 0;
            height: 0;
        }
       
        #statusConnection {
            color: #FF0033;
            font-weight: bold;
            padding: 2px 10px;
        }
       
        #statsLabel {
            font-weight: bold;
            color: #00FFFF;
            padding: 5px;
        }
       
        #statsValue {
            color: #E5E5E5;
            padding: 5px;
            font-family: 'Consolas', monospace;
        }
       
        QStatusBar {
            background-color: rgba(46, 46, 46, 0.9);
            color: #E5E5E5;
            border-top: 1px solid #FF0033;
        }
        """
       
        self.setStyleSheet(style)
   
    def set_websocket_client(self, ws_client):
        """تعيين WebSocketClient لإعادة الاتصال"""
        self.ws_client = ws_client

    def reconnect_to_server(self):
        """إعادة الاتصال بالخادم"""
        try:
            if self.ws_client:
                self.ws_client.running = False
                self.log_message("إيقاف الاتصال الحالي...")
                self.msleep(1000)  # انتظار لإغلاق الخيط
                self.ws_client.running = True
                threading.Thread(target=self.ws_client.run, daemon=True).start()
                self.log_message("محاولة إعادة الاتصال بالخادم...")
        except Exception as e:
            error_msg = f"خطأ في إعادة الاتصال: {str(e)}"
            logging.error(error_msg)
            self.log_message(error_msg, "الأخطاء")

    def filter_log_messages(self, filter_type):
        """تصفية رسائل السجل"""
        try:
            self.text_area.clear()
            for msg, msg_type in self.log_messages:
                if filter_type == "جميع الرسائل" or filter_type == msg_type:
                    self.text_area.append(f"[{msg_type}] {msg}")
        except Exception as e:
            error_msg = f"خطأ في تصفية السجل: {str(e)}"
            logging.error(error_msg)
            self.log_message(error_msg, "الأخطاء")

    def clear_log(self):
        """مسح السجل"""
        try:
            self.text_area.clear()
            self.log_messages = []
            self.log_message("تم مسح السجل")
        except Exception as e:
            error_msg = f"خطأ في مسح السجل: {str(e)}"
            logging.error(error_msg)
            self.log_message(error_msg, "الأخطاء")

    def save_log(self):
        """حفظ السجل إلى ملف"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(self, "حفظ السجل", "", "Text Files (*.txt);;All Files (*)")
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    for msg, _ in self.log_messages:
                        f.write(f"{msg}\n")
                self.log_message(f"تم حفظ السجل في: {file_path}")
        except Exception as e:
            error_msg = f"خطأ في حفظ السجل: {str(e)}"
            logging.error(error_msg)
            self.log_message(error_msg, "الأخطاء")

    def update_ram_info(self, ram_data):
        """تحديث معلومات الرامات"""
        try:
            percent = ram_data['percent']
            used = ram_data['used']
            total = ram_data['total']
           
            self.ram_progress.setValue(int(percent))
            self.ram_details.setText(f"{used} GB / {total} GB ({percent:.1f}%)")
           
            # تحديث لون شريط التقدم حسب النسبة
            if percent >= 90:
                self.ram_progress.setStyleSheet("""
                    QProgressBar::chunk { background-color: #FF0033; }
                """)
                current_time = time.time()
                if percent >= 95 and (current_time - self.last_ram_warning) >= 300:  # 5 دقائق
                    self.show_warning("تحذير", f"استخدام الذاكرة مرتفع جداً: {percent:.1f}%")
                    self.last_ram_warning = current_time
                    self.log_message(f"تحذير: استخدام الذاكرة مرتفع جداً: {percent:.1f}%", "التحذيرات")
                elif percent >= 95:
                    self.log_message(f"تحذير: استخدام الذاكرة مرتفع جداً: {percent:.1f}%", "التحذيرات")
            elif percent >= 70:
                self.ram_progress.setStyleSheet("""
                    QProgressBar::chunk { background-color: #FFB300; }
                """)
            else:
                self.ram_progress.setStyleSheet("""
                    QProgressBar::chunk { background-color: #00FF88; }
                """)
               
            # حفظ التاريخ للرسم البياني
            if len(self.ram_history) > 60:  # الاحتفاظ بآخر 60 قراءة (دقيقتين)
                self.ram_history.pop(0)
            self.ram_history.append(percent)
           
        except Exception as e:
            logging.error(f"خطأ في تحديث معلومات RAM: {str(e)}")
            self.log_message(f"خطأ في تحديث معلومات RAM: {str(e)}", "الأخطاء")

    def update_cpu_info(self, cpu_percent):
        """تحديث معلومات المعالج"""
        try:
            self.cpu_progress.setValue(int(cpu_percent))
            self.cpu_details.setText(f"{cpu_percent:.1f}%")
           
            # تحديث لون شريط التقدم حسب النسبة
            if cpu_percent >= 80:
                self.cpu_progress.setStyleSheet("""
                    QProgressBar::chunk { background-color: #FF0033; }
                """)
                current_time = time.time()
                if cpu_percent >= 80 and (current_time - self.last_cpu_warning) >= 300:  # 5 دقائق
                    self.show_warning("تحذير", f"استخدام المعالج مرتفع جداً: {cpu_percent:.1f}%")
                    self.last_cpu_warning = current_time
                    self.log_message(f"تحذير: استخدام المعالج مرتفع جداً: {cpu_percent:.1f}%", "التحذيرات")
                elif cpu_percent >= 80:
                    self.log_message(f"تحذير: استخدام المعالج مرتفع جداً: {cpu_percent:.1f}%", "التحذيرات")
            elif cpu_percent >= 60:
                self.cpu_progress.setStyleSheet("""
                    QProgressBar::chunk { background-color: #FFB300; }
                """)
            else:
                self.cpu_progress.setStyleSheet("""
                    QProgressBar::chunk { background-color: #00FFFF; }
                """)
           
            # حفظ التاريخ
            if len(self.cpu_history) > 60:
                self.cpu_history.pop(0)
            self.cpu_history.append(cpu_percent)
           
        except Exception as e:
            logging.error(f"خطأ في تحديث معلومات CPU: {str(e)}")
            self.log_message(f"خطأ في تحديث معلومات CPU: {str(e)}", "الأخطاء")

    def update_network_table(self, connections):
        """تحديث جدول اتصالات الشبكة"""
        try:
            self.network_table.setRowCount(len(connections))
           
            for row, conn in enumerate(connections):
                self.network_table.setItem(row, 0, QTableWidgetItem(conn['local']))
                self.network_table.setItem(row, 1, QTableWidgetItem(conn['remote']))
               
                status_item = QTableWidgetItem(conn['status'])
                if conn['status'] == 'ESTABLISHED':
                    status_item.setForeground(QColor('#00FF88'))
                else:
                    status_item.setForeground(QColor('#FFB300'))
                self.network_table.setItem(row, 2, status_item)
               
                self.network_table.setItem(row, 3, QTableWidgetItem(str(conn['pid'])))
               
        except Exception as e:
            logging.error(f"خطأ في تحديث جدول الشبكة: {str(e)}")
            self.log_message(f"خطأ في تحديث جدول الشبكة: {str(e)}", "الأخطاء")

    def update_network_info(self):
        """تحديث معلومات الشبكة"""
        try:
            # الحصول على IP
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.connect(("8.8.8.8", 80))
                ip = sock.getsockname()[0]
                sock.close()
                self.ip_label.setText(f"IP: {ip}")
            except:
                self.ip_label.setText("IP: غير متاح")
           
            # الحصول على معلومات Wi-Fi (Windows)
            try:
                result = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'],
                                      capture_output=True, text=True, encoding='cp1256')
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'SSID' in line and ':' in line:
                            ssid = line.split(':')[-1].strip()
                            if ssid and ssid != "":
                                self.wifi_label.setText(f"شبكة Wi-Fi: {ssid}")
                                break
                    else:
                        self.wifi_label.setText("شبكة Wi-Fi: غير متصل")
                else:
                    self.wifi_label.setText("شبكة Wi-Fi: خطأ في الوصول")
            except:
                self.wifi_label.setText("شبكة Wi-Fi: غير متاح")
               
        except Exception as e:
            logging.error(f"خطأ في تحديث معلومات الشبكة: {str(e)}")
            self.log_message(f"خطأ في تحديث معلومات الشبكة: {str(e)}", "الأخطاء")

    def update_stats(self):
        """تحديث الإحصائيات"""
        try:
            # وقت التشغيل
            boot_time = psutil.boot_time()
            uptime = datetime.now().timestamp() - boot_time
            hours, remainder = divmod(int(uptime), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.stats_labels["uptime"].setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # العمليات النشطة
            processes = len(psutil.pids())
            self.stats_labels["processes"].setText(str(processes))
            
            # استخدام القرص
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            self.stats_labels["disk"].setText(f"{disk_percent:.1f}%")
            
            # درجة الحرارة (قد لا تكون متاحة على كل الأنظمة)
            try:
                temps = psutil.sensors_temperatures()
                if temps and 'coretemp' in temps:
                    temp = temps['coretemp'][0].current
                    self.stats_labels["temperature"].setText(f"{temp:.1f}°C")
                else:
                    self.stats_labels["temperature"].setText("غير متاح")
            except:
                self.stats_labels["temperature"].setText("غير متاح")
            
            # البيانات المرسلة والمستلمة
            net_io = psutil.net_io_counters()
            self.stats_labels["bytes_sent"].setText(f"{net_io.bytes_sent // (1024**2)} MB")
            self.stats_labels["bytes_recv"].setText(f"{net_io.bytes_recv // (1024**2)} MB")
            
        except Exception as e:
            logging.error(f"خطأ في تحديث الإحصائيات: {str(e)}")
            self.log_message(f"خطأ في تحديث الإحصائيات: {str(e)}", "الأخطاء")

    def update_time(self):
        """تحديث الوقت في شريط الحالة"""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.status_time.setText(current_time)
        except Exception as e:
            logging.error(f"خطأ في تحديث الوقت: {str(e)}")
            self.log_message(f"خطأ في تحديث الوقت: {str(e)}", "الأخطاء")

    def show_warning(self, title, message):
        """عرض تحذير"""
        try:
            QMessageBox.warning(self, title, message)
        except Exception as e:
            logging.error(f"خطأ في عرض التحذير: {str(e)}")
            self.log_message(f"خطأ في عرض التحذير: {str(e)}", "الأخطاء")

    def log_message(self, message, msg_type="المعلومات"):
        """تسجيل رسالة في السجل"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            full_message = f"[{timestamp}] {message}"
            self.log_messages.append((full_message, msg_type))
            if self.log_filter.currentText() == "جميع الرسائل" or self.log_filter.currentText() == msg_type:
                self.text_area.append(full_message)
            self.text_area.ensureCursorVisible()
            logging.info(f"سجل: {message}")
        except Exception as e:
            logging.error(f"خطأ في log_message: {str(e)}")
            print(f"خطأ في log_message: {str(e)}")

    def update_connection_status(self, connected):
        """تحديث حالة الاتصال"""
        try:
            self.connection_status = connected
            if connected:
                self.connection_label.setText("حالة الاتصال: متصل")
                self.connection_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; border-radius: 5px; color: #00FF88; background-color: rgba(0, 255, 136, 0.1);")
                self.status_connection.setText("متصل")
                self.status_connection.setStyleSheet("color: #00FF88; font-weight: bold; padding: 2px 10px;")
                self.statusBar.showMessage("متصل بالخادم")
            else:
                self.connection_label.setText("حالة الاتصال: غير متصل")
                self.connection_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; border-radius: 5px; color: #FF0033; background-color: rgba(255, 0, 51, 0.1);")
                self.status_connection.setText("غير متصل")
                self.status_connection.setStyleSheet("color: #FF0033; font-weight: bold; padding: 2px 10px;")
                self.statusBar.showMessage("غير متصل بالخادم")
        except Exception as e:
            logging.error(f"خطأ في تحديث حالة الاتصال: {str(e)}")
            self.log_message(f"خطأ في تحديث حالة الاتصال: {str(e)}", "الأخطاء")