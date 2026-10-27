#!/usr/bin/env python3
"""Generate native Capella XHTML documentation for the static demonstrator."""
import argparse
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile

from prepare_export import prepare_export

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', type=Path, default=ROOT / 'demonstrator/capella-model')
    args = parser.parse_args()
    model = args.model.resolve()
    for suffix in ('capella', 'aird', 'afm'):
        if not (model / f'FischertechnikFactory.{suffix}').is_file():
            parser.error(f'Missing FischertechnikFactory.{suffix} in {model}')
    architecture = 'aarch64' if platform.machine().lower() in ('arm64', 'aarch64') else 'x86_64'
    image = f'zorro-capella-export:7.0.1-{architecture}'
    subprocess.run([
        'docker', 'build', '-t', image,
        '--build-arg', f'CAPELLA_URL=https://download.eclipse.org/capella/core/products/releases/7.0.1/capella-7.0.1.202503211540-linux-gtk-{architecture}.tar.gz',
        str(ROOT / 'tools/capella'),
    ], check=True)
    with tempfile.TemporaryDirectory(prefix='zorro-capella-') as temporary:
        subprocess.run([
            'docker', 'run', '--rm',
            '--mount', f'type=bind,source={model},target=/model,readonly',
            '--mount', f'type=bind,source={temporary},target=/output', image,
        ], check=True)
        source = Path(temporary)
        if not list(source.rglob('*.html')) or not list(source.rglob('*.png')):
            raise RuntimeError('Export is incomplete: expected HTML pages and diagram images')
        prepare_export(source, model)
        destination = ROOT / 'demonstrator/capella-export'
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination)
        print(f'Native Capella documentation generated in {destination}')


if __name__ == '__main__':
    main()
