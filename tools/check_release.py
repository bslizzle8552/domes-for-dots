#!/usr/bin/env python3
"""Conservative release hygiene checks; never print matched secret values."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import re
from pathlib import Path, PurePosixPath
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_DIRECTORIES = {".git", ".godot", ".tools", ".venv", "dist", "artifacts", "node_modules", "__pycache__", ".pytest_cache", ".agent-browser"}
FORBIDDEN_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".log", ".tmp", ".bak", ".pyc"}
SECRET_RULES = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b"),
    "AWS access key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "OpenAI-style key": re.compile(r"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}\b"),
    "Slack token": re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{20,}\b"),
    "credential assignment": re.compile(r'''(?i)["']?(?:api_key|access_token|refresh_token|password|client_secret)["']?\s*[:=]\s*["'](?!redacted|example|replace|your_|fixture|dummy|test_)[A-Za-z0-9_+/.=-]{20,}["']'''),
}
PRIVATE_PATH = re.compile(r"(?i)(?:\b[A-Z]:[\\/]Users[\\/](?!Public(?:[\\/]|\b)|Default(?:[\\/]|\b))[^\s\"'<>]+|/(?:Users|home)/[A-Za-z0-9_.-]+/[^\s\"'<>]*)")
PROVENANCE_PATH_EXCEPTIONS = {"prototype/Dot_World_Preview.html", "prototype/Dot_World_Starter_Kit.md", "prototype/README.md", "docs/THIRD_PARTY_NOTICES.md"}
REQUIRED = {"README.md", "LICENSE", "CHANGELOG.md", "BUILD_STATUS.md", "godot/project.godot", "godot/export_presets.cfg", "godot/content/catalog.json", "docs/GODOT_LICENSE.txt", "docs/GODOT_COPYRIGHT.txt", "docs/THIRD_PARTY_NOTICES.md"}


@dataclass(frozen=True)
class Issue:
    path: str
    message: str
    line: int = 0

    def __str__(self) -> str:
        return f"{self.path}{':' + str(self.line) if self.line else ''}: {self.message}"


def git(root: Path, *args: str) -> bytes:
    result = subprocess.run(["git", "-C", str(root), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode:
        raise ValueError("Git failed: " + result.stderr.decode("utf-8", "replace").strip())
    return result.stdout


def tracked_files(root: Path, include_untracked: bool = False) -> list[str]:
    args = ["ls-files", "--cached", "-z"]
    if include_untracked:
        args += ["--others", "--exclude-standard"]
    return sorted(set(value.decode("utf-8") for value in git(root, *args).split(b"\0") if value))


def inspect_file(root: Path, relative: str) -> list[Issue]:
    logical = PurePosixPath(relative)
    if logical.is_absolute() or ".." in logical.parts:
        return [Issue(relative, "unsafe archive path")]
    path = root / relative
    if path.is_symlink():
        return [Issue(relative, "symlinks are not accepted in a release archive")]
    if not path.resolve().is_relative_to(root.resolve()):
        return [Issue(relative, "resolved path escapes repository")]
    if not path.is_file():
        return [Issue(relative, "tracked file is missing or not a regular file")]
    issues = []
    if any(part in FORBIDDEN_DIRECTORIES for part in logical.parts):
        issues.append(Issue(relative, "generated/private directory must not be tracked"))
    name = logical.name.lower()
    if (logical.suffix.lower() in FORBIDDEN_SUFFIXES or name in {".env", ".export_credentials", "export_credentials.cfg", "id_rsa", "id_ed25519"}
            or (name.startswith(".env.") and name != ".env.example") or name.endswith(".save.json")):
        issues.append(Issue(relative, "credential, local-state, cache or temporary filename"))
    if path.stat().st_size > 50 * 1024 * 1024:
        return issues + [Issue(relative, "source file exceeds 50 MiB; review binary/toolchain inclusion")]
    content = path.read_bytes()
    if b"\x00" in content:
        return issues
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return issues
    for number, line in enumerate(text.splitlines(), 1):
        for label, pattern in SECRET_RULES.items():
            if pattern.search(line):
                issues.append(Issue(relative, f"possible {label}; matched value withheld", number))
        if relative not in PROVENANCE_PATH_EXCEPTIONS and PRIVATE_PATH.search(line):
            issues.append(Issue(relative, "private absolute home-directory path", number))
    return issues


def scan(root: Path, include_untracked: bool = False, require_complete: bool = True) -> tuple[list[str], list[Issue]]:
    files = tracked_files(root, include_untracked)
    issues = []
    if require_complete:
        for relative in sorted(REQUIRED - set(files)):
            issues.append(Issue(relative, "required release file is not included in Git candidates"))
    for relative in files:
        issues.extend(inspect_file(root, relative))
    return files, issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--include-untracked", action="store_true", help="also inspect nonignored candidates before staging; final packaging always uses tracked files")
    args = parser.parse_args()
    try:
        files, issues = scan(args.root.resolve(), args.include_untracked)
    except (ValueError, OSError, UnicodeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    if issues:
        print(f"FAIL: {len(issues)} hygiene issue(s) in {len(files)} candidate files")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    print(f"PASS: {len(files)} {'tracked/nonignored candidate' if args.include_untracked else 'tracked'} files checked for obvious secrets, private paths and accidental artifacts")
    print("This heuristic scan is a release check, not a guarantee that every possible secret format is recognized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
