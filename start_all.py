import subprocess
import time
import os
import sys
import webbrowser

def run_process(name, cmd, cwd):
    print(f"Starting {name}...")
    # On Windows, shell=True helps resolve npm/uvicorn commands reliably
    return subprocess.Popen(
        cmd,
        cwd=cwd,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

if __name__ == "__main__":
    processes = []
    
    # 1. Start Backends
    processes.append(run_process("Radar Backend", "uvicorn main:app --port 8001", "opportunity-radar/backend"))
    processes.append(run_process("Chart Backend", "uvicorn main:app --port 8002", "chart-pattern-intel/backend"))
    processes.append(run_process("ChatGPT Backend", "uvicorn main:app --port 8003", "market-chatgpt/backend"))
    processes.append(run_process("Video Backend", "uvicorn main:app --port 8004", "market-video-engine/backend"))
    
    # 2. Start Frontends (forcing specific ports via Vite)
    processes.append(run_process("Radar Frontend", "npm run dev -- --port 3001", "opportunity-radar/frontend"))
    processes.append(run_process("Chart Frontend", "npm run dev -- --port 3002", "chart-pattern-intel/frontend"))
    processes.append(run_process("ChatGPT Frontend", "npm run dev -- --port 3003", "market-chatgpt/frontend"))
    processes.append(run_process("Video Frontend", "npm run dev -- --port 3004", "market-video-engine/frontend"))

    # 3. Start Launchpad
    if not os.path.exists("launchpad"):
        os.makedirs("launchpad")
    processes.append(run_process("Launchpad UI", f"{sys.executable} -m http.server 3000 --directory launchpad", "."))

    print("\nAll services started!")
    print("Wait a few seconds for React/Vite servers to compile...")
    
    # Open the Launchpad automatically
    time.sleep(3)
    print("\nOpening Launchpad at http://localhost:3000 ...")
    webbrowser.open("http://localhost:3000")

    print("\nPress Ctrl+C to stop all services.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down all services...")
        for p in processes:
            p.terminate()
        sys.exit(0)
