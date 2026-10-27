/* Display native Capella exports; the browser does not reconstruct the diagrams. */
'use strict';
(async () => {
  const $ = id => document.getElementById(id);
  const image = $('native-diagram');
  let zoom = 1;
  const resize = () => {
    image.style.width = `${image.naturalWidth * zoom}px`;
    image.style.height = `${image.naturalHeight * zoom}px`;
  };
  const fit = () => {
    if (!image.naturalWidth) return;
    zoom = Math.min(($('diagram-viewport').clientWidth - 16) / image.naturalWidth,
      ($('diagram-viewport').clientHeight - 16) / image.naturalHeight, 1);
    resize();
    $('diagram-viewport').scrollTo(0, 0);
  };
  $('diagram-fit').addEventListener('click', fit);
  $('diagram-in').addEventListener('click', () => { zoom = Math.min(8, zoom * 1.4); resize(); });
  $('diagram-out').addEventListener('click', () => { zoom = Math.max(.01, zoom / 1.4); resize(); });
  image.addEventListener('load', fit);
  image.addEventListener('error', () => { $('diagram-status').textContent = 'Diagram image unavailable. Try the model documentation below.'; });
  $('diagram-documentation').addEventListener('click', () => {
    $('documentation-panel').open = true;
    $('documentation-panel').scrollIntoView({behavior: 'smooth', block: 'start'});
  });
  try {
    const response = await fetch('capella-export/diagrams.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const diagrams = await response.json();
    $('diagram-select').replaceChildren(...diagrams.map((diagram, i) => new Option(diagram.name, i)));
    $('diagram-select').disabled = false;
    const show = () => {
      const diagram = diagrams[Number($('diagram-select').value)];
      image.alt = diagram.name;
      image.src = 'capella-export/' + diagram.svg.split('/').map(encodeURIComponent).join('/');
      $('diagram-download').href = image.src;
      $('diagram-download').download = diagram.name + '.svg';
      $('diagram-documentation').href = 'capella-export/' + diagram.documentation;
      $('diagram-status').textContent = `${diagram.name} · Native Capella SVG · ${diagrams.length} diagrams available`;
    };
    $('diagram-select').addEventListener('change', show);
    const initial = diagrams.findIndex(diagram => diagram.name === 'OAB_OperationalArchitecture');
    $('diagram-select').value = String(initial >= 0 ? initial : 0);
    show();
  } catch (error) {
    $('diagram-status').textContent = `Could not load native exports (${error.message}). Open the generated model documentation below.`;
  }
})();
