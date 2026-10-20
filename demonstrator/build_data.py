"""Rebuild the browser graph: python demonstrator/build_data.py (requires rdflib)."""
import json
from pathlib import Path
from urllib.parse import unquote
from rdflib import Graph, Literal, RDF, RDFS

ROOT = Path(__file__).resolve().parent

def build():
    graph = Graph().parse(ROOT / 'WP5KG.ttl')
    ontology = Graph().parse(ROOT / 'Zorro_ontology.owl', format='xml')
    ontology.serialize(ROOT / 'ontology.ttl', format='turtle')
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
