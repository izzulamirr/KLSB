// nav.js - modern navigation interactions
(function(){
  const header = document.getElementById('site-header');
  const toggle = document.querySelector('.nav-toggle');
  const panel = document.getElementById('mobile-nav');
  const focusableSelectors = 'a[href], button:not([disabled])';
  let lastFocused;

  function setExpanded(expanded){
    if(!toggle || !panel) return;
    toggle.setAttribute('aria-expanded', expanded);
    panel.classList.toggle('open', expanded);
    if(expanded){
      panel.removeAttribute('hidden');
      lastFocused = document.activeElement;
      // focus first link
      const firstLink = panel.querySelector(focusableSelectors);
      if(firstLink) firstLink.focus();
      document.addEventListener('keydown', onKeydown);
    } else {
      panel.setAttribute('hidden', '');
      document.removeEventListener('keydown', onKeydown);
      if(lastFocused) lastFocused.focus();
    }
  }

  function onKeydown(e){
    if(e.key === 'Escape') {
      setExpanded(false);
    }
  }

  if(toggle){
    toggle.addEventListener('click', () => {
      const expanded = toggle.getAttribute('aria-expanded') === 'true';
      setExpanded(!expanded);
    });
  }

  // Close when clicking outside sheet
  if(panel){
    panel.addEventListener('click', (e) => {
      if(e.target === panel){
        setExpanded(false);
      }
    });
  }

  // Active link highlighting (only one at a time)
  const navLinks = Array.from(document.querySelectorAll('[data-nav]'));
  const currentPath = window.location.pathname; // e.g., '/projects'

  function clearActive(){
    navLinks.forEach(l => l.classList.remove('active'));
  }

  function setActiveByPredicate(predicate){
    clearActive();
    const target = navLinks.find(predicate);
    if(target) target.classList.add('active');
  }

  // 1. Exact page match first (non-hash links)
  setActiveByPredicate(link => {
    try { return new URL(link.href).pathname === currentPath && !link.hash; } catch { return false; }
  });

  // 2. If on root ('/') and there is a hash in location OR user scrolls to sections, we can highlight based on hash
  function hashActive(){
    if(currentPath !== '/') return; // only treat sections on home
    const currentHash = window.location.hash; // includes '#'
    if(!currentHash) return; // leave page-level active state
    setActiveByPredicate(link => link.getAttribute('href') === '/' + currentHash);
  }
  window.addEventListener('hashchange', hashActive);
  hashActive();

  // 3. Optional scroll-based section activation (simple heuristic: element top in viewport)
  const sectionAnchors = navLinks.filter(l => l.getAttribute('href')?.startsWith('/#'));
  const sectionIds = sectionAnchors.map(l => l.getAttribute('href').slice(2));
  const sectionEls = sectionIds.map(id => document.getElementById(id)).filter(Boolean);

  function onScrollSections(){
    if(currentPath !== '/' || sectionEls.length === 0) return;
    const scrollY = window.scrollY;
    // choose the last section whose top is above threshold
    let activeId = null;
    for(const el of sectionEls){
      const top = el.getBoundingClientRect().top + window.scrollY;
      if(top - 140 <= scrollY){ // offset for header
        activeId = el.id;
      }
    }
    if(activeId){
      setActiveByPredicate(link => link.getAttribute('href') === '/#' + activeId);
    }
  }
  window.addEventListener('scroll', onScrollSections, { passive:true });

  // Scroll shrink effect
  let lastScroll = 0;
  function onScroll(){
    const y = window.scrollY;
    if(y > 40){
      header?.classList.add('shrink');
    } else {
      header?.classList.remove('shrink');
    }
    lastScroll = y;
  }
  window.addEventListener('scroll', onScroll, { passive:true });
  onScroll();

})();