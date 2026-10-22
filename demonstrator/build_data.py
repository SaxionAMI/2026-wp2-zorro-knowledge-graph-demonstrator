"""Build browser exports from the supplied research files without modifying them."""
import json
from pathlib import Path
from urllib.parse import unquote

from rdflib import Graph, Literal, RDF, RDFS, OWL

ROOT = Path(__file__).resolve().parent
ONTOLOGY_FILES = ('ZorroOntology.owl', 'ZorroDemo.owl')


def label(term):
    return unquote(str(term).rstrip('/').rsplit('#', 1)[-1].rsplit('/', 1)[-1]).replace('_', ' ')


def load_ontology():
    ontology = Graph()
    for filename in ONTOLOGY_FILES:
        ontology.parse(ROOT / filename, format='xml')
    return ontology


def export_webvowl(ontology, filename="ontology", title="ZORRO", iri="http://w3id.org/ZorroOntology/"):
    """Display declared properties, subclass and disjointness axioms as supplied."""
    properties = sorted(set(ontology.subjects(RDF.type, OWL.ObjectProperty)) |
                        set(ontology.subjects(RDF.type, OWL.DatatypeProperty)), key=str)
    datatypes = {r for p in properties if (p, RDF.type, OWL.DatatypeProperty) in ontology
                 for r in ontology.objects(p, RDFS.range)}
    classes = set(ontology.subjects(RDF.type, OWL.Class))
    for predicate in (RDFS.domain, RDFS.range):
        classes.update(ontology.objects(None, predicate))
    relations = []
    for predicate, kind in ((RDFS.subClassOf, 'rdfs:SubClassOf'), (OWL.disjointWith, 'owl:disjointWith')):
        for subject, obj in sorted(set(ontology.subject_objects(predicate)), key=lambda pair: tuple(map(str, pair))):
            classes.update((subject, obj))
            relations.append((subject, predicate, obj, kind))
    classes = sorted(classes - datatypes, key=str)
    datatypes = sorted(datatypes, key=str)
    ids = {term: str(i) for i, term in enumerate(classes + datatypes + properties)}

    def attributes(term):
        text = str(term)
        separator = '#' if '#' in text else '/'
        return {'id': ids[term], 'iri': text, 'baseIri': text.rsplit(separator, 1)[0],
                'label': {'IRI-based': label(term)}}

    result = {
        'header': {'languages': ['en'], 'iri': iri,
                   'title': {'en': title}},
        'namespace': [],
        'class': [{'id': ids[c], 'type': 'owl:Class'} for c in classes] +
                 [{'id': ids[d], 'type': 'rdfs:Datatype'} for d in datatypes],
        'classAttribute': [dict(attributes(c), instances=0) for c in classes + datatypes],
        'property': [], 'propertyAttribute': []}
    for prop in properties:
        datatype = (prop, RDF.type, OWL.DatatypeProperty) in ontology
        domain, range_ = ontology.value(prop, RDFS.domain), ontology.value(prop, RDFS.range)
        flags = ['datatype' if datatype else 'object']
        if (prop, RDF.type, OWL.TransitiveProperty) in ontology:
            flags.append('transitive')
        result['property'].append({'id': ids[prop], 'type': 'owl:datatypeProperty' if datatype else 'owl:objectProperty'})
        result['propertyAttribute'].append(dict(attributes(prop), domain=ids[domain], range=ids[range_], attributes=flags))
    for i, (subject, predicate, obj, kind) in enumerate(relations):
        id_ = f'axiom-{i}'
        result['property'].append({'id': id_, 'type': kind})
        result['propertyAttribute'].append({'id': id_, 'domain': ids[subject], 'range': ids[obj],
                                            'attributes': ['object', 'anonymous']})
    directory = ROOT / 'webvowl' / 'data'
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f'{filename}.json').write_text(json.dumps(result, indent=2) + '\n')


def build():
    ontology = load_ontology()
    export_webvowl(Graph().parse(ROOT / 'ZorroOntology.owl', format='xml'))
    # The extension imports ZORRO; resolve that import from the supplied local file.
    export_webvowl(ontology, 'demo', 'Demo Extension',
                   'http://www.semanticweb.org/ontologies/2026/ZorroDemo/')
    graph = Graph().parse(ROOT / 'WP5KG.ttl') + ontology

    def display_label(term):
        return str(next(graph.objects(term, RDFS.label), label(term)))

    entities = sorted({t for s, p, o in graph for t in (s, o) if not isinstance(t, Literal)}, key=str)
    nodes = [{'id': str(t), 'label': display_label(t),
              'group': next((label(c) for c in sorted(graph.objects(t, RDF.type), key=str)), 'Resource'),
              'properties': [{'predicate': display_label(p), 'value': str(o)}
                             for p, o in sorted(graph.predicate_objects(t), key=lambda x: tuple(map(str, x)))
                             if isinstance(o, Literal)]} for t in entities]
    edges = [{'from': str(s), 'to': str(o), 'label': display_label(p), 'predicate': str(p)}
             for s, p, o in sorted(graph, key=lambda t: tuple(map(str, t))) if not isinstance(o, Literal)]
    (ROOT / 'graph-data.json').write_text(json.dumps({'nodes': nodes, 'edges': edges, 'triples': len(graph)}, indent=2) + '\n')


if __name__ == '__main__':
    build()
