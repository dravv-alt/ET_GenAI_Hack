import subprocess
import time
import os
import sys
import webbrowser

def run_process(name, cmd, cwd):
    print(f"Starting {name} in {cwd}...")
    
    # Auto-run npm install if it's a frontend and node_modules is missing
    if "frontend" in cwd and not os.path.exists(os.path.join(cwd, "node_modules")):
        print(f"[{name}] node_modules missing. Running npm install first...")
        subprocess.run("npm install", cwd=cwd, shell=True)

    # Auto-run pip install if it's a backend (very quick if already installed)
    if "backend" in cwd and os.path.exists(os.path.join(cwd, "requirements.txt")):
        print(f"[{name}] Ensuring requirements are installed...")
        subprocess.run(f"{sys.executable} -m pip install -r requirements.txt", cwd=cwd, shell=True)

    # On Windows, shell=True helps resolve commands reliably
    # We remove DEVNULL so you can actually see if it crashes!
    return subprocess.Popen(
        cmd,
        cwd=cwd,
        shell=True
    )

if __name__ == "__main__":
    processes = []
    
    # 1. Start all FastAPI Backends
    processes.append(run_process("Radar Backend", "python -m uvicorn main:app --port 8001", "opportunity-radar/backend"))
    processes.append(run_process("Chart Backend", "python -m uvicorn main:app --port 8002", "chart-pattern-intel/backend"))
    processes.append(run_process("ChatGPT Backend", "python -m uvicorn main:app --port 8003", "market-chatgpt/backend"))
    processes.append(run_process("Video Backend", "python -m uvicorn main:app --port 8004", "market-video-engine/backend"))
    
    # 2. Start Frontends (forcing specific ports via Vite)
    processes.append(run_process("Radar Frontend", "npm run dev -- --port 3001", "opportunity-radar/frontend"))
    processes.append(run_process("Chart Frontend", "npm run dev -- --port 3002", "chart-pattern-intel/frontend"))
    processes.append(run_process("ChatGPT Frontend", "npm run dev -- --port 3003", "market-chatgpt/frontend"))
    processes.append(run_process("Video Frontend", "npm run dev -- --port 3004", "market-video-engine/frontend"))

    # 3. Start Launchpad
    if not os.path.exists("launchpad"):
        os.makedirs("launchpad")
    processes.append(run_process("Launchpad UI", f"{sys.executable} -m http.server 3000", "launchpad"))

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
