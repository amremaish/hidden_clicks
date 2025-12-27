"""Common classes shared by action types."""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import pyqtSignal, QObject
import threading
from pynput import mouse

from src.ui.icons import get_icon, get_icon_text, get_unicode_icon


class CoordinateSignal(QObject):
    """Signal object for thread-safe UI updates"""
    coords_captured = pyqtSignal(int, int)


class ClickActionDialog(QDialog):
    """Base dialog for click actions (left click or double click)"""
    def __init__(self, action_type_id, parent=None):
        super().__init__(parent)
        self.action_type_id = action_type_id
        self.captured_coords = None
        self.listener = None
        
        # Signal for thread-safe UI updates
        self.signal = CoordinateSignal()
        self.signal.coords_captured.connect(self.on_coords_captured)
        
        action_name = action_type_id.replace("_", " ").title()
        self.setWindowTitle(get_icon_text('mouse', f"Add {action_name} Action"))
        self.setModal(True)
        self.setFixedSize(450, 220)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header with icon
        header_layout = QHBoxLayout()
        icon_label = QLabel(get_unicode_icon('mouse'))
        icon_label.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon_label)
        self.instructions_label = QLabel(
            f"Click anywhere on screen to capture coordinates for {action_name}."
        )
        self.instructions_label.setWordWrap(True)
        self.instructions_label.setStyleSheet("font-size: 13px; color: #333;")
        header_layout.addWidget(self.instructions_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Coordinates display
        self.coords_label = QLabel("")
        self.coords_label.setStyleSheet("""
            color: #42a5f5;
            font-weight: bold;
            font-size: 14px;
            padding: 10px;
            background-color: #e3f2fd;
            border-radius: 4px;
            border: 2px solid #42a5f5;
        """)
        layout.addWidget(self.coords_label)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        self.add_button = QPushButton(get_icon_text('ok', 'Add to Actions'))
        self.add_button.setIcon(get_icon('ok'))
        self.add_button.setEnabled(False)
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #42a5f5;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #64b5f6;
            }
            QPushButton:pressed {
                background-color: #2196f3;
            }
            QPushButton:disabled {
                background-color: #e0e0e0;
                color: #999;
            }
        """)
        self.add_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton(get_icon_text('cancel', 'Cancel'))
        self.cancel_button.setIcon(get_icon('cancel'))
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                color: #333;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QPushButton:pressed {
                background-color: #bdbdbd;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        # Start coordinate capture
        self.start_capture()
        
    def start_capture(self):
        """Start the mouse listener to capture coordinates"""
        import win32con
        import ctypes
        
        # Change cursor to crosshair
        ctypes.windll.user32.SetSystemCursor(
            ctypes.windll.user32.LoadCursorW(0, win32con.IDC_CROSS), 32512
        )
        
        def on_click(x, y, button, pressed):
            if pressed:
                # Restore cursor
                ctypes.windll.user32.SystemParametersInfoW(87, 0, None, 0)
                # Emit signal for thread-safe UI update
                self.signal.coords_captured.emit(x, y)
                return False
        
        def click_listener():
            with mouse.Listener(on_click=on_click) as listener:
                listener.join()
        
        self.listener = threading.Thread(target=click_listener, daemon=True)
        self.listener.start()
        
    def on_coords_captured(self, x, y):
        """Handle coordinates captured signal (called on main thread)"""
        self.captured_coords = (x, y)
        self.coords_label.setText(f"✓ Coordinates captured: ({x}, {y})")
        self.instructions_label.setText("✓ Coordinates captured! Click 'Add to Actions' to add this action.")
        self.instructions_label.setStyleSheet("font-size: 13px; color: #4caf50; font-weight: bold;")
        self.add_button.setEnabled(True)
            
    def closeEvent(self, event):
        """Restore cursor when dialog closes"""
        import ctypes
        ctypes.windll.user32.SystemParametersInfoW(87, 0, None, 0)
        super().closeEvent(event)
        
    def get_action(self):
        """Return the click action dictionary"""
        if self.captured_coords:
            x, y = self.captured_coords
            return {"type": self.action_type_id, "x": x, "y": y}
        return None

