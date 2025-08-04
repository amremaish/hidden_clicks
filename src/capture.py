from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QListWidget, QComboBox, QSpinBox, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
import threading
import queue
import json
import os
from pynput import mouse

from src.action_loop import start_threads_for_all

ACTIONS_PATH = "actions.json"


class CoordinateCaptureWindow(QWidget):
    def __init__(self, attached_processes):
        super().__init__()
        self.setWindowTitle("Capture Actions")
        self.setGeometry(600, 300, 600, 650)
        self.center_window()

        self.coord_queue = queue.Queue()
        self.attached_processes = attached_processes
        self.running = False
        self.actions = []
        self.window_titles = [name for name, hwnd, base in self.attached_processes]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # --- Label: Processes
        processes_label = QLabel("Processes:")
        layout.addWidget(processes_label)

        # --- Scrollable process names
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedHeight(100)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setAlignment(Qt.AlignTop)

        all_titles = "<br>".join(f"• {title}" for title in self.window_titles)
        label = QLabel(all_titles)
        label.setStyleSheet("font-size: 11px; color: #ccc;")
        label.setTextFormat(Qt.RichText)
        label.setWordWrap(True)

        scroll_layout.addWidget(label)
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        # --- Action List
        layout.addWidget(QLabel("Action List:"))
        self.action_list = QListWidget()
        layout.addWidget(self.action_list)

        # --- Action controls
        action_row = QHBoxLayout()
        self.action_type = QComboBox()
        self.action_type.addItems(["Left Click", "Double Click", "Delay"])

        self.delay_input = QSpinBox()
        self.delay_input.setRange(10, 10000)
        self.delay_input.setValue(300)
        self.delay_input.setSuffix(" ms")
        self.delay_input.setFixedWidth(100)

        add_button = QPushButton("Add Action")
        add_button.clicked.connect(self.capture_action_location)

        action_row.addWidget(self.action_type)
        action_row.addWidget(self.delay_input)
        action_row.addWidget(add_button)
        layout.addLayout(action_row)

        # --- Remove selected
        remove_btn = QPushButton("Remove Selected Action")
        remove_btn.clicked.connect(self.remove_action)
        layout.addWidget(remove_btn)

        # --- Start button
        self.start_button = QPushButton("Start")
        self.start_button.setStyleSheet("background-color: #067c33; color: white; font-weight: bold;")
        self.start_button.setMinimumHeight(40)
        self.start_button.clicked.connect(self.start_loop)
        layout.addWidget(self.start_button)

        # --- Hint
        hint_label = QLabel("Press F7 to pause & F8 to continue.")
        hint_label.setStyleSheet("color: orange; font-size: 11px; padding-left: 10px;")
        layout.addWidget(hint_label)

        self.timer = QTimer()
        self.timer.timeout.connect(self.check_queue)
        self.timer.start(100)

        self.load_actions()

    def center_window(self):
        frame = self.frameGeometry()
        screen_center = self.screen().availableGeometry().center()
        frame.moveCenter(screen_center)
        self.move(frame.topLeft())

    def capture_action_location(self):
        import win32con, ctypes

        action_type = self.action_type.currentText()
        if action_type == "Delay":
            delay = self.delay_input.value()
            self.actions.append({"type": "delay", "ms": delay})
            self.action_list.addItem(f"Delay {delay} ms")
            self.save_actions()
            return

        QMessageBox.information(self, "Click", f"Click anywhere to capture coordinates for {action_type}.")

        def click_listener():
            ctypes.windll.user32.SetSystemCursor(
                ctypes.windll.user32.LoadCursorW(0, win32con.IDC_CROSS), 32512
            )

            def on_click(x, y, button, pressed):
                if pressed:
                    ctypes.windll.user32.SystemParametersInfoW(87, 0, None, 0)
                    self.coord_queue.put((action_type.lower().replace(" ", "_"), x, y))
                    return False

            with mouse.Listener(on_click=on_click) as listener:
                listener.join()

        threading.Thread(target=click_listener, daemon=True).start()

    def check_queue(self):
        try:
            while True:
                action_type, x, y = self.coord_queue.get_nowait()
                action = {"type": action_type, "x": x, "y": y}
                self.actions.append(action)
                self.action_list.addItem(f"{action_type.replace('_', ' ').title()} at ({x}, {y})")
                self.save_actions()
        except queue.Empty:
            pass

    def remove_action(self):
        row = self.action_list.currentRow()
        if row >= 0:
            self.action_list.takeItem(row)
            self.actions.pop(row)
            self.save_actions()

    def start_loop(self):
        if self.running:
            return
        self.running = True
        self.start_button.setEnabled(False)
        self.start_button.setStyleSheet("background-color: #067c33; color: white; font-weight: bold;")
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
                if action["type"] == "delay":
                    self.action_list.addItem(f"Delay {action['ms']} ms")
                else:
                    self.action_list.addItem(
                        f"{action['type'].replace('_', ' ').title()} at ({action['x']}, {action['y']})"
                    )
        except Exception as e:
            print(f"❌ Failed to load actions: {e}")
