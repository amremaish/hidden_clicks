"""Delay action type."""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QSpinBox, QDialogButtonBox, QHBoxLayout

from src.action_types.base import BaseActionType
from src.ui.icons import get_icon, get_icon_text, get_unicode_icon


class DelayActionDialog(QDialog):
    """Dialog for adding a delay action"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(get_icon_text('clock', 'Add Delay Action'))
        self.setModal(True)
        self.setFixedSize(350, 180)
        self._action_data = None
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333;
            }
            QSpinBox {
                background-color: #ffffff;
                border: 2px solid #ccc;
                border-radius: 4px;
                padding: 8px;
                color: #333;
                font-size: 12px;
            }
            QSpinBox:hover {
                border-color: #42a5f5;
            }
            QSpinBox:focus {
                border-color: #42a5f5;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header with icon
        header_layout = QHBoxLayout()
        icon_label = QLabel(get_unicode_icon('clock'))
        icon_label.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon_label)
        label = QLabel("Enter delay in milliseconds:")
        label.setStyleSheet("font-size: 13px; font-weight: bold; color: #333;")
        header_layout.addWidget(label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Delay input
        self.delay_input = QSpinBox()
        self.delay_input.setRange(10, 10000)
        self.delay_input.setValue(300)
        self.delay_input.setSuffix(" ms")
        layout.addWidget(self.delay_input)
        
        layout.addStretch()
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.button(QDialogButtonBox.Ok).setText(get_icon_text('ok', 'Add'))
        button_box.button(QDialogButtonBox.Cancel).setText(get_icon_text('cancel', 'Cancel'))
        button_box.setStyleSheet("""
            QPushButton {
                background-color: #42a5f5;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #64b5f6;
            }
            QPushButton:pressed {
                background-color: #2196f3;
            }
            QPushButton[text*="Cancel"] {
                background-color: #e0e0e0;
                color: #333;
            }
            QPushButton[text*="Cancel"]:hover {
                background-color: #d0d0d0;
            }
        """)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def load_action_data(self, action_data):
        """Load existing action data into the dialog"""
        self._action_data = action_data
        if "ms" in action_data:
            self.delay_input.setValue(action_data["ms"])
        self.setWindowTitle(get_icon_text('clock', 'Edit Delay Action'))
    
    def get_action(self):
        """Return the delay action dictionary"""
        return {"type": "delay", "ms": self.delay_input.value()}


class DelayActionType(BaseActionType):
    """Action type for delays"""
    
    def get_type_id(self) -> str:
        return "delay"
    
    def get_display_name(self) -> str:
        return "Delay"
    
    def create_dialog(self, parent=None) -> QDialog:
        return DelayActionDialog(parent)
    
    def format_action_display(self, action_data: dict) -> str:
        return f"Delay {action_data['ms']} ms"
    
    def validate_action_data(self, action_data: dict) -> bool:
        return "ms" in action_data and isinstance(action_data["ms"], (int, float))

