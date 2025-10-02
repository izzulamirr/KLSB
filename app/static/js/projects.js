// projects.js - filtering & modal activation for project showcase
(function(){
  const filterBar = document.getElementById('project-filters');
  const cards = Array.from(document.querySelectorAll('.project-card'));
  if(!filterBar || cards.length === 0) return;

  function applyFilter(cat){
    cards.forEach(card => {
      const cats = card.getAttribute('data-cat').split(/\s+/);
      const show = cat === 'all' || cats.includes(cat);
      card.style.display = show ? '' : 'none';
    });
  }

  filterBar.addEventListener('click', e => {
    const btn = e.target.closest('button[data-filter]');
    if(!btn) return;
    const cat = btn.getAttribute('data-filter');
    filterBar.querySelectorAll('.filter-chip').forEach(b => b.classList.remove('is-active'));
    btn.classList.add('is-active');
    applyFilter(cat);
  });

  // Optional: init from hash (#cat=engineering)
  const hash = new URLSearchParams(window.location.hash.slice(1));
  const catParam = hash.get('cat');
  if(catParam){
    const target = filterBar.querySelector(`[data-filter="${catParam}"]`);
    if(target){ target.click(); }
  }
})();
