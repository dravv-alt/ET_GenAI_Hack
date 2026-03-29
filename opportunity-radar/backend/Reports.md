# Opportunity Radar Endpoint Tests

```text

--- Testing Health (GET /health) ---
SUCCESS (200) in 2.05s
Response (truncated): {'status': 'ok', 'service': 'opportunity-radar', 'port': 8001, 'version': '1.0.0'}

--- Testing Get Watchlist (GET /watchlist) ---
SUCCESS (200) in 2.05s
Response (truncated): {'tickers': ['RELIANCE', 'TCS'], 'items': [{'ticker': 'RELIANCE', 'added_at': '2026-03-29T17:13:58.822854'}, {'ticker': 'TCS', 'added_at': '2026-03-29T17:13:58.822854'}], 'count': 2}

--- Testing Update Watchlist (POST /watchlist) ---
SUCCESS (200) in 2.05s
Response (truncated): {'tickers': ['RELIANCE', 'TCS'], 'items': [{'ticker': 'RELIANCE', 'added_at': '2026-03-29T17:15:26.862255'}, {'ticker': 'TCS', 'added_at': '2026-03-29T17:15:26.862255'}], 'count': 2}

--- Testing Trigger Scan (POST /scan) ---
SUCCESS (200) in 42.44s
Response (truncated): {'status': 'complete', 'alerts_found': 2, 'tickers_scanned': ['RELIANCE', 'TCS'], 'alerts': [{'id': '426729b1-3bda-4f31-90a6-710af920e47a', 'ticker': 'RELIANCE', 'alert_type': 'insider_buy', 'signal_s

--- Testing Get Alerts (GET /alerts) ---
SUCCESS (200) in 2.06s
Response (truncated): {'alerts': [{'id': '426729b1-3bda-4f31-90a6-710af920e47a', 'ticker': 'RELIANCE', 'alert_type': 'insider_buy', 'signal_strength': 'high', 'title': 'MUKESH D AMBANI (Promoter) bought ₹124cr of RELIANCE'

--- Testing Get Alerts for RELIANCE (GET /alerts/RELIANCE) ---
SUCCESS (200) in 2.03s
Response (truncated): {'ticker': 'RELIANCE', 'alerts': [{'id': '426729b1-3bda-4f31-90a6-710af920e47a', 'ticker': 'RELIANCE', 'alert_type': 'insider_buy', 'signal_strength': 'high', 'title': 'MUKESH D AMBANI (Promoter) boug

--- Testing Get High Alerts (GET /alerts) ---
SUCCESS (200) in 2.05s
Response (truncated): {'alerts': [{'id': '426729b1-3bda-4f31-90a6-710af920e47a', 'ticker': 'RELIANCE', 'alert_type': 'insider_buy', 'signal_strength': 'high', 'title': 'MUKESH D AMBANI (Promoter) bought ₹124cr of RELIANCE'
```
