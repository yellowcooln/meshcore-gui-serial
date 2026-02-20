#!/usr/bin/env python3
"""
MeshCore GUI — Threaded Serial Edition
====================================

Entry point.  Parses arguments, wires up the components, registers
NiceGUI pages and starts the server.

Usage:
    python meshcore_gui.py <SERIAL_PORT>
    python meshcore_gui.py <SERIAL_PORT> --debug-on
    python meshcore_gui.py <SERIAL_PORT> --port=9090
    python meshcore_gui.py <SERIAL_PORT> --baud=115200
    python meshcore_gui.py <SERIAL_PORT> --serial-cx-dly=0.1
    python meshcore_gui.py <SERIAL_PORT> --ssl
    python -m meshcore_gui <SERIAL_PORT>

                   Author: PE1HVH
                  Version: 5.0
  SPDX-License-Identifier: MIT
                Copyright: (c) 2026 PE1HVH
"""

import sys

from nicegui import app, ui

# Allow overriding DEBUG before anything imports it
import meshcore_gui.config as config

try:
    from meshcore import MeshCore, EventType  # noqa: F401 — availability check
except ImportError:
    print("ERROR: meshcore library not found")
    print("Install with: pip install meshcore")
    sys.exit(1)

from meshcore_gui.ble.worker import SerialWorker
from meshcore_gui.core.shared_data import SharedData
from meshcore_gui.gui.dashboard import DashboardPage
from meshcore_gui.gui.route_page import RoutePage
from meshcore_gui.gui.archive_page import ArchivePage
from meshcore_gui.services.pin_store import PinStore
from meshcore_gui.services.room_password_store import RoomPasswordStore


# Global instances (needed by NiceGUI page decorators)
_shared = None
_dashboard = None
_route_page = None
_archive_page = None


@ui.page('/')
def _page_dashboard():
    """NiceGUI page handler — main dashboard."""
    if _dashboard:
        _dashboard.render()


@ui.page('/route/{msg_key}')
def _page_route(msg_key: str):
    """NiceGUI page handler — route visualization."""
    if _route_page:
        _route_page.render(msg_key)


@ui.page('/archive')
def _page_archive():
    """NiceGUI page handler — message archive."""
    if _archive_page:
        _archive_page.render()


