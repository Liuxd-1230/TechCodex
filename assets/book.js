// Progressive enhancement only; chapters and native details work without this script.
document.querySelectorAll('.md-content figure img').forEach(img => {
  img.decoding = 'async';
});
