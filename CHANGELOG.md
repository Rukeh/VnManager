# Changelog

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
