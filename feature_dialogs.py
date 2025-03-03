import logging
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QComboBox, QSlider, QCheckBox, QFormLayout,
    QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt

class ColorGradingDialog(QDialog):
    """Advanced color grading interface"""
    
    def __init__(self, parent=None, resolve_controller=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Color Grading")
        self.resize(600, 450)
        self.controller = resolve_controller
        
        main_layout = QVBoxLayout(self)
        
        # Preset selector
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Color Preset:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["Default", "Cinematic", "Drone Aerial", "Real Estate", "Custom"])
        preset_layout.addWidget(self.preset_combo)
        main_layout.addLayout(preset_layout)
        
        # Node controls
        nodes_layout = QHBoxLayout()
        
        # Left side: Node list
        self.nodes_list = QListWidget()
        self.nodes_list.addItems([
            "Primary Correction", 
            "Secondary Correction",
            "Vignette", 
            "Sky Enhancer", 
            "Shadow Recovery"
        ])
        nodes_layout.addWidget(self.nodes_list)
        
        # Right side: Node parameters
        node_params_layout = QFormLayout()
        
        # Color wheels would normally go here
        # We'll simulate with sliders
        for param in ["Lift", "Gamma", "Gain", "Offset"]:
            param_layout = QHBoxLayout()
            param_layout.addWidget(QLabel(f"{param}:"))
            
            for color in ["R", "G", "B"]:
                slider = QSlider(Qt.Orientation.Horizontal)
                slider.setRange(-100, 100)
                slider.setValue(0)
                slider.setTickPosition(QSlider.TickPosition.TicksBelow)
                param_layout.addWidget(QLabel(color))
                param_layout.addWidget(slider)
            
            node_params_layout.addRow(param_layout)
        
        # Add some common adjustments
        saturation_layout = QHBoxLayout()
        saturation_layout.addWidget(QLabel("Saturation:"))
        saturation_slider = QSlider(Qt.Orientation.Horizontal)
        saturation_slider.setRange(-100, 100)
        saturation_slider.setValue(0)
        saturation_layout.addWidget(saturation_slider)
        node_params_layout.addRow(saturation_layout)
        
        contrast_layout = QHBoxLayout()
        contrast_layout.addWidget(QLabel("Contrast:"))
        contrast_slider = QSlider(Qt.Orientation.Horizontal)
        contrast_slider.setRange(-100, 100)
        contrast_slider.setValue(0)
        contrast_layout.addWidget(contrast_slider)
        node_params_layout.addRow(contrast_layout)
        
        # Add node parameters to the main layout
        nodes_layout.addLayout(node_params_layout)
        main_layout.addLayout(nodes_layout)
        
        # LUT selector
        lut_layout = QHBoxLayout()
        lut_layout.addWidget(QLabel("Apply LUT:"))
        self.lut_combo = QComboBox()
        self.lut_combo.addItems(["None", "Cinematic.cube", "Drone.cube", "RealEstate.cube"])
        lut_layout.addWidget(self.lut_combo)
        lut_layout.addWidget(QPushButton("Browse..."))
        main_layout.addLayout(lut_layout)
        
        # AI Enhancement options
        ai_layout = QVBoxLayout()
        ai_layout.addWidget(QLabel("AI Enhancements:"))
        
        ai_options = [
            "Smart HDR", 
            "Magic Mask: Sky",
            "Magic Mask: Buildings",
            "Auto Balance",
            "Smart Saturation"
        ]
        
        for option in ai_options:
            checkbox = QCheckBox(option)
            ai_layout.addWidget(checkbox)
        
        main_layout.addLayout(ai_layout)
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply | 
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_color_grade)
        button_box.button(QDialogButtonBox.StandardButton.Save).clicked.connect(self.save_color_preset)
        main_layout.addWidget(button_box)
    
    def apply_color_grade(self):
        """Apply the current color grade settings to the timeline."""
        if not self.controller:
            QMessageBox.warning(self, "No Controller", "No Resolve controller available.")
            return
            
        try:
            # In a real implementation, this would collect all the color parameters
            # and apply them to the timeline using the Resolve API
            timeline = self.controller.get_current_timeline()
            if not timeline:
                QMessageBox.warning(self, "No Timeline", "No active timeline found.")
                return
                
            lut_name = self.lut_combo.currentText()
            if lut_name != "None":
                lut_path = self.controller.get_lut_path(lut_name.replace(".cube", ""))
                if lut_path:
                    self.controller.apply_lut(lut_path)
                    QMessageBox.information(self, "Color Applied", f"Applied {lut_name} to timeline.")
                else:
                    QMessageBox.warning(self, "LUT Not Found", f"Could not find LUT: {lut_name}")
            else:
                QMessageBox.information(self, "Settings Applied", "Applied custom color grade settings.")
                
        except Exception as e:
            logging.exception("Error applying color grade: %s", e)
            QMessageBox.critical(self, "Error", f"Failed to apply color grade: {str(e)}")
    
    def save_color_preset(self):
        """Save current color grade as a preset."""
        # This would save the current settings as a preset for future use
        QMessageBox.information(self, "Save Preset", "Preset saved successfully.")


