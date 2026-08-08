const scanners=["hourly","daily","eod","stockbee"];
const labels={hourly:"Hourly",daily:"Daily",eod:"High Volume",stockbee:"Stockbee"};
document.querySelectorAll("#tabs button").forEach(b=>b.onclick=()=>{
 document.querySelectorAll("#tabs button").forEach(x=>x.classList.remove("active"));
 document.querySelectorAll(".tab").forEach(x=>x.classList.remove("active"));
 b.classList.add("active");document.getElementById(b.dataset.tab).classList.add("active");
});
function esc(v){return String(v??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]))}
function table(rows){
 if(!rows.length)return '<div class="empty">No results in this run.</div>';
 const keys=[...new Set(rows.flatMap(r=>Object.keys(r)))];
 const preferred=["Scan","Ticker","Universe","Updated","Price","Close","Change %","Volume","Avg Volume 20","Volume / Avg Volume 20","sales_pct","eps_pct","mktcap_b","ti65","ext_atr","adr_pct"];
 const cols=[...preferred.filter(k=>keys.includes(k)),...keys.filter(k=>!preferred.includes(k))].slice(0,12);
 return `<table class="table"><thead><tr>${cols.map(k=>`<th>${esc(k)}</th>`).join("")}</tr></thead><tbody>${rows.map(r=>`<tr>${cols.map(k=>`<td class="${k.toLowerCase().includes("ticker")?"ticker":""}">${esc(r[k])}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
}
function render(id,payload){
 const el=document.getElementById(id+"-data");
 if(!payload){el.innerHTML='<div class="empty">No data yet. Run the corresponding GitHub Action once.</div>';return}
 const rows=payload.rows||[];
 const by={};
 rows.forEach(r=>{const k=r.Scan||r.scan||r.Universe||r.market||"Results";(by[k]??=[]).push(r)});
 el.innerHTML=Object.entries(by).map(([k,v])=>`<div class="group"><h3>${esc(k)} <span>(${v.length})</span></h3><div class="meta">Updated ${esc(payload.updated_at||"")}</div>${table(v)}</div>`).join("")||'<div class="empty">No hits.</div>';
}
async function load(){
 const results=await Promise.all(scanners.map(async s=>[s,await fetch(`data/${s}.json?${Date.now()}`).then(r=>r.ok?r.json():null).catch(()=>null)]));
 let latest=null;
 results.forEach(([s,p])=>{render(s,p);if(p&&(!latest||p.updated_at>latest))latest=p.updated_at});
 document.getElementById("updated").textContent=latest?`Latest update: ${new Date(latest).toLocaleString()}`:"No scan data yet";
}
load();
setInterval(load,5*60*1000);
