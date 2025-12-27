"""Image Matcher action type."""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QDialogButtonBox, QPushButton, QFileDialog, QMessageBox,
    QListWidget, QListWidgetItem, QGroupBox, QScrollArea, QWidget, QSpinBox
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
    
    def validate_and_accept(self):
        """Validate inputs before accepting"""
        image_path = self.image_path_input.text().strip()
        match_number = self.match_number_input.value()
        
        if not image_path:
            QMessageBox.warning(self, "Validation Error", "Please enter an image path.")
            return
        
        if not os.path.exists(image_path):
            reply = QMessageBox.question(
                self,
                "File Not Found",
                f"Image file not found: {image_path}\nDo you want to continue anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # Check if it's a valid image file
        valid_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
        if not any(image_path.lower().endswith(ext) for ext in valid_extensions):
            QMessageBox.warning(
                self,
                "Invalid File",
                "Please select a valid image file (PNG, JPG, JPEG, BMP, or GIF)."
            )
            return
        
        if match_number < 1:
            QMessageBox.warning(self, "Validation Error", "Match number must be at least 1.")
            return
        
        self.accept()
    
    def get_action(self):
        """Return the image matcher action dictionary"""
        return {
            "type": "image_matcher",
            "image_path": self.image_path_input.text().strip(),
            "match_number": self.match_number_input.value(),
            "true_actions": self.true_actions.copy(),
            "false_actions": self.false_actions.copy()
        }
    
    def load_action_data(self, action_data):
        """Load existing action data into the dialog (for editing)"""
        self._action_data = action_data
        self.image_path_input.setText(action_data.get("image_path", ""))
        self.match_number_input.setValue(action_data.get("match_number", 1))
        self.true_actions = action_data.get("true_actions", []).copy()
        self.false_actions = action_data.get("false_actions", []).copy()
        self._populate_sub_action_list(True)
        self._populate_sub_action_list(False)
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
        true_actions = action_data.get("true_actions", [])
        false_actions = action_data.get("false_actions", [])
        # Show just filename if path is long
        filename = os.path.basename(image_path) if image_path else "No image"
        true_count = len(true_actions)
        false_count = len(false_actions)
        return f"Image Matcher: {filename} (match #{match_number}) → True: {true_count} actions, False: {false_count} actions"
    
    def validate_action_data(self, action_data: dict) -> bool:
        return (
            "image_path" in action_data and
            "match_number" in action_data and
            "true_actions" in action_data and
            "false_actions" in action_data and
            isinstance(action_data["match_number"], int) and
            action_data["match_number"] >= 1 and
            isinstance(action_data["true_actions"], list) and
            isinstance(action_data["false_actions"], list)
        )

