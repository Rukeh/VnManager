# Copilot Instructions for VnManager

## Build, run, and verification commands

- Install dependencies:
  - `pip install -r requirements.txt`
- Run the app locally:
  - `python main.py`
- Linux/Wayland fallback (from README):
  - `GDK_BACKEND=x11 python main.py`
- Build AppImage (Docker-based):
  - `./build-appimage.sh`

There is currently no configured automated test suite or lint/type-check command in this repository (no `tests/`, `pytest` config, or lint config files).  
When validating changes, use targeted runtime checks by launching the app and exercising the changed UI flow.

## High-level architecture

- Entrypoint is `main.py`, which calls `run()` in `app/ui/main/main_window.py`.
- `main_window.py` composes the top-level views (menu, library, settings) and creates a shared `AppState` object that carries:
  - persistent data (`data`)
  - selected category and UI vars (`selected_category`, `search_var`, `sort_var`)
  - refresh callbacks wired by submodules (`refresh_categories`, `refresh_library`)
- Main UI modules:
  - `app/ui/main/categories.py`: category CRUD, selected-category state, and sidebar rendering
  - `app/ui/main/library.py`: VN cards, sorting/filtering, notes popup, remove/move actions
  - `app/ui/main/settings_panel.py`: performance toggle + cover-cache controls
  - `app/ui/search/search_window.py`: VNDB search window, list/grid rendering, tag query builder
  - `app/ui/search/vn_detail.py`: details popup used from both library and search
- API boundary:
  - `app/api/vndb.py` encapsulates VNDB calls (`search_vns`, `search_tags`) and retry behavior via `_post_with_retry`.
- Persistence boundary:
  - `app/utils/save.py` owns save-file location and JSON serialization.
  - All feature modules mutate `data` and persist via `save_data(data)`.
- Image subsystem:
  - `app/utils/image.py` handles cover download, disk/memory caching, async image tasks, and context-specific cover sizing.

## Key repository conventions

- Persisted data shape is centralized in `app/utils/save.py`:
  - `data["categories"]`: ordered category names
  - `data["vns"][category]`: list of VN dicts for that category
  - `data["settings"]`: feature flags and cache limits
- Cross-module state updates follow this pattern:
  - mutate `data` in-place
  - call `save_data(data)`
  - trigger relevant refresh callback(s) from `AppState`
- Search tag semantics are intentional and must be preserved:
  - tags within a group = OR
  - groups = AND
  - encoded as `tag_groups: list[list[tag_id]]` and passed to `search_vns(...)`.
- Search/render concurrency conventions (`search_window.py`):
  - use thread pools for network/image work
  - use `_render_gen` generation checks to drop stale renders
  - cancel queued image futures when starting a new search
  - schedule UI updates back on the Tk thread with `window.after(...)`
- Platform paths must use helpers, not hardcoded paths:
  - save file via `_get_save_dir()` in `save.py`
  - cover cache via `_get_cover_cache_dir()` in `image.py`
- Tag rendering has a project-specific performance mode:
  - `set_low_perf_mode()` in `app/ui/shared/components.py` toggles chip rendering vs plain text.
