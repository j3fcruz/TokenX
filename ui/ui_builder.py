"""
UI Builder - constructs all UI elements.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt
from config import QR_CODE_SIZE


class UIBuilder:
    """Builds the main UI."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.label = None
        self.profile_table = None
        self.totp_label = None
        self.qr_label = None
        self.status_label = None
    
    def build(self):
        """Build entire UI."""
        central_widget = QWidget()
        self.main_window.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        self._build_header(main_layout)
        self._build_profile_table(main_layout)
        self._build_status_label(main_layout)
        self._build_bottom_section(main_layout)
    
    def _build_header(self, layout):
        """Build header label."""
        self.label = QLabel("🔄 Select a profile or upload QR code")
        self.label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
    
    def _build_profile_table(self, layout):
        """Build profile table."""
        profile_group = QGroupBox("📋 Stored Profiles")
        profile_group.setFont(QFont("Segoe UI", 10, QFont.Bold))
        profile_layout = QVBoxLayout()
        
        self.profile_table = QTableWidget(0, 2)
        self.profile_table.setHorizontalHeaderLabels(["Profile Name", "TOTP Code"])
        header = self.profile_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.profile_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.profile_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.profile_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.profile_table.verticalHeader().setVisible(False)
        self.profile_table.setAlternatingRowColors(True)
        
        profile_layout.addWidget(self.profile_table)
        profile_group.setLayout(profile_layout)
        layout.addWidget(profile_group, 3)
    
    def _build_status_label(self, layout):
        """Build status label."""
        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Segoe UI", 20, QFont.Normal))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                background-color: #333333;
                border-radius: 6px;
                padding: 6px;
            }
        """)
        layout.addWidget(self.status_label)
    
    def _build_bottom_section(self, layout):
        """Build TOTP and QR code sections."""
        bottom_layout = QHBoxLayout()
        
        # TOTP Group
        totp_group = QGroupBox("⏱️ Current TOTP Code")
        totp_group.setFont(QFont("Segoe UI", 20, QFont.Bold))
        totp_layout = QVBoxLayout()
        self.totp_label = QLabel("------")
        self.totp_label.setFont(QFont("Consolas", 20, QFont.Bold))
        self.totp_label.setAlignment(Qt.AlignCenter)
        self.totp_label.setStyleSheet("""
            QLabel {
                color: #39ff14;
                padding: 20px;
                background-color: #1e1e1e;
                border-radius: 8px;
                border: 2px solid #39ff14;
            }
        """)
        totp_layout.addWidget(self.totp_label)
        totp_group.setLayout(totp_layout)
        bottom_layout.addWidget(totp_group, 1)
        
        # QR Group
        qr_group = QGroupBox("📷 QR Code Preview")
        qr_group.setFont(QFont("Segoe UI", 10, QFont.Bold))
        qr_layout = QVBoxLayout()
        self.qr_label = QLabel("No QR Code")
        self.qr_label.setFixedSize(QR_CODE_SIZE, QR_CODE_SIZE)
        self.qr_label.setStyleSheet("""
            QLabel {
                border: 2px solid #ccc;
                background-color: white;
                border-radius: 8px;
            }
        """)
        self.qr_label.setAlignment(Qt.AlignCenter)
        qr_layout.addWidget(self.qr_label, 0, Qt.AlignCenter)
        qr_group.setLayout(qr_layout)
        bottom_layout.addWidget(qr_group, 1)
        
        layout.addLayout(bottom_layout, 2)