#!/usr/bin/env python3
"""
ClawRecord Dashboard Generator

Reads user_stats, tasks, config, check_ins and produces
a beautiful static HTML dashboard with:
  - Profile card with evolution avatar
  - XP progress bar
  - Stats grid (Level, Streak, HP, Weekly XP, League)
  - Skill radar chart (SVG)
  - Achievement wall (locked / unlocked)
  - Activity heatmap (last 90 days)
  - Recent activity log
"""

import json
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import DATA_DIR, OUTPUT_DIR, get_text, load_json

OUTPUT_DIR.mkdir(exist_ok=True)


# ── SVG Radar Chart ─────────────────────────────────────────────────

def build_radar_svg(skills_data, config_skills, lang):
    """Generate an SVG radar chart for skills."""
    n = len(config_skills)
    if n < 3:
        return ""
    cx, cy, r = 120, 120, 90
    angle_step = 2 * math.pi / n

    grid_lines = []
    for ring in [0.25, 0.5, 0.75, 1.0]:
        points = []
        for i in range(n):
            a = -math.pi / 2 + i * angle_step
            px = cx + r * ring * math.cos(a)
            py = cy + r * ring * math.sin(a)
            points.append(f"{px:.1f},{py:.1f}")
        grid_lines.append(f'<polygon points="{" ".join(points)}" fill="none" stroke="rgba(148,163,184,0.15)" stroke-width="1"/>')

    axis_lines = []
    labels = []
    data_points = []
    for i, skill in enumerate(config_skills):
        a = -math.pi / 2 + i * angle_step
        ex = cx + r * math.cos(a)
        ey = cy + r * math.sin(a)
        axis_lines.append(f'<line x1="{cx}" y1="{cy}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="rgba(148,163,184,0.1)" stroke-width="1"/>')

        lx = cx + (r + 28) * math.cos(a)
        ly = cy + (r + 28) * math.sin(a)
        anchor = "middle"
        if lx < cx - 10:
            anchor = "end"
        elif lx > cx + 10:
            anchor = "start"
        label = get_text(skill["name"], lang)
        level = skills_data.get(skill["id"], 0)
        labels.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" dominant-baseline="middle" fill="#94a3b8" font-size="11">{skill["icon"]} {label} ({level})</text>')

        ratio = min(level / skill["max_level"], 1.0) if skill["max_level"] > 0 else 0
        dx = cx + r * ratio * math.cos(a)
        dy = cy + r * ratio * math.sin(a)
        data_points.append(f"{dx:.1f},{dy:.1f}")

    polygon = f'<polygon points="{" ".join(data_points)}" fill="rgba(34,197,94,0.2)" stroke="#22c55e" stroke-width="2"/>'
    dots = "".join(
        f'<circle cx="{p.split(",")[0]}" cy="{p.split(",")[1]}" r="3" fill="#22c55e"/>'
        for p in data_points
    )

    return f'''<svg viewBox="0 0 240 240" class="radar-chart">
    {"".join(grid_lines)}
    {"".join(axis_lines)}
    {polygon}
    {dots}
    {"".join(labels)}
    </svg>'''


# ── Heatmap ─────────────────────────────────────────────────────────

def build_heatmap(check_ins, lang):
    today = datetime.utcnow().date()
    start = today - timedelta(days=89)
    cells = []
    for i in range(90):
        d = start + timedelta(days=i)
        ds = d.strftime("%Y-%m-%d")
        ci = check_ins.get(ds, {})
        xp = ci.get("xp_gained", 0)
        if xp == 0:
            level = 0
        elif xp < 50:
            level = 1
        elif xp < 150:
            level = 2
        elif xp < 300:
            level = 3
        else:
            level = 4
        cells.append(f'<div class="hm-cell hm-{level}" title="{ds}: {xp} XP"></div>')
    return "".join(cells)


# ── Dashboard HTML ──────────────────────────────────────────────────