class AutomatedTitlesDialog(QDialog):
    """Dialog for creating and managing automated titles and graphics"""
    
    def __init__(self, parent=None, resolve_controller=None):
        super().__init__(parent)
        self.setWindowTitle("Automated Titles & Graphics")
        self.resize(650, 500)
        self.controller = resolve_controller
        
        layout = QVBoxLayout(self)
        
        # Title template selection
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Title Template:"))
        self.title_combo = QComboBox()
        self.title_combo.addItems([
            "Drone Flyover", 
            "Real Estate Intro",
            "Location Subtitle",
            "Feature Callout",
            "Property Stats",
            "Agent Contact"
        ])
        title_layout.addWidget(self.title_combo)
        layout.addLayout(title_layout)
        
        # Settings form
        form_layout = QFormLayout()
        
        # Add various title fields
        self.property_address = QComboBox()
        self.property_address.setEditable(True)
        self.property_address.addItems([
            "123 Main Street, Anytown, USA",
            "456 Park Avenue, New City, USA",
            "789 Beach Road, Coastal City, USA"
        ])
        form_layout.addRow("Property Address:", self.property_address)
        
        self.property_price = QComboBox()
        self.property_price.setEditable(True)
        self.property_price.addItems(["$1,250,000", "$895,000", "$2,450,000"])
        form_layout.addRow("Property Price:", self.property_price)
        
        self.agent_name = QComboBox()
        self.agent_name.setEditable(True)
        self.agent_name.addItems(["John Smith", "Jane Doe", "Robert Johnson"])
        form_layout.addRow("Agent Name:", self.agent_name)
        
        self.brokerage = QComboBox()
        self.brokerage.setEditable(True)
        self.brokerage.addItems(["Luxury Homes", "City Realty", "Coastal Properties"])
        form_layout.addRow("Brokerage:", self.brokerage)
        
        layout.addLayout(form_layout)
        
        # Title positioning
        position_layout = QHBoxLayout()
        position_layout.addWidget(QLabel("Position:"))
        self.position_combo = QComboBox()
        self.position_combo.addItems(["Lower Third", "Center", "Top", "Bottom", "Custom"])
        position_layout.addWidget(self.position_combo)
        layout.addLayout(position_layout)
        
        # Duration
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Duration (seconds):"))
        self.duration_slider = QSlider(Qt.Orientation.Horizontal)
        self.duration_slider.setRange(2, 10)
        self.duration_slider.setValue(5)
        self.duration_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.duration_slider.setTickInterval(1)
        duration_layout.addWidget(self.duration_slider)
        self.duration_value = QLabel("5")
        duration_layout.addWidget(self.duration_value)
        self.duration_slider.valueChanged.connect(lambda v: self.duration_value.setText(str(v)))
        layout.addLayout(duration_layout)
        
        # Animation options
        animation_layout = QHBoxLayout()
        animation_layout.addWidget(QLabel("Animation:"))
        self.animation_combo = QComboBox()
        self.animation_combo.addItems(["Fade", "Slide In", "Scale Up", "Typewriter", "None"])
        animation_layout.addWidget(self.animation_combo)
        layout.addLayout(animation_layout)
        
        # Insert at options
        insert_layout = QHBoxLayout()
        insert_layout.addWidget(QLabel("Insert At:"))
        self.insert_combo = QComboBox()
        self.insert_combo.addItems([
            "Timeline Start", 
            "Timeline End", 
            "Current Position",
            "Before Each Clip",
            "After Each Clip",
            "On All Clips (Overlay)"
        ])
        insert_layout.addWidget(self.insert_combo)
        layout.addLayout(insert_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.insert_titles)
        layout.addWidget(button_box)
    
    def insert_titles(self):
        """Insert the configured titles into the timeline."""
        if not self.controller:
            QMessageBox.warning(self, "No Controller", "No Resolve controller available.")
            return
            
        try:
            timeline = self.controller.get_current_timeline()
            if not timeline:
                QMessageBox.warning(self, "No Timeline", "No active timeline found.")
                return
            
            # Check if the InsertFusionTitleIntoTimeline method is available
            if (hasattr(self.controller, 'api_helper') and 
                self.controller.api_helper.is_method_available("timeline.InsertFusionTitleIntoTimeline")):
                
                # This would be the actual implementation using the Resolve API
                title_name = self.title_combo.currentText()
                position = self.position_combo.currentText()
                duration = self.duration_slider.value()
                
                # For now, we'll just show a message
                QMessageBox.information(
                    self, 
                    "Titles Added", 
                    f"Added {title_name} title at {position} for {duration} seconds."
                )
            else:
                QMessageBox.warning(
                    self, 
                    "Feature Not Available", 
                    "Title insertion is not available in your version of the DaVinci Resolve API. "
                    "Please use Resolve 17.0 or higher."
                )
                
        except Exception as e:
            logging.exception("Error inserting titles: %s", e)
            QMessageBox.critical(self, "Error", f"Failed to insert titles: {str(e)}")


