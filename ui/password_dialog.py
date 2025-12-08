"""
Advanced password dialog with strength meter and verification.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QProgressBar, QMessageBox, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
import re
from config import ICON_PATH


class PasswordStrengthMeter:
    """Calculates password strength."""

    @staticmethod
    def calculate_strength(password):
        """
        Calculate password strength (0-100).

        Args:
            password (str): Password to evaluate

        Returns:
            tuple: (strength_score, strength_level, feedback_messages, color)
        """
        if not password:
            return 0, "Very Weak", ["Password is empty"], "#ff0000"

        score = 0
        feedback = []

        # Length checks
        if len(password) >= 8:
            score += 10
        else:
            feedback.append(f"Password should be at least 8 characters (currently {len(password)})")

        if len(password) >= 12:
            score += 10

        if len(password) >= 16:
            score += 10

        # Character variety checks
        has_lower = bool(re.search(r'[a-z]', password))
        has_upper = bool(re.search(r'[A-Z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password))

        if has_lower:
            score += 15
        else:
            feedback.append("Add lowercase letters (a-z)")

        if has_upper:
            score += 15
        else:
            feedback.append("Add uppercase letters (A-Z)")

        if has_digit:
            score += 15
        else:
            feedback.append("Add numbers (0-9)")

        if has_special:
            score += 15
        else:
            feedback.append("Add special characters (!@#$%^&*)")

        # Common patterns to avoid
        if re.search(r'(.)\1{2,}', password):  # Repeating characters
            score -= 10
            feedback.append("Avoid repeating characters")

        if re.search(r'(012|123|234|345|456|567|678|789|abc|bcd|cde)', password.lower()):
            score -= 5
            feedback.append("Avoid sequential characters")

        # Ensure score is between 0-100
        score = max(0, min(100, score))

        # Determine strength level and color
        if score < 20:
            level = "Very Weak"
            color = "#ff0000"
        elif score < 40:
            level = "Weak"
            color = "#ff6600"
        elif score < 60:
            level = "Fair"
            color = "#ffcc00"
        elif score < 80:
            level = "Good"
            color = "#99cc00"
        else:
            level = "Strong"
            color = "#00cc00"

        return score, level, feedback, color


class PasswordDialog(QDialog):
    """
    Advanced password setup/change dialog with strength meter.
    """

    password_set = pyqtSignal(str)  # Emitted when password is confirmed

    def __init__(self, parent=None, mode="setup", min_length=8):
        """
        Initialize password dialog.

        Args:
            parent: Parent widget
            mode: "setup" for new password, "change" for changing existing
            min_length: Minimum password length (default 8)
        """
        super().__init__(parent)
        self.mode = mode
        self.min_length = min_length
        self.confirmed_password = None
        self.password_input:QLineEdit | None = None
        self.show_password_cb:QCheckBox | None = None
        self.strength_label:QLabel | None = None
        self.strength_bar: QLabel | None = None
        self.strength_level_label:QLabel | None = None
        self.feedback_label:QLabel | None = None
        self.show_confirm_cb:QCheckBox | None = None
        self.confirm_button:QPushButton | None = None
        self.confirm_input:QLineEdit | None = None
        self.match_label:QLabel | None = None



        self.setWindowTitle("Master Password Setup" if mode == "setup" else "Change Master Password")
        self.setWindowIcon(QIcon(ICON_PATH))
        self.setModal(True)
        self.setMinimumWidth(500)

        self.init_ui()
        self.center_dialog()

    def init_ui(self):
        """Initialize user interface."""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title_label = QLabel("Create a Strong Master Password")
        title_font = QFont("Segoe UI", 12, QFont.Bold)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        # Instructions
        instructions = QLabel(
            "Your master password must have:\n"
            "• At least 8 characters\n"
            "• Mix of uppercase and lowercase letters\n"
            "• Numbers and special characters\n"
            "• No simple patterns"
        )
        instructions.setFont(QFont("Segoe UI", 9))
        instructions.setStyleSheet("color: #666; margin-bottom: 10px;")
        main_layout.addWidget(instructions)

        # --- Password Input Section ---
        password_label = QLabel("Master Password:")
        password_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        main_layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter a strong password...")
        self.password_input.setMinimumHeight(40)
        self.password_input.setFont(QFont("Segoe UI", 10))
        #noinspection PyUnresolvedReferences
        self.password_input.textChanged.connect(self.on_password_changed)
        main_layout.addWidget(self.password_input)

        # Show/Hide toggle
        self.show_password_cb = QCheckBox("Show Password")
        # noinspection PyUnresolvedReferences
        self.show_password_cb.stateChanged.connect(self.toggle_password_visibility)
        main_layout.addWidget(self.show_password_cb)

        # Strength Meter
        strength_label = QLabel("Password Strength:")
        strength_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        main_layout.addWidget(strength_label)

        self.strength_bar = QProgressBar()
        self.strength_bar.setMinimum(0)
        self.strength_bar.setMaximum(100)
        self.strength_bar.setValue(0)
        self.strength_bar.setMinimumHeight(25)  # Use setMinimumHeight instead of setHeight
        self.strength_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ccc;
                border-radius: 5px;
                background-color: #f0f0f0;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #ff0000;
                border-radius: 3px;
            }
        """)
        main_layout.addWidget(self.strength_bar)

        # Strength feedback
        strength_feedback_layout = QHBoxLayout()
        self.strength_level_label = QLabel("Very Weak")
        self.strength_level_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.strength_level_label.setStyleSheet("color: #ff0000;")
        strength_feedback_layout.addWidget(self.strength_level_label)
        strength_feedback_layout.addStretch()
        main_layout.addLayout(strength_feedback_layout)

        # Feedback text
        self.feedback_label = QLabel("")
        self.feedback_label.setFont(QFont("Segoe UI", 8))
        self.feedback_label.setStyleSheet("color: #666; margin-top: -5px;")
        self.feedback_label.setWordWrap(True)
        self.feedback_label.setMinimumHeight(50)
        main_layout.addWidget(self.feedback_label)

        # --- Confirm Password Section ---
        confirm_label = QLabel("Confirm Password:")
        confirm_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        main_layout.addWidget(confirm_label)

        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setPlaceholderText("Re-enter your password...")
        self.confirm_input.setMinimumHeight(40)
        self.confirm_input.setFont(QFont("Segoe UI", 10))
        # noinspection PyUnresolvedReferences
        self.confirm_input.textChanged.connect(self.on_confirm_changed)
        main_layout.addWidget(self.confirm_input)

        # Show/Hide toggle for confirm
        self.show_confirm_cb = QCheckBox("Show Confirmation")
        # noinspection PyUnresolvedReferences
        self.show_confirm_cb.stateChanged.connect(self.toggle_confirm_visibility)
        main_layout.addWidget(self.show_confirm_cb)

        # Match indicator
        self.match_label = QLabel("")
        self.match_label.setFont(QFont("Segoe UI", 9))
        self.match_label.setMinimumHeight(25)
        main_layout.addWidget(self.match_label)

        # Spacer
        main_layout.addSpacing(10)

        # --- Buttons ---
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.confirm_button = QPushButton("✓ Create Password")
        self.confirm_button.setMinimumHeight(40)
        self.confirm_button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.confirm_button.setCursor(Qt.PointingHandCursor)
        self.confirm_button.setEnabled(False)
        # noinspection PyUnresolvedReferences
        self.confirm_button.clicked.connect(self.confirm_password)
        self.confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover:!disabled {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #999999;
            }
        """)
        button_layout.addWidget(self.confirm_button)

        cancel_button = QPushButton("✕ Cancel")
        cancel_button.setMinimumHeight(40)
        cancel_button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        cancel_button.setCursor(Qt.PointingHandCursor)
        # noinspection PyUnresolvedReferences
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        button_layout.addWidget(cancel_button)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def on_password_changed(self):
        """Handle password input change."""
        password = self.password_input.text()
        score, level, feedback, color = PasswordStrengthMeter.calculate_strength(password)

        # Update strength bar
        self.strength_bar.setValue(score)
        self.strength_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #ccc;
                border-radius: 5px;
                background-color: #f0f0f0;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)

        # Update strength level
        self.strength_level_label.setText(level)
        self.strength_level_label.setStyleSheet(f"color: {color};")

        # Update feedback
        feedback_text = "\n".join([f"• {msg}" for msg in feedback]) if feedback else "✓ Password meets all requirements!"
        self.feedback_label.setText(feedback_text)

        # Check match with confirm field
        self.on_confirm_changed()

    def on_confirm_changed(self):
        """Handle confirm password change."""
        password = self.password_input.text()
        confirm = self.confirm_input.text()

        if not password or not confirm:
            self.match_label.setText("")
            self.confirm_button.setEnabled(False)
            return

        if password == confirm:
            score, level, _, _ = PasswordStrengthMeter.calculate_strength(password)

            # Check minimum requirements
            if len(password) < self.min_length:
                self.match_label.setText(f"✗ Password must be at least {self.min_length} characters")
                self.match_label.setStyleSheet("color: #ff6600;")
                self.confirm_button.setEnabled(False)
                return

            # Check strength requirement
            if score < 60:
                self.match_label.setText("✗ Password is not strong enough (needs at least 60% strength)")
                self.match_label.setStyleSheet("color: #ff6600;")
                self.confirm_button.setEnabled(False)
                return

            self.match_label.setText("✓ Passwords match and are strong!")
            self.match_label.setStyleSheet("color: #00cc00;")
            self.confirm_button.setEnabled(True)
        else:
            self.match_label.setText("✗ Passwords do not match")
            self.match_label.setStyleSheet("color: #ff0000;")
            self.confirm_button.setEnabled(False)

    def toggle_password_visibility(self):
        """Toggle password visibility."""
        if self.show_password_cb.isChecked():
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)

    def toggle_confirm_visibility(self):
        """Toggle confirm password visibility."""
        if self.show_confirm_cb.isChecked():
            self.confirm_input.setEchoMode(QLineEdit.Normal)
        else:
            self.confirm_input.setEchoMode(QLineEdit.Password)

    def confirm_password(self):
        """Confirm and validate password."""
        password = self.password_input.text()
        confirm = self.confirm_input.text()

        # Final validation
        if len(password) < self.min_length:
            QMessageBox.warning(self, "Weak Password",
                                f"Password must be at least {self.min_length} characters long.")
            return

        if password != confirm:
            QMessageBox.warning(self, "Mismatch", "Passwords do not match.")
            return

        # Check strength
        score, level, _, _ = PasswordStrengthMeter.calculate_strength(password)
        if score < 60:
            QMessageBox.warning(self, "Weak Password",
                                "Password is not strong enough. Please add more complexity.")
            return

        # Password valid
        self.confirmed_password = password
        # noinspection PyUnresolvedReferences
        self.password_set.emit(password)
        self.accept()

    def get_password(self):
        """Get the confirmed password."""
        return self.confirmed_password

    def center_dialog(self):
        """Center dialog on parent window."""
        if self.parent():
            parent_geometry = self.parent().frameGeometry()
            center_point = parent_geometry.center()
            self.move(center_point.x() - self.width() // 2,
                     center_point.y() - self.height() // 2)
        else:
            # Center on screen if no parent
            screen = self.screen()
            screen_geometry = screen.geometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)