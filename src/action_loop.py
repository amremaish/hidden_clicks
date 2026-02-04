import threading
import time
import os
import glob
from datetime import datetime
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

# Try to configure Tesseract path early (optional, won't break if pytesseract not installed)
try:
    import pytesseract
    import platform
    
    if platform.system() == 'Windows':
        # Common Tesseract installation paths on Windows
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'.format(os.getenv('USERNAME', '')),
            r'C:\Tesseract-OCR\tesseract.exe',
        ]
        
        # Check current setting - if it's just 'tesseract' (default) or doesn't exist, try to set a real path
        current_cmd = getattr(pytesseract.pytesseract, 'tesseract_cmd', None)
        if not current_cmd or current_cmd == 'tesseract' or (current_cmd != 'tesseract' and not os.path.exists(current_cmd)):
            # Try to find and set Tesseract path
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
except ImportError:
    # pytesseract not installed, that's okay - will be handled in match_ocr_text
    pass
except Exception:
    # Any other error, ignore - will be handled in match_ocr_text
    pass

def save_image_matcher_screenshot(screenshot):
    """Save screenshot to logs folder, keeping only the last 5 screenshots (non-blocking)"""
    try:
        # Create logs folder if it doesn't exist
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # Generate filename with datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
        filename = f"image_matcher_{timestamp}.png"
        filepath = os.path.join(logs_dir, filename)
        
        # Convert BGR to RGB for saving (OpenCV uses BGR, PIL uses RGB)
        screenshot_rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(screenshot_rgb)
        img.save(filepath, "PNG", optimize=False, compress_level=1)  # Faster saving
        
        # Quick cleanup: only check if we need to delete (optimize file operations)
        # Get all image_matcher screenshots and sort by modification time (newest first)
        pattern = os.path.join(logs_dir, "image_matcher_*.png")
        existing_files = glob.glob(pattern)
        
        # Only do cleanup if we have more than 5 files (avoid unnecessary sorting)
        if len(existing_files) > 5:
            existing_files.sort(key=os.path.getmtime, reverse=True)
            # Keep only the 5 most recent files, delete the rest
            for old_file in existing_files[5:]:
                try:
                    os.remove(old_file)
                except:
                    pass  # Silently ignore deletion errors to avoid slowing down
        
        return filepath
    except Exception as e:
        # Silently fail to avoid slowing down the main process
        return None

def save_ocr_matcher_screenshot(screenshot):
    """Save OCR screenshot to logs folder, keeping only the last 5 screenshots (non-blocking)"""
    try:
        # Create logs folder if it doesn't exist
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # Generate filename with datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
        filename = f"ocr_image_{timestamp}.png"
        filepath = os.path.join(logs_dir, filename)
        
        # Convert BGR to RGB for saving (OpenCV uses BGR, PIL uses RGB)
        screenshot_rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(screenshot_rgb)
        img.save(filepath, "PNG", optimize=False, compress_level=1)  # Faster saving
        
        # Quick cleanup: only check if we need to delete (optimize file operations)
        # Get all ocr_image screenshots and sort by modification time (newest first)
        pattern = os.path.join(logs_dir, "ocr_image_*.png")
        existing_files = glob.glob(pattern)
        
        # Only do cleanup if we have more than 5 files (avoid unnecessary sorting)
        if len(existing_files) > 5:
            existing_files.sort(key=os.path.getmtime, reverse=True)
            # Keep only the 5 most recent files, delete the rest
            for old_file in existing_files[5:]:
                try:
                    os.remove(old_file)
                except:
                    pass  # Silently ignore deletion errors to avoid slowing down
        
        return filepath
    except Exception as e:
        # Silently fail to avoid slowing down the main process
        return None

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


