(async () => {
  const $ = id => document.getElementById(id);
  let original = '', engine;
  const sources = ['WP5KG.ttl'].map(path => ({type: 'file', value: new URL(path, location.href).href}));
  const {status} = ZorroQueryRunner({getEngine: () => engine, sources});
  async function fetchText(path) {
    const response = await fetch(path);
    if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
    return response.text();
  }
  function lockExample() {
    $('query').readOnly = true; $('edit').textContent = 'Try it yourself';
    $('edit').setAttribute('aria-pressed', 'false'); $('context-edited').hidden = true;
    $('results').replaceChildren(); $('download').disabled = true;
    status('Example loaded. Run the query to see results.');
  }
  $('edit').onclick = () => {
    if ($('query').readOnly) {
      $('query').readOnly = false; $('query').focus(); $('edit').textContent = 'Back to example';
      $('edit').setAttribute('aria-pressed', 'true');
    } else { $('query').value = original; lockExample(); }
  };
  $('reset').onclick = () => { $('query').value = original; lockExample(); };
  $('query').addEventListener('input', () => {
    $('context-edited').hidden = $('query').value === original;
    $('results').replaceChildren(); $('download').disabled = true;
    status('Query edited. Run the query to see results.');
  });
  try {
    if (!window.Comunica) throw new Error('The query engine could not load. Check your internet connection and reload.');
    engine = new Comunica.QueryEngine();
    const examples = JSON.parse(await fetchText('examples.json'));
    const texts = await Promise.all(examples.map(example => fetchText(example.file)));
    const buttons = examples.map((example, index) => {
      const button = document.createElement('button'); button.textContent = example.name;
      button.onclick = () => {
        original = texts[index]; $('query').value = original; lockExample();
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
    $('run').disabled = false; $('reset').disabled = false; $('edit').disabled = false;
  } catch (error) { $('examples').textContent = 'Examples unavailable.'; status(error.message, true); }
})();
