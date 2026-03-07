<div align="center">

# 🎮 ClawRecord

[![GitHub stars](https://img.shields.io/github/stars/luka2chat/clawrecord?style=social)](https://github.com/luka2chat/clawrecord/stargazers)
[![License](https://img.shields.io/github/license/luka2chat/clawrecord?color=blue)](LICENSE)
[![Last Updated](https://img.shields.io/github/last-commit/luka2chat/clawrecord?label=last%20updated&color=green)](https://github.com/luka2chat/clawrecord/commits/main)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-compatible-orange?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJMNCAyMGgyMEwxMiAyeiIgZmlsbD0id2hpdGUiLz48L3N2Zz4=)](https://github.com/openclaw/openclaw)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-16+-339933?logo=node.js&logoColor=white)](https://nodejs.org)

**Gamified OpenClaw Tracking — XP, levels, achievements, global leaderboard**

[English](./README.md) | [简体中文](./README_CN.md) | [Live Demo →](https://luka2chat.github.io/clawrecord/)

</div>

---

> 🕹️ Duolingo for your AI assistant — ClawRecord automatically tracks your [OpenClaw](https://github.com/openclaw/openclaw) usage and turns it into a gamified experience.

**Your AI grows. You get the credit. No cheating allowed.**

---

## 📸 Screenshots

<!-- TODO: Replace placeholders with actual screenshots/GIFs -->

<div align="center">

| Dashboard Overview | Achievement Wall | Activity Heatmap |
|:---:|:---:|:---:|
| ![Dashboard](https://via.placeholder.com/350x220/1a1a2e/e94560?text=Dashboard+Overview) | ![Achievements](https://via.placeholder.com/350x220/16213e/0f3460?text=Achievement+Wall) | ![Heatmap](https://via.placeholder.com/350x220/1a1a2e/53a653?text=Activity+Heatmap) |
| XP, level, streak, HP at a glance | 47 achievements across 7 categories | 90-day visual activity map |

| Skill Cards | League Ranking | Daily Quests |
|:---:|:---:|:---:|
| ![Skills](https://via.placeholder.com/350x220/0f3460/e94560?text=Skill+Cards) | ![League](https://via.placeholder.com/350x220/533483/e94560?text=League+Ranking) | ![Quests](https://via.placeholder.com/350x220/1a1a2e/f0a500?text=Daily+Quests) |
| 6 skill trees with level progression | Bronze → Diamond competitive leagues | 3 daily challenges + combo bonus |

</div>

> 📌 **Screenshots coming soon** — Deploy your own instance and submit a screenshot PR!

---

## ⚡ Quick Start

> ⏱️ Estimated time: **~5 minutes**

### Prerequisites

Before you begin, make sure you have:
- ✅ [OpenClaw](https://github.com/openclaw/openclaw) installed and running
- ✅ Python 3.8+
- ✅ Node.js 16+ (for the hook)
- ✅ A GitHub account (for Pages deployment & leaderboard)

### Step 1 — Install the Hook

```bash
# Copy hook to OpenClaw directory
cp -r hooks/clawrecord-hook ~/.openclaw/hooks/

# Enable the hook
openclaw hooks enable clawrecord-hook

# Restart gateway to activate
openclaw gateway restart
```

> ✅ **Verify:** Run `openclaw hooks list` — you should see `clawrecord-hook` with status `enabled`.

### Step 2 — Collect & Score

```bash
# Parse OpenClaw runtime data
python3 scripts/collect.py

# Calculate XP, levels, achievements
python3 scripts/score.py

# Generate dashboard pages
python3 scripts/generate_pages.py
```

> ✅ **Verify:** Check `docs/index.html` exists and open it in your browser.

### Step 3 — Deploy to GitHub Pages

```bash
# Push to GitHub — the Action runs the pipeline daily
git add . && git commit -m "init clawrecord" && git push
```

Then enable GitHub Pages in **Settings → Pages → Source: `docs/`**.

> ✅ **Verify:** Visit `https://<your-username>.github.io/clawrecord/`

### Step 4 — Join the Global Leaderboard

Submit a PR to [clawrecord-leaderboard](https://github.com/luka2chat/clawrecord-leaderboard) to register your repo.

> 🏆 Once merged, you'll appear on the global leaderboard!

---

## ✨ Features

### 🎯 Core Gameplay

| Feature | Description |
|:---|:---|
| 📊 **Auto Data Collection** | Hook + session parser extracts metrics from OpenClaw runtime |
| ⭐ **XP System** | Earn XP from messages, tool calls, multi-turn conversations, skill diversity |
| 📈 **Level & Evolution** | Progress from 🥚 Novice Tamer to 👑 AI Overlord across 8 ranks |
| 🔥 **Streak & HP** | Daily streak with freeze protection, health decay, and recovery mechanics |
| 📋 **Daily Quests** | 3 rotating daily challenges + combo bonus for extra XP |

### 🏅 Gamification & Progression

| Feature | Description |
|:---|:---|
| 🏆 **47 Achievements** | Milestones, streaks, skills, tools, efficiency, time-based, and special |
| 🌳 **6 Skill Trees** | 💻 Coding · ✍️ Content · 🔍 Research · 💬 Communication · ⚙️ Automation · 📊 Data |
| 🎖️ **5-Tier Badges** | Bronze → Silver → Gold → Diamond → Legend for every achievement |
| ⬆️ **Claw Power** | Composite score combining XP, streak, badges, and skill levels |

### 🌐 Social & Competition

| Feature | Description |
|:---|:---|
| 🏟️ **League System** | 🟤 Bronze → 🥈 Silver → 🥇 Gold → 💠 Sapphire → 💎 Diamond (10 tiers) |
| 🗺️ **Activity Heatmap** | 90-day visual activity map |
| 🌍 **Global Leaderboard** | Decentralized via GitHub, zero infrastructure cost |
| 🌏 **Multi-language** | English and Chinese (i18n) |

---

## 🏆 Achievement Preview

<div align="center">

| Category | Achievements | Example |
|:---|:---|:---|
| 📍 **Milestone** | 👣 Session Runner · 💬 Messenger · 💰 Token Consumer | *"Centurion" — Complete 100 sessions* |
| 🔥 **Streak** | 🔥 Streak Master | *"Legendary" — 90-day streak* |
| 🧠 **Skill** | 🧙 Code Wizard · 📝 Wordsmith · 🌈 Renaissance Claw | *"Architect" — Coding skill level 8* |
| 🔧 **Tool** | 🔧 Tool Wielder · 🗡️ Swiss Army Knife · 🖥️ Shell Commander · 🖊️ Author · 🌐 Web Explorer | *"Full Arsenal" — Use 15 different tools* |
| 🚀 **Efficiency** | 🚀 Productivity Beast · 🏃 Marathon Runner | *"Unstoppable" — 200 messages in one day* |
| ⏰ **Time** | 🦉 Night Owl · 🐦 Early Bird | *"Vampire" — 200 late-night messages* |
| 🎁 **Special** | 📱 Telegram Pioneer · 📡 Multi-Channel · 🔬 Model Explorer · ⬆️ Level Master · 🔄 Comeback Kid | *"Omni-Channel" — Use 5 different channels* |

</div>

---

## 📊 Level System

<div align="center">

| Level | Rank | Icon | XP Required |
|:---:|:---|:---:|---:|
| 1 | Novice Tamer | 🥚 | 0 |
| 3 | Apprentice Tamer | 🐣 | 500 |
| 5 | Assistant Tamer | 🐥 | 1,500 |
| 10 | Senior Tamer | 🦅 | 5,000 |
| 20 | Claw Master | 🦉 | 15,000 |
| 35 | AI Expert | 🤖 | 40,000 |
| 50 | AI Sage | 🧠 | 80,000 |
| 100 | AI Overlord | 👑 | 200,000 |

</div>

---

## 🏟️ League System

<div align="center">

🟤 Bronze → 🥈 Silver → 🥇 Gold → 💠 Sapphire → 🔴 Ruby → 🟢 Emerald → 🟣 Amethyst → ⚪ Pearl → 🖤 Obsidian → 💎 Diamond

</div>

Leagues are determined by your **weekly XP**. Compete with other ClawRecord users to climb the ranks!

| League | Weekly XP Required |
|:---|---:|
| 🟤 Bronze | 0 |
| 🥈 Silver | 500 |
| 🥇 Gold | 1,500 |
| 💠 Sapphire | 3,000 |
| 💎 Diamond | 40,000 |

---

## 🏗️ Architecture

```
OpenClaw Runtime → Hook (real-time) → collect.py → score.py → generate_pages.py → GitHub Pages
                   Session JSONL ────↗                ↓
                                              public_profile.json → Global Registry → Leaderboard
```

## 📂 Project Structure

```
clawrecord/
├── hooks/clawrecord-hook/   # OpenClaw hook for real-time event capture
├── scripts/
│   ├── collect.py           # Data collection from OpenClaw runtime
│   ├── score.py             # XP / achievement / level calculation engine
│   ├── generate_pages.py    # Static dashboard generator
│   └── utils.py             # Shared utilities
├── data/
│   ├── config.json          # Game rules, levels, 47 achievements, leagues
│   ├── raw/                 # Auto-collected metrics (do not edit)
│   ├── user_stats.json      # Computed user state
│   ├── tasks.json           # Auto-detected daily tasks
│   ├── check_ins.json       # Daily check-in records
│   └── public_profile.json  # Public data for global leaderboard
├── registry/                # Global leaderboard aggregator (separate repo)
├── docs/                    # Generated static dashboard
└── .github/workflows/       # CI/CD pipeline
```

## 🛡️ Anti-Cheat

- All XP is computed from verified OpenClaw runtime logs
- `data/raw/` is machine-generated — manual edits are ignored by the pipeline
- `public_profile.json` includes a SHA-256 signature for integrity verification
- The global registry checks XP growth rate anomalies

## 🤝 Contributing

Contributions welcome! Feel free to:
- 🐛 Report bugs via [Issues](https://github.com/luka2chat/clawrecord/issues)
- 💡 Suggest features via [Discussions](https://github.com/luka2chat/clawrecord/discussions)
- 🔧 Submit PRs for improvements

## 📄 License

This project is open source. See [LICENSE](LICENSE) for details.

---

<div align="center">

**Powered by [OpenClaw](https://github.com/openclaw/openclaw) & GitHub Actions**

⭐ Star this repo if you find it useful!

</div>
