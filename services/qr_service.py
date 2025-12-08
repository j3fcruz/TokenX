"""
QR code operations service.
"""
import qrcode
from PIL import Image
from io import BytesIO
from pyzbar.pyzbar import decode
from PyQt5.QtGui import QPixmap
from config import QR_PREVIEW_SIZE
from core.totp_crypto import encrypt_bytes, decrypt_bytes


class QRService:
    """Handles QR code operations."""
    
    def decode_qr_file(self, fname, master_pw):
        """Decode QR code from file."""
        if fname.lower().endswith(".enc"):
            with open(fname, "rb") as f:
                encrypted_bytes = f.read()
            raw_bytes = decrypt_bytes(encrypted_bytes, master_pw)
            img = Image.open(BytesIO(raw_bytes))
        else:
            img = Image.open(fname)
        
        result = decode(img)
        if not result:
            return None
        
        return result[0].data.decode()
    
    def generate_qr_pixmap(self, uri):
        """Generate QR code as pixmap."""
        qr = qrcode.make(uri).resize(QR_PREVIEW_SIZE)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue())
        return pixmap
    
    def save_qr_encrypted(self, uri, save_path, master_pw):
        """Save QR code encrypted."""
        img = qrcode.make(uri).resize((200, 200))
        buf = BytesIO()
        img.save(buf, format="PNG")
        raw_bytes = buf.getvalue()
        encrypted = encrypt_bytes(raw_bytes, master_pw)
        
        with open(save_path, "wb") as f:
            f.write(encrypted)