import sys
import os

def test_app(module_path, app_name):
    print(f"Testing {app_name}...")
    sys.path.insert(0, os.path.abspath(module_path))
    try:
        from main import app
        from fastapi.testclient import TestClient
        client = TestClient(app)
        try:
            res = client.get("/health")
            print(f"  [{app_name}] /health status: {res.status_code}")
        except Exception as e:
            print(f"  [{app_name}] /health failed, but app loaded: {e}")
        return True
    except Exception as e:
        print(f"  [{app_name}] FAILED to load: {e}")
        return False
    finally:
        sys.path.pop(0)

if __name__ == "__main__":
    results = [
        test_app("chart-pattern-intel/backend", "Chart Pattern Intelligence"),
        test_app("market-video-engine/backend", "Market Video Engine"),
        test_app("opportunity-radar/backend", "Opportunity Radar"),
        test_app("market-chatgpt/backend", "Market ChatGPT")
    ]
    if all(results):
        print("\nALL 4 APPS LOADED SUCCESSFULLY.")
    else:
        print("\nSOME APPS FAILED TO LOAD.")
