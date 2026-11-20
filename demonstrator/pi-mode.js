(function () {
  var params = new URLSearchParams(window.location.search);
  var piMode = params.get('pi') === 'true';
  try {
    if (piMode) sessionStorage.setItem('zorro-pi-mode', 'true');
    else if (sessionStorage.getItem('zorro-pi-mode') === 'true') {
      piMode = true;
      params.set('pi', 'true');
      var query = params.toString();
      history.replaceState(null, '', window.location.pathname + (query ? '?' + query : '') + window.location.hash);
    }
  } catch (_) {}
  if (!piMode) return;
  document.documentElement.classList.add('pi-mode');

  // Keep touchscreen mode as visitors follow links to other demonstrator pages.
  document.addEventListener('click', function (event) {
    var link = event.target.closest('a[href]');
    if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    var target = new URL(link.href, window.location.href);
    if (target.origin !== window.location.origin || !target.pathname.includes('/demonstrator/')) return;
    if (target.searchParams.get('pi') !== 'true') target.searchParams.set('pi', 'true');
    link.href = target.pathname + target.search + target.hash;
  });

  var lastTouchEnd = 0;
  document.addEventListener('touchend', function (event) {
    var now = Date.now();
    if (now - lastTouchEnd <= 350) event.preventDefault();
    lastTouchEnd = now;
  }, { passive: false });
})();
