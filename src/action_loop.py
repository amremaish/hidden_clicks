import threading
import time
import win32con
import win32gui
import win32api
import win32ui
import keyboard
import cv2
import numpy as np
from PIL import Image
import ctypes
from ctypes import wintypes

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


def capture_window_screenshot(hwnd):
    """Capture a screenshot of the specified window using PrintWindow (works even when minimized)"""
    try:
        # Get client rectangle (content area of the window)
        left, top, right, bottom = win32gui.GetClientRect(hwnd)
        width = right - left
        height = bottom - top
        
        # If client rect is zero (window is minimized), get the restore size
        if width == 0 or height == 0:
            try:
                # Get window placement to find restore size
                placement = win32gui.GetWindowPlacement(hwnd)
                if placement and len(placement) > 2:
                    # placement[2] is rcNormalPosition (restore rectangle)
                    restore_rect = placement[2]
                    if restore_rect:
                        # restore_rect is (left, top, right, bottom)
                        width = restore_rect[2] - restore_rect[0]
                        height = restore_rect[3] - restore_rect[1]
                        # Adjust for window borders (approximate)
                        # We'll use the restore size but need to account for borders
                        # For now, use the restore size directly
                        if width > 0 and height > 0:
                            print(f"ℹ️ Window is minimized, using restore size: {width}x{height}")
                        else:
                            # Try GetWindowRect as fallback
                            try:
                                left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                                width = right - left
                                height = bottom - top
                            except:
                                pass
                
                # If still zero, try GetWindowRect
                if width == 0 or height == 0:
                    try:
                        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                        width = right - left
                        height = bottom - top
                    except:
                        pass
                
                # If still zero, we can't proceed
                if width == 0 or height == 0:
                    print(f"⚠️ Cannot determine window size (minimized or zero size)")
                    return None
            except Exception as e:
                print(f"⚠️ Error getting window size: {e}")
                return None
        
        # Get device context
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        
        # Create bitmap
        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(bitmap)
        
        # PrintWindow with PW_RENDERFULLCONTENT = 2 (Windows 8+)
        # This works even when the window is minimized
        # Call PrintWindow through ctypes since it's not directly available in win32gui
        user32 = ctypes.windll.user32
        PW_RENDERFULLCONTENT = 2
        result = user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), PW_RENDERFULLCONTENT)
        
        if not result:
            print(f"⚠️ PrintWindow failed for window {hwnd}")
            # Cleanup
            win32gui.DeleteObject(bitmap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwndDC)
            return None
        
        # Get bitmap data
        bmpinfo = bitmap.GetInfo()
        bmpstr = bitmap.GetBitmapBits(True)
        
        # Convert to PIL Image
        img = Image.frombuffer(
            "RGB",
            (bmpinfo["bmWidth"], bmpinfo["bmHeight"]),
            bmpstr,
            "raw",
            "BGRX",
            0,
            1
        )
        
        # Convert PIL Image to numpy array for OpenCV
        screenshot_np = np.array(img)
        # Convert RGB to BGR for OpenCV
        screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
        
        # Cleanup
        win32gui.DeleteObject(bitmap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)
        
        return screenshot_bgr
    except Exception as e:
        print(f"⚠️ Error capturing screenshot: {e}")
        return None


