// ============================================================
// Teams page logic
// ============================================================

const teamsGrid = document.getElementById('teams-grid');

async function init() {
  try {
    const res = await fetch('/api/teams-meta');
    const teams = await res.json();

    teamsGrid.innerHTML = teams.map((team) => `
      <div class="team-tile" data-team="${team.name}">
        <div class="team-tile-badge" style="background:${team.color}">${team.short}</div>
        <div class="team-tile-name">${team.name}</div>
        <div class="team-tile-rating">RATING ${team.rating.toFixed(1)}</div>
      </div>
    `).join('');

    // Clicking a team card takes you to the Home page with that team
    // pre-selected as Team A, using a URL query parameter.
    document.querySelectorAll('.team-tile').forEach((tile) => {
      tile.addEventListener('click', () => {
        const teamName = tile.getAttribute('data-team');
        window.location.href = `/?team1=${encodeURIComponent(teamName)}`;
      });
    });

  } catch (err) {
    teamsGrid.innerHTML = `<p style="color: var(--text-muted)">Could not load teams.</p>`;
    console.error(err);
  }
}

init();
