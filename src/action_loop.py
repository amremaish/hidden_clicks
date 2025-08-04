import threading
import time
import win32con
import win32gui
import win32api
import keyboard

running_flags = {}
threads = {}

def loop_for_process(name, hwnd, actions):
    running_flags[hwnd] = True
    print(f"🧵 Started thread for {name} ({hwnd})")
    while True:
        if not running_flags.get(hwnd, False):
            time.sleep(0.1)
            continue

        try:
            for action in actions:
                if not running_flags.get(hwnd, False):
                    break

                if action["type"] == "left_click":
                    send_left_click(hwnd, action["x"], action["y"])
                elif action["type"] == "double_click":
                    send_double_click(hwnd, action["x"], action["y"])
                elif action["type"] == "delay":
                    time.sleep(action["ms"] / 1000.0)

        except Exception as e:
            print(f"❌ Error in {name}: {e}")

        time.sleep(1)  # short pause between action loop cycles


def start_threads_for_all(attached_processes, actions):
    for name, hwnd, base_address in attached_processes:
        if running_flags.get(hwnd):
            continue

        t = threading.Thread(
            target=loop_for_process,
            args=(name, hwnd, actions),
            daemon=True
        )
        threads[hwnd] = t
        t.start()

    if not keyboard.is_pressed('f7') and not keyboard.is_pressed('f8'):
        threading.Thread(target=_listen_for_keys, daemon=True).start()


def stop_all_threads():
    for hwnd in running_flags:
        running_flags[hwnd] = False


def continue_all_threads():
    for hwnd in running_flags:
        running_flags[hwnd] = True


def _listen_for_keys():
    while True:
        if keyboard.is_pressed("f7"):
            stop_all_threads()
            while keyboard.is_pressed("f7"):
                time.sleep(0.1)
        elif keyboard.is_pressed("f8"):
            continue_all_threads()
            while keyboard.is_pressed("f8"):
                time.sleep(0.1)
        time.sleep(0.1)



def send_left_click(hwnd, x, y):
    x, y = win32gui.ScreenToClient(hwnd, (x, y))
    lParam = win32api.MAKELONG(x, y)
    win32gui.PostMessage(hwnd, win32con.WM_MOUSEMOVE, 0, lParam)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)


def send_double_click(hwnd, x, y):
    x, y = win32gui.ScreenToClient(hwnd, (x, y))
    lParam = win32api.MAKELONG(x, y)

    win32gui.PostMessage(hwnd, win32con.WM_MOUSEMOVE, 0, lParam)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDBLCLK, win32con.MK_LBUTTON, lParam)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)