def generate_dashboard(user_stats, tasks, config, check_ins, lang):
    ui = {k: get_text(v, lang) for k, v in config["ui_text"].items()}

    level_info = next(
        (l for l in reversed(config["levels"]) if l["level"] <= user_stats["level"]),
        config["levels"][0],
    )
    next_level = None
    for lv in config["levels"]:
        if lv["xp_required"] > user_stats["xp"]:
            next_level = lv
            break
    xp_progress = 0
    if next_level:
        prev_xp = level_info["xp_required"]
        xp_progress = ((user_stats["xp"] - prev_xp) / max(next_level["xp_required"] - prev_xp, 1)) * 100

    lang_links = " ".join(
        f'<a href="{"index.html" if l == "en" else f"index_{l}.html"}" '
        f'class="lang-btn {"active" if l == lang else ""}">{l.upper()}</a>'
        for l in config["supported_languages"]
    )

    league = user_stats.get("league", {})
    league_conf = next((lg for lg in config["leagues"] if lg["id"] == league.get("id")), config["leagues"][0])
    league_name = get_text(league_conf["name"], lang)

    radar_svg = build_radar_svg(user_stats.get("skills", {}), config["skills"], lang)
    heatmap_html = build_heatmap(check_ins, lang)

    # Achievements
    unlocked_ids = {b["id"] for b in user_stats.get("badges", [])}
    badges_html_parts = []
    for badge in config["badges"]:
        is_unlocked = badge["id"] in unlocked_ids
        cls = "badge-item unlocked" if is_unlocked else "badge-item locked"
        name = get_text(badge["name"], lang)
        desc = get_text(badge["description"], lang)
        icon = badge["icon"] if is_unlocked else "🔒"
        badges_html_parts.append(
            f'<div class="{cls}" title="{desc}">'
            f'<span class="badge-icon">{icon}</span>'
            f'<span class="badge-name">{name}</span>'
            f'</div>'
        )
    badges_html = "".join(badges_html_parts)

    # Recent tasks (last 10)
    recent = sorted(tasks, key=lambda t: t["date"], reverse=True)[:10]
    tasks_html = ""
    if recent:
        rows = "".join(
            f'<div class="task-row">'
            f'<span class="task-date">{t["date"]}</span>'
            f'<span class="task-desc">{t["description"]}</span>'
            f'<span class="task-xp">+{t["xp_gained"]} XP</span>'
            f'<span class="task-complexity cx-{t["complexity"]}">{t["complexity"]}</span>'
            f'</div>'
            for t in recent
        )
        tasks_html = f'<div class="tasks-list">{rows}</div>'
    else:
        tasks_html = f'<p class="empty-msg">{ui["empty_tasks"]}</p>'

    streak_freeze_text = ""
    sf = user_stats.get("streak_freezes", 0)
    if sf > 0:
        freeze_label = get_text(config["ui_text"]["streak_freeze"], lang)
        streak_freeze_text = f'<span class="freeze-badge" title="{freeze_label}">🧊 x{sf}</span>'

    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{ui["title"]} — {user_stats["username"]}</title>
<link rel="stylesheet" href="styles.css">
</head>
<body>
<div class="container">
  <nav class="top-bar">
    <span class="logo">🐾 {ui["title"]}</span>
    <div class="nav-right">
      <span class="league-badge">{league_conf["icon"]} {league_name}</span>
      {lang_links}
    </div>
  </nav>

  <section class="profile-card">
    <div class="avatar-area">
      <div class="avatar-circle">{user_stats.get("avatar", level_info["icon"])}</div>
      <div class="evolution-label">{get_text(level_info["rank"], lang)}</div>
    </div>
    <div class="profile-info">
      <h1 class="username">{user_stats["username"]}</h1>
      <div class="xp-bar-container">
        <div class="xp-bar" style="width:{xp_progress:.1f}%"></div>
        <span class="xp-text">{user_stats["xp"]} / {next_level["xp_required"] if next_level else user_stats["xp"]} XP</span>
      </div>
      <div class="stats-row">
        <div class="stat-chip"><span class="stat-val">Lv.{user_stats["level"]}</span><span class="stat-label">{ui["level"]}</span></div>
        <div class="stat-chip"><span class="stat-val">🔥 {user_stats["streak"]}</span>{streak_freeze_text}<span class="stat-label">{ui["streak"]}</span></div>
        <div class="stat-chip"><span class="stat-val">❤️ {user_stats["hp"]}/{user_stats["max_hp"]}</span><span class="stat-label">{ui["hp"]}</span></div>
        <div class="stat-chip"><span class="stat-val">⚡ {user_stats.get("weekly_xp", 0)}</span><span class="stat-label">{ui["weekly_xp"]}</span></div>
      </div>
    </div>
  </section>

  <div class="two-col">
    <section class="card">
      <h2>{ui["skills_tree"]}</h2>
      <div class="radar-wrap">{radar_svg}</div>
    </section>
    <section class="card">
      <h2>{ui["league"]}</h2>
      <div class="league-display">
        <span class="league-icon-large">{league_conf["icon"]}</span>
        <span class="league-name-large">{league_name}</span>
        <div class="league-xp">{ui["weekly_xp"]}: <strong>{user_stats.get("weekly_xp", 0)}</strong></div>
      </div>
      <div class="league-tiers">
        {"".join(f'<div class="tier {"active" if lg["id"] == league.get("id") else ""}"><span>{lg["icon"]}</span><small>{get_text(lg["name"], lang)}</small><small>{lg["min_weekly_xp"]}+</small></div>' for lg in config["leagues"])}
      </div>
    </section>
  </div>

  <section class="card">
    <h2>{ui["heatmap"]}</h2>
    <div class="heatmap-grid">{heatmap_html}</div>
    <div class="heatmap-legend">
      <span>{ui["less"]}</span>
      <div class="hm-cell hm-0"></div><div class="hm-cell hm-1"></div><div class="hm-cell hm-2"></div><div class="hm-cell hm-3"></div><div class="hm-cell hm-4"></div>
      <span>{ui["more"]}</span>
    </div>
  </section>

  <section class="card achievements-card">
    <h2>{ui["achievements"]} <span class="badge-count">{len(user_stats.get("badges", []))} / {len(config["badges"])}</span></h2>
    <div class="badges-grid">{badges_html}</div>
  </section>

  <section class="card">
    <h2>{ui["recent_tasks"]}</h2>
    {tasks_html}
  </section>

  <footer class="footer">
    <p>{ui["last_updated"]}: {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}</p>
    <p class="powered">Powered by <a href="https://github.com/openclaw/openclaw">OpenClaw</a> &amp; GitHub Actions</p>
  </footer>
