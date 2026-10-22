"""Check browser exports and query examples against the supplied research files."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

from rdflib import Graph, Literal, Namespace, RDF, RDFS, OWL

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


def test_queries_preserve_document_examples_with_updated_ids():
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
    # The deduplicated KG renumbered these resources; retain the original questions.
    supplied[0] = supplied[0].replace('demo:problem038', 'demo:problem018')
    supplied[4] = supplied[4].replace('demo:problem037', 'demo:problem017')
    supplied[7] = supplied[7].replace('demo:cause020', 'demo:cause016')
    for example, source, count in zip(examples, supplied, [2, 49, 1, 6, 1, 1, 49, 1]):
        text = (ROOT / example['file']).read_text()
        assert text == source
        assert len(list(graph.query(text))) == count


def test_webvowl_export_preserves_relationships():
    graph = Graph().parse(ROOT / 'ZorroOntology.owl', format='xml')
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


def test_viewer_excludes_extension_properties():
    export = json.loads((ROOT / 'webvowl/data/ontology.json').read_text())
    declared = {p['iri'] for p in export['propertyAttribute'] if 'iri' in p}
    extension = Graph().parse(ROOT / 'ZorroDemo.owl', format='xml')
    extension_properties = {str(p) for kind in (OWL.ObjectProperty, OWL.DatatypeProperty)
                            for p in extension.subjects(RDF.type, kind)}
    assert declared.isdisjoint(extension_properties)


def test_demo_view_resolves_imported_upper_ontology():
    graph = ontology()
    export = json.loads((ROOT / 'webvowl/data/demo.json').read_text())
    expected = {str(p) for kind in (OWL.ObjectProperty, OWL.DatatypeProperty)
                for p in graph.subjects(RDF.type, kind)}
    assert {p['iri'] for p in export['propertyAttribute'] if 'iri' in p} == expected

    nodes = {item['id']: item['iri'] for item in export['classAttribute']}
    attributes = {item['id']: item for item in export['propertyAttribute']}
    subclass_edges = {(nodes[attributes[p['id']]['domain']], nodes[attributes[p['id']]['range']])
                      for p in export['property'] if p['type'] == 'rdfs:SubClassOf'}
    assert ('http://w3id.org/ZorroOntology/Assembly',
            'http://w3id.org/ZorroOntology/Component') in subclass_edges
    by_iri = {item['iri']: item for item in export['propertyAttribute'] if 'iri' in item}
    has_cause = by_iri['http://w3id.org/ZorroOntology/hasCause']
    assert nodes[has_cause['domain']] == 'http://w3id.org/ZorroOntology/Problem'
    assert nodes[has_cause['range']] == 'http://w3id.org/ZorroOntology/Cause'


def test_renumbered_examples_keep_original_problem_and_cause_meaning():
    graph = Graph().parse(ROOT / 'WP5KG.ttl')
    demo = Namespace('http://www.semanticweb.org/ontologies/2026/ZorroDemo/')
    assert str(graph.value(demo.problem018, RDFS.label)) == 'Warehouse HBW fails to pick up carrier from rack'
    assert str(graph.value(demo.problem017, RDFS.label)) == 'Warehouse HBW picks wrong workpiece from storage'
    assert str(graph.value(demo.cause016, RDFS.label)) == 'Incorrect warehouse reference position'
    causes = list(graph.query((ROOT / 'queries/01-problem-causes.rq').read_text()))
    assert {str(row.label) for row in causes} == {
        'Warehouse positioning miscalibration', 'Loose mechanical components in drive system'}
    assemblies = list(graph.query((ROOT / 'queries/05-problem-assembly.rq').read_text()))
    assert {str(row.assembly) for row in assemblies} == {str(demo['Warehouse_%28HBW%29'])}
    solutions = list(graph.query((ROOT / 'queries/08-cause-solutions.rq').read_text()))
    assert {str(row.solutionLabel) for row in solutions} == {'Verify and reset reference switches'}
