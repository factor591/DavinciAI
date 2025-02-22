import logging
import os

# Enhanced logging configuration with function names and timestamps.
LOG_FILE = 'drone_video_editor.log'
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

## ADDED: Filter to remove duplicate log messages
class NoDuplicateFilter(logging.Filter):
    def __init__(self):
        super().__init__()
        self.last_msg = None

    def filter(self, record):
        current_msg = record.getMessage()
        if current_msg == self.last_msg:
            return False
        self.last_msg = current_msg
        return True

logger = logging.getLogger('')
logger.addFilter(NoDuplicateFilter())

# Default settings for the application
DEFAULT_SETTINGS = {
    "ai_processing_level": "Medium",
    "lut_selection": "Default",
    "export_resolution": "1080p",
    "export_format": "MP4",
    "auto_volume": False,
    "noise_gate_eq": False,
    "music_selection": "None"
}
