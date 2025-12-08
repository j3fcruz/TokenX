"""
Main window implementation for TokenX TOTP Manager.
"""
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QTimer, QEvent
import time

from config import APP_NAME, ICON_PATH, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT
from ui.ui_builder import UIBuilder
from core.manager import TOTPManagerCore
from services.auth_service import AuthService
from PyQt5.QtGui import QIcon


class TOTPManager(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"🔐 {APP_NAME}")
        self.setWindowIcon(QIcon(ICON_PATH))
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        
        # Core attributes
        self.last_activity_time = time.time()
        
        # Initialize services
        self.auth_service = AuthService()
        self.core = None
        
        # UI Builder
        self.ui_builder = None
        self.totp_timer:QTimer | None = None
        self.idle_timer:QTimer | None = None
        self.clipboard_timer:QTimer | None = None
        
        # Status bar
        from PyQt5.QtWidgets import QStatusBar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Timers
        self.setup_timers()
        
        # Build UI
        self.build_ui()
        
        # Authenticate
        self.authenticate_master()
    
    def setup_timers(self):
        """Initialize all timers."""
        self.totp_timer = QTimer()
        #noinspection PyUnresolvedReferences
        self.totp_timer.timeout.connect(self.on_refresh_totps)
        self.totp_timer.start(1000)
        
        self.idle_timer = QTimer()
        # noinspection PyUnresolvedReferences
        self.idle_timer.timeout.connect(self.on_check_idle)
        self.idle_timer.start(10_000)
        
        self.clipboard_timer = QTimer()
        # noinspection PyUnresolvedReferences
        self.clipboard_timer.timeout.connect(self.on_check_clipboard)
        self.clipboard_timer.start(2000)
    
    def build_ui(self):
        """Build user interface."""
        self.ui_builder = UIBuilder(self)
        self.ui_builder.build()
    
    def authenticate_master(self):
        """Authenticate master password/key."""
        self.auth_service.authenticate()
        self.core = TOTPManagerCore(
            self.auth_service.master_pw,
            self.auth_service.master_key,
            self.ui_builder
        )
        self.core.load_profiles()
    
    def on_refresh_totps(self):
        """Refresh TOTP codes."""
        if self.core:
            self.core.refresh_totps()
    
    def on_check_idle(self):
        """Check idle timeout."""
        if self.core:
            self.core.check_idle(self.last_activity_time)
    
    def on_check_clipboard(self):
        """Check clipboard for OTP URI."""
        if self.core:
            self.core.check_clipboard()
    
    def event(self, event):
        """Handle events for activity tracking."""
        if event.type() in (QEvent.MouseMove, QEvent.KeyPress):
            self.last_activity_time = time.time()
        return super().event(event)