"""
Configuration constants for TokenX TOTP Manager.
"""
import os

# Application
APP_NAME = "TokenX TOTP Manager"
APP_VERSION = "1.0"
ICON_PATH = ":/assets/icons/icon.png"
THEME_PATH = ":/assets/themes/calm_edition_theme.qss"

# Directories
PROFILE_DIR = "profiles"
os.makedirs(PROFILE_DIR, exist_ok=True)

# Files
MASTER_KEY_FILE = os.path.join(PROFILE_DIR, ".master")

# Security
IDLE_TIMEOUT_SECS = 180
CLIPBOARD_CHECK_INTERVAL_MS = 2000
TOTP_REFRESH_INTERVAL_MS = 1000
IDLE_CHECK_INTERVAL_MS = 10_000

# UI
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 700
QR_CODE_SIZE = 250
QR_PREVIEW_SIZE = (200, 200)

