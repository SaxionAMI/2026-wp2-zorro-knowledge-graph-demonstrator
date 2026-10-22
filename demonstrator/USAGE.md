# Running the demonstrator

From the repository root, run:

```sh
python3 -m http.server 8000
```

Open http://localhost:8000/demonstrator/ (the repository root also redirects there).
The default page opens the SPARQL queries. Navigation also provides the knowledge graph
and ontology viewer, plus a Demonstrator tab with component and installation context.
The static pages can also be served by GitHub Pages from the repository root.
Internet access is needed for the Comunica query engine and vis-network graph library.
Open the pages through HTTP rather than directly as local files.

- **Demonstrator:** module and part descriptions, supplied equipment images, manual page
  references. Distinguishes the local
  Turck/CODESYS setup from the standard manual.
- **SPARQL queries:** eight examples extracted from `Example_query2.docx`, editable queries,
  SELECT tables with CSV downloads, ASK results, and CONSTRUCT/DESCRIBE output as Turtle.
  Examples are read-only until **Try it yourself** is selected. Resetting or selecting
  another example restores read-only mode. Ctrl/Cmd+Enter runs a query. Resource links open that resource in the graph explorer.
  Each example also shows an equipment image and explanation with a link to its
  overview section. This context describes the selected example, including after
  editing (an edit notice is shown); it does not interpret arbitrary query results.
- **Query builder:** choices come directly from `WP5KG.ttl`. Select a type or item,
  add incoming/outgoing relationships, optionally choose values, and run the generated
  SPARQL. Rows match together; use an earlier result in the From selector to follow
  a chain (for example warehouse → parts → specifications). Manual editing is optional;
  returning to the builder restores the query from its selections. No extra plugin,
  server or ontology inference is required.
- **Ontology:** switch between standard ZORRO (`ZorroOntology.owl`) and Demo Extension
  (`ZorroDemo.owl`) in WebVOWL. Full screen and the OWL download follow the selected
  view. Demo Extension includes the ZORRO definitions imported by `ZorroDemo.owl`,
  resolved using the local `ZorroOntology.owl`. There is no separate combined tab.
- **Knowledge graph:** every resource and resource relationship in `WP5KG.ttl` and
  the two updated OWL files; literal values appear in the resource details. Search and type
  filters include immediate neighbours to preserve context. Ontology/type links can
  be hidden. Resource details also list incoming relationships.

Queries read `WP5KG.ttl` directly; this supplied export already includes both ontologies.
The graph explorer uses `graph-data.json`; WebVOWL uses `webvowl/data/ontology.json`.
After replacing the graph or ontology sources, regenerate the browser exports:

```sh
python demonstrator/build_data.py
```

The build requires `rdflib`, already declared in `pyproject.toml`.
Validate the exports and example results with:

```sh
pytest tests/test_demonstrator.py
```

Source identifiers are preserved, including differently encoded equipment names;
no equivalence or fault-propagation inference is added. The aircraft playground,
ontology documentation and original research files remain available unchanged.

`KG_construction.py` is the researcher's original construction script, preserved as
supplied. It is not needed to serve the site. Reconstructing the research graph requires
its input CSV files (`processed_troubleshooting.csv`, `InputCSVfiles/parts_catalog.csv`,
`InputCSVfiles/process_flow.csv`) and dependencies; these CSVs were not supplied here.
The eight queries are based on `Example_query2.docx`. After KG deduplication,
the warehouse pickup, wrong-workpiece and reference-position examples were updated
to `problem018`, `problem017` and `cause016` respectively, preserving their original
meaning. Example 6 asks for
assemblies in Handling, rather than all assemblies. No reasoning or URI corrections
are applied; identifiers and relationship directions remain as supplied.

The `solves` domain URI typo was corrected in `ZorroOntology.owl` and `WP5KG.ttl`
to use `http://w3id.org/ZorroOntology/Solution`. The supplied extension
uses `demo:hasSolution`, while the graph and examples use `zorro:hasSolution`;
`PartOf` and `partOf` also differ in case. No equivalences or missing subclass
axioms are invented to reconcile these differences.
