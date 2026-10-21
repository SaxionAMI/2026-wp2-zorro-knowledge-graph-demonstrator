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


# -----------------------------
for i, line in enumerate(trouble_data, start=1):

    problem = zorroDemo[f"problem{i:03d}"]
    cause = zorroDemo[f"cause{i:03d}"]
    solution = zorroDemo[f"solution{i:03d}"]
    involved_assembly = zorroDemo[line['INVLOVED_PART'].strip().replace(
        " ", "_")]

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


for line in process_flow_data:
    assembly = zorroDemo[urllib.parse.quote(line['STATION'].replace(" ", "_"))]
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
