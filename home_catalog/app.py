from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "home_catalog.json"
CONFIG_PATH = Path(
    os.getenv("HOME_CATALOG_CONFIG", str(DEFAULT_CONFIG_PATH))
).resolve()

app = FastAPI(title="Home Catalog", version="1.0.0")
_catalog_cache: dict | None = None


class ServiceRegistration(BaseModel):
    name: str = Field(..., min_length=1)
    config: dict


def _load_config() -> dict:
    global _catalog_cache
    if _catalog_cache is not None:
        return _catalog_cache
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing config file: {CONFIG_PATH}")
    _catalog_cache = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return _catalog_cache


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


@app.get("/services")
def list_services() -> dict:
    config = _load_config().get("services", {})
    return {"services": sorted(config.keys())}


@app.post("/register")
def register_service(registration: ServiceRegistration) -> dict:
    config = _load_config().setdefault("services", {})
    if registration.name in config:
        raise HTTPException(status_code=409, detail="service already registered")
    config[registration.name] = registration.config
    return {"status": "registered", "service": registration.name}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("home_catalog.app:app", host="0.0.0.0", port=8000, reload=False)
