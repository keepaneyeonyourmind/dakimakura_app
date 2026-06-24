import sys
from PyQt6.QtWidgets import QApplication
from main_window import DakimakuraApp

# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = DakimakuraApp()

    window.show()

    sys.exit(app.exec())