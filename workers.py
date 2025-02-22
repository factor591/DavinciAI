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
                # Use QThread.msleep for non-blocking delay.
                delay_ms = int((0.005 * self.num_clips + random.random() * 0.005) * 1000)
                QThread.msleep(delay_ms)
                self.progress.emit(i)
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
                delay_ms = int((0.01 + random.random() * 0.01) * 1000)
                QThread.msleep(delay_ms)
                self.progress.emit(i)
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
                delay_ms = int((0.005 + random.random() * 0.005) * 1000)
                QThread.msleep(delay_ms)
                self.progress.emit(int(i / total_steps * 100))
        except Exception as e:
            logging.exception("Exception in BatchExportWorker: %s", e)
        finally:
            self.finished.emit()

class SceneDetectionWorker(QObject):
    progress = pyqtSignal(int)
    # Emits a list of subclip tuples: (MediaPoolItem, start, end)
    finished = pyqtSignal(list)

    def __init__(self, imported_items):
        super().__init__()
        self.imported_items = imported_items

    def run(self):
        new_clips = []
        total_items = len(self.imported_items)
        progress_counter = 0
        for item in self.imported_items:
            if not hasattr(item, "GetClipProperty"):
                logging.warning("Skipping invalid item in scene detection: %s", type(item))
                progress_counter += 1
                self.progress.emit(int((progress_counter / total_items) * 100))
                continue

            try:
                clip_name = (
                    item.GetClipProperty("File Path")
                    or item.GetClipProperty("Clip Name")
                    or "Unknown"
                )
                # For demonstration, random duration between 20 and 60 seconds
                duration = random.randint(20, 60)
                if duration > 4:
                    t1 = random.randint(2, duration - 2)
                    t2 = random.randint(2, duration - 2)
                    scene_changes = sorted([0, t1, t2, duration])
                else:
                    scene_changes = [0, duration]
                logging.info(
                    "Clip '%s' (duration %s sec): Detected scene changes: %s",
                    clip_name, duration, scene_changes
                )
                for i in range(len(scene_changes) - 1):
                    start = scene_changes[i]
                    end = scene_changes[i + 1]
                    segment_duration = end - start
                    if segment_duration < 2:
                        logging.info(
                            "Skipping segment from %s to %s (duration %s sec) as too short.",
                            start, end, segment_duration
                        )
                        continue
                    if random.random() < 0.1:
                        logging.info(
                            "Skipping segment from %s to %s as dark/empty scene.",
                            start, end
                        )
                        continue
                    new_clips.append((item, start, end))
                    logging.info("Created subclip for '%s': %s to %s", clip_name, start, end)
            except Exception as e:
                logging.exception("Error processing clip %s: %s", item, e)
            progress_counter += 1
            self.progress.emit(int((progress_counter / total_items) * 100))

        self.finished.emit(new_clips)
