"""Hotkey action type."""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import pyqtSignal, QObject
import threading
import keyboard

from src.action_types.base import BaseActionType
from src.ui.icons import get_icon, get_icon_text, get_unicode_icon


class HotkeySignal(QObject):
    """Signal object for thread-safe UI updates"""
    hotkey_captured = pyqtSignal(str, bool, bool, bool)  # key, ctrl, alt, shift


class HotkeyActionDialog(QDialog):
    """Dialog for capturing hotkey actions"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.captured_hotkey = None
        self.captured_key = None
        self.captured_ctrl = False
        self.captured_alt = False
        self.captured_shift = False
        self.listener = None
        self._action_data = None
        
        # Signal for thread-safe UI updates
        self.signal = HotkeySignal()
        self.signal.hotkey_captured.connect(self.on_hotkey_captured)
        
        self.setWindowTitle(get_icon_text('keyboard', 'Add Hotkey Action'))
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
        icon_label = QLabel(get_unicode_icon('keyboard'))
        icon_label.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon_label)
        self.instructions_label = QLabel(
            "Press any key or key combination (e.g., Ctrl+X, F1, 0) to capture it."
        )
        self.instructions_label.setWordWrap(True)
        self.instructions_label.setStyleSheet("font-size: 13px; color: #333;")
        header_layout.addWidget(self.instructions_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Hotkey display
        self.hotkey_label = QLabel("")
        self.hotkey_label.setStyleSheet("""
            color: #42a5f5;
            font-weight: bold;
            font-size: 14px;
            padding: 10px;
            background-color: #e3f2fd;
            border-radius: 4px;
            border: 2px solid #42a5f5;
        """)
        layout.addWidget(self.hotkey_label)
        
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
        
        # Load action data if provided (for editing)
        if self._action_data:
            self.load_action_data(self._action_data)
        else:
            # Start hotkey capture only if not editing
            self.start_capture()
    
    def start_capture(self):
        """Start the keyboard listener to capture hotkeys"""
        # Track modifier states manually
        self._modifier_states = {'ctrl': False, 'alt': False, 'shift': False}
        
        def on_key_press(event):
            key_name = event.name.lower()
            
            # Track modifier key states (handle various naming conventions)
            is_modifier = False
            if key_name in ['ctrl', 'ctrl_l', 'ctrl_r', 'ctrl left', 'ctrl right', 'left ctrl', 'right ctrl']:
                self._modifier_states['ctrl'] = True
                is_modifier = True
            elif key_name in ['alt', 'alt_l', 'alt_r', 'alt left', 'alt right', 'left alt', 'right alt']:
                self._modifier_states['alt'] = True
                is_modifier = True
            elif key_name in ['shift', 'shift_l', 'shift_r', 'shift left', 'shift right', 'left shift', 'right shift']:
                self._modifier_states['shift'] = True
                is_modifier = True
            
            # If it's a modifier key, continue listening
            if is_modifier:
                return True
            
            # If it's a non-modifier key, capture it with current modifier states
            ctrl_pressed = self._modifier_states['ctrl']
            alt_pressed = self._modifier_states['alt']
            shift_pressed = self._modifier_states['shift']
            
            # Also check using keyboard.is_pressed for more reliable detection
            try:
                if keyboard.is_pressed('ctrl'):
                    ctrl_pressed = True
            except:
                pass
            
            try:
                if keyboard.is_pressed('alt'):
                    alt_pressed = True
            except:
                pass
            
            try:
                if keyboard.is_pressed('shift'):
                    shift_pressed = True
            except:
                pass
            
            # Emit signal for thread-safe UI update
            self.signal.hotkey_captured.emit(key_name, ctrl_pressed, alt_pressed, shift_pressed)
            # Unhook to stop listening
            try:
                keyboard.unhook_all()
            except:
                pass
            return False  # Stop listener after capturing
        
        def on_key_release(event):
            # Update modifier states when released
            key_name = event.name.lower()
            if key_name in ['ctrl', 'ctrl_l', 'ctrl_r', 'ctrl left', 'ctrl right', 'left ctrl', 'right ctrl']:
                self._modifier_states['ctrl'] = False
            elif key_name in ['alt', 'alt_l', 'alt_r', 'alt left', 'alt right', 'left alt', 'right alt']:
                self._modifier_states['alt'] = False
            elif key_name in ['shift', 'shift_l', 'shift_r', 'shift left', 'shift right', 'left shift', 'right shift']:
                self._modifier_states['shift'] = False
        
        def key_listener():
            try:
                keyboard.on_press(on_key_press)
                keyboard.on_release(on_key_release)
                keyboard.wait()  # Keep listener alive
            except Exception as e:
                print(f"Error in key listener: {e}")
        
        self.listener = threading.Thread(target=key_listener, daemon=True)
        self.listener.start()
    
    def on_hotkey_captured(self, key, ctrl, alt, shift):
        """Handle hotkey captured signal (called on main thread)"""
        self.captured_key = key
        self.captured_ctrl = ctrl
        self.captured_alt = alt
        self.captured_shift = shift
        
        # Format hotkey display
        modifiers = []
        if ctrl:
            modifiers.append("Ctrl")
        if alt:
            modifiers.append("Alt")
        if shift:
            modifiers.append("Shift")
        
        # Format key name for display
        key_display = key.upper() if len(key) == 1 else key.title()
        
        if modifiers:
            hotkey_display = "+".join(modifiers) + "+" + key_display
        else:
            hotkey_display = key_display
        
        self.hotkey_label.setText(f"✓ Hotkey captured: {hotkey_display}")
        self.instructions_label.setText("✓ Hotkey captured! Click 'Add to Actions' to add this action.")
        self.instructions_label.setStyleSheet("font-size: 13px; color: #4caf50; font-weight: bold;")
        self.add_button.setEnabled(True)
    
    def closeEvent(self, event):
        """Clean up when dialog closes"""
        # Stop keyboard listener if running
        try:
            keyboard.unhook_all()
        except:
            pass
        super().closeEvent(event)
    
    def load_action_data(self, action_data):
        """Load existing action data into the dialog"""
        self._action_data = action_data
        if "key" in action_data:
            self.captured_key = action_data["key"]
            self.captured_ctrl = action_data.get("ctrl", False)
            self.captured_alt = action_data.get("alt", False)
            self.captured_shift = action_data.get("shift", False)
            
            # Format hotkey display
            modifiers = []
            if self.captured_ctrl:
                modifiers.append("Ctrl")
            if self.captured_alt:
                modifiers.append("Alt")
            if self.captured_shift:
                modifiers.append("Shift")
            
            key_display = self.captured_key.upper() if len(self.captured_key) == 1 else self.captured_key.title()
            
            if modifiers:
                hotkey_display = "+".join(modifiers) + "+" + key_display
            else:
                hotkey_display = key_display
            
            self.hotkey_label.setText(f"Hotkey: {hotkey_display}")
            self.instructions_label.setText("Click 'Add to Actions' to save changes, or press a key to capture a new hotkey.")
            self.instructions_label.setStyleSheet("font-size: 13px; color: #333;")
            self.add_button.setEnabled(True)
            self.add_button.setText(get_icon_text('ok', 'Update Action'))
            self.setWindowTitle(get_icon_text('keyboard', 'Edit Hotkey Action'))
            # Still allow capturing new hotkeys
            self.start_capture()
    
    def get_action(self):
        """Return the hotkey action dictionary"""
        if self.captured_key:
            return {
                "type": "hotkey",
                "key": self.captured_key,
                "ctrl": self.captured_ctrl,
                "alt": self.captured_alt,
                "shift": self.captured_shift
            }
        return None


class HotkeyActionType(BaseActionType):
    """Action type for hotkeys"""
    
    def get_type_id(self) -> str:
        return "hotkey"
    
    def get_display_name(self) -> str:
        return "Hotkey"
    
    def create_dialog(self, parent=None) -> QDialog:
        return HotkeyActionDialog(parent)
    
    def format_action_display(self, action_data: dict) -> str:
        key = action_data.get("key", "")
        ctrl = action_data.get("ctrl", False)
        alt = action_data.get("alt", False)
        shift = action_data.get("shift", False)
        
        modifiers = []
        if ctrl:
            modifiers.append("Ctrl")
        if alt:
            modifiers.append("Alt")
        if shift:
            modifiers.append("Shift")
        
        key_display = key.upper() if len(key) == 1 else key.title()
        
        if modifiers:
            return f"Hotkey: {'+'.join(modifiers)}+{key_display}"
        else:
            return f"Hotkey: {key_display}"
    
    def validate_action_data(self, action_data: dict) -> bool:
        return (
            "key" in action_data and
            isinstance(action_data.get("ctrl", False), bool) and
            isinstance(action_data.get("alt", False), bool) and
            isinstance(action_data.get("shift", False), bool)
        )

