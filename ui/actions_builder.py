"""
Actions and menu/toolbar builder.
"""
from PyQt5.QtWidgets import QAction, QToolBar, QMessageBox
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import QSize

class ActionsBuilder:
    """Creates and manages application actions."""
    
    def __init__(self, main_window, core):
        self.main_window = main_window
        self.core = core
        self.actions = {}
    
    def create_actions(self):
        """Create all actions."""
        self.actions['upload'] = QAction("📤 Upload QR Code", self.main_window)
        self.actions['upload'].setShortcut(QKeySequence("Ctrl+O"))
        self.actions['upload'].setStatusTip("Upload a QR code image")
        self.actions['upload'].triggered.connect(self.core.upload_qr)
        
        self.actions['save_qr'] = QAction("💾 Save QR Code", self.main_window)
        self.actions['save_qr'].setShortcut(QKeySequence("Ctrl+S"))
        self.actions['save_qr'].setStatusTip("Save current QR code")
        self.actions['save_qr'].triggered.connect(self.core.save_qr)
        
        self.actions['exit'] = QAction("🚪 Exit", self.main_window)
        self.actions['exit'].setShortcut(QKeySequence("Ctrl+Q"))
        self.actions['exit'].setStatusTip("Exit application")
        self.actions['exit'].triggered.connect(self.main_window.close)
        
        self.actions['refresh'] = QAction("🔄 Refresh List", self.main_window)
        self.actions['refresh'].setShortcut(QKeySequence("F5"))
        self.actions['refresh'].setStatusTip("Refresh profile list")
        self.actions['refresh'].triggered.connect(self.core.load_profiles)
        
        self.actions['delete'] = QAction("🗑️ Delete Profile", self.main_window)
        self.actions['delete'].setShortcut(QKeySequence("Delete"))
        self.actions['delete'].setStatusTip("Delete selected profile")
        self.actions['delete'].triggered.connect(self.core.delete_profile)
        
        self.actions['change_pw'] = QAction("🔐 Change Master Password", self.main_window)
        self.actions['change_pw'].setStatusTip("Change master password")
        self.actions['change_pw'].triggered.connect(self.core.change_master_password)
        
        self.actions['reset_key'] = QAction("🔑 Reset Master Key", self.main_window)
        self.actions['reset_key'].setStatusTip("Reset master encryption key")
        self.actions['reset_key'].triggered.connect(self.core.reset_master_key)
        
        self.actions['reset_vault'] = QAction("Reset Vault (Delete All Profiles)", self.main_window)
        self.actions['reset_vault'].triggered.connect(self.core.reset_vault)
        
        self.actions['lock'] = QAction("🔒 Lock Application", self.main_window)
        self.actions['lock'].setShortcut(QKeySequence("Ctrl+L"))
        self.actions['lock'].setStatusTip("Lock the application")
        self.actions['lock'].triggered.connect(self.core.lock_application)
        
        self.actions['about'] = QAction("ℹ️ About", self.main_window)
        self.actions['about'].setStatusTip("About this application")
        self.actions['about'].triggered.connect(self.show_about)
        
        self.actions['help'] = QAction("❓ Help", self.main_window)
        self.actions['help'].setShortcut(QKeySequence("F1"))
        self.actions['help'].setStatusTip("Show help documentation")
        self.actions['help'].triggered.connect(self.show_help)
        
        self.actions['manual_totp'] = QAction("Generate TOTP", self.main_window)
        self.actions['manual_totp'].setStatusTip("Generate a TOTP code manually")
        self.actions['manual_totp'].triggered.connect(self.core.manual_totp_prompt)
    
    def create_menu_bar(self):
        """Create menu bar."""
        menubar = self.main_window.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("📁 &File")
        file_menu.addAction(self.actions['upload'])
        file_menu.addAction(self.actions['save_qr'])
        file_menu.addSeparator()
        file_menu.addAction(self.actions['exit'])
        
        # Profile Menu
        profile_menu = menubar.addMenu("👤 &Profile")
        profile_menu.addAction(self.actions['refresh'])
        profile_menu.addAction(self.actions['delete'])
        
        # Security Menu
        security_menu = menubar.addMenu("🔒 &Security")
        security_menu.addAction(self.actions['change_pw'])
        security_menu.addAction(self.actions['reset_key'])
        security_menu.addSeparator()
        security_menu.addAction(self.actions['lock'])
        
        # Vault Menu
        vault_menu = menubar.addMenu("🗃️ &Vault")
        vault_menu.addAction(self.actions['reset_vault'])
        
        # TOTP Menu
        totp_menu = menubar.addMenu("⏱️ &TOTP")
        totp_menu.addAction(self.actions['manual_totp'])
        
        # Help Menu
        help_menu = menubar.addMenu("❓ &Help")
        help_menu.addAction(self.actions['help'])
        help_menu.addSeparator()
        help_menu.addAction(self.actions['about'])
    
    def create_toolbar(self):
        """Create toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.main_window.addToolBar(toolbar)
        
        toolbar.addAction(self.actions['upload'])
        toolbar.addAction(self.actions['save_qr'])
        toolbar.addSeparator()
        toolbar.addAction(self.actions['refresh'])
        toolbar.addAction(self.actions['delete'])
        toolbar.addSeparator()
        toolbar.addAction(self.actions['lock'])
    
    def show_about(self):
        """Show about dialog."""
        from config import APP_NAME, APP_VERSION
        QMessageBox.about(self.main_window, "About TOTP Manager",
                          f"<h3>{APP_NAME}</h3>"
                          "<p>A secure TOTP code manager with encryption.</p>"
                          f"<p>Version {APP_VERSION}</p>")
    
    def show_help(self):
        """Show help dialog."""
        QMessageBox.information(self.main_window, "Help",
                                "<h3>Quick Help</h3>"
                                "<p><b>Ctrl+O:</b> Upload QR Code</p>"
                                "<p><b>Ctrl+S:</b> Save QR Code</p>"
                                "<p><b>F5:</b> Refresh Profiles</p>"
                                "<p><b>Delete:</b> Delete Profile</p>"
                                "<p><b>Ctrl+L:</b> Lock Application</p>"
                                "<p><b>Ctrl+Q:</b> Exit</p>")
