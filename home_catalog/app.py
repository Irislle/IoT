from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "home_catalog.json"

app = FastAPI(title="Home Catalog", version="1.0.0")


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing config file: {CONFIG_PATH}")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/mqtt")
def mqtt_config() -> dict:
    return _load_config()["mqtt"]


@app.get("/config/{service_name}")
def service_config(service_name: str) -> dict:
    config = _load_config().get("services", {})
    if service_name not in config:
        raise HTTPException(status_code=404, detail="service not registered")
    return config[service_name]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("home_catalog.app:app", host="0.0.0.0", port=8000, reload=False)
