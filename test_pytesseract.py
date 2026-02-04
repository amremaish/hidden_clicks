"""Test script to verify pytesseract and Tesseract OCR installation"""

print("Testing pytesseract installation...")
print("=" * 50)

# Test 1: Import pytesseract
try:
    import pytesseract
    print("✅ pytesseract imported successfully")
except ImportError as e:
    print(f"❌ Failed to import pytesseract: {e}")
    print("\nPlease install with: pip install pytesseract")
    exit(1)

# Test 2: Find Tesseract executable
import os
import platform

print(f"\nPlatform: {platform.system()}")

if platform.system() == 'Windows':
    # Common paths
    possible_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        r'C:\Tesseract-OCR\tesseract.exe',
    ]
    
    # Check current setting
    current_cmd = getattr(pytesseract.pytesseract, 'tesseract_cmd', None)
    if current_cmd:
        print(f"Current tesseract_cmd: {current_cmd}")
        if os.path.exists(current_cmd):
            print("✅ Current path exists")
        else:
            print("❌ Current path does not exist")
    else:
        print("No tesseract_cmd set (will use PATH)")
    
    # Check common paths
    print("\nChecking common installation paths:")
    found = False
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ Found: {path}")
            found = True
            # Try to set it
            try:
                pytesseract.pytesseract.tesseract_cmd = path
                print(f"   Set as tesseract_cmd")
            except:
                pass
        else:
            print(f"❌ Not found: {path}")
    
    if not found:
        print("\n⚠️ Tesseract not found in common locations")
        print("Please ensure Tesseract OCR is installed at:")
        print("  C:\\Program Files\\Tesseract-OCR\\")

# Test 3: Get Tesseract version
print("\n" + "=" * 50)
print("Testing Tesseract executable access...")
try:
    version = pytesseract.get_tesseract_version()
    print(f"✅ Tesseract version: {version}")
except Exception as e:
    print(f"❌ Failed to get Tesseract version: {e}")
    print("\nThis usually means:")
    print("  1. Tesseract OCR is not installed")
    print("  2. Tesseract is not in your PATH")
    print("  3. The tesseract_cmd path is incorrect")
    print("\nSolution:")
    print("  - Install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki")
    print("  - Or set the path manually:")
    print("    pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'")
    exit(1)

print("\n" + "=" * 50)
print("✅ All tests passed! pytesseract is ready to use.")

