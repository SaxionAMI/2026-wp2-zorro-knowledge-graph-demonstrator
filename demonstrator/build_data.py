"""Rebuild the browser graph: python demonstrator/build_data.py (requires rdflib)."""
import json
from pathlib import Path
from urllib.parse import unquote
from rdflib import Graph, Literal, RDF, RDFS, OWL

ROOT = Path(__file__).resolve().parent

def export_webvowl(ontology):
    """Export the supplied named classes and domain/range properties to VOWL JSON."""
    classes = sorted(ontology.subjects(RDF.type, OWL.Class), key=str)
    properties = sorted(set(ontology.subjects(RDF.type, OWL.ObjectProperty)) |
                        set(ontology.subjects(RDF.type, OWL.DatatypeProperty)), key=str)
    datatypes = sorted({r for p in properties for r in ontology.objects(p, RDFS.range)
                        if (p, RDF.type, OWL.DatatypeProperty) in ontology}, key=str)
    ids = {term: str(i) for i, term in enumerate(classes + datatypes + properties)}
    def attributes(term):
        return {'id': ids[term], 'iri': str(term), 'baseIri': str(term).rsplit('#', 1)[0],
                'label': {'IRI-based': str(term).rsplit('#', 1)[-1]}}
    result = {
        'header': {'languages': ['en'], 'iri': str(next(ontology.subjects(RDF.type, OWL.Ontology))),
                   'title': {'en': 'ZORRO demonstrator ontology'},
                   'description': {'en': 'Classes and properties from the supplied WP5 demonstrator ontology.'}},
        'namespace': [],
        'class': [{'id': ids[c], 'type': 'owl:Class'} for c in classes] +
                 [{'id': ids[d], 'type': 'rdfs:Datatype'} for d in datatypes],
        'classAttribute': [dict(attributes(c), instances=0) for c in classes + datatypes],
        'property': [], 'propertyAttribute': []}
    for prop in properties:
        datatype = (prop, RDF.type, OWL.DatatypeProperty) in ontology
        domain = ontology.value(prop, RDFS.domain)
        range_ = ontology.value(prop, RDFS.range)
        result['property'].append({'id': ids[prop], 'type': 'owl:datatypeProperty' if datatype else 'owl:objectProperty'})
        result['propertyAttribute'].append(dict(attributes(prop), domain=ids[domain], range=ids[range_],
                                                attributes=['datatype' if datatype else 'object']))
    directory = ROOT / 'webvowl' / 'data'
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'ontology.json').write_text(json.dumps(result, indent=2) + '\n')


def build():
    graph = Graph().parse(ROOT / 'WP5KG.ttl')
    ontology = Graph().parse(ROOT / 'Zorro_ontology.owl', format='xml')
    ontology.serialize(ROOT / 'ontology.ttl', format='turtle')
    export_webvowl(ontology)
    graph += ontology
    def label(term):
        return str(next(graph.objects(term, RDFS.label), unquote(str(term).rsplit('#', 1)[-1]).replace('_', ' ')))
    entities = sorted({t for s, p, o in graph for t in (s, o) if not isinstance(t, Literal)}, key=str)
    nodes = [{'id': str(t), 'label': label(t), 'group': next((label(c) for c in sorted(graph.objects(t, RDF.type), key=str)), 'Resource'),
              'properties': [{'predicate': label(p), 'value': str(o)} for p, o in sorted(graph.predicate_objects(t), key=lambda x: (str(x[0]), str(x[1]))) if isinstance(o, Literal)]} for t in entities]
    edges = [{'from': str(s), 'to': str(o), 'label': label(p), 'predicate': str(p)} for s, p, o in sorted(graph, key=lambda t: tuple(map(str, t))) if not isinstance(o, Literal)]
    (ROOT / 'graph-data.json').write_text(json.dumps({'nodes': nodes, 'edges': edges, 'triples': len(graph)}, indent=2) + '\n')

if __name__ == '__main__':
    build()
