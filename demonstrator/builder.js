(async () => {
  const $ = id => document.getElementById(id);
  let engine, triples = [], conditions = [], counter = 0, manual = false;
  const sources = [{type: 'file', value: new URL('WP5KG.ttl', location.href).href}];
  const {status} = ZorroQueryRunner({getEngine: () => engine, sources});
  const TYPE = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type';
  const LABEL = 'http://www.w3.org/2000/01/rdf-schema#label';
  const names = new Map(), terms = new Map();
  const key = term => JSON.stringify([term.termType, term.value, term.language || '', term.datatype?.value || '']);
  const unique = values => [...new Map(values.map(term => [key(term), term])).values()];
  function name(term) {
    if (term.termType === 'Literal') return term.value;
    if (names.has(term.value)) return names.get(term.value);
    let local = term.value.replace(/\/$/, '').split(/[#/]/).pop();
    try { local = decodeURIComponent(local); } catch {}
    return local.replaceAll('_', ' ');
  }
  function sparql(term) {
    if (term.termType === 'NamedNode') return '<' + term.value.replaceAll('>', '%3E') + '>';
    if (term.termType === 'Literal') {
      return JSON.stringify(term.value) + (term.language ? '@' + term.language :
        term.datatype ? '^^<' + term.datatype.value + '>' : '');
    }
    throw new Error('This value cannot be used as a fixed query filter.');
  }
  function option(value, text, title) {
    const item = document.createElement('option'); item.value = value; item.textContent = text;
    if (title) item.title = title; return item;
  }
  function fill(select, values, firstLabel, current = '') {
    select.replaceChildren(option('', firstLabel), ...values.map(term => option(key(term), name(term), term.value)));
    select.value = [...select.options].some(o => o.value === current) ? current : '';
  }
  const sort = values => values.sort((a, b) => name(a).localeCompare(name(b)) || a.value.localeCompare(b.value));
  function items() {
    const type = $('builder-type').value;
    return sort(unique(triples.filter(t => t.s.termType === 'NamedNode' &&
      (!type || (t.p.value === TYPE && key(t.o) === type))).map(t => t.s)));
  }
  function startingItems() {
    return $('builder-item').value ? [terms.get($('builder-item').value)] : items();
  }
  function matching(condition, scope) {
    if (!condition.relation) return [];
    const [direction, predicate] = JSON.parse(condition.relation);
    const keys = new Set(scope.map(key));
    return triples.filter(t => t.p.value === predicate && keys.has(key(direction === 'out' ? t.s : t.o)))
      .map(t => direction === 'out' ? t.o : t.s);
  }
  function refresh() {
    const pools = new Map([['item', startingItems()]]);
    conditions.forEach(condition => {
      if (!pools.has(condition.from)) condition.from = 'item';
      const scope = pools.get(condition.from), keys = new Set(scope.map(key));
      const relations = new Map();
      triples.forEach(t => {
        if (keys.has(key(t.s))) relations.set(JSON.stringify(['out', t.p.value]), '→ ' + name(t.p));
        if (keys.has(key(t.o))) relations.set(JSON.stringify(['in', t.p.value]), '← ' + name(t.p));
      });
      const row = condition.element;
      const from = row.querySelector('.condition-from');
      from.replaceChildren(...[...pools.keys()].map(value => option(value, value === 'item' ? 'Item' : 'Result ' + value.slice(5))));
      from.value = condition.from;
      const relation = row.querySelector('.condition-relation');
      relation.replaceChildren(option('', 'Select relationship'), ...[...relations].sort((a,b) => a[1].localeCompare(b[1])).map(([value, text]) => option(value, text, JSON.parse(value)[1])));
      if (!relations.has(condition.relation)) { condition.relation = ''; condition.target = ''; }
      relation.value = condition.relation;
      const targets = sort(unique(matching(condition, scope))).filter(t => t.termType !== 'BlankNode');
      const target = row.querySelector('.condition-target');
      fill(target, targets, 'Any value', condition.target); condition.target = target.value;
      target.disabled = !condition.relation;
      const output = condition.target ? [terms.get(condition.target)] : unique(matching(condition, scope));
      pools.set('value' + condition.id, output);
    });
    generate();
  }
  function generate() {
    const lines = [], variables = ['?item'];
    const type = $('builder-type').value, item = $('builder-item').value;
    if (type) lines.push('?item a ' + sparql(terms.get(type)) + ' .');
    if (item) lines.push('VALUES ?item { ' + sparql(terms.get(item)) + ' }');
    conditions.forEach(condition => {
      if (!condition.relation) return;
      const [direction, predicate] = JSON.parse(condition.relation);
      const from = '?' + condition.from, value = '?value' + condition.id;
      variables.push(value);
      lines.push(direction === 'out' ? `${from} <${predicate}> ${value} .` : `${value} <${predicate}> ${from} .`);
      if (condition.target) lines.push(`VALUES ${value} { ${sparql(terms.get(condition.target))} }`);
    });
    if (!type && !conditions.some(c => c.relation)) lines.push('?item ?property ?value .');
    $('query').value = `SELECT DISTINCT ${variables.join(' ')}\nWHERE {\n${lines.map(line => '  ' + line).join('\n')}\n}\nORDER BY ?item\nLIMIT ${$('builder-limit').value}`;
    $('results').replaceChildren(); $('download').disabled = true;
    const incomplete = conditions.some(c => !c.relation);
    $('run').disabled = incomplete;
    status(incomplete ? 'Select a relationship in each row, or remove unused rows.' : 'Ready. Run the query to see results.');
  }
  function addCondition() {
    const condition = {id: ++counter, from: 'item', relation: '', target: ''};
    const row = document.createElement('div'); row.className = 'condition-row';
    const number = document.createElement('span'); number.textContent = 'Result ' + condition.id;
    row.append(number);
    for (const [field, title] of [['from', 'From'], ['relation', 'Relationship'], ['target', 'Value']]) {
      const label = document.createElement('label'); label.append(document.createTextNode(title));
      const select = document.createElement('select'); select.className = 'condition-' + field;
      select.onchange = () => { condition[field] = select.value; refresh(); };
      label.append(select); row.append(label);
    }
    const remove = document.createElement('button'); remove.className = 'secondary'; remove.textContent = 'Remove';
    remove.setAttribute('aria-label', 'Remove result ' + condition.id);
    remove.onclick = () => { conditions = conditions.filter(c => c !== condition); row.remove(); refresh(); };
    row.append(remove); condition.element = row; conditions.push(condition); $('conditions').append(row); refresh();
  }
  $('add-condition').onclick = addCondition;
  $('builder-type').onchange = () => { fill($('builder-item'), items(), 'All items'); refresh(); };
  $('builder-item').onchange = refresh; $('builder-limit').onchange = generate;
  $('query').addEventListener('input', () => {
    $('results').replaceChildren(); $('download').disabled = true;
    status('Manual query edited. Run the query to see results.');
  });
  $('manual').onclick = () => {
    manual = !manual;
    $('query').readOnly = !manual; $('builder-controls').inert = manual;
    $('manual-note').hidden = !manual;
    $('manual').textContent = manual ? 'Return to builder' : 'Edit manually';
    $('manual').setAttribute('aria-pressed', String(manual));
    if (manual) { $('run').disabled = false; $('query').focus(); } else refresh();
  };
  try {
    if (!window.Comunica) throw new Error('Query engine unavailable. Check your connection and reload.');
    engine = new Comunica.QueryEngine();
    const stream = await engine.queryBindings('SELECT ?s ?p ?o WHERE { ?s ?p ?o }', {sources});
    const rows = await stream.toArray();
    triples = rows.map(row => ({s: row.get('s'), p: row.get('p'), o: row.get('o')}));
    triples.forEach(t => {
      [t.s, t.p, t.o].forEach(term => terms.set(key(term), term));
      if (t.p.value === LABEL && t.o.termType === 'Literal') names.set(t.s.value, t.o.value);
    });
    const types = sort(unique(triples.filter(t => t.p.value === TYPE && t.o.termType === 'NamedNode').map(t => t.o)));
    fill($('builder-type'), types, 'All types');
    const assembly = types.find(t => t.value === 'http://w3id.org/ZorroOntology/Assembly');
    if (assembly) $('builder-type').value = key(assembly);
    fill($('builder-item'), items(), 'All items');
    $('builder-type').disabled = false; $('builder-item').disabled = false;
    $('add-condition').disabled = false; $('manual').disabled = false; refresh();
  } catch (error) { status('Could not load knowledge graph: ' + error.message, true); }
})();
