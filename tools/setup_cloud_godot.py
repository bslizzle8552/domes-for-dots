#!/usr/bin/env python3
"""Install pinned Godot into an ephemeral Linux CI worker, never a visitor device."""
from pathlib import Path
import hashlib
import os
import platform
import urllib.request
import zipfile

VERSION = '4.5.1-stable'
BASE = f'https://github.com/godotengine/godot-builds/releases/download/{VERSION}/'


def main():
    if platform.system() != 'Linux' or platform.machine() not in {'x86_64', 'AMD64'}:
        raise SystemExit('This bootstrap is only for ephemeral Linux x86_64 cloud workers.')
    target = Path('.tools/cloud-godot').resolve()
    target.mkdir(parents=True, exist_ok=True)
    checksums = urllib.request.urlopen(BASE + 'SHA512-SUMS.txt', timeout=60).read().decode()
    sums = {line.split()[1].lstrip('*'): line.split()[0] for line in checksums.splitlines() if line.strip()}
    def download(name):
        dest = target / name
        urllib.request.urlretrieve(BASE + name, dest)
        actual = hashlib.sha512(dest.read_bytes()).hexdigest()
        if actual != sums.get(name):
            raise ValueError('Upstream SHA512 mismatch: ' + name)
        return dest
    editor_name = f'Godot_v{VERSION}_linux.x86_64'
    editor = download(editor_name + '.zip')
    with zipfile.ZipFile(editor) as archive:
        (target / editor_name).write_bytes(archive.read(editor_name))
    (target / editor_name).chmod(0o755)
    templates = download(f'Godot_v{VERSION}_export_templates.tpz')
    template_dir = Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share'))) / 'godot/export_templates/4.5.1.stable'
    template_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(templates) as archive:
        for name in ['web_release.zip', 'web_debug.zip', 'version.txt']:
            (template_dir / name).write_bytes(archive.read('templates/' + name))
    print(str(target / editor_name))


if __name__ == '__main__':
    main()
