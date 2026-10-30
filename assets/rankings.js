/* Five prior reviews at the catalogue-wide mean temper very small samples. */
(function(root){
 function rank(units,reviews,university=''){
  const ids=new Set(units.map(u=>u.id)),groups=new Map();let total=0,count=0;
  for(const r of reviews){if(!r||r.demo||!ids.has(r.unit)||!Number.isInteger(r.rating)||r.rating<1||r.rating>5)continue;const s=groups.get(r.unit)||{count:0,sum:0,fives:0};s.count++;s.sum+=r.rating;s.fives+=Number(r.rating===5);groups.set(r.unit,s);total+=r.rating;count++}
  const mean=count?total/count:0;
  return units.filter(u=>(!university||u.university===university)&&groups.has(u.id)).map(u=>{const s=groups.get(u.id);return {...u,count:s.count,fives:s.fives,rating:s.sum/s.count,score:(s.sum+5*mean)/(s.count+5)}}).sort((a,b)=>b.score-a.score||b.fives-a.fives||b.count-a.count||a.id.localeCompare(b.id)).slice(0,10);
 }
 root.LunchTableRankings={rank};if(typeof module!=='undefined')module.exports=root.LunchTableRankings;
})(typeof window!=='undefined'?window:globalThis);
