"""Shared JSON/schema and file-digest helpers; no producer assumptions."""
import hashlib
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from validate_content import read_json
ROOT = Path(__file__).resolve().parents[1]


def canonical(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, allow_nan=False)+"\n", encoding="utf-8", newline="\n")


def validate_schema(kind, data):
    schema = read_json(ROOT / "schemas" / (kind+".schema.json"))
    issues = list(Draft202012Validator(schema).iter_errors(data))
    # jsonschema's numeric checks alone are not a NaN guard.
    canonical(data)
    if issues:
        raise ValueError("; ".join(f"{'.'.join(map(str, item.path))}: {item.message}" for item in issues))
