# VnManager

A desktop app for tracking Visual Novels, powered by the [VNDB Kana API](https://api.vndb.org/kana).

![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-green)

## Features

- Search the VNDB database by title
- Add VNs to custom categories (Playing, Finished, Planned by default)
- Remove VNs and manage categories
- Data is saved locally in `data/save.json`

## Requirements

- Python 3.10 or newer
- On Linux: `tk` package (usually `sudo pacman -S tk` or `sudo apt install python3-tk`)

## Installation

```bash
git clone https://github.com/Rukeh/VnManager.git
cd VnManager
pip install -r requirements.txt
python main.py
```

> **Linux/Wayland:** If the window doesn't open, try `GDK_BACKEND=x11 python main.py`

## License

MIT — see [LICENSE](LICENSE)