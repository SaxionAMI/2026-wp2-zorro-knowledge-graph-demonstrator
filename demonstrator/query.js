(async () => {
  const $ = id => document.getElementById(id);
  let original = '', csv = '', engine;
  const sources = ['WP5KG.ttl'].map(path => ({type: 'file', value: new URL(path, location.href).href}));
  const status = (message, error = false) => { $('status').textContent = message; $('status').className = error ? 'error' : ''; };
  async function fetchText(path) {
    const response = await fetch(path);
    if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
    return response.text();
  }
  function termCell(term) {
    const cell = document.createElement('td');
    if (!term) return cell;
    if (term.termType === 'NamedNode') {
      const link = document.createElement('a');
      link.href = `graph.html?node=${encodeURIComponent(term.value)}`;
      link.textContent = decodeURIComponent(term.value.replace(/\/$/, '').split(/[#/]/).pop()).replaceAll('_', ' ');
      link.title = term.value; cell.append(link);
    } else cell.textContent = term.value;
    return cell;
  }
  $('run').onclick = async () => {
    $('run').disabled = true; $('download').disabled = true;
    $('results').replaceChildren(); csv = ''; status('Running query…');
    const start = performance.now();
    try {
      const result = await engine.query($('query').value, {sources});
      if (result.resultType === 'bindings') {
        const stream = await result.execute();
        const rows = await stream.toArray();
        const metadata = await result.metadata();
        const vars = metadata.variables.map(v => (v.variable || v).value);
        const table = document.createElement('table'), head = document.createElement('thead'), tr = document.createElement('tr');
        vars.forEach(v => { const th = document.createElement('th'); th.textContent = v; tr.append(th); });
        head.append(tr); table.append(head);
        const body = document.createElement('tbody');
        rows.forEach(row => { const tr = document.createElement('tr'); vars.forEach(v => tr.append(termCell(row.get(v)))); body.append(tr); });
        table.append(body); $('results').append(table);
        const quote = v => '"' + String(v).replaceAll('"', '""') + '"';
        csv = [vars, ...rows.map(row => vars.map(v => row.get(v)?.value ?? ''))].map(row => row.map(quote).join(',')).join('\r\n');
        $('download').disabled = false;
        status(`${rows.length} results · ${((performance.now() - start) / 1000).toFixed(2)} seconds`);
      } else if (result.resultType === 'boolean') {
        status(`ASK result: ${await result.execute()}`);
      } else if (result.resultType === 'quads') {
        const {data} = await engine.resultToString(result, 'text/turtle');
        const chunks = []; for await (const chunk of data) chunks.push(String(chunk));
        const pre = document.createElement('pre'); pre.textContent = chunks.join(''); $('results').append(pre);
        status('Graph query completed (Turtle).');
      } else throw new Error('Use SELECT, ASK, CONSTRUCT or DESCRIBE.');
    } catch (error) { status(`Query failed: ${error.message}`, true); }
    finally { $('run').disabled = false; }
  };
  $('query').addEventListener('keydown', event => {
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') { event.preventDefault(); if (!$('run').disabled) $('run').click(); }
  });
  $('reset').onclick = () => { $('query').value = original; $('context-edited').hidden = true; };
  $('query').addEventListener('input', () => { $('context-edited').hidden = $('query').value === original; });
  $('download').onclick = () => {
    const url = URL.createObjectURL(new Blob([csv], {type: 'text/csv;charset=utf-8'}));
    const link = document.createElement('a'); link.href = url; link.download = 'zorro-results.csv'; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  try {
    if (!window.Comunica) throw new Error('The query engine could not load. Check your internet connection and reload.');
    engine = new Comunica.QueryEngine();
    const examples = JSON.parse(await fetchText('examples.json'));
    const texts = await Promise.all(examples.map(example => fetchText(example.file)));
    const buttons = examples.map((example, index) => {
      const button = document.createElement('button'); button.textContent = example.name;
      button.onclick = () => {
        original = texts[index]; $('query').value = original;
        const context = example.context;
        $('context-content').replaceChildren();
        $('query-context').hidden = !context;
        $('context-edited').hidden = true;
        if (context) {
          const imageLink = document.createElement('a'); imageLink.href = context.overview;
          const image = document.createElement('img'); image.src = context.image; image.alt = context.alt;
          imageLink.append(image);
          const text = document.createElement('div');
          const title = document.createElement('h3'); title.textContent = context.title;
          const description = document.createElement('p'); description.textContent = context.description;
          const link = document.createElement('a'); link.href = context.overview; link.textContent = 'Component details →';
          text.append(title, description, link);
          $('context-content').append(imageLink, text);
        }
        buttons.forEach((item, i) => item.setAttribute('aria-pressed', String(i === index)));
        const url = new URL(location.href); url.searchParams.set('example', index); history.replaceState(null, '', url);
        $('results').replaceChildren(); $('download').disabled = true; status('Example loaded. Run the query to see results.');
      }; return button;
    });
    $('examples').replaceChildren(...buttons);
    const index = Number(new URLSearchParams(location.search).get('example') || 0);
    buttons[Number.isInteger(index) && index >= 0 && index < buttons.length ? index : 0].click();
    $('run').disabled = false; $('reset').disabled = false;
  } catch (error) { $('examples').textContent = 'Examples unavailable.'; status(error.message, true); }
})();
