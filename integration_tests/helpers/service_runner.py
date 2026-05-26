import subprocess
import time
import os
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.resolve()
PYTHON = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
APP = REPO_ROOT / "server" / "app.py"


def start_service() -> subprocess.Popen:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["PYTHONIOENCODING"] = "utf-8"

    process = subprocess.Popen(
        [str(PYTHON), str(APP)],
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    time.sleep(5)  # Wait for the service to fully start
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        raise RuntimeError(
            f"Service failed to start.\nSTDOUT: {stdout.decode()}\nSTDERR: {stderr.decode()}"
        )
    print(f"CMSY service started (pid={process.pid})")
    return process


def stop_service(process: subprocess.Popen):
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
    print("CMSY service stopped")