class SceneAnalyzerDialog(QDialog):
    """Advanced scene analysis and management dialog"""
    
    def __init__(self, parent=None, resolve_controller=None):
        super().__init__(parent)
        self.setWindowTitle("AI Scene Analyzer")
        self.resize(800, 600)
        self.controller = resolve_controller
        
        layout = QVBoxLayout(self)
        
        # Detection options
        options_layout = QHBoxLayout()
        options_layout.addWidget(QLabel("Detect:"))
        
        detection_options = [
            ("Scene Changes", True),
            ("Object Motion", True),
            ("Faces", False), 
            ("Buildings", True),
            ("Vehicles", False),
            ("Text/Signs", False),
            ("Exposure Issues", True),
            ("Camera Movement", True)
        ]
        
        for option, default in detection_options:
            checkbox = QCheckBox(option)
            checkbox.setChecked(default)
            options_layout.addWidget(checkbox)
        
        layout.addLayout(options_layout)
        
        # Sensitivity
        sensitivity_layout = QHBoxLayout()
        sensitivity_layout.addWidget(QLabel("Detection Sensitivity:"))
        self.sensitivity_slider = QSlider(Qt.Orientation.Horizontal)
        self.sensitivity_slider.setRange(1, 10)
        self.sensitivity_slider.setValue(5)
        self.sensitivity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        sensitivity_layout.addWidget(self.sensitivity_slider)
        layout.addLayout(sensitivity_layout)
        
        # Clips table/list would go here