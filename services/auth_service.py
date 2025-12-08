"""
Authentication service with enhanced password dialog.
"""
import os
import base64
from PyQt5.QtWidgets import QInputDialog, QLineEdit, QMessageBox
from config import MASTER_KEY_FILE
from core.totp_crypto import encrypt_secret, decrypt_secret
from ui.password_dialog import PasswordDialog



class AuthService:
    """Handles authentication operations."""

    def __init__(self):
        self.master_pw = None
        self.master_key = None

    def authenticate(self):
        """Authenticate user with master password."""
        if os.path.exists(MASTER_KEY_FILE):
            # Existing master password - simple prompt
            pw, ok = QInputDialog.getText(None, "Master Password", "Enter master password:", QLineEdit.Password)
            if not ok or not pw:
                import sys
                sys.exit()
            try:
                with open(MASTER_KEY_FILE, "r") as f:
                    encrypted_master = f.read()
                self.master_key = decrypt_secret(encrypted_master, pw)
                self.master_pw = pw
            except Exception:
                QMessageBox.critical(None, "Error", "Incorrect master password or corrupted key file.")
                import sys
                sys.exit()
        else:
            # New setup - use advanced password dialog
            dialog = PasswordDialog(mode="setup", min_length=8)
            if dialog.exec() == PasswordDialog.Accepted:
                pw = dialog.get_password()
                self.master_key = base64.urlsafe_b64encode(os.urandom(32)).decode()
                self.master_pw = pw
                encrypted = encrypt_secret(self.master_key, pw)
                with open(MASTER_KEY_FILE, "w") as f:
                    f.write(encrypted)
            else:
                import sys
                sys.exit()

    def change_master_password(self, parent_window, profile_service):
        """Change master password with strength requirements."""
        if not os.path.exists(MASTER_KEY_FILE):
            QMessageBox.warning(parent_window, "Error", "Master key file not found.")
            return

        # Current password
        old_pw, ok = QInputDialog.getText(
            parent_window, "Current Password",
            "Enter current master password:",
            QLineEdit.Password
        )
        if not ok or not old_pw:
            return

        # Validate
        try:
            with open(MASTER_KEY_FILE, "r", encoding="utf-8") as f:
                encrypted = f.read().strip()
            master_key = decrypt_secret(encrypted, old_pw)
        except Exception:
            QMessageBox.critical(parent_window, "Invalid Password", "The current password is incorrect.")
            return

        # New password dialog
        dialog = PasswordDialog(parent=parent_window, mode="change", min_length=8)
        if dialog.exec() != PasswordDialog.Accepted:
            return

        new_pw = dialog.get_password()

        # Re-encrypt profiles
        succeeded, failed = profile_service.reencrypt_all_profiles(old_pw, new_pw)

        if failed:
            QMessageBox.critical(
                parent_window, "Profile Error",
                "Password NOT changed.\n\n"
                "The following profiles could not be re-encrypted:\n"
                + "\n".join(failed)
            )
            return

        # Update master key file
        new_master = encrypt_secret(master_key, new_pw)
        with open(MASTER_KEY_FILE, "w", encoding="utf-8") as f:
            f.write(new_master)

        self.master_pw = new_pw

        QMessageBox.information(
            parent_window, "Success",
            "Master password updated successfully.\nAll profiles were re-encrypted."
        )