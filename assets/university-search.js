/* Bounded directory results; independent of catalogue size and university names. */
(function(root){
 const normalize=value=>String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase().trim();
 function search(items,{query='',country='',city='',page=0,pageSize=8}={}){
  const terms=normalize(query).split(/\s+/).filter(Boolean);
  const matches=items.filter(u=>{
   const locations=u.locations||[];
   const place=!country&&!city||locations.some(l=>(!country||l.country===country)&&(!city||l.city===city));
   const text=normalize([u.name,u.short_name,...(u.aliases||[])].join(' '));
   return place&&terms.every(term=>text.includes(term));
  }).sort((a,b)=>a.name.localeCompare(b.name));
  const pages=Math.max(1,Math.ceil(matches.length/pageSize));page=Math.min(Math.max(0,page),pages-1);
  return {items:matches.slice(page*pageSize,(page+1)*pageSize),total:matches.length,page,pages};
 }
 root.UniversityDirectory={search};
 if(typeof module!=='undefined')module.exports=root.UniversityDirectory;
})(typeof window!=='undefined'?window:globalThis);
