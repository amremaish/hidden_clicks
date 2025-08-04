
# Hidden Clicks

**Hidden Clicks** is a Python-based automation tool designed to simulate and manage mouse-based interactions on screen. It uses screen coordinates and visual elements to control workflows, potentially for automation or game botting purposes.

## 🧠 Features

- ⌛ Background action loop executor
- 🎯 Screen capture and coordinate detection
- 🧩 Modular structure with `capture`, `action_loop`, and `selector`
- 🐍 Packaged with `PyInstaller` (`main.spec` included)

## 🗂 Project Structure

```
hidden_clicks/
├── coords.json                # Predefined coordinates or target positions
├── requirements.txt           # Python dependencies
├── src/
│   ├── main.py                # Main entry point
│   ├── action_loop.py         # Loop execution logic
│   ├── capture.py             # Screenshot and coordinate reading
│   ├── selector.py            # Decision/selector logic
│   └── main.spec              # PyInstaller spec file
```

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/hidden_clicks.git
cd hidden_clicks
```

### 2. Create a Virtual Environment (Optional but Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install PyInstaller (if not already installed)

```bash
pip install pyinstaller
```

### 6. Run the App

```bash
python src/main.py
```

## 📦 Build Executable

To package the app into an executable using PyInstaller:

```bash
pyinstaller src/main.spec
```

## ⚠️ Disclaimer

This tool is intended for educational and productivity use. Ensure you comply with the terms of service of any software or game you automate.

## 📄 License

MIT License
