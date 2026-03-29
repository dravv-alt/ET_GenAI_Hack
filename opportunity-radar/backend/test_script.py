import requests
import json
import time
import sys

# Ensure stdout uses utf-8 on Windows
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8001"
output = []

def log(msg):
    output.append(msg)
    try:
        print(msg)
    except:
        pass

def test_endpoint(name, method, endpoint, **kwargs):
    url = f"{BASE_URL}{endpoint}"
    log(f"\n--- Testing {name} ({method} {endpoint}) ---")
    try:
        t0 = time.time()
        start_time = time.time()
        if method == "GET":
            response = requests.get(url, **kwargs)
        elif method == "POST":
            response = requests.post(url, **kwargs)
        duration = time.time() - t0
        
        status = response.status_code
        try:
            data = response.json()
        except:
            data = response.text
            
        if status in [200, 201]:
            log(f"SUCCESS ({status}) in {duration:.2f}s")
            log(f"Response (truncated): {str(data)[:200]}")
            return True, data
        else:
            log(f"FAILED ({status}) in {duration:.2f}s")
            log(f"Response: {str(data)}")
            return False, data
    except Exception as e:
        log(f"ERROR: {str(e)}")
        return False, str(e)

if __name__ == "__main__":
    
    # Wait for server to be ready
    server_ready = False
    for i in range(30):
        try:
            resp = requests.get(f"{BASE_URL}/health")
            if resp.status_code == 200:
                server_ready = True
                break
        except requests.exceptions.ConnectionError:
            pass
        print(f"Waiting for server... ({i+1}/30)")
        time.sleep(2)
        
    if not server_ready:
        log("Server failed to start or is unreachable on port 8001 after 60 seconds.")
        with open("../Reports.md", "w", encoding="utf-8") as f:
            f.write("# Opportunity Radar Endpoint Tests\n\nServer failed to start.\n")
        exit(1)
        
    print("Server is up! Testing endpoints...")
    time.sleep(1)
    
    # 1. Health check
    test_endpoint("Health", "GET", "/health")
    
    # 2. Watchlist (GET)
    test_endpoint("Get Watchlist", "GET", "/watchlist")
    
    # 3. Watchlist (POST)
    test_endpoint("Update Watchlist", "POST", "/watchlist", json={"tickers": ["RELIANCE", "TCS"]})
    
    # 4. Trigger Scan
    test_endpoint("Trigger Scan", "POST", "/scan", json=["RELIANCE", "TCS"])
    
    # 5. Get All Alerts
    test_endpoint("Get Alerts", "GET", "/alerts")
    
    # 6. Get Alerts specifically for a ticker
    test_endpoint("Get Alerts for RELIANCE", "GET", "/alerts/RELIANCE")

    # 7. Get Filters
    test_endpoint("Get High Alerts", "GET", "/alerts", params={"signal": "high", "limit": 2})

    with open("../Reports.md", "w", encoding="utf-8") as f:
        f.write("# Opportunity Radar Endpoint Tests\n\n")
        f.write("```text\n")
        f.write("\n".join(output))
        f.write("\n```\n")
