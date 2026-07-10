const NS = 'http://www.w3.org/2000/svg';
const metricSvg = document.querySelector('#metricMap');
const nnSvg = document.querySelector('#nnMap');
const nodeSelect = document.querySelector('#nodeSelect');

function svgEl(tag, attrs = {}) {
  const el = document.createElementNS(NS, tag);
  for (const [key, value] of Object.entries(attrs)) {
    el.setAttribute(key, value);
  }
  return el;
}

function formatPoint(point) {
  return `${point[0]},${-point[1]}`;
}

function distance(a, b) {
  return Math.hypot(b[0] - a[0], b[1] - a[1]);
}

function routeDistance(points) {
  return points.slice(1).reduce((sum, point, index) => sum + distance(points[index], point), 0);
}

function routeFor(node, plannerKey) {
  return plannerKey === 'metric' ? node.metric.trajectory : node.nn.trajectory;
}

function plannerMetrics(node, plannerKey) {
  const route = routeFor(node, plannerKey);
  if (route.length < 2) {
    return { approach: 0, middle: 0, return: 0, total: 0 };
  }
  return {
    approach: distance(route[0], route[1]),
    middle: route.length > 3 ? routeDistance(route.slice(1, -1)) : 0,
    return: distance(route[route.length - 2], route[route.length - 1]),
    total: routeDistance(route),
  };
}

function renderMetricCards(target, metrics) {
  target.innerHTML = [
    ['first approach', metrics.approach],
    ['middle segment', metrics.middle],
    ['final return', metrics.return],
  ].map(([label, value]) => `<div class="leg"><span>${label}</span><b>${value.toFixed(3)} m</b></div>`).join('');
}

function renderRoute(svg, node, plannerKey, isBaseline) {
  svg.innerHTML = '';
  const route = routeFor(node, plannerKey);
  const geometry = [...D.aoi, ...D.noFly.flat(), ...D.cells.flatMap((cell) => cell.vertices), ...route];
  const xs = geometry.map((point) => point[0]);
  const ys = geometry.map((point) => point[1]);
  const padding = D.cellWidth * 0.8;
  svg.setAttribute(
    'viewBox',
    `${Math.min(...xs) - padding} ${-(Math.max(...ys) + padding)} ${Math.max(...xs) - Math.min(...xs) + 2 * padding} ${Math.max(...ys) - Math.min(...ys) + 2 * padding}`,
  );

  svg.append(svgEl('polygon', { points: D.aoi.map(formatPoint).join(' '), class: 'aoi' }));

  const assignedCells = new Set(node.cellIds);
  for (const cell of D.cells) {
    svg.append(svgEl('polygon', {
      points: cell.vertices.map(formatPoint).join(' '),
      class: `cell ${assignedCells.has(cell.id) ? 'assigned' : ''}`,
    }));
  }

  for (const zone of D.noFly) {
    svg.append(svgEl('polygon', { points: zone.map(formatPoint).join(' '), class: 'nofly-area' }));
  }

  svg.append(svgEl('polyline', { points: route.map(formatPoint).join(' '), class: `route ${isBaseline ? 'nn' : ''}` }));

  const first = route[1] ?? route[0];
  const last = route.at(-2) ?? route[0];
  const markers = [
    [node.start, 'S', '#fff'],
    [first, '1', '#4ade80'],
    [last, 'L', '#fb7185'],
  ];
  for (const [point, label, fill] of markers) {
    svg.append(svgEl('circle', { cx: point[0], cy: -point[1], r: D.cellWidth * 0.2, fill, class: 'point' }));
    const text = svgEl('text', { x: point[0] + D.cellWidth * 0.18, y: -point[1] - D.cellWidth * 0.18, class: 'point-label' });
    text.textContent = label;
    svg.append(text);
  }
}

function setText(selector, text) {
  document.querySelector(selector).textContent = text;
}

function render() {
  const node = D.nodes.find((item) => item.id === nodeSelect.value);
  const metricMetrics = plannerMetrics(node, 'metric');
  const nnMetrics = plannerMetrics(node, 'nn');

  renderRoute(metricSvg, node, 'metric', false);
  renderRoute(nnSvg, node, 'nn', true);

  document.querySelector('#metricDistance').innerHTML = `selected route<b>${metricMetrics.total.toFixed(3)} m</b>`;
  document.querySelector('#nnDistance').innerHTML = `selected route<b>${nnMetrics.total.toFixed(3)} m</b>`;
  renderMetricCards(document.querySelector('#metricLegs'), metricMetrics);
  renderMetricCards(document.querySelector('#nnLegs'), nnMetrics);

  const delta = (nnMetrics.total - metricMetrics.total) / nnMetrics.total * 100;
  setText('#delta', `${delta >= 0 ? '−' : '+'}${Math.abs(delta).toFixed(2)}%`);
  setText('#finding', `Metric-TSP is ${Math.abs(delta).toFixed(2)}% ${delta >= 0 ? 'shorter' : 'longer'} than NN for ${node.id}.`);
  setText('#detail', 'Comparison uses the same grid-adjacent executable model with no-fly blocking.');
  setText('#orientationNote', 'Executable comparison only.');
}

for (const node of D.nodes) {
  nodeSelect.insertAdjacentHTML('beforeend', `<option value="${node.id}" ${node.id === 'node-01' ? 'selected' : ''}>${node.id} · ${node.cells} cells</option>`);
}

setText('#subtitle', `${D.name} · ${D.cells.length} cells · seed ${D.seed} · B=${D.bias}`);
nodeSelect.addEventListener('change', render);
render();
