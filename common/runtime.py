from __future__ import annotations

import os

DEFAULT_HOME_CATALOG_URL = "http://localhost:8000"


def get_home_catalog_url() -> str:
    return os.getenv("HOME_CATALOG_URL", DEFAULT_HOME_CATALOG_URL)
