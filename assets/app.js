const apiBase=window.UNIT_CLUB_API_BASE ? new URL(window.UNIT_CLUB_API_BASE,document.baseURI) : null;
const reviewStorageKey='unitclub-reviews:'+new URL('.',document.baseURI).pathname;
const submitLabel=apiBase?'Publish review ↗':'Save review in this browser ↗';
async function readJSON(url,options){const response=await fetch(url,options);const body=await response.json();if(!response.ok)throw Error(body.error||'Could not load data');return body}
function validReview(r){return r&&typeof r==='object'&&catalogue.some(u=>u.id===r.unit)&&Number.isInteger(r.rating)&&r.rating>=1&&r.rating<=5&&Number.isInteger(r.year)&&r.year>=1958&&r.year<=Number(new Intl.DateTimeFormat('en',{year:'numeric',timeZone:'Australia/Melbourne'}).format(new Date()))&&typeof r.author==='string'&&r.author.trim().length>=2&&r.author.length<=60&&typeof r.body==='string'&&r.body.trim().length>=20&&r.body.length<=2000&&['Semester 1','Semester 2','Summer semester','Winter semester','Trimester 1','Trimester 2','Trimester 3','Full year','Other teaching period'].includes(r.semester)}
function readBrowserReviews(){const raw=localStorage.getItem(reviewStorageKey);const data=raw?JSON.parse(raw):[];if(!Array.isArray(data))throw Error('Browser review storage is unreadable.');return data.filter(validReview)}
const $=s=>document.querySelector(s), esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let catalogue=[],universities=[],coverage={},reviews=[],view='explore',faculty='All faculties',query='',demo=false,selected=null,visibleCount=24;
let reviewIndex=new Map();
let selectedUniversity=null,universityPage=0;
const demoCodes=new Set('FIT1045 FIT1047 FIT1051 FIT2094 FIT2099 FIT3178 ATS1261 ECC1000 ETC1000 MGC1010 ENG1011 MTH1020 BIO1011 CHM1011 PSY1011 LAW1111 PHA2022'.split(' '));
let saved;try{saved=new Set(JSON.parse(localStorage.getItem('unitclub-saved')||'[]'))}catch{saved=new Set()}
const colours=[['#edf0e4','#7b8d59'],['#f6e9df','#ac7654'],['#e7edf6','#6e88b0'],['#eee8f4','#9a7ab7'],['#f3edda','#a58b4d']];
const bookmark='<svg viewBox="0 0 18 22" aria-hidden="true"><path d="M3 2h12v18l-6-4-6 4Z"/></svg>';
const demoBodies=['The practical work made the ideas click. I enjoyed having something tangible to work on each week. Keep up with the weekly material and give yourself time for the assignments.','An interesting unit with a good mix of concepts and hands-on learning. I found discussing the tutorial questions with classmates especially helpful.','I enjoyed the subject, although some weeks took more work than I expected. Starting assessments early made the semester a lot more manageable.'];
function allReviews(){return [...reviews,...(demo?catalogue.filter(u=>u.university==='monash'&&demoCodes.has(u.code)).flatMap((u,i)=>Array.from({length:3+i%6},(_,j)=>({unit:u.id,author:'Demo student '+(j+1),rating: Math.max(2,5-(j%(i%3+2)===0?1:0)-(i%4===0?1:0)),body:demoBodies[j%3],semester:'Semester 1',year:2026,created:'2026-06-20',demo:true}))):[])]}
function stats(u){const r=reviewIndex.get(u.id)||[];return{count:r.length,rating:r.length?r.reduce((a,r)=>a+r.rating,0)/r.length:0}}
function stars(n){return `<span class="stars" aria-label="${Number(n).toFixed(1)} out of 5 stars">${'★'.repeat(Math.round(n))}${'☆'.repeat(5-Math.round(n))}</span>`}
function shortFaculty(f){return f.replace('Business and Economics','Business & Economics').replace('Medicine, Nursing and Health Sciences','Medicine & Health').replace('Art Design and Architecture','Art, Design & Architecture').replace('Pharmacy and Pharmaceutical Sciences','Pharmacy')}
function toast(text){$('#toast').textContent=text;$('#toast').style.display='block';setTimeout(()=>$('#toast').style.display='none',3000)}
function render(){
 const hasUniversity=Boolean(selectedUniversity);
 $('#catalogue').hidden=!hasUniversity;$('.demo-note').hidden=!hasUniversity;$('.contribute').hidden=!hasUniversity;$('#handbook-link').hidden=!hasUniversity;
 $('#write').disabled=!hasUniversity;$('#write').title=hasUniversity?'':'Choose a university first';
 if(!hasUniversity)return;
 $('#selected-university').textContent='Browsing '+universities.find(u=>u.id===selectedUniversity).name;

 reviewIndex=new Map();for(const r of allReviews()){if(!reviewIndex.has(r.unit))reviewIndex.set(r.unit,[]);reviewIndex.get(r.unit).push(r)}
 const university=universities.find(u=>u.id===selectedUniversity)||universities[0];
 const scoped=catalogue.filter(u=>u.university===university.id);
 const report=coverage[university.id]||{};
 $('#coverage-note').textContent=`2026 catalogue · ${scoped.length.toLocaleString()} units imported. `+(report.status==='complete'?'All units discovered by this importer are loaded.':report.status==='running'?'Import in progress. Refresh to see newly imported units.':'Partial catalogue — additional units are still to be imported.')+(report.note?' '+report.note:'');
 $('#handbook-link').href=university.handbook;
 const faculties=['All faculties',...new Set(catalogue.filter(u=>u.university===selectedUniversity).map(u=>u.faculty))];
 $('#faculties').innerHTML=faculties.map(f=>`<button class="chip ${faculty===f?'active':''}" data-faculty="${esc(f)}" aria-pressed="${faculty===f}">${esc(shortFaculty(f))}</button>`).join('');
 const settings={explore:['YOUR NEXT SEMESTER STARTS HERE','Explore the possibilities'],leaderboard:['THE STUDENT FAVOURITES',university.short_name+'’s top 10 units'],saved:['A LITTLE PLANNING GOES A LONG WAY','Your saved units']};
 $('#section-eyebrow').textContent=settings[view][0];$('#section-title').innerHTML=esc(settings[view][1])+'<span>.</span>';
 document.querySelectorAll('.nav').forEach(n=>n.classList.toggle('active',n.dataset.view===view));
 $('#total-count').textContent=`${scoped.length.toLocaleString()} imported units · 2026`;
 let list=scoped.map(u=>({...u,...stats(u)}));
 if(view==='leaderboard')list=list.filter(u=>u.count>0).sort((a,b)=>b.rating-a.rating||b.count-a.count||a.code.localeCompare(b.code)).slice(0,10).map((u,i)=>({...u,rank:i+1}));
 else list.sort($('#sort').value==='code'?(a,b)=>a.code.localeCompare(b.code):$('#sort').value==='rating'?(a,b)=>b.rating-a.rating||b.count-a.count:(a,b)=>b.count-a.count||b.rating-a.rating);
 list=list.filter(u=>(faculty==='All faculties'||u.faculty===faculty)&&`${u.code} ${u.name}`.toLowerCase().includes(query.toLowerCase())&&(view!=='saved'||saved.has(u.id)));
 $('#sort').disabled=view==='leaderboard';$('#rank-note').textContent=view==='leaderboard'?'Average stars · ties broken by review count':'A little insight goes a long way.';
 $('#result-count').textContent=`${list.length} ${list.length===1?'unit':'units'}${demo?' · includes demo ratings':''}`;
 $('#load-more').hidden=list.length<=visibleCount;
 $('#units').innerHTML=list.length?list.slice(0,visibleCount).map(u=>{const c=colours[faculties.indexOf(u.faculty)%colours.length];return `<article class="card" style="--tint:${c[0]};--tone:${c[1]}"><div class="card-top"><span class="faculty-tag">${u.rank?`<span class="rank">#${u.rank}</span>`:''}${esc(shortFaculty(u.faculty))}</span><button class="bookmark ${saved.has(u.id)?'saved':''}" data-save="${esc(u.id)}" aria-label="${saved.has(u.id)?'Unsave':'Save'} ${esc(u.code)}" aria-pressed="${saved.has(u.id)}">${bookmark}</button></div><div class="code">${esc(u.code)}</div><button class="unit-title" data-unit="${esc(u.id)}">${esc(u.name)}</button><div class="rating">${u.count?`${u.rating.toFixed(1)} ${stars(u.rating)} <small>(${u.count} ${u.count===1?'review':'reviews'})</small>`:'<small>No reviews yet · be the first</small>'}</div><div class="card-bottom"><span>${esc(u.year)} handbook <span>·</span> ${u.credits?esc(u.credits)+(Number(u.credits)===1?' credit point':' credit points'):'Credits not listed'}</span><button data-unit="${esc(u.id)}">Explore unit ↗</button></div></article>`}).join(''):`<div class="empty"><h3>${view==='saved'?'Your next semester, bookmarked.':view==='leaderboard'?'The leaderboard starts with you.':'No matching units yet.'}</h3><p>${view==='saved'?'Tap the bookmark on a unit to save it here.':view==='leaderboard'?'Write the first review to give a unit its place.':'Try a different search or faculty. Catalogue coverage is shown above.'}</p></div>`;
}
function detail(id){selected=id;const u=catalogue.find(u=>u.id===id),s=stats(u),r=allReviews().filter(r=>r.unit===id);$('#detail-content').innerHTML=`<div class="eyebrow">${esc(shortFaculty(u.faculty))} · ${esc(u.code)}</div><h2>${esc(u.name)}</h2><div class="rating">${s.count?s.rating.toFixed(1)+' '+stars(s.rating)+` <small>${s.count} ${s.count===1?'review':'reviews'}</small>`:'No reviews yet'}</div><p class="detail-description">${esc(u.description||'Visit the official handbook for the full unit description.')}</p><p class="muted">${esc(u.credits)} credit points · ${esc(u.year)} handbook</p><div class="detail-actions"><button class="primary" id="detail-review">Review this unit ↗</button><a href="${esc(u.source)}" target="_blank" rel="noreferrer">View official handbook ↗</a></div><h3>Student experiences</h3>${r.length?r.map(r=>`<article class="review-item"><div class="review-head"><strong>${esc(r.author)} ${r.demo?'· Sample review':''}</strong>${stars(r.rating)}</div><small>Taken: ${esc(r.semester)}${r.year ? `, ${esc(r.year)}` : ''}</small><p>${esc(r.body)}</p></article>`).join(''):'<p class="muted">Taken this unit? Tell the next student what to expect.</p>'}`;$('#detail-review').onclick=()=>openReview(id);if(!$('#detail').open)$('#detail').showModal()}
function openReview(id){$('#detail').close();$('#review-form').reset();$('#review-year').max=new Intl.DateTimeFormat('en',{year:'numeric',timeZone:'Australia/Melbourne'}).format(new Date());$('#form-error').textContent='';$('#review-unit').innerHTML=catalogue.filter(u=>u.university===selectedUniversity).sort((a,b)=>a.code.localeCompare(b.code)).map(u=>`<option value="${esc(u.id)}">${esc(u.code)} — ${esc(u.name)}</option>`).join('');if(id)$('#review-unit').value=id;$('#rating-input').innerHTML=[1,2,3,4,5].map(n=>`<label><input type="radio" name="rating" value="${n}" required aria-label="${n} ${n===1?'star':'stars'}"><span aria-hidden="true">★</span></label>`).join('');$('#review-dialog').showModal()}
$('#rating-input').onchange=e=>document.querySelectorAll('.rating-input label').forEach((l,i)=>l.classList.toggle('selected',i<Number(e.target.value)));
$('#review-form').onsubmit=async e=>{
 e.preventDefault();const button=$('.submit');button.disabled=true;button.textContent='Saving…';
 try{
  const data=Object.fromEntries(new FormData(e.target));data.rating=Number(data.rating);data.year=Number(data.year);data.author=data.author.trim();data.body=data.body.trim();
  if(!validReview(data))throw Error('Please enter a valid name, rating, year, teaching period, and a review of 20–2,000 characters.');
  if(apiBase){await readJSON(new URL('reviews',apiBase),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});reviews=await readJSON(new URL('reviews',apiBase))}
  else{const updated=[{...data,id:crypto.randomUUID(),created:new Date().toISOString()},...readBrowserReviews()];try{localStorage.setItem(reviewStorageKey,JSON.stringify(updated))}catch{throw Error('This browser could not save your review. Check storage permissions or available space.')}reviews=updated}
  $('#review-dialog').close();demo=false;$('#demo').checked=false;render();detail(data.unit);toast(apiBase?'Review published. Thanks for passing it on!':'Review saved in this browser only.');
 }catch(err){$('#form-error').textContent=err.message||'Could not save. Please try again.'}
 finally{button.disabled=false;button.textContent=submitLabel}
};
document.addEventListener('click',e=>{const unit=e.target.closest('[data-unit]'),save=e.target.closest('[data-save]'),filter=e.target.closest('[data-faculty]'),nav=e.target.closest('[data-view]');const uni=e.target.closest('[data-university]');if(uni){selectedUniversity=uni.dataset.university;switchUniversity();renderUniversityFinder();$('.catalogue').scrollIntoView({behavior:'smooth'})}if(unit)detail(unit.dataset.unit);if(save){const id=save.dataset.save;saved.has(id)?saved.delete(id):saved.add(id);try{localStorage.setItem('unitclub-saved',JSON.stringify([...saved]))}catch{toast('Browser storage unavailable; saved for this session.')}render()}if(filter){faculty=filter.dataset.faculty;visibleCount=24;render()}if(nav){e.preventDefault();if(!selectedUniversity){$('#universities').scrollIntoView({behavior:'smooth'});$('#university-search').focus();return}visibleCount=24;view=nav.dataset.view;faculty='All faculties';query='';$('#search').value='';render();$('.catalogue').scrollIntoView({behavior:'smooth'})}});
$('#write').onclick=$('#contribute').onclick=()=>openReview();$('#search').oninput=e=>{query=e.target.value;visibleCount=24;render()};$('#sort').onchange=render;$('#demo').onchange=e=>{demo=e.target.checked;render()};
function switchUniversity(){faculty='All faculties';query='';$('#search').value='';visibleCount=24;render()}
$('#load-more').onclick=()=>{visibleCount+=24;render()};
document.querySelectorAll('dialog .close').forEach(b=>b.onclick=()=>b.closest('dialog').close());document.querySelectorAll('dialog').forEach(d=>d.addEventListener('click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close()}}));
document.addEventListener('keydown',e=>{if((e.metaKey||e.ctrlKey)&&e.key==='k'){e.preventDefault();$(selectedUniversity?'#search':'#university-search').focus()}});
(async()=>{
 try{
  const data=await readJSON(apiBase?new URL('catalog',apiBase):new URL('./data/catalog.json',document.baseURI));
  catalogue=data.units;universities=data.universities;coverage=data.coverage||{};
  setupUniversityFinder();
  if(apiBase){reviews=await readJSON(new URL('reviews',apiBase));$('#review-storage-label').textContent='Community reviews';$('#review-storage-note').textContent='Reviews are shared through the connected server.';$('#form-storage-note').textContent='Your review will be saved on the connected server.'}
  else{try{reviews=readBrowserReviews()}catch{reviews=[];toast('Browser review storage is unavailable. Saving may be disabled by your browser.')}}
  $('.submit').textContent=submitLabel;const requested=catalogue.find(u=>u.id===new URLSearchParams(location.search).get('unit'));if(requested)selectedUniversity=requested.university;render();if(requested)detail(requested.id);
 }catch(e){$('#units').innerHTML='<div class="empty"><h3>Could not load the catalogue.</h3><p>Refresh the page or try again later. For local previews, serve the project over HTTP.</p></div>';$('#write').disabled=true;$('#contribute').disabled=true}
})();

function setupUniversityFinder(){
 const countries=[...new Set(universities.flatMap(u=>(u.locations||[]).map(l=>l.country)))].sort((a,b)=>a.localeCompare(b));
 $('#university-country').innerHTML='<option value="">All countries</option>'+countries.map(c=>`<option value="${esc(c)}">${esc(c)}</option>`).join('');
 $('#university-search').oninput=()=>{universityPage=0;renderUniversityFinder()};
 $('#university-country').onchange=()=>{const country=$('#university-country').value;const cities=[...new Set(universities.flatMap(u=>(u.locations||[]).filter(l=>l.country===country).map(l=>l.city)))].sort((a,b)=>a.localeCompare(b));$('#university-city').innerHTML='<option value="">All cities</option>'+cities.map(c=>`<option value="${esc(c)}">${esc(c)}</option>`).join('');$('#university-city').disabled=!country;universityPage=0;renderUniversityFinder()};
 $('#university-city').onchange=()=>{universityPage=0;renderUniversityFinder()};
 $('#university-clear').onclick=()=>{$('#university-search').value='';$('#university-country').value='';$('#university-country').onchange();$('#university-search').focus()};
 $('#university-prev').onclick=()=>{universityPage--;renderUniversityFinder()};$('#university-next').onclick=()=>{universityPage++;renderUniversityFinder()};
 renderUniversityFinder();
}
function renderUniversityFinder(){
 const query=$('#university-search').value,country=$('#university-country').value,city=$('#university-city').value;
 const active=query.trim()||country||city;
 if(!active){$('#university-result-count').textContent='Enter a university name or choose a country to get started.';$('#university-results').innerHTML='';$('#university-pagination').hidden=true;return}
 const result=UniversityDirectory.search(universities,{query,country,city,page:universityPage});universityPage=result.page;
 $('#university-result-count').textContent=result.total?`${result.total.toLocaleString()} ${result.total===1?'university':'universities'} found`:'No matching universities. Try another name or clear your filters.';
 $('#university-results').innerHTML=result.items.map(u=>`<button class="university-result ${u.id===selectedUniversity?'selected':''}" data-university="${esc(u.id)}" aria-pressed="${u.id===selectedUniversity}"><span><strong>${esc(u.name)}</strong><small>${esc((u.locations||[]).filter(l=>!country||l.country===country).map(l=>l.city+', '+l.country).join(' · ')||u.location||'Location not listed')}</small></span><span>${u.id===selectedUniversity?'Selected ✓':'View units ↗'}</span></button>`).join('');
 $('#university-pagination').hidden=result.pages<=1;$('#university-prev').disabled=result.page===0;$('#university-next').disabled=result.page>=result.pages-1;$('#university-page').textContent=`Page ${result.page+1} of ${result.pages}`;
}

// Reflect bookmark changes made on the separate Saved Units page.
window.addEventListener('storage',e=>{if(e.key==='unitclub-saved'||e.key===null){try{const items=JSON.parse(localStorage.getItem('unitclub-saved')||'[]');if(Array.isArray(items)){saved=new Set(items);render()}}catch{}}});
window.addEventListener('pageshow',e=>{if(e.persisted){try{const items=JSON.parse(localStorage.getItem('unitclub-saved')||'[]');if(Array.isArray(items)){saved=new Set(items);render()}}catch{}}});
