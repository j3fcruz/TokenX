"""
Core TOTP Manager logic with fixed imports.
"""
import os
import json
import time
import re
from PyQt5.QtWidgets import (
    QMessageBox, QInputDialog, QLineEdit, QFileDialog, QTableWidgetItem, QApplication
)
from PyQt5.QtCore import QTimer
import pyotp

from config import PROFILE_DIR, MASTER_KEY_FILE, IDLE_TIMEOUT_SECS
from services.auth_service import AuthService
from services.profile_service import ProfileService
from services.qr_service import QRService
from services.totp_service import TOTPService
from services.qr_parser import parse_otpauth_uri, QRParser
from ui.actions_builder import ActionsBuilder
from core.totp_crypto import encrypt_secret, decrypt_secret


class TOTPManagerCore:
    """Core business logic for TOTP Manager."""
    
    def __init__(self, master_pw, master_key, ui_builder):
        self.master_pw = master_pw
        self.master_key = master_key
        self.ui_builder = ui_builder
        
        # Services
        self.profile_service = ProfileService(master_pw)
        self.qr_service = QRService()
        self.totp_service = TOTPService()
        self.auth_service = AuthService()
        self.qr_parser = QRParser()
        
        # Data
        self.profiles = {}
        self.active_profile = None
        
        # UI Actions
        self.actions_builder = ActionsBuilder(ui_builder.main_window, self)
        self.actions_builder.create_actions()
        self.actions_builder.create_menu_bar()
        self.actions_builder.create_toolbar()
        
        # Connections
        self.ui_builder.profile_table.cellClicked.connect(self.load_profile)
        
        # Clipboard state
        self.last_clipboard_text = ""
    
    def load_profiles(self):
        """Load all profiles from disk."""
        self.profiles.clear()
        self.ui_builder.profile_table.setRowCount(0)
        
        for f in os.listdir(PROFILE_DIR):
            if f.endswith(".enc"):
                name = f[:-4]
                try:
                    data = self.profile_service.load_profile(name)
                    if data:
                        self.profiles[name] = data
                        row = self.ui_builder.profile_table.rowCount()
                        self.ui_builder.profile_table.insertRow(row)
                        self.ui_builder.profile_table.setItem(row, 0, QTableWidgetItem(name))
                        self.ui_builder.profile_table.setItem(row, 1, QTableWidgetItem(""))
                except Exception as e:
                    self.update_status(f"[Error] Loading '{name}': {e}", color="red", duration_ms=5000)
        
        self.active_profile = None
        self.ui_builder.label.setText("🔄 Select a profile or upload QR code")
        self.ui_builder.qr_label.clear()
        self.ui_builder.totp_label.setText("TOTP Code:")
        self.refresh_totps()
    
    def load_profile(self, row, column):
        """Load selected profile."""
        profile_name = self.ui_builder.profile_table.item(row, 0).text()
        data = self.profiles.get(profile_name)
        if not data:
            return
        
        self.active_profile = data
        self.ui_builder.label.setText(f"🧾 Profile: {profile_name}")
        self.ui_builder.totp_label.setText(f"⏱️ Code: {pyotp.TOTP(data['secret']).now()}")
        
        # Display QR
        uri = f"otpauth://totp/{data['label']}?secret={data['secret']}&issuer={data['issuer']}"
        pixmap = self.qr_service.generate_qr_pixmap(uri)
        self.ui_builder.qr_label.setPixmap(pixmap)
    
    def refresh_totps(self):
        """Refresh all TOTP codes."""
        for row in range(self.ui_builder.profile_table.rowCount()):
            name_item = self.ui_builder.profile_table.item(row, 0)
            if not name_item:
                continue
            name = name_item.text()
            data = self.profiles.get(name)
            if data:
                try:
                    code, remaining = self.totp_service.generate_totp(data)
                    code_display = f"{code} ⏱️({remaining}s)"
                    self.ui_builder.profile_table.setItem(row, 1, QTableWidgetItem(code_display))
                    if self.active_profile == data:
                        self.ui_builder.totp_label.setText(code_display)
                except Exception:
                    self.ui_builder.profile_table.setItem(row, 1, QTableWidgetItem("❌ Error"))
    
    def upload_qr(self):
        """Upload QR code from file."""
        fname, _ = QFileDialog.getOpenFileName(
            self.ui_builder.main_window,
            "Upload QR or Encrypted QR",
            filter="All Supported (*.png *.jpg *.bmp *.enc);;Encrypted QR (*.enc);;Images (*.png *.jpg *.bmp)"
        )
        if not fname:
            return
        
        try:
            uri = self.qr_service.decode_qr_file(fname, self.master_pw)
            if not uri:
                raise ValueError("No QR code detected in this file.")
            
            # Parse the URI
            parsed = parse_otpauth_uri(uri)
            name = re.sub(r"[^\w.@-]", "_", parsed["label"])
            
            if self.profile_service.profile_exists(name):
                if QMessageBox.question(self.ui_builder.main_window, "Overwrite?",
                    f"Profile '{name}' exists. Overwrite?",
                    QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
                    return
            
            self.profile_service.save_profile(name, parsed)
            self.load_profiles()
            
            for row in range(self.ui_builder.profile_table.rowCount()):
                if self.ui_builder.profile_table.item(row, 0).text() == name:
                    self.ui_builder.profile_table.selectRow(row)
                    self.load_profile(row, 0)
                    break
            
            self.update_status(f"Imported '{name}'", color="lime")
        except Exception as e:
            self.update_status("QR Import Failed", str(e), color="red")
    
    def save_qr(self):
        """Save QR code to file."""
        if not self.active_profile:
            QMessageBox.warning(self.ui_builder.main_window, "No Profile", "Load a profile first to save its QR code.")
            return
        
        try:
            data = self.active_profile
            uri = f"otpauth://totp/{data['label']}?secret={data['secret']}&issuer={data.get('issuer','')}"
            
            default_name = re.sub(r"[^\w.@-]", "_", data["label"]) + "_qr.enc"
            save_path, _ = QFileDialog.getSaveFileName(
                self.ui_builder.main_window,
                "Save Encrypted QR",
                default_name,
                "Encrypted QR (*.enc)"
            )
            
            if save_path:
                self.qr_service.save_qr_encrypted(uri, save_path, self.master_pw)
                self.update_status(f"Encrypted QR saved: {save_path}", color="lime")
        except Exception as e:
            self.update_status(f"QR Save Error: {e}", color="red")
    
    def delete_profile(self):
        """Delete selected profile."""
        row = self.ui_builder.profile_table.currentRow()
        if row < 0:
            QMessageBox.warning(self.ui_builder.main_window, "No Selection", "Select a profile to delete.")
            return
        
        name = self.ui_builder.profile_table.item(row, 0).text()
        
        confirm = QMessageBox.question(
            self.ui_builder.main_window, "Confirm Delete",
            f"Delete profile '{name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                self.profile_service.delete_profile(name)
                self.profiles.pop(name, None)
                self.ui_builder.profile_table.removeRow(row)
                self.ui_builder.label.setText("🔄 Select a profile or upload QR")
                self.ui_builder.qr_label.clear()
                self.ui_builder.totp_label.setText("TOTP Code:")
                self.active_profile = None
            except Exception as e:
                QMessageBox.critical(self.ui_builder.main_window, "Delete Error", str(e))
    
    def check_clipboard(self):
        """Monitor clipboard for OTP URIs."""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text != self.last_clipboard_text and text.startswith("otpauth://"):
            self.last_clipboard_text = text
            try:
                parsed = parse_otpauth_uri(text)
                name = re.sub(r'[^\w.@-]', '_', parsed['label'])
                
                if self.profile_service.profile_exists(name):
                    reply = QMessageBox.question(self.ui_builder.main_window, "Overwrite?", f"Profile '{name}' exists. Overwrite?",
                                                 QMessageBox.Yes | QMessageBox.No)
                    if reply != QMessageBox.Yes:
                        return
                
                self.profile_service.save_profile(name, parsed)
                self.load_profiles()
                self.update_status("Clipboard Imported", f"Imported: {name}")
            except Exception as e:
                self.update_status("Invalid OTP URI", f"Error: {str(e)}", color="red", duration_ms=5000)
    
    def change_master_password(self):
        """Change master password."""
        self.auth_service.change_master_password(self.ui_builder.main_window, self.profile_service)
        self.master_pw = self.auth_service.master_pw
        self.load_profiles()
    
    def reset_master_key(self):
        """Reset master key."""
        confirm = QMessageBox.question(self.ui_builder.main_window, "Reset Key", "Resetting the master key will invalidate all existing profiles. Proceed?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return
        
        self.profile_service.reset_all_profiles()
        if os.path.exists(MASTER_KEY_FILE):
            os.remove(MASTER_KEY_FILE)
        QMessageBox.information(self.ui_builder.main_window, "Reset Done", "Master key and all profiles reset. Restart application.")
        QApplication.quit()
    
    def lock_application(self):
        """Lock application."""
        pw, ok = QInputDialog.getText(self.ui_builder.main_window, "Session Locked", "Re-enter master password:", QLineEdit.Password)
        if not ok or not pw:
            QApplication.quit()
        
        try:
            with open(MASTER_KEY_FILE, "r") as f:
                encrypted_master = f.read()
            master_key = decrypt_secret(encrypted_master, pw)
            self.master_key = master_key
        except Exception:
            QMessageBox.critical(self.ui_builder.main_window, "Access Denied", "Incorrect password.")
            QApplication.quit()
    
    def check_idle(self, last_activity_time):
        """Check idle timeout."""
        if time.time() - last_activity_time > IDLE_TIMEOUT_SECS:
            self._lock_interface()
    
    def _lock_interface(self):
        """Lock interface."""
        pw, ok = QInputDialog.getText(self.ui_builder.main_window, "Session Locked", "Re-enter master password:", QLineEdit.Password)
        if not ok or not pw:
            QApplication.quit()
        
        try:
            with open(MASTER_KEY_FILE, "r") as f:
                encrypted_master = f.read()
            master_key = decrypt_secret(encrypted_master, pw)
            self.master_key = master_key
        except Exception:
            QMessageBox.critical(self.ui_builder.main_window, "Access Denied", "Incorrect password.")
            QApplication.quit()
    
    def reset_vault(self):
        """Reset entire vault."""
        reply = QMessageBox.warning(
            self.ui_builder.main_window,
            "Reset Vault",
            "This will DELETE all profiles and the master password.\n"
            "You cannot undo this.\n\n"
            "Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            self.profile_service.reset_all_profiles()
            if os.path.exists(MASTER_KEY_FILE):
                os.remove(MASTER_KEY_FILE)
            
            self.profiles.clear()
            self.active_profile = None
            self.ui_builder.profile_table.setRowCount(0)
            self.ui_builder.totp_label.setText("------")
            self.ui_builder.qr_label.setText("No QR Code")
            self.ui_builder.qr_label.clear()
            
            QMessageBox.information(self.ui_builder.main_window, "Vault Reset", "Vault successfully reset.\nAll data has been removed.")
            self.ui_builder.main_window.close()
        except Exception as e:
            QMessageBox.critical(self.ui_builder.main_window, "Error", f"Failed to reset vault:\n{str(e)}")
    
    def manual_totp_prompt(self):
        """Open TOTP dialog."""
        try:
            from ui.totp_generator import TOTPDialog
            dialog = TOTPDialog(parent=self.ui_builder.main_window)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self.ui_builder.main_window, "Error", f"Failed to open TOTP Generator:\n{str(e)}")
    
    def update_status(self, message, detail=None, color="lime", duration_ms=4000):
        """Update status label."""
        if detail:
            full_text = f"{message}: {detail}"
        else:
            full_text = message
        
        self.ui_builder.status_label.setText(full_text)
        self.ui_builder.status_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                background-color: #222;
                border-radius: 6px;
                padding: 6px;
            }}
        """)
        
        QTimer.singleShot(duration_ms, lambda: self.ui_builder.status_label.setText("Ready"))