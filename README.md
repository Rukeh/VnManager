# VnManager

A desktop app for tracking Visual Novels, powered by the [VNDB Kana API](https://api.vndb.org/kana).

## Setup

```bash
pip install -r requirements.txt
python main.py
```

## Project Structure

```
VnManager/
├── main.py                  # Entry point
├── requirements.txt
├── assets/
│   └── logo.png
├── data/
│   └── save.json            # Your save data
└── app/
    ├── api/
    │   └── vndb.py          # VNDB API calls
    ├── ui/
    │   ├── main_window.py   # Main app window
    │   └── search_window.py # VN search popup
    └── utils/
        ├── image.py         # Image loading
        └── text.py          # Description cleaning
```

## Features

- Organise VNs into custom categories
- Search VnDB and browse results in list or grid view
- Cover art loaded asynchronously
