import sys
from PyQt6.QtWidgets import QApplication
from ui import DroneVideoEditor
from backend import ResolveController
from config import DEFAULT_SETTINGS
import logging

def main():
    try:
        backend = ResolveController()
    except Exception as e:
        logging.critical("Fatal error initializing backend: %s", e)
        sys.exit("A fatal error occurred. Check the log for details.")

    app = QApplication(sys.argv)
    editor = DroneVideoEditor(backend, DEFAULT_SETTINGS)
    editor.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
