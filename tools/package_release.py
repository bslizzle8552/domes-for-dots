#!/usr/bin/env python3
"""Package verified local artifacts. This tool never publishes or contacts GitHub."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import zipfile

from build import GODOT_TEST_SUITES, GODOT_VERSION, VERSION, runtime_hashes, sha256
from check_release import ROOT, git, scan


def write_zip(destination: Path, root: Path, files: list[str], prefix: str = "", extra: dict[str, bytes] | None = None) -> None:
    temporary = destination.with_suffix(".zip.tmp")
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for relative in sorted(files):
                info = zipfile.ZipInfo(prefix + relative, date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (0o100644 << 16)
                archive.writestr(info, (root / relative).read_bytes())
            for relative, content in sorted((extra or {}).items()):
                info = zipfile.ZipInfo(prefix + relative, date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (0o100644 << 16)
                archive.writestr(info, content)
        with zipfile.ZipFile(temporary) as archive:
            if bad := archive.testzip():
                raise ValueError(f"Archive CRC verification failed: {bad}")
        temporary.replace(destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def verify_web(root: Path) -> tuple[Path, dict, list[str]]:
    web = root / "dist/web"
    path = web / "build_manifest.json"
    if not path.is_file():
        raise ValueError("Missing verified dist/web/build_manifest.json; run tools/build.py first")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("version") != VERSION or not manifest.get("godot_version", "").startswith(GODOT_VERSION + ".stable"):
        raise ValueError("Web artifact version/Godot pin mismatch")
    if manifest.get("validation") != "passed" or manifest.get("python_tests") != "passed" or manifest.get("character_audit") != "passed" or manifest.get("godot_tests") != {name: "passed" for name in GODOT_TEST_SUITES}:
        raise ValueError("Web build has not passed every required validation/test suite")
    if manifest.get("runtime_source_sha256") != runtime_hashes(root):
        raise ValueError("Runtime source differs from the verified Web build; rebuild before packaging")
    expected = manifest.get("files", {})
    if not expected:
        raise ValueError("Web build manifest contains no file inventory")
    required = {"index.html", "index.js", "index.wasm", "index.pck", "LICENSE", "README.txt", "docs/GODOT_LICENSE.txt", "docs/GODOT_COPYRIGHT.txt", "docs/THIRD_PARTY_NOTICES.md"}
    if not required.issubset(expected):
        raise ValueError("Web build is missing required runtime files or license notices")
    for relative, digest in expected.items():
        target = web / relative
        if not target.resolve().is_relative_to(web.resolve()) or not target.is_file() or target.is_symlink() or sha256(target) != digest:
            raise ValueError(f"Web file integrity mismatch: {relative}")
    files = sorted(path.relative_to(web).as_posix() for path in web.rglob("*") if path.is_file())
    if set(files) != set(expected) | {"build_manifest.json"}:
        raise ValueError("Unexpected files in dist/web; rebuild into a clean export")
    return web, manifest, files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-dirty", action="store_true", help="explicitly permit a candidate package from modified tracked files; never adds untracked source")
    args = parser.parse_args()
    root = ROOT.resolve()
    try:
        dirty = bool(git(root, "status", "--porcelain", "--untracked-files=no").strip())
        if dirty and not args.allow_dirty:
            raise ValueError("Tracked files are dirty/staged. Commit the final source first, or explicitly use --allow-dirty for a candidate.")
        files, issues = scan(root)
        if issues:
            raise ValueError("Release hygiene failed:\n" + "\n".join(str(issue) for issue in issues))
        web, build, web_files = verify_web(root)
        if not set(build["runtime_source_sha256"]).issubset(files):
            raise ValueError("The tested Web runtime contains untracked source. Add and commit it before packaging; source archives include tracked files only.")
        commit = git(root, "rev-parse", "HEAD").decode().strip()
        output = root / "dist/release"
        output.mkdir(parents=True, exist_ok=True)
        if not output.resolve().is_relative_to((root / "dist").resolve()):
            raise ValueError("Release output escapes project dist directory")
        prefix = f"domes-for-dots-v{VERSION}"
        source_zip = output / f"{prefix}-source.zip"
        web_zip = output / f"{prefix}-web.zip"
        receipt = dict(schema_version=1,version=VERSION,source_commit=commit,candidate=dirty or args.allow_dirty,
            packaged_at_utc=datetime.now(timezone.utc).isoformat(),godot_version=build["godot_version"],
            source_file_count=len(files),web_file_count=len(web_files),validation="passed",godot_tests=build["godot_tests"],
            source_files="Git tracked files only; runtime source matched the tested Web build")
        write_zip(source_zip, root, files, prefix + "/")
        write_zip(web_zip, web, web_files, extra={"release_manifest.json":(json.dumps(receipt,indent=2)+"\n").encode()})
        # A concurrent edit must not silently produce a final release package.
        if git(root, "rev-parse", "HEAD").decode().strip() != commit or (not args.allow_dirty and git(root,"status","--porcelain","--untracked-files=no").strip()):
            raise ValueError("Repository changed during packaging; generated archives are candidates, not release-approved")
        (output / "SHA256SUMS").write_text("".join(f"{sha256(path)}  {path.name}\n" for path in [source_zip,web_zip]),encoding="utf-8")
        (output / "release_manifest.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
        print(f"PASS: {'CANDIDATE' if receipt['candidate'] else 'RELEASE'} {VERSION}; {len(files)} tracked source files, {len(web_files)} Web files")
        for path in [source_zip,web_zip,output/"SHA256SUMS"]:
            print(path.relative_to(root))
        return 0
    except (ValueError,OSError,json.JSONDecodeError) as error:
        print(f"FAIL: {error}",file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
