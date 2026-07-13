# Changelog

## [0.3.0] - 2026-07-14
### New features
- Welcome menu screen
- Settings panel to configure theme and qol options
- Added ability to change themes of the app in settings
- Barebone topbar to navigate between menus
- Cover cache management in Settings: configurable max cached covers, cache scope toggle (main window only vs. include search)
- Reset savefile option (danger zone in settings)
- Tag-based search with AND/OR (works similarly to vndb search, read in app explanation)
- "Load more" pagination for search results, with a render cap safeguard for very large result sets as it caused bug previously
- VN detail popup now shows languages, platforms, VNDB ID, and length in minutes, plus a direct "Open on VNDB" link
### Fixes
- Increased scroll speed
- Search failures now show an inline error message instead of failing silently
- Wraplength and layout sizing corrected on Windows HiDPI/scaled displays (not fully tested)
- Library and search results now render in batches to keep the UI responsive with large lists (probably cant do more to keep window responsive as its a ctkinter limitation)

---

## [0.2.0] - 2026-03-08
### New features
- VN detail popup 
- Personal notes on library VNs
- Move VNs between categories
- Category rename and delete
- Tag chips on cards and search results
- Filter and sort VNs within a category
- NSFW content toggle in search
- Touchpad scroll support on Linux
### Fixes
- Window resizing no longer triggers excessive refreshes
- Stale search renders are cancelled when switching view or searching again
- Image loading tasks are cancelled on new search instead of piling up
- Text wrapping updates correctly when resizing windows
- Save failures now show an error message instead of silently failing
- Category state preserved correctly after rename
### Distribution
- Windows executable (.exe) available
- Now also available on the Arch Linux User Repository (AUR)

---

## [0.1.0] - 2026-02-25
### Initial release
- Search VnDB by title, browse up to 50 results
- List and grid view for search results
- Add VNs to custom categories
- Remove VNs from categories
- Create, rename and delete categories
- Persistent save to data/save.json
- Async image loading 