def main():
    """
    Main entry point.

    Parses CLI arguments, initialises all components and starts the
    NiceGUI server.
    """
    global _shared, _dashboard, _route_page, _archive_page

    # Parse arguments
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    flags = [a for a in sys.argv[1:] if a.startswith('--')]

    if not args:
        print("MeshCore GUI - Threaded Serial Edition")
        print("=" * 40)
        print("Usage: python meshcore_gui.py <SERIAL_PORT> [--debug-on] [--port=PORT] [--baud=BAUD] [--serial-cx-dly=SECONDS] [--ssl]")
        print("Example: python meshcore_gui.py /dev/ttyACM0")
        print("         python meshcore_gui.py /dev/ttyACM0 --debug-on")
        print("         python meshcore_gui.py /dev/ttyACM0 --port=9090")
        print("         python meshcore_gui.py /dev/ttyACM0 --baud=57600")
        print("         python meshcore_gui.py /dev/ttyACM0 --serial-cx-dly=0.1")
        print("         python meshcore_gui.py /dev/ttyACM0 --ssl")
        print()
        print("Options:")
        print("  --debug-on        Enable verbose debug logging")
        print("  --port=PORT       Web server port (default: 8081)")
        print("  --baud=BAUD       Serial baudrate (default: 115200)")
        print("  --serial-cx-dly=SECONDS  Serial connection delay (default: 0.1)")
        print("  --ssl             Enable HTTPS with auto-generated self-signed certificate")
        print()
        print("Tip: On Linux, use 'ls -l /dev/serial/by-id' to find your device")
        sys.exit(1)

    serial_port = args[0]
    config.set_log_file_for_device(serial_port)

    # Apply --debug-on flag
    if '--debug-on' in flags:
        config.DEBUG = True

    # Apply --port flag
    port = 8081
    for flag in flags:
        if flag.startswith('--port='):
            try:
                port = int(flag.split('=', 1)[1])
            except ValueError:
                print(f"ERROR: Invalid port number: {flag}")
                sys.exit(1)

    # Apply --baud flag
    for flag in flags:
        if flag.startswith('--baud='):
            try:
                config.SERIAL_BAUDRATE = int(flag.split('=', 1)[1])
            except ValueError:
                print(f"ERROR: Invalid baudrate: {flag}")
                sys.exit(1)

    # Apply --serial-cx-dly flag
    for flag in flags:
        if flag.startswith('--serial-cx-dly='):
            try:
                config.SERIAL_CX_DELAY = float(flag.split('=', 1)[1])
            except ValueError:
                print(f"ERROR: Invalid serial cx delay: {flag}")
                sys.exit(1)

    # Apply --ssl flag (auto-generate self-signed certificate if needed)
    ssl_enabled = '--ssl' in flags
    ssl_keyfile = None
    ssl_certfile = None

    if ssl_enabled:
        import socket
        import subprocess
        from pathlib import Path
        ssl_dir = config.DATA_DIR / 'ssl'
        ssl_dir.mkdir(parents=True, exist_ok=True)
        ssl_keyfile = str(ssl_dir / 'key.pem')
        ssl_certfile = str(ssl_dir / 'cert.pem')

        if not (ssl_dir / 'cert.pem').exists():
            # Detect local IP for SAN (Subject Alternative Name)
            local_ip = '127.0.0.1'
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(('8.8.8.8', 80))
                local_ip = s.getsockname()[0]
                s.close()
            except Exception:
                pass

            san = f"DNS:localhost,IP:127.0.0.1,IP:{local_ip}"
            print(f"Generating self-signed SSL certificate (SAN: {san}) ...")
            subprocess.run([
                'openssl', 'req', '-x509',
                '-newkey', 'rsa:2048',
                '-keyout', ssl_keyfile,
                '-out', ssl_certfile,
                '-days', '3650',
                '-nodes',
                '-subj', '/CN=DOMCA MeshCore GUI',
                '-addext', f'subjectAltName={san}',
            ], check=True, capture_output=True)
            print(f"Certificate saved to {ssl_dir}/")
        else:
            print(f"Using existing certificate from {ssl_dir}/")

    # Startup banner
    print("=" * 50)
    print("MeshCore GUI - Threaded Serial Edition")
    print("=" * 50)
    print(f"Device:     {serial_port}")
    print(f"Port:       {port}")
    print(f"Baudrate:   {config.SERIAL_BAUDRATE}")
    print(f"CX delay:   {config.SERIAL_CX_DELAY}")
    print(f"SSL:        {'ON (https)' if ssl_enabled else 'OFF (http)'}")
    print(f"Debug mode: {'ON' if config.DEBUG else 'OFF'}")
    print("=" * 50)

    # Assemble components
    _shared = SharedData(serial_port)
    _pin_store = PinStore(serial_port)
    _room_password_store = RoomPasswordStore(serial_port)
    _dashboard = DashboardPage(_shared, _pin_store, _room_password_store)
    _route_page = RoutePage(_shared)
    _archive_page = ArchivePage(_shared)

    # Start Serial worker in background thread
    worker = SerialWorker(
        serial_port,
        _shared,
        baudrate=config.SERIAL_BAUDRATE,
        cx_dly=config.SERIAL_CX_DELAY,
    )
    worker.start()

    # Serve static PWA assets (manifest, icons)
    from pathlib import Path
    static_dir = Path(__file__).parent / 'static'
    if static_dir.is_dir():
        app.add_static_files('/static', str(static_dir))

    # Start NiceGUI server (blocks)
    run_kwargs = dict(
        show=False, host='0.0.0.0', title='DOMCA MeshCore',
        port=port, reload=False, storage_secret='meshcore-gui-secret',
    )
    if ssl_enabled:
        run_kwargs['ssl_keyfile'] = ssl_keyfile
        run_kwargs['ssl_certfile'] = ssl_certfile
    ui.run(**run_kwargs)


if __name__ == "__main__":
    main()
