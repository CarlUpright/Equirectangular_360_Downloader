# 📥 Installation Guide - Panorama Downloader

## For Complete Beginners (No Python Installed)

### Step 1: Install Python
1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download **Python 3.11** or newer
3. **IMPORTANT:** During installation, check the box **"Add Python to PATH"**
4. Click **"Install Now"**

### Step 2: Install Required Libraries
Open **Command Prompt** (Windows) or **Terminal** (Mac/Linux) and type:

```bash
pip install requests pillow
```

Press Enter and wait for installation to complete.

### Step 3: Download the Script
1. Go to [github.com/CarlUpright/Equirectangular_360_Downloader](https://github.com/CarlUpright/Equirectangular_360_Downloader)
2. Click on `panorama_downloader_gui.py`
3. Click the **"Raw"** button (top right)
4. Right-click → **"Save As"** → Save to your desired location

**OR** use git:
```bash
git clone https://github.com/CarlUpright/Equirectangular_360_Downloader.git
cd Equirectangular_360_Downloader
```

### Step 4: Run the Script

**Option A - Double-click:**
- Simply double-click `panorama_downloader_gui.py`

**Option B - Command line:**
```bash
python panorama_downloader_gui.py
```

Or on some systems:
```bash
python3 panorama_downloader_gui.py
```

---

## Quick Install (For Users with Python Already Installed)

```bash
# Clone repository
git clone https://github.com/CarlUpright/Equirectangular_360_Downloader.git
cd Equirectangular_360_Downloader

# Install dependencies
pip install requests pillow

# Run
python panorama_downloader_gui.py
```

---

## Requirements

- Python 3.11 or newer
- `requests` library (for downloading images)
- `pillow` library (for image processing)
- `tkinter` (usually included with Python)

---

## Troubleshooting

### "Python not found" or "'python' is not recognized"
- **Solution:** Reinstall Python and make sure to check **"Add Python to PATH"** during installation
- **Alternative:** Use the full path to python.exe, e.g., `C:\Users\YourName\AppData\Local\Programs\Python\Python311\python.exe panorama_downloader_gui.py`

### "No module named 'requests'" or "No module named 'PIL'"
- **Solution:** Run `pip install requests pillow` in Command Prompt/Terminal
- If `pip` is not found, try: `python -m pip install requests pillow`

### Script won't open when double-clicking
- **Solution:** Right-click the file → "Open with" → Choose Python
- **Alternative:** Run from command line using `python panorama_downloader_gui.py`

### "tkinter not found"
- **Windows/Mac:** tkinter should be included with Python
- **Linux:** Install with `sudo apt-get install python3-tk` (Ubuntu/Debian) or equivalent for your distribution

### Permission errors when saving files
- **Solution:** Make sure you have write permissions to the output directory
- Try running as administrator (Windows) or with `sudo` (Mac/Linux) if necessary

---

## Platform-Specific Notes

### Windows
- Use **Command Prompt** or **PowerShell**
- Python is usually installed in `C:\Users\YourName\AppData\Local\Programs\Python\`

### macOS
- Use **Terminal**
- You may need to use `python3` instead of `python`
- If pip doesn't work, try `pip3`

### Linux
- Use **Terminal**
- You may need to install tkinter separately: `sudo apt-get install python3-tk`
- Use `python3` and `pip3` commands

---

## Updating the Script

To get the latest version:

```bash
cd Equirectangular_360_Downloader
git pull origin main
```

Or simply download the new `panorama_downloader_gui.py` file from GitHub and replace your old one.

---

## Support

If you encounter issues not covered here, please open an issue on the [GitHub repository](https://github.com/CarlUpright/Equirectangular_360_Downloader/issues).
