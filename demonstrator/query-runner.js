window.ZorroQueryRunner = ({getEngine, sources}) => {
  const $ = id => document.getElementById(id);
  let csv = '';
  const status = (message, error = false) => { $('status').textContent = message; $('status').className = error ? 'error' : ''; };
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
      const result = await getEngine().query($('query').value, {sources});
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
        const {data} = await getEngine().resultToString(result, 'text/turtle');
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
  $('download').onclick = () => {
    const url = URL.createObjectURL(new Blob([csv], {type: 'text/csv;charset=utf-8'}));
    const link = document.createElement('a'); link.href = url; link.download = 'zorro-results.csv'; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  return {status};
};
