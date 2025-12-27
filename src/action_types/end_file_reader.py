"""End File Reader action type."""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QDialogButtonBox, QPushButton, QFileDialog, QMessageBox,
    QListWidget, QListWidgetItem, QGroupBox, QScrollArea, QWidget
)
import os

from src.action_types.base import BaseActionType
from src.ui.icons import get_icon, get_icon_text, get_unicode_icon


class EndFileReaderDialog(QDialog):
    """Dialog for adding an end file reader action"""
    def __init__(self, parent=None, max_action_count=1):
        super().__init__(parent)
        self.max_action_count = max_action_count
        # Lazy import to avoid circular dependency
        from src.action_types.registry import get_action_registry
        self.action_registry = get_action_registry()
        self.true_actions = []
        self.false_actions = []
        self._action_data = None
        self.setWindowTitle(get_icon_text('list', 'Add End File Reader Action'))
        self.setModal(True)
        self.setFixedSize(600, 650)
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
        icon_label = QLabel(get_unicode_icon('list'))
        icon_label.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon_label)
        label = QLabel("Configure End File Reader:")
        label.setStyleSheet("font-size: 13px; font-weight: bold; color: #333;")
        header_layout.addWidget(label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # File path input
        file_path_label = QLabel("File Path:")
        file_path_label.setStyleSheet("font-size: 12px; color: #333; font-weight: bold;")
        layout.addWidget(file_path_label)
        
        file_path_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Enter file path or click Browse...")
        file_path_layout.addWidget(self.file_path_input)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.setFixedWidth(90)
        browse_btn.setFixedHeight(35)
        browse_btn.clicked.connect(self.browse_file)
        file_path_layout.addWidget(browse_btn)
        layout.addLayout(file_path_layout)
        
        # Key text input
        key_text_label = QLabel("Key Text (to search in last line):")
        key_text_label.setStyleSheet("font-size: 12px; color: #333; font-weight: bold;")
        layout.addWidget(key_text_label)
        self.key_text_input = QLineEdit()
        self.key_text_input.setPlaceholderText("Enter text to search for")
        layout.addWidget(self.key_text_input)
        
        # True Actions Section
        true_group = QGroupBox("True Actions (execute when key text is found)")
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
        false_group = QGroupBox("False Actions (execute when key text is NOT found)")
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
        main_layout.addWidget(button_box)
        
        # Load action data if provided
        if self._action_data:
            self.load_action_data(self._action_data)
    
    def browse_file(self):
        """Open file browser dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "All Files (*.*)"
        )
        if file_path:
            self.file_path_input.setText(file_path)
    
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
        type_dialog.setFixedSize(300, 400)
        type_dialog.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333;
                font-size: 12px;
            }
        """)
        
        layout = QVBoxLayout(type_dialog)
        label = QLabel("Double-click an action type to add:")
        layout.addWidget(label)
        
        type_list = QListWidget()
        type_list.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                border: 2px solid #ccc;
                border-radius: 4px;
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
        layout.addWidget(type_list)
        
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
                # Note: Most dialogs don't support editing existing actions yet
                # For now, we'll remove and re-add
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
        file_path = self.file_path_input.text().strip()
        key_text = self.key_text_input.text().strip()
        
        if not file_path:
            QMessageBox.warning(self, "Validation Error", "Please enter a file path.")
            return
        
        if not key_text:
            QMessageBox.warning(self, "Validation Error", "Please enter a key text to search for.")
            return
        
        if not os.path.exists(file_path):
            reply = QMessageBox.question(
                self,
                "File Not Found",
                f"File not found: {file_path}\nDo you want to continue anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        self.accept()
    
    def get_action(self):
        """Return the end file reader action dictionary"""
        return {
            "type": "end_file_reader",
            "file_path": self.file_path_input.text().strip(),
            "key_text": self.key_text_input.text().strip(),
            "true_actions": self.true_actions.copy(),
            "false_actions": self.false_actions.copy()
        }
    
    def load_action_data(self, action_data):
        """Load existing action data into the dialog (for editing)"""
        self._action_data = action_data
        self.file_path_input.setText(action_data.get("file_path", ""))
        self.key_text_input.setText(action_data.get("key_text", ""))
        self.true_actions = action_data.get("true_actions", []).copy()
        self.false_actions = action_data.get("false_actions", []).copy()
        self._populate_sub_action_list(True)
        self._populate_sub_action_list(False)
        self.setWindowTitle(get_icon_text('list', 'Edit End File Reader Action'))


class EndFileReaderActionType(BaseActionType):
    """Action type for end file reader conditional jumps"""
    
    def get_type_id(self) -> str:
        return "end_file_reader"
    
    def get_display_name(self) -> str:
        return "End File Reader"
    
    def create_dialog(self, parent=None) -> QDialog:
        # Get current action count from parent if available
        max_count = 1
        if parent and hasattr(parent, 'action_list'):
            max_count = parent.action_list.count() + 1
        return EndFileReaderDialog(parent, max_count)
    
    def format_action_display(self, action_data: dict) -> str:
        file_path = action_data.get("file_path", "")
        key_text = action_data.get("key_text", "")
        true_actions = action_data.get("true_actions", [])
        false_actions = action_data.get("false_actions", [])
        # Show just filename if path is long
        filename = os.path.basename(file_path) if file_path else "No file"
        true_count = len(true_actions)
        false_count = len(false_actions)
        return f"End File Reader: {filename} → '{key_text}' → True: {true_count} actions, False: {false_count} actions"
    
    def validate_action_data(self, action_data: dict) -> bool:
        return (
            "file_path" in action_data and
            "key_text" in action_data and
            "true_actions" in action_data and
            "false_actions" in action_data and
            isinstance(action_data["true_actions"], list) and
            isinstance(action_data["false_actions"], list)
        )

