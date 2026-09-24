import { Chessground } from "https://cdn.jsdelivr.net/npm/chessground@9.1.1/+esm";

// State
const state = {
  username: null,
  timeClasses: [],
  selectedTimeClass: null,
  currentRoute: "overview",
  currentGameId: null,
  meta: null,
  insights: null,
  games: [],
  currentGame: null,
  puzzles: [],
  currentPuzzleIndex: 0,
  progress: null,
  gamesOffset: 0,
  gamesTotal: null,
};

const cg = {}; // Chessground instance container

// HTML escaping
function esc(str) {
  if (typeof str !== "string") return str;
  const map = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  };
  return str.replace(/[&<>"']/g, (c) => map[c]);
}

// API client
const api = {
  async get(path) {
    try {
      const res = await fetch(path);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      console.error(`API error: ${path}`, e);
      throw e;
    }
  },
  async post(path, body) {
    try {
      const res = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      console.error(`API error: ${path}`, e);
      throw e;
    }
  },
};

// Formatting utilities
function fmtScore(score) {
  return score != null ? (score).toFixed(1) + "%" : "-";
}

function fmtDate(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function fmtDateFull(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function fmtMonthYear(month) {
  const [year, m] = month.split("-");
  return new Date(year, m - 1).toLocaleDateString("en-US", { month: "short", year: "2-digit" });
}

function fmtTime(seconds) {
  if (seconds == null) return "-";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m > 0 ? `${m}:${String(s).padStart(2, "0")}` : `${s}s`;
}

function fmtEval(cp, mate) {
  if (mate != null) return mate > 0 ? `#${mate}` : `-#${Math.abs(mate)}`;
  if (cp == null) return "-";
  const sign = cp > 0 ? "+" : "";
  return sign + (cp / 100).toFixed(2);
}

function fmtWinPct(pct) {
  if (pct == null) return "-";
  return (pct).toFixed(0) + "%";
}

// SVG utilities
function svgLine(points, width = 2, color = "currentColor") {
  if (!points.length) return "";
  const pathData = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${p[0]} ${p[1]}`)
    .join(" ");
  return `<path d="${pathData}" stroke="${color}" stroke-width="${width}" fill="none" stroke-linecap="round" stroke-linejoin="round" />`;
}

function svgArea(points, height = 300, color = "currentColor", opacity = 0.1) {
  if (!points.length) return "";
  const pathData = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p[0]} ${p[1]}`).join(" ");
  return `<path d="${pathData} L ${points[points.length - 1][0]} ${height} L ${points[0][0]} ${height} Z" fill="${color}" opacity="${opacity}" />`;
}

function svgBar(x, y, width, height, color = "currentColor") {
  const rx = Math.min(height / 2, 4);
  return `<rect x="${x}" y="${y}" width="${width}" height="${height}" fill="${color}" rx="${rx}" />`;
}

const STREAK_LABELS = {
  fresh: "First game of a sitting",
  after_win: "After a win",
  after_loss: "After a loss",
  after_two_plus_losses: "After 2+ losses",
};

function ratingChart(data) {
  const months = (data || []).slice(-24);
  if (months.length === 0) return '<div class="chart-placeholder">No data</div>';
  const W = 720, H = 260, left = 48, right = 56, top = 16, bottom = 28;
  const ratings = months.map((m) => m.rating);
  const step = 50;
  const lo = Math.floor(Math.min(...ratings) / step) * step;
  const hi = Math.ceil(Math.max(...ratings) / step) * step || lo + step;
  const x = (i) => left + (i / Math.max(1, months.length - 1)) * (W - left - right);
  const y = (r) => top + (1 - (r - lo) / Math.max(step, hi - lo)) * (H - top - bottom);
  const tickEvery = Math.ceil((hi - lo) / step / 5);
  const ticks = [];
  for (let r = lo; r <= hi; r += step * tickEvery) ticks.push(r);
  const grid = ticks
    .map((r) => `<line x1="${left}" x2="${W - right}" y1="${y(r)}" y2="${y(r)}" stroke="var(--grid)" />
      <text x="${left - 8}" y="${y(r) + 4}" text-anchor="end" class="chart-axis">${r}</text>`)
    .join("");
  const labelEvery = Math.max(1, Math.ceil(months.length / 6));
  const xLabels = months
    .map((m, i) => (i % labelEvery === 0 ? `<text x="${x(i)}" y="${H - 8}" text-anchor="middle" class="chart-axis">${fmtMonthYear(m.month)}</text>` : ""))
    .join("");
  const path = months.map((m, i) => `${i ? "L" : "M"}${x(i)},${y(m.rating)}`).join(" ");
  const last = months[months.length - 1];
  const hits = months
    .map((m, i) => `<g class="hit"><title>${esc(fmtMonthYear(m.month))}: ${m.rating} (${m.games} games)</title>
      <rect x="${x(i) - 12}" y="${top}" width="24" height="${H - top - bottom}" fill="transparent" />
      <circle cx="${x(i)}" cy="${y(m.rating)}" r="4" class="hit-dot" /></g>`)
    .join("");
  return `<svg viewBox="0 0 ${W} ${H}" class="chart" role="img" aria-label="Rating by month">
    ${grid}${xLabels}
    <path d="${path}" fill="none" stroke="var(--series-1)" stroke-width="2" stroke-linejoin="round" />
    <circle cx="${x(months.length - 1)}" cy="${y(last.rating)}" r="4" fill="var(--series-1)" stroke="var(--surface)" stroke-width="2" />
    <text x="${x(months.length - 1) + 8}" y="${y(last.rating) + 4}" class="chart-value">${last.rating}</text>
    ${hits}
  </svg>`;
}

// Chart: Openings diverging bar (top 12 by games)
function openingsChart(overall, openings) {
  if (!openings || openings.length === 0) {
    return '<div class="chart-placeholder">No opening data</div>';
  }
  const top = openings.slice(0, 12);
  const diffs = top.map((o) => o.score_pct - overall.score_pct);
  const maxDiff = Math.max(5, ...diffs.map(Math.abs));
  const W = 720, labelW = 250, valueW = 70, rowH = 28;
  const zero = labelW + (W - labelW) / 2;
  const half = (W - labelW) / 2 - valueW;
  const H = rowH * top.length + 8;
  const rows = top.map((o, i) => {
    const y = 4 + i * rowH;
    const diff = diffs[i];
    const len = Math.max(2, (Math.abs(diff) / maxDiff) * half);
    const x = diff >= 0 ? zero : zero - len;
    const color = diff >= 0 ? "var(--series-1)" : "var(--negative)";
    const valueX = diff >= 0 ? zero + len + 6 : zero - len - 6;
    const tip = `${o.color} · ${o.family}: ${o.score_pct.toFixed(1)}% in ${o.games} games (${o.wins}/${o.draws}/${o.losses}), ${formatSigned(diff)} pts vs your ${overall.score_pct.toFixed(1)}%`;
    return `<g class="bar-row"><title>${esc(tip)}</title>
      <rect x="0" y="${y}" width="${W}" height="${rowH}" fill="transparent" />
      <text x="${labelW - 12}" y="${y + rowH / 2 + 4}" text-anchor="end" class="chart-label">${esc(o.color)} · ${esc(o.family)}</text>
      ${svgBar(x, y + 6, len, rowH - 12, color)}
      <text x="${valueX}" y="${y + rowH / 2 + 4}" text-anchor="${diff >= 0 ? "start" : "end"}" class="chart-value">${formatSigned(diff)} pts</text>
    </g>`;
  });
  return `<svg viewBox="0 0 ${W} ${H}" class="chart" role="img" aria-label="Opening scores relative to your average">
    <line x1="${zero}" x2="${zero}" y1="0" y2="${H}" stroke="var(--grid)" stroke-width="1" />
    ${rows.join("")}
  </svg>`;
}

function formatSigned(value) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(1)}`;
}

// Chart: Eval graph (white win % by ply)
const CLASS_LABEL = { inaccuracy: "Inaccuracy", mistake: "Mistake", blunder: "Blunder" };
const CLASS_ICON = { inaccuracy: "?!", mistake: "?", blunder: "??" };

function evalGraph(moves, userColor) {
  if (!moves.length) return "";
  const W = 720, H = 180, left = 40, right = 12, top = 10, bottom = 10;
  const x = (i) => left + (i / Math.max(1, moves.length - 1)) * (W - left - right);
  const y = (pct) => top + (1 - pct / 100) * (H - top - bottom);
  const path = moves.map((m, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(m.white_win_pct_after).toFixed(1)}`).join(" ");
  const area = `${path} L${x(moves.length - 1)},${y(0)} L${x(0)},${y(0)} Z`;
  const grid = [0, 50, 100]
    .map((p) => `<line x1="${left}" x2="${W - right}" y1="${y(p)}" y2="${y(p)}" stroke="var(--grid)" />
      <text x="${left - 6}" y="${y(p) + 4}" text-anchor="end" class="chart-axis">${p}%</text>`)
    .join("");
  const markers = moves
    .filter((m) => m.color === userColor && CLASS_LABEL[m.move_class])
    .map((m) => `<circle cx="${x(moves.indexOf(m))}" cy="${y(m.white_win_pct_after)}" r="4.5"
      fill="var(--${m.move_class === "blunder" ? "critical" : m.move_class === "mistake" ? "serious" : "warning"})"
      stroke="var(--surface)" stroke-width="2" pointer-events="none" />`)
    .join("");
  const slot = (W - left - right) / Math.max(1, moves.length - 1);
  const hits = moves
    .map((m, i) => `<rect class="eval-hit" data-idx="${i + 1}" x="${x(i) - slot / 2}" y="${top}" width="${slot}" height="${H - top - bottom}" fill="transparent">
      <title>${moveLabel(m.ply)} ${esc(m.san)} · ${m.white_win_pct_after.toFixed(0)}% White</title></rect>`)
    .join("");
  return `<svg viewBox="0 0 ${W} ${H}" class="chart eval-graph" role="img" aria-label="White win chance by move">
    ${grid}
    <path d="${area}" fill="var(--series-1)" opacity="0.12" />
    <path d="${path}" fill="none" stroke="var(--series-1)" stroke-width="2" stroke-linejoin="round" />
    <line id="evalCursor" x1="0" x2="0" y1="${top}" y2="${H - bottom}" stroke="var(--text-2)" stroke-width="1" visibility="hidden" data-left="${left}" data-slot="${slot}" />
    ${markers}${hits}
  </svg>`;
}

