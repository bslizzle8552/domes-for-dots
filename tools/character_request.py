#!/usr/bin/env python3
"""Bounded data-only transport for an operator's approved character request.

pack(interview_path, reference_root) -> JSON-ready request (at most 48 KiB).
unpack(request, fresh_output_dir) -> approved interview.json in that directory.
dispatch(request, repository=..., ref=..., workflow=...) -> submission receipt.

This adapter validates the current procedural producer's approved interview.
Only the operator/CI environment needs Python or GITHUB_TOKEN. This is not a
public upload service. Requests cannot select a repository, workflow, or code.
The GitHub input name is request_json; bind it to DOMES_CHARACTER_REQUEST
as a workflow environment variable, never interpolate it into shell source.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid

from character_factory import derive_spec, validate_schema

MAX_REQUEST_BYTES = 48 * 1024
MAX_REFERENCE_BYTES = MAX_REQUEST_BYTES * 3 // 4
GITHUB_API_VERSION = "2026-03-10"
RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL"} | {f"{prefix}{n}" for prefix in ("COM", "LPT") for n in range(1, 10)}


def encode(request: dict) -> bytes:
    """Canonical bounded wire encoding; NaN and recursion are rejected."""
    try:
        data = json.dumps(request, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, RecursionError, UnicodeError) as error:
        raise ValueError("request must be finite JSON data") from error
    if len(data) > MAX_REQUEST_BYTES:
        raise ValueError("request exceeds the 48 KiB transport limit")
    return data


def _no_links(path: Path) -> Path:
    absolute = path.absolute()
    for candidate in (absolute, *absolute.parents):
        if candidate.is_symlink() or (candidate.exists() and getattr(candidate.lstat(), "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)):
            raise ValueError("symlinks and reparse points are not request paths")
    return absolute.resolve()


def _reference_name(value: str) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= 240:
        raise ValueError("invalid reference path")
    parts = value.split("/")
    if len(parts) > 8 or any(not re.fullmatch(r"[A-Za-z0-9_-][A-Za-z0-9_.-]{0,159}", part) or part.endswith(".") or part.split(".")[0].upper() in RESERVED_NAMES for part in parts):
        raise ValueError("reference path must be a portable relative image filename")
    if Path(value).suffix.lower() not in {".png", ".jpg", ".jpeg"}:
        raise ValueError("only PNG/JPEG reference files are transported")
    return value


def _declared(interview: dict) -> list[str]:
    validate_schema("character-interview", interview)
    names = [_reference_name(item["path"]) for item in interview["references"]]
    folded = [name.casefold() for name in names]
    if len(set(folded)) != len(folded) or any(other.startswith(name + "/") for name in folded for other in folded if name != other):
        raise ValueError("duplicate or conflicting reference paths")
    return names


def pack(interview_path: Path, reference_root: Path) -> dict:
    source = _no_links(Path(interview_path))
    root = _no_links(Path(reference_root))
    if not source.is_file() or source.stat().st_size > MAX_REQUEST_BYTES or not root.is_dir():
        raise ValueError("interview or reference directory is unavailable or oversized")
    interview = json.loads(source.read_text(encoding="utf-8"))
    names = _declared(interview)
    blobs = []
    for name in names:
        path = _no_links(root / name)
        if not path.is_relative_to(root) or not path.is_file() or not 0 < path.stat().st_size <= MAX_REFERENCE_BYTES:
            raise ValueError("reference is missing, outside the upload directory, or oversized")
        raw = path.read_bytes()
        blobs.append({"path": name, "sha256": hashlib.sha256(raw).hexdigest(), "bytes_base64": base64.b64encode(raw).decode("ascii")})
    derive_spec(interview, root)
    request = {"schema_version": 1, "interview": interview, "references": blobs}
    encode(request)
    return request


def _validate(request: dict) -> tuple[dict, list[tuple[str, bytes]]]:
    encode(request)
    if not isinstance(request, dict) or set(request) != {"schema_version", "interview", "references"} or type(request["schema_version"]) is not int or request["schema_version"] != 1:
        raise ValueError("invalid request envelope")
    names = _declared(request["interview"])
    blobs = request["references"]
    if not isinstance(blobs, list) or len(blobs) != len(names):
        raise ValueError("request must contain exactly the declared references")
    decoded = []
    seen = set()
    for item in blobs:
        if not isinstance(item, dict) or set(item) != {"path", "sha256", "bytes_base64"}:
            raise ValueError("invalid reference envelope")
        name = _reference_name(item["path"])
        if name not in names or name in seen:
            raise ValueError("undeclared or duplicate reference")
        seen.add(name)
        if not isinstance(item["sha256"], str) or not re.fullmatch(r"[a-f0-9]{64}", item["sha256"]) or not isinstance(item["bytes_base64"], str):
            raise ValueError("invalid reference encoding or digest")
        try:
            raw = base64.b64decode(item["bytes_base64"], validate=True)
        except (ValueError, UnicodeError) as error:
            raise ValueError("reference is not strict base64") from error
        if not 0 < len(raw) <= MAX_REFERENCE_BYTES or hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise ValueError("reference size or SHA256 mismatch")
        decoded.append((name, raw))
    return request["interview"], decoded


def unpack(request: dict, output_dir: Path) -> Path:
    interview, blobs = _validate(request)
    destination = _no_links(Path(output_dir))
    if destination.exists():
        raise FileExistsError("request output already exists; use a fresh directory")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.parent / (".request-" + uuid.uuid4().hex)
    temporary.mkdir()
    try:
        for name, raw in blobs:
            path = temporary / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        derive_spec(interview, temporary)
        (temporary / "interview.json").write_text(json.dumps(interview, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        temporary.rename(destination)
    finally:
        if temporary.exists():
            resolved = temporary.resolve()
            if resolved.parent != destination.parent or not resolved.name.startswith(".request-") or temporary.is_symlink():
                raise ValueError("refusing cleanup outside the request staging directory")
            shutil.rmtree(resolved)
    return destination / "interview.json"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def dispatch(request: dict, *, repository: str, ref: str, workflow: str = "character-factory.yml") -> dict:
    """Submit with the operator's Actions-write token; acceptance is not completion.

    Config arguments must come from the operator, never from request contents.
    API contract: https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event
    """
    if not isinstance(repository, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}/[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", repository) or ".." in repository:
        raise ValueError("repository must be an operator-configured owner/repo")
    if not isinstance(ref, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_./-]{0,254}", ref) or ".." in ref or "//" in ref or ref.endswith(("/", ".")) or any(part.endswith(".lock") or part.startswith(".") for part in ref.split("/")):
        raise ValueError("ref must be an operator-configured branch or tag")
    if not isinstance(workflow, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}\.ya?ml", workflow) or ".." in workflow:
        raise ValueError("workflow must be an operator-configured YAML filename")
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token or len(token) > 2048 or any(character.isspace() for character in token):
        raise ValueError("GITHUB_TOKEN must be configured in the operator environment")
    wire = encode(request)
    with tempfile.TemporaryDirectory(prefix="domes-dispatch-") as directory:
        unpack(request, Path(directory) / "request")
    url = f"https://api.github.com/repos/{repository}/actions/workflows/{urllib.parse.quote(workflow)}/dispatches"
    payload = json.dumps({"ref": ref, "inputs": {"request_json": wire.decode("utf-8")}}, separators=(",", ":")).encode("utf-8")
    call = urllib.request.Request(url, data=payload, method="POST", headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json", "Content-Type": "application/json", "X-GitHub-Api-Version": GITHUB_API_VERSION, "User-Agent": "Domes-character-worker"})
    try:
        with urllib.request.build_opener(_NoRedirect()).open(call, timeout=30) as response:
            status = response.status
            body = response.read(8193)
    except urllib.error.HTTPError as error:
        raise ValueError(f"GitHub dispatch rejected (HTTP {error.code})") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ValueError("GitHub dispatch transport failed; submission outcome is unknown") from None
    receipt = {"status": "accepted", "repository": repository, "ref": ref, "workflow": workflow, "request_sha256": hashlib.sha256(wire).hexdigest(), "workflow_run_id": None, "html_url": None}
    if status == 204:
        return receipt
    if status != 200 or len(body) > 8192:
        raise ValueError("GitHub dispatch returned an unexpected response; submission outcome is unknown")
    try:
        result = json.loads(body)
        run_id = result["workflow_run_id"]
        if type(run_id) is not int or run_id <= 0 or result["html_url"] != f"https://github.com/{repository}/actions/runs/{run_id}":
            raise ValueError()
    except (ValueError, TypeError, KeyError, UnicodeError):
        raise ValueError("GitHub dispatch response lacked a valid run receipt; submission outcome is unknown") from None
    receipt.update(workflow_run_id=run_id, html_url=result["html_url"])
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-env", default="DOMES_CHARACTER_REQUEST")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--default-interview", type=Path)
    parser.add_argument("--reference-root", type=Path)
    args = parser.parse_args()
    try:
        if not re.fullmatch(r"[A-Z_][A-Z0-9_]{0,127}", args.from_env):
            raise ValueError("invalid request environment variable")
        incoming = os.environ.get(args.from_env, "")
        if incoming.strip():
            if len(incoming.encode("utf-8")) > MAX_REQUEST_BYTES:
                raise ValueError("request exceeds the 48 KiB transport limit")
            request = json.loads(incoming)
        elif args.default_interview:
            request = pack(args.default_interview, args.reference_root or args.default_interview.parent)
        else:
            raise ValueError("request is absent and no approved default interview was configured")
        path = unpack(request, args.output_dir)
        print(json.dumps({"status": "unpacked", "interview": str(path)}))
        return 0
    except (ValueError, OSError, RecursionError, UnicodeError):
        print("Character request rejected; no request contents or credentials were logged.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