</div>
</body>
</html>'''


def generate_css():
    return '''/* ClawRecord 2.0 Dashboard */
:root {
  --bg: #0b1120;
  --surface: #131c31;
  --card: #182240;
  --border: #1e2d4a;
  --primary: #22c55e;
  --primary-dim: rgba(34,197,94,.15);
  --accent: #3b82f6;
  --text: #e2e8f0;
  --text-dim: #94a3b8;
  --text-muted: #64748b;
  --danger: #ef4444;
  --warning: #f59e0b;
  --radius: 12px;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--text);line-height:1.5;min-height:100vh}
a{color:var(--primary);text-decoration:none}
.container{max-width:880px;margin:0 auto;padding:16px 20px}

/* Top bar */
.top-bar{display:flex;justify-content:space-between;align-items:center;padding:12px 0;margin-bottom:20px;border-bottom:1px solid var(--border)}
.logo{font-size:1.2em;font-weight:700;letter-spacing:-.02em}
.nav-right{display:flex;align-items:center;gap:10px}
.league-badge{background:var(--card);padding:4px 12px;border-radius:20px;font-size:.85em;border:1px solid var(--border)}
.lang-btn{color:var(--text-dim);padding:4px 10px;border:1px solid var(--border);border-radius:6px;font-size:.8em;transition:all .2s}
.lang-btn.active{background:var(--primary);color:#fff;border-color:var(--primary)}

/* Profile card */
.profile-card{display:flex;gap:24px;align-items:center;background:linear-gradient(135deg,var(--card),var(--surface));padding:28px;border-radius:var(--radius);border:1px solid var(--border);margin-bottom:20px}
.avatar-area{text-align:center;flex-shrink:0}
.avatar-circle{width:88px;height:88px;border-radius:50%;background:var(--primary-dim);display:flex;align-items:center;justify-content:center;font-size:44px;border:3px solid var(--primary);margin:0 auto 6px;animation:pulse 3s ease-in-out infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(34,197,94,.3)}50%{box-shadow:0 0 20px 6px rgba(34,197,94,.15)}}
.evolution-label{font-size:.75em;color:var(--primary);font-weight:600;letter-spacing:.04em;text-transform:uppercase}
.profile-info{flex:1;min-width:0}
.username{font-size:1.6em;font-weight:700;margin-bottom:8px}
.xp-bar-container{position:relative;height:20px;background:var(--surface);border-radius:10px;overflow:hidden;margin-bottom:14px;border:1px solid var(--border)}
.xp-bar{height:100%;background:linear-gradient(90deg,#16a34a,#22c55e,#4ade80);border-radius:10px;transition:width .6s ease}
.xp-text{position:absolute;top:0;left:0;right:0;bottom:0;display:flex;align-items:center;justify-content:center;font-size:.72em;font-weight:600;color:#fff;text-shadow:0 1px 2px rgba(0,0,0,.4)}
.stats-row{display:flex;gap:10px;flex-wrap:wrap}
.stat-chip{background:var(--surface);padding:8px 14px;border-radius:8px;border:1px solid var(--border);text-align:center;min-width:80px;flex:1}
.stat-val{display:block;font-size:1.1em;font-weight:700;color:var(--primary)}
.stat-label{display:block;font-size:.7em;color:var(--text-dim);margin-top:2px}
.freeze-badge{font-size:.7em;margin-left:4px;vertical-align:middle}

/* Cards */
.card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:22px;margin-bottom:16px}
.card h2{font-size:1.05em;font-weight:600;margin-bottom:16px;display:flex;align-items:center;gap:8px}
.badge-count{font-size:.75em;color:var(--text-dim);font-weight:400;margin-left:auto}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:640px){.two-col{grid-template-columns:1fr}.profile-card{flex-direction:column;text-align:center}.stats-row{justify-content:center}}

/* Radar */
.radar-wrap{display:flex;justify-content:center;padding:8px 0}
.radar-chart{width:100%;max-width:260px;height:auto}

/* League */
.league-display{text-align:center;padding:12px 0}
.league-icon-large{font-size:2.5em;display:block}
.league-name-large{font-size:1.1em;font-weight:600;display:block;margin:4px 0}
.league-xp{font-size:.85em;color:var(--text-dim)}
.league-tiers{display:flex;gap:6px;margin-top:16px}
.tier{flex:1;text-align:center;padding:8px 4px;border-radius:8px;background:var(--surface);border:1px solid var(--border);opacity:.5;transition:all .2s}
.tier.active{opacity:1;border-color:var(--primary);box-shadow:0 0 8px rgba(34,197,94,.2)}
.tier span{display:block;font-size:1.2em}
.tier small{display:block;font-size:.6em;color:var(--text-dim)}

/* Heatmap */
.heatmap-grid{display:grid;grid-template-columns:repeat(18,1fr);gap:3px}
.hm-cell{aspect-ratio:1;border-radius:2px;min-width:0}
.hm-0{background:#1e293b}.hm-1{background:#064e3b}.hm-2{background:#047857}.hm-3{background:#10b981}.hm-4{background:#34d399}
.heatmap-legend{display:flex;align-items:center;gap:4px;justify-content:flex-end;margin-top:8px;font-size:.7em;color:var(--text-dim)}
.heatmap-legend .hm-cell{width:12px;height:12px;display:inline-block}

/* Achievements */
.badges-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(90px,1fr));gap:8px}
.badge-item{text-align:center;padding:10px 6px;border-radius:8px;border:1px solid var(--border);transition:transform .15s,box-shadow .15s;cursor:default}
.badge-item:hover{transform:translateY(-2px)}
.badge-item.unlocked{background:var(--surface);border-color:rgba(34,197,94,.3)}
.badge-item.unlocked:hover{box-shadow:0 4px 12px rgba(34,197,94,.15)}
.badge-item.locked{background:var(--bg);opacity:.4}
.badge-icon{display:block;font-size:1.6em;margin-bottom:4px}
.badge-name{display:block;font-size:.62em;color:var(--text-dim);line-height:1.3;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.badge-item.unlocked .badge-name{color:var(--text)}

/* Tasks */
.tasks-list{display:flex;flex-direction:column;gap:6px}
.task-row{display:flex;align-items:center;gap:10px;padding:8px 12px;background:var(--surface);border-radius:8px;font-size:.85em;border:1px solid var(--border)}
.task-date{color:var(--text-dim);min-width:80px;font-size:.8em}
.task-desc{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.task-xp{color:var(--primary);font-weight:600;white-space:nowrap}
.task-complexity{font-size:.7em;padding:2px 8px;border-radius:10px;text-transform:uppercase;font-weight:600}
.cx-low{background:rgba(34,197,94,.15);color:#4ade80}
.cx-medium{background:rgba(245,158,11,.15);color:#fbbf24}
.cx-high{background:rgba(239,68,68,.15);color:#f87171}
.empty-msg{color:var(--text-dim);text-align:center;padding:20px;font-size:.9em}

/* Footer */
.footer{text-align:center;padding:24px 0 12px;color:var(--text-muted);font-size:.75em}
.powered{margin-top:4px}
.powered a{color:var(--primary)}
'''


def main():
    u = load_json(DATA_DIR / "user_stats.json")
    t = load_json(DATA_DIR / "tasks.json")
    c = load_json(DATA_DIR / "config.json")
    ci = load_json(DATA_DIR / "check_ins.json")

    for lang in c["supported_languages"]:
        filename = "index.html" if lang == "en" else f"index_{lang}.html"
        html = generate_dashboard(u, t, c, ci, lang)
        with open(OUTPUT_DIR / filename, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[generate] Written {filename}")

    with open(OUTPUT_DIR / "styles.css", "w", encoding="utf-8") as f:
        f.write(generate_css())
    print("[generate] Written styles.css")


if __name__ == "__main__":
    main()
