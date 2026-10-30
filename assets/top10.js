const $=s=>document.querySelector(s);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let units=[],universities=[],reviews=[];
const api=window.UNIT_CLUB_API_BASE?new URL(window.UNIT_CLUB_API_BASE,document.baseURI):null;
async function json(url){const r=await fetch(url);if(!r.ok)throw Error('Loading failed');return r.json()}
function renderList(target,university=''){
 const ranked=LunchTableRankings.rank(units,reviews,university);
 $(target).innerHTML=ranked.length?ranked.map((u,i)=>`<li class="leaderboard-row"><span class="leaderboard-place" aria-label="Rank ${i+1}">${String(i+1).padStart(2,'0')}</span><div class="leaderboard-unit"><small>${esc(universities.find(v=>v.id===u.university)?.name||u.university)} · ${esc(u.code)}</small><h3><a href="./index.html?unit=${encodeURIComponent(u.id)}">${esc(u.name)} ↗</a></h3><span>${esc(u.faculty)}</span></div><div class="leaderboard-stats"><strong>★ ${u.rating.toFixed(2)} <small>/ 5</small></strong><span>${u.count} ${u.count===1?'review':'reviews'} · ${u.fives} five-star</span><small>Ranking score ${u.score.toFixed(3)}</small></div></li>`).join(''):'<li class="empty"><h3>No rated units yet.</h3><p>Units appear here when students add reviews. We show up to ten rated units.</p><a href="./index.html#universities">Find a university and leave a review ↗</a></li>';
}
function choose(){const value=$('#ranking-university').value.trim();const u=universities.find(u=>u.name===value);$('#university-ranking').hidden=!u;$('#selection-status').textContent=value&&!u?'Choose a university from the matching suggestions.':'';if(u){$('#university-title').textContent=u.name+' — Top 10';renderList('#university-list',u.id)}}
function loadLocal(){const value=JSON.parse(localStorage.getItem('unitclub-reviews:'+new URL('.',document.baseURI).pathname)||'[]');if(!Array.isArray(value))throw Error('Invalid reviews');return value}
(async()=>{try{
 const data=await json(api?new URL('catalog',api):new URL('./data/catalog.json',document.baseURI));units=data.units;universities=data.universities;
 reviews=api?await json(new URL('reviews',api)):loadLocal();
 $('#ranking-storage').textContent=api?'Rankings use reviews shared through the connected server.':'Browser-only rankings: these results use reviews saved on this device. Shared rankings require a connected review server.';
 $('#ranking-options').innerHTML=universities.slice().sort((a,b)=>a.name.localeCompare(b.name)).map(u=>`<option value="${esc(u.name)}"></option>`).join('');
 $('#ranking-university').disabled=false;renderList('#global-list');$('#ranking-university').addEventListener('input',choose);
 }catch(e){$('#ranking-storage').textContent='Could not load rankings. Refresh the page to try again.';$('#global-list').innerHTML='<li class="empty">Rankings are unavailable.</li>'}
})();
window.addEventListener('storage',()=>{if(!api){try{reviews=loadLocal();renderList('#global-list');choose()}catch{$('#ranking-storage').textContent='Could not read saved reviews. Refresh to try again.'}}});
