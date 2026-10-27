"""Validate published Capella exports without requiring a local Capella install."""
import json
from pathlib import Path
import unittest
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1] / 'demonstrator'
EXPORT = ROOT / 'capella-export'


class CapellaExportTests(unittest.TestCase):
    def test_every_source_diagram_has_a_native_svg_and_documentation(self):
        source = ET.parse(ROOT / 'capella-model/FischertechnikFactory.aird')
        expected = {node.get('name') for node in source.iter('ownedRepresentationDescriptors')}
        diagrams = json.loads((EXPORT / 'diagrams.json').read_text())
        self.assertEqual(expected, {entry['name'] for entry in diagrams})
        for entry in diagrams:
            with self.subTest(diagram=entry['name']):
                svg = ET.parse(EXPORT / entry['svg']).getroot()
                self.assertEqual(svg.tag, '{http://www.w3.org/2000/svg}svg')
                self.assertGreater(float(svg.get('width')), 0)
                self.assertGreater(float(svg.get('height')), 0)
                # Native Sirius metadata distinguishes a Capella export from a redraw.
                self.assertIn('{http://www.eclipse.org/sirius/diagram/1.1.0}semanticRoot', svg.attrib)
                url = urlsplit(entry['documentation'])
                self.assertTrue((EXPORT / url.path).is_file())
                page = EXPORT / 'output/FischertechnikFactory' / (url.query + '.html')
                self.assertIn(f'id="{url.fragment}"', page.read_text())

    def test_github_pages_keeps_underscore_named_diagram_images(self):
        self.assertTrue((ROOT.parent / '.nojekyll').is_file())

    def test_oversized_diagrams_are_present_in_documentation(self):
        for page in (EXPORT / 'output/FischertechnikFactory').glob('*.html'):
            self.assertNotIn('image is missing', page.read_text(), str(page))
        for entry in json.loads((EXPORT / 'diagrams.json').read_text()):
            if entry['name'] not in ('LCBD_FactoryStructure', '[LFBD] Hierarchy'):
                continue
            url = urlsplit(entry['documentation'])
            page = EXPORT / 'output/FischertechnikFactory' / (url.query + '.html')
            self.assertTrue(unquote(entry['svg']) in unquote(page.read_text()), entry['name'])


if __name__ == '__main__':
    unittest.main()
