(async () => {
  const target = document.getElementById('stats');
  try {
    const response = await fetch('graph-data.json');
    if (!response.ok) throw new Error(`Graph data: HTTP ${response.status}`);
    const graph = await response.json();
    const stats = [[graph.triples, 'RDF statements'], [graph.nodes.filter(n => n.group === 'Problem').length, 'Recorded problems'], [graph.nodes.filter(n => n.group === 'Function').length, 'Equipment functions'], [graph.nodes.filter(n => n.group === 'Part').length, 'Parts']];
    target.replaceChildren(...stats.map(([value, label]) => {
      const box = document.createElement('div'); box.className = 'stat';
      const number = document.createElement('strong'); number.textContent = value.toLocaleString();
      const caption = document.createElement('span'); caption.textContent = label;
      box.append(number, caption); return box;
    }));
  } catch (error) { target.textContent = `Could not load statistics. ${error.message}`; }
})();