function moveLabel(ply) {
  return `${Math.floor(ply / 2) + 1}${ply % 2 === 0 ? "." : "..."}`;
}

function renderLoading() {
  return '<div class="loading">Loading...</div>';
}

function renderError(msg) {
  return `<div class="error">${esc(msg)}</div>`;
}

function renderHeader() {
  const h1 = state.username ? `Chess Coach · ${esc(state.username)}` : "Chess Coach";
  document.querySelector(".app-title").textContent = h1;

  const navLinks = document.querySelectorAll(".nav-link");
  navLinks.forEach((link) => {
    const route = link.getAttribute("data-route");
    link.classList.toggle("active", route === state.currentRoute);
  });
}

function renderTimeClassSelector() {
  if (!state.timeClasses || state.timeClasses.length === 0) return;

  const container = document.getElementById("timeClassButtons");
  container.innerHTML = state.timeClasses
    .map(
      (tc) =>
        `<button class="time-class-btn ${tc.time_class === state.selectedTimeClass ? "active" : ""}" data-tc="${tc.time_class}">${esc(tc.time_class)} (${tc.games})</button>`
    )
    .join("");

  container.querySelectorAll(".time-class-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const tc = e.target.getAttribute("data-tc");
      state.selectedTimeClass = tc;
      localStorage.setItem("selectedTimeClass", tc);
      renderTimeClassSelector();
      routeTo(state.currentRoute);
    });
  });
}

