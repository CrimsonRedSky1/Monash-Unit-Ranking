/* Deterministic fictional fixtures. Never persisted or submitted as student reviews. */
(function(root){
 function generate(units){
  const patterns=[[5],[...Array(32).fill(5),...Array(8).fill(4)],[5,5,5,4,4],[4,4],[5,3],[...Array(12).fill(5),...Array(8).fill(4)],[3,3,4,4,5],[2,3,3,4],[5,5,4],[4,4,4,4,4,4],[1,2,3],[5,4,5,4,5,4,5,4]];
  const bodies=['Fictional test review: I enjoyed the practical activities and found the weekly exercises useful.','Fictional test review: The concepts were interesting, though the workload took some planning.','Fictional test review: A mixed experience for me; some topics were more engaging than others.'];
  return [...new Set(units.map(u=>u.university))].sort().flatMap((university,ui)=>units.filter(u=>u.university===university).sort((a,b)=>a.code.localeCompare(b.code)).slice(0,12).flatMap((u,i)=>patterns[(i+ui)%patterns.length].map((rating,j)=>({id:`demo:${u.id}:${j}`,unit:u.id,rating,author:`Demo student ${j+1}`,body:bodies[j%3],year:2024+j%3,semester:j%2?'Semester 2':'Semester 1',created:'2026-01-01',demo:true}))));
 }
 root.LunchTableDemo={generate};if(typeof module!=='undefined')module.exports=root.LunchTableDemo;
})(typeof window!=='undefined'?window:globalThis);
