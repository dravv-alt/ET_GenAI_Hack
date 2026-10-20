# Backend (Python only)

This backend is implemented in Python (FastAPI). No JS/TS backend code should be added here.

## API Endpoints

- `GET /health` - service health check
- `POST /video/preview-script` - generate narration script preview without video rendering; supports `custom_tickers`
- `POST /video/generate` - generate full market video and return download URL + metadata; supports `custom_tickers`
- `GET /video/download/{filename}` - download generated MP4
- `GET /video/history` - list recent generation runs
- `GET /video/run/{run_id}` - run detail and replay metadata
- `POST /video/cleanup` - trigger cleanup policy manually
