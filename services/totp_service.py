"""
TOTP generation service.
"""
import time
import pyotp


class TOTPService:
    """Handles TOTP generation."""
    
    def generate_totp(self, data):
        """Generate TOTP code and remaining time."""
        totp = pyotp.TOTP(
            data['secret'],
            digits=int(data.get('digits', 6)),
            interval=int(data.get('period', 30)),
            digest=data.get('algorithm', 'SHA1').lower()
        )
        interval = totp.interval
        remaining = interval - int(time.time()) % interval
        code = totp.now()
        return code, remaining