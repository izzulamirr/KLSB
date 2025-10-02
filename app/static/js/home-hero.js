// home-hero.js - enhanced slideshow with indicators
// Each slide can include image and optional alt/label in future
const heroSlides = [
  { image: '/static/img/shutterstock_1431518426.jpg' }
  // { image: '/static/img/another.jpg' },
];

let current = 0;
let timer = null;
const INTERVAL = 6000;

function updateIndicators(index){
  const dots = document.querySelectorAll('.hero-slide-indicator');
  dots.forEach((d,i)=>{
    if(i===index){
      d.setAttribute('aria-current','true');
    } else {
      d.removeAttribute('aria-current');
    }
  });
}

function showSlide(index){
  const slides = document.querySelectorAll('.hero-slide');
  if(!slides.length) return;
  slides.forEach((s,i)=> s.classList.toggle('is-active', i===index));
  updateIndicators(index);
}

function nextSlide(){
  current = (current + 1) % heroSlides.length;
  showSlide(current);
}

function goToSlide(i){
  current = i % heroSlides.length;
  showSlide(current);
  restartTimer();
}

function restartTimer(){
  if(timer){ clearInterval(timer); }
  if(heroSlides.length > 1){
    timer = setInterval(nextSlide, INTERVAL);
  }
}

function buildIndicators(count){
  const progress = document.querySelector('.hero-progress');
  if(!progress) return;
  progress.innerHTML = '';
  for(let i=0;i<count;i++){
    const span = document.createElement('span');
    span.className = 'hero-slide-indicator';
    span.role = 'button';
    span.tabIndex = 0;
    span.dataset.index = i;
    span.addEventListener('click', ()=> goToSlide(i));
    span.addEventListener('keydown', (e)=>{ if(e.key==='Enter' || e.key===' '){ e.preventDefault(); goToSlide(i);} });
    progress.appendChild(span);
  }
}

function initHeroSlideshow(){
  const container = document.querySelector('.hero-slides');
  if(!container) return;

  if(container.children.length === 0){
    heroSlides.forEach((s,i)=>{
      const div = document.createElement('div');
      div.className = 'hero-slide' + (i===0 ? ' is-active' : '');
      div.style.backgroundImage = `url(${s.image})`;
      container.appendChild(div);
    });
  }

  buildIndicators(heroSlides.length);
  showSlide(0);
  restartTimer();
}

document.addEventListener('DOMContentLoaded', initHeroSlideshow);
