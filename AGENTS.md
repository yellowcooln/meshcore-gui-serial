# MeshCore GUI — Agent Notes

## Purpose
MeshCore GUI is a NiceGUI-based desktop/headless web UI for MeshCore radios. This fork uses **USB serial** (not BLE) via `meshcore`'s `create_serial` connection.

## Entry Points
- `meshcore_gui.py` (primary)
- `python -m meshcore_gui` (`meshcore_gui/__main__.py`)

### Common Run
```
./venv/bin/python meshcore_gui.py /dev/ttyACM0 --debug-on --baud=115200
```

## Architecture (High-Level)
- **UI thread (NiceGUI)**: `meshcore_gui/gui/*`
- **Worker thread (serial + asyncio)**: `meshcore_gui/ble/worker.py` (name kept for historical reasons)
- **Commands**: `meshcore_gui/ble/commands.py`
- **Events**: `meshcore_gui/ble/events.py`
- **Shared state**: `meshcore_gui/core/shared_data.py`

## Serial Connection
- Uses `MeshCore.create_serial(port, baudrate, cx_dly)`.
- Config defaults in `meshcore_gui/config.py`:
  - `SERIAL_BAUDRATE`, `SERIAL_CX_DELAY`, `DEFAULT_TIMEOUT`.

## Device Name Behavior
- BOT toggle changes device name via `set_device_name` command.
- Warning labels are shown next to BOT toggles.
- Explicit device name can be set via the **Actions** panel input.

## Map Centering
- Map is in `meshcore_gui/gui/panels/map_panel.py`.
- Centering happens on device updates or when the MAP panel is opened.
- There is a **Center on Device** button that uses the last known GPS.
- Leaflet size invalidation is called before centering to handle hidden panels.
- Map theme follows UI dark/light mode by default.
- Map theme can be overridden with the **Theme** toggle (Auto/Dark/Light).

## Panel URLs
- Drawer and sidebar actions navigate to `/?panel=<id>&channel=<optional>` so browser back restores the last panel.
- On load, the dashboard reads the query params and shows the requested panel.

## Route Viewer
- Clicking a message opens `/route/{msg_key}` in the **same tab**.
- The route page has **Back to Dashboard** and **Back to Archive** buttons.

## Refresh Behavior
- GUI refresh queues a full device reload.
- Contacts fetch is bounded by a timeout to prevent hangs.

## Persistent Data
Stored under `~/.meshcore-gui/`:
- `cache/`, `archive/`, `logs/`, `pins/`, `room_passwords/`.

## Tests
- Tests live in `tests/`.
- `pytest` is not installed by default; use `pip install pytest` in the venv.

## Legacy BLE Docs
BLE-specific docs/scripts remain in `docs/ble/` and `install_ble_stable.sh` but are marked legacy.