function renderOverview() {
  const html = [
    '<div class="view-container">',
    '<div class="overview-grid">',
    // Stats row
    '<div class="stats-row">',
  ];

  if (!state.insights) {
    html.push(renderLoading());
    html.push("</div></div></div>");
    document.getElementById("main").innerHTML = html.join("");
    return;
  }

  const { overall, openings, highlights, clock, streaks, by_session_position, by_day_part, by_weekday, by_rating_gap, rating_by_month, analyzed_games, engine } = state.insights;
  const lastRating = rating_by_month && rating_by_month.length > 0 ? rating_by_month[rating_by_month.length - 1].rating : null;

  html.push(
    '<div class="stat-tile">',
    `<div class="stat-label">Games</div>`,
    `<div class="stat-value">${overall.games}</div>`,
    "</div>"
  );
  html.push(
    '<div class="stat-tile">',
    `<div class="stat-label">Score %</div>`,
    `<div class="stat-value">${fmtScore(overall.score_pct)}</div>`,
    "</div>"
  );
  if (lastRating)
    html.push(
      '<div class="stat-tile">',
      `<div class="stat-label">Current Rating</div>`,
      `<div class="stat-value">${lastRating}</div>`,
      "</div>"
    );
  html.push(
    '<div class="stat-tile">',
    `<div class="stat-label">Analyzed</div>`,
    `<div class="stat-value">${analyzed_games}</div>`,
    "</div>"
  );
  html.push("</div>"); // stats-row

  // Highlights section
  html.push('<div class="highlights-section">');
  if (highlights && highlights.length > 0) {
    const workOn = highlights.filter((h) => !h.strength);
    const keepDoing = highlights.filter((h) => h.strength);

    if (workOn.length > 0) {
      html.push('<div class="highlight-column">');
      html.push('<h3>Work on</h3>');
      workOn.forEach((h) => {
        html.push(
          `<div class="highlight-item"><span class="highlight-icon">▼</span><span>${esc(h.text)}</span></div>`
        );
      });
      html.push("</div>");
    }

    if (keepDoing.length > 0) {
      html.push('<div class="highlight-column">');
      html.push('<h3>Keep doing</h3>');
      keepDoing.forEach((h) => {
        html.push(
          `<div class="highlight-item"><span class="highlight-icon good">▲</span><span>${esc(h.text)}</span></div>`
        );
      });
      html.push("</div>");
    }
  }
  html.push("</div>"); // highlights-section

  // Rating chart
  html.push('<div class="chart-section">');
  html.push('<h3>Rating by month</h3>');
  if (rating_by_month) {
    html.push(ratingChart(rating_by_month));
  }
  html.push("</div>");

  // Openings chart
  html.push('<div class="chart-section">');
  html.push('<h3>Openings vs your average</h3>');
  if (openings) {
    html.push(openingsChart(overall, openings));
  }
  html.push("</div>");

  // Clock section
  if (clock) {
    html.push('<div class="section">');
    html.push('<h3>Clock</h3>');
    html.push('<div class="stats-row">');
    html.push(
      '<div class="stat-tile">',
      `<div class="stat-label">Games in time trouble</div>`,
      `<div class="stat-value">${fmtScore((100 * clock.in_trouble.games) / clock.games)}</div>`,
      `<div class="stat-note">under 10% of your clock</div>`,
      "</div>"
    );
    html.push(
      '<div class="stat-tile">',
      `<div class="stat-label">Score in time trouble</div>`,
      `<div class="stat-value">${fmtScore(clock.in_trouble.score_pct)}</div>`,
      `<div class="stat-note">vs ${fmtScore(clock.not_in_trouble.score_pct)} otherwise</div>`,
      "</div>"
    );
    html.push(
      '<div class="stat-tile">',
      `<div class="stat-label">Losses on time</div>`,
      `<div class="stat-value">${fmtScore(clock.losses ? (100 * clock.losses_on_time) / clock.losses : null)}</div>`,
      `<div class="stat-note">${clock.losses_on_time} of ${clock.losses} losses</div>`,
      "</div>"
    );
    html.push("</div>"); // stats-row
    html.push("</div>"); // section
  }

  // Habits tables
  html.push('<div class="section">');
  html.push('<h3>Habits</h3>');

  if (streaks) {
    html.push('<table class="compact-table">');
    html.push("<tr><th>Streak</th><th>Games</th><th>W/D/L</th><th>Score</th></tr>");
    Object.entries(STREAK_LABELS).forEach(([k, label]) => {
      const s = streaks[k];
      if (s) {
        html.push(
          `<tr><td>${label}</td><td>${s.games}</td><td>${s.wins}/${s.draws}/${s.losses}</td><td>${fmtScore(s.score_pct)}</td></tr>`
        );
      }
    });
    html.push("</table>");
  }

  if (by_session_position) {
    html.push('<table class="compact-table">');
    html.push("<tr><th>Position</th><th>Games</th><th>W/D/L</th><th>Score</th></tr>");
    by_session_position.forEach((s) => {
      html.push(
        `<tr><td>${esc(s.label)}</td><td>${s.games}</td><td>${s.wins}/${s.draws}/${s.losses}</td><td>${fmtScore(s.score_pct)}</td></tr>`
      );
    });
    html.push("</table>");
  }

  if (by_day_part) {
    html.push('<table class="compact-table">');
    html.push("<tr><th>Day part</th><th>Games</th><th>W/D/L</th><th>Score</th></tr>");
    by_day_part.forEach((s) => {
      html.push(
        `<tr><td>${esc(s.label)}</td><td>${s.games}</td><td>${s.wins}/${s.draws}/${s.losses}</td><td>${fmtScore(s.score_pct)}</td></tr>`
      );
    });
    html.push("</table>");
  }

  if (by_weekday) {
    html.push('<table class="compact-table">');
    html.push("<tr><th>Weekday</th><th>Games</th><th>W/D/L</th><th>Score</th></tr>");
    by_weekday.forEach((s) => {
      html.push(
        `<tr><td>${esc(s.label)}</td><td>${s.games}</td><td>${s.wins}/${s.draws}/${s.losses}</td><td>${fmtScore(s.score_pct)}</td></tr>`
      );
    });
    html.push("</table>");
  }

  html.push("</div>"); // habits section

  if (by_rating_gap) {
    html.push('<div class="section">');
    html.push('<h3>Opponents by rating</h3>');
    html.push('<table class="compact-table">');
    html.push("<tr><th>Gap</th><th>Expected %</th><th>Games</th><th>Score %</th></tr>");
    by_rating_gap.forEach((s) => {
      html.push(
        `<tr><td>${esc(s.label)}</td><td>${fmtScore(s.expected_score_pct)}</td><td>${s.games}</td><td>${fmtScore(s.score_pct)}</td></tr>`
      );
    });
    html.push("</table>");
    html.push("</div>");
  }

  // Engine section
  if (engine) {
    html.push('<div class="section">');
    html.push('<h3>Engine analysis</h3>');
    html.push('<div class="stats-row">');
    html.push(
      '<div class="stat-tile">',
      `<div class="stat-label">Accuracy</div>`,
      `<div class="stat-value">${(engine.accuracy).toFixed(1)}%</div>`,
      "</div>"
    );
    html.push(
      '<div class="stat-tile">',
      `<div class="stat-label">Opponent accuracy</div>`,
      `<div class="stat-value">${(engine.opponent_accuracy).toFixed(1)}%</div>`,
      "</div>"
    );
    html.push("</div>"); // stats-row

    if (engine.by_phase) {
      html.push('<table class="compact-table">');
      html.push("<tr><th>Phase</th><th>Moves</th><th>Avg loss</th><th>Inaccurate</th><th>Mistakes</th><th>Blunders</th><th>Serious/100</th></tr>");
      engine.by_phase.forEach((p) => {
        html.push(
          `<tr><td>${esc(p.phase)}</td><td>${p.moves}</td><td>${p.avg_win_pct_loss ? (p.avg_win_pct_loss).toFixed(1) + "%" : "-"}</td><td>${p.inaccuracies}</td><td>${p.mistakes}</td><td>${p.blunders}</td><td>${(p.serious_per_100).toFixed(1)}</td></tr>`
        );
      });
      html.push("</table>");
    }

    if (engine.missed_mates && engine.missed_mates.length > 0) {
      html.push('<div class="engine-list">');
      html.push('<h4>Missed mates</h4>');
      engine.missed_mates.forEach((m) => {
        const encUrl = encodeURIComponent(m.game_url);
        html.push(
          `<div><a href="#/games/${encUrl}">${esc(m.san)} was ${esc(m.best_move_san)}</a></div>`
        );
      });
      html.push("</div>");
    }

    if (engine.unpunished && engine.unpunished.length > 0) {
      html.push('<div class="engine-list">');
      html.push('<h4>Unpunished mistakes</h4>');
      engine.unpunished.forEach((m) => {
        const encUrl = encodeURIComponent(m.game_url);
        html.push(
          `<div><a href="#/games/${encUrl}">Game at ply ${m.ply}</a></div>`
        );
      });
      html.push("</div>");
    }

    if (engine.conversion && engine.conversion.thrown && engine.conversion.thrown.length > 0) {
      html.push('<div class="engine-list">');
      html.push('<h4>Thrown positions</h4>');
      html.push(
        `<p>Converted ${engine.conversion.converted}/${engine.conversion.winning_games} winning games (${(engine.conversion.rate).toFixed(1)}%)</p>`
      );
      engine.conversion.thrown.forEach((m) => {
        const encUrl = encodeURIComponent(m.game_url);
        html.push(
          `<div><a href="#/games/${encUrl}">Game at ply ${m.ply}</a></div>`
        );
      });
      html.push("</div>");
    }

    html.push("</div>"); // engine section
  } else if (analyzed_games > 0) {
    html.push(
      '<div class="section"><p>Engine findings appear after analyzing 20 games.</p></div>'
    );
  }

  html.push("</div></div>");
  document.getElementById("main").innerHTML = html.join("");
}

