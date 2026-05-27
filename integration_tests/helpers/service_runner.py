import socket
import sys
import time
import threading
from pathlib import Path

# Ensure repo root is on sys.path so `server.*` imports resolve
REPO_ROOT = Path(__file__).parent.parent.parent.resolve()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# app.py uses bare imports like `from vault_service import ...` which only work
# when server/ is on sys.path (as it is when running `python server/app.py`)
SERVER_DIR = REPO_ROOT / "server"
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

PORT = 5021


def _wait_for_port(port: int, timeout: int = 30) -> bool:
    """Return True once something is accepting connections on *port*."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False


def start_service() -> threading.Thread:
    """Start the gRPC server in a background daemon thread.

    Because the server runs in the same process as pytest, the VS Code
    debugger will hit breakpoints in StockAssesment.py automatically.
    No CMSY_EXTERNAL_SERVICE env var needed.
    """
    from server.app import serve_in_thread

    thread = threading.Thread(target=serve_in_thread, daemon=True, name="cmsy-grpc")
    thread.start()

    if not _wait_for_port(PORT, timeout=30):
        raise RuntimeError("CMSY service did not start within 30 seconds.")

    print(f"CMSY service started in-process on port {PORT}")
    return thread


def stop_service(thread: threading.Thread):
    """Nothing to do — the daemon thread stops when pytest exits."""
    print("CMSY service thread will stop with pytest process")