def capture_window_screenshot(hwnd, crop_area=None):
    """Capture a screenshot of the specified window using PrintWindow (works even when minimized)
    
    Args:
        hwnd: Window handle
        crop_area: Optional tuple (x, y, width, height) to crop the screenshot. 
                   Coordinates are relative to the window client area.
    
    Returns:
        Screenshot as numpy array (BGR format), or None on failure
    """
    hwndDC = None
    mfcDC = None
    saveDC = None
    bitmap = None
    
    try:
        # Verify window handle is still valid (fast check, no logging)
        if not win32gui.IsWindow(hwnd):
            return None
        
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
        if not hwndDC:
            return None  # Fast fail, no logging to avoid slowdown
        
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
            return None  # Fast fail, no logging to avoid slowdown
        
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
        
        # Crop the screenshot if crop_area is specified
        if crop_area:
            crop_x, crop_y, crop_width, crop_height = crop_area
            # Ensure crop coordinates are within bounds
            h, w = screenshot_bgr.shape[:2]
            crop_x = max(0, min(crop_x, w - 1))
            crop_y = max(0, min(crop_y, h - 1))
            crop_width = min(crop_width, w - crop_x)
            crop_height = min(crop_height, h - crop_y)
            
            if crop_width > 0 and crop_height > 0:
                screenshot_bgr = screenshot_bgr[crop_y:crop_y+crop_height, crop_x:crop_x+crop_width]
        
        # Explicitly delete intermediate objects to free memory
        del img
        del screenshot_np
        del bmpstr
        
        return screenshot_bgr
    except Exception as e:
        print(f"⚠️ Error capturing screenshot: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # Always cleanup resources, even if an exception occurred
        try:
            if bitmap:
                try:
                    win32gui.DeleteObject(bitmap.GetHandle())
                except:
                    pass
            if saveDC:
                try:
                    saveDC.DeleteDC()
                except:
                    pass
            if mfcDC:
                try:
                    mfcDC.DeleteDC()
                except:
                    pass
            if hwndDC and hwnd:
                try:
                    win32gui.ReleaseDC(hwnd, hwndDC)
                except:
                    pass
        except:
            pass  # Ignore cleanup errors


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
    template = None
    try:
        # Validate screenshot
        if screenshot is None or screenshot.size == 0:
            print(f"⚠️ Invalid screenshot provided")
            return None
        
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
    finally:
        # Explicitly release template memory if it was loaded
        if template is not None:
            del template


def match_ocr_text(screenshot, search_text, case_sensitive=False, match_mode="contains"):
    """Perform OCR on screenshot and search for text
    
    Args:
        screenshot: OpenCV image (BGR format) or PIL Image
        search_text: Text to search for
        case_sensitive: Whether search should be case sensitive
        match_mode: Matching mode - "contains", "starts_with", or "ends_with"
    
    Returns:
        True if text is found, False otherwise
    """
    try:
        # Try to import pytesseract
        try:
            import pytesseract
        except ImportError as e:
            print(f"⚠️ pytesseract import failed: {e}")
            print("⚠️ This might mean:")
            print("   1. pytesseract is not installed in the current Python environment")
            print("   2. If running from PyInstaller build, rebuild with pytesseract in hiddenimports")
            print("⚠️ Install with: pip install pytesseract")
            print("⚠️ Also install Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki")
            return False
        except Exception as e:
            print(f"⚠️ Unexpected error importing pytesseract: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Set Tesseract path if not already set to a valid path (for Windows)
        import platform
        if platform.system() == 'Windows':
            current_cmd = getattr(pytesseract.pytesseract, 'tesseract_cmd', None)
            if not current_cmd or current_cmd == 'tesseract' or (current_cmd != 'tesseract' and not os.path.exists(current_cmd)):
                tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
                if os.path.exists(tesseract_path):
                    pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Check if Tesseract executable can be found
        try:
            # Try to get Tesseract version to verify it's accessible
            pytesseract.get_tesseract_version()
        except Exception as e:
            # Tesseract not found in PATH, try to set it manually for Windows
            # Note: os is already imported at the top of the file
            import platform
            if platform.system() == 'Windows':
                # Common Tesseract installation paths on Windows
                possible_paths = [
                    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                    r'C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'.format(os.getenv('USERNAME', '')),
                    r'C:\Tesseract-OCR\tesseract.exe',
                ]
                
                tesseract_found = False
                for path in possible_paths:
                    if os.path.exists(path):
                        pytesseract.pytesseract.tesseract_cmd = path
                        try:
                            pytesseract.get_tesseract_version()
                            print(f"✅ Found Tesseract at: {path}")
                            tesseract_found = True
                            break
                        except:
                            continue
                
                if not tesseract_found:
                    print("⚠️ Tesseract OCR executable not found!")
                    print("⚠️ Please ensure Tesseract OCR is installed and either:")
                    print("   1. Add Tesseract to your system PATH, OR")
                    print("   2. Install it to one of these locations:")
                    for path in possible_paths:
                        print(f"      - {path}")
                    print("⚠️ Download from: https://github.com/UB-Mannheim/tesseract/wiki")
                    return False
            else:
                print(f"⚠️ Tesseract OCR not found in PATH: {e}")
                print("⚠️ Please install Tesseract OCR and ensure it's in your system PATH")
                return False
        
        # Convert screenshot to PIL Image if it's OpenCV format
        if isinstance(screenshot, np.ndarray):
            # Check image dimensions
            h, w = screenshot.shape[:2]
            print(f"📏 OCR image size: {w}×{h} pixels")
            
            if w < 10 or h < 10:
                print(f"⚠️ Image too small for OCR: {w}×{h}")
                return False
            
            # Preprocess image for better OCR accuracy
            # Convert to grayscale
            if len(screenshot.shape) == 3:
                gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            else:
                gray = screenshot
            
            # Check if image is mostly black/empty
            mean_brightness = np.mean(gray)
            print(f"📊 Image brightness: {mean_brightness:.1f} (0=black, 255=white)")
            if mean_brightness < 10:
                print(f"⚠️ Image appears to be mostly black - might be empty or wrong crop area")
            
            # Increase contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # Apply adaptive thresholding to improve text contrast
            # This helps with text on dark backgrounds
            thresh = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Convert back to RGB for PIL
            screenshot_rgb = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)
            pil_image = Image.fromarray(screenshot_rgb)
            
            # Also create a thresholded version for OCR
            thresh_rgb = cv2.cvtColor(thresh, cv2.COLOR_GRAY2RGB)
            pil_image_thresh = Image.fromarray(thresh_rgb)
        else:
            pil_image = screenshot
            pil_image_thresh = None
        
        # Perform OCR - try multiple preprocessing methods and PSM modes
        extracted_text = ""
        try:
            # Try different PSM modes (Page Segmentation Modes)
            # PSM 6 = Assume a single uniform block of text
            # PSM 7 = Treat the image as a single text line
            # PSM 8 = Treat the image as a single word (good for buttons)
            # PSM 11 = Sparse text (find as much text as possible)
            
            # First try with enhanced image, PSM 8 (single word) - best for button text
            extracted_text = pytesseract.image_to_string(pil_image, config='--psm 8')
            
            # If no text, try PSM 6 (uniform block)
            if not extracted_text.strip():
                extracted_text = pytesseract.image_to_string(pil_image, config='--psm 6')
            
            # If still no text and we have thresholded version, try that
            if not extracted_text.strip() and pil_image_thresh is not None:
                extracted_text = pytesseract.image_to_string(pil_image_thresh, config='--psm 8')
                if not extracted_text.strip():
                    extracted_text = pytesseract.image_to_string(pil_image_thresh, config='--psm 6')
            
            # Last resort: try PSM 11 (sparse text) - finds any text anywhere
            if not extracted_text.strip():
                extracted_text = pytesseract.image_to_string(pil_image, config='--psm 11')
                if not extracted_text.strip() and pil_image_thresh is not None:
                    extracted_text = pytesseract.image_to_string(pil_image_thresh, config='--psm 11')
        except Exception as e:
            error_msg = str(e)
            if "tesseract" in error_msg.lower() or "not found" in error_msg.lower():
                print(f"⚠️ Error: Tesseract OCR executable not found: {e}")
                print("⚠️ Please ensure Tesseract OCR is installed and in your PATH")
            else:
                print(f"⚠️ Error performing OCR: {e}")
            return False
        
        # Check if we got any text at all
        if not extracted_text or not extracted_text.strip():
            print(f"⚠️ OCR returned empty text - image might be too small, low contrast, or contain no readable text")
            if isinstance(screenshot, np.ndarray):
                print(f"📏 Screenshot dimensions: {screenshot.shape}")
            return False
        
        # Clean extracted text (remove extra whitespace, newlines)
        extracted_text_clean = ' '.join(extracted_text.split())
        
        # Also create a version with all non-alphanumeric characters removed for more flexible matching
        import re
        extracted_text_alphanumeric = re.sub(r'[^a-zA-Z0-9\s]', '', extracted_text)
        extracted_text_alphanumeric = ' '.join(extracted_text_alphanumeric.split())
        
        # Search for text based on match mode
        if case_sensitive:
            search_text_processed = search_text
            extracted_text_processed = extracted_text
            extracted_text_alphanumeric_processed = extracted_text_alphanumeric
        else:
            search_text_processed = search_text.lower()
            extracted_text_processed = extracted_text.lower()
            extracted_text_alphanumeric_processed = extracted_text_alphanumeric.lower()
        
        # Apply match mode - try both normal and alphanumeric-only versions
        match_mode_lower = match_mode.lower().replace(" ", "_")
        found = False
        
        if match_mode_lower == "starts_with":
            found = (extracted_text_processed.startswith(search_text_processed) or 
                    extracted_text_alphanumeric_processed.startswith(search_text_processed))
        elif match_mode_lower == "ends_with":
            found = (extracted_text_processed.endswith(search_text_processed) or 
                    extracted_text_alphanumeric_processed.endswith(search_text_processed))
        else:  # "contains" (default)
            found = (search_text_processed in extracted_text_processed or 
                    search_text_processed in extracted_text_alphanumeric_processed)
        
        match_mode_display = match_mode.replace("_", " ").title()
        if found:
            print(f"📝 OCR text found: \"{search_text}\" (mode: {match_mode_display})")
            # Print the extracted text (truncate if too long)
            if len(extracted_text_clean) > 200:
                print(f"📄 Extracted text (first 200 chars): {extracted_text_clean[:200]}...")
            else:
                print(f"📄 Extracted text: {extracted_text_clean}")
        else:
            print(f"📝 OCR text not found: \"{search_text}\" (mode: {match_mode_display})")
            # Show both raw and cleaned extracted text for debugging
            print(f"📄 Raw extracted text: {repr(extracted_text[:100])}")  # Show raw with repr to see hidden chars
            if len(extracted_text_clean) > 100:
                print(f"📄 Cleaned text (first 100 chars): {extracted_text_clean[:100]}...")
            else:
                print(f"📄 Cleaned text: {extracted_text_clean}")
            print(f"📄 Alphanumeric-only text: {extracted_text_alphanumeric[:100] if len(extracted_text_alphanumeric) > 100 else extracted_text_alphanumeric}")
        
        return found
        
    except Exception as e:
        print(f"⚠️ Error in OCR matching: {e}")
        import traceback
        traceback.print_exc()
        return False


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
                # Verify window is still valid before capturing
                if not win32gui.IsWindow(hwnd):
                    print(f"⚠️ Window handle {hwnd} is no longer valid")
                    return
                
                # Get crop area if specified (only if not using full screen)
                crop_area = None
                use_full_screen = action.get("use_full_screen", False)
                if not use_full_screen and "crop_x" in action and "crop_y" in action and "crop_width" in action and "crop_height" in action:
                    # Crop coordinates are stored as screen coordinates, need to convert to client coordinates
                    try:
                        screen_x = action["crop_x"]
                        screen_y = action["crop_y"]
                        crop_width = action["crop_width"]
                        crop_height = action["crop_height"]
                        
                        # Convert screen coordinates to client coordinates
                        # Use ScreenToClient to convert the top-left corner directly
                        client_top_left = win32gui.ScreenToClient(hwnd, (screen_x, screen_y))
                        client_x = client_top_left[0]
                        client_y = client_top_left[1]
                        
                        # Get client rect for bounds checking
                        client_rect = win32gui.GetClientRect(hwnd)
                        
                        # Ensure coordinates are within client bounds
                        client_x = max(0, min(client_x, client_rect[2] - 1))
                        client_y = max(0, min(client_y, client_rect[3] - 1))
                        crop_width = min(crop_width, client_rect[2] - client_x)
                        crop_height = min(crop_height, client_rect[3] - client_y)
                        
                        if crop_width > 0 and crop_height > 0:
                            crop_area = (client_x, client_y, crop_width, crop_height)
                    except Exception as e:
                        print(f"⚠️ Error converting crop coordinates: {e}")
                        # Fall back to using coordinates as-is (assume they're already client coordinates)
                        crop_area = (
                            action["crop_x"],
                            action["crop_y"],
                            action["crop_width"],
                            action["crop_height"]
                        )
                
                # Capture screenshot of the window
                screenshot = capture_window_screenshot(hwnd, crop_area)
                if screenshot is not None:
                    try:
                        # Save screenshot to logs folder
                        save_image_matcher_screenshot(screenshot)
                        
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
                    finally:
                        # Explicitly release screenshot memory
                        if screenshot is not None:
                            del screenshot
                else:
                    # Screenshot failed - execute false actions
                    print(f"⚠️ Screenshot capture failed, executing false actions")
                    execute_actions(false_actions, hwnd)
        elif action["type"] == "ocr_matcher":
            # Handle OCR matcher conditional actions
            search_text = action.get("text", "")
            match_mode = action.get("match_mode", "contains")
            case_sensitive = action.get("case_sensitive", False)
            true_actions = action.get("true_actions", [])
            false_actions = action.get("false_actions", [])
            
            if search_text:
                # Verify window is still valid before capturing
                if not win32gui.IsWindow(hwnd):
                    print(f"⚠️ Window handle {hwnd} is no longer valid")
                    return
                
                # Get crop area if specified (only if not using full screen)
                crop_area = None
                use_full_screen = action.get("use_full_screen", False)
                if not use_full_screen and "crop_x" in action and "crop_y" in action and "crop_width" in action and "crop_height" in action:
                    # Crop coordinates are stored as screen coordinates, need to convert to client coordinates
                    try:
                        screen_x = action["crop_x"]
                        screen_y = action["crop_y"]
                        crop_width = action["crop_width"]
                        crop_height = action["crop_height"]
                        
                        # Convert screen coordinates to client coordinates
                        # Use ScreenToClient to convert the top-left corner
                        client_top_left = win32gui.ScreenToClient(hwnd, (screen_x, screen_y))
                        client_x = client_top_left[0]
                        client_y = client_top_left[1]
                        
                        # Get client rect for bounds checking
                        client_rect = win32gui.GetClientRect(hwnd)
                        
                        # Ensure coordinates are within client bounds
                        client_x = max(0, min(client_x, client_rect[2] - 1))
                        client_y = max(0, min(client_y, client_rect[3] - 1))
                        crop_width = min(crop_width, client_rect[2] - client_x)
                        crop_height = min(crop_height, client_rect[3] - client_y)
                        
                        if crop_width > 0 and crop_height > 0:
                            crop_area = (client_x, client_y, crop_width, crop_height)
                    except Exception as e:
                        print(f"⚠️ Error converting crop coordinates: {e}")
                        # Fall back to using coordinates as-is
                        crop_area = (
                            action["crop_x"],
                            action["crop_y"],
                            action["crop_width"],
                            action["crop_height"]
                        )
                
                # Capture screenshot of the window
                screenshot = capture_window_screenshot(hwnd, crop_area)
                if screenshot is not None:
                    try:
                        # Save screenshot to logs folder
                        save_ocr_matcher_screenshot(screenshot)
                        
                        # Perform OCR and search for text
                        text_found = match_ocr_text(screenshot, search_text, case_sensitive, match_mode)
                        if text_found:
                            # Text found - execute true actions
                            execute_actions(true_actions, hwnd)
                        else:
                            # Text not found - execute false actions
                            execute_actions(false_actions, hwnd)
                    finally:
                        # Explicitly release screenshot memory
                        if screenshot is not None:
                            del screenshot
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
                        # Get crop area if specified (only if not using full screen)
                        crop_area = None
                        use_full_screen = action.get("use_full_screen", False)
                        if not use_full_screen and "crop_x" in action and "crop_y" in action and "crop_width" in action and "crop_height" in action:
                            # Crop coordinates are stored as screen coordinates, need to convert to client coordinates
                            try:
                                screen_x = action["crop_x"]
                                screen_y = action["crop_y"]
                                crop_width = action["crop_width"]
                                crop_height = action["crop_height"]
                                
                                # Convert screen coordinates to client coordinates
                                # Use ScreenToClient to convert the top-left corner directly
                                client_top_left = win32gui.ScreenToClient(hwnd, (screen_x, screen_y))
                                client_x = client_top_left[0]
                                client_y = client_top_left[1]
                                
                                # Get client rect for bounds checking
                                client_rect = win32gui.GetClientRect(hwnd)
                                
                                # Ensure coordinates are within client bounds
                                client_x = max(0, min(client_x, client_rect[2] - 1))
                                client_y = max(0, min(client_y, client_rect[3] - 1))
                                crop_width = min(crop_width, client_rect[2] - client_x)
                                crop_height = min(crop_height, client_rect[3] - client_y)
                                
                                if crop_width > 0 and crop_height > 0:
                                    crop_area = (client_x, client_y, crop_width, crop_height)
                            except Exception as e:
                                print(f"⚠️ Error converting crop coordinates: {e}")
                                # Fall back to using coordinates as-is (assume they're already client coordinates)
                                crop_area = (
                                    action["crop_x"],
                                    action["crop_y"],
                                    action["crop_width"],
                                    action["crop_height"]
                                )
                        
                        # Capture screenshot of the window
                        screenshot = capture_window_screenshot(hwnd, crop_area)
                        if screenshot is not None:
                            # Save screenshot to logs folder
                            save_image_matcher_screenshot(screenshot)
                            
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
                elif action["type"] == "ocr_matcher":
                    # Handle OCR matcher conditional actions
                    search_text = action.get("text", "")
                    match_mode = action.get("match_mode", "contains")
                    case_sensitive = action.get("case_sensitive", False)
                    true_actions = action.get("true_actions", [])
                    false_actions = action.get("false_actions", [])
                    
                    if search_text:
                        # Get crop area if specified (only if not using full screen)
                        crop_area = None
                        use_full_screen = action.get("use_full_screen", False)
                        if not use_full_screen and "crop_x" in action and "crop_y" in action and "crop_width" in action and "crop_height" in action:
                            # Crop coordinates are stored as screen coordinates, need to convert to client coordinates
                            try:
                                screen_x = action["crop_x"]
                                screen_y = action["crop_y"]
                                crop_width = action["crop_width"]
                                crop_height = action["crop_height"]
                                
                                # Convert screen coordinates to client coordinates
                                # Use ScreenToClient to convert the top-left corner directly
                                client_top_left = win32gui.ScreenToClient(hwnd, (screen_x, screen_y))
                                client_x = client_top_left[0]
                                client_y = client_top_left[1]
                                
                                # Get client rect for bounds checking
                                client_rect = win32gui.GetClientRect(hwnd)
                                
                                # Ensure coordinates are within client bounds
                                client_x = max(0, min(client_x, client_rect[2] - 1))
                                client_y = max(0, min(client_y, client_rect[3] - 1))
                                crop_width = min(crop_width, client_rect[2] - client_x)
                                crop_height = min(crop_height, client_rect[3] - client_y)
                                
                                if crop_width > 0 and crop_height > 0:
                                    crop_area = (client_x, client_y, crop_width, crop_height)
                            except Exception as e:
                                print(f"⚠️ Error converting crop coordinates: {e}")
                                crop_area = (
                                    action["crop_x"],
                                    action["crop_y"],
                                    action["crop_width"],
                                    action["crop_height"]
                                )
                        
                        # Capture screenshot of the window
                        screenshot = capture_window_screenshot(hwnd, crop_area)
                        if screenshot is not None:
                            try:
                                # Save screenshot to logs folder
                                save_ocr_matcher_screenshot(screenshot)
                                
                                # Perform OCR and search for text
                                text_found = match_ocr_text(screenshot, search_text, case_sensitive, match_mode)
                                if text_found:
                                    # Text found - execute true actions
                                    print(f"✓ OCR text '{search_text}' found, executing {len(true_actions)} true actions")
                                    execute_actions(true_actions, hwnd)
                                else:
                                    # Text not found - execute false actions
                                    print(f"✗ OCR text '{search_text}' not found, executing {len(false_actions)} false actions")
                                    execute_actions(false_actions, hwnd)
                            finally:
                                # Explicitly release screenshot memory
                                if screenshot is not None:
                                    del screenshot
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