function renderGames() {
  const html = ['<div class="view-container"><div class="games-view">'];

  if (!state.games) {
    html.push(renderLoading());
    html.push("</div></div>");
    document.getElementById("main").innerHTML = html.join("");
    return;
  }

  html.push(
    '<table class="games-table"><thead><tr><th>Date</th><th>Color</th><th>Opponent</th><th>Result</th><th>Opening</th><th>Accuracy</th><th>Analyzed</th></tr></thead><tbody>'
  );

  state.games.forEach((g) => {
    const encId = encodeURIComponent(g.id);
    const outcome = g.outcome === "win" ? "✓" : g.outcome === "draw" ? "=" : "✗";
    const outcomeClass =
      g.outcome === "win" ? "win" : g.outcome === "draw" ? "draw" : "loss";
    const accuracy = g.accuracy != null ? (g.accuracy).toFixed(1) + "%" : "-";
    const analyzed = g.analyzed ? "yes" : "-";
    html.push(
      `<tr class="game-row" data-game-id="${encId}">`,
      `<td>${fmtDate(g.played_at)}</td>`,
      `<td>${esc(g.color)}</td>`,
      `<td>${esc(g.opponent)} (${g.opponent_rating})</td>`,
      `<td class="outcome ${outcomeClass}">${outcome}</td>`,
      `<td>${esc(g.opening)}</td>`,
      `<td>${accuracy}</td>`,
      `<td>${analyzed}</td>`,
      "</tr>"
    );
  });

  html.push(
    "</tbody></table>",
    '<div class="load-more-container">',
    '<button id="loadMoreBtn" class="btn-primary">Load more</button>',
    "</div>",
    "</div></div>"
  );

  document.getElementById("main").innerHTML = html.join("");

  document.querySelectorAll(".game-row").forEach((row) => {
    row.addEventListener("click", () => {
      location.hash = `#/games/${row.getAttribute("data-game-id")}`;
    });
  });

  document.getElementById("loadMoreBtn").addEventListener("click", async () => {
    state.gamesOffset += 50;
    await loadGames();
    renderGames();
  });
}

