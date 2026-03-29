import requests, json, time, sys

print("=== 1. Testing GET /market/live ===")
try:
    res = requests.get("http://localhost:8003/market/live")
    if res.status_code == 200:
        data = res.json()
        stocks = data.get("data", [])
        print(f"SUCCESS! Retrieved {len(stocks)} stocks.")
        if stocks:
            print(f"Top gainer: {stocks[0]['ticker']} at ₹{stocks[0]['current_price']} ({stocks[0]['pnl_pct']}%)")
    else:
        print(f"FAILED (Status {res.status_code}): {res.text}")
        sys.exit(1)
except Exception as e:
    print(f"FAILED to connect: {e}")
    sys.exit(1)

print("\n=== 2. Testing POST /chat (SSE STREAMS) ===")
payload = {
    "question": "Which of these top 2 gainers look best fundamentally?",
    "portfolio": [],
    "market_context": stocks[:2],
    "conversation_history": []
}

try:
    res = requests.post("http://localhost:8003/chat", json=payload, stream=True)
    if res.status_code == 200:
        for line in res.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith("data: "):
                    content = decoded_line[6:]
                    try:
                        event = json.loads(content)
                        if event['type'] == 'thinking':
                            print(f"\033[93m[ THINKING ]\033[0m {event['content']}")
                        elif event['type'] == 'token':
                            print(f"\033[92m{event['content']}\033[0m", end='', flush=True)
                        elif event['type'] == 'signal_card':
                            print(f"\n\n\033[96m[ SIGNAL GENERATED ]\033[0m {event['content']['ticker']} | {event['content']['signal'].upper()}")
                        elif event['type'] == 'source':
                            print(f"\n\033[94m[ SOURCE CITED ]\033[0m {event['url']}")
                        elif event['type'] == 'error':
                            print(f"\n\033[91m[ ERROR ]\033[0m {event['content']}")
                    except Exception as e:
                        pass
        print("\n\nSTREAM COMPLETE.")
    else:
        print(f"FAILED (Status {res.status_code}): {res.text}")
except Exception as e:
    print(f"FAILED to connect: {e}")
