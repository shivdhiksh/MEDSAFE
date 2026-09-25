# MEDSAFE — Offline Medicine Expiry Tracker

MedSafe is a free, private, offline-first Windows desktop application designed to track medicine expiry dates locally, protecting households from accidentally using expired medications.

---

## ⚠️ Important Safety & Medical Disclaimer

> **MEDSAFE helps organize medicine expiry information. It does not provide medical advice. Always verify the original packaging and consult a pharmacist or healthcare professional if you are unsure whether a medicine can be used.**

MedSafe does not make safety judgments, determine medical efficacy, or provide dosage recommendations.

---

## 👤 End Users Guide

### 1. Installation
1. Download `MedSafe_Setup_v1.0.exe`.
2. Double-click the installer to run the setup wizard.
3. **No Administrator Rights Required**: MedSafe installs into your personal user profile:
   ```text
   %LOCALAPPDATA%\Programs\MedSafe\
   ```
4. Optional choices during installation:
   - Create a Desktop shortcut.
   - **Enable Daily Expiry Notifications**: Automatically checks your medicine inventory every morning at 9:00 AM using Windows native toast alerts.

### 2. How to Launch
- Open your **Start Menu** and search for **MEDSAFE**.
- Double-click the **MEDSAFE** shortcut on your Desktop (if enabled).
- Or run directly from: `%LOCALAPPDATA%\Programs\MedSafe\MedSafe.exe`.

### 3. Where Your Data Is Stored
All your medicine records, settings, and backups remain 100% private on your computer:
- **Local Database**: `%LOCALAPPDATA%\MedSafe\data\medsafe.db`
- **Exports & Backups**: `%LOCALAPPDATA%\MedSafe\backups\`
- **Application Logs**: `%LOCALAPPDATA%\MedSafe\logs\medsafe.log`

No accounts, no internet connection, and no cloud synchronization are ever used.

### 4. Backups and Data Exports
- Open **Settings** in the application.
- Click **Export CSV** to create a spreadsheet of your entire medicine inventory.
- Click **Export JSON** to create a full structured backup.
- Click **📂 Open Backups Folder** to access your export files directly in Windows Explorer.

### 5. Daily Expiry Reminders
If scheduled notifications are enabled, MedSafe runs quietly in the background at 9:00 AM without opening any windows. When a medicine batch reaches an alert threshold (default: 30, 7, or 1 days before expiry, or when expired), a native Windows toast notification appears. Duplicate alerts are automatically suppressed on the same day.

### 6. Uninstallation & Data Protection
- To uninstall, open **Windows Settings → Apps → Installed apps**, locate **MEDSAFE**, and click **Uninstall** (or use **Start Menu → MEDSAFE → Uninstall MEDSAFE**).
- **Your Data Remains Safe**: Uninstalling MedSafe removes the program binaries, shortcuts, and scheduled task. **It does NOT delete your medicine database or backups** in `%LOCALAPPDATA%\MedSafe\`. If you reinstall MedSafe in the future, all your medicine records will be restored automatically.

---

## 🛠️ Developer Guide

### 1. Architecture Overview
MedSafe enforces a strict unidirectional layer separation:
$$\text{Frontend View} \longrightarrow \text{Backend Service} \longrightarrow \text{Backend Repository} \longrightarrow \text{SQLite}$$

- `frontend/`: CustomTkinter desktop interface (zero SQL, zero direct `sqlite3` access).
- `backend/`: Business services, data models, repositories, and platform utilities (zero CustomTkinter imports).
- `backend/config.py`: Dual-mode path resolution. Resolves local workspace paths during development and `%LOCALAPPDATA%\MedSafe` when packaged.

### 2. Prerequisites
- **Operating System**: Windows 10 or Windows 11.
- **Python**: Python 3.11 or newer (Python 3.13 recommended).
- **Inno Setup**: Version 6 (for building the Windows installer).

### 3. Running From Source
1. Open PowerShell in the project directory:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. Launch the desktop GUI:
   ```powershell
   python -m frontend.main
   ```
3. Run the headless notification checker:
   ```powershell
   python -m frontend.main --check-notifications
   ```

### 4. Running Automated Tests
Run the complete pytest regression suite:
```powershell
pytest -v
```

### 5. Building the Standalone Executable (PyInstaller ONEDIR)
Compile the standalone distribution with CustomTkinter asset bundling:
```powershell
pip install pyinstaller
pyinstaller medsafe.spec --noconfirm --clean
```
Output directory: `dist/MedSafe/` containing `MedSafe.exe` and `_internal/`.

### 6. Building the Windows Installer (Inno Setup)
Compile the single-file setup wizard:
```powershell
& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" setup.iss
```
Output installer: `dist/installer/MedSafe_Setup_v1.0.exe`.

---

## 🔍 Inspecting the SQLite Database

You can inspect the local SQLite database safely:

### Development Mode Database
```powershell
sqlite3 data/medsafe.db ".tables"
sqlite3 data/medsafe.db "SELECT * FROM settings;"
```

### Production Mode Database
```powershell
sqlite3 "$env:LOCALAPPDATA\MedSafe\data\medsafe.db" ".tables"
```

You can also open the `.db` file in **DB Browser for SQLite** or the **SQLite Viewer** IDE extension.
