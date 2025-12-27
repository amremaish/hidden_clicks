import threading
import time
import win32con
import win32gui
import win32api
import keyboard

running_flags = {}
threads = {}

def read_file_last_line(file_path):
    """Read the last line of a file"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            return lines[-1].strip() if lines else ""
    except FileNotFoundError:
        print(f"⚠️ File not found: {file_path}")
        return ""
    except PermissionError:
        print(f"⚠️ Permission denied: {file_path}")
        return ""
    except Exception as e:
        print(f"⚠️ Error reading file {file_path}: {e}")
        return ""


def execute_actions(actions, hwnd):
    """Execute a list of actions sequentially"""
    for action in actions:
        if not running_flags.get(hwnd, False):
            break
        
        if action["type"] == "left_click":
            send_left_click(hwnd, action["x"], action["y"])
        elif action["type"] == "double_click":
            send_double_click(hwnd, action["x"], action["y"])
        elif action["type"] == "delay":
            time.sleep(action["ms"] / 1000.0)
        elif action["type"] == "hotkey":
            send_hotkey(
                hwnd,
                action.get("key", ""),
                action.get("ctrl", False),
                action.get("alt", False),
                action.get("shift", False)
            )
        elif action["type"] == "end_file_reader":
            # Handle nested end_file_reader actions
            file_path = action.get("file_path", "")
            key_text = action.get("key_text", "")
            true_actions = action.get("true_actions", [])
            false_actions = action.get("false_actions", [])
            
            if file_path and key_text:
                last_line = read_file_last_line(file_path)
                if key_text in last_line:
                    execute_actions(true_actions, hwnd)
                else:
                    execute_actions(false_actions, hwnd)


def loop_for_process(name, hwnd, actions):
    running_flags[hwnd] = True
    print(f"🧵 Started thread for {name} ({hwnd})")
    max_iterations = 10000  # Prevent infinite loops
    iteration_count = 0
    
    while True:
        if not running_flags.get(hwnd, False):
            time.sleep(0.1)
            continue

        try:
            if not actions:
                time.sleep(1)
                continue
            
            # Use index-based loop to support conditional jumps
            action_index = 0
            cycle_count = 0
            max_cycles = 1000  # Max cycles per loop iteration to prevent infinite loops
            
            while action_index < len(actions) and cycle_count < max_cycles:
                if not running_flags.get(hwnd, False):
                    break
                
                action = actions[action_index]
                next_index = action_index + 1  # Default: move to next action
                
                if action["type"] == "left_click":
                    send_left_click(hwnd, action["x"], action["y"])
                elif action["type"] == "double_click":
                    send_double_click(hwnd, action["x"], action["y"])
                elif action["type"] == "delay":
                    time.sleep(action["ms"] / 1000.0)
                elif action["type"] == "hotkey":
                    send_hotkey(
                        hwnd,
                        action.get("key", ""),
                        action.get("ctrl", False),
                        action.get("alt", False),
                        action.get("shift", False)
                    )
                elif action["type"] == "end_file_reader":
                    # Read last line of file and check for key text
                    file_path = action.get("file_path", "")
                    key_text = action.get("key_text", "")
                    true_actions = action.get("true_actions", [])
                    false_actions = action.get("false_actions", [])
                    
                    if file_path and key_text:
                        last_line = read_file_last_line(file_path)
                        if key_text in last_line:
                            # Execute true actions
                            print(f"✓ Key text '{key_text}' found in {file_path}, executing {len(true_actions)} true actions")
                            execute_actions(true_actions, hwnd)
                        else:
                            # Execute false actions
                            print(f"✗ Key text '{key_text}' not found in {file_path}, executing {len(false_actions)} false actions")
                            execute_actions(false_actions, hwnd)
                    # Continue to next action after sub actions complete
                
                action_index = next_index
                cycle_count += 1
                
                # Safety check for infinite loops
                if cycle_count >= max_cycles:
                    print(f"⚠️ Maximum cycles reached in {name}, restarting action sequence")
                    break

        except Exception as e:
            print(f"❌ Error in {name}: {e}")

        iteration_count += 1
        if iteration_count >= max_iterations:
            print(f"⚠️ Maximum iterations reached for {name}, resetting counter")
            iteration_count = 0
        
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


def send_hotkey(hwnd, key, ctrl=False, alt=False, shift=False):
    """Send a hotkey combination to the specified window"""
    import time
    
    # Log the hotkey being sent
    modifiers = []
    if ctrl:
        modifiers.append("Ctrl")
    if alt:
        modifiers.append("Alt")
    if shift:
        modifiers.append("Shift")
    
    hotkey_str = ""
    if modifiers:
        hotkey_str = "+".join(modifiers) + "+" + key.upper()
        print(f"⌨️ Sending hotkey: {hotkey_str}")
    else:
        hotkey_str = key.upper()
        print(f"⌨️ Sending key: {hotkey_str}")
    
    # Map key names to virtual key codes
    key_map = {
        'f1': win32con.VK_F1, 'f2': win32con.VK_F2, 'f3': win32con.VK_F3, 'f4': win32con.VK_F4,
        'f5': win32con.VK_F5, 'f6': win32con.VK_F6, 'f7': win32con.VK_F7, 'f8': win32con.VK_F8,
        'f9': win32con.VK_F9, 'f10': win32con.VK_F10, 'f11': win32con.VK_F11, 'f12': win32con.VK_F12,
        'enter': win32con.VK_RETURN, 'return': win32con.VK_RETURN,
        'tab': win32con.VK_TAB, 'space': win32con.VK_SPACE,
        'backspace': win32con.VK_BACK, 'delete': win32con.VK_DELETE,
        'escape': win32con.VK_ESCAPE, 'esc': win32con.VK_ESCAPE,
        'up': win32con.VK_UP, 'down': win32con.VK_DOWN,
        'left': win32con.VK_LEFT, 'right': win32con.VK_RIGHT,
        'home': win32con.VK_HOME, 'end': win32con.VK_END,
        'page up': win32con.VK_PRIOR, 'page down': win32con.VK_NEXT,
        'pageup': win32con.VK_PRIOR, 'pagedown': win32con.VK_NEXT,
    }
    
    # Get virtual key code
    key_lower = key.lower()
    if key_lower in key_map:
        vk_code = key_map[key_lower]
    elif len(key) == 1:
        # Single character - get virtual key code
        vk_code = win32api.VkKeyScan(key)
        if vk_code == -1:
            # Try uppercase
            vk_code = win32api.VkKeyScan(key.upper())
        if vk_code != -1:
            vk_code = vk_code & 0xFF  # Get low byte
        else:
            print(f"⚠️ Could not find virtual key code for key: {key}")
            return
    else:
        print(f"⚠️ Unknown key: {key}")
        return
    
    # Send modifier keys down first using PostMessage with lParam=0
    if ctrl:
        print(f"  → Sending Ctrl DOWN (vk: {win32con.VK_CONTROL})")
        win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_CONTROL, 0)
        time.sleep(0.03)  # Delay to ensure modifier is registered
    
    if alt:
        print(f"  → Sending Alt DOWN (vk: {win32con.VK_MENU})")
        win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_MENU, 0)
        time.sleep(0.03)
    
    if shift:
        print(f"  → Sending Shift DOWN (vk: {win32con.VK_SHIFT})")
        win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_SHIFT, 0)
        time.sleep(0.03)
    
    # Send main key down - use SendMessage to ensure it's processed while modifier is down
    print(f"  → Sending {key.upper()} DOWN (vk: {vk_code})")
    win32gui.SendMessage(hwnd, win32con.WM_KEYDOWN, vk_code, 0)
    time.sleep(0.02)
    
    # Send main key up
    print(f"  → Sending {key.upper()} UP")
    win32gui.SendMessage(hwnd, win32con.WM_KEYUP, vk_code, 0)
    time.sleep(0.02)
    
    # Release modifier keys in reverse order using PostMessage with lParam=0
    if shift:
        print(f"  → Sending Shift UP")
        win32gui.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_SHIFT, 0)
        time.sleep(0.01)
    
    if alt:
        print(f"  → Sending Alt UP")
        win32gui.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_MENU, 0)
        time.sleep(0.01)
    
    if ctrl:
        print(f"  → Sending Ctrl UP")
        win32gui.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_CONTROL, 0)
    
    print(f"✓ Hotkey {hotkey_str} sent successfully")
