"""
totp_generator.py
"""

import sys
import time
import base64
import secrets
import pyotp
import qrcode
import os
from io import BytesIO
from urllib.parse import urlparse, parse_qs
from PIL import Image
from pyzbar.pyzbar import decode
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon, QFont
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QFileDialog, QGroupBox,
    QHBoxLayout, QProgressBar, QDialog, QFormLayout, QScrollArea
)


class TOTPDialog(QDialog):
    """Live TOTP generator as a modal dialog with QR code & TOTP on right panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.totp = None
        self.qr_image = None
        self.init_ui()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_totp)
        self.timer.start(1000)
        self.setModal(True)  # Ensure it's modal

    def init_ui(self):
        """Initialize UI with left panel (controls) and right panel (QR + TOTP)."""
        self.setWindowTitle("TOTP Manager - Security Administration")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "assets/icons/icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.setFixedSize(700, 650)

        # Indigo Dark color scheme
        self.setStyleSheet("""
            QWidget {
                background-color: #1c1c1c;
                color: #d6d6e0;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #2a2a2a;
                color: #e8e8f2;
                border: 2px solid #303A52;
                border-radius: 8px;
                padding: 6px 10px;
            }

            QLineEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #4b597a;
                background-color: #333;
            }
            QPushButton {
                background-color: #303A52;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 10px 15px;
                font-weight: normal;
                font-size: 12px;
            }


            QPushButton:hover {
                background-color: #3f4a66;
            }

            QPushButton:pressed {
                background-color: #26304a;
            }

            QTabWidget::pane {
                border: 2px solid #303A52;
                border-radius: 12px;
                background-color: #252525;
                margin-top: -1px;
            }
            QLabel {
                color: #e8eaed;
            }
            QFrame {
                background-color: #1a1f2e;
                border: none;
            }
        """)

        # Main horizontal layout: LEFT | RIGHT
        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(24, 24, 24, 24)

        # ============== LEFT PANEL: Controls ==============
        left_layout = QVBoxLayout()
        left_layout.setSpacing(16)

        # Header Section
        header = QLabel("Security Key Configuration")
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #d6d6e0;")
        left_layout.addWidget(header)

        # Input Section with grouped layout
        input_group = QGroupBox("Secret Key Input")
        input_group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #303A52;
                    border-radius: 10px;
                    margin-top: 1ex;
                    padding-top: 15px;
                    background-color: #252525;
                }

                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 8px;
                    color: #d6d6e0;
                    font-size: 14px;
                }
        """)
        input_layout = QVBoxLayout()
        input_layout.setSpacing(10)

        secret_label = QLabel("Base32 Secret Key")
        secret_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #d6d6e0;")
        input_layout.addWidget(secret_label)

        self.secret_input = QLineEdit()
        self.secret_input.setPlaceholderText("Paste your Base32 encoded secret key here...")
        self.secret_input.textChanged.connect(self.auto_update_totp)
        input_layout.addWidget(self.secret_input)

        input_group.setLayout(input_layout)
        left_layout.addWidget(input_group)

        # Action Buttons - Vertical layout for left panel
        button_layout = QVBoxLayout()
        button_layout.setSpacing(8)

        gen_btn = QPushButton("🔑 Generate Secret")
        gen_btn.clicked.connect(self.generate_base32_secret)
        button_layout.addWidget(gen_btn)

        upload_btn = QPushButton("📁 Upload Key")
        upload_btn.clicked.connect(self.upload_key)
        button_layout.addWidget(upload_btn)

        start_btn = QPushButton("▶ Update QR TOTP ")
        start_btn.clicked.connect(self.start_totp)
        button_layout.addWidget(start_btn)

        save_btn = QPushButton("💾 Save QR Image")
        save_btn.clicked.connect(self.save_qr_image)
        button_layout.addWidget(save_btn)

        left_layout.addLayout(button_layout)

        # Account Details Section
        account_group = QGroupBox("Account Information")
        account_group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #303A52;
                    border-radius: 10px;
                    margin-top: 1ex;
                    padding-top: 15px;
                    background-color: #252525;
                }

                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 8px;
                    color: #d6d6e0;
                    font-size: 14px;
                }
        """)
        account_layout = QVBoxLayout()
        account_layout.setSpacing(10)

        account_label = QLabel("Account Name")
        account_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #d6d6e0;")
        account_layout.addWidget(account_label)

        self.account_input = QLineEdit()
        self.account_input.setPlaceholderText("e.g., john.doe@company.com")
        account_layout.addWidget(self.account_input)

        issuer_label = QLabel("Issuer")
        issuer_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #d6d6e0;")
        account_layout.addWidget(issuer_label)

        self.issuer_input = QLineEdit()
        self.issuer_input.setPlaceholderText("e.g., Company Name")
        account_layout.addWidget(self.issuer_input)

        account_group.setLayout(account_layout)
        left_layout.addWidget(account_group)

        # Recommendation label
        self.recommendation_label = QLabel("")
        self.recommendation_label.setAlignment(Qt.AlignCenter)
        self.recommendation_label.setStyleSheet("font-size: 11px; font-weight: bold;")
        left_layout.addWidget(self.recommendation_label)

        left_layout.addStretch()

        # ============== RIGHT PANEL: QR Code & TOTP ==============
        right_layout = QVBoxLayout()
        right_layout.setSpacing(20)

        # QR Code Display Section
        qr_group = QGroupBox("QR Code Preview")
        qr_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #303A52;
                border-radius: 10px;
                margin-top: 1ex;
                padding-top: 15px;
                background-color: #252525;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                color: #d6d6e0;
                font-size: 14px;
            }
        """)
        qr_layout = QVBoxLayout()
        qr_layout.setAlignment(Qt.AlignCenter)

        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setFixedSize(240, 240)
        self.qr_label.setScaledContents(True)
        self.qr_label.setStyleSheet("""
            QLabel {
                background-color: #ffffff;
                border: 2px solid #303A52;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        qr_layout.addWidget(self.qr_label)

        qr_group.setLayout(qr_layout)
        right_layout.addWidget(qr_group)

        # TOTP Display Section
        totp_group = QGroupBox("Current TOTP Code")
        totp_group.setFixedHeight(220)
        totp_group.setStyleSheet("""
            QGroupBox {
                color: #d6d6e0;
                border: 2px solid #00e676;
                border-radius: 6px;
                margin-top: 2px;
                padding-top: 2px;
                font-weight: 400;
                font-size: 10px;
                background-color: #1a1f2e;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0px 2px;
            }
        """)
        totp_layout = QVBoxLayout()
        totp_layout.setSpacing(12)
        totp_layout.setAlignment(Qt.AlignCenter)

        self.totp_label = QLabel("------")
        self.totp_label.setAlignment(Qt.AlignCenter)
        self.totp_label.setStyleSheet("""
            font-size: 40px; 
            font-weight: bold; 
            color: #00e676;
            font-family: 'Courier New', monospace;
            letter-spacing: 12px;
            padding: 20px;
            background-color: #0d2818;
            border-radius: 4px;
            min-height: 100px;
        """)
        totp_layout.addWidget(self.totp_label)

        # Countdown Bar
        countdown_container = QVBoxLayout()
        countdown_container.setSpacing(6)

        self.countdown_label = QLabel("Time Remaining: 30s")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setStyleSheet("font-size: 14px; font-weight: 500; color: #d6d6e0;")
        countdown_container.addWidget(self.countdown_label)

        # Progress bar for countdown visualization
        self.countdown_bar = QProgressBar()
        self.countdown_bar.setMaximum(30)
        self.countdown_bar.setValue(30)
        self.countdown_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #3949ab;
                border-radius: 3px;
                background-color: #1a1f2e;
                height: 12px;
            }
            QProgressBar::chunk {
                background-color: #00e676;
                border-radius: 2px;
            }
        """)
        countdown_container.addWidget(self.countdown_bar)

        totp_layout.addLayout(countdown_container)

        # Copy TOTP button
        copy_totp_btn = QPushButton("📋 Copy Code")
        copy_totp_btn.clicked.connect(self._copy_totp_code)
        copy_totp_btn.setStyleSheet("""
            QPushButton {
                background-color: #00e676;
                color: #0f1419;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #00c853;
            }
        """)
        totp_layout.addWidget(copy_totp_btn)

        totp_group.setLayout(totp_layout)
        right_layout.addWidget(totp_group)

        # Info box
        info_text = QLabel(
            "💡 Scan the QR code with your authenticator app.\n"
            "The 6-digit code updates every 30 seconds."
        )
        info_text.setWordWrap(True)
        info_text.setAlignment(Qt.AlignCenter)
        info_text.setStyleSheet("""
            background-color: #303A52; 
            padding: 12px; 
            border-radius: 4px; 
            font-size: 10px;
            color: #d6d6e0;
            border: 1px solid #2a2a2a;
        """)
        right_layout.addWidget(info_text)

        # ============== Combine Left and Right Panels ==============
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 1)

        self.setLayout(main_layout)

    # ============================================================================
    # TOTP Auto Update
    # ============================================================================
    def auto_update_totp(self):
        """Automatically generate QR and TOTP when a valid secret is entered."""
        secret = self.secret_input.text().strip().replace(" ", "")

        if not secret:
            self.totp_label.setText("------")
            self.countdown_label.setText("Time Remaining: 30s")
            self.qr_label.clear()
            self.totp = None
            self.qr_image = None
            self.recommendation_label.setText("")
            return

        try:
            # Try Base32 decode
            base64.b32decode(secret.upper(), casefold=True)
            is_base32 = True
        except Exception:
            is_base32 = False

        # Show recommendation
        if is_base32 and len(secret) == 32:
            self.recommendation_label.setText("✅ Recommended: Base32 secret (32 chars)")
            self.recommendation_label.setStyleSheet("color: #00e676; font-size: 11px; font-weight: bold;")
        else:
            self.recommendation_label.setText("⚠️ Not recommended: Use Base32 (32 chars only)")
            self.recommendation_label.setStyleSheet("color: #ff5252; font-size: 11px; font-weight: bold;")

        # Only generate TOTP if Base32
        if is_base32:
            account = self.account_input.text().strip() or "user@example.com"
            issuer = self.issuer_input.text().strip() or "MyApp"
            self.totp = pyotp.TOTP(secret)
            self.generate_qr(secret, account, issuer)
            self.update_totp()
        else:
            self.totp_label.setText("Invalid Secret")
            self.countdown_label.setText("Time Remaining: --")
            self.qr_label.clear()
            self.totp = None
            self.qr_image = None

    # ============================================================================
    # Secret Generation
    # ============================================================================
    def generate_base32_secret(self):
        """Generate a random Base32 secret."""
        random_bytes = secrets.token_bytes(20)
        self.secret_input.setText(base64.b32encode(random_bytes).decode("utf-8"))

    # ============================================================================
    # TOTP Core
    # ============================================================================
    def start_totp(self):
        """Start TOTP generation."""
        secret = self.secret_input.text().strip().replace(" ", "")
        account = self.account_input.text().strip() or "user@example.com"
        issuer = self.issuer_input.text().strip() or "MyApp"

        if not secret:
            QMessageBox.warning(self, "Error", "Please enter a Base32 TOTP secret.")
            return

        try:
            base64.b32decode(secret.upper(), casefold=True)
        except Exception as e:
            QMessageBox.critical(self, "Invalid Secret", f"Base32 decode failed: {e}")
            return

        self.totp = pyotp.TOTP(secret)
        self.generate_qr(secret, account, issuer)
        self.update_totp()

    def update_totp(self):
        """Update the displayed TOTP code and countdown."""
        if not self.totp:
            self.totp_label.setText("------")
            self.countdown_label.setText("Time Remaining: 30s")
            self.countdown_bar.setValue(30)
            self._update_progress_color(30)
            return
        try:
            current_code = self.totp.now()
            remaining = 30 - (int(time.time()) % 30)
            self.totp_label.setText(current_code)
            self.countdown_label.setText(f"Time Remaining: {remaining:02d}s")
            self.countdown_bar.setValue(remaining)
            self._update_progress_color(remaining)
        except Exception as e:
            self.totp_label.setText("ERROR")
            self.countdown_label.setText(str(e))

    def _update_progress_color(self, remaining: int):
        """Update progress bar color based on remaining time."""
        percentage = (remaining / 30) * 100

        if percentage < 33:
            # Red for less than 33%
            self.countdown_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #3949ab;
                    border-radius: 3px;
                    background-color: #1a1f2e;
                    height: 8px;
                }
                QProgressBar::chunk {
                    background-color: #ff5252;
                    border-radius: 2px;
                }
            """)
            self.totp_label.setStyleSheet("""
                font-size: 56px; 
                font-weight: bold; 
                color: #ff5252;
                font-family: 'Courier New', monospace;
                letter-spacing: 12px;
                padding: 20px;
                background-color: #3d1212;
                border-radius: 4px;
                min-height: 100px;
            """)
        else:
            # Green for 33% and above
            self.countdown_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #3949ab;
                    border-radius: 3px;
                    background-color: #1a1f2e;
                    height: 8px;
                }
                QProgressBar::chunk {
                    background-color: #00e676;
                    border-radius: 2px;
                }
            """)
            self.totp_label.setStyleSheet("""
                font-size: 56px; 
                font-weight: bold; 
                color: #00e676;
                font-family: 'Courier New', monospace;
                letter-spacing: 12px;
                padding: 20px;
                background-color: #0d2818;
                border-radius: 4px;
                min-height: 100px;
            """)

    # ============================================================================
    # QR Generation
    # ============================================================================
    def generate_qr(self, secret: str, account: str, issuer: str):
        """Generate QR code from secret."""
        uri = f"otpauth://totp/{issuer}:{account}?secret={secret}&issuer={issuer}&algorithm=SHA1&digits=6&period=30"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4
        )
        qr.add_data(uri)
        qr.make(fit=True)
        self.qr_image = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        self.qr_image.save(buffer, format="PNG")
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue())
        self.qr_label.setPixmap(pixmap.scaled(260, 260, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    # ============================================================================
    # Save QR Image with URI backup
    # ============================================================================
    def save_qr_image(self):
        """Save QR image and TOTP URI."""
        if self.qr_image is None:
            QMessageBox.warning(self, "Error", "No QR image to save. Generate TOTP first.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save QR Image", "totp_qr.png", "PNG Files (*.png);;All Files (*)"
        )
        if not file_path:
            return

        try:
            # Save the QR image
            self.qr_image.save(file_path, format="PNG")

            # Save the TOTP URI alongside as .txt
            secret = self.secret_input.text().strip().replace(" ", "")
            account = self.account_input.text().strip() or "user@example.com"
            issuer = self.issuer_input.text().strip() or "MyApp"
            totp_uri = f"otpauth://totp/{issuer}:{account}?secret={secret}&issuer={issuer}&algorithm=SHA1&digits=6&period=30"

            txt_path = file_path.rsplit(".", 1)[0] + ".txt"
            with open(txt_path, "w") as f:
                f.write(totp_uri)

            QMessageBox.information(
                self,
                "Saved",
                f"✓ QR image saved to:\n{file_path}\n\n"
                f"✓ TOTP URI saved to:\n{txt_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save QR and URI: {e}")

    # ============================================================================
    # Upload Key
    # ============================================================================
    def upload_key(self):
        """Upload key from file (text or QR image)."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Key File or QR Image",
            "",
            "Text Files (*.txt);;Image Files (*.png *.jpg *.bmp *.jpeg);;All Files (*)"
        )
        if not file_path:
            return

        try:
            secret = None

            if file_path.lower().endswith(".txt"):
                with open(file_path, "r") as f:
                    content = f.read().strip().replace(" ", "")

                if content.upper().startswith("OTPAUTH://TOTP/"):
                    # It's a full TOTP URI
                    parsed = urlparse(content)
                    params = parse_qs(parsed.query)
                    secret = params.get("secret", [None])[0]
                    account = parsed.path.split(":")[-1] if ":" in parsed.path else "user@example.com"
                    issuer = params.get("issuer", [None])[0] or "MyApp"
                    self.account_input.setText(account)
                    self.issuer_input.setText(issuer)
                else:
                    # Treat as plain Base32
                    base64.b32decode(content.upper(), casefold=True)
                    secret = content

            else:
                # It's an image
                img = Image.open(file_path)
                decoded = decode(img)
                if not decoded:
                    raise ValueError("No QR code found in the image.")

                qr_data = decoded[0].data.decode("utf-8").strip()
                try:
                    base64.b32decode(qr_data.upper(), casefold=True)
                    secret = qr_data
                except Exception:
                    if qr_data.startswith("otpauth://totp/"):
                        parsed = urlparse(qr_data)
                        params = parse_qs(parsed.query)
                        secret = params.get("secret", [None])[0]
                        account = parsed.path.split(":")[-1] if ":" in parsed.path else "user@example.com"
                        issuer = params.get("issuer", [None])[0] or "MyApp"
                        self.account_input.setText(account)
                        self.issuer_input.setText(issuer)
                    else:
                        raise ValueError("QR code is not a valid Base32 key or URI.")

            if not secret:
                raise ValueError("No valid secret found.")

            self.secret_input.setText(secret)
            account = self.account_input.text().strip() or "user@example.com"
            issuer = self.issuer_input.text().strip() or "MyApp"

            self.totp = pyotp.TOTP(secret)
            self.generate_qr(secret, account, issuer)
            self.update_totp()
            QMessageBox.information(self, "Success", "✓ Key loaded successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load key: {e}")

    def _copy_totp_code(self):
        """Copy current TOTP code to clipboard."""
        clipboard = QApplication.clipboard()
        code = self.totp_label.text()
        if code and code != "------" and code != "Invalid Secret" and code != "ERROR":
            clipboard.setText(code)
            QMessageBox.information(self, "Copied", f"Code '{code}' copied to clipboard!")
        else:
            QMessageBox.warning(self, "Error", "No valid code to copy.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = TOTPDialog()
    dialog.exec_()  # Modal

