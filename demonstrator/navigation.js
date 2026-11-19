document.addEventListener('click', function (event) {
  document.querySelectorAll('nav .wp-menu[open]').forEach(function (menu) {
    if (!menu.contains(event.target)) menu.open = false;
  });
});
document.addEventListener('keydown', function (event) {
  if (event.key !== 'Escape') return;
  document.querySelectorAll('nav .wp-menu[open]').forEach(function (menu) {
    menu.open = false;
    menu.querySelector('summary').focus();
  });
});
