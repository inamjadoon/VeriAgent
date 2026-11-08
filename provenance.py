"""Provenance: SHA-256 hashes and run records in runs/<id>/record.json."""
import hashlib
import json
import os

RUNS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_dir(run_id: str) -> str:
    d = os.path.join(RUNS_DIR, run_id)
    os.makedirs(d, exist_ok=True)
    return d


def save_record(record: dict) -> str:
    path = os.path.join(run_dir(record["id"]), "record.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)
    return path


def load_record(run_id: str) -> dict | None:
    path = os.path.join(RUNS_DIR, run_id, "record.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)
