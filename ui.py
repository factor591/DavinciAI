import sys
import os
import json
import logging
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QGridLayout, QFrame, QProgressBar, QDialog, QDialogButtonBox,
    QComboBox, QFormLayout, QCheckBox, QMessageBox, QSpinBox,
    QScrollArea
)
from PyQt6.QtGui import QDrag
from PyQt6.QtCore import QMimeData, Qt, QUrl, QThread
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

# Settings Dialog
class SettingsDialog(QDialog):
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(300, 400)
        self.settings = current_settings.copy()

        layout = QFormLayout(self)

        self.ai_level_combo = QComboBox(self)
        self.ai_level_combo.addItems(["Low", "Medium", "High"])
        self.ai_level_combo.setCurrentText(self.settings.get("ai_processing_level", "Medium"))
        layout.addRow("AI Processing Level:", self.ai_level_combo)

        self.lut_combo = QComboBox(self)
        self.lut_combo.addItems(["Default", "Cinematic", "Vintage"])
        self.lut_combo.setCurrentText(self.settings.get("lut_selection", "Default"))
        layout.addRow("LUT Selection:", self.lut_combo)

        self.resolution_combo = QComboBox(self)
        self.resolution_combo.addItems(["1080p", "4K", "8K"])
        if isinstance(self.settings.get("export_resolution"), dict):
            self.resolution_combo.setCurrentText("1080p")
        else:
            self.resolution_combo.setCurrentText(self.settings.get("export_resolution", "1080p"))
        layout.addRow("Export Resolution Preset:", self.resolution_combo)

        self.custom_resolution_checkbox = QCheckBox("Use Custom Resolution", self)
        layout.addRow("", self.custom_resolution_checkbox)
        custom_res_layout = QHBoxLayout()
        self.width_spinbox = QSpinBox(self)
        self.width_spinbox.setRange(100, 7680)
        self.width_spinbox.setValue(1920)
        self.width_spinbox.setEnabled(False)
        custom_res_layout.addWidget(QLabel("Width:"))
        custom_res_layout.addWidget(self.width_spinbox)
        self.height_spinbox = QSpinBox(self)
        self.height_spinbox.setRange(100, 4320)
        self.height_spinbox.setValue(1080)
        self.height_spinbox.setEnabled(False)
        custom_res_layout.addWidget(QLabel("Height:"))
        custom_res_layout.addWidget(self.height_spinbox)
        layout.addRow("Custom Resolution:", custom_res_layout)
        self.custom_resolution_checkbox.toggled.connect(
            lambda checked: (
                self.width_spinbox.setEnabled(checked),
                self.height_spinbox.setEnabled(checked)
            )
        )

        audio_header = QLabel("Audio Enhancements", self)
        audio_header.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addRow(audio_header)
        self.auto_volume_checkbox = QCheckBox("Auto Volume Balancing", self)
        self.auto_volume_checkbox.setChecked(self.settings.get("auto_volume", False))
        layout.addRow("", self.auto_volume_checkbox)
        self.noise_gate_checkbox = QCheckBox("Noise Gate & EQ Adjustments", self)
        self.noise_gate_checkbox.setChecked(self.settings.get("noise_gate_eq", False))
        layout.addRow("", self.noise_gate_checkbox)

        self.music_combo = QComboBox(self)
        self.music_combo.addItems(["None", "Track 1", "Track 2", "Track 3"])
        self.music_combo.setCurrentText(self.settings.get("music_selection", "None"))
        layout.addRow("Music Selection:", self.music_combo)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)

    def getSettings(self):
        if self.custom_resolution_checkbox.isChecked():
            resolution = {"width": self.width_spinbox.value(), "height": self.height_spinbox.value()}
        else:
            resolution = self.resolution_combo.currentText()
        return {
            "ai_processing_level": self.ai_level_combo.currentText(),
            "lut_selection": self.lut_combo.currentText(),
            "export_resolution": resolution,
            "export_format": "MP4",
            "auto_volume": self.auto_volume_checkbox.isChecked(),
            "noise_gate_eq": self.noise_gate_checkbox.isChecked(),
            "music_selection": self.music_combo.currentText()
        }