def match_template_image(screenshot, template_path, match_number=1, threshold=0.99):
    """Match a template image in the screenshot and return the nth match location
    
    Args:
        screenshot: Screenshot image as numpy array (BGR format)
        template_path: Path to the template image file
        match_number: Which match to return (1 = first, 2 = second, etc.)
        threshold: Matching threshold (0.0 to 1.0)
    
    Returns:
        Tuple (x, y) of the match location, or None if not found
    """
    try:
        # Load template image
        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        if template is None:
            print(f"⚠️ Could not load template image: {template_path}")
            return None
        
        # Check if screenshot is smaller than template (can't match)
        if screenshot.shape[0] < template.shape[0] or screenshot.shape[1] < template.shape[1]:
            print(f"⚠️ Screenshot ({screenshot.shape[1]}x{screenshot.shape[0]}) is smaller than template ({template.shape[1]}x{template.shape[0]})")
            return None
        
        template_h, template_w = template.shape[:2]
        
        # For high thresholds (>= 0.99), use color matching for pixel-perfect matching
        # For lower thresholds, use grayscale for more flexible matching
        use_color_matching = threshold >= 0.99
        
        if use_color_matching:
            # Use color matching for strict, pixel-perfect matching
            # Split into BGR channels and match each channel separately
            # Then combine results - all channels must match well
            
            # Method 1: Multi-channel template matching
            # Match each color channel separately
            result_b = cv2.matchTemplate(screenshot[:,:,0], template[:,:,0], cv2.TM_CCOEFF_NORMED)
            result_g = cv2.matchTemplate(screenshot[:,:,1], template[:,:,1], cv2.TM_CCOEFF_NORMED)
            result_r = cv2.matchTemplate(screenshot[:,:,2], template[:,:,2], cv2.TM_CCOEFF_NORMED)
            
            # Combine results: all channels must exceed threshold
            # Use minimum of all three channels (all must match well)
            result_combined = np.minimum(np.minimum(result_b, result_g), result_r)
            
            # For very strict matching (100%), also verify pixel-by-pixel
            if threshold >= 0.999:
                # Find candidates first
                candidate_locations = np.where(result_combined >= (threshold - 0.01))  # Slightly lower for candidates
                candidates = []
                for pt in zip(*candidate_locations[::-1]):
                    x, y = pt[0], pt[1]
                    # Extract the region from screenshot
                    region = screenshot[y:y+template_h, x:x+template_w]
                    if region.shape == template.shape:
                        # Calculate pixel-perfect match percentage
                        diff = np.abs(region.astype(np.int16) - template.astype(np.int16))
                        # Calculate mean absolute difference per channel
                        mean_diff = np.mean(diff, axis=(0, 1))
                        # Convert to similarity (0-1 scale, where 1 = perfect match)
                        # For 8-bit images, max difference is 255 per channel
                        similarity = 1.0 - (np.mean(mean_diff) / 255.0)
                        
                        if similarity >= threshold:
                            # Also check that no single pixel is too different
                            max_pixel_diff = np.max(diff)
                            if max_pixel_diff <= 10:  # Allow small differences for anti-aliasing
                                candidates.append((x, y, similarity))
                
                # Sort by similarity
                candidates.sort(key=lambda x: x[2], reverse=True)
                matches = candidates
            else:
                # For 99% threshold, use combined channel matching
                locations = np.where(result_combined >= threshold)
                matches = []
                for pt in zip(*locations[::-1]):
                    confidence = result_combined[pt[1], pt[0]]
                    matches.append((pt[0], pt[1], confidence))
                matches.sort(key=lambda x: x[2], reverse=True)
        else:
            # Use grayscale matching for lower thresholds (more flexible)
            screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            
            # Perform template matching
            result = cv2.matchTemplate(screenshot_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            
            # Find all locations where the result exceeds the threshold
            locations = np.where(result >= threshold)
            
            # Get all matches with their confidence scores
            matches = []
            for pt in zip(*locations[::-1]):  # Switch x and y coordinates
                confidence = result[pt[1], pt[0]]
                matches.append((pt[0], pt[1], confidence))
            
            # Sort by confidence (highest first)
            matches.sort(key=lambda x: x[2], reverse=True)
        
        # Remove overlapping matches (non-maximum suppression)
        filtered_matches = []
        # Use template size to determine overlap distance (matches within template size are overlapping)
        overlap_distance_x = max(template_w // 2, 10)  # At least 10 pixels
        overlap_distance_y = max(template_h // 2, 10)  # At least 10 pixels
        
        for match in matches:
            x, y, conf = match
            # Check if this match overlaps with any existing match
            overlap = False
            for existing_x, existing_y, _ in filtered_matches:
                # If matches are within the overlap distance, consider them overlapping
                if abs(x - existing_x) < overlap_distance_x and abs(y - existing_y) < overlap_distance_y:
                    overlap = True
                    break
            if not overlap:
                # Verify the match is within bounds
                if (x >= 0 and y >= 0 and 
                    x + template_w <= screenshot.shape[1] and 
                    y + template_h <= screenshot.shape[0]):
                    filtered_matches.append((x, y, conf))
        
        # Return the nth match (1-indexed)
        if len(filtered_matches) >= match_number:
            x, y, confidence = filtered_matches[match_number - 1]
            match_type = "color" if use_color_matching else "grayscale"
            print(f"🖼️ Image match #{match_number} found at ({x}, {y}) with confidence {confidence:.4f} ({match_type} matching)")
            return (x, y)
        else:
            print(f"🖼️ Image match #{match_number} not found (found {len(filtered_matches)} matches)")
            return None
            
    except Exception as e:
        print(f"⚠️ Error matching template image: {e}")
        import traceback
        traceback.print_exc()
        return None


def execute_actions(actions, hwnd):
    """Execute a list of actions sequentially"""
    for action in actions:
        if not running_flags.get(hwnd, False):
            break
        
        # Skip disabled actions
        if not action.get("enabled", True):
            continue
        
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
        elif action["type"] == "image_matcher":
            # Handle image matcher conditional actions
            image_path = action.get("image_path", "")
            match_number = action.get("match_number", 1)
            true_actions = action.get("true_actions", [])
            false_actions = action.get("false_actions", [])
            
            if image_path:
                # Capture screenshot of the window
                screenshot = capture_window_screenshot(hwnd)
                if screenshot is not None:
                    # Get threshold (0-100, convert to 0.0-1.0)
                    threshold = action.get("threshold", 99)
                    if isinstance(threshold, int):
                        threshold = threshold / 100.0  # Convert 0-100 to 0.0-1.0
                    # Try to match the template
                    match_location = match_template_image(screenshot, image_path, match_number, threshold)
                    if match_location is not None:
                        # Image matched - execute true actions
                        execute_actions(true_actions, hwnd)
                    else:
                        # Image did not match - execute false actions
                        execute_actions(false_actions, hwnd)
                else:
                    # Screenshot failed - execute false actions
                    print(f"⚠️ Screenshot capture failed, executing false actions")
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
                
                # Skip disabled actions
                if not action.get("enabled", True):
                    action_index = next_index
                    cycle_count += 1
                    continue
                
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
                elif action["type"] == "image_matcher":
                    # Capture screenshot and match template image
                    image_path = action.get("image_path", "")
                    match_number = action.get("match_number", 1)
                    true_actions = action.get("true_actions", [])
                    false_actions = action.get("false_actions", [])
                    
                    if image_path:
                        # Capture screenshot of the window
                        screenshot = capture_window_screenshot(hwnd)
                        if screenshot is not None:
                            # Get threshold (0-100, convert to 0.0-1.0)
                            threshold = action.get("threshold", 99)
                            if isinstance(threshold, int):
                                threshold = threshold / 100.0  # Convert 0-100 to 0.0-1.0
                            # Try to match the template
                            match_location = match_template_image(screenshot, image_path, match_number, threshold)
                            if match_location is not None:
                                # Image matched - execute true actions
                                print(f"✓ Image match #{match_number} found in {image_path}, executing {len(true_actions)} true actions")
                                execute_actions(true_actions, hwnd)
                            else:
                                # Image did not match - execute false actions
                                print(f"✗ Image match #{match_number} not found in {image_path}, executing {len(false_actions)} false actions")
                                execute_actions(false_actions, hwnd)
                        else:
                            # Screenshot failed - execute false actions
                            print(f"⚠️ Screenshot capture failed, executing {len(false_actions)} false actions")
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
