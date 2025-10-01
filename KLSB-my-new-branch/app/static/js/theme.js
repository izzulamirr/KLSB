// theme.js - light/dark theme persistence & toggle
(function(){
  const root = document.documentElement;
  const toggle = document.getElementById('theme-toggle');
  const STORAGE_KEY = 'klsb-theme';

  function getPreferred(){
    const stored = localStorage.getItem(STORAGE_KEY);
    if(stored === 'light' || stored === 'dark') return stored;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function apply(theme){
    root.setAttribute('data-theme', theme);
    if(toggle){
      toggle.setAttribute('aria-pressed', theme === 'dark');
      toggle.title = theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
    }
  }

  function set(theme){
    localStorage.setItem(STORAGE_KEY, theme);
    apply(theme);
  }

  // init
  const initial = getPreferred();
  apply(initial);

  // listen for system changes
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if(!stored){
      apply(e.matches ? 'dark' : 'light');
    }
  });

  toggle?.addEventListener('click', () => {
    const current = root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    set(current === 'dark' ? 'light' : 'dark');
  });
})();
