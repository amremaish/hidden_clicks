"""Image Matcher action type."""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QDialogButtonBox, QPushButton, QFileDialog, QMessageBox,
    QListWidget, QListWidgetItem, QGroupBox, QScrollArea, QWidget, QSpinBox, QCheckBox
)
from PyQt5.QtCore import Qt
import os

from src.action_types.base import BaseActionType
from src.ui.icons import get_icon, get_icon_text, get_unicode_icon


class ImageMatcherDialog(QDialog):
    """Dialog for adding an image matcher action"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # Lazy import to avoid circular dependency
        from src.action_types.registry import get_action_registry
        self.action_registry = get_action_registry()
        self.true_actions = []
        self.false_actions = []
        self._action_data = None
        self.setWindowTitle(get_icon_text('image', 'Add Image Matcher Action'))
        self.setModal(True)
        self.setFixedSize(600, 700)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 2px solid #ccc;
                border-radius: 4px;
                padding: 8px;
                color: #333;
                font-size: 12px;
                min-height: 28px;
            }
            QLineEdit::placeholder {
                color: #999999;
            }
            QLineEdit:hover {
                border-color: #42a5f5;
            }
            QLineEdit:focus {
                border-color: #42a5f5;
                background-color: #ffffff;
            }
            QSpinBox {
                background-color: #ffffff;
                border: 2px solid #ccc;
                border-radius: 4px;
                padding: 4px 8px;
                color: #333;
                font-size: 12px;
                min-height: 20px;
                max-height: 24px;
            }
            QSpinBox:hover {
                border-color: #42a5f5;
            }
            QSpinBox:focus {
                border-color: #42a5f5;
                background-color: #ffffff;
            }
            QListWidget {
                background-color: #ffffff;
                border: 2px solid #ccc;
                border-radius: 4px;
                padding: 5px;
                color: #333;
                font-size: 11px;
                min-height: 100px;
                max-height: 150px;
            }
            QListWidget::item {
                padding: 5px;
                border-radius: 3px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
            QListWidget::item:selected {
                background-color: #42a5f5;
                color: white;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 11px;
                border: 2px solid #ccc;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #1976d2;
            }
            QPushButton {
                background-color: #42a5f5;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #64b5f6;
                color: white;
            }
            QPushButton:pressed {
                background-color: #2196f3;
                color: white;
            }
            QPushButton[text*="Cancel"] {
                background-color: #e0e0e0;
                color: #333;
            }
            QPushButton[text*="Cancel"]:hover {
                background-color: #d0d0d0;
                color: #333;
            }
            QPushButton[text*="Cancel"]:pressed {
                background-color: #bdbdbd;
                color: #333;
            }
        """)
        
        # Create scroll area for the dialog content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header with icon
        header_layout = QHBoxLayout()
        icon_label = QLabel(get_unicode_icon('image'))
        icon_label.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon_label)
        label = QLabel("Configure Image Matcher:")
        label.setStyleSheet("font-size: 13px; font-weight: bold; color: #333;")
        header_layout.addWidget(label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Image path input
        image_path_label = QLabel("Template Image Path:")
        image_path_label.setStyleSheet("font-size: 12px; color: #333; font-weight: bold;")
        layout.addWidget(image_path_label)
        
        image_path_layout = QHBoxLayout()
        self.image_path_input = QLineEdit()
        self.image_path_input.setPlaceholderText("Enter image path or click Browse...")
        image_path_layout.addWidget(self.image_path_input)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.setFixedWidth(90)
        browse_btn.setFixedHeight(35)
        browse_btn.clicked.connect(self.browse_image)
        image_path_layout.addWidget(browse_btn)
        layout.addLayout(image_path_layout)
        
        # Match number input
        match_number_label = QLabel("Match Number (1 = first match, 2 = second match, etc.):")
        match_number_label.setStyleSheet("font-size: 12px; color: #333; font-weight: bold;")
        layout.addWidget(match_number_label)
        
        match_number_layout = QHBoxLayout()
        self.match_number_input = QSpinBox()
        self.match_number_input.setMinimum(1)
        self.match_number_input.setMaximum(100)
        self.match_number_input.setValue(1)
        match_number_layout.addWidget(self.match_number_input)
        match_number_layout.addStretch()
        layout.addLayout(match_number_layout)
        
        # Threshold input
        threshold_label = QLabel("Threshold (0-100, higher = stricter matching):")
        threshold_label.setStyleSheet("font-size: 12px; color: #333; font-weight: bold;")
        layout.addWidget(threshold_label)
        
        threshold_layout = QHBoxLayout()
        self.threshold_input = QSpinBox()
        self.threshold_input.setMinimum(0)
        self.threshold_input.setMaximum(100)
        self.threshold_input.setValue(99)  # Default to 99 (0.99)
        threshold_layout.addWidget(self.threshold_input)
        threshold_layout.addStretch()
        layout.addLayout(threshold_layout)
        
        # Full screen checkbox
        self.full_screen_checkbox = QCheckBox("Use full screen screenshot (no crop area)")
        self.full_screen_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 12px;
                color: #333;
                font-weight: bold;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #ccc;
                border-radius: 3px;
                background-color: #ffffff;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #42a5f5;
                border-radius: 3px;
                background-color: #42a5f5;
            }
        """)
        self.full_screen_checkbox.stateChanged.connect(self.on_full_screen_changed)
        layout.addWidget(self.full_screen_checkbox)
        
        # Crop area selection
        crop_label = QLabel("Crop Area (optional - select area to screenshot):")
        crop_label.setStyleSheet("font-size: 12px; color: #333; font-weight: bold;")
        layout.addWidget(crop_label)
        
        crop_layout = QHBoxLayout()
        self.crop_info_label = QLabel("No area selected")
        self.crop_info_label.setStyleSheet("""
            font-size: 11px; 
            color: #666; 
            padding: 8px;
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            border-radius: 4px;
            min-height: 28px;
        """)
        crop_layout.addWidget(self.crop_info_label)
        
        self.select_area_btn = QPushButton("Select Area...")
        self.select_area_btn.setFixedWidth(120)
        self.select_area_btn.setFixedHeight(35)
        self.select_area_btn.clicked.connect(self.select_crop_area)
        crop_layout.addWidget(self.select_area_btn)
        
        self.clear_area_btn = QPushButton("Clear")
        self.clear_area_btn.setFixedWidth(80)
        self.clear_area_btn.setFixedHeight(35)
        self.clear_area_btn.clicked.connect(self.clear_crop_area)
        crop_layout.addWidget(self.clear_area_btn)
        
        layout.addLayout(crop_layout)
        
        # Store crop area
        self.crop_area = None
        self.use_full_screen = False
        
        # True Actions Section
        true_group = QGroupBox("True Actions (execute when image matches)")
        true_layout = QVBoxLayout(true_group)
        true_layout.setContentsMargins(10, 15, 10, 10)
        true_layout.setSpacing(8)
        
        self.true_actions_list = QListWidget()
        true_layout.addWidget(self.true_actions_list)
        
        true_buttons_layout = QHBoxLayout()
        add_true_btn = QPushButton("Add Action")
        add_true_btn.clicked.connect(self._add_true_action)
        edit_true_btn = QPushButton("Edit")
        edit_true_btn.clicked.connect(lambda: self._edit_sub_action(True))
        remove_true_btn = QPushButton("Remove")
        remove_true_btn.clicked.connect(lambda: self._remove_sub_action(True))
        true_buttons_layout.addWidget(add_true_btn)
        true_buttons_layout.addWidget(edit_true_btn)
        true_buttons_layout.addWidget(remove_true_btn)
        true_buttons_layout.addStretch()
        true_layout.addLayout(true_buttons_layout)
        
        layout.addWidget(true_group)
        
        # False Actions Section
        false_group = QGroupBox("False Actions (execute when image does NOT match)")
        false_layout = QVBoxLayout(false_group)
        false_layout.setContentsMargins(10, 15, 10, 10)
        false_layout.setSpacing(8)
        
        self.false_actions_list = QListWidget()
        false_layout.addWidget(self.false_actions_list)
        
        false_buttons_layout = QHBoxLayout()
        add_false_btn = QPushButton("Add Action")
        add_false_btn.clicked.connect(self._add_false_action)
        edit_false_btn = QPushButton("Edit")
        edit_false_btn.clicked.connect(lambda: self._edit_sub_action(False))
        remove_false_btn = QPushButton("Remove")
        remove_false_btn.clicked.connect(lambda: self._remove_sub_action(False))
        false_buttons_layout.addWidget(add_false_btn)
        false_buttons_layout.addWidget(edit_false_btn)
        false_buttons_layout.addWidget(remove_false_btn)
        false_buttons_layout.addStretch()
        false_layout.addLayout(false_buttons_layout)
        
        layout.addWidget(false_group)
        
        layout.addStretch()
        
        scroll.setWidget(content_widget)
        
        # Main dialog layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.button(QDialogButtonBox.Ok).setText(get_icon_text('ok', 'Add'))
        button_box.button(QDialogButtonBox.Cancel).setText(get_icon_text('cancel', 'Cancel'))
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        main_layout.addSpacing(15)  # Add spacing before buttons
        main_layout.addWidget(button_box)
        main_layout.setContentsMargins(0, 0, 15, 15)  # Add right and bottom margins
        
        # Load action data if provided
        if self._action_data:
            self.load_action_data(self._action_data)
    
    def browse_image(self):
        """Open image file browser dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Template Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*.*)"
        )
        if file_path:
            self.image_path_input.setText(file_path)
    
    def select_crop_area(self):
        """Open screen selector to choose crop area"""
        try:
            from src.ui.screen_selector import ScreenSelector
            
            # Show selector (it will handle hiding this dialog)
            print(f"🔍 Calling ScreenSelector.select_area...")
            area = ScreenSelector.select_area(parent=self)
            print(f"🔍 ScreenSelector returned: {area}")
            
            # Dialog should be visible again after selector closes
            # Force it to be visible and active
            self.show()
            self.raise_()
            self.activateWindow()
            self.setFocus()
            
            if area:
                x, y, width, height = area
                self.crop_area = area
                print(f"✅ Crop area selected: ({x}, {y}) - {width} × {height}")
                self.crop_info_label.setText(f"Area: ({x}, {y}) - {width} × {height} px")
                self.crop_info_label.setStyleSheet("""
                    font-size: 11px; 
                    color: #1976d2; 
                    padding: 8px;
                    background-color: #e3f2fd;
                    border: 1px solid #42a5f5;
                    border-radius: 4px;
                    min-height: 28px;
                """)
            else:
                print(f"⚠️ Crop area selection cancelled")
                self.clear_crop_area()
        except Exception as e:
            import traceback
            traceback.print_exc()
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", f"Failed to open screen selector: {e}")
            # Show dialog again even if there was an error
            self.show()
            self.raise_()
            self.activateWindow()
    
    def on_full_screen_changed(self, state):
        """Handle full screen checkbox state change"""
        print(f"🔍 on_full_screen_changed called with state: {state} (Qt.Checked={Qt.Checked})")
        print(f"   - Before: self.use_full_screen={self.use_full_screen}, self.crop_area={self.crop_area}")
        
        self.use_full_screen = (state == Qt.Checked)
        
        # Enable/disable crop area controls based on checkbox
        enabled = not self.use_full_screen
        self.crop_info_label.setEnabled(enabled)
        self.select_area_btn.setEnabled(enabled)
        self.clear_area_btn.setEnabled(enabled)
        
        # Visual feedback for disabled state
        if enabled:
            self.crop_info_label.setStyleSheet("""
                font-size: 11px; 
                color: #666; 
                padding: 8px;
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
                min-height: 28px;
            """)
        else:
            self.crop_info_label.setStyleSheet("""
                font-size: 11px; 
                color: #999; 
                padding: 8px;
                background-color: #e0e0e0;
                border: 1px solid #bbb;
                border-radius: 4px;
                min-height: 28px;
            """)
        
        # Clear crop area when enabling full screen
        if self.use_full_screen:
            print(f"   - Clearing crop_area because full screen is enabled")
            self.crop_area = None
        
        print(f"   - After: self.use_full_screen={self.use_full_screen}, self.crop_area={self.crop_area}")
    
    def clear_crop_area(self):
        """Clear the selected crop area"""
        self.crop_area = None
        self.crop_info_label.setText("No area selected")
        self.crop_info_label.setStyleSheet("""
            font-size: 11px; 
            color: #666; 
            padding: 8px;
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            border-radius: 4px;
            min-height: 28px;
        """)
    
    def _add_true_action(self):
        """Add an action to the true actions list"""
        self._add_sub_action(True)
    
    def _add_false_action(self):
        """Add an action to the false actions list"""
        self._add_sub_action(False)
    
    def _add_sub_action(self, is_true):
        """Add a sub action by opening action type selection"""
        # Create a simple dialog to select action type
        type_dialog = QDialog(self)
        type_dialog.setWindowTitle("Select Action Type")
        type_dialog.setModal(True)
        type_dialog.setFixedSize(300, 200)
        type_dialog.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333;
                font-size: 12px;
                margin: 0px;
                padding: 0px;
            }
        """)
        
        layout = QVBoxLayout(type_dialog)
        layout.setContentsMargins(10, -5, 10, -5)  # Negative top and bottom margins to remove space
        layout.setSpacing(0)  # Remove spacing
        label = QLabel("Double-click an action type to add:")
        label.setStyleSheet("""
            margin: 0px;
            padding: 0px;
            border: none;
            margin-bottom: -10px;
        """)
        label.setContentsMargins(0, 0, 0, 0)  # Remove label margins
        label.setWordWrap(False)
        label.setAlignment(Qt.AlignTop | Qt.AlignLeft)  # Align to top
        layout.addWidget(label, 0, Qt.AlignTop)  # Add with stretch factor 0 and top alignment
        
        type_list = QListWidget()
        type_list.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                border: 2px solid #ccc;
                border-radius: 4px;
                margin-top: -10px;
                margin-bottom: 0px;
            }
            QListWidget::item {
                padding: 8px;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
            QListWidget::item:selected {
                background-color: #42a5f5;
                color: white;
            }
        """)
        for display_name in self.action_registry.get_all_display_names():
            item = QListWidgetItem(display_name)
            type_list.addItem(item)
        type_list.setContentsMargins(0, 0, 0, 0)  # Remove list widget margins
        layout.addWidget(type_list, 1)  # Add with stretch factor
        
        def on_type_double_clicked(item):
            display_name = item.text()
            action_type = self.action_registry.get_by_display_name(display_name)
            if action_type:
                type_dialog.accept()
                # Create dialog for this action type
                dialog = action_type.create_dialog(self)
                if dialog.exec_() == QDialog.Accepted:
                    if hasattr(dialog, 'get_action'):
                        action = dialog.get_action()
                        if action and action_type.validate_action_data(action):
                            if is_true:
                                self.true_actions.append(action)
                                self._populate_sub_action_list(True)
                            else:
                                self.false_actions.append(action)
                                self._populate_sub_action_list(False)
        
        type_list.itemDoubleClicked.connect(on_type_double_clicked)
        type_dialog.exec_()
    
    def _edit_sub_action(self, is_true):
        """Edit the selected sub action"""
        actions_list = self.true_actions_list if is_true else self.false_actions_list
        actions = self.true_actions if is_true else self.false_actions
        
        current_item = actions_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select an action to edit.")
            return
        
        row = actions_list.row(current_item)
        if 0 <= row < len(actions):
            action = actions[row]
            action_type = self.action_registry.get_by_type_id(action.get("type", ""))
            if action_type:
                # Create dialog and populate with existing action data
                dialog = action_type.create_dialog(self)
                if hasattr(dialog, 'load_action_data'):
                    dialog.load_action_data(action)
                if dialog.exec_() == QDialog.Accepted:
                    if hasattr(dialog, 'get_action'):
                        new_action = dialog.get_action()
                        if new_action and action_type.validate_action_data(new_action):
                            actions[row] = new_action
                            self._populate_sub_action_list(is_true)
    
    def _remove_sub_action(self, is_true):
        """Remove the selected sub action"""
        actions_list = self.true_actions_list if is_true else self.false_actions_list
        actions = self.true_actions if is_true else self.false_actions
        
        current_item = actions_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select an action to remove.")
            return
        
        row = actions_list.row(current_item)
        if 0 <= row < len(actions):
            actions.pop(row)
            self._populate_sub_action_list(is_true)
    
    def _populate_sub_action_list(self, is_true):
        """Populate the sub action list widget"""
        actions_list = self.true_actions_list if is_true else self.false_actions_list
        actions = self.true_actions if is_true else self.false_actions
        
        actions_list.clear()
        for action in actions:
            action_type = self.action_registry.get_by_type_id(action.get("type", ""))
            if action_type:
                display_text = action_type.format_action_display(action)
                actions_list.addItem(display_text)
    
    def accept(self):
        """Override accept to add logging"""
        print(f"🔍 ImageMatcherDialog.accept() called - crop_area: {self.crop_area}")
        super().accept()
        print(f"✅ ImageMatcherDialog accepted, result code: {self.result()}")
    
    def reject(self):
        """Override reject to add logging"""
        print(f"⚠️ ImageMatcherDialog.reject() called - crop_area: {self.crop_area}")
        import traceback
        traceback.print_stack()
        super().reject()
        print(f"❌ ImageMatcherDialog rejected, result code: {self.result()}")
    
    def closeEvent(self, event):
        """Override closeEvent to add logging"""
        print(f"🔍 ImageMatcherDialog.closeEvent() called - crop_area: {self.crop_area}, result: {self.result()}")
        super().closeEvent(event)
    
    def validate_and_accept(self):
        """Validate inputs before accepting"""
        print(f"🔍 validate_and_accept called - crop_area: {self.crop_area}")
        image_path = self.image_path_input.text().strip()
        match_number = self.match_number_input.value()
        
        if not image_path:
            print(f"⚠️ Validation failed: No image path")
            QMessageBox.warning(self, "Validation Error", "Please enter an image path.")
            return
        
        if not os.path.exists(image_path):
            print(f"⚠️ Image file not found: {image_path}")
            reply = QMessageBox.question(
                self,
                "File Not Found",
                f"Image file not found: {image_path}\nDo you want to continue anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                print(f"⚠️ User chose not to continue with missing file")
                return
            else:
                print(f"✅ User chose to continue despite missing file")
        
        # Check if it's a valid image file
        valid_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
        if not any(image_path.lower().endswith(ext) for ext in valid_extensions):
            print(f"⚠️ Validation failed: Invalid file extension for {image_path}")
            QMessageBox.warning(
                self,
                "Invalid File",
                "Please select a valid image file (PNG, JPG, JPEG, BMP, or GIF)."
            )
            return
        
        if match_number < 1:
            print(f"⚠️ Validation failed: Match number < 1")
            QMessageBox.warning(self, "Validation Error", "Match number must be at least 1.")
            return
        
        threshold = self.threshold_input.value()
        if threshold < 0 or threshold > 100:
            print(f"⚠️ Validation failed: Threshold out of range")
            QMessageBox.warning(self, "Validation Error", "Threshold must be between 0 and 100.")
            return
        
        print(f"✅ Validation passed - calling accept() with crop_area: {self.crop_area}")
        self.accept()
    
    def get_action(self):
        """Return the image matcher action dictionary"""
        print(f"🔍 get_action called - crop_area: {self.crop_area}, use_full_screen: {self.use_full_screen}")
        action = {
            "type": "image_matcher",
            "image_path": self.image_path_input.text().strip(),
            "match_number": self.match_number_input.value(),
            "threshold": self.threshold_input.value(),  # 0-100, will be converted to 0.0-1.0
            "true_actions": self.true_actions.copy(),
            "false_actions": self.false_actions.copy(),
            "use_full_screen": self.use_full_screen
        }
        
        # Add crop area if selected (only if not using full screen)
        if self.crop_area and not self.use_full_screen:
            x, y, width, height = self.crop_area
            action["crop_x"] = x
            action["crop_y"] = y
            action["crop_width"] = width
            action["crop_height"] = height
            print(f"✅ Crop area added to action: ({x}, {y}) - {width} × {height}")
        else:
            print(f"⚠️ Crop area NOT added - crop_area exists: {self.crop_area is not None}, full_screen: {self.use_full_screen}")
        
        return action
    
    def load_action_data(self, action_data):
        """Load existing action data into the dialog (for editing)"""
        print(f"🔍 load_action_data called")
        print(f"   - use_full_screen in data: {action_data.get('use_full_screen', False)}")
        print(f"   - crop coords in data: crop_x={action_data.get('crop_x')}, crop_y={action_data.get('crop_y')}, crop_width={action_data.get('crop_width')}, crop_height={action_data.get('crop_height')}")
        
        self._action_data = action_data
        self.image_path_input.setText(action_data.get("image_path", ""))
        self.match_number_input.setValue(action_data.get("match_number", 1))
        # Handle both old format (0.0-1.0) and new format (0-100)
        threshold = action_data.get("threshold", 99)
        if isinstance(threshold, float) and threshold <= 1.0:
            # Old format: convert 0.0-1.0 to 0-100
            threshold = int(threshold * 100)
        self.threshold_input.setValue(threshold)
        self.true_actions = action_data.get("true_actions", []).copy()
        self.false_actions = action_data.get("false_actions", []).copy()
        self._populate_sub_action_list(True)
        self._populate_sub_action_list(False)
        
        # Load crop area BEFORE setting checkbox state to prevent it from being cleared
        # Load crop area if present (only if not using full screen)
        use_full_screen = action_data.get("use_full_screen", False)
        if not use_full_screen and "crop_x" in action_data and "crop_y" in action_data and "crop_width" in action_data and "crop_height" in action_data:
            self.crop_area = (
                action_data["crop_x"],
                action_data["crop_y"],
                action_data["crop_width"],
                action_data["crop_height"]
            )
            x, y, width, height = self.crop_area
            print(f"✅ Crop area loaded EARLY: ({x}, {y}) - {width} × {height}")
        else:
            print(f"⚠️ No crop area to load - use_full_screen: {use_full_screen}, has coords: {('crop_x' in action_data and 'crop_y' in action_data)}")
            self.crop_area = None
        
        # Now set the full screen checkbox state
        # Block signals temporarily to prevent automatic triggering of on_full_screen_changed
        self.use_full_screen = use_full_screen
        print(f"   - Setting checkbox to: {self.use_full_screen}")
        self.full_screen_checkbox.blockSignals(True)
        self.full_screen_checkbox.setChecked(self.use_full_screen)
        self.full_screen_checkbox.blockSignals(False)
        
        # Manually update UI state based on checkbox without clearing crop_area
        enabled = not self.use_full_screen
        self.crop_info_label.setEnabled(enabled)
        self.select_area_btn.setEnabled(enabled)
        self.clear_area_btn.setEnabled(enabled)
        
        # Update crop info label and style based on loaded crop area
        if self.crop_area and not self.use_full_screen:
            x, y, width, height = self.crop_area
            self.crop_info_label.setText(f"Area: ({x}, {y}) - {width} × {height} px")
            self.crop_info_label.setStyleSheet("""
                font-size: 11px; 
                color: #1976d2; 
                padding: 8px;
                background-color: #e3f2fd;
                border: 1px solid #42a5f5;
                border-radius: 4px;
                min-height: 28px;
            """)
        else:
            self.crop_info_label.setText("No area selected")
            if enabled:
                self.crop_info_label.setStyleSheet("""
                    font-size: 11px; 
                    color: #666; 
                    padding: 8px;
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    min-height: 28px;
                """)
            else:
                self.crop_info_label.setStyleSheet("""
                    font-size: 11px; 
                    color: #999; 
                    padding: 8px;
                    background-color: #e0e0e0;
                    border: 1px solid #bbb;
                    border-radius: 4px;
                    min-height: 28px;
                """)
        
        print(f"   - Final self.crop_area: {self.crop_area}")
        self.setWindowTitle(get_icon_text('image', 'Edit Image Matcher Action'))


class ImageMatcherActionType(BaseActionType):
    """Action type for image matcher conditional actions"""
    
    def get_type_id(self) -> str:
        return "image_matcher"
    
    def get_display_name(self) -> str:
        return "Image Matcher"
    
    def create_dialog(self, parent=None) -> QDialog:
        return ImageMatcherDialog(parent)
    
    def format_action_display(self, action_data: dict) -> str:
        image_path = action_data.get("image_path", "")
        match_number = action_data.get("match_number", 1)
        threshold = action_data.get("threshold", 99)
        # Handle both old format (0.0-1.0) and new format (0-100)
        if isinstance(threshold, float) and threshold <= 1.0:
            threshold = int(threshold * 100)
        true_actions = action_data.get("true_actions", [])
        false_actions = action_data.get("false_actions", [])
        # Show just filename if path is long
        filename = os.path.basename(image_path) if image_path else "No image"
        true_count = len(true_actions)
        false_count = len(false_actions)
        return f"Image Matcher: {filename} (match #{match_number}, threshold: {threshold}%) → True: {true_count} actions, False: {false_count} actions"
    
    def validate_action_data(self, action_data: dict) -> bool:
        threshold = action_data.get("threshold", 99)
        # Handle both old format (0.0-1.0) and new format (0-100)
        if isinstance(threshold, float) and threshold <= 1.0:
            threshold_valid = 0.0 <= threshold <= 1.0
        else:
            threshold_valid = isinstance(threshold, int) and 0 <= threshold <= 100
        
        return (
            "image_path" in action_data and
            "match_number" in action_data and
            "true_actions" in action_data and
            "false_actions" in action_data and
            isinstance(action_data["match_number"], int) and
            action_data["match_number"] >= 1 and
            threshold_valid and
            isinstance(action_data["true_actions"], list) and
            isinstance(action_data["false_actions"], list)
        )