# Export Dialog
class ExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Settings")
        self.resize(350, 250)

        layout = QFormLayout(self)

        self.format_combo = QComboBox(self)
        self.format_combo.addItems(["MP4", "MOV", "AVI", "ProRes", "H.265"])
        layout.addRow("Output Format:", self.format_combo)

        self.size_label = QLabel("Estimated Size: N/A", self)
        layout.addRow(self.size_label)

        self.directory_label = QLabel(os.path.join(os.getcwd(), "Exports"), self)
        self.dir_button = QPushButton("Select Export Directory", self)
        self.dir_button.clicked.connect(self.selectDirectory)
        layout.addRow("Export Location:", self.directory_label)
        layout.addWidget(self.dir_button)

        self.batch_export_checkbox = QCheckBox("Batch Export Clips", self)
        layout.addRow("", self.batch_export_checkbox)

        self.watermark_checkbox = QCheckBox("Apply Watermark", self)
        layout.addRow("", self.watermark_checkbox)
        watermark_layout = QHBoxLayout()
        self.watermark_button = QPushButton("Select Watermark Image", self)
        self.watermark_button.clicked.connect(self.selectWatermark)
        self.watermark_label = QLabel("None", self)
        watermark_layout.addWidget(self.watermark_button)
        watermark_layout.addWidget(self.watermark_label)
        layout.addRow("Watermark:", watermark_layout)

        self.format_combo.currentTextChanged.connect(self.updateEstimate)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)

        self.updateEstimate(self.format_combo.currentText())

    def selectDirectory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Export Directory", os.getcwd())
        if directory:
            self.directory_label.setText(directory)
            self.updateEstimate(self.format_combo.currentText())

    def selectWatermark(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Watermark Image", "", "Image Files (*.png *.jpg *.bmp)")
        if file_path:
            self.watermark_label.setText(file_path)

    def updateEstimate(self, fmt):
        resolution = "1080p"
        if self.parent() and hasattr(self.parent(), 'settings'):
            resolution = self.parent().settings.get("export_resolution", "1080p")
        if isinstance(resolution, dict):
            width = resolution.get("width", 1920)
            height = resolution.get("height", 1080)
        else:
            presets = {
                "1080p": (1920, 1080),
                "4K": (3840, 2160),
                "8K": (7680, 4320)
            }
            width, height = presets.get(resolution, (1920, 1080))
        num_clips = 1
        if self.parent() and hasattr(self.parent(), 'preview_widgets'):
            num_clips = len(self.parent().preview_widgets) or 1
        base_sizes = {
            "MP4": 5,
            "MOV": 6,
            "AVI": 5.5,
            "ProRes": 7,
            "H.265": 4
        }
        base_size = base_sizes.get(fmt, 5)
        est_size = num_clips * base_size * (width * height) / (1920 * 1080)
        self.size_label.setText(f"Estimated Size: {est_size:.1f} MB")

    def getExportSettings(self):
        return {
            "export_format": self.format_combo.currentText(),
            "estimated_size": self.size_label.text().split(": ")[1],
            "export_location": self.directory_label.text(),
            "batch_export": self.batch_export_checkbox.isChecked(),
            "watermark": self.watermark_label.text() if self.watermark_checkbox.isChecked() else None
        }

# Video Preview Widget with Drag & Drop
class VideoPreviewWidget(QFrame):
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setFixedSize(150, 100)
        self.setStyleSheet("""
            QFrame {
                background-color: #506680;
                border-radius: 10px;
            }
        """)
        self.setAcceptDrops(True)
        self._drag_start_position = None

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.video_widget = QVideoWidget()
        self.video_widget.setFixedSize(150, 100)

        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setSource(QUrl.fromLocalFile(file_path))

        self.layout.addWidget(self.video_widget)

        self.remove_button = QPushButton("×", self)
        self.remove_button.setFixedSize(20, 20)
        self.remove_button.setStyleSheet("""
            QPushButton {
                background-color: #FF0000;
                color: white;
                font-weight: bold;
                border-radius: 10px;
                font-size: 16px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #CC0000;
            }
        """)
        self.remove_button.setToolTip("Remove this clip")
        self.remove_button.move(125, 5)

        self.enterEvent = self.on_mouse_enter
        self.leaveEvent = self.on_mouse_leave

    def on_mouse_enter(self, event):
        self.media_player.play()

    def on_mouse_leave(self, event):
        self.media_player.pause()
        self.media_player.setPosition(0)

    def cleanup(self):
        self.media_player.stop()
        self.media_player = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_position = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            if (event.pos() - self._drag_start_position).manhattanLength() > 10:
                drag = QDrag(self)
                mimeData = QMimeData()
                mimeData.setData("application/x-clipwidget", b"")
                drag.setMimeData(mimeData)
                pixmap = self.grab()
                drag.setPixmap(pixmap)
                main_window = self.window()
                if hasattr(main_window, 'drag_source'):
                    main_window.drag_source = self
                drag.exec()
        super().mouseMoveEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-clipwidget"):
            event.acceptProposedAction()

    def dropEvent(self, event):
        main_window = self.window()
        if hasattr(main_window, 'drag_source') and main_window.drag_source and main_window.drag_source != self:
            main_window.reorderClips(main_window.drag_source, self)
            main_window.drag_source = None
        event.acceptProposedAction()

# Main Application Widget
class DroneVideoEditor(QWidget):
    def __init__(self, backend, settings):
        super().__init__()
        self.backend = backend
        self.settings = settings.copy()
        self.preview_widgets = []
        self.imported_items = []  # Contains valid MediaPoolItem objects
        self.drag_source = None
        self.clip_count = 0
        self.initUI()

    def createStyledButton(self, text, function):
        button = QPushButton(text, self)
        button.clicked.connect(function)
        button.setStyleSheet("""
            QPushButton {
                background-color: #324A5E;
                border-radius: 8px;
                padding: 8px;
                color: white;
            }
            QPushButton:hover {
                background-color: #3A5875;
            }
        """)
        return button

    def initUI(self):
        self.setWindowTitle("Drone Video Editor")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("""
            QWidget {
                background-color: #1E2A38;
                color: white;
                font-size: 14px;
            }
        """)
        self.setAcceptDrops(True)
        main_layout = QVBoxLayout()

        menubar_layout = QHBoxLayout()
        save_button = self.createStyledButton("Save Project", self.saveProject)
        load_button = self.createStyledButton("Load Project", self.loadProject)
        settings_button = self.createStyledButton("Settings", self.openSettings)
        menubar_layout.addWidget(save_button)
        menubar_layout.addWidget(load_button)
        menubar_layout.addStretch()
        menubar_layout.addWidget(settings_button)
        main_layout.addLayout(menubar_layout)

        self.drop_area = QFrame(self)
        self.drop_area.setStyleSheet("""
            QFrame {
                background-color: #2B3B4E;
                border-radius: 15px;
                border: 2px dashed #506680;
            }
        """)
        self.drop_area.setFixedHeight(220)
        drop_layout = QVBoxLayout(self.drop_area)

        self.plus_label = QLabel("+", self.drop_area)
        self.plus_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.plus_label.setStyleSheet("font-size: 80px; font-weight: bold; color: rgba(255, 255, 255, 0.5);")
        drop_layout.addWidget(self.plus_label)

        self.scroll_area = QScrollArea(self.drop_area)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #2B3B4E;
            }
        """)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.clip_layout = QGridLayout(self.scroll_content)
        self.clip_layout.setSpacing(10)
        self.scroll_content.setLayout(self.clip_layout)

        self.scroll_area.setWidget(self.scroll_content)
        drop_layout.addWidget(self.scroll_area)

        main_layout.addWidget(self.drop_area)

        button_grid = QGridLayout()
        button_grid.setSpacing(10)
        buttons = [
            ("Import Footage", self.importFootage),
            ("Create Timeline", self.createTimeline),
            ("AI Auto Color", self.autoColorGrade),
            ("AI Smart Reframe", self.applySmartReframe),
            ("AI Scene Detection", self.detectScenes),
            ("AI Noise Reduction", self.applyNoiseReduction),
            ("AI Voice Isolation", self.applyVoiceIsolation),
            ("Smart Highlight", self.smartHighlight),
            ("AI Audio Enhancements", self.aiAudioEnhancements),
            ("AI Music Sync", self.aiMusicSync),
            ("Fusion Automation", self.applyFusionEffects)
        ]
        for i, (text, func) in enumerate(buttons):
            btn = self.createStyledButton(text, func)
            button_grid.addWidget(btn, i // 3, i % 3)
        button_widget = QWidget()
        button_widget.setLayout(button_grid)
        main_layout.addWidget(button_widget)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        export_layout = QHBoxLayout()
        self.export_button = self.createStyledButton("Export Video", self.exportVideo)
        self.export_button.setFixedWidth(300)
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #FF5733;
                border-radius: 8px;
                padding: 16px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background-color: #FF6B4A;
            }
        """)
        export_layout.addStretch()
        export_layout.addWidget(self.export_button)
        export_layout.addStretch()
        main_layout.addLayout(export_layout)

        self.setLayout(main_layout)

    def addClipPreview(self, file_path):
        self.plus_label.hide()
        preview_widget = VideoPreviewWidget(file_path)
        preview_widget.remove_button.clicked.connect(lambda: self.removeClip(preview_widget))
        row = self.clip_count // 4
        col = self.clip_count % 4
        self.clip_layout.addWidget(preview_widget, row, col)
        self.preview_widgets.append(preview_widget)
        self.clip_count += 1
        logging.info("Added clip: %s", file_path)

    def removeClip(self, preview_widget):
        try:
            preview_widget.cleanup()
            self.clip_layout.removeWidget(preview_widget)
            self.preview_widgets.remove(preview_widget)
            preview_widget.deleteLater()
            self.clip_count -= 1
            logging.info("Removed a clip.")
        except Exception as e:
            logging.exception("Error removing clip: %s", e)
            QMessageBox.critical(self, "Removal Error", "Failed to remove the clip properly.")
        if self.clip_count == 0:
            self.plus_label.show()

    def importFootage(self):
        try:
            file_paths, _ = QFileDialog.getOpenFileNames(
                self, "Select Drone Footage", "",
                "Video Files (*.mp4 *.mov *.avi)"
            )
            if file_paths:
                new_items = self.backend.import_media(file_paths)
                if new_items:
                    for item in new_items:
                        try:
                            logging.info("Imported item type: %s, name: %s", type(item),
                                         item.GetName() if hasattr(item, "GetName") else "Unknown")
                        except Exception as e:
                            logging.warning("Error retrieving name for item: %s", e)
                    self.imported_items.extend(new_items)
                else:
                    logging.info("No new media items imported.")
                for file_path in file_paths:
                    self.addClipPreview(file_path)
            else:
                logging.info("Import cancelled or no files selected.")
        except Exception as e:
            logging.exception("Error importing footage: %s", e)
            QMessageBox.critical(self, "Import Error", "An error occurred while importing footage.")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        try:
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(('.mp4', '.mov', '.avi')):
                    new_items = self.backend.import_media([file_path])
                    if new_items:
                        self.imported_items.extend(new_items)
                    self.addClipPreview(file_path)
                else:
                    logging.warning("Unsupported file type dropped: %s", file_path)
                    QMessageBox.warning(self, "Unsupported File", f"File '{file_path}' is not a supported video format.")
        except Exception as e:
            logging.exception("Error during file drop: %s", e)

    def createTimeline(self):
        if not self.preview_widgets:
            logging.warning("No clips available to create a timeline.")
            QMessageBox.information(self, "No Clips", "Please import clips before creating a timeline.")
            return
        if not self.imported_items:
            logging.warning("No imported items in the Media Pool.")
            QMessageBox.warning(self, "Timeline Error", "No media items found in the Media Pool.")
            return
        timeline = self.backend.create_timeline(self.imported_items)
        if timeline is None:
            QMessageBox.warning(self, "Timeline Error", "Failed to create timeline.")

    def getLUTPath(self, lut_name):
        return self.backend.get_lut_path(lut_name)

    def runAITask(self, operation):
        num_clips = len(self.preview_widgets)
        if num_clips == 0:
            logging.warning("No clips to process for %s.", operation)
            return
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.thread = QThread()
        from workers import AIWorker
        self.worker = AIWorker(operation, num_clips)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(lambda: logging.info("Finished %s on %d clip(s).", operation, num_clips))
        self.worker.finished.connect(lambda: self.progress_bar.hide())
        self.thread.start()

    def autoColorGrade(self):
        lut_name = self.settings.get("lut_selection", "Default")
        if lut_name != "Default":
            lut_path = self.getLUTPath(lut_name)
            if lut_path and os.path.exists(lut_path):
                self.backend.apply_lut(lut_path)
            else:
                logging.error("LUT file for '%s' not found.", lut_name)
        self.runAITask("AI Auto Color")

    def applySmartReframe(self):
        self.runAITask("AI Smart Reframe")

    def detectScenes(self):
        if not self.imported_items:
            logging.warning("No clips available for scene detection.")
            QMessageBox.warning(self, "No Clips", "Please import clips before running scene detection.")
            return
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.scene_thread = QThread()
        from workers import SceneDetectionWorker
        self.scene_worker = SceneDetectionWorker(self.imported_items)
        self.scene_worker.moveToThread(self.scene_thread)
        self.scene_thread.started.connect(self.scene_worker.run)
        self.scene_worker.progress.connect(self.progress_bar.setValue)
        self.scene_worker.finished.connect(self.onSceneDetectionFinished)
        self.scene_worker.finished.connect(self.scene_worker.deleteLater)
        self.scene_thread.finished.connect(self.scene_thread.deleteLater)
        self.scene_thread.start()

    def onSceneDetectionFinished(self, new_clips):
        self.progress_bar.hide()
        success = self.backend.update_timeline_with_trimmed_clips(new_clips)
        if success:
            QMessageBox.information(self, "Scene Detection Complete", "Automatic trimming and scene detection completed successfully.")
        else:
            QMessageBox.critical(self, "Timeline Error", "An error occurred while updating the timeline with trimmed clips.")

    def applyNoiseReduction(self):
        self.runAITask("AI Noise Reduction")

    def applyVoiceIsolation(self):
        self.runAITask("AI Voice Isolation")

    def smartHighlight(self):
        self.runAITask("AI Smart Highlight")

    def aiAudioEnhancements(self):
        self.runAITask("AI Audio Enhancements")

    def aiMusicSync(self):
        self.runAITask("AI Music Sync")

    def applyFusionEffects(self):
        success = self.backend.fusion_automation()
        if success:
            QMessageBox.information(self, "Fusion Automation", "Fusion effects applied and composition saved successfully.")
        else:
            QMessageBox.warning(self, "Fusion Automation", "Fusion automation failed. Check logs for details.")

    def reorderClips(self, source_widget, target_widget):
        try:
            idx_source = self.preview_widgets.index(source_widget)
            idx_target = self.preview_widgets.index(target_widget)
            self.preview_widgets[idx_source], self.preview_widgets[idx_target] = self.preview_widgets[idx_target], self.preview_widgets[idx_source]
            for i in reversed(range(self.clip_layout.count())):
                item = self.clip_layout.itemAt(i)
                if item and item.widget():
                    self.clip_layout.removeWidget(item.widget())
            for idx, widget in enumerate(self.preview_widgets):
                row = idx // 4
                col = idx % 4
                self.clip_layout.addWidget(widget, row, col)
            logging.info("Clips reordered.")
        except Exception as e:
            logging.exception("Error reordering clips: %s", e)

    def openSettings(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.settings = dialog.getSettings()
            logging.info("Settings updated: %s", self.settings)

    def saveProject(self):
        try:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "Project Files (*.json)")
            if file_path:
                project_data = {
                    "clips": [widget.file_path for widget in self.preview_widgets],
                    "settings": self.settings
                }
                with open(file_path, "w") as f:
                    json.dump(project_data, f, indent=4)
                logging.info("Project saved to %s.", file_path)
        except Exception as e:
            logging.exception("Error saving project: %s", e)
            QMessageBox.critical(self, "Save Error", "Failed to save the project.")

    def loadProject(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "Project Files (*.json)")
            if file_path:
                with open(file_path, "r") as f:
                    project_data = json.load(f)
                for widget in self.preview_widgets:
                    widget.cleanup()
                    widget.deleteLater()
                self.preview_widgets = []
                self.clip_count = 0
                while self.clip_layout.count():
                    item = self.clip_layout.takeAt(0)
                    if item and item.widget():
                        item.widget().deleteLater()
                for clip in project_data.get("clips", []):
                    self.addClipPreview(clip)
                self.settings = project_data.get("settings", self.settings)
                logging.info("Project loaded from %s.", file_path)
        except Exception as e:
            logging.exception("Error loading project: %s", e)
            QMessageBox.critical(self, "Load Error", "Failed to load the project.")

    def exportVideo(self):
        dialog = ExportDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            export_settings = dialog.getExportSettings()
            self.settings["export_format"] = export_settings["export_format"]
            logging.info("Exporting Video in %s format at %s resolution.",
                         self.settings["export_format"], self.settings["export_resolution"])
            if export_settings.get("batch_export"):
                total_clips = len(self.preview_widgets)
                if total_clips == 0:
                    QMessageBox.warning(self, "Batch Export", "No clips to export.")
                    return
                self.progress_bar.show()
                self.progress_bar.setValue(0)
                self.thread = QThread()
                from workers import BatchExportWorker
                self.batch_export_worker = BatchExportWorker(total_clips)
                self.batch_export_worker.moveToThread(self.thread)
                self.thread.started.connect(self.batch_export_worker.run)
                self.batch_export_worker.progress.connect(self.progress_bar.setValue)
                self.batch_export_worker.finished.connect(self.thread.quit)
                self.batch_export_worker.finished.connect(self.batch_export_worker.deleteLater)
                self.thread.finished.connect(self.thread.deleteLater)
                self.batch_export_worker.finished.connect(lambda: logging.info("Batch export completed."))
                self.batch_export_worker.finished.connect(lambda: self.progress_bar.hide())
                self.thread.start()
                return

            timeline = self.backend.get_current_timeline()
            if not timeline:
                logging.error("No timeline found. Create a timeline before exporting.")
                QMessageBox.warning(self, "Export Error", "No timeline found. Please create one before exporting.")
                return

            render_settings = {
                "TargetDir": export_settings["export_location"],
                "Format": self.settings["export_format"],
                "Resolution": self.settings["export_resolution"],
            }
            if export_settings.get("watermark"):
                render_settings["WatermarkPath"] = export_settings["watermark"]
            success = self.backend.export_video(render_settings)
            if not success:
                QMessageBox.critical(self, "Render Error", "Failed to start rendering. Check your render settings.")
            
            self.progress_bar.show()
            self.progress_bar.setValue(0)
            self.thread = QThread()
            from workers import ExportWorker
            self.export_worker = ExportWorker()
            self.export_worker.moveToThread(self.thread)
            self.thread.started.connect(self.export_worker.run)
            self.export_worker.progress.connect(self.progress_bar.setValue)
            self.export_worker.finished.connect(self.thread.quit)
            self.export_worker.finished.connect(self.export_worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.export_worker.finished.connect(lambda: logging.info("Export completed."))
            self.export_worker.finished.connect(lambda: self.progress_bar.hide())
            self.thread.start()
        else:
            logging.info("Export cancelled.")

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys
    backend = None
    try:
        from backend import ResolveController
        backend = ResolveController()
    except Exception as e:
        logging.critical("Fatal error initializing backend: %s", e)
        sys.exit("A fatal error occurred. Check the log for details.")

    app = QApplication(sys.argv)
    editor = DroneVideoEditor(backend, {})
    editor.show()
    sys.exit(app.exec())
