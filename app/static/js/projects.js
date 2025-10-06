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

// Modal builder for project cards
(function(){
  const projectCards = Array.from(document.querySelectorAll('.project-card'));
  const modalTargets = Array.from(document.querySelectorAll('[data-modal-target]'));
  if(projectCards.length===0 && modalTargets.length===0) return;

  function buildModal(sourceEl){
  const overlay = document.createElement('div');
  overlay.className = 'project-modal-overlay fixed inset-0 z-50 flex items-center justify-center';

    const panel = document.createElement('div');
    panel.className = 'bg-white rounded-xl shadow-xl max-w-3xl w-[min(96%,900px)] p-6 relative';

    const closeBtn = document.createElement('button');
    closeBtn.className = 'project-modal-close text-slate-500 hover:text-teal-600 absolute top-4 right-4 text-2xl';
    closeBtn.setAttribute('aria-label','Close');
    closeBtn.innerHTML = '&times;';

    // clone source content
    const content = sourceEl.cloneNode(true);
    content.classList.remove('hidden');

  // place close button in a header row so it doesn't overlap the hero image
  const headerRow = document.createElement('div');
  headerRow.style.display = 'flex';
  headerRow.style.justifyContent = 'flex-end';
  headerRow.style.alignItems = 'center';
  headerRow.style.marginBottom = '0.5rem';
  headerRow.appendChild(closeBtn);
  panel.appendChild(headerRow);
  panel.appendChild(content);
    overlay.appendChild(panel);

    // lock body scroll while modal is open
    document.body.style.overflow = 'hidden';

    // open animation
    requestAnimationFrame(()=> overlay.classList.add('open'));

    // keep track of who opened the modal so we can return focus
    const opener = document.activeElement;

    // close handlers
    function onKey(e){ if(e.key==='Escape') close(); }
    function onOverlayClick(e){ if(e.target === overlay) close(); }
    function close(){
      document.removeEventListener('keydown', onKey);
      overlay.removeEventListener('click', onOverlayClick);
      try{ closeBtn.removeEventListener('click', close); }catch(e){}
      // restore body scroll
      document.body.style.overflow = '';
      overlay.remove();
      try{ if(opener && typeof opener.focus === 'function') opener.focus(); }catch(e){}
    }

    overlay.addEventListener('click', onOverlayClick);
    closeBtn.addEventListener('click', close);
    document.addEventListener('keydown', onKey);

    return overlay;
  }

  function attach(el){
    if(el._modalAttached) return;
    el._modalAttached = true;
    el.addEventListener('click', (e)=>{
      e.preventDefault();
      e.stopPropagation();
      const target = el.getAttribute('data-modal-target');
      if(!target) return;
      const src = document.getElementById('modal-source-' + target);
      if(!src) return;
      const modal = buildModal(src);
      document.body.appendChild(modal);
    });
  }

  projectCards.forEach(card=>{ if(card.getAttribute('data-modal-target')) attach(card); });
  modalTargets.forEach(t=> attach(t));
})();
