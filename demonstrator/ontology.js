const viewer = document.querySelector('.ontology-viewer');
const buttons = document.querySelectorAll('[data-view]');
buttons.forEach(button => button.addEventListener('click', () => {
  const src = 'webvowl/index.html?view=' + button.dataset.view + '#' + button.dataset.view;
  viewer.src = src;
  document.getElementById('fullscreen').href = src;
  buttons.forEach(item => {
    const active = item === button;
    item.setAttribute('aria-pressed', String(active));
    item.classList.toggle('secondary', !active);
  });
}));
