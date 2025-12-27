from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QListWidget, QMessageBox, QDialog, QListWidgetItem,
    QGroupBox, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
import json
import os

from src.action_loop import start_threads_for_all
from src.action_types import get_action_registry
from src.ui.icons import get_icon, get_icon_text, get_unicode_icon

ACTIONS_PATH = "actions.json"


class ActionListItemWidget(QWidget):
    """Custom widget for action list items with move up/down and remove buttons"""
    move_up = pyqtSignal()
    move_down = pyqtSignal()
    remove = pyqtSignal()
    
    def __init__(self, text, icon_name, parent=None):
        super().__init__(parent)
        self.setup_ui(text, icon_name)
    
    def setup_ui(self, text, icon_name):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        
        # Icon and text
        icon_label = QLabel(get_unicode_icon(icon_name))
        icon_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(icon_label)
        
        text_label = QLabel(text)
        text_label.setStyleSheet("color: #333; font-size: 12px;")
        text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(text_label)
        
        # Buttons
        move_up_btn = QPushButton("↑")
        move_up_btn.setToolTip("Move up")
        move_up_btn.setFixedSize(30, 25)
        move_up_btn.setStyleSheet("""
            QPushButton {
                background-color: #42a5f5;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #64b5f6;
            }
            QPushButton:pressed {
                background-color: #2196f3;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #888;
            }
        """)
        move_up_btn.clicked.connect(self.move_up.emit)
        
        move_down_btn = QPushButton("↓")
        move_down_btn.setToolTip("Move down")
        move_down_btn.setFixedSize(30, 25)
        move_down_btn.setStyleSheet("""
            QPushButton {
                background-color: #42a5f5;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #64b5f6;
            }
            QPushButton:pressed {
                background-color: #2196f3;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #888;
            }
        """)
        move_down_btn.clicked.connect(self.move_down.emit)
        
        remove_btn = QPushButton(get_unicode_icon('remove'))
        remove_btn.setToolTip("Remove")
        remove_btn.setFixedSize(30, 25)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f44336;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        remove_btn.clicked.connect(self.remove.emit)
        
        layout.addWidget(move_up_btn)
        layout.addWidget(move_down_btn)
        layout.addWidget(remove_btn)
        
        self.move_up_btn = move_up_btn
        self.move_down_btn = move_down_btn


