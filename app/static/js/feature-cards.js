// feature-cards.js - accessible modal popouts for feature cards
(function(){
  // Do NOT early-return if no triggers yet; markup may be injected later.
  const triggers = document.querySelectorAll('[data-modal-target]');

  let activeOverlay = null;
  let lastFocused = null;

  const FOCUSABLE = 'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])';

  function buildOverlay(id){
    const source = document.getElementById('modal-source-' + id);
    if(!source) return null;

    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.setAttribute('role','dialog');
    overlay.setAttribute('aria-modal','true');
    overlay.id = 'modal-' + id;
    overlay.innerHTML = `\n      <div class="modal-dialog" role="document">\n        <button class="modal-close" aria-label="Close dialog">\n          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>\n        </button>\n        <div class="modal-header">${source.querySelector('.modal-title')?.outerHTML || ''}</div>\n        <hr class="modal-divider" />\n        <div class="modal-body">${Array.from(source.children).filter(el=>!el.classList.contains('modal-title')).map(el=>el.outerHTML).join('')} </div>\n      </div>`;
    document.body.appendChild(overlay);
    return overlay;
  }

  function trapFocus(e){
    if(!activeOverlay) return;
    if(e.key !== 'Tab') return;
    const focusables = Array.from(activeOverlay.querySelectorAll(FOCUSABLE)).filter(el=>el.offsetParent !== null);
    if(!focusables.length) return;
    const first = focusables[0];
    const last = focusables[focusables.length - 1];
    if(e.shiftKey && document.activeElement === first){
      e.preventDefault(); last.focus();
    } else if(!e.shiftKey && document.activeElement === last){
      e.preventDefault(); first.focus();
    }
  }

  function openModal(id, trigger){
    if(activeOverlay) closeModal();
    const overlay = buildOverlay(id);
    if(!overlay) return;
    lastFocused = trigger || document.activeElement;
    requestAnimationFrame(()=>{
      overlay.classList.add('open');
      const firstFocusable = overlay.querySelector(FOCUSABLE);
      firstFocusable?.focus();
    });
    activeOverlay = overlay;
    document.addEventListener('keydown', onKeydown, { passive:false });
  }

  function closeModal(){
    if(!activeOverlay) return;
    const overlay = activeOverlay;
    overlay.classList.remove('open');
    setTimeout(()=>{ overlay.remove(); }, 300);
    document.removeEventListener('keydown', onKeydown);
    if(lastFocused) lastFocused.focus();
    activeOverlay = null;
  }

  function onKeydown(e){
    if(e.key === 'Escape'){ closeModal(); }
    else if(e.key === 'Tab'){ trapFocus(e); }
  }

  document.addEventListener('click', (e)=>{
    // Open trigger
    const trigger = e.target.closest('[data-modal-target]');
    if(trigger){
      e.preventDefault();
      openModal(trigger.getAttribute('data-modal-target'), trigger);
      return;
    }
    // Close if clicking overlay (allow slight child gap by checking currentTarget != dialog)
    if(activeOverlay && e.target === activeOverlay){
      closeModal();
      return;
    }
    // Close button (SVG clicks bubble up)
    if(e.target.closest('.modal-close')){
      e.preventDefault();
      closeModal();
    }
  });

    // Equalize hero cards to match the first card's height (fallback when CSS alone doesn't do it)
    function equalizeHeroCards(){
      const container = document.querySelector('.hero-cards');
      if(!container) return;
      const cards = Array.from(container.querySelectorAll(':scope > a'));
      if(!cards.length) return;
      // Reset heights first to allow natural measurement
      cards.forEach(c=>{ c.style.minHeight = ''; c.style.height = ''; });
      // Measure the first card's computed height (including padding)
      const firstRect = cards[0].getBoundingClientRect();
      const target = Math.round(firstRect.height);
      // Apply target as minHeight to all cards
      cards.forEach(c=>{ c.style.minHeight = target + 'px'; });
    }

    // Debounced resize handler
    let resizeTimer = null;
    function onResizeDebounced(){
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(()=>{ equalizeHeroCards(); }, 120);
    }

    // Run on DOM ready and on window resize
    document.addEventListener('DOMContentLoaded', equalizeHeroCards);
    window.addEventListener('resize', onResizeDebounced);

  })();
