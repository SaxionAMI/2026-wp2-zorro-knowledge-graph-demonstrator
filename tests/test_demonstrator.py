"""Check browser exports and query examples against the supplied research files."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

from rdflib import Graph, Literal, RDF, RDFS, OWL
from rdflib.compare import isomorphic

ROOT = Path(__file__).resolve().parents[1] / 'demonstrator'


def ontology():
    graph = Graph()
    for filename in ('ZorroOntology.owl', 'ZorroDemo.owl'):
        graph.parse(ROOT / filename, format='xml')
    return graph


def test_graph_export_includes_every_statement():
    graph = Graph().parse(ROOT / 'WP5KG.ttl') + ontology()
    export = json.loads((ROOT / 'graph-data.json').read_text())
    assert export['triples'] == len(graph)
    ids = {node['id'] for node in export['nodes']}
    expected = {(str(s), str(p), str(o)) for s, p, o in graph if not isinstance(o, Literal)}
    assert {(e['from'], e['predicate'], e['to']) for e in export['edges']} == expected
    assert all(s in ids and o in ids for s, _, o in expected)
    assert sum(len(n['properties']) for n in export['nodes']) + len(export['edges']) == len(graph)


def test_queries_match_researcher_document_and_return_results():
    with zipfile.ZipFile(ROOT / 'Example_query2.docx') as archive:
        doc = ET.fromstring(archive.read('word/document.xml'))
    ns = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    paragraphs = [''.join(t.text or '' for t in p.iter(ns + 't')).strip() for p in doc.iter(ns + 'p')]
    prefixes = '\n'.join(p for p in paragraphs if p.startswith('PREFIX'))
    supplied = []
    for i, p in enumerate(paragraphs):
        if p.lower().startswith('select '):
            end = i
            while '}' not in paragraphs[end]:
                end += 1
            supplied.append(prefixes + '\n\n' + '\n'.join(paragraphs[i:end + 1]) + '\n')
    graph = Graph().parse(ROOT / 'WP5KG.ttl')
    examples = json.loads((ROOT / 'examples.json').read_text())
    assert len(examples) == len(supplied) == 8
    for example, source, count in zip(examples, supplied, [1, 49, 1, 6, 1, 1, 49, 1]):
        text = (ROOT / example['file']).read_text()
        assert text == source
        assert len(list(graph.query(text))) == count


def test_browser_ontology_matches_supplied_ontologies():
    assert isomorphic(ontology(), Graph().parse(ROOT / 'ontology.ttl'))


def test_webvowl_export_preserves_relationships():
    graph = ontology()
    export = json.loads((ROOT / 'webvowl/data/ontology.json').read_text())
    ids = {item['id']: item['iri'] for item in export['classAttribute']}
    assert {str(c) for c in graph.subjects(RDF.type, OWL.Class)} <= set(ids.values())
    attributes = {p['id']: p for p in export['propertyAttribute']}
    kinds = {p['id']: p['type'] for p in export['property']}
    for kind, vowl in ((OWL.ObjectProperty, 'owl:objectProperty'), (OWL.DatatypeProperty, 'owl:datatypeProperty')):
        expected = {(str(p), str(graph.value(p, RDFS.domain)), str(graph.value(p, RDFS.range))) for p in graph.subjects(RDF.type, kind)}
        actual = {(p['iri'], ids[p['domain']], ids[p['range']]) for p in attributes.values() if kinds[p['id']] == vowl}
        assert actual == expected
    for predicate, kind in ((RDFS.subClassOf, 'rdfs:SubClassOf'), (OWL.disjointWith, 'owl:disjointWith')):
        assert {(ids[p['domain']], ids[p['range']]) for p in attributes.values() if kinds[p['id']] == kind} == {
            (str(s), str(o)) for s, o in graph.subject_objects(predicate)}


def test_switchable_ontology_exports_use_only_selected_sources():
    for filename, source in (('zorro', 'ZorroOntology.owl'), ('demo', 'ZorroDemo.owl')):
        graph = Graph().parse(ROOT / source, format='xml')
        export = json.loads((ROOT / f'webvowl/data/{filename}.json').read_text())
        actual = {p['iri'] for p in export['propertyAttribute'] if 'iri' in p}
        expected = {str(p) for kind in (OWL.ObjectProperty, OWL.DatatypeProperty)
                    for p in graph.subjects(RDF.type, kind)}
        assert actual == expected
