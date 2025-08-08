import sys
import threading
import json
import sqlite3
import logging
from datetime import datetime
from PyQt5.QtWidgets import QApplication
from ui.terminal import TerminalWindow
from ui.overlay import HUDOverlay
from utils.net_monitor import NetworkMonitor
from utils.emergency import EmergencyHandler
from utils.encryption import Encryption
from websocket_server import WebsocketServer

logging.basicConfig(filename="server.log", level=logging.INFO, 
                    format="%(asctime)s - %(levelname)s - %(message)s")

def init_database():
    conn = sqlite3.connect("database/sifer_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_data (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            ram_total REAL,
            ram_used REAL,
            ram_percent REAL,
            network_connections TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS network_status (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            ssid TEXT,
            local_ip TEXT,
            status TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS permissions_log (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            permission TEXT,
            status TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emergency_trigger (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            reason TEXT,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

def load_config():
    with open("config/settings.json", "r") as f:
        return json.load(f)

def start_websocket_server(terminal):
    def on_message(client, server, message):
        enc = Encryption()
        try:
            logging.info(f"البيانات الخام: {message}")
            print(f"البيانات الخام: {message}")
            decrypted = enc.decrypt_data(message)
            logging.info(f"فك التشفير: {decrypted}")
            print(f"فك التشفير: {decrypted}")
            terminal.log_message(f"بيانات من العميل: {decrypted}")
            
            # تخزين البيانات في قاعدة البيانات
            try:
                data = eval(decrypted)  # تحويل النص إلى قاموس
                conn = sqlite3.connect("database/sifer_data.db")
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO system_data (timestamp, ram_total, ram_used, ram_percent, network_connections)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    data["ram"]["total"],
                    data["ram"]["used"],
                    data["ram"]["percent"],
                    json.dumps(data["network"])
                ))
                conn.commit()
                conn.close()
            except Exception as e:
                error_msg = f"خطأ في تخزين البيانات: {str(e)}"
                logging.error(error_msg)
                print(error_msg)
                terminal.log_message(error_msg)
            
            server.send_message(client, enc.encrypt_data("تم الاستلام"))
        except Exception as e:
            error_msg = f"خطأ في فك التشفير: {str(e)}"
            logging.error(error_msg)
            print(error_msg)
            terminal.log_message(error_msg)

    server = WebsocketServer(host="0.0.0.0", port=12345)
    server.set_fn_message_received(on_message)
    try:
        logging.info("بدء خادم WebSocket على 0.0.0.0:12345")
        print("بدء خادم WebSocket على 0.0.0.0:12345")
        server.run_forever()
    except Exception as e:
        error_msg = f"خطأ في خادم WebSocket: {str(e)}"
        logging.error(error_msg)
        print(error_msg)

def main():
    try:
        app = QApplication(sys.argv)
        init_database()
        config = load_config()
        terminal = TerminalWindow()
        terminal.show()
        hud = HUDOverlay()
        hud.show()
        net_monitor = NetworkMonitor()
        net_monitor.start()
        emergency_handler = EmergencyHandler(config["emergency_timeout"])
        emergency_handler.start()
        ws_thread = threading.Thread(target=start_websocket_server, args=(terminal,))
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