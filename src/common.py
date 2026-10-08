from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_config(path: str | Path = "config.yaml") -> dict[str, Any]:
    import yaml
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def ensure_dirs(root: Path) -> None:
    for rel in [
        "data/raw_assays",
        "data/intermediate",
        "data/final",
        "checkpoints",
        "logs",
    ]:
        (root / rel).mkdir(parents=True, exist_ok=True)


def checkpoint_path(root: Path, step: str) -> Path:
    return root / "checkpoints" / f"CINTA-Chem_{step}.json"


def load_checkpoint(root: Path, step: str) -> dict:
    path = checkpoint_path(root, step)
    if path.exists():
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def save_checkpoint(root: Path, step: str, payload: dict) -> None:
    path = checkpoint_path(root, step)
    tmp = path.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
    tmp.replace(path)
