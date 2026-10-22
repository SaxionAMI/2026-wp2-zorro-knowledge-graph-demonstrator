import csv
import rdflib
import urllib.parse
import os
import re
import pandas as pd
from rdflib import Literal, XSD, RDF, RDFS, BNode
from pyoxigraph import Store, Triple, NamedNode, Literal as PyLiteral, Quad

# -----------------------------
# Setup rdflib graph (normal RDF)
# -----------------------------
g = rdflib.Graph()
zorroDemo = rdflib.Namespace(
    "http://www.semanticweb.org/ontologies/2026/ZorroDemo/")
Zorro = rdflib.Namespace("http://w3id.org/ZorroOntology/")
g.bind("demo", zorroDemo)
g.bind("zorro", Zorro)

g.parse("ZorroOntology.owl", format="xml")
g.parse("ZorroDemo.owl", format="xml")


# -----------------------------
# Input CSVs
# -----------------------------
trouble_file = "processed_troubleshooting.csv"
catalog_file = "InputCSVfiles/parts_catalog.csv"
process_flow_file = "InputCSVfiles/process_flow.csv"


trouble_data = csv.DictReader(open(trouble_file, encoding='utf-8'))
catalog_data = csv.DictReader(open(catalog_file, encoding='utf-8'))
process_flow_data = csv.DictReader(open(process_flow_file, encoding='utf-8'))


known_assemblies = set()
for line in process_flow_data:
    assembly = zorroDemo[urllib.parse.quote(line['STATION'].replace(" ", "_"))]
    known_assemblies.add(assembly)
    function = zorroDemo[urllib.parse.quote(
        line['FUNCTION'].replace(" ", "_"))]
    partTypes = line['MAIN PARTS INVOLVED'].split("+")
    function_description = line["DESCRIPTION"].strip()

    triples = [
        (assembly, rdflib.RDF.type, Zorro.Assembly),
        (function, rdflib.RDF.type, Zorro.Function),
        (assembly, Zorro.hasFunction, function),
        (function, zorroDemo.hasFunctionDescription, Literal(function_description)),
    ]

    for part_name in partTypes:
        part_name = part_name.strip()
        partType = zorroDemo[urllib.parse.quote(part_name.replace(" ", "_"))]
        triples.extend([
            (partType, rdflib.RDF.type, zorroDemo.PartType),
            (function, zorroDemo.partTypeInvolvedInFunc, partType),
        ])

    for triple in triples:
        g.add(triple)


problem_map = {}
cause_map = {}
solution_map = {}

for line in trouble_data:
    problem = line['TROUBLE'].strip()
    cause = line['PROBABLE CAUSE'].strip()
    solution = line['REMEDY'].strip()
    if problem not in problem_map:
        problem_id = f"problem{len(problem_map) + 1:03d}"
        problem_map[problem] = zorroDemo[problem_id]
    problem = problem_map[problem]

    if cause not in cause_map:
        cause_id = f"cause{len(cause_map) + 1:03d}"
        cause_map[cause] = zorroDemo[cause_id]
    cause = cause_map[cause]

    if solution not in solution_map:
        solution_id = f"solution{len(solution_map) + 1:03d}"
        solution_map[solution] = zorroDemo[solution_id]
    solution = solution_map[solution]

    def make_uri(text, namespace=zorroDemo):
        clean_text = text.strip().replace(" ", "_")
        return namespace[urllib.parse.quote(clean_text)]

    involved_assembly = make_uri(line['INVLOVED_PART'])

    if involved_assembly not in known_assemblies:
        g.add((involved_assembly, rdflib.RDF.type, Zorro.Assembly))
        known_assemblies.add(involved_assembly)

    triples = [
        (problem, rdflib.RDF.type, Zorro.Problem),
        (cause, rdflib.RDF.type, Zorro.Cause),
        (solution, rdflib.RDF.type, Zorro.Solution),

        (problem, rdflib.RDFS.label, Literal(line['TROUBLE'].strip())),
        (cause, rdflib.RDFS.label, Literal(line['PROBABLE CAUSE'].strip())),
        (solution, rdflib.RDFS.label, Literal(line['REMEDY'].strip())),

        (problem, Zorro.hasCause, cause),
        (involved_assembly, Zorro.failsVia, problem),
        (cause, Zorro.hasSolution, solution),
    ]

    for t in triples:
        g.add(t)


for line in catalog_data:
    subSystem = zorroDemo[urllib.parse.quote(
        line['Section'].replace(" ", "_"))]
    assembly = zorroDemo[urllib.parse.quote(line['Figure'].replace(" ", "_"))]
    part = zorroDemo[urllib.parse.quote(line['Part Number'].replace(" ", "_"))]
    partType = zorroDemo[urllib.parse.quote(line['Type'].replace(" ", "_"))]
    specification = zorroDemo[urllib.parse.quote(
        line['Specifics'].replace(" ", "_"))]

    triples = [
        (subSystem, rdflib.RDF.type, Zorro.SubSystem),
        (assembly, rdflib.RDF.type, Zorro.Assembly),
        (part, rdflib.RDF.type, Zorro.Part),
        (partType, rdflib.RDF.type, zorroDemo.PartType),
        (specification, rdflib.RDF.type, zorroDemo.PartSpecification),

        (assembly, zorroDemo.inSubsystem, subSystem),
        (part, Zorro.partOf, assembly),
        (part, zorroDemo.hasPartType, partType),
        (part, zorroDemo.hasPartSpecification, specification),

    ]

    for t in triples:
        g.add(t)


g.serialize("WP5KG.ttl", format="turtle")
