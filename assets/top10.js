const $=s=>document.querySelector(s);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let units=[],universities=[],reviews=[],demoReviews=[];
let demoMode=new URLSearchParams(location.search).get('demo')==='1';
const api=window.UNIT_CLUB_API_BASE?new URL(window.UNIT_CLUB_API_BASE,document.baseURI):null;
async function json(url){const r=await fetch(url);if(!r.ok)throw Error('Loading failed');return r.json()}
function universityLogo(id){const u=universities.find(v=>v.id===id);return u?.logo?`<img class="university-logo" src="${esc(u.logo)}" alt="" loading="lazy">`:''}
function renderList(target,university=''){
 const ranked=LunchTableRankings.rank(units,demoMode?demoReviews:reviews,university,{includeDemo:demoMode});
 $(target).innerHTML=ranked.length?ranked.map((u,i)=>`<li class="leaderboard-row"><span class="leaderboard-place" aria-label="Rank ${i+1}">${String(i+1).padStart(2,'0')}</span>${universityLogo(u.university)}<div class="leaderboard-unit"><small>${esc(universities.find(v=>v.id===u.university)?.name||u.university)} · ${esc(u.code)}</small><h3><a href="./index.html?unit=${encodeURIComponent(u.id)}${demoMode?'&demo=1':''}">${esc(u.name)}</a></h3><span>${esc(u.faculty)}</span></div><div class="leaderboard-stats"><strong>★ ${u.rating.toFixed(2)} <small>/ 5</small></strong><span>${u.count} ${u.count===1?'review':'reviews'} · ${u.fives} five-star</span><small>Ranking score ${u.score.toFixed(3)}</small></div></li>`).join(''):'<li class="empty"><h3>No rated units yet.</h3><p>Units appear here when students add reviews. We show up to ten rated units.</p><a href="./index.html#universities">Find a university and leave a review</a></li>';
}
let selectedRankingUniversity=null;
function selectUniversity(id){
 const u=universities.find(u=>u.id===id);if(!u)return;
 selectedRankingUniversity=u;$('#ranking-university').value=u.name;$('#ranking-options').innerHTML='';
 $('#selection-status').textContent='Showing the top rated units at '+u.name+'.';
 $('#university-ranking').hidden=false;$('#university-title').innerHTML=universityLogo(u.id)+'<span>'+esc(u.name)+' — Top 10</span>'; renderList('#university-list',u.id);
}
function searchUniversities(){
 selectedRankingUniversity=null;$('#university-ranking').hidden=true;
 const query=$('#ranking-university').value.trim();
 if(!query){$('#ranking-options').innerHTML='';$('#selection-status').textContent='Type a university name or abbreviation, then select a result.';return}
 const result=UniversityDirectory.search(universities,{query});
 $('#selection-status').textContent=result.total?`${result.total} matching ${result.total===1?'university':'universities'}. Select a result${result.total>8?' or keep typing to narrow your search':''}.`:'No matching universities. Try another name or abbreviation.';
 $('#ranking-options').innerHTML=result.items.map(u=>`<button type="button" class="university-result" data-ranking-university="${esc(u.id)}"><strong>${esc(u.name)}</strong><span>View Top 10</span></button>`).join('');
}
function loadLocal(){const value=JSON.parse(localStorage.getItem('unitclub-reviews:'+new URL('.',document.baseURI).pathname)||'[]');if(!Array.isArray(value))throw Error('Invalid reviews');return value}
(async()=>{try{
 const data=await json(api?new URL('catalog',api):new URL('./data/catalog.json',document.baseURI));units=data.units;universities=data.universities;
 reviews=api?await json(new URL('reviews',api)):loadLocal();
 $('#ranking-storage').textContent=api?'Rankings use reviews shared through the connected server.':'Browser-only rankings: these results use reviews saved on this device. Shared rankings require a connected review server.';
 demoReviews=LunchTableDemo.generate(units);$('#ranking-demo').checked=demoMode;
 function updateDemo(){demoMode=$('#ranking-demo').checked;$('#ranking-storage').hidden=demoMode;$('#demo-status').textContent=demoMode?`DEMO ONLY — ${demoReviews.length} fictional reviews across ${new Set(demoReviews.map(r=>r.unit)).size} units. Real reviews are excluded from this preview. Nothing is saved.`:'Demo mode is off. Rankings use real reviews only.';const url=new URL(location.href);demoMode?url.searchParams.set('demo','1'):url.searchParams.delete('demo');history.replaceState(null,'',url);renderList('#global-list');if(selectedRankingUniversity)renderList('#university-list',selectedRankingUniversity.id)}
 $('#ranking-demo').addEventListener('change',updateDemo);updateDemo();
 $('#ranking-university').disabled=false;renderList('#global-list');searchUniversities();
 $('#ranking-university').addEventListener('input',searchUniversities);
 $('#ranking-options').addEventListener('click',e=>{const button=e.target.closest('[data-ranking-university]');if(button){selectUniversity(button.dataset.rankingUniversity);$('#ranking-university').focus()}});
 $('#ranking-university').addEventListener('keydown',e=>{if(e.key==='Enter'){const result=UniversityDirectory.search(universities,{query:e.target.value.trim()});if(e.target.value.trim()&&result.total===1){e.preventDefault();selectUniversity(result.items[0].id)}}if(e.key==='ArrowDown'){const first=$('#ranking-options button');if(first){e.preventDefault();first.focus()}}});
 }catch(e){$('#ranking-storage').textContent='Could not load rankings. Refresh the page to try again.';$('#global-list').innerHTML='<li class="empty">Rankings are unavailable.</li>'}
})();
window.addEventListener('storage',()=>{if(!api){try{reviews=loadLocal();renderList('#global-list');if(selectedRankingUniversity)renderList('#university-list',selectedRankingUniversity.id)}catch{$('#ranking-storage').textContent='Could not read saved reviews. Refresh to try again.'}}});
