// ============================================================
// Stats page logic
// ============================================================

const teamSelect = document.getElementById('team-select');
const tableBody = document.getElementById('stats-table-body');

async function init() {
  try {
    const res = await fetch('/api/teams-meta');
    const teams = await res.json();

    teams.forEach((team) => {
      const option = document.createElement('option');
      option.value = team.name;
      option.textContent = team.name;
      teamSelect.appendChild(option);
    });

    if (teams.length) {
      teamSelect.value = teams[0].name;
      loadStats(teams[0].name);
    }
  } catch (err) {
    tableBody.innerHTML = `<tr class="loading-row"><td colspan="5">Could not load teams.</td></tr>`;
    console.error(err);
  }
}

teamSelect.addEventListener('change', () => loadStats(teamSelect.value));

async function loadStats(teamName) {
  tableBody.innerHTML = `<tr class="loading-row"><td colspan="5">Loading ${teamName}...</td></tr>`;

  try {
    const res = await fetch(`/api/team-stats?team=${encodeURIComponent(teamName)}`);
    const players = await res.json();

    if (!players.length) {
      tableBody.innerHTML = `<tr class="loading-row"><td colspan="5">No stats found for this team.</td></tr>`;
      return;
    }

    tableBody.innerHTML = players.map((p) => `
      <tr>
        <td class="player-name-cell">${p.name}</td>
        <td>${formatStat(p.batting_average)}</td>
        <td>${formatStat(p.strike_rate)}</td>
        <td>${formatStat(p.bowling_average)}</td>
        <td>${formatStat(p.economy)}</td>
      </tr>
    `).join('');

  } catch (err) {
    tableBody.innerHTML = `<tr class="loading-row"><td colspan="5">Something went wrong loading stats.</td></tr>`;
    console.error(err);
  }
}

// Specialist batsmen have no bowling stats (and vice versa) — show a dash instead of 0 or blank
function formatStat(value) {
  if (value === null || value === undefined) {
    return '<span class="stat-dash">—</span>';
  }
  return value.toFixed(1);
}

init();
