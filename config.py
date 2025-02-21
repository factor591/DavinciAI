import logging
import os

# Logging configuration
LOG_FILE = 'drone_video_editor.log'
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

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
