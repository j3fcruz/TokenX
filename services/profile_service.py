"""
Profile management service.
"""
import os
import json
from config import PROFILE_DIR
from core.totp_crypto import encrypt_secret, decrypt_secret


class ProfileService:
    """Handles profile operations."""
    
    def __init__(self, master_pw):
        self.master_pw = master_pw
    
    def load_profile(self, name):
        """Load profile from disk."""
        profile_path = os.path.join(PROFILE_DIR, name + ".enc")
        if not os.path.exists(profile_path):
            return None
        
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                encrypted = f.read()
            decrypted = decrypt_secret(encrypted, self.master_pw)
            return json.loads(decrypted)
        except Exception:
            return None
    
    def save_profile(self, name, data):
        """Save profile to disk."""
        profile_path = os.path.join(PROFILE_DIR, name + ".enc")
        encrypted = encrypt_secret(json.dumps(data), self.master_pw)
        with open(profile_path, 'w', encoding='utf-8') as f:
            f.write(encrypted)
    
    def delete_profile(self, name):
        """Delete profile."""
        profile_path = os.path.join(PROFILE_DIR, name + ".enc")
        if os.path.exists(profile_path):
            os.remove(profile_path)
    
    def profile_exists(self, name):
        """Check if profile exists."""
        return os.path.exists(os.path.join(PROFILE_DIR, name + ".enc"))
    
    def reset_all_profiles(self):
        """Delete all profiles."""
        for f in os.listdir(PROFILE_DIR):
            if f.endswith(".enc"):
                os.remove(os.path.join(PROFILE_DIR, f))
    
    def reencrypt_all_profiles(self, old_pw, new_pw):
        """Re-encrypt all profiles with new password."""
        failed = []
        succeeded = []
        
        for f_name in os.listdir(PROFILE_DIR):
            if not f_name.endswith(".enc"):
                continue
            
            full_path = os.path.join(PROFILE_DIR, f_name)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as pf:
                    raw = pf.read().strip()
                
                decrypted = decrypt_secret(raw, old_pw)
                new_enc = encrypt_secret(decrypted, new_pw)
                
                with open(full_path, "w", encoding="utf-8") as pf:
                    pf.write(new_enc)
                
                succeeded.append(f_name)
            except Exception:
                failed.append(f_name)
        
        return succeeded, failed