function renderGameViewer() {
  const main = document.getElementById("main");
  if (!state.currentGame) {
    main.innerHTML = renderLoading();
    return;
  }
  const { game, positions, analysis } = state.currentGame;
  const me = state.meta ? state.meta.username : "You";
  const [white, black] = game.color === "white"
    ? [`${me} (${game.rating})`, `${game.opponent} (${game.opponent_rating})`]
    : [`${game.opponent} (${game.opponent_rating})`, `${me} (${game.rating})`];
  const moves = analysis ? analysis.moves : [];
  const byPly = new Map(moves.map((m) => [m.ply, m]));
  const accuracy = analysis && analysis.accuracy.user != null
    ? ` · accuracy ${analysis.accuracy.user.toFixed(1)}% (opponent ${analysis.accuracy.opponent?.toFixed(1) ?? "-"}%)`
    : "";

  const rows = [];
  for (let idx = 1; idx < positions.length; idx += 2) {
    rows.push(`<div class="move-row"><span class="move-num">${Math.floor((idx - 1) / 2) + 1}.</span>
      ${moveCell(positions, idx, byPly, game.color)}${moveCell(positions, idx + 1, byPly, game.color)}</div>`);
  }

  main.innerHTML = `<div class="view-container game-viewer">
    <div class="game-header">
      <div class="players"><strong>${esc(white)}</strong> vs <strong>${esc(black)}</strong></div>
      <div class="meta">${esc(game.outcome)} by ${esc(game.termination)} · ${esc(game.time_class)} ${esc(game.time_control)} ·
        ${fmtDateFull(game.played_at)}${accuracy} · <a href="${esc(game.url)}" target="_blank" rel="noopener">Open on chess.com</a></div>
    </div>
    <div class="game-content">
      <div class="board-section">
        <div id="board" class="board"></div>
        <div class="board-controls">${NAV_BUTTONS}</div>
      </div>
      <div class="moves-section">
        <div class="move-list" id="moveList">${rows.join("") || "<p>No moves.</p>"}</div>
        <div class="move-panel" id="moveInfo"></div>
      </div>
    </div>
    ${analysis ? `<div class="section"><h3>White win chance (engine depth ${analysis.depth})</h3>${evalGraph(moves, game.color)}</div>`
               : '<div class="section"><p class="muted">Not analyzed yet. The nightly job will pick it up, or run <code>coach analyze</code>.</p></div>'}
  </div>`;

  if (cg.instance) cg.instance.destroy();
  cg.instance = Chessground(document.getElementById("board"), {
    fen: positions[0].fen,
    orientation: game.color,
    coordinates: true,
    viewOnly: true,
  });

  let current = 0;
  const goTo = (idx) => {
    current = Math.max(0, Math.min(positions.length - 1, idx));
    cg.instance.set({ fen: positions[current].fen });
    document.querySelectorAll(".move.current").forEach((el) => el.classList.remove("current"));
    const cell = document.querySelector(`.move[data-idx="${current}"]`);
    if (cell) {
      cell.classList.add("current");
      keepInView(document.getElementById("moveList"), cell);
    }
    document.getElementById("moveInfo").innerHTML = movePanel(positions, current, byPly);
    const cursor = document.getElementById("evalCursor");
    if (cursor) {
      const cx = Number(cursor.dataset.left) + (current - 1) * Number(cursor.dataset.slot);
      cursor.setAttribute("x1", cx);
      cursor.setAttribute("x2", cx);
      cursor.setAttribute("visibility", current > 0 ? "visible" : "hidden");
    }
  };
  const nav = { first: () => goTo(0), prev: () => goTo(current - 1), next: () => goTo(current + 1), last: () => goTo(positions.length - 1) };
  main.querySelectorAll("[data-nav]").forEach((b) => b.addEventListener("click", nav[b.dataset.nav]));
  main.querySelectorAll("[data-idx]").forEach((el) => el.addEventListener("click", () => goTo(Number(el.dataset.idx))));
  bindMoveKeys(nav);
  goTo(0);
}

