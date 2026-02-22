# VnManager

A desktop app for tracking Visual Novels, powered by the [VNDB Kana API](https://api.vndb.org/kana).

![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-green)

---

## Features

- **Search VnDB** — Search the VNDB database by title and browse up to 50 results
- **Custom categories** — Create, rename and delete your own categories (e.g. *Playing*, *Finished*, *Planned* (by default))
- **Add / Remove VNs** — Add any search result to a category of your choice
- **Persistent save** — Your library is saved to `data/save.json` automatically after every change

---

## Installation

### Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.10 or newer |
---

### Arch Linux

```bash
# 1. Install Python (usually pre-installed on Arch)
sudo pacman -S python python-pip

# 2. Install Tkinter (required by CustomTkinter)
sudo pacman -S tk

# 3. Clone the repository
git clone https://github.com/youruser/VnManager.git
cd VnManager

# 4. (Recommended) Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# 5. Install dependencies
pip install -r requirements.txt

# 6. Run the app
python main.py
```

> **Note:** If you use a Wayland compositor, you may need to set `GDK_BACKEND=x11` or install `xorg-xwayland` for Tkinter to work correctly:
> ```bash
> GDK_BACKEND=x11 python main.py
> ```

---

### Windows

```powershell
# 1. Download and install Python from https://www.python.org/downloads/
#    Make sure to check "Add Python to PATH" during installation

# 2. Clone the repository (requires Git — https://git-scm.com/)
git clone https://github.com/youruser/VnManager.git
cd VnManager

# 3. (Recommended) Create a virtual environment
python -m venv .venv
.venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the app
python main.py
```

> **Note:** Tkinter ships with the official Python Windows installer by default, so no extra steps are needed.

---

## Dependencies

| Package | Purpose |
|---|---|
| `customtkinter` | Modern themed UI widgets |
| `Pillow` | Image loading and processing |
| `requests` | HTTP calls to the VNDB API |

---

## Data & Privacy

All data is stored locally in `data/save.json`. Nothing is sent anywhere except search queries to the public [VNDB Kana API](https://api.vndb.org/kana).
