window.MathJax = {
  tex: {inlineMath: [['\\(', '\\)']], displayMath: [['\\[', '\\]']], processEscapes: true},
  options: {ignoreHtmlClass: '.*|', processHtmlClass: 'arithmatex'},
  chtml: {matchFontHeight: false},
  startup: {ready() { MathJax.startup.defaultReady(); }}
};
