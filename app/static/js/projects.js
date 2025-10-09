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
    // update KPI after category filter
    if(typeof window.updateProjectsKPI === 'function') window.updateProjectsKPI();
  });

  // Optional: init from hash (#cat=engineering)
  const hash = new URLSearchParams(window.location.hash.slice(1));
  const catParam = hash.get('cat');
  if(catParam){
    const target = filterBar.querySelector(`[data-filter="${catParam}"]`);
    if(target){ target.click(); }
  }
})();

// Industry filter (Engineering only by default)
(function(){
  const industryBar = document.getElementById('industry-filters');
  if(!industryBar) return;
  const chips = Array.from(industryBar.querySelectorAll('button[data-industry]'));
  const allCards = Array.from(document.querySelectorAll('.project-card'));

  function applyIndustry(ind){
    allCards.forEach(card => {
      const raw = (card.getAttribute('data-industry') || '').trim();
      // support multiple industries separated by space, comma or pipe
      const parts = raw.split(/[\s,|]+/).filter(Boolean).map(s=>s.toLowerCase());
      const matches = ind === 'all' || parts.includes(ind.toLowerCase());
      card.style.display = matches ? '' : 'none';
    });
    // Hide year details that have no visible project cards
    const details = Array.from(document.querySelectorAll('details'));
    details.forEach(d => {
      const visibleChild = d.querySelector('.project-card:not([style*="display: none"])');
      // If no visible project-card inside, hide the details entirely
      d.style.display = visibleChild ? '' : 'none';
    });
    // update KPI after industry filter
    if(typeof window.updateProjectsKPI === 'function') window.updateProjectsKPI();
  }

  industryBar.addEventListener('click', e => {
    const btn = e.target.closest('button[data-industry]');
    if(!btn) return;
    chips.forEach(c=> c.classList.remove('is-active'));
    btn.classList.add('is-active');
    applyIndustry(btn.getAttribute('data-industry'));
  });

  // initialize: set Engineering active
  const init = industryBar.querySelector('[data-industry="engineering"]');
  if(init) init.click();
})();

// Search integration for project cards
(function(){
  const searchInput = document.getElementById('project-search');
  if(!searchInput) return;
  const cards = Array.from(document.querySelectorAll('.project-card'));
  function normalize(s){ return (s||'').toLowerCase(); }
  searchInput.addEventListener('input', ()=>{
    const q = normalize(searchInput.value.trim());
    cards.forEach(card=>{
      const title = normalize(card.querySelector('.project-title')?.textContent);
      const excerpt = normalize(card.querySelector('.project-excerpt')?.textContent);
      const tags = normalize(card.getAttribute('data-cat'));
      const matches = q === '' || title.indexOf(q) !== -1 || excerpt.indexOf(q) !== -1 || tags.indexOf(q) !== -1;
      // keep existing category filtering by relying on current inline display style
      if(matches){
        if(card._shouldBeHiddenByCategory) card.style.display = 'none'; else card.style.display = '';
      } else {
        card.style.display = 'none';
      }
    });
    // update KPI after search
    if(typeof window.updateProjectsKPI === 'function') window.updateProjectsKPI();
  });
})();

// KPI updater: exposes window.updateProjectsKPI so other scripts can call it
window.updateProjectsKPI = function(){
  const countEl = document.getElementById('kpi-projects-count');
  if(!countEl) return;
  const visible = Array.from(document.querySelectorAll('.project-card')).filter(c => c.offsetParent !== null && c.style.display !== 'none');
  countEl.textContent = visible.length;
};

// run once on load to initialize the KPI
if(typeof window.updateProjectsKPI === 'function') window.updateProjectsKPI();

