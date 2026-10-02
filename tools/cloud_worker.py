#!/usr/bin/env python3
"""Operator/cloud entrypoint: approved interview -> isolated character/world -> Web.

GitHub Actions supplies job identity, queueing, logs, durable status and artifacts.
This module deliberately contains no public unauthenticated job or upload API.
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
import subprocess
import sys

from build import WEB_README, find_godot, run, sha256

ROOT = Path(__file__).resolve().parents[1]


def atomic_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix('.partial')
    temporary.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def execute(interview_path: Path, reference_root: Path, job_dir: Path,
            world_id: str = 'cedar_atelier', godot_bin: str | None = None,
            export_web: bool = True) -> dict:
    # Never treat an existing output as a new job or overwrite an earlier proof.
    from character_factory import derive_spec, generate_package, validate_package, install_package
    job_dir = job_dir.resolve()
    job_dir.mkdir(parents=True, exist_ok=False)
    logs = job_dir / 'logs'
    logs.mkdir()
    receipt = {
        'schema_version': 1, 'status': 'running', 'phase': 'specification',
        'started_at_utc': datetime.now(timezone.utc).isoformat(),
        'interview_sha256': None, 'world_id': world_id,
        'provider': 'github_actions' if os.environ.get('GITHUB_ACTIONS') == 'true' else 'developer_worker',
        'run_id': os.environ.get('GITHUB_RUN_ID'),
        'source_commit': os.environ.get('GITHUB_SHA'), 'events': [],
        'deployment': {'status': 'not_deployed', 'url': None},
    }
    def phase(name: str) -> None:
        receipt['phase'] = name
        receipt['events'].append({'phase': name, 'at_utc': datetime.now(timezone.utc).isoformat()})
        atomic_json(job_dir / 'job.json', receipt)
    try:
        phase('specification')
        receipt['interview_sha256'] = sha256(interview_path)
        interview = json.loads(interview_path.read_text(encoding='utf-8'))
        spec = derive_spec(interview, reference_root)
        atomic_json(job_dir / 'spec.json', spec)
        phase('production')
        package = job_dir / 'package'
        generate_package(spec, package)
        phase('validation')
        receipt['package_validation'] = validate_package(package)
        if receipt['package_validation'].get('ok') is not True:
            raise ValueError('Generated character package failed validation')
        phase('world_install')
        stage = job_dir / 'stage'
        receipt['installation'] = install_package(package, ROOT, stage, world_id)
        # The factory returns a new isolated project; never changes source worlds.
        godot = find_godot(godot_bin, ROOT)
        version = run([str(godot), '--version'], 'engine_version', ROOT, logs).strip()
        if not re.fullmatch(r'4\.5\.1\.stable(?:\.official)?(?:\.[A-Za-z0-9]+)?', version):
            raise ValueError('Worker requires pinned Godot 4.5.1 Standard stable')
        base = [str(godot), '--headless', '--path', str(stage / 'godot')]
        phase('engine_import')
        run([*base, '--editor', '--import'], 'import', ROOT, logs)
        phase('engine_audit')
        audit_path = job_dir / 'engine-audit.json'
        run([*base, '--script', 'res://tools/audit_characters.gd', '--', '--output', str(audit_path)], 'audit', ROOT, logs)
        audit = json.loads(audit_path.read_text(encoding='utf-8'))
        generated_id = receipt['installation']['character_id']
        if (audit.get('ok') is not True or not audit.get('characters')
                or not all(character.get('ok') is True for character in audit['characters'])
                or not any(character.get('character_id') == generated_id for character in audit['characters'])):
            raise ValueError('Engine audit must pass and include the generated character')
        receipt['engine_audit'] = audit
        phase('animation_acceptance')
        motion = run([*base, '--script', 'res://tests/test_factory_character.gd', '--',
                      '--character', f'res://content/characters/{generated_id}.json'],
                     'animation_tests', ROOT, logs)
        if not re.search(r'FACTORY CHARACTER TESTS:\s*\d+ passed,\s*0 failed', motion):
            raise ValueError('Generated animation tests did not report success')
        receipt['animation_tests'] = 'passed'
        if export_web:
            phase('web_export')
            web = job_dir / 'web'
            web.mkdir()
            run([*base, '--export-release', 'Web', str(web / 'index.html')], 'web_export', ROOT, logs)
            for name in ['index.html', 'index.js', 'index.wasm', 'index.pck']:
                if not (web / name).is_file() or not (web / name).stat().st_size:
                    raise ValueError('Missing Web export: ' + name)
            (web / 'docs').mkdir()
            shutil.copy2(ROOT / 'LICENSE', web / 'LICENSE')
            for name in ['GODOT_LICENSE.txt', 'GODOT_COPYRIGHT.txt', 'THIRD_PARTY_NOTICES.md']:
                shutil.copy2(ROOT / 'docs' / name, web / 'docs' / name)
            (web / 'README.txt').write_text(WEB_README, encoding='utf-8')
            shutil.copy2(ROOT / 'cloud/vercel.json', web / 'vercel.json')
            (web / '.nojekyll').touch()
            # Artifact downloads are for contributors, never required by visitors.
            shutil.copytree(package, web / 'character-package')
            receipt['web_sha256'] = {p.relative_to(web).as_posix(): sha256(p) for p in sorted(web.rglob('*')) if p.is_file()}
        receipt['status'] = 'succeeded'
        phase('complete')
        return receipt
    except Exception as error:
        receipt['status'] = 'failed'
        receipt['error'] = f'{type(error).__name__}: {error}'
        atomic_json(job_dir / 'job.json', receipt)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--interview', type=Path, required=True)
    parser.add_argument('--reference-root', type=Path)
    parser.add_argument('--job-dir', type=Path, required=True)
    parser.add_argument('--world-id', default='cedar_atelier')
    parser.add_argument('--godot')
    parser.add_argument('--no-web', action='store_true')
    args = parser.parse_args()
    try:
        receipt = execute(args.interview, args.reference_root or args.interview.parent,
                          args.job_dir, args.world_id, args.godot, not args.no_web)
        print(json.dumps({'status': receipt['status'], 'job': str(args.job_dir / 'job.json')}))
        return 0
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(f'Cloud worker failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
