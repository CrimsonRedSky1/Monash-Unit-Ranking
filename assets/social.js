(async()=>{
 const A=window.LunchTableAccount,$=s=>document.querySelector(s),page=$('[data-social-page]').dataset.socialPage;
 const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const profileURL=name=>'./profile.html?username='+encodeURIComponent(name);
 const status=message=>$('#social-status').textContent=message;
 let catalog,scope='all',offset=0,profile,feedVersion=0;
 function uni(id){return catalog.universities.find(u=>u.id===id)?.name||id}
 function unitLink(id){const u=catalog.units.find(u=>u.id===id);return `<a href="./index.html?unit=${encodeURIComponent(id)}">${esc(u?u.code+' · '+u.name:id)}</a>`}
 function fields(form){const d=Object.fromEntries(new FormData(form));for(const key of ['enrolment_year','study_year','semester'])if(key in d)d[key]=Number(d[key]);return d}
 async function action(button,fn){button.disabled=true;status('');try{await fn()}catch(e){status(e.message)}finally{button.disabled=false}}
 function person(u){return `<div class="social-person"><span class="social-avatar" aria-hidden="true">${esc(u.username[0].toUpperCase())}</span><div><a href="${profileURL(u.username)}"><strong>@${esc(u.username)}</strong></a><p>${esc(uni(u.university))}</p><p>Year ${u.study_year} Semester ${u.semester} · ${u.followers} followers</p></div></div>`}
 function populateFields(){document.querySelectorAll('select[name="university"]').forEach(el=>{el.innerHTML='<option value="">Choose your university</option>'+catalog.universities.map(u=>`<option value="${esc(u.id)}">${esc(u.name)}</option>`).join('')});document.querySelectorAll('[name="enrolment_year"]').forEach(el=>el.max=new Intl.DateTimeFormat('en',{year:'numeric',timeZone:'Australia/Melbourne'}).format(new Date()))}
 async function feed(append=false){const version=++feedVersion;const data=await A.request(`feed?scope=${scope}&offset=${offset}`);if(version!==feedVersion)return;const html=data.items.map(r=>`<article class="social-item"><a href="${profileURL(r.username)}"><strong>@${esc(r.username)}</strong></a><span class="social-meta"> ${r.kind==='review'?'reviewed':'recommends'}</span><h3>${unitLink(r.unit)}</h3>${r.kind==='review'?`<div aria-label="${r.rating} out of 5 stars">${'★'.repeat(r.rating)}${'☆'.repeat(5-r.rating)} <span class="social-meta">Taken ${esc(r.semester)}, ${r.year}</span></div>`:''}<p>${esc(r.content)}</p></article>`).join('');if(append)$('#feed').insertAdjacentHTML('beforeend',html);else $('#feed').innerHTML=html||'<div class="social-panel">No posts yet. Explore units to write a review, or visit your profile to recommend one.</div>';$('#more').hidden=!data.has_more;offset+=data.items.length}
 let searchVersion=0;
 async function people(){const version=++searchVersion;const data=await A.request('people?q='+encodeURIComponent($('#people-query').value));if(version===searchVersion)$('#people').innerHTML=data.users.map(person).join('')||'<p>No matching students yet.</p>'}
 function recommendationOptions(){const query=$('#unit-query').value.toLowerCase().trim();const matches=catalog.units.filter(u=>(u.code+' '+u.name+' '+uni(u.university)).toLowerCase().includes(query)).slice(0,50);$('#recommend-unit').innerHTML=matches.map(u=>`<option value="${esc(u.id)}">${esc(u.code+' · '+u.name+' — '+uni(u.university))}</option>`).join('');if(!matches.length)$('#recommend-unit').innerHTML='<option value="">No matching units</option>'}
 async function renderProfile(){
  const name=new URLSearchParams(location.search).get('username')||A.state.user?.username;
  if(!name){$('#profile-content').innerHTML='<h1>Your profile starts here.</h1><a class="primary" href="./account.html">Sign in or create an account</a>';return}
  profile=await A.request('profile?username='+encodeURIComponent(name));const own=profile.id===A.state.user?.id;
  document.title='@'+profile.username+' — LunchTable';
  $('#profile-content').innerHTML=`<div class="social-profile-head"><span class="social-avatar" aria-hidden="true">${esc(profile.username[0].toUpperCase())}</span><div><div class="eyebrow">STUDENT PROFILE</div><h1>@${esc(profile.username)}</h1><p>${esc(uni(profile.university))}</p><p>Enrolled ${profile.enrolment_year} · <strong>Year ${profile.study_year} Semester ${profile.semester}</strong></p></div></div><p>${esc(profile.bio)}</p><p class="social-meta">Study details are self-reported.</p><div class="social-counts">${['followers','following'].map(key=>`<details><summary><strong>${profile[key]}</strong> ${key}</summary>${profile[key+'_users'].map(u=>`<a href="${profileURL(u.username)}">@${esc(u.username)}</a>`).join('')||'<p>None yet.</p>'}${profile[key]>100?'<p>First 100 shown.</p>':''}</details>`).join('')}</div><div class="social-actions">${own?'<button class="secondary" id="edit-toggle">Edit profile</button><a class="primary" href="./index.html#universities">Write a review</a>':`<button class="primary" id="follow">${profile.is_following?'Unfollow':'Follow'}</button>`}</div><div class="social-grid"><section><h2>Reviews <span class="social-meta">${profile.reviews.length}</span></h2>${profile.reviews.map(r=>`<article class="social-item"><h3>${unitLink(r.unit)}</h3><div>${'★'.repeat(r.rating)}${'☆'.repeat(5-r.rating)}</div><p class="social-meta">Taken ${esc(r.semester)}, ${r.year}</p><p>${esc(r.body)}</p></article>`).join('')||'<p>No reviews yet.</p>'}</section><section><h2>Recommendations</h2>${profile.recommendations.map(r=>`<article class="social-item"><h3>${unitLink(r.unit)}</h3><p>${esc(r.note)}</p>${own?`<button class="secondary" data-remove="${esc(r.unit)}">Remove recommendation</button>`:''}</article>`).join('')||'<p>No recommendations yet.</p>'}</section></div>`;
  $('#recommend-panel').hidden=!own;
  if(own){for(const [key,value]of Object.entries(profile)){const field=$('#edit').elements.namedItem(key);if(field)field.value=value}$('#edit-toggle').onclick=()=>{$('#profile-edit').hidden=!$('#profile-edit').hidden};recommendationOptions()}
  else{$('#profile-edit').hidden=true;$('#follow').onclick=e=>action(e.currentTarget,async()=>{if(!A.state.user){location.href='./account.html';return}await A.request('follow',{username:profile.username,follow:!profile.is_following});await renderProfile()})}
  document.querySelectorAll('[data-remove]').forEach(b=>b.onclick=()=>action(b,async()=>{await A.request('recommendations',{unit:b.dataset.remove,remove:true});await renderProfile()}));
 }
 try{
  await A.ready;
  if(!A.enabled){status('This static preview cannot create shared accounts. Start the LunchTable Python server to use profiles, follows and community posts.');document.querySelectorAll('main form,main button,main input').forEach(el=>{if(el.tagName==='FORM')el.hidden=true;else el.disabled=true});return}
  if(A.state.error)throw Error(A.state.error);
  catalog=await A.request('catalog');populateFields();
  if(page==='account'){
   if(A.state.user){location.replace(profileURL(A.state.user.username));return}
   ['signup','login'].forEach(id=>$('#'+id).onsubmit=e=>{e.preventDefault();action(e.submitter,async()=>{A.update(await A.request(id,fields(e.target)));location.href=profileURL(A.state.user.username)})});
  }else if(page==='community'){
   await Promise.all([feed(),people()]);
   let timer;$('#people-query').oninput=()=>{clearTimeout(timer);timer=setTimeout(()=>people().catch(e=>status(e.message)),200)};
   document.querySelectorAll('[data-scope]').forEach(b=>b.onclick=()=>action(b,async()=>{scope=b.dataset.scope;offset=0;document.querySelectorAll('[data-scope]').forEach(el=>el.setAttribute('aria-pressed',String(el===b)));$('#feed').innerHTML='';$('#more').hidden=true;await feed()}));
   $('#more').onclick=e=>action(e.currentTarget,()=>feed(true));
  }else{
   await renderProfile();$('#unit-query').oninput=recommendationOptions;
   $('#edit').onsubmit=e=>{e.preventDefault();action(e.submitter,async()=>{await A.request('profile',fields(e.target));await renderProfile();$('#profile-edit').hidden=true;status('Profile updated.')})};
   $('#recommend').onsubmit=e=>{e.preventDefault();action(e.submitter,async()=>{await A.request('recommendations',fields(e.target));e.target.reset();await renderProfile();status('Recommendation saved.')})};
   $('#logout').onclick=e=>action(e.currentTarget,async()=>{await A.request('logout',{});location.href='./account.html'});
  }
 }catch(e){status(e.message)}
})();