// Insert visible industry badges into each project card based on data-industry
(function(){
  // Normalize header structure so CSS can style company/year consistently
  function normalizeCardHeaders(){
    const cards = Array.from(document.querySelectorAll('.project-card'));
    cards.forEach(card=>{
      // find first child flex row (company + year)
      const headerRow = card.querySelector('.flex.items-start') || card.querySelector('.flex');
      if(!headerRow) return;
      // if already normalized, skip
      if(headerRow.classList.contains('card-header')) return;
      // create wrappers
      const company = headerRow.querySelector('.flex-1');
      const year = headerRow.querySelector('.text-right');
      // also find project owner to place inline if present
      const ownerBlock = card.querySelector('.mt-3 .text-xs') ? card.querySelector('.mt-3') : null;
      const wrapper = document.createElement('div');
      wrapper.className = 'card-header';
      const compWrap = document.createElement('div');
      compWrap.className = 'company-wrap';
      if(company) compWrap.appendChild(company);
      // if ownerBlock exists, create an inline owner element and attach
      if(ownerBlock){
        const ownerText = ownerBlock.querySelector('.font-semibold') ? ownerBlock.querySelector('.font-semibold').textContent : '';
        const ownerInline = document.createElement('div');
        ownerInline.className = 'owner-inline';
        ownerInline.textContent = ownerText;
        // insert after company name
        compWrap.appendChild(ownerInline);
        // remove original ownerBlock to avoid duplication
        ownerBlock.remove();
      }
      const yearWrap = document.createElement('div');
      yearWrap.className = 'year-wrap text-sm text-slate-500';
      if(year) yearWrap.appendChild(year);
      // if ownerBlock exists, move owner text into the right-side yearWrap so it appears on the right
      if(ownerBlock){
        const ownerText = ownerBlock.querySelector('.font-semibold') ? ownerBlock.querySelector('.font-semibold').textContent.trim() : ownerBlock.textContent.trim();
        // set data-owner for reliable exports / future logic
        try{ card.setAttribute('data-owner', ownerText); }catch(e){ }
        // ensure we don't duplicate the owner under year
        const yearContainsOwner = yearWrap && ((yearWrap.textContent||'').trim().indexOf(ownerText) !== -1);
        if(!yearContainsOwner){
          const ownerUnder = document.createElement('div');
          ownerUnder.className = 'owner-under-year';
          ownerUnder.textContent = ownerText;
          yearWrap.appendChild(ownerUnder);
        }
        // remove original ownerBlock to avoid duplication
        ownerBlock.remove();
      }
      // move into wrapper (company left, year + owner right)
      wrapper.appendChild(compWrap);
      wrapper.appendChild(yearWrap);
      // replace headerRow with wrapper
      headerRow.replaceWith(wrapper);
      // guard: remove accidental duplicate nodes or stray text that repeat the company name
      try{
        const companyText = company ? (company.querySelector('.font-semibold') ? company.querySelector('.font-semibold').textContent.trim() : company.textContent.trim()) : '';
        if(companyText){
          // remove element nodes inside wrapper that match the company text but are not the intended wraps
          const descendants = Array.from(wrapper.querySelectorAll('*'));
          descendants.forEach(node=>{
            // skip the wrapper containers and any node that lives inside them
            if(node === compWrap || node === yearWrap) return;
            if(compWrap.contains(node) || yearWrap.contains(node)) return;
            const t = (node.textContent||'').trim();
            if(t === companyText) node.remove();
          });
          // also remove stray text nodes directly under the wrapper that equal the company text
          Array.from(wrapper.childNodes).forEach(n => {
            if(n.nodeType === Node.TEXT_NODE && n.textContent.trim() === companyText) n.remove();
          });
        }
      }catch(e){ /* fail silently - non-critical */ }
    });
  }
  // run normalization early
  document.addEventListener('DOMContentLoaded', normalizeCardHeaders);
  // after DOM ready, ensure badges and KPI refresh
  document.addEventListener('DOMContentLoaded', ()=>{
    try{ if(typeof window.addIndustryBadges === 'function') window.addIndustryBadges(); }catch(e){}
    try{ if(typeof window.updateProjectsKPI === 'function') window.updateProjectsKPI(); }catch(e){}
  });
  function industryLabelFromKey(key){
    if(!key) return '';
    const k = key.toLowerCase();
    const map = {
      'engineering': 'Engineering Solutions',
      'manpower': 'Manpower',
      'construction': 'Construction',
      'cybersecurity': 'Cybersecurity',
      'inspection': 'Inspection',
      'supply-trading': 'Supply Trading',
      'supply': 'Supply Trading',
    };
    return map[k] || k.replace(/-/g,' ').replace(/\b\w/g, c=>c.toUpperCase());
  }

  function addIndustryBadges(){
    const cards = Array.from(document.querySelectorAll('.project-card'));
    cards.forEach(card=>{
      // don't duplicate
      if(card.querySelector('.industry-badge')) return;
      const raw = (card.getAttribute('data-industry') || '').trim();
      if(!raw) return;
      const parts = raw.split(/[\s,|]+/).filter(Boolean);
      if(parts.length === 0) return;
      const label = industryLabelFromKey(parts[0]);
      // find company element (.flex-1 > .font-semibold)
      // create absolute badge and attach to card
      const span = document.createElement('span');
      span.className = 'industry-badge';
      span.textContent = label;
      card.appendChild(span);
      // ensure project title left-align
      const titleContainer = card.querySelector('.mt-3.text-slate-700');
      if(titleContainer){
        titleContainer.classList.add('project-title-content');
      }
    });
  }

  // run now and also expose for later calls
  addIndustryBadges();
  window.addIndustryBadges = addIndustryBadges;
})();

// CSV export: collect currently visible project cards and build CSV
const exportBtn = document.getElementById('export-csv');
if (exportBtn) {
  exportBtn.addEventListener('click', () => {
    const visibleCards = Array.from(document.querySelectorAll('.project-card')).filter(c => c.offsetParent !== null && !c.classList.contains('hidden'));
    if (!visibleCards.length) {
      alert('No projects are visible to export.');
      return;
    }

    const headers = ['Company','Project Owner','Year','Title'];
    const rows = visibleCards.map(card => {
      const company = card.getAttribute('data-company') || '';
      const owner = card.getAttribute('data-owner') || '';
      const year = card.getAttribute('data-year') || '';
      const title = card.getAttribute('data-title') || (card.querySelector('.project-excerpt') ? card.querySelector('.project-excerpt').innerText.trim() : '');
      // Escape double quotes
      return [company, owner, year, title].map(v => '"' + (v || '').replace(/"/g, '""') + '"').join(',');
    });

    const csvContent = [headers.join(','), ...rows].join('\r\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'projects-export.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });
}

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
