import sys
import threading
import time
import json
import logging
import psutil
from datetime import datetime
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal
from websocket import WebSocket, create_connection
from cryptography.fernet import Fernet
from ui.main_window import MainWindow

logging.basicConfig(filename="client.log", level=logging.INFO, 
                    format="%(asctime)s - %(levelname)s - %(message)s")

class Encryptor:
    def __init__(self):
        self.key = b'uJnmGjIDuQnR_GYZ5uFPGYW5xYAi-JpMO_gwoTqg0EM='
        self.cipher = Fernet(self.key)
    
    def encrypt_data(self, data):
        return self.cipher.encrypt(data.encode())
    
    def decrypt_data(self, encrypted_data):
        return self.cipher.decrypt(encrypted_data).decode()

class WebSocketClient(QObject):
    message_received = pyqtSignal(str)
    connection_status = pyqtSignal(bool)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.encryptor = Encryptor()
        self.running = True

    def run(self):
        while self.running:
            ws = WebSocket()
            try:
                logging.info(f"الاتصال بـ {self.url}")
                print(f"الاتصال بـ {self.url}")
                ws.connect(self.url)
                self.connection_status.emit(True)
                while self.running:
                    try:
                        # جمع بيانات الرامات
                        memory = psutil.virtual_memory()
                        ram_data = {
                            "total": round(memory.total / (1024 ** 3), 2),  # GB
                            "used": round(memory.used / (1024 ** 3), 2),    # GB
                            "percent": memory.percent
                        }
                        
                        # جمع بيانات الشبكة
                        net_connections = psutil.net_connections()
                        net_data = [
                            {
                                "local_addr": f"{conn.laddr.ip}:{conn.laddr.port}",
                                "remote_addr": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A",
                                "status": conn.status
                            } for conn in net_connections if conn.status == "ESTABLISHED"
                        ]
                        
                        # تجميع البيانات
                        data = {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "ram": ram_data,
                            "network": net_data[:5]  # الحد الأقصى 5 اتصالات
                        }
                        data_str = json.dumps(data)
                        
                        logging.info(f"البيانات قبل التشفير: {data_str}")
                        print(f"البيانات قبل التشفير: {data_str}")
                        encrypted_data = self.encryptor.encrypt_data(data_str)
                        print(f"إرسال مشفر: {encrypted_data}")
                        ws.send(encrypted_data)
                        message = ws.recv()
                        decrypted = self.encryptor.decrypt_data(message)
                        print(f"استقبال: {decrypted}")
                        self.message_received.emit(f"رسالة من الخادم: {decrypted}")
                        time.sleep(2)  # تأخير لمنع [WinError 10054]
                    except Exception as e:
                        error_msg = f"خطأ في الإرسال أو الاستقبال: {str(e)}"
                        logging.error(error_msg)
                        print(error_msg)
                        self.message_received.emit(error_msg)
                        if "10054" in str(e):
                            self.connection_status.emit(False)
                            time.sleep(5)  # إعادة المحاولة
                            break
                        else:
                            self.connection_status.emit(False)
                            break
            except Exception as e:
                error_msg = f"لا يمكن الاتصال: {str(e)}"
                logging.error(error_msg)
                print(error_msg)
                self.message_received.emit(error_msg)
                self.connection_status.emit(False)
                time.sleep(5)
            finally:
                ws.close()

def main():
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()

        # WebSocket
        ws_client = WebSocketClient("ws://localhost:12345")
        ws_client.message_received.connect(window.log_message)
        ws_client.connection_status.connect(window.update_connection_status)
        ws_thread = threading.Thread(target=ws_client.run)
        ws_thread.daemon = True
        ws_thread.start()

        sys.exit(app.exec_())
    except Exception as e:
        error_msg = f"خطأ في التطبيق: {str(e)}"
        logging.error(error_msg)
        print(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()