function keepInView(container, item) {
  const box = container.getBoundingClientRect();
  const rect = item.getBoundingClientRect();
  if (rect.top < box.top) container.scrollTop -= box.top - rect.top;
  else if (rect.bottom > box.bottom) container.scrollTop += rect.bottom - box.bottom;
}

function bindMoveKeys(nav) {
  const keys = {
    ArrowLeft: nav.prev,
    ArrowRight: nav.next,
    ArrowUp: nav.first,
    ArrowDown: nav.last,
    Home: nav.first,
    End: nav.last,
  };
  document.onkeydown = (e) => {
    if (!keys[e.key] || e.altKey || e.ctrlKey || e.metaKey || e.target.closest?.("input, textarea, select")) return;
    e.preventDefault();
    keys[e.key]();
  };
}

const NAV_BUTTONS = `
  <button data-nav="first" class="btn-small" aria-label="First move (↑)" title="First move (↑)">⏮</button>
  <button data-nav="prev" class="btn-small" aria-label="Previous move (←)" title="Previous move (←)">◀</button>
  <button data-nav="next" class="btn-small" aria-label="Next move (→)" title="Next move (→)">▶</button>
  <button data-nav="last" class="btn-small" aria-label="Last move (↓)" title="Last move (↓)">⏭</button>`;

function moveCell(positions, idx, byPly, userColor) {
  if (idx >= positions.length) return "<span></span>";
  const move = byPly.get(idx - 1);
  const flagged = move && move.color === userColor && CLASS_LABEL[move.move_class];
  const badge = flagged
    ? `<span class="move-flag ${move.move_class}" title="${CLASS_LABEL[move.move_class]}">${CLASS_ICON[move.move_class]}</span>`
    : "";
  return `<span class="move" data-idx="${idx}">${esc(positions[idx].san)}${badge}</span>`;
}

function movePanel(positions, idx, byPly) {
  if (idx === 0) return '<span class="muted">Start position. ← → step through moves, ↑ first, ↓ last.</span>';
  const move = byPly.get(idx - 1);
  const head = `<strong>${moveLabel(idx - 1)} ${esc(positions[idx].san)}</strong>`;
  if (!move) return head;
  const judgement = CLASS_LABEL[move.move_class]
    ? ` <span class="move-flag ${move.move_class}">${CLASS_ICON[move.move_class]}</span> ${CLASS_LABEL[move.move_class]}`
    : "";
  const best = move.best_move_san && move.best_move_san !== move.san ? ` · best was <strong>${esc(move.best_move_san)}</strong>` : "";
  const clock = move.clock_seconds != null ? ` · clock ${fmtTime(move.clock_seconds)}` : "";
  return `${head}${judgement}<br><span class="muted">eval ${fmtEval(move.eval_before.cp, move.eval_before.mate)} → ${fmtEval(move.eval_after.cp, move.eval_after.mate)} ·
    ${Math.max(0, move.win_pct_loss).toFixed(1)}% win chance lost${best}${clock}</span>`;
}

