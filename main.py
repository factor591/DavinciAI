import sys
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox

from ui import DroneVideoEditor
from backend import ResolveController
from config import DEFAULT_SETTINGS

def main():
    # Attempt to initialize ResolveController
    try:
        backend = ResolveController()
    except Exception as e:
        logging.critical("Fatal error initializing backend: %s", e)
        # We need a QApplication to show message boxes, so create it here:
        app = QApplication(sys.argv)
        QMessageBox.critical(
            None, 
            "Resolve Error",
            "Cannot initialize DaVinci Resolve.\n"
            "Check if DaVinci Resolve is running or if fusionscript.dll is present."
        )
        sys.exit(1)

    # If successful, proceed with the main application
    app = QApplication(sys.argv)
    editor = DroneVideoEditor(backend, DEFAULT_SETTINGS)
    editor.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
