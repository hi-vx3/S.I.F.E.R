from PyQt5.QtCore import QThread
import sqlite3
import datetime
import time

class EmergencyHandler(QThread):
    def __init__(self, timeout):
        super().__init__()
        self.timeout = timeout
        self.running = True
    
    def run(self):
        start_time = None
        while self.running:
            # فحص فقدان الاتصال
            if self.connection_lost():
                if not start_time:
                    start_time = time.time()
                
                if time.time() - start_time >= self.timeout:
                    self.activate_emergency()
            
            else:
                start_time = None
            time.sleep(1)
    
    def connection_lost(self):
        # بديل: تنفيذ فحص فعلي للاتصال
        return False
    
    def activate_emergency(self):
        conn = sqlite3.connect("database/sifer_data.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO emergency_trigger (timestamp, reason, status)
            VALUES (?, ?, ?)
        """, (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "فقدان الاتصال", "نشط"))
        conn.commit()
        conn.close()
        # بديل: تنفيذ منع الإغلاق وإرسال الموقع
        print("تم تفعيل وضع الطوارئ")