function renderPuzzles() {
  const main = document.getElementById("main");
  if (!state.puzzles) {
    main.innerHTML = renderLoading();
    return;
  }
  if (state.puzzles.length === 0) {
    main.innerHTML = '<div class="view-container"><div class="empty-state">No puzzles due. Come back later or analyze more games.</div></div>';
    return;
  }

  const index = state.currentPuzzleIndex;
  const puzzle = state.puzzles[index];
  const isLast = index === state.puzzles.length - 1;
  main.innerHTML = `<div class="view-container puzzles-view">
    <div class="puzzle-header"><h2>Puzzle ${index + 1}/${state.puzzles.length} · vs ${esc(puzzle.opponent)} ·
      ${fmtDateFull(puzzle.played_at)} · ${esc(puzzle.phase)}</h2></div>
    <div class="puzzle-content">
      <div class="puzzle-board">
        <div id="puzzleBoard" class="board"></div>
        <div class="board-controls">${NAV_BUTTONS}</div>
      </div>
      <div class="puzzle-info">
        <p>You played <strong>${esc(puzzle.played_san)}</strong> (${esc(puzzle.mistake)}).
          Find the best move for <strong>${esc(puzzle.color)}</strong>.</p>
        <p id="puzzlePosition" class="muted"></p>
        <div id="puzzleMessage" class="puzzle-message"></div>
        <button id="nextPuzzleBtn" class="btn-primary" hidden>${isLast ? "Done" : "Next puzzle"}</button>
      </div>
    </div>
  </div>`;

  if (cg.puzzleInstance) cg.puzzleInstance.destroy();
  cg.puzzleInstance = Chessground(document.getElementById("puzzleBoard"), {
    fen: puzzle.fen,
    orientation: puzzle.color,
    coordinates: true,
    movable: { free: true, color: puzzle.color, events: { after: (orig, dest) => answer(orig, dest) } },
  });

  let positions = null;
  let current = puzzle.ply;
  let answered = false;
  const limit = () => (positions ? (answered ? positions.length - 1 : puzzle.ply) : puzzle.ply);

  const goTo = (idx) => {
    if (!positions) return;
    current = Math.max(0, Math.min(limit(), idx));
    const onPuzzle = current === puzzle.ply && !answered;
    cg.puzzleInstance.set({
      fen: positions[current].fen,
      lastMove: undefined,
      movable: { color: onPuzzle ? puzzle.color : undefined },
    });
    document.getElementById("puzzlePosition").textContent = onPuzzle
      ? "Your move. ← → step through the game, ↑ to its start."
      : `Viewing ${current === 0 ? "the start" : `after ${moveLabel(current - 1)} ${positions[current].san}`}. ↓ returns to the ${answered ? "end of the game" : "puzzle"}.`;
  };
  const nav = { first: () => goTo(0), prev: () => goTo(current - 1), next: () => goTo(current + 1), last: () => goTo(limit()) };
  main.querySelectorAll("[data-nav]").forEach((b) => b.addEventListener("click", nav[b.dataset.nav]));
  bindMoveKeys(nav);

  api.get(`/api/games/${encodeURIComponent(puzzle.game_id)}`).then((detail) => {
    positions = detail.positions;
    goTo(current);
  }).catch(() => {
    document.getElementById("puzzlePosition").textContent = "Game moves unavailable; the puzzle still works.";
  });

  async function answer(orig, dest) {
    const piece = cg.puzzleInstance.state.pieces.get(dest);
    const promotes = piece && piece.role === "pawn" && (dest[1] === "8" || dest[1] === "1");
    const message = document.getElementById("puzzleMessage");
    try {
      const result = await api.post(`/api/puzzles/${encodeURIComponent(puzzle.id)}/answer`, {
        move: `${orig}${dest}${promotes ? "q" : ""}`,
      });
      if (!result.legal) {
        message.textContent = "Not a legal move, try again.";
        message.className = "puzzle-message error";
        cg.puzzleInstance.set({ fen: puzzle.fen, lastMove: undefined });
        return;
      }
      answered = true;
      cg.puzzleInstance.set({ movable: { color: undefined } });
      if (result.correct) {
        message.textContent = `Correct! ${result.solution_san}`;
        message.className = "puzzle-message success";
      } else {
        message.innerHTML = `Not quite. Best was <strong>${esc(result.solution_san)}</strong>.
          <a href="#/games/${encodeURIComponent(puzzle.game_id)}">Review the game</a>`;
        message.className = "puzzle-message info";
      }
      if (positions) {
        document.getElementById("puzzlePosition").textContent = "Game unlocked: ← → to see how it continued, ↓ to the end.";
      }
      document.getElementById("nextPuzzleBtn").hidden = false;
    } catch (e) {
      message.textContent = `Error: ${e.message}`;
      message.className = "puzzle-message error";
    }
  }

  document.getElementById("nextPuzzleBtn").addEventListener("click", () => {
    if (isLast) {
      main.querySelector(".puzzle-info").innerHTML = '<p>Session done. Come back tomorrow for the next batch.</p>';
      return;
    }
    state.currentPuzzleIndex += 1;
    renderPuzzles();
  });
}

