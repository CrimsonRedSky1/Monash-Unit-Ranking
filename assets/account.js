/* Same-origin account client. Session credentials stay in an HttpOnly cookie. */
window.LunchTableAccount=(()=>{
 const base=window.UNIT_CLUB_API_BASE?new URL(window.UNIT_CLUB_API_BASE,document.baseURI):null;
 const state={user:null,csrf:null};
 async function request(path,data){
  if(!base)throw Error('Accounts require the LunchTable server. This static preview cannot store shared profiles.');
  const response=await fetch(new URL(path,base),{credentials:'same-origin',...(data===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':state.csrf||''},body:JSON.stringify(data)})});
  const value=await response.json();if(!response.ok)throw Error(value.error||'Unable to complete request.');return value;
 }
 function update(value){Object.assign(state,value);const link=document.querySelector('[data-account-link]');if(link){link.textContent=state.user?'@'+state.user.username:'Sign in';link.href=state.user?'./profile.html?username='+encodeURIComponent(state.user.username):'./account.html'}}
 const ready=base?request('me').then(update).catch(e=>{state.error=e.message}):Promise.resolve();
 return {state,ready,request,update,enabled:!!base};
})();
