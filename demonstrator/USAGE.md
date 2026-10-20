# Running the demonstrator

From the repository root, run:

```sh
python3 -m http.server 8000
```

Open http://localhost:8000/demonstrator/ (the repository root also redirects there).
The static pages can also be served by GitHub Pages from the repository root.
Internet access is needed for the Comunica query engine and vis-network graph library.
Open the pages through HTTP rather than directly as local files.

- **Overview:** explains the manufacturing use case and displays counts from the supplied data.
- **SPARQL queries:** eight examples extracted from `Example_query.docx`, editable queries,
  SELECT tables with CSV downloads, ASK results, and CONSTRUCT/DESCRIBE output as Turtle.
  Ctrl/Cmd+Enter runs a query. Resource links open that resource in the graph explorer.
- **Knowledge graph:** every resource and resource relationship in `WP5KG.ttl` and
  `Zorro_ontology.owl`; literal values appear in the resource details. Search and type
  filters include immediate neighbours to preserve context. Ontology/type links can
  be hidden. Resource details also list incoming relationships.

Queries read `WP5KG.ttl` and `ontology.ttl` directly. The latter is a generated Turtle
copy of the supplied OWL file to avoid HTTP servers treating `.owl` as binary data.
The explorer and overview use `graph-data.json`. After changing either research file,
regenerate both browser exports with the project's Python environment:

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
