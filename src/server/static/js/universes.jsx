// src/server/static/js/universes.jsx

async function loadUniverses() {
  const list = document.getElementById('universe-list');
  list.innerHTML = '';
  try {
    const resp = await fetch('/api/universe/list');
    if (!resp.ok) throw new Error();
    const universes = await resp.json();
    universes.forEach(u => {
      const li = document.createElement('li');
      li.textContent = u.name;
      li.dataset.id = u.id;
      li.addEventListener('click', () => selectUniverse(u));
      list.appendChild(li);
    });
  } catch (e) {
    list.innerHTML = '<li>Error loading universes</li>';
  }
}

function filterUniverses() {
  const term = document.getElementById('universe-search').value.toLowerCase();
  document.querySelectorAll('#universe-list li').forEach(li => {
    li.style.display = li.textContent.toLowerCase().includes(term) ? '' : 'none';
  });
}

async function selectUniverse(universe) {
  const svg = d3.select('#sankey-diagram');
  svg.selectAll('*').remove();
  try {
    const [eventsResp, gamesResp] = await Promise.all([
      fetch(`/api/universe/${universe.id}/events`),
      fetch(`/api/universe/${universe.id}/games`)
    ]);
    if (!eventsResp.ok || !gamesResp.ok) throw new Error();
    const events = await eventsResp.json();
    const games = await gamesResp.json();
    drawSankey(universe.name, games, events);
  } catch (e) {
    drawPlaceholder(universe.name);
  }
}

function drawPlaceholder(name) {
  const svg = d3.select('#sankey-diagram');
  const width = parseInt(svg.style('width')) || 600;
  const height = parseInt(svg.attr('height')) || 400;
  svg.selectAll('*').remove();
  const colors = ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2'];
  for (let i = 0; i < 3; i++) {
    svg.append('rect')
      .attr('x', (i + 0.25) * width / 3)
      .attr('y', 0)
      .attr('width', width / 6)
      .attr('height', height)
      .attr('fill', colors[i % colors.length])
      .attr('opacity', 0.7);
  }
  svg.append('text')
    .attr('x', 10)
    .attr('y', 20)
    .text(`Sankey placeholder for ${name}`);
}

function drawSankey(name, games, events) {
  const svg = d3.select('#sankey-diagram');
  const width = parseInt(svg.style('width')) || 600;
  const height = parseInt(svg.attr('height')) || 400;
  svg.selectAll('*').remove();

  const nodes = [];
  const links = [];
  const nodeById = new Map();

  games.forEach(g => {
    const node = {
      id: g.id,
      name: g.name,
      time: new Date(g.created_at)
    };
    nodes.push(node);
    nodeById.set(g.id, node);
  });

  events.forEach(ev => {
    if (ev.event_type === 'branched_from') {
      const child = nodeById.get(ev.game_id);
      if (child) child.time = new Date(ev.event_time);
      const parent = nodeById.get(ev.event_payload.original_game_id);
      if (parent && child) {
        links.push({ source: parent.id, target: child.id, value: 1 });
      }
    } else if (ev.event_type === 'merger') {
      const target = nodeById.get(ev.game_id);
      if (target) target.time = new Date(ev.event_time);
      const fromIds = ev.event_payload.from_instance_ids || [];
      fromIds.forEach(src => {
        if (nodeById.has(src) && target) {
          links.push({ source: src, target: target.id, value: 1 });
        }
      });
    }
  });

  const times = Array.from(new Set(nodes.map(n => n.time.getTime())))
    .sort((a, b) => a - b)
    .map(t => new Date(t));
  const timeIndex = new Map(times.map((t, i) => [t.getTime(), i]));

  const sankeyGen = d3.sankey()
    .nodeId(d => d.id)
    .nodeWidth(8)
    .nodePadding(10)
    .nodeAlign(d => timeIndex.get(d.time.getTime()))
    .extent([[0, 0], [width, height]]);

  const graph = sankeyGen({ nodes: nodes.map(d => Object.assign({}, d)), links });

  const scale = d3.scaleTime()
    .domain(d3.extent(times))
    .range([0, height - sankeyGen.nodeWidth()]);

  svg.append('g')
    .attr('transform', 'translate(30,0)')
    .call(d3.axisLeft(scale).tickValues(times));

  graph.nodes.forEach(n => {
    const y = scale(n.time);
    n.y0 = y;
    n.y1 = y + sankeyGen.nodeWidth();
  });

  svg.append('g')
    .selectAll('path')
    .data(graph.links)
    .join('path')
    .attr('d', d3.sankeyLinkVertical())
    .attr('fill', 'none')
    .attr('stroke', '#888')
    .attr('stroke-width', 8)
    .attr('opacity', 0.6);

  svg.append('g')
    .selectAll('rect')
    .data(graph.nodes)
    .join('rect')
    .attr('x', d => d.x0)
    .attr('y', d => d.y0)
    .attr('width', d => d.x1 - d.x0)
    .attr('height', d => d.y1 - d.y0)
    .attr('fill', '#4e79a7')
    .attr('opacity', 0.8);

  svg.append('g')
    .selectAll('text')
    .data(graph.nodes)
    .join('text')
    .attr('x', d => d.x1 + 5)
    .attr('y', d => (d.y0 + d.y1) / 2)
    .attr('dy', '0.35em')
    .text(d => d.name)
    .style('font-size', '10px');
}

document.addEventListener('DOMContentLoaded', () => {
  loadUniverses();
  document.getElementById('universe-search').addEventListener('input', filterUniverses);
});
