/* ═══════════════════════════════════════════
   ClawRecord v4 — Client-Side Renderer
   ═══════════════════════════════════════════ */
(function () {
  "use strict";

  const isElectron = typeof window.clawrecord !== "undefined";

  if (isElectron && navigator.platform.includes("Mac")) {
    document.body.classList.add("electron-mac");
  }

  if (typeof D === "undefined" || window._dataLoadFailed) {
    if (isElectron && window._setupModule) {
      window._setupModule.showSetup();
      return;
    }
    document.getElementById("app").innerHTML =
      '<div style="text-align:center;padding:60px 20px;color:#777">' +
      '<div style="font-size:3rem;margin-bottom:12px">🐾</div>' +
      '<h2 style="margin-bottom:8px">No Data Yet</h2>' +
      "<p>Run the pipeline first:<br><code>python3 scripts/collect.py && python3 scripts/score.py && python3 scripts/generate_pages.py</code></p>" +
      "</div>";
    return;
  }

  const $ = (s, p) => (p || document).querySelector(s);
  const $$ = (s, p) => [...(p || document).querySelectorAll(s)];
  const h = (s) => { s = s == null ? "" : String(s); return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); };

  let lang = localStorage.getItem("cr-lang") || "en";
  const t = (obj) => {
    if (!obj) return "";
    if (typeof obj === "string") return obj;
    return obj[lang] || obj.en || "";
  };

  const U = D.user, C = D.config, Q = D.quests, A = D.analytics, CI = D.checkIns, T = D.tasks;

  /* ── i18n ─────────────────────────────── */
  const i18n = {
    en: {
      tab_home: "Home", tab_quests: "Quests", tab_skills: "Skills", tab_stats: "Stats", tab_profile: "Profile",
      claw_power: "Claw Power", level: "Level", streak: "Streak", hp: "HP", weekly_xp: "Wk XP",
      daily_quests: "Daily Quests", resets_in: "Resets in",
      journey: "Your Journey", beginner: "Beginner", intermediate: "Intermediate", advanced: "Advanced",
      beginner_d: "Learn OpenClaw basics", intermediate_d: "Master tools & track progress", advanced_d: "Compete globally",
      skills: "Skills", league: "League", next_league: "Next", activity: "Activity", less: "Less", more: "More",
      analytics: "Usage Analytics", achievements: "Achievements", records: "Personal Bests", recent: "Recent Activity",
      best_xp: "Best XP/Day", longest_streak: "Best Streak", best_session: "Best Session", best_tools: "Best Tools/Day",
      leaderboard: "Global Leaderboard", lb_desc: "Compete with OpenClaw users worldwide",
      join_lb: "Join the Leaderboard", share_x: "Share to X", updated: "Updated",
      b_tasks: ["Send first message", "Use a tool call", "Complete a session", "Unlock first badge", "Reach Lv.3"],
      i_tasks: ["7-day streak", "Gold league", "10 badges", "Skill to Lv.5", "Deploy dashboard"],
      a_tasks: ["Join leaderboard", "Diamond league", "Legend badge", "30-day streak", "Share on X"],
    },
    zh: {
      tab_home: "首页", tab_quests: "任务", tab_skills: "技能", tab_stats: "数据", tab_profile: "档案",
      claw_power: "龙虾战力", level: "等级", streak: "连胜", hp: "生命值", weekly_xp: "周XP",
      daily_quests: "每日三件套", resets_in: "重置倒计时",
      journey: "你的旅程", beginner: "新手", intermediate: "进阶", advanced: "资深",
      beginner_d: "学习 OpenClaw 基础", intermediate_d: "精通工具，追踪成长", advanced_d: "全球排行榜竞技",
      skills: "技能", league: "联赛", next_league: "下一", activity: "活动", less: "少", more: "多",
      analytics: "使用分析", achievements: "成就", records: "个人纪录", recent: "最近活动",
      best_xp: "最佳XP/日", longest_streak: "最长连胜", best_session: "最长会话", best_tools: "最多工具/日",
      leaderboard: "全球排行榜", lb_desc: "与全球 OpenClaw 用户竞技",
      join_lb: "加入排行榜", share_x: "分享到 X", updated: "更新于",
      b_tasks: ["发送第一条消息", "使用一次工具", "完成一次会话", "解锁第一个成就", "达到等级3"],
      i_tasks: ["7天连胜", "进入黄金联赛", "10个成就", "技能升到Lv.5", "部署仪表盘"],
      a_tasks: ["加入排行榜", "钻石联赛", "传奇徽章", "30天连胜", "分享到X"],
    }
  };
  const L = () => i18n[lang] || i18n.en;

  /* ── Helpers ──────────────────────────── */
  function fmtNum(n) {
    if (n >= 1e6) return (n / 1e6).toFixed(1) + "M";
    if (n >= 1e3) return (n / 1e3).toFixed(1) + "K";
    return String(n);
  }

  function animateCounter(el, target, duration) {
    if (!el) return;
    const start = 0;
    const startTime = performance.now();
    const comma = target >= 1000;
    function update(now) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const val = Math.round(start + (target - start) * eased);
      el.textContent = comma ? val.toLocaleString() : String(val);
      if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
  }

  function shareToX(text) {
    const url = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&hashtags=ClawRecord,OpenClaw`;
    window.open(url, "_blank", "noopener,width=600,height=400");
  }

  function getTimeUntilMidnight() {
    const now = new Date();
    const mid = new Date(now);
    mid.setUTCHours(24, 0, 0, 0);
    const diff = mid - now;
    const hrs = Math.floor(diff / 3600000);
    const mins = Math.floor((diff % 3600000) / 60000);
    return `${hrs}h ${mins}m`;
  }

  /* ── Level helpers ────────────────────── */
  function getLevelInfo() {
    const levels = C.levels;
    let cur = levels[0], next = null;
    for (const lv of levels) {
      if (lv.level <= U.level) cur = lv;
    }
    for (const lv of levels) {
      if (lv.xp_required > U.xp) { next = lv; break; }
    }
    let pct = 0;
    if (next) {
      pct = ((U.xp - cur.xp_required) / Math.max(next.xp_required - cur.xp_required, 1)) * 100;
    }
    return { cur, next, pct: Math.min(pct, 100) };
  }

  function getLeagueInfo() {
    const leagues = C.leagues;
    let idx = 0;
    for (let i = 0; i < leagues.length; i++) {
      if (leagues[i].id === (U.league && U.league.id)) idx = i;
    }
    const cur = leagues[idx];
    const next = leagues[idx + 1] || null;
    let pct = 100, xpNeeded = 0;
    if (next) {
      const range = next.min_weekly_xp - cur.min_weekly_xp;
      xpNeeded = Math.max(next.min_weekly_xp - U.weekly_xp, 0);
      pct = range > 0 ? Math.min(((U.weekly_xp - cur.min_weekly_xp) / range) * 100, 100) : 100;
    }
    return { idx, cur, next, pct, xpNeeded, leagues };
  }

  /* ── Share Card (Canvas) ──────────────── */
  function generateShareCard() {
    const canvas = $("#shareCanvas");
    const ctx = canvas.getContext("2d");
    const W = 600, H = 340;

    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, W, H);

    ctx.fillStyle = "#d7ffb8";
    ctx.fillRect(0, 0, W, 6);

    ctx.fillStyle = "#58CC02";
    ctx.font = "900 20px Inter, sans-serif";
    ctx.fillText("🐾 ClawRecord", 30, 44);

    ctx.fillStyle = "#afafaf";
    ctx.font = "700 11px Inter, sans-serif";
    ctx.fillText(L().claw_power.toUpperCase(), 30, 78);

    ctx.fillStyle = "#3c3c3c";
    ctx.font = "900 54px Inter, sans-serif";
    ctx.fillText(U.claw_power.toLocaleString(), 30, 136);

    ctx.fillStyle = "#58CC02";
    ctx.font = "800 14px Inter, sans-serif";
    const { cur } = getLevelInfo();
    ctx.fillText(`Lv.${U.level}  ${t(cur.rank)}`, 30, 166);

    const stats = [
      [`🔥 ${U.streak}`, L().streak],
      [`⚡ ${U.weekly_xp}`, L().weekly_xp],
      [`❤️ ${U.hp}`, L().hp],
    ];
    stats.forEach(([val, label], i) => {
      const x = 30 + i * 180;
      ctx.fillStyle = "#3c3c3c";
      ctx.font = "900 16px Inter, sans-serif";
      ctx.fillText(val, x, 216);
      ctx.fillStyle = "#afafaf";
      ctx.font = "700 10px Inter, sans-serif";
      ctx.fillText(label, x, 234);
    });

    ctx.fillStyle = "#e5e5e5";
    ctx.fillRect(30, 260, W - 60, 2);

    ctx.fillStyle = "#afafaf";
    ctx.font = "600 10px Inter, sans-serif";
    ctx.fillText(`@${U.username}  •  ${D.generated}`, 30, H - 24);

    const { cur: leagueCur } = getLeagueInfo();
    ctx.fillStyle = "#3c3c3c";
    ctx.font = "700 12px Inter, sans-serif";
    ctx.fillText(`${leagueCur.icon} ${t(leagueCur.name)}`, W - 140, 44);

    const badgeCount = U.badges ? U.badges.length : 0;
    ctx.fillText(`🏅 ${badgeCount} Badges`, W - 140, 66);

    return canvas.toDataURL("image/png");
  }

  /* ── Render: Home ─────────────────────── */
  function renderHome() {
    const l = L();
    const { cur, next, pct } = getLevelInfo();
    const nextXp = next ? next.xp_required.toLocaleString() : U.xp.toLocaleString();
    const mult = U.streak_multiplier > 1 ? `<span class="mult">🚀 x${U.streak_multiplier}</span>` : "";

    return `
<div class="content-row home-row">
<div class="content-col">
<div class="hero">
  <div class="hero-avatar"><div class="hero-avatar-inner">${U.avatar || cur.icon}</div></div>
  <div class="hero-rank">${h(t(cur.rank))}</div>
  <div class="hero-power-label">${h(l.claw_power)}</div>
  <div class="hero-power"><span class="counter" data-target="${U.claw_power}">0</span></div>
  <div class="hero-delta">+${U.today_xp} today ${mult}</div>
  <div class="xp-bar">
    <div class="xp-bar-fill" style="width:0%" data-w="${pct.toFixed(1)}%"></div>
    <span class="xp-bar-label">Lv.${U.level} — ${U.xp.toLocaleString()} / ${nextXp} XP</span>
  </div>
</div>
<div class="stat-row">
  <div class="stat-box"><div class="stat-val c-green">${U.level}</div><div class="stat-key">${h(l.level)}</div></div>
  <div class="stat-box"><div class="stat-val c-gold">🔥 <span class="counter" data-target="${U.streak}">0</span></div><div class="stat-key">${h(l.streak)}</div></div>
  <div class="stat-box"><div class="stat-val c-red">❤️ ${U.hp}</div><div class="stat-key">${h(l.hp)}</div></div>
  <div class="stat-box"><div class="stat-val c-blue">⚡ <span class="counter" data-target="${U.weekly_xp}">0</span></div><div class="stat-key">${h(l.weekly_xp)}</div></div>
</div>
</div>
${renderQuests()}
</div>
<div class="foot">${h(l.updated)}: ${D.generated}</div>`;
  }

  /* ── Render: Quests ───────────────────── */
  function renderQuests() {
    const l = L();
    const combo = Q.combo || {};
    const ch = Q.challenge || {};
    const st = Q.streak || {};

    const skillMap = {};
    C.skills.forEach(s => skillMap[s.id] = s);

    let comboPills = "";
    (combo.skills || []).forEach(sid => {
      const sk = skillMap[sid] || {};
      const on = (combo.activated_skills || []).includes(sid) ? " on" : "";
      comboPills += `<span class="quest-pill${on}">${sk.icon || ""} ${h(t(sk.name) || sid)}</span>`;
    });

    const comboPct = Math.min((combo.activated || 0) / Math.max(combo.total || 3, 1) * 100, 100);
    const chDesc = (t(ch.desc) || "").replace("{n}", String(ch.target || 0));
    const chPct = Math.min((ch.progress || 0) / Math.max(ch.target || 1, 1) * 100, 100);

    return `
<div class="section">
  <div class="section-title">🎯 ${h(l.daily_quests)}</div>
  <div class="quest-grid">
    <div class="quest${combo.complete ? " done" : ""}">
      <div class="quest-top">
        <div class="quest-icon">🎰</div>
        <div class="quest-info"><div class="quest-name">${h(t(((C.daily_quests||{}).combo||{}).name) || "Daily Combo")}</div></div>
        <div class="quest-xp">+${combo.xp_reward || 100} XP</div>
      </div>
      <div class="quest-pills">${comboPills}</div>
      <div class="quest-bar"><div class="quest-bar-fill" style="width:0%" data-w="${comboPct.toFixed(0)}%"></div></div>
      <div class="quest-stat">${combo.activated || 0}/${combo.total || 3}</div>
    </div>
    <div class="quest${ch.complete ? " done" : ""}">
      <div class="quest-top">
        <div class="quest-icon">⚔️</div>
        <div class="quest-info">
          <div class="quest-name">${h(t(ch.name) || "Challenge")}</div>
          <div class="quest-desc">${h(chDesc)}</div>
        </div>
        <div class="quest-xp">+${ch.xp_reward || 0} XP</div>
      </div>
      <div class="quest-bar"><div class="quest-bar-fill" style="width:0%" data-w="${chPct.toFixed(0)}%"></div></div>
      <div class="quest-stat">${ch.progress || 0}/${ch.target || 0}</div>
    </div>
    <div class="quest${st.complete ? " done" : ""}">
      <div class="quest-top">
        <div class="quest-icon">🔥</div>
        <div class="quest-info">
          <div class="quest-name">${h(t(((C.daily_quests||{}).streak||{}).name) || "Daily Streak")}</div>
          <div class="quest-desc">${h(t(((C.daily_quests||{}).streak||{}).desc) || "")}</div>
        </div>
      </div>
      <div class="quest-bar"><div class="quest-bar-fill" style="width:0%" data-w="${st.complete ? "100" : "0"}%"></div></div>
    </div>
  </div>
  <div class="quest-timer">⏰ ${h(l.resets_in)} ${getTimeUntilMidnight()}</div>
</div>`;
  }

  /* ── Render: Quests Page (with Journey) ─ */
  function renderQuestsPage() {
    const l = L();
    const badges = U.badges || [];
    const skills = U.skills || {};
    const leagueId = (U.league || {}).id || "bronze";
    const maxSkillLvl = Math.max(0, ...Object.values(skills).map(s => typeof s === "object" ? s.level || 0 : 0));
    const hasLegend = badges.some(b => b.tier >= 5);

    const bChecks = [U.xp > 0, Object.keys(skills).some(k => skills[k].xp > 0), badges.length > 0, badges.length >= 1, U.level >= 3];
    const iChecks = [U.streak >= 7, ["gold","sapphire","ruby","emerald","amethyst","pearl","obsidian","diamond"].includes(leagueId), badges.length >= 10, maxSkillLvl >= 5, true];
    const aChecks = [true, leagueId === "diamond", hasLegend, U.streak >= 30, true];

    function pathNode(title, desc, tasks, checks, color, idx) {
      const done = checks.filter(Boolean).length;
      const total = tasks.length;
      const pct = (done / total * 100).toFixed(0);
      const isActive = done < total && (idx === 0 || true);
      const cls = done >= total ? "done" : (isActive ? "active" : "");
      const taskHtml = tasks.map((t, i) => `<div class="path-task${checks[i] ? " checked" : ""}">${checks[i] ? "✅" : "⬜"} ${h(t)}</div>`).join("");
      return `<div class="path-node ${cls}">
        <div class="path-dot" style="background:${done >= total ? "var(--c-primary)" : color}">${done}/${total}</div>
        <div class="path-label">${h(title)}</div>
        <div class="path-sub">${h(desc)}</div>
        <div class="path-tasks">${taskHtml}</div>
        <div class="path-progress"><div class="path-progress-fill" style="width:0%" data-w="${pct}%"></div></div>
      </div>`;
    }

    return `
<div class="content-row">
${renderQuests()}
<div class="section">
  <div class="section-title">🗺️ ${h(l.journey)}</div>
  <div class="path-list">
    ${pathNode(l.beginner, l.beginner_d, l.b_tasks, bChecks, "#58CC02", 0)}
    ${pathNode(l.intermediate, l.intermediate_d, l.i_tasks, iChecks, "#FFC800", 1)}
    ${pathNode(l.advanced, l.advanced_d, l.a_tasks, aChecks, "#CE82FF", 2)}
  </div>
</div>
</div>`;
  }

  /* ── Render: Skills ───────────────────── */
  function renderSkills() {
    const l = L();
    const groups = C.skill_groups || {};
    const grouped = {};
    C.skills.forEach(s => { (grouped[s.group] = grouped[s.group] || []).push(s); });

    let skillHtml = "";
    for (const [gid, gConf] of Object.entries(groups)) {
      skillHtml += `<div class="skill-group-hdr">${gConf.icon || ""} ${h(t(gConf.name))}</div>`;
      (grouped[gid] || []).forEach(sk => {
        const sd = U.skills[sk.id] || {};
        const lvl = sd.level || 0;
        const xp = sd.xp || 0;
        const nextXp = sd.next_level_xp || sk.xp_per_level;
        const pct = lvl >= sk.max_level ? 100 : Math.min(xp / Math.max(nextXp, 1) * 100, 100);
        skillHtml += `<div class="skill">
          <div class="skill-top">
            <span class="skill-emoji">${sk.icon}</span>
            <span class="skill-name">${h(t(sk.name))}</span>
            <span class="skill-lvl">Lv.${lvl}<span style="color:var(--c-muted);font-weight:400">/${sk.max_level}</span></span>
          </div>
          <div class="skill-bar"><div class="skill-bar-fill" style="width:0%" data-w="${pct.toFixed(0)}%"></div></div>
        </div>`;
      });
    }

    const li = getLeagueInfo();
    let leagueItems = "";
    li.leagues.forEach((lg, i) => {
      const cls = i === li.idx ? "current" : i < li.idx ? "passed" : "";
      leagueItems += `<div class="league-item ${cls}"><div class="league-emoji">${lg.icon}</div><div class="league-name">${h(t(lg.name))}</div></div>`;
    });

    let leagueNext = "";
    if (li.next) {
      leagueNext = `<div class="league-next">
        <div class="league-next-top"><span class="league-next-label">${h(l.next_league)}: ${li.next.icon} ${h(t(li.next.name))}</span><span class="league-next-xp">${li.xpNeeded.toLocaleString()} XP</span></div>
        <div class="league-next-bar"><div class="league-next-fill" style="width:0%" data-w="${li.pct.toFixed(1)}%"></div></div>
      </div>`;
    }

    const hmCells = buildHeatmap();

    return `
<div class="content-row">
<div class="section">
  <div class="section-title">⚡ ${h(l.skills)}</div>
  <div class="skill-grid">${skillHtml}</div>
</div>
<div class="section">
  <div class="section-title">🏆 ${h(l.league)} <span class="dim">${h(l.weekly_xp)}: ${U.weekly_xp.toLocaleString()}</span></div>
  <div class="league-track">${leagueItems}</div>
  ${leagueNext}
</div>
</div>
<div class="section">
  <div class="section-title">📅 ${h(l.activity)}</div>
  <div class="heatmap">${hmCells}</div>
  <div class="hm-legend"><span>${h(l.less)}</span><div class="hm-cell hm-0"></div><div class="hm-cell hm-1"></div><div class="hm-cell hm-2"></div><div class="hm-cell hm-3"></div><div class="hm-cell hm-4"></div><span>${h(l.more)}</span></div>
</div>`;
  }

  function buildHeatmap() {
    const today = new Date();
    const start = new Date(today);
    start.setDate(start.getDate() - 90);
    const offset = start.getDay();
    let cells = "";
    for (let i = 0; i <= 90; i++) {
      const d = new Date(start);
      d.setDate(d.getDate() + i);
      const ds = d.toISOString().slice(0, 10);
      const ci = CI[ds] || {};
      const xp = ci.xp_gained || 0;
      const lvl = xp === 0 ? 0 : xp < 50 ? 1 : xp < 150 ? 2 : xp < 300 ? 3 : 4;
      const row = (offset + i) % 7 + 1;
      const col = Math.floor((offset + i) / 7) + 1;
      cells += `<div class="hm-cell hm-${lvl}" style="grid-row:${row};grid-column:${col}" title="${ds}: ${xp} XP"></div>`;
    }
    return cells;
  }

  /* ── Render: Stats ────────────────────── */
  function renderStats() {
    const l = L();
    const colors = ["#58CC02", "#1CB0F6", "#CE82FF", "#FFC800", "#FF4B4B", "#FF9600", "#E8548F", "#2BB8A4"];

    let statsGrid = "";
    const statItems = [
      [fmtNum(A.tokens_total || 0), "Tokens"],
      [`$${(A.cost_total || 0).toFixed(2)}`, "Cost"],
      [`${A.cache_hit_rate || 0}%`, "Cache"],
      [`$${(A.avg_cost_per_day || 0).toFixed(3)}`, "$/Day"],
      [fmtNum(A.avg_tokens_per_msg || 0), "Tok/Msg"],
      [String(A.total_sessions || 0), "Sessions"],
    ];
    statItems.forEach(([v, k]) => { statsGrid += `<div class="ana-box"><div class="ana-val">${v}</div><div class="ana-key">${k}</div></div>`; });

    function barPanel(title, data, tokData) {
      const sorted = Object.entries(data || {}).filter(([, p]) => p > 0).sort((a, b) => b[1] - a[1]);
      let rows = "";
      sorted.forEach(([name, pct], i) => {
        const short = name.includes("/") ? name.split("/").pop() : name;
        const tok = tokData ? fmtNum((tokData[name] || 0)) : "";
        const color = colors[i % colors.length];
        rows += `<div class="ana-bar-row"><div class="ana-bar-label">${h(short)}</div><div class="ana-bar-track"><div class="ana-bar-fill" style="width:0%;background:${color}" data-w="${pct}%"></div></div><div class="ana-bar-pct">${pct}%${tok ? " " + tok : ""}</div></div>`;
      });
      return `<div class="ana-panel"><div class="ana-panel-title">${title}</div>${rows}</div>`;
    }

    const trend = A.daily_trend || [];
    let sparkHtml = "";
    if (trend.length) {
      const maxTok = Math.max(...trend.map(d => d.tokens || 0), 1);
      trend.forEach(d => {
        const hPct = Math.max((d.tokens || 0) / maxTok * 100, 2);
        sparkHtml += `<div class="ana-spark-bar" style="height:${hPct.toFixed(0)}%" title="${d.date}: ${fmtNum(d.tokens)} tok"></div>`;
      });
    }

    let toolBars = "";
    const topTools = (A.top_tools || []).slice(0, 6);
    const maxTool = Math.max(...topTools.map(t => t.count), 1);
    topTools.forEach((tool, i) => {
      const pct = (tool.count / maxTool * 100).toFixed(0);
      toolBars += `<div class="ana-bar-row"><div class="ana-bar-label">${h(tool.name)}</div><div class="ana-bar-track"><div class="ana-bar-fill" style="width:0%;background:${colors[i % colors.length]}" data-w="${pct}%"></div></div><div class="ana-bar-pct">${tool.count}</div></div>`;
    });

    const rec = U.personal_records || {};

    let actHtml = "";
    const recent = (T || []).slice().sort((a, b) => b.date.localeCompare(a.date)).slice(0, 6);
    if (recent.length) {
      recent.forEach(task => {
        actHtml += `<div class="act-row"><span class="act-date">${task.date}</span><span class="act-desc">${h(task.description)}</span><span class="act-xp">+${task.xp_gained}</span><span class="act-cx ${task.complexity}">${task.complexity}</span></div>`;
      });
    } else {
      actHtml = `<div class="empty">No activity yet</div>`;
    }

    return `
<div class="section">
  <div class="section-title">📊 ${h(l.analytics)}</div>
  <div class="ana-grid">${statsGrid}</div>
  <div class="ana-panels-row">
  ${barPanel("🤖 Models", A.model_share, A.model_tokens)}
  ${barPanel("☁️ Providers", A.provider_share, A.provider_tokens)}
  </div>
  <div class="ana-panels-row">
  ${sparkHtml ? `<div class="ana-panel"><div class="ana-panel-title">📈 Trend</div><div class="ana-spark">${sparkHtml}</div></div>` : ""}
  ${toolBars ? `<div class="ana-panel"><div class="ana-panel-title">🔧 Tools</div>${toolBars}</div>` : ""}
  </div>
</div>
<div class="content-row">
<div class="section">
  <div class="section-title">🥇 ${h(l.records)}</div>
  <div class="rec-grid">
    <div class="rec"><div class="rec-icon">⚡</div><div class="rec-val">${(rec.best_daily_xp || 0).toLocaleString()}</div><div class="rec-label">${h(l.best_xp)}</div></div>
    <div class="rec"><div class="rec-icon">🔥</div><div class="rec-val">${rec.longest_streak || 0}d</div><div class="rec-label">${h(l.longest_streak)}</div></div>
    <div class="rec"><div class="rec-icon">💬</div><div class="rec-val">${rec.best_session_turns || 0}</div><div class="rec-label">${h(l.best_session)}</div></div>
    <div class="rec"><div class="rec-icon">🔧</div><div class="rec-val">${rec.best_daily_tools || 0}</div><div class="rec-label">${h(l.best_tools)}</div></div>
  </div>
</div>
<div class="section">
  <div class="section-title">📋 ${h(l.recent)}</div>
  <div class="act-list">${actHtml}</div>
</div>
</div>`;
  }

  /* ── Render: Profile ──────────────────── */
  function renderProfile() {
    const l = L();
    const allBadges = C.badges || [];
    const unlocked = {};
    (U.badges || []).forEach(b => unlocked[b.id] = b);

    const tierStyles = C.badge_tier_styles || {};
    const catLabels = {
      milestone: { en: "Milestones", zh: "里程碑" }, streak: { en: "Streaks", zh: "连续" },
      skill: { en: "Skills", zh: "技能" }, tool: { en: "Tools", zh: "工具" },
      efficiency: { en: "Efficiency", zh: "效率" }, time: { en: "Time", zh: "时间" },
      special: { en: "Special", zh: "特殊" }
    };

    const byCat = {};
    allBadges.forEach(b => { (byCat[b.category] = byCat[b.category] || []).push(b); });

    let badgeHtml = "";
    for (const [cat, list] of Object.entries(byCat)) {
      badgeHtml += `<div class="badge-cat-title">${h(t(catLabels[cat]) || cat)}</div>`;
      list.forEach(badge => {
        const u = unlocked[badge.id];
        if (u) {
          const tier = u.tier || 1;
          const maxT = u.max_tier || badge.tiers.length;
          const ts = tierStyles[String(tier)] || {};
          const stars = "⭐".repeat(ts.stars || tier);
          let pct = 100;
          if (u.next_tier_value && u.next_tier_value > 0) {
            const curVal = (badge.tiers.find(t => t.tier === tier) || {}).value || 0;
            const range = u.next_tier_value - curVal;
            if (range > 0) pct = Math.min((u.metric - curVal) / range * 100, 100);
          }
          badgeHtml += `<div class="badge badge-t${Math.min(tier, 5)}" title="${h(u.tier_label || "")}">
            <div class="badge-icon">${badge.icon}</div>
            <div class="badge-name">${h(t(badge.name))}</div>
            <div class="badge-stars">${stars}</div>
            <div class="badge-bar"><div class="badge-bar-fill" style="width:${pct.toFixed(0)}%"></div></div>
            <div class="badge-tier">T${tier}/${maxT}</div>
          </div>`;
        } else {
          badgeHtml += `<div class="badge locked"><div class="badge-icon">🔒</div><div class="badge-name">${h(t(badge.name))}</div></div>`;
        }
      });
    }

    const badgeCount = (U.badges || []).length;
    const { cur } = getLevelInfo();
    const li = getLeagueInfo();
    const shareText = `I'm a Lv.${U.level} ${t(cur.rank)} on ClawRecord with ${U.claw_power.toLocaleString()} Claw Power! 🐾`;

    return `
<div class="section" style="text-align:center">
  <div class="hero-avatar" style="margin:0 auto 8px"><div class="hero-avatar-inner">${U.avatar || cur.icon}</div></div>
  <div style="font-weight:800;font-size:1.1rem;margin-bottom:2px">${h(U.username)}</div>
  <div style="font-size:.75rem;color:var(--c-sub);font-family:var(--mono);margin-bottom:12px">Lv.${U.level} ${h(t(cur.rank))} • ${li.cur.icon} ${h(t(li.cur.name))}</div>
  <div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap">
    <button class="share-btn" onclick="window._shareX()">
      <svg viewBox="0 0 24 24"><path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z" fill="currentColor"/></svg>
      ${h(l.share_x)}
    </button>
    <button class="share-btn" onclick="window._shareCard()">📷 Card</button>
  </div>
</div>
<div class="section">
  <div class="section-title">🏅 ${h(l.achievements)} <span class="dim">${badgeCount}/${allBadges.length}</span></div>
  <div class="badge-grid">${badgeHtml}</div>
</div>
<div class="lb-cta">
  <div class="lb-title">🌍 ${h(l.leaderboard)}</div>
  <div class="lb-desc">${h(l.lb_desc)}</div>
  <div class="lb-stats">
    <div class="lb-stat"><div class="lb-stat-val">${U.claw_power.toLocaleString()}</div><div class="lb-stat-key">Power</div></div>
    <div class="lb-stat"><div class="lb-stat-val">${li.cur.icon} ${h(t(li.cur.name))}</div><div class="lb-stat-key">${h(l.league)}</div></div>
    <div class="lb-stat"><div class="lb-stat-val">${badgeCount}</div><div class="lb-stat-key">Badges</div></div>
  </div>
  <a href="https://github.com/luka2chat/clawrecord-leaderboard" target="_blank" class="lb-btn">🏆 ${h(l.join_lb)}</a>
</div>`;
  }

  /* ── Tab Router ───────────────────────── */
  const pages = {
    home: renderHome,
    quests: renderQuestsPage,
    skills: renderSkills,
    stats: renderStats,
    profile: renderProfile,
  };

  let currentTab = "home";

  function navigate(tab) {
    currentTab = tab;
    location.hash = tab;
    $$(".tab").forEach(t => t.classList.toggle("active", t.dataset.tab === tab));
    $$(".sb-item").forEach(t => t.classList.toggle("active", t.dataset.tab === tab));
    const app = $("#app");
    const renderer = pages[tab] || pages.home;

    const refreshBtn = isElectron
      ? `<button class="topbar-btn" onclick="window._refreshData()" title="Refresh" id="refresh-btn">🔄</button>`
      : "";

    const topbar = `<div class="topbar">
      <div class="topbar-brand">🐾 ClawRecord</div>
      <div class="topbar-r">
        ${refreshBtn}
        <div class="lang-sw">
          <button class="${lang === "en" ? "active" : ""}" onclick="window._setLang('en')">EN</button>
          <button class="${lang === "zh" ? "active" : ""}" onclick="window._setLang('zh')">ZH</button>
        </div>
      </div>
    </div>`;

    app.innerHTML = topbar + renderer();
    updateNavLabels();
    app.scrollTop = 0;
    window.scrollTo(0, 0);

    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        $$("[data-w]").forEach(el => { el.style.width = el.dataset.w; });
        $$(".counter[data-target]").forEach(el => {
          animateCounter(el, parseInt(el.dataset.target, 10), 800);
        });
      });
    });
  }

  /* ── Global handlers ──────────────────── */
  window._shareX = function () {
    const { cur } = getLevelInfo();
    shareToX(`I'm a Lv.${U.level} ${t(cur.rank)} on ClawRecord with ${U.claw_power.toLocaleString()} Claw Power! 🐾`);
  };

  window._shareCard = function () {
    const dataUrl = generateShareCard();
    const link = document.createElement("a");
    link.download = "clawrecord-card.png";
    link.href = dataUrl;
    link.click();
  };

  window._setLang = function (newLang) {
    lang = newLang;
    localStorage.setItem("cr-lang", lang);
    navigate(currentTab);
  };

  /* ── Electron refresh ─────────────────── */
  if (isElectron) {
    window._refreshData = async function () {
      const btn = document.getElementById("refresh-btn");
      if (btn) { btn.textContent = "⏳"; btn.disabled = true; }
      try {
        const result = await window.clawrecord.refreshData();
        if (result.success) {
          window.location.reload();
        } else {
          if (btn) btn.textContent = "❌";
          setTimeout(() => { if (btn) { btn.textContent = "🔄"; btn.disabled = false; } }, 2000);
        }
      } catch {
        if (btn) btn.textContent = "❌";
        setTimeout(() => { if (btn) { btn.textContent = "🔄"; btn.disabled = false; } }, 2000);
      }
    };
  }

  function updateNavLabels() {
    const l = L();
    $$("#tabs [data-i18n], #sidebar [data-i18n]").forEach(el => {
      const key = el.dataset.i18n;
      if (l[key]) el.textContent = l[key];
    });
  }

  /* ── Init ─────────────────────────────── */
  $$(".tab").forEach(tabEl => {
    tabEl.addEventListener("click", () => navigate(tabEl.dataset.tab));
  });
  $$(".sb-item").forEach(item => {
    item.addEventListener("click", () => navigate(item.dataset.tab));
  });

  const hash = location.hash.replace("#", "");
  navigate(pages[hash] ? hash : "home");
})();
