const C=['#38bdf8','#fb923c','#4ade80','#f87171','#c084fc','#facc15','#2dd4bf','#f472b6'];
const svg=document.querySelector('#map'),NS='http://www.w3.org/2000/svg';let selected=null,step=0,timer=null;
const allPoints=[...D.aoi,...D.noFly.flat(),...D.cells.flatMap(c=>c.vertices),...D.nodes.flatMap(n=>n.trajectory)];
const xs=allPoints.map(p=>p[0]),ys=allPoints.map(p=>p[1]),pad=D.cellWidth*.8,minX=Math.min(...xs)-pad,maxX=Math.max(...xs)+pad,minY=Math.min(...ys)-pad,maxY=Math.max(...ys)+pad;
svg.setAttribute('viewBox',`${minX} ${-maxY} ${maxX-minX} ${maxY-minY}`);
const E=(tag,attrs={})=>{const e=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);return e};
const pts=a=>a.map(p=>`${p[0]},${-p[1]}`).join(' ');
svg.append(E('polygon',{points:pts(D.aoi),class:'aoi'}));
const noFly=E('g',{id:'noFly'});D.noFly.forEach(z=>noFly.append(E('polygon',{points:pts(z),class:'nofly'})));svg.append(noFly);
const cells=E('g',{id:'cells'});D.cells.forEach(c=>cells.append(E('polygon',{points:pts(c.vertices),fill:C[c.owner%C.length],class:'cell',id:`cell-${c.id}`,'data-owner':c.owner})));svg.append(cells);
const routes=E('g',{id:'routes'});D.nodes.forEach(n=>routes.append(E('polyline',{points:pts(n.trajectory),stroke:C[n.index%C.length],class:'route',id:`route-${n.index}`,'data-owner':n.index})));svg.append(routes);
const nodeLayer=E('g',{id:'nodeLayer'});D.nodes.forEach(n=>nodeLayer.append(E('circle',{cx:n.start[0],cy:-n.start[1],r:D.cellWidth*.18,fill:C[n.index%C.length],class:'node','data-owner':n.index})));svg.append(nodeLayer);
const cursorLayer=E('g',{id:'cursorLayer'});D.nodes.forEach(n=>cursorLayer.append(E('circle',{id:`cursor-${n.index}`,r:D.cellWidth*.15,class:'cursor',fill:C[n.index%C.length]})));svg.append(cursorLayer);
document.querySelector('#subtitle').textContent=`${D.name} · ${D.cells.length} cells · ${D.nodes.length} nodes · ${D.profile}${D.randomSeed===null?'':` · seed ${D.randomSeed}`}`;
const metricData=[['Cell',D.cells.length],['Conflict',D.conflicts],['Makespan',`${D.makespan.toFixed(2)} m`],['총 거리',`${D.totalDistance.toFixed(2)} m`]];
document.querySelector('#metrics').innerHTML=metricData.map(x=>`<div class="metric"><b>${x[1]}</b><span>${x[0]}</span></div>`).join('');
document.querySelector('#nodes').innerHTML=D.nodes.map(n=>`<div class="node-row" data-testid="node-${n.index}" data-index="${n.index}"><i class="dot" style="background:${C[n.index%C.length]}"></i><div><b>${n.id}</b><br><small>${n.cells} cells · ${n.distance.toFixed(2)} m</small><div class="movement" id="node-status-${n.index}">대기 · (${n.start[0].toFixed(2)}, ${n.start[1].toFixed(2)})</div><div class="progressbar"><i id="bar-${n.index}"></i></div></div><span>${n.waypoints.length}</span></div>`).join('');
const maxSteps=Math.max(...D.nodes.map(n=>n.trajectory.length));
function applyFilter(){document.querySelectorAll('[data-owner]').forEach(e=>e.classList.toggle('dim',selected!==null&&+e.dataset.owner!==selected));document.querySelectorAll('.node-row').forEach(e=>e.classList.toggle('active',selected!==null&&+e.dataset.index===selected))}
function positionAt(n,t){const end=n.trajectory.length-1,clamped=Math.min(t,end),i=Math.floor(clamped),f=clamped-i,a=n.trajectory[i],b=n.trajectory[Math.min(i+1,end)];return{p:[a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f],i,f}}
function cumulative(n,t){const s=positionAt(n,t);let d=0;for(let i=1;i<=s.i;i++){const a=n.trajectory[i-1],b=n.trajectory[i];d+=Math.hypot(b[0]-a[0],b[1]-a[1])}if(s.f&&s.i<n.trajectory.length-1){const a=n.trajectory[s.i],b=n.trajectory[s.i+1];d+=Math.hypot(b[0]-a[0],b[1]-a[1])*s.f}return d}
function drawStep(){
 document.querySelectorAll('.visited').forEach(e=>e.classList.remove('visited'));
 const active=selected===null?D.nodes:D.nodes.filter(n=>n.index===selected);
 D.nodes.forEach(n=>{
  const isActive=active.some(a=>a.index===n.index),s=positionAt(n,step),p=s.p,cursor=document.querySelector(`#cursor-${n.index}`),motionIndex=Math.min(s.i,n.motionCellIds.length-1);
  cursor.setAttribute('cx',p[0]);cursor.setAttribute('cy',-p[1]);cursor.setAttribute('visibility',isActive?'visible':'hidden');
  if(isActive){const covered=new Set(n.cellIds);n.motionCellIds.slice(0,Math.max(0,s.i)).filter(id=>covered.has(id)).forEach(id=>document.querySelector(`#cell-${id}`)?.classList.add('visited'))}
  const returning=motionIndex>=n.returnMotionIndex||s.i>=n.motionCellIds.length,target=s.i>=n.motionCellIds.length?'시작점':n.motionCellIds[motionIndex],isCoverage=n.cellIds.includes(target),mode=returning?'복귀':step===0?'대기':isCoverage?'탐색':'경유',dist=cumulative(n,step),pct=n.trajectory.length>1?Math.min(step,n.trajectory.length-1)/(n.trajectory.length-1)*100:100;
  document.querySelector(`#node-status-${n.index}`).textContent=`${mode} · (${p[0].toFixed(2)}, ${p[1].toFixed(2)}) · 다음 ${target} · ${dist.toFixed(2)} m`;document.querySelector(`#bar-${n.index}`).style.width=`${pct}%`;
 });
 document.querySelector('#movement').innerHTML=active.map(n=>{const s=positionAt(n,step),p=s.p;return`<div style="margin:5px 0;color:${C[n.index%C.length]}"><b>${n.id}</b> — 인접 이동 ${s.i}/${n.trajectory.length-1}, 위치 (${p[0].toFixed(2)}, ${p[1].toFixed(2)}), 누적 ${cumulative(n,step).toFixed(2)} m</div>`}).join('');
 document.querySelector('#step').textContent=`${step.toFixed(1)} / ${selected===null?maxSteps-1:D.nodes[selected].trajectory.length-1}`;
}
function stop(){if(timer){clearInterval(timer);timer=null}document.querySelector('#play').textContent='▶ 재생'}
function play(){if(timer){stop();return}document.querySelector('#play').textContent='Ⅱ 일시정지';timer=setInterval(()=>{const limit=selected===null?maxSteps-1:D.nodes[selected].trajectory.length-1;if(step>=limit){step=limit;drawStep();stop();return}step=Math.min(limit,step+(+document.querySelector('#speed').value));drawStep()},50)}
document.querySelector('#play').onclick=play;document.querySelector('#reset').onclick=()=>{stop();step=0;drawStep()};document.querySelector('#speed').onchange=()=>{if(timer){stop();play()}};
document.querySelector('#showCells').onchange=e=>cells.style.display=e.target.checked?'':'none';document.querySelector('#showRoutes').onchange=e=>routes.style.display=e.target.checked?'':'none';document.querySelector('#showNoFly').onchange=e=>noFly.style.display=e.target.checked?'':'none';
document.querySelectorAll('.node-row').forEach(e=>e.onclick=()=>{selected=selected===+e.dataset.index?null:+e.dataset.index;step=0;stop();applyFilter();drawStep()});applyFilter();drawStep();
