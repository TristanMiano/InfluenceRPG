#!/usr/bin/env python3
"""
server_control.py - Script to start and stop the Influence RPG Prototype Server.

Usage:
    python server_control.py start  -> Starts the server.
    python server_control.py stop   -> Stops the server (if running in background).

Notes:
- This script uses uvicorn to run the FastAPI server defined in src/server/main.py.
- The script automatically sets the working directory to the project root (the parent of the "src" folder)
  if it's run from within the "src" directory.
- The server's process ID is saved to a file (server.pid) for later termination.
"""

import sys
import os
import subprocess
import signal
import time

PID_FILE = "server.pid"

def get_project_root() -> str:
    """
    Determines the project root directory.
    If the current working directory is the "src" folder, returns its parent; otherwise, returns the current directory.
    """
    cwd = os.getcwd()
    if os.path.basename(cwd).lower() == "src":
        return os.path.abspath(os.path.join(cwd, os.pardir))
    return cwd

def start_server():
    project_root = get_project_root()
    # Always use the module path as if launched from the project root.
    module_path = "src.server.main:app"
    cmd = [
        "python", "-m", "uvicorn", module_path,
        "--reload",
        "--reload-dir", "src/server/static",
        "--reload-dir", "src/server/templates",
        "--host", "127.0.0.1", "--port", "8000"
    ]
    
    try:
        proc = subprocess.Popen(cmd, cwd=project_root)
        with open(PID_FILE, "w") as f:
            f.write(str(proc.pid))
        print("Server started with PID:", proc.pid)
        print("Press CTRL+C in this window to stop the server, or run:")
        print("    python server_control.py stop")
        proc.wait()
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Stopping server...")
        proc.terminate()
        proc.wait()
    except Exception as e:
        print("Error starting server:", e)

def stop_server():
    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read())
        print("Stopping server with PID:", pid)
        os.kill(pid, signal.SIGTERM)
        time.sleep(2)
        os.remove(PID_FILE)
        print("Server stopped.")
    except Exception as e:
        print("Error stopping server:", e)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python server_control.py [start|stop]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    if command == "start":
        start_server()
    elif command == "stop":
        stop_server()
    else:
        print("Unknown command:", command)
        sys.exit(1)