class CoordinateCaptureWindow(QWidget):
    def __init__(self, attached_processes):
        super().__init__()
        self.setWindowTitle("Capture Actions")
        self.setGeometry(600, 300, 800, 650)
        self.center_window()

        self.attached_processes = attached_processes
        self.running = False
        self.actions = []
        self.window_titles = [name for name, hwnd, base in self.attached_processes]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # --- Main horizontal split: Left controls and Right action list
        main_horizontal = QHBoxLayout()
        main_horizontal.setSpacing(15)

        # --- Left side: Action controls
        left_group = QGroupBox()
        left_group.setTitle(get_icon_text('add', 'Action Types'))
        left_controls = QVBoxLayout(left_group)
        left_controls.setContentsMargins(10, 15, 10, 10)
        left_controls.setSpacing(10)

        # Action type list
        action_type_label = QLabel(get_icon_text('info', 'Double-click an action type to add it'))
        action_type_label.setStyleSheet("color: #666; font-size: 10px; padding: 5px;")
        left_controls.addWidget(action_type_label)
        
        self.action_type = QListWidget()
        self.action_type.setSelectionMode(QListWidget.SingleSelection)
        self.action_type.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f0f0f0;
                padding: 5px;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 3px;
                margin: 2px;
                color: #333;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
            QListWidget::item:selected {
                background-color: #42a5f5;
                color: white;
            }
        """)
        
        # Get action types from registry
        self.action_registry = get_action_registry()
        self._populate_action_types()
        self.action_type.setFixedHeight(200)
        # Connect double-click signal
        self.action_type.itemDoubleClicked.connect(self.on_action_type_double_clicked)
        left_controls.addWidget(self.action_type)

        # Add stretch to push controls to top
        left_controls.addStretch()

        # --- Right side: Action List
        right_group = QGroupBox()
        right_group.setTitle(get_icon_text('list', 'Action Sequence'))
        right_actions = QVBoxLayout(right_group)
        right_actions.setContentsMargins(10, 15, 10, 10)
        right_actions.setSpacing(10)
        
        action_list_info = QLabel(get_icon_text('info', 'Actions will execute in order'))
        action_list_info.setStyleSheet("color: #666; font-size: 10px; padding: 5px;")
        right_actions.addWidget(action_list_info)
        
        self.action_list = QListWidget()
        self.action_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f0f0f0;
                padding: 5px;
            }
            QListWidget::item {
                border-radius: 3px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
            }
        """)
        self.action_list.itemDoubleClicked.connect(self.on_action_double_clicked)
        right_actions.addWidget(self.action_list)

        # Add groups to horizontal layout
        main_horizontal.addWidget(left_group, 1)
        main_horizontal.addWidget(right_group, 1)

        layout.addLayout(main_horizontal)

        # --- Start button
        self.start_button = QPushButton(get_icon_text('play', 'Start Automation'))
        self.start_button.setIcon(get_icon('play'))
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #067c33;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0a9d47;
            }
            QPushButton:pressed {
                background-color: #055a26;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
        """)
        self.start_button.setMinimumHeight(45)
        self.start_button.clicked.connect(self.start_loop)
        layout.addWidget(self.start_button)

        # --- Hint
        hint_label = QLabel(get_icon_text('info', 'Press F7 to pause & F8 to continue'))
        hint_label.setStyleSheet("color: #ff9800; font-size: 11px; padding: 8px; background-color: #fff3e0; border: 1px solid #ffb74d; border-radius: 4px;")
        layout.addWidget(hint_label)
        
        # --- Processes at bottom (comma-separated)
        processes_text = ", ".join(self.window_titles)
        processes_label = QLabel(f"Attached processes: {processes_text}")
        processes_label.setStyleSheet("color: #666; font-size: 10px; padding: 5px;")
        processes_label.setWordWrap(True)
        layout.addWidget(processes_label)
        
        # Apply group box styling
        self._apply_group_box_styling()


        self.load_actions()

    def _apply_group_box_styling(self):
        """Apply consistent styling to all group boxes"""
        group_style = """
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #ccc;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #f5f5f5;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #1976d2;
            }
        """
        for widget in self.findChildren(QGroupBox):
            widget.setStyleSheet(group_style)

    def _populate_action_types(self):
        """Populate action type list with icons"""
        icon_map = {
            'Delay': 'clock',
            'Left Click': 'mouse',
            'Double Click': 'mouse',
            'End File Reader': 'list',
            'Hotkey': 'keyboard',
        }
        
        for display_name in self.action_registry.get_all_display_names():
            item = QListWidgetItem(get_icon_text(icon_map.get(display_name, 'list'), display_name))
            item.setIcon(get_icon(icon_map.get(display_name, 'list')))
            self.action_type.addItem(item)

    def center_window(self):
        frame = self.frameGeometry()
        screen_center = self.screen().availableGeometry().center()
        frame.moveCenter(screen_center)
        self.move(frame.topLeft())

    def on_action_type_double_clicked(self, item):
        """Handle double-click on action type - open appropriate dialog"""
        # Extract display name (remove icon if present)
        display_name = item.text()
        # Remove icon character if present
        for icon_name in ['clock', 'mouse', 'list', 'process', 'keyboard']:
            icon_char = get_unicode_icon(icon_name)
            if icon_char and display_name.startswith(icon_char):
                display_name = display_name.replace(icon_char, '').strip()
                break
        
        action_type = self.action_registry.get_by_display_name(display_name)
        
        if action_type is None:
            QMessageBox.warning(self, "Error", f"Unknown action type: {display_name}")
            return
        
        # Create dialog for this action type
        # Update max action count for dialogs that need it (like End File Reader)
        dialog = action_type.create_dialog(self)
        if hasattr(dialog, 'update_max_action_count'):
            dialog.update_max_action_count(self.action_list.count() + 1)
        
        if dialog.exec_() == QDialog.Accepted:
            # Get action data from dialog
            if hasattr(dialog, 'get_action'):
                action = dialog.get_action()
                if action and action_type.validate_action_data(action):
                    self.actions.append(action)
                    display_text = action_type.format_action_display(action)
                    self._add_action_to_list(action, display_text)
                    self.save_actions()
                else:
                    QMessageBox.warning(self, "Error", "Invalid action data")
    
    def on_action_double_clicked(self, item):
        """Handle double-click on action in the list - edit the action"""
        row = self.action_list.row(item)
        if 0 <= row < len(self.actions):
            action = self.actions[row]
            action_type = self.action_registry.get_by_type_id(action.get("type", ""))
            
            if action_type is None:
                QMessageBox.warning(self, "Error", f"Unknown action type: {action.get('type', '')}")
                return
            
            # Create dialog for editing
            dialog = action_type.create_dialog(self)
            
            # Load existing action data into dialog if supported
            if hasattr(dialog, 'load_action_data'):
                dialog.load_action_data(action)
            elif hasattr(dialog, 'update_max_action_count'):
                dialog.update_max_action_count(self.action_list.count())
            
            if dialog.exec_() == QDialog.Accepted:
                # Get updated action data from dialog
                if hasattr(dialog, 'get_action'):
                    updated_action = dialog.get_action()
                    if updated_action and action_type.validate_action_data(updated_action):
                        # Update the action
                        self.actions[row] = updated_action
                        # Rebuild the list to show updated display
                        self._rebuild_action_list()
                        self.save_actions()
                    else:
                        QMessageBox.warning(self, "Error", "Invalid action data")

    def remove_action(self, row):
        """Remove action at specified row"""
        if 0 <= row < len(self.actions):
            self.action_list.takeItem(row)
            self.actions.pop(row)
            self.save_actions()
            self._update_move_buttons()
    
    def move_action_up(self, row):
        """Move action up in the list"""
        if row > 0:
            # Swap actions
            self.actions[row], self.actions[row - 1] = self.actions[row - 1], self.actions[row]
            # Rebuild the list
            self._rebuild_action_list()
            self._update_move_buttons()
            self.save_actions()
    
    def move_action_down(self, row):
        """Move action down in the list"""
        if row < len(self.actions) - 1:
            # Swap actions
            self.actions[row], self.actions[row + 1] = self.actions[row + 1], self.actions[row]
            # Rebuild the list
            self._rebuild_action_list()
            self._update_move_buttons()
            self.save_actions()
    
    def _rebuild_action_list(self):
        """Rebuild the entire action list"""
        self.action_list.clear()
        for action in self.actions:
            action_type = self.action_registry.get_by_type_id(action.get("type", ""))
            if action_type:
                display_text = action_type.format_action_display(action)
                self._add_action_to_list(action, display_text)
    
    def _update_move_buttons(self):
        """Update move up/down button states based on position"""
        for i in range(self.action_list.count()):
            item = self.action_list.item(i)
            widget = self.action_list.itemWidget(item)
            if widget:
                # Enable/disable move up button
                widget.move_up_btn.setEnabled(i > 0)
                # Enable/disable move down button
                widget.move_down_btn.setEnabled(i < self.action_list.count() - 1)

    def start_loop(self):
        if self.running:
            return
        self.running = True
        self.start_button.setEnabled(False)
        self.start_button.setText(get_icon_text('stop', 'Running...'))
        self.start_button.setIcon(get_icon('stop'))
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #f57c00;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:disabled {
                background-color: #f57c00;
                color: white;
            }
        """)
        start_threads_for_all(self.attached_processes, self.actions)

    def save_actions(self):
        try:
            with open(ACTIONS_PATH, "w") as f:
                json.dump(self.actions, f, indent=2)
        except Exception as e:
            print(f"❌ Failed to save actions: {e}")

    def load_actions(self):
        if not os.path.exists(ACTIONS_PATH):
            return
        try:
            with open(ACTIONS_PATH, "r") as f:
                self.actions = json.load(f)
            for action in self.actions:
                action_type = self.action_registry.get_by_type_id(action.get("type", ""))
                if action_type:
                    display_text = action_type.format_action_display(action)
                    self._add_action_to_list(action, display_text)
                else:
                    # Fallback for unknown action types
                    action_type_str = action.get("type", "unknown")
                    widget = ActionListItemWidget(f"Unknown action: {action_type_str}", 'warning')
                    item = QListWidgetItem()
                    item.setSizeHint(widget.sizeHint())
                    self.action_list.addItem(item)
                    self.action_list.setItemWidget(item, widget)
                    row = self.action_list.count() - 1
                    widget.remove.connect(lambda r=row: self.remove_action(r))
                    self._update_move_buttons()
        except Exception as e:
            print(f"❌ Failed to load actions: {e}")
    
    def _add_action_to_list(self, action, display_text):
        """Add an action to the list with appropriate icon and buttons"""
        action_type_id = action.get("type", "")
        icon_map = {
            'delay': 'clock',
            'left_click': 'mouse',
            'double_click': 'mouse',
            'end_file_reader': 'list',
            'hotkey': 'keyboard',
        }
        icon_name = icon_map.get(action_type_id, 'list')
        
        # Create custom widget
        widget = ActionListItemWidget(display_text, icon_name)
        
        # Create list item
        item = QListWidgetItem()
        item.setSizeHint(widget.sizeHint())
        
        # Add to list first to get the correct row
        self.action_list.addItem(item)
        self.action_list.setItemWidget(item, widget)
        row = self.action_list.count() - 1  # Current row index
        
        # Connect signals with proper row capture using default parameter
        widget.move_up.connect(lambda r=row: self.move_action_up(r))
        widget.move_down.connect(lambda r=row: self.move_action_down(r))
        widget.remove.connect(lambda r=row: self.remove_action(r))
        
        # Update button states after adding
        self._update_move_buttons()
