(async () => {
  const $ = id => document.getElementById(id);
  try {
    if (!window.vis) throw new Error('Graph viewer could not load. Check your internet connection and reload.');
    const response = await fetch('graph-data.json');
    if (!response.ok) throw new Error(`Graph data: HTTP ${response.status}`);
    const data = await response.json();
    const byId = new Map(data.nodes.map(node => [node.id, node]));
    const palette = ['#167d8d','#d79040','#6c69ac','#bc667b','#258974','#78934a','#5482bb','#aa744e','#8a839b','#53766f','#9c7332'];
    const groups = [...new Set(data.nodes.map(node => node.group))].sort();
    const colors = Object.fromEntries(groups.map((group, i) => [group, palette[i % palette.length]]));
    groups.forEach(group => {
      const option = document.createElement('option'); option.value = group; option.textContent = group; $('type').append(option);
      const label = document.createElement('span'), swatch = document.createElement('span'); swatch.className = 'swatch'; swatch.style.background = colors[group]; label.append(swatch, document.createTextNode(group)); $('legend').append(label);
    });
    const network = new vis.Network($('network'), {}, {
      nodes: {shape: 'dot', size: 10, font: {size: 12, color: '#183a41'}, borderWidth: 1},
      edges: {arrows: 'to', color: {color: '#aabfbb', highlight: '#007e78'}, font: {size: 9, align: 'middle'}, smooth: {type: 'continuous'}},
      physics: {stabilization: {iterations: 180}, barnesHut: {gravitationalConstant: -4500}},
      interaction: {hideEdgesOnDrag: true, keyboard: {enabled: true, bindToWindow: false}},
      layout: {randomSeed: 42, improvedLayout: false}
    });
    let visibleIds = new Set();
    function render() {
      const search = $('search').value.toLowerCase().trim(), type = $('type').value;
      const schema = $('schema').checked;
      const edges = data.edges.filter(edge => schema || !/www\.w3\.org\//.test(edge.predicate));
      const matches = data.nodes.filter(node => (!type || node.group === type) && (!search || `${node.label} ${node.id}`.toLowerCase().includes(search)));
      visibleIds = new Set(matches.map(node => node.id));
      // Include immediate neighbours so a filtered resource keeps its relationship context.
      if (search || type) edges.forEach(edge => { if (matches.some(node => node.id === edge.from || node.id === edge.to)) { visibleIds.add(edge.from); visibleIds.add(edge.to); } });
      const shownEdges = edges.filter(edge => visibleIds.has(edge.from) && visibleIds.has(edge.to));
      if (!schema && !search && !type) visibleIds = new Set(shownEdges.flatMap(edge => [edge.from, edge.to]));
      const nodes = data.nodes.filter(node => visibleIds.has(node.id)).map(node => ({id: node.id, label: node.label, color: colors[node.group]}));
      network.setData({nodes, edges: shownEdges.map((edge, i) => ({...edge, id: i}))});
      $('status').textContent = `${nodes.length} / ${data.nodes.length} resources · ${shownEdges.length} / ${data.edges.length} relationships · ${data.triples} RDF statements including literal values${search || type ? ' · Matching resources and immediate neighbours' : ''}`;
    }
    function inspect(id) {
      const node = byId.get(id); if (!node) return;
      const title = document.createElement('h2'); title.textContent = node.label;
      const kind = document.createElement('p'); kind.textContent = node.group;
      const uri = document.createElement('code'); uri.textContent = id;
      const list = document.createElement('dl');
      node.properties.forEach(property => { const dt = document.createElement('dt'), dd = document.createElement('dd'); dt.textContent = property.predicate; dd.textContent = property.value; list.append(dt, dd); });
      const heading = document.createElement('h3'); heading.textContent = 'Connected resources';
      const related = document.createElement('div');
      data.edges.filter(edge => edge.from === id || edge.to === id).forEach(edge => {
        const other = edge.from === id ? edge.to : edge.from;
        const button = document.createElement('button');
        button.textContent = `${edge.from === id ? '→' : '←'} ${edge.label}: ${byId.get(other)?.label || other}`;
        button.onclick = () => { reveal(other); }; related.append(button);
      });
      $('details').replaceChildren(title, kind, uri, list, heading, related);
      if (visibleIds.has(id)) { network.selectNodes([id]); network.focus(id, {scale: 1.1, animation: true}); }
      const url = new URL(location.href); url.searchParams.set('node', id); history.replaceState(null, '', url);
    }
    function reveal(id) {
      if (!visibleIds.has(id)) { $('type').value = ''; $('schema').checked = true; $('search').value = id; render(); }
      inspect(id);
    }
    network.on('selectNode', event => inspect(event.nodes[0]));
    let timer; $('search').oninput = () => { clearTimeout(timer); timer = setTimeout(render, 200); };
    $('type').onchange = render; $('schema').onchange = render;
    $('fit').onclick = () => network.fit({animation: true});
    $('reset').onclick = () => { $('search').value = ''; $('type').value = ''; $('schema').checked = true; render(); network.fit(); };
    render();
    const id = new URLSearchParams(location.search).get('node');
    if (id && byId.has(id)) reveal(id);
  } catch (error) { $('status').textContent = `Could not load graph. ${error.message}`; $('status').className = 'error'; }
})();
