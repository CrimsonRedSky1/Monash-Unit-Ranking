const $=s=>document.querySelector(s);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const storageKey='unitclub-saved';let catalogue=null;
function readSaved(){const data=JSON.parse(localStorage.getItem(storageKey)||'[]');if(!Array.isArray(data))throw Error('Invalid saved units');return new Set(data.filter(id=>typeof id==='string'))}
function renderSaved(){
 if(!catalogue)return;
 try{
 const saved=readSaved(),groups=new Map(),known=new Set(catalogue.units.map(u=>u.id));
 for(const unit of catalogue.units){if(!saved.has(unit.id))continue;if(!groups.has(unit.university))groups.set(unit.university,[]);groups.get(unit.university).push(unit)}
 const names=new Map(catalogue.universities.map(u=>[u.id,u.name]));const missing=[...saved].filter(id=>!known.has(id));
 $('#saved-status').textContent=`${saved.size} saved ${saved.size===1?'unit':'units'}${groups.size?' across '+groups.size+' '+(groups.size===1?'university':'universities'):''}.`;
 $('#saved-groups').innerHTML=[...groups].sort(([a],[b])=>(names.get(a)||a).localeCompare(names.get(b)||b)).map(([id,units],i)=>`<section class="saved-university" aria-labelledby="saved-heading-${i}"><div class="section-heading"><h2 id="saved-heading-${i}">${esc(names.get(id)||id)}</h2><span>${units.length} saved</span></div><ul class="saved-list">${units.sort((a,b)=>a.code.localeCompare(b.code)).map(u=>`<li class="saved-row"><div><small>${esc(u.code)} · ${esc(u.faculty)}</small><h3><a href="./index.html?unit=${encodeURIComponent(u.id)}">${esc(u.name)}</a></h3><span>${esc(u.year)} handbook${u.credits?' · '+esc(u.credits)+' credit points':''}</span></div><button class="secondary" data-remove="${esc(u.id)}" aria-label="Remove ${esc(u.code)} from saved units">Remove</button></li>`).join('')}</ul></section>`).join('');
 if(missing.length)$('#saved-groups').innerHTML+=`<section class="saved-university"><h2>Unavailable units</h2><p>These bookmarks are retained, but their units are not in the current catalogue.</p><ul class="saved-list">${missing.map(id=>`<li class="saved-row"><span>${esc(id)}</span><button class="secondary" data-remove="${esc(id)}" aria-label="Remove ${esc(id)} from saved units">Remove</button></li>`).join('')}</ul></section>`;
 if(!saved.size)$('#saved-groups').innerHTML='<div class="empty"><h2>Your shortlist starts here.</h2><p>Use the bookmark button on any unit to save it here.</p><a class="primary" href="./index.html#universities">Explore universities</a></div>';
 }catch{$('#saved-status').textContent='Your saved units could not be read. Check that browser storage is available and refresh to try again.';$('#saved-groups').innerHTML=''}
}
$('#saved-groups').addEventListener('click',e=>{const button=e.target.closest('[data-remove]');if(!button)return;try{const saved=readSaved();saved.delete(button.dataset.remove);localStorage.setItem(storageKey,JSON.stringify([...saved]));renderSaved();$('#saved-status').textContent+=' Unit removed.';$('#saved-status').setAttribute('tabindex','-1');$('#saved-status').focus()}catch{$('#saved-status').textContent='Could not remove this bookmark. Check browser storage and try again.'}});
(async()=>{try{const api=window.UNIT_CLUB_API_BASE?new URL(window.UNIT_CLUB_API_BASE,document.baseURI):null;const response=await fetch(api?new URL('catalog',api):new URL('./data/catalog.json',document.baseURI));if(!response.ok)throw Error('Catalogue unavailable');catalogue=await response.json();renderSaved()}catch{$('#saved-status').textContent='Could not load the catalogue. Your bookmarks are retained; refresh to try again.'}})();
window.addEventListener('storage',e=>{if(e.key===storageKey||e.key===null)renderSaved()});
window.addEventListener('pageshow',e=>{if(e.persisted)renderSaved()});
