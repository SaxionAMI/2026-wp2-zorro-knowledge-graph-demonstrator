"""Index native exports and repair the XHTML raster-limit placeholders."""
import html
import json
from pathlib import Path
import re
from urllib.parse import quote
import xml.etree.ElementTree as ET


def prepare_export(folder: Path, model: Path):
    aird = ET.parse(model / 'FischertechnikFactory.aird').getroot()
    svg_directory = folder / 'native-svg/FischertechnikFactory/FischertechnikFactory.aird'
    entries = []
    for descriptor in aird.iter('ownedRepresentationDescriptors'):
        name = descriptor.get('name')
        svg = svg_directory / (name + '.svg')
        if not svg.is_file():
            raise RuntimeError(f'Native SVG missing for {name}')
        ET.parse(svg)
        uid = descriptor.get('repPath').lstrip('#')
        target_id = descriptor.find('target').get('href').split('#')[-1].replace('-', '')
        page = folder / f'output/FischertechnikFactory/{target_id}.html'
        source = page.read_text()
        # Docgen emits this placeholder when native raster dimensions exceed SWT limits.
        pattern = r'(<p class="diagram-name" id="' + re.escape(uid) + r'">[^<]*</p>\s*)<p>image is missing</p>'
        relative_svg = '../../' + quote(svg.relative_to(folder).as_posix())
        replacement = f'<p class="diagram"><a href="{relative_svg}" target="_blank"><img src="{relative_svg}" alt="{html.escape(name, quote=True)}" /></a></p>'
        source = re.sub(pattern, lambda match: match.group(1) + replacement, source, flags=re.S)
        page.write_text(source)
        entries.append({
            'name': name,
            'svg': svg.relative_to(folder).as_posix(),
            'documentation': f'output/FischertechnikFactory/index.html?{target_id}#{uid}',
        })
    if len(entries) != len(list(svg_directory.glob('*.svg'))):
        raise RuntimeError('Mismatch between named diagrams and SVG exports')
    (folder / 'diagrams.json').write_text(json.dumps(entries, indent=2) + '\n')
    return entries
