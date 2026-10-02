#!/usr/bin/env python3
"""Operator-only, first-publication GitHub Pages proof for a synthetic demo.

Verifies a succeeded cloud job's exact Web hashes, creates a fresh isolated
branch without force, and requests Pages publication. It does not poll or claim
browser acceptance. Requires --public-demo and existing operator Git credentials.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "codex/hosted-character-proof"
API_VERSION = "2026-03-10"
FORBIDDEN = {".git", ".gitmodules", ".gitattributes", ".gitconfig", ".git-credentials", ".lfsconfig"}


def _git_environment() -> dict[str, str]:
    # Inherited checkout overrides must never redirect writes into the source tree.
    blocked = {"GIT_DIR", "GIT_COMMON_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT"}
    env = {key: value for key, value in os.environ.items() if key not in blocked and not key.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_"))}
    return {**env, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "Never"}


def _plain(path: Path) -> Path:
    absolute = Path(path).absolute()
    for part in (absolute, *absolute.parents):
        if part.is_symlink() or (part.exists() and getattr(part.lstat(), "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)):
            raise ValueError("publication paths cannot contain links or reparse points")
    return absolute.resolve()


def _sha(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def verify_web(web: Path, job_receipt: Path) -> tuple[dict, dict[str, str], str]:
    web, receipt_path = _plain(web), _plain(job_receipt)
    if not web.is_dir() or not receipt_path.is_file() or receipt_path.stat().st_size > 10 * 1024 * 1024:
        raise ValueError("Web directory or bounded job receipt is unavailable")
    raw = receipt_path.read_bytes()
    job = json.loads(raw)
    if not isinstance(job, dict) or job.get("status") != "succeeded":
        raise ValueError("only a succeeded job may be published")
    expected = job.get("web_sha256")
    if not isinstance(expected, dict) or not expected or any(not isinstance(name, str) or not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value) for name, value in expected.items()):
        raise ValueError("job receipt lacks a valid Web hash inventory")
    actual = {}
    for directory, subdirs, names in os.walk(web, followlinks=False):
        for name in subdirs + names:
            path = Path(directory) / name
            if name.casefold() in FORBIDDEN:
                raise ValueError("Git metadata cannot be part of a static publication")
            _plain(path)
        for name in names:
            path = Path(directory) / name
            if not path.is_file():
                raise ValueError("Web outputs must be regular files")
            actual[path.relative_to(web).as_posix()] = _sha(path)
    if actual != expected or "index.html" not in actual:
        raise ValueError("Web files differ from the job inventory: missing, extra or modified files")
    return job, actual, hashlib.sha256(raw).hexdigest()


def _git(args: list[str], cwd: Path, allowed: tuple[int, ...] = (0,)) -> tuple[int, bytes]:
    try:
        process = subprocess.run(["git", *args], cwd=cwd, env=_git_environment(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise ValueError("Git operation failed or timed out; inspect the preserved publication checkout") from None
    if process.returncode not in allowed:
        raise ValueError(f"Git {args[0]} failed (exit {process.returncode}); publication checkout preserved")
    return process.returncode, process.stdout


def _token() -> str:
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        try:
            result = subprocess.run(["git", "credential", "fill"], input=b"protocol=https\nhost=github.com\n\n", cwd=ROOT, env=_git_environment(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=False)
        except (OSError, subprocess.TimeoutExpired):
            raise ValueError("operator API credentials are unavailable") from None
        if result.returncode == 0:
            values = dict(line.split("=", 1) for line in result.stdout.decode("utf-8", "replace").splitlines() if "=" in line)
            token = values.get("password", "")
    if not token or len(token) > 4096 or any(character.isspace() for character in token):
        raise ValueError("operator GITHUB_TOKEN or Git credential helper is required")
    return token


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def _pages(repository: str, token: str, create: bool = False) -> dict | None:
    # https://docs.github.com/en/rest/pages/pages#create-a-github-pages-site
    payload = {"build_type": "legacy", "source": {"branch": BRANCH, "path": "/"}}
    request = urllib.request.Request(f"https://api.github.com/repos/{repository}/pages", method="POST" if create else "GET", data=json.dumps(payload).encode() if create else None, headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json", "Content-Type": "application/json", "X-GitHub-Api-Version": API_VERSION, "User-Agent": "Domes-proof-publisher"})
    try:
        with urllib.request.build_opener(_NoRedirect()).open(request, timeout=30) as response:
            raw = response.read(65537)
            if response.status != (201 if create else 200) or len(raw) > 65536:
                raise ValueError("unexpected Pages API response")
    except urllib.error.HTTPError as error:
        if error.code == 404 and not create:
            return None
        raise ValueError(f"Pages API rejected the operation (HTTP {error.code}); no access settings were changed by this helper") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ValueError("Pages API transport failed; publication outcome is unknown") from None
    result = json.loads(raw)
    if not isinstance(result, dict):
        raise ValueError("invalid Pages API response")
    return result


def _matching_source(site: dict) -> bool:
    return site.get("source") == {"branch": BRANCH, "path": "/"} and site.get("build_type", "legacy") == "legacy"


def _save(path: Path, value: dict) -> None:
    temporary = path.with_suffix(".partial")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def publish(web: Path, job_receipt: Path, repository: str, checkout: Path, *, public_demo: bool = False) -> dict:
    if public_demo is not True:
        raise ValueError("--public-demo is required to acknowledge publication of the synthetic demo")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}/[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", repository) or ".." in repository:
        raise ValueError("repository must be owner/repo")
    job, hashes, job_hash = verify_web(web, job_receipt)
    web, checkout = _plain(web), _plain(checkout)
    artifacts = _plain(ROOT / "artifacts")
    if checkout == artifacts or not checkout.is_relative_to(artifacts) or checkout.exists() or checkout.is_relative_to(web) or web.is_relative_to(checkout):
        raise ValueError("checkout must be a fresh child of this project's ignored artifacts directory, separate from the Web output")
    receipt_path = checkout.with_name(checkout.name + ".publication.json")
    if receipt_path.exists():
        raise FileExistsError("publication receipt already exists; use a fresh checkout name")
    token = _token()
    site = _pages(repository, token)
    if site is not None and not _matching_source(site):
        raise ValueError("repository already has a different Pages source; it will not be reconfigured")
    remote = f"https://github.com/{repository}.git"
    code, _ = _git(["ls-remote", "--exit-code", "--heads", remote, "refs/heads/" + BRANCH], ROOT, (0, 2))
    if code == 0:
        raise ValueError("proof branch already exists; first-publication helper refuses to overwrite it")
    checkout.parent.mkdir(parents=True, exist_ok=True)
    receipt = {"schema_version": 1, "status": "preparing", "repository": repository, "branch": BRANCH, "started_at_utc": datetime.now(timezone.utc).isoformat(), "job_receipt_sha256": job_hash, "job_run_id": job.get("run_id"), "source_commit": job.get("source_commit"), "web_sha256": hashes, "commit": None, "html_url": None, "branch_pushed": False, "browser_verified": False}
    _save(receipt_path, receipt)
    try:
        checkout.mkdir()
        _git(["init", "--initial-branch=" + BRANCH, "--template="], checkout)
        for key, value in [("user.name", "Domes Cloud Publisher"), ("user.email", "domes-publisher@users.noreply.github.com"), ("core.autocrlf", "false"), ("core.hooksPath", str(checkout / ".git/no-hooks")), ("commit.gpgsign", "false")]:
            _git(["config", key, value], checkout)
        _git(["remote", "add", "origin", remote], checkout)
        for name in sorted(hashes):
            destination = checkout / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(web / name, destination)
        _git(["add", "--force", "--all", "--", "."], checkout)
        _git(["commit", "-m", "Publish verified synthetic Domes character proof"], checkout)
        _, commit_bytes = _git(["rev-parse", "HEAD"], checkout)
        commit = commit_bytes.decode("ascii").strip()
        if not re.fullmatch(r"[a-f0-9]{40,64}", commit):
            raise ValueError("Git did not return a valid publication commit")
        _, names = _git(["ls-files", "-z"], checkout)
        if set(names.decode("utf-8").rstrip("\0").split("\0")) != set(hashes):
            raise ValueError("publication commit file inventory differs from verified Web output")
        for name, expected in hashes.items():
            _, blob = _git(["cat-file", "blob", "HEAD:" + name], checkout)
            if hashlib.sha256(blob).hexdigest() != expected:
                raise ValueError("publication commit changed a verified Web file")
        receipt["commit"] = commit
        receipt["status"] = "verified_commit"
        _save(receipt_path, receipt)
        _git(["push", "--set-upstream", "origin", "HEAD:refs/heads/" + BRANCH], checkout)
        receipt["branch_pushed"] = True
        receipt["status"] = "source_pushed"
        _save(receipt_path, receipt)
        if site is None:
            site = _pages(repository, token, create=True)
        if not isinstance(site, dict) or not _matching_source(site):
            raise ValueError("Pages did not confirm the intended source; inspect the separate receipt")
        url = site.get("html_url")
        parsed = urllib.parse.urlsplit(url) if isinstance(url, str) else None
        if parsed is None or parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Pages did not return a usable HTTPS publication URL")
        receipt.update(status="submitted", html_url=url, server_status=site.get("status"), submitted_at_utc=datetime.now(timezone.utc).isoformat())
        _save(receipt_path, receipt)
        return receipt
    except Exception as error:
        receipt["status"] = "failed"
        receipt["error_type"] = type(error).__name__
        _save(receipt_path, receipt)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--web", type=Path, required=True)
    parser.add_argument("--job-receipt", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--public-demo", action="store_true")
    args = parser.parse_args()
    try:
        result = publish(args.web, args.job_receipt, args.repository, args.checkout, public_demo=args.public_demo)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, subprocess.SubprocessError):
        print("Publication failed; inspect the separate publication receipt when present. Credentials and response bodies were not logged.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
