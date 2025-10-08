// board-modals.js - page-scoped modal handlers for About → Board
(function(){
  // find all modal triggers on the page (directors and managers)
  const targets = Array.from(document.querySelectorAll('[data-modal-target]'));
  if(targets.length === 0) return;

  function buildModalFromSource(sourceEl){
    const overlay = document.createElement('div');
    overlay.className = 'board-modal-overlay fixed inset-0 z-50 flex items-center justify-center';

  const panel = document.createElement('div');
  // panel has no outer padding so hero can reach edges; body content is wrapped separately
  panel.className = 'bg-white rounded-xl shadow-xl max-w-3xl w-[min(96%,900px)] p-0 relative overflow-hidden';
  panel.setAttribute('role','dialog');
  panel.setAttribute('aria-modal','true');

    const closeBtn = document.createElement('button');
    closeBtn.className = 'board-modal-close absolute top-4 right-4 z-10 bg-white/80 hover:bg-white text-slate-700 hover:text-red-600 rounded-full w-8 h-8 flex items-center justify-center text-xl font-bold shadow-lg transition-all';
    closeBtn.setAttribute('aria-label','Close');
    closeBtn.innerHTML = '&times;';

  const content = sourceEl.cloneNode(true);
    content.classList.remove('hidden');

  // Move the hero (image) to the top so it spans the full panel width, then wrap the rest in a padded body
  const hero = content.querySelector('.modal-hero');
  if(hero){
    // remove any layout-specific negative margins from templates and ensure it fills
    hero.classList.remove('-mx-6','-mt-6','mb-4','rounded-t-xl');
    hero.classList.add('w-full','block');
    // detach from cloned content and append into panel
    hero.remove();
    panel.appendChild(hero);
  }

  // create a padded body wrapper for title, text and lists
  const bodyWrap = document.createElement('div');
  bodyWrap.className = 'p-6';
  while(content.firstChild){
    bodyWrap.appendChild(content.firstChild);
  }

  panel.appendChild(bodyWrap);
  panel.appendChild(closeBtn);
    overlay.appendChild(panel);

  // lock scroll
  document.body.style.overflow = 'hidden';

    // remember opener
    const opener = document.activeElement;

  function onKey(e){ if(e.key === 'Escape') close(); }
    function onOverlayClick(e){ if(e.target === overlay) close(); }
    function close(){
      document.removeEventListener('keydown', onKey);
      overlay.removeEventListener('click', onOverlayClick);
      try{ closeBtn.removeEventListener('click', close); }catch(e){}
      document.body.style.overflow = '';
      overlay.remove();
      try{ if(opener && typeof opener.focus === 'function') opener.focus(); }catch(e){}
    }

    overlay.addEventListener('click', onOverlayClick);
    closeBtn.addEventListener('click', close);
    document.addEventListener('keydown', onKey);

    // ensure title has an id for aria-labelledby
    const title = bodyWrap.querySelector('.modal-title');
    if(title){
      const titleId = 'modal-title-' + Math.random().toString(36).slice(2,9);
      title.id = titleId;
      panel.setAttribute('aria-labelledby', titleId);
    }

    // move focus to the panel for accessibility
    panel.tabIndex = -1;
    requestAnimationFrame(()=> {
      overlay.classList.add('open');
      try{ panel.focus(); }catch(e){}
    });

    return overlay;
  }

  targets.forEach(el => {
    if(el._boardModalAttached) return;
    el._boardModalAttached = true;
    el.addEventListener('click', e=>{
      e.preventDefault();
      e.stopPropagation();
      const id = el.getAttribute('data-modal-target');
      if(!id) return;
      const src = document.getElementById('modal-source-' + id);
      if(!src) return;
      const modal = buildModalFromSource(src);
      document.body.appendChild(modal);
    });
  });
})();
