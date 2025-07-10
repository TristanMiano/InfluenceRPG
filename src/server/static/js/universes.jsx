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

function selectUniverse(universe) {
  drawPlaceholder(universe.name);
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

document.addEventListener('DOMContentLoaded', () => {
  loadUniverses();
  document.getElementById('universe-search').addEventListener('input', filterUniverses);
});
