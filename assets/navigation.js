/* Carry the active indicator's position across real page navigations. */
(()=>{
 const nav=document.querySelector('header nav');if(!nav)return;
 const indicator=document.createElement('span');indicator.className='nav-indicator';indicator.setAttribute('aria-hidden','true');nav.append(indicator);
 const key='lunchtable-nav-transition';const reduced=matchMedia('(prefers-reduced-motion: reduce)');
 const active=()=>nav.querySelector('.nav.active');
 function position(el){const a=el.getBoundingClientRect(),b=nav.getBoundingClientRect();return {left:a.left-b.left,width:a.width}}
 function paint(p){indicator.style.transform=`translateX(${p.left}px)`;indicator.style.width=p.width+'px'}
 function align(){const el=active();indicator.hidden=!el;if(el)paint(position(el))}
 let previous=null;try{previous=JSON.parse(sessionStorage.getItem(key));sessionStorage.removeItem(key)}catch{}
 function start(){const el=active();if(!el){indicator.hidden=true;return}indicator.hidden=false;const target=position(el);
  if(previous&&previous.path===location.pathname&&Date.now()-previous.time<10000&&!reduced.matches){const source=nav.querySelector(`[data-nav-key="${previous.from}"]`);if(source){paint(position(source));indicator.getBoundingClientRect();requestAnimationFrame(()=>{indicator.classList.add('animate');paint(target)});return}}
  paint(target);requestAnimationFrame(()=>indicator.classList.add('animate'));
 }
 nav.querySelectorAll('.nav').forEach(el=>{const text=el.textContent.trim();el.dataset.navKey=text.startsWith('Top 10')?'top10':text.startsWith('Saved')?'saved':'explore'});
 nav.addEventListener('click',e=>{const link=e.target.closest('a.nav');if(!link||e.button!==0||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey)return;const url=new URL(link.href);if(url.origin!==location.origin)return;
  try{sessionStorage.setItem(key,JSON.stringify({from:active()?.dataset.navKey||link.dataset.navKey,path:url.pathname,time:Date.now()}))}catch{}
 });
 start();document.fonts?.ready.then(()=>{if(!previous)align()});let navWidth=nav.getBoundingClientRect().width;new ResizeObserver(()=>{const width=nav.getBoundingClientRect().width;if(width!==navWidth){navWidth=width;align()}}).observe(nav);
 new MutationObserver(records=>{if(records.some(r=>r.target.matches('.nav')))align()}).observe(nav,{subtree:true,attributes:true,attributeFilter:['class']});
 window.addEventListener('pageshow',e=>{if(e.persisted)align()});
})();
