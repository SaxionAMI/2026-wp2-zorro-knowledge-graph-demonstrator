const viewer = document.querySelector('.ontology-viewer');
const buttons = document.querySelectorAll('[data-view]');
buttons.forEach(button => button.addEventListener('click', () => {
  const demo = button.dataset.view === 'demo';
  const src = 'webvowl/index.html?view=' + button.dataset.view + '#' + button.dataset.view;
  viewer.src = src;
  viewer.title = demo ? 'Demo Extension ontology in WebVOWL' : 'ZORRO ontology in WebVOWL';
  document.getElementById('fullscreen').href = src;
  const download = document.getElementById('ontology-download');
  download.href = demo ? 'ZorroDemo.owl' : 'ZorroOntology.owl';
  download.textContent = demo ? 'Download Demo Extension (OWL)' : 'Download ZORRO (OWL)';
  buttons.forEach(item => {
    const active = item === button;
    item.setAttribute('aria-pressed', String(active));
    item.classList.toggle('secondary', !active);
  });
}));
