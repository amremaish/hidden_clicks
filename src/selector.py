import ctypes
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLineEdit, QListWidget,
    QPushButton, QMessageBox, QLabel, QHBoxLayout
)
import win32gui
import win32process
import win32con
import ctypes as c

from src.capture import CoordinateCaptureWindow


def find_window_flexible(search_title):
    """
    Find window by flexible matching:
    1. Exact title match
    2. Partial title match (contains)
    3. Process name match
    
    Returns: (hwnd, actual_title) or (None, None) if not found
    """
    # Try exact match first
    hwnd = win32gui.FindWindow(None, search_title)
    if hwnd != 0:
        return (hwnd, search_title)
    
    # Try partial match (window title contains search_title)
    found_hwnd = None
    found_title = None
    
    def enum_handler(hwnd, _):
        nonlocal found_hwnd, found_title
        if found_hwnd:  # Already found, skip
            return
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd).strip()
            if title and search_title.lower() in title.lower():
                found_hwnd = hwnd
                found_title = title
    
    win32gui.EnumWindows(enum_handler, None)
    
    if found_hwnd:
        return (found_hwnd, found_title)
    
    # Try reverse partial match (search_title contains window title keywords)
    # This helps if user saved "Tibia - Byte" but title is now "Tibia - Byte - 3233859lvl"
    keywords = search_title.split()
    if len(keywords) >= 2:  # At least 2 words to match
        found_hwnd = None
        found_title = None
        
        def enum_handler2(hwnd, _):
            nonlocal found_hwnd, found_title
            if found_hwnd:
                return
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).strip()
                if title:
                    # Check if all keywords appear in the title
                    title_lower = title.lower()
                    if all(keyword.lower() in title_lower for keyword in keywords):
                        found_hwnd = hwnd
                        found_title = title
        
        win32gui.EnumWindows(enum_handler2, None)
        
        if found_hwnd:
            return (found_hwnd, found_title)
    
    return (None, None)


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

        for saved_name in self.selected_windows:
            try:
                # Try flexible matching first
                hwnd, actual_title = find_window_flexible(saved_name)
                
                if hwnd is None or hwnd == 0:
                    raise Exception("Window not found.")
                
                # Use the actual found title (might be different from saved_name)
                # Loading Addresses
                proc_id = win32process.GetWindowThreadProcessId(hwnd)
                proc_id = proc_id[1]
                process_handle = c.windll.kernel32.OpenProcess(0x1F0FFF, False, proc_id)
                modules = win32process.EnumProcessModules(process_handle)
                base_address = modules[0]

                # Store with actual title (so it works even if title changed)
                self.attached_processes.append((actual_title, hwnd, base_address))

                if actual_title != saved_name:
                    print(f"⚠️ Title changed: '{saved_name}' -> '{actual_title}'")
                print(f"{actual_title} -> HWND: {proc_id}, Base Address: {base_address}")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to attach to {saved_name}:\n{e}")

        if self.attached_processes:
            self.capture_window = CoordinateCaptureWindow(self.attached_processes)
            self.capture_window.show()
            self.capture_window.raise_()
            self.capture_window.activateWindow()
            self.hide()
        else:
            QMessageBox.warning(self, "No processes", "No processes were successfully attached.")
