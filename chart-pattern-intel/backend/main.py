"""Chart Pattern Intelligence FastAPI entrypoint (port 8002)."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.backtest import router as backtest_router
from routes.chart import router as chart_router
from routes.patterns import router as patterns_router


def create_app() -> FastAPI:
	app = FastAPI(title="Chart Pattern Intelligence", version="0.1.0")

	app.add_middleware(
		CORSMiddleware,
		allow_origins=["*"],
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)

	app.include_router(patterns_router)
	app.include_router(backtest_router)
	app.include_router(chart_router)

	@app.get("/health")
	def health() -> dict:
		return {"status": "ok"}

	return app


app = create_app()
