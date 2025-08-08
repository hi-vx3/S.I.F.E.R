from cryptography.fernet import Fernet

class Encryption:
    def __init__(self):
        # استخدم المفتاح الذي قدمته
        self.key = b'uJnmGjIDuQnR_GYZ5uFPGYW5xYAi-JpMO_gwoTqg0EM='
        self.cipher = Fernet(self.key)
    
    def encrypt_data(self, data):
        return self.cipher.encrypt(data.encode())
    
    def decrypt_data(self, encrypted_data):
        return self.cipher.decrypt(encrypted_data).decode()