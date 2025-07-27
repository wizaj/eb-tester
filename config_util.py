#!/usr/bin/env python3
"""Utility functions for persisting simple user configuration (integration key, base URL).
Configuration is stored as JSON in ~/.ebanx_ptp_tester/config.json.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

CONFIG_DIR = Path.home() / ".ebanx_ptp_tester"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config() -> Dict[str, Any]:
    """Return stored config or an empty dict if file not found/corrupt."""
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return {}
    except (OSError, json.JSONDecodeError):
        # Corrupt or unreadable – start fresh
        return {}


def save_config(cfg: Dict[str, Any]) -> None:
    """Persist *cfg* to disk. Creates parent directory if needed."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2) 