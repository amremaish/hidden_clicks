import ctypes
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLineEdit, QListWidget,
    QPushButton, QMessageBox, QLabel, QHBoxLayout
)
import win32gui
import win32process
import ctypes as c

from src.capture import CoordinateCaptureWindow


class OTClientSelector(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select OTClientV8 Window")
        self.setGeometry(100, 100, 600, 400)
        self.center_window()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.textChanged.connect(self.update_list)
        layout.addWidget(self.search_input)

        lists_layout = QHBoxLayout()
        self.available_listbox = QListWidget()
        self.selected_listbox = QListWidget()

        self.available_listbox.itemDoubleClicked.connect(self.select_process)
        self.selected_listbox.itemDoubleClicked.connect(self.remove_process)
        layout.addLayout(lists_layout)

        lists_layout.addWidget(self.available_listbox)
        lists_layout.addWidget(self.selected_listbox)

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.handle_start)
        layout.addWidget(self.start_button)

        self.windows = []
        self.selected_windows = []
        self.update_list()

    def center_window(self):
        frame = self.frameGeometry()
        screen_center = self.screen().availableGeometry().center()
        frame.moveCenter(screen_center)
        self.move(frame.topLeft())

    def update_list(self):
        self.available_listbox.clear()
        self.windows.clear()

        def enum_handler(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).strip()
                if title and self.search_input.text().lower() in title.lower():
                    if title not in self.selected_windows:
                        self.windows.append(title)

        win32gui.EnumWindows(enum_handler, None)
        self.available_listbox.addItems(self.windows)

    def select_process(self, item):
        process_name = item.text().strip()
        if process_name and process_name not in self.selected_windows:
            self.selected_windows.append(process_name)
            self.selected_listbox.addItem(process_name)
            self.update_list()

    def remove_process(self, item):
        process_name = item.text().strip()
        if process_name in self.selected_windows:
            self.selected_windows.remove(process_name)
            self.selected_listbox.takeItem(self.selected_listbox.row(item))
            self.update_list()


    def handle_start(self):
        self.attached_processes = []

        for name in self.selected_windows:
            try:
                hwnd = win32gui.FindWindow(None, name)
                if hwnd == 0:
                    raise Exception("Window not found.")

                # Loading Addresses
                game = win32gui.FindWindow(None, name)
                proc_id = win32process.GetWindowThreadProcessId(game)
                proc_id = proc_id[1]
                process_handle = c.windll.kernel32.OpenProcess(0x1F0FFF, False, proc_id)
                modules = win32process.EnumProcessModules(process_handle)
                base_address = modules[0]

                self.attached_processes.append((name, game, base_address))

                print(f"{name} -> HWND: {proc_id}, Base Address: {base_address}")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to attach to {name}:\n{e}")

        if self.attached_processes:
            self.capture_window = CoordinateCaptureWindow(self.attached_processes)
            self.capture_window.show()
            self.capture_window.raise_()
            self.capture_window.activateWindow()
            self.hide()
        else:
            QMessageBox.warning(self, "No processes", "No processes were successfully attached.")
