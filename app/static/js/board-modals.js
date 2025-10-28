// board-modals.js - page-scoped modal handlers for About → Board
(function(){
  // find all modal triggers on the page (directors and managers)
  const targets = Array.from(document.querySelectorAll('[data-modal-target]'));
  if(targets.length === 0) return;

  function buildModalFromSource(sourceEl, triggerEl){
    const overlay = document.createElement('div');
    overlay.className = 'board-modal-overlay fixed inset-0 z-50 flex items-center justify-center';

  const panel = document.createElement('div');
  // panel has no outer padding so hero can reach edges; body content is wrapped separately
  // remove rounded corners so hero image appears rectangular (not clipped)
  panel.className = 'bg-white shadow-xl max-w-3xl w-[min(96%,900px)] p-0 relative overflow-hidden';
  panel.setAttribute('role','dialog');
  panel.setAttribute('aria-modal','true');

  // initialize hidden animation state
  overlay.style.opacity = '0';
  overlay.style.transition = 'opacity .28s ease';
  panel.style.transform = 'scale(0.98) translateY(12px)';
  panel.style.opacity = '0';
  panel.style.transition = 'transform .36s cubic-bezier(.2,.9,.2,1), opacity .28s ease';

    const closeBtn = document.createElement('button');
  // Use the same visual style as the pillar-close button on the homepage
  // keep `board-modal-close` for any page-scoped z-index rules
  closeBtn.className = 'board-modal-close pillar-close absolute right-4 top-4 text-slate-400 hover:text-teal-600 text-2xl leading-none font-bold';
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
    // remove any gradient/overlay siblings that were used for cards so they don't create
    // translucent bands in the modal. Common patterns: absolute inset overlays and
    // utility classes like bg-gradient-to-t
    try{
      const overlays = hero.querySelectorAll('.absolute.inset-0, .bg-gradient-to-t, .overlay, .modal-hero > div');
      overlays.forEach(o => { if(o && o.parentNode) o.parentNode.removeChild(o); });
    }catch(e){}
    // detach from cloned content and append into panel
    hero.remove();
    panel.appendChild(hero);
    // ensure the image inside the hero can scale to a reasonable viewport height
    try{
      const img = hero.querySelector('img');
      if(img){
        img.style.height = 'auto';
        img.style.maxHeight = '75vh';
        img.style.objectFit = 'cover';
        img.style.display = 'block';
      }
    }catch(e){}
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
      // animate out
      overlay.style.opacity = '0';
      panel.style.transform = 'scale(0.98) translateY(12px)';
      panel.style.opacity = '0';

      // cleanup after transition (with timeout fallback)
      let done = false;
      const tidy = () => {
        if (done) return; done = true;
        document.removeEventListener('keydown', onKey);
        overlay.removeEventListener('click', onOverlayClick);
        try{ closeBtn.removeEventListener('click', close); }catch(e){}
        document.body.style.overflow = '';
        try{ overlay.remove(); }catch(e){}
        try{ if(opener && typeof opener.focus === 'function') opener.focus(); }catch(e){}
      };

      overlay.addEventListener('transitionend', (ev) => {
        if (ev.target === overlay) tidy();
      }, { once: true });
      setTimeout(tidy, 520);
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

    // move focus to the panel for accessibility and run open animation
    panel.tabIndex = -1;
    requestAnimationFrame(()=> {
      overlay.classList.add('open');
      // set transform-origin from trigger so animation feels anchored (approx)
      if (triggerEl && triggerEl.getBoundingClientRect) {
        try {
          const r = triggerEl.getBoundingClientRect();
          const ox = r.left + r.width/2;
          const oy = r.top + r.height/2;
          panel.style.transformOrigin = `${ox}px ${oy}px`;
        } catch(e){}
      }
      overlay.style.opacity = '1';
      panel.style.transform = 'scale(1) translateY(0)';
      panel.style.opacity = '1';
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
  const modal = buildModalFromSource(src, el);
      document.body.appendChild(modal);
    });
  });
})();
