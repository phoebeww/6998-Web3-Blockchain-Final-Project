import subprocess
import time
import sys
import os
import webbrowser

# Configuration
PYTHON_EXEC = sys.executable
TRACKER_PORT = 9000
NODES = [
    {"id": "node-1", "port": 8000},
    {"id": "node-2", "port": 8001},
    {"id": "node-3", "port": 8002}
]

processes = []

def start_tracker():
    print(f"Starting Tracker on port {TRACKER_PORT}...")
    p = subprocess.Popen(
        [PYTHON_EXEC, "-m", "uvicorn", "network.tracker:app", "--port", str(TRACKER_PORT)],
        cwd=os.getcwd()
    )
    processes.append(p)

def start_node(node_id, port):
    print(f"Starting {node_id} on port {port}...")
    
    env = os.environ.copy()
    env["NODE_ID"] = node_id
    env["NODE_PORT"] = str(port)
    env["TRACKER_URL"] = f"http://127.0.0.1:{TRACKER_PORT}"
    
    p = subprocess.Popen(
        [PYTHON_EXEC, "-m", "uvicorn", "api.server:app", "--port", str(port)],
        env=env,
        cwd=os.getcwd()
    )
    processes.append(p)

def open_browsers():
    print("Opening browser tabs...")
    for node in NODES:
        url = f"http://localhost:{node['port']}"
        webbrowser.open(url)

def main():
    try:
        # 1. Start Tracker
        start_tracker()
        time.sleep(2) 

        # 2. Start Nodes
        for node in NODES:
            start_node(node['id'], node['port'])
            time.sleep(1)

        # 3. Open UI
        time.sleep(2)
        open_browsers()

        print("\nNetwork is running! Press Ctrl+C to stop everything.\n")
        
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down network...")
        for p in processes:
            p.terminate()
        print("Goodbye!")

if __name__ == "__main__":
    main()