function renderProgress() {
  const html = ['<div class="view-container"><div class="progress-view">'];

  if (!state.progress) {
    html.push(renderLoading());
    html.push("</div></div>");
    document.getElementById("main").innerHTML = html.join("");
    return;
  }

  const { current, previous } = state.progress;

  html.push('<div class="period-buttons">');
  [7, 30, 90].forEach((d) =>
    html.push(`<button data-days="${d}" class="period-btn${state.progress.days === d ? " active" : ""}">${d} days</button>`)
  );
  html.push("</div>");
  html.push(`<p class="muted">Last ${state.progress.days} days compared with the ${state.progress.days} days before.</p>`);

  html.push('<table class="progress-table">');
  html.push(
    "<tr><th>Metric</th><th>Previous</th><th>Last</th><th>Change</th></tr>"
  );

  const count = (v) => (v != null ? String(v) : "-");
  const signed = (v) => (v != null ? `${v > 0 ? "+" : ""}${v}` : "-");
  const decimal = (v) => (v != null ? v.toFixed(1) : "-");
  const metrics = [
    { label: "Games", key: "games", good: null, format: count },
    { label: "Score", key: "score_pct", good: "up", format: fmtScore },
    { label: "Rating change", key: "rating_change", good: "up", format: signed },
    { label: "Games in time trouble", key: "time_trouble_pct", good: "down", format: fmtScore },
    { label: "Losses on time", key: "losses_on_time_pct", good: "down", format: fmtScore },
    { label: "Analyzed games", key: "analyzed_games", good: null, format: count },
    { label: "Accuracy", key: "accuracy", good: "up", format: fmtScore },
    { label: "Mistakes + blunders per 100 moves", key: "serious_per_100", good: "down", format: decimal },
  ];

  metrics.forEach(({ label, key, good, format }) => {
    const fmt = format || ((v) => (v != null ? v : "-"));
    const prevVal = previous ? fmt(previous[key]) : "-";
    const currVal = current ? fmt(current[key]) : "-";

    let change = "-";
    let arrow = "";
    let arrowColor = "";

    if (previous && current && previous[key] != null && current[key] != null) {
      const diff = current[key] - previous[key];
      const isGood = (good === "up" && diff > 0) || (good === "down" && diff < 0);
      const isBad = (good === "up" && diff < 0) || (good === "down" && diff > 0);
      arrowColor = isGood ? "var(--good)" : isBad ? "var(--negative)" : "var(--text-2)";
      arrow = diff > 0 ? "▲" : diff < 0 ? "▼" : "=";
      change = `${arrow} ${Math.abs(diff).toFixed(Number.isInteger(diff) ? 0 : 1)}`;
    }

    html.push(
      `<tr><td>${label}</td><td>${prevVal}</td><td>${currVal}</td><td style="color: ${arrowColor}">${esc(change)}</td></tr>`
    );
  });

  html.push("</table>");
  html.push("</div></div>");

  document.getElementById("main").innerHTML = html.join("");

  document.querySelectorAll(".period-btn").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      document.querySelectorAll(".period-btn").forEach((b) => b.classList.remove("active"));
      e.target.classList.add("active");

      const days = e.target.getAttribute("data-days");
      try {
        state.progress = await api.get(`/api/progress/${state.selectedTimeClass}?days=${days}`);
        renderProgress();
      } catch (e) {
        console.error("Error loading progress:", e);
      }
    });
  });
}

// Loading functions
async function loadMeta() {
  try {
    state.meta = await api.get("/api/meta");
    state.username = state.meta.username;
    state.timeClasses = state.meta.time_classes;

    // Restore selected time class or use default
    let selected = localStorage.getItem("selectedTimeClass");
    if (!selected || !state.timeClasses.find((tc) => tc.time_class === selected)) {
      selected = state.timeClasses[0]?.time_class || "blitz";
    }
    state.selectedTimeClass = selected;

    renderHeader();
    renderTimeClassSelector();
  } catch (e) {
    console.error("Error loading meta:", e);
  }
}

async function loadInsights() {
  try {
    state.insights = await api.get(`/api/insights/${state.selectedTimeClass}`);
  } catch (e) {
    if (e.message.includes("404")) {
      state.insights = null; // 404 for no games
    } else {
      console.error("Error loading insights:", e);
      throw e;
    }
  }
}

async function loadGames() {
  try {
    const data = await api.get(
      `/api/games?time_class=${state.selectedTimeClass}&limit=50&offset=${state.gamesOffset}`
    );
    if (state.gamesOffset === 0) {
      state.games = data;
    } else {
      state.games = state.games.concat(data);
    }
  } catch (e) {
    console.error("Error loading games:", e);
  }
}

async function loadGame(id) {
  try {
    state.currentGame = await api.get(`/api/games/${id}`);
  } catch (e) {
    console.error("Error loading game:", e);
  }
}

async function loadPuzzles() {
  try {
    state.puzzles = await api.get(
      `/api/puzzles?time_class=${state.selectedTimeClass}&limit=10`
    );
    state.currentPuzzleIndex = 0;
  } catch (e) {
    console.error("Error loading puzzles:", e);
    state.puzzles = [];
  }
}

async function loadProgress(days = 30) {
  try {
    state.progress = await api.get(
      `/api/progress/${state.selectedTimeClass}?days=${days}`
    );
  } catch (e) {
    console.error("Error loading progress:", e);
  }
}

// Router
async function routeTo(route) {
  const parts = route.split("/");
  const view = parts[0];
  const param = parts[1];

  state.currentRoute = view;
  document.onkeydown = null;
  renderHeader();

  try {
    if (view === "overview") {
      await loadInsights();
      renderOverview();
    } else if (view === "games") {
      if (param) {
        const id = decodeURIComponent(param);
        await loadGame(id);
        renderGameViewer();
      } else {
        state.gamesOffset = 0;
        state.games = null;
        renderGames();
        await loadGames();
        renderGames();
      }
    } else if (view === "puzzles") {
      state.puzzles = null;
      renderPuzzles();
      await loadPuzzles();
      renderPuzzles();
    } else if (view === "progress") {
      await loadProgress();
      renderProgress();
    }
  } catch (e) {
    const main = document.getElementById("main");
    main.innerHTML = renderError("Failed to load: " + e.message);
  }
}

// Hash routing
window.addEventListener("hashchange", () => {
  const hash = window.location.hash.slice(2); // Remove #/
  routeTo(hash || "overview");
});

// Init
async function init() {
  await loadMeta();
  const hash = window.location.hash.slice(2);
  routeTo(hash || "overview");
}

init();
