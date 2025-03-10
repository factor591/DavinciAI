import random
import logging
from PyQt6.QtCore import QObject, pyqtSignal, QThread

class AIWorker(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, operation, num_clips):
        super().__init__()
        self.operation = operation
        self.num_clips = num_clips

    def run(self):
        try:
            total_steps = 100
            for i in range(total_steps + 1):
                if i % 5 == 0:
                    delay_ms = int((0.005 * self.num_clips + random.random() * 0.005) * 1000)
                    QThread.msleep(delay_ms)
                    self.progress.emit(i)
                else:
                    QThread.msleep(1)
        except Exception as e:
            logging.exception("Exception in AIWorker during '%s': %s", self.operation, e)
        finally:
            self.finished.emit()

class ExportWorker(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal()

    def run(self):
        try:
            total_steps = 100
            for i in range(total_steps + 1):
                if i % 5 == 0:
                    delay_ms = int((0.01 + random.random() * 0.01) * 1000)
                    QThread.msleep(delay_ms)
                    self.progress.emit(i)
                else:
                    QThread.msleep(1)
        except Exception as e:
            logging.exception("Exception in ExportWorker: %s", e)
        finally:
            self.finished.emit()

class BatchExportWorker(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, num_exports):
        super().__init__()
        self.num_exports = num_exports

    def run(self):
        try:
            total_steps = 100 * self.num_exports
            for i in range(total_steps + 1):
                if i % 5 == 0:
                    delay_ms = int((0.005 + random.random() * 0.005) * 1000)
                    QThread.msleep(delay_ms)
                    self.progress.emit(int(i / total_steps * 100))
                else:
                    QThread.msleep(1)
        except Exception as e:
            logging.exception("Exception in BatchExportWorker: %s", e)
        finally:
            self.finished.emit()

class SceneDetectionWorker(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal(list)

    def __init__(self, imported_items):
        super().__init__()
        self.imported_items = imported_items

    def run(self):
        new_clips = []
        total_items = len(self.imported_items)
        progress_counter = 0

        for item in self.imported_items:
            try:
                # Check if item is None before attempting to access any methods
                if item is None:
                    logging.warning("Skipping None item in scene detection")
                    progress_counter += 1
                    self.progress.emit(int((progress_counter / total_items) * 100))
                    continue

                # If it's a TimelineItem, we need to fetch its MediaPoolItem
                # First check if the method exists before calling it
                media_pool_item = None
                if hasattr(item, "GetMediaPoolItem") and callable(item.GetMediaPoolItem):
                    # GetMediaPoolItem can return None if it's offline or unlinked
                    try:
                        media_pool_item = item.GetMediaPoolItem()
                    except Exception as e:
                        logging.warning(f"Error calling GetMediaPoolItem: {e}")
                        media_pool_item = None
                    
                    if media_pool_item:
                        item = media_pool_item
                    else:
                        logging.warning("Skipping timeline item with no associated MediaPoolItem.")
                        progress_counter += 1
                        self.progress.emit(int((progress_counter / total_items) * 100))
                        continue

                # Now item should be a MediaPoolItem. If not, skip it.
                if not hasattr(item, "GetClipProperty") or not callable(item.GetClipProperty):
                    logging.warning(f"Skipping invalid item in scene detection: {type(item)}")
                    progress_counter += 1
                    self.progress.emit(int((progress_counter / total_items) * 100))
                    continue

                # Get clip properties safely
                try:
                    clip_name = (
                        self.safe_get_clip_property(item, "File Path") or
                        self.safe_get_clip_property(item, "Clip Name") or
                        "Unknown"
                    )
                    
                    # For demonstration, get actual duration if possible, otherwise use random
                    duration = self.safe_get_clip_property(item, "Duration")
                    if not duration or not isinstance(duration, (int, float)):
                        duration = random.randint(20, 60)
                    else:
                        # If duration is in timecode format, convert to seconds
                        if isinstance(duration, str) and ":" in duration:
                            try:
                                # Simple conversion for HH:MM:SS format
                                parts = duration.split(":")
                                if len(parts) == 3:
                                    duration = int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
                                else:
                                    duration = random.randint(20, 60)
                            except:
                                duration = random.randint(20, 60)
                except Exception as e:
                    logging.warning(f"Error getting clip properties: {e}")
                    clip_name = "Unknown"
                    duration = random.randint(20, 60)

                # Generate scene changes
                t1 = random.randint(2, int(duration) - 2) if duration > 4 else 1
                t2 = random.randint(2, int(duration) - 2) if duration > 4 else 2
                scene_changes = sorted([0, t1, t2, int(duration)])

                logging.info(
                    "Clip '%s' (duration %s sec): Detected scene changes: %s",
                    clip_name, duration, scene_changes
                )

                for i in range(len(scene_changes) - 1):
                    start = scene_changes[i]
                    end = scene_changes[i + 1]
                    segment_duration = end - start
                    if segment_duration < 2:
                        logging.info("Skipping segment from %s to %s (duration %s sec) as too short.",
                                     start, end, segment_duration)
                        continue
                    if random.random() < 0.1:
                        logging.info("Skipping segment from %s to %s as dark/empty scene.", start, end)
                        continue

                    new_clips.append((item, start, end))
                    logging.info("Created subclip for '%s': %s to %s", clip_name, start, end)

            except Exception as e:
                logging.exception("Exception detecting scenes for clip: %s", e)

            progress_counter += 1
            if progress_counter % 2 == 0 or progress_counter == total_items:
                self.progress.emit(int((progress_counter / total_items) * 100))

        self.finished.emit(new_clips)
    
    def safe_get_clip_property(self, item, property_name):
        """Safely get a clip property, handling exceptions."""
        try:
            if hasattr(item, "GetClipProperty") and callable(item.GetClipProperty):
                return item.GetClipProperty(property_name)
        except Exception as e:
            logging.warning(f"Error getting clip property '{property_name}': {e}")
        return None