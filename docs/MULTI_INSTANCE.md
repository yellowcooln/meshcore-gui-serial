# Running Multiple MeshCore GUI Instances

> ⚠️ **WARNING: This guide has not been tested yet.** The configuration below is based on the application's architecture and should work, but has not been validated in practice. Please report any issues.

## Overview

MeshCore GUI supports running multiple instances simultaneously — for example, to monitor two different MeshCore devices from the same machine. Each instance gets its own web port, BLE connection, and all persistent data (cache, archive, logs, pins, room passwords) is automatically separated by BLE device address.

## Prerequisites

- MeshCore GUI v1.9.2 or later (with `--port` and `--ble-pin` CLI parameters)
- D-Bus policy file installed (see main README, section 5.5)

## Quick Test (foreground)

Before creating services, verify that both instances start correctly:

**Terminal 1:**
```bash
cd ~/meshcore-gui
source venv/bin/activate
python meshcore_gui.py F0:9E:9E:75:A3:01 --debug-on --port=8081 --ble-pin=171227
```

**Terminal 2:**
```bash
cd ~/meshcore-gui
source venv/bin/activate
python meshcore_gui.py AA:BB:CC:DD:EE:FF --debug-on --port=8082 --ble-pin=123456
```

Verify both are accessible at `http://localhost:8081` and `http://localhost:8082`.

## systemd Service Setup

### Service 1

```bash
sudo nano /etc/systemd/system/meshcore-gui-device1.service
```

```ini
[Unit]
Description=MeshCore GUI — Device 1 (F0:9E:9E:75:A3:01)
After=bluetooth.target
Wants=bluetooth.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/meshcore-gui
ExecStart=/home/your-username/meshcore-gui/venv/bin/python meshcore_gui.py F0:9E:9E:75:A3:01 --debug-on --port=8081 --ble-pin=171227
Restart=on-failure
RestartSec=30
Environment=DBUS_SYSTEM_BUS_ADDRESS=unix:path=/var/run/dbus/system_bus_socket

[Install]
WantedBy=multi-user.target
```

### Service 2

```bash
sudo nano /etc/systemd/system/meshcore-gui-device2.service
```

```ini
[Unit]
Description=MeshCore GUI — Device 2 (AA:BB:CC:DD:EE:FF)
After=bluetooth.target
Wants=bluetooth.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/meshcore-gui
ExecStart=/home/your-username/meshcore-gui/venv/bin/python meshcore_gui.py AA:BB:CC:DD:EE:FF --debug-on --port=8082 --ble-pin=123456
Restart=on-failure
RestartSec=30
Environment=DBUS_SYSTEM_BUS_ADDRESS=unix:path=/var/run/dbus/system_bus_socket

[Install]
WantedBy=multi-user.target
```

Replace `your-username` and BLE addresses/PINs with your actual values.

### Enable and Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable meshcore-gui-device1 meshcore-gui-device2
sudo systemctl start meshcore-gui-device1
sudo systemctl start meshcore-gui-device2
```

## Data Separation

All persistent data is automatically separated by BLE device address. No additional configuration is needed.

| Data | Path example (device F0:9E:9E:75:A3:01) |
|------|------------------------------------------|
| Web interface | `http://host:8081` (via `--port`) |
| Cache | `~/.meshcore-gui/cache/F0_9E_9E_75_A3_01.json` |
| Message archive | `~/.meshcore-gui/archive/F0_9E_9E_75_A3_01_messages.json` |
| RX log archive | `~/.meshcore-gui/archive/F0_9E_9E_75_A3_01_rxlog.json` |
| Debug log | `~/.meshcore-gui/logs/F0_9E_9E_75_A3_01_meshcore_gui.log` |
| Pin state | `~/.meshcore-gui/pins/F0_9E_9E_75_A3_01_pins.json` |
| Room passwords | `~/.meshcore-gui/room_passwords/F0_9E_9E_75_A3_01_rooms.json` |

## Useful Commands

| Command | Description |
|---------|-------------|
| `sudo systemctl status meshcore-gui-device1` | Check status of device 1 |
| `sudo systemctl status meshcore-gui-device2` | Check status of device 2 |
| `sudo journalctl -u meshcore-gui-device1 -f` | Follow live log of device 1 |
| `sudo journalctl -u meshcore-gui-device2 -f` | Follow live log of device 2 |
| `sudo systemctl restart meshcore-gui-device1` | Restart device 1 (without affecting device 2) |
| `sudo systemctl stop meshcore-gui-device1` | Stop device 1 only |
| `sudo systemctl disable meshcore-gui-device1` | Prevent device 1 from starting on boot |

## Bluetooth Adapter Note

Most modern Bluetooth 4.0+ adapters (including the Raspberry Pi's built-in adapter) support **multiple simultaneous BLE connections** — typically 5 to 10, depending on the chipset. Running two MeshCore GUI instances against two different devices on a single adapter should work fine.

To verify your adapter:

```bash
bluetoothctl list
```

> **Note:** If you experience connection instability with multiple simultaneous BLE connections, adding a USB BLE dongle as a second adapter is an option. However, this should not be necessary in most cases.

## Removing a Service

```bash
sudo systemctl stop meshcore-gui-device2
sudo systemctl disable meshcore-gui-device2
sudo rm /etc/systemd/system/meshcore-gui-device2.service
sudo systemctl daemon-reload
```

Optionally remove the device's persistent data:

```bash
rm ~/.meshcore-gui/cache/AA_BB_CC_DD_EE_FF.json
rm ~/.meshcore-gui/archive/AA_BB_CC_DD_EE_FF_*.json
rm ~/.meshcore-gui/logs/AA_BB_CC_DD_EE_FF_meshcore_gui.log
rm ~/.meshcore-gui/pins/AA_BB_CC_DD_EE_FF_pins.json
rm ~/.meshcore-gui/room_passwords/AA_BB_CC_DD_EE_FF_rooms.json
```
