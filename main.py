"""
Entry point for TokenX TOTP Manager application.
"""
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QFile, QTextStream
from config import THEME_PATH, APP_NAME
from ui.main_window import TOTPManager
import resources_rc
_ = resources_rc

def main():
    app = QApplication(sys.argv)
    
    # Load theme
    file = QFile(THEME_PATH)
    if file.open(QFile.ReadOnly | QFile.Text):
        stream = QTextStream(file)
        app.setStyleSheet(stream.readAll())
    
    window = TOTPManager()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
