import asyncio
import websockets
import logging
from datetime import datetime
from cryptography.fernet import Fernet

# إعداد السجل
logging.basicConfig(
    filename="dummy_websocket_server.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

class Encryptor:
    def __init__(self):
        self.key = b'uJnmGjIDuQnR_GYZ5uFPGYW5xYAi-JpMO_gwoTqg0EM='
        self.cipher = Fernet(self.key)
    
    def encrypt_data(self, data):
        return self.cipher.encrypt(data.encode())
    
    def decrypt_data(self, encrypted_data):
        return self.cipher.decrypt(encrypted_data).decode()

async def handle_connection(websocket, path):
    """التعامل مع الاتصال الوارد"""
    encryptor = Encryptor()
    try:
        logging.info(f"اتصال جديد: {websocket.remote_address}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] اتصال جديد من {websocket.remote_address}")
        
        async for message in websocket:
            try:
                # فك تشفير البيانات المستلمة
                decrypted_data = encryptor.decrypt_data(message)
                logging.info(f"البيانات المستلمة: {decrypted_data}")
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] البيانات المستلمة: {decrypted_data}")
                
                # إرسال رد مشفر
                response = "تم الاستلام"
                encrypted_response = encryptor.encrypt_data(response)
                await websocket.send(encrypted_response)
                logging.info(f"تم إرسال الرد: {response}")
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] تم إرسال الرد: {response}")
                
            except Exception as e:
                error_msg = f"خطأ في معالجة البيانات: {str(e)}"
                logging.error(error_msg)
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {error_msg}")
                if "10054" in str(e):
                    break  # إنهاء الاتصال عند [WinError 10054]
    
    except Exception as e:
        error_msg = f"خطأ في الاتصال: {str(e)}"
        logging.error(error_msg)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {error_msg}")
    
    finally:
        logging.info(f"إغلاق الاتصال: {websocket.remote_address}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] إغلاق الاتصال: {websocket.remote_address}")

async def main():
    """تشغيل الخادم"""
    try:
        server = await websockets.serve(handle_connection, "localhost", 12345)
        logging.info("الخادم يعمل على ws://localhost:12345")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] الخادم يعمل على ws://localhost:12345")
        await server.wait_closed()
    except Exception as e:
        logging.error(f"خطأ في تشغيل الخادم: {str(e)}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] خطأ في تشغيل الخادم: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("تم إيقاف الخادم بواسطة المستخدم")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] تم إيقاف الخادم")
    except Exception as e:
        logging.error(f"خطأ في التطبيق: {str(e)}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] خطأ: {str(e)}")