// ============================================================
// Home / Predict page logic
// ============================================================

const team1Select = document.getElementById('team1-select');
const team2Select = document.getElementById('team2-select');
const team1Badge = document.getElementById('team1-badge');
const team2Badge = document.getElementById('team2-badge');
const predictBtn = document.getElementById('predict-btn');
const errorMessage = document.getElementById('error-message');
const resultsSection = document.getElementById('results');
const factorGrid = document.getElementById('factor-grid');

let TEAMS_META = []; // filled from /api/teams-meta — [{name, short, color}, ...]

// Circle circumference for r=27 (matches the SVG in the HTML) — used for the ring animation
const RING_RADIUS = 27;
const RING_CIRCUMFERENCE = 2 * Math.PI * RING_RADIUS;

function findMeta(teamName) {
  return TEAMS_META.find((t) => t.name === teamName) || { short: '??', color: '#2F8FFF' };
}

function applyBadge(el, teamName) {
  const meta = findMeta(teamName);
  el.textContent = meta.short;
  el.style.background = meta.color;
}

async function init() {
  try {
    const res = await fetch('/api/teams-meta');
    TEAMS_META = await res.json();

    TEAMS_META.forEach((team, i) => {
      [team1Select, team2Select].forEach((select) => {
        const option = document.createElement('option');
        option.value = team.name;
        option.textContent = team.name;
        select.appendChild(option);
      });
    });

    if (TEAMS_META.length > 1) team2Select.value = TEAMS_META[1].name;

    // If we arrived here from the Teams page (e.g. /?team1=Mumbai%20Indians),
    // pre-select that team instead of the default first item.
    const params = new URLSearchParams(window.location.search);
    const preselected = params.get('team1');
    if (preselected && TEAMS_META.some((t) => t.name === preselected)) {
      team1Select.value = preselected;
      if (team2Select.value === preselected && TEAMS_META.length > 1) {
        team2Select.value = TEAMS_META.find((t) => t.name !== preselected).name;
      }
    }

    updateBadges();
  } catch (err) {
    showError('Could not load teams. Is the Flask server running?');
    console.error(err);
  }
}

function updateBadges() {
  applyBadge(team1Badge, team1Select.value);
  applyBadge(team2Badge, team2Select.value);
}

team1Select.addEventListener('change', updateBadges);
team2Select.addEventListener('change', updateBadges);

predictBtn.addEventListener('click', async () => {
  const team1 = team1Select.value;
  const team2 = team2Select.value;

  hideError();

  if (team1 === team2) {
    showError('Pick two different teams.');
    return;
  }

  predictBtn.disabled = true;
  predictBtn.textContent = 'Calculating...';

  try {
    const res = await fetch('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ team1, team2 }),
    });

    if (!res.ok) throw new Error('Prediction failed');
    const data = await res.json();
    renderResults(team1, team2, data);

  } catch (err) {
    showError('Something went wrong getting a prediction.');
    console.error(err);
  } finally {
    predictBtn.disabled = false;
    predictBtn.textContent = 'Predict Winner';
  }
});

function setRing(ringEl, pctEl, pct) {
  const offset = RING_CIRCUMFERENCE * (1 - pct / 100);
  // Set full offset first (empty ring), then animate to target on next frame
  ringEl.style.strokeDasharray = RING_CIRCUMFERENCE;
  ringEl.style.strokeDashoffset = RING_CIRCUMFERENCE;
  requestAnimationFrame(() => {
    ringEl.style.strokeDashoffset = offset;
  });
  pctEl.textContent = `${pct}%`;
}

function renderResults(team1, team2, data) {
  const pct1 = Math.round(data.team1_win_probability * 100);
  const pct2 = Math.round(data.team2_win_probability * 100);
  const meta1 = findMeta(team1);
  const meta2 = findMeta(team2);

  document.getElementById('result-badge-1').textContent = meta1.short;
  document.getElementById('result-badge-1').style.background = meta1.color;
  document.getElementById('result-name-1').textContent = meta1.short;
  document.getElementById('result-sub-1').textContent = team1.toUpperCase();

  document.getElementById('result-badge-2').textContent = meta2.short;
  document.getElementById('result-badge-2').style.background = meta2.color;
  document.getElementById('result-name-2').textContent = meta2.short;
  document.getElementById('result-sub-2').textContent = team2.toUpperCase();

  setRing(document.getElementById('ring-1'), document.getElementById('ring-pct-1'), pct1);
  setRing(document.getElementById('ring-2'), document.getElementById('ring-pct-2'), pct2);

  const card1 = document.getElementById('result-card-1');
  const card2 = document.getElementById('result-card-2');
  card1.classList.toggle('leading', pct1 >= pct2);
  card2.classList.toggle('leading', pct2 > pct1);

  const favourite = pct1 >= pct2 ? team1 : team2;
  document.getElementById('verdict-team').textContent = favourite;

  renderFactors(team1, team2, meta1, meta2, data.features || {});

  resultsSection.classList.add('visible');
}

function starRating(value, max = 10) {
  // Turns a numeric strength value into a 5-star display
  const stars = Math.max(0, Math.min(5, Math.round((value / max) * 5)));
  let html = '';
  for (let i = 0; i < 5; i++) {
    html += i < stars ? '&#9733;' : '<span class="dim">&#9733;</span>';
  }
  return html;
}

// Real feature values can sit on very different scales depending on how
// they were engineered (e.g. bowling strength ~0.07 vs batting strength ~80),
// so stars are shown RELATIVE to whichever of the two compared teams is
// higher, rather than against a fixed absolute max. This stays meaningful
// no matter what scale the underlying numbers are on.
function starsForPair(value1, value2) {
  const safeMax = Math.max(Math.abs(value1), Math.abs(value2), 0.0001);
  return [starRating(value1, safeMax), starRating(value2, safeMax)];
}

function formBadges(sequence) {
  if (!sequence || !sequence.length) return '<span class="stat-dash">—</span>';
  return `<div class="form-badges">${sequence.map(
    (r) => `<div class="form-badge ${r === 'W' ? 'w' : 'l'}">${r}</div>`
  ).join('')}</div>`;
}

function renderFactors(team1, team2, meta1, meta2, f) {
  const [batStars1, batStars2] = starsForPair(f.team1_batting_strength ?? 0, f.team2_batting_strength ?? 0);
  const [bowlStars1, bowlStars2] = starsForPair(f.team1_bowling_strength ?? 0, f.team2_bowling_strength ?? 0);

  factorGrid.innerHTML = `
    <div class="factor-card">
      <div class="factor-title">BATTING STRENGTH</div>
      <div class="factor-row"><span class="factor-team-tag">${meta1.short}</span><span class="stars">${batStars1}</span></div>
      <div class="factor-row"><span class="factor-team-tag">${meta2.short}</span><span class="stars">${batStars2}</span></div>
    </div>
    <div class="factor-card">
      <div class="factor-title">BOWLING STRENGTH</div>
      <div class="factor-row"><span class="factor-team-tag">${meta1.short}</span><span class="stars">${bowlStars1}</span></div>
      <div class="factor-row"><span class="factor-team-tag">${meta2.short}</span><span class="stars">${bowlStars2}</span></div>
    </div>
    <div class="factor-card">
      <div class="factor-title">TEAM RATING</div>
      <div class="factor-row"><span class="factor-team-tag">${meta1.short}</span><span class="factor-value">${(f.team1_rating ?? 0).toFixed(1)}</span></div>
      <div class="factor-row"><span class="factor-team-tag">${meta2.short}</span><span class="factor-value">${(f.team2_rating ?? 0).toFixed(1)}</span></div>
    </div>
    <div class="factor-card">
      <div class="factor-title">STAR PRESENCE</div>
      <div class="star-names"><strong>${meta1.short}:</strong> ${(f.team1_star_players || []).join(', ') || '—'}</div>
      <div class="star-names" style="margin-top:6px"><strong>${meta2.short}:</strong> ${(f.team2_star_players || []).join(', ') || '—'}</div>
    </div>
    <div class="factor-card">
      <div class="factor-title">TEAM FORM (LAST 5)</div>
      <div class="factor-row"><span class="factor-team-tag">${meta1.short}</span>${formBadges(f.team1_form_sequence)}</div>
      <div class="factor-row"><span class="factor-team-tag">${meta2.short}</span>${formBadges(f.team2_form_sequence)}</div>
    </div>
  `;
}

function showError(msg) {
  errorMessage.textContent = msg;
  errorMessage.classList.add('visible');
}
function hideError() {
  errorMessage.textContent = '';
  errorMessage.classList.remove('visible');
}

init();
