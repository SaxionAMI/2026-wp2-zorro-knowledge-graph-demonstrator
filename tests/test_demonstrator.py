"""Ensure the browser export and supplied examples stay aligned with research data."""
import json
from pathlib import Path

from rdflib import Graph, Literal, RDF, RDFS, OWL
from rdflib.compare import isomorphic

ROOT = Path(__file__).resolve().parents[1] / 'demonstrator'


def test_graph_export_includes_every_statement():
    graph = Graph().parse(ROOT / 'WP5KG.ttl')
    graph.parse(ROOT / 'Zorro_ontology.owl', format='xml')
    export = json.loads((ROOT / 'graph-data.json').read_text())
    assert export['triples'] == len(graph)
    ids = {node['id'] for node in export['nodes']}
    expected_edges = {(str(s), str(p), str(o)) for s, p, o in graph if not isinstance(o, Literal)}
    assert {(e['from'], e['predicate'], e['to']) for e in export['edges']} == expected_edges
    assert all(s in ids and o in ids for s, _, o in expected_edges)
    assert sum(len(n['properties']) for n in export['nodes']) + len(export['edges']) == len(graph)


def test_supplied_query_examples_return_expected_results():
    graph = Graph().parse(ROOT / 'WP5KG.ttl')
    graph.parse(ROOT / 'Zorro_ontology.owl', format='xml')
    examples = json.loads((ROOT / 'examples.json').read_text())
    assert len(examples) == 8
    for example, count in zip(examples, [1, 49, 1, 6, 1, 8, 49, 1]):
        assert len(list(graph.query((ROOT / example['file']).read_text()))) == count


def test_browser_ontology_matches_original():
    assert isomorphic(
        Graph().parse(ROOT / "Zorro_ontology.owl", format="xml"),
        Graph().parse(ROOT / "ontology.ttl"),
    )


def test_webvowl_export_matches_supplied_schema():
    ontology = Graph().parse(ROOT / 'Zorro_ontology.owl', format='xml')
    export = json.loads((ROOT / 'webvowl/data/ontology.json').read_text())
    ids = {item['id']: item['iri'] for item in export['classAttribute']}
    classes = {item['id'] for item in export['class'] if item['type'] == 'owl:Class'}
    assert {ids[id_] for id_ in classes} == {str(c) for c in ontology.subjects(RDF.type, OWL.Class)}
    expected = {(str(p), str(ontology.value(p, RDFS.domain)), str(ontology.value(p, RDFS.range)))
                for kind in (OWL.ObjectProperty, OWL.DatatypeProperty)
                for p in ontology.subjects(RDF.type, kind)}
    assert {(p['iri'], ids[p['domain']], ids[p['range']]) for p in export['propertyAttribute']} == expected
