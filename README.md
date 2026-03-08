<div align="center">

# 🐾 ClawRecord

**Duolingo for your AI assistant — gamified OpenClaw tracking**

[![GitHub stars](https://img.shields.io/github/stars/luka2chat/clawrecord?style=social)](https://github.com/luka2chat/clawrecord/stargazers)
[![License](https://img.shields.io/github/license/luka2chat/clawrecord?color=blue)](LICENSE)
[![Last Updated](https://img.shields.io/github/last-commit/luka2chat/clawrecord?label=last%20updated&color=green)](https://github.com/luka2chat/clawrecord/commits/main)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-compatible-orange?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJMNCAyMGgyMEwxMiAyeiIgZmlsbD0id2hpdGUiLz48L3N2Zz4=)](https://github.com/openclaw/openclaw)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-16+-339933?logo=node.js&logoColor=white)](https://nodejs.org)

[English](./README.md) | [简体中文](./README_CN.md) | [Live Demo →](https://luka2chat.github.io/clawrecord/)

</div>

---

> **Your AI grows. You get the credit. ClawRecord automatically tracks your [OpenClaw](https://github.com/openclaw/openclaw) usage and turns it into XP, achievements, leagues, and a personal dashboard — all shareable to X.**

---

## 🚀 30-Second Quick Start

```bash
# 1. Clone into your OpenClaw directory
git clone https://github.com/luka2chat/clawrecord.git
cd clawrecord

# 2. Install the hook
cp -r hooks/clawrecord-hook ~/.openclaw/hooks/
openclaw hooks enable clawrecord-hook && openclaw gateway restart

# 3. Generate your dashboard
python3 scripts/collect.py && python3 scripts/score.py && python3 scripts/generate_pages.py

# 4. Open it!
open docs/index.html  # macOS, or xdg-open on Linux
```

That's it. Your personal ClawRecord dashboard is ready.

---

## 🎮 For Every Type of Player

ClawRecord adapts to your experience level with a guided learning path:

### 🌱 Beginners — Learn OpenClaw

| Step | What you'll learn | Reward |
|:---:|:---|:---|
| 1 | Send your first message | 🥚 First Steps badge |
| 2 | Use a tool call | 🔧 Tool Wielder badge |
| 3 | Complete a session | 👣 Session Runner badge |
| 4 | Unlock your first achievement | ⭐ First star |
| 5 | Reach Level 3 | 🐣 Apprentice Tamer rank |

### 🚀 Intermediate — Track & Grow

| Goal | How to get there | Reward |
|:---:|:---|:---|
| Build a 7-day streak | Use OpenClaw every day | 🔥 On Fire badge |
| Reach Gold league | Earn 1,500+ weekly XP | 🥇 Gold league status |
| Master a skill to Lv.5 | Focus on one skill area | 🧙 Skill specialist badge |
| Unlock 10 achievements | Explore different features | 🏅 Achievement wall |
| Deploy your dashboard | Push to GitHub Pages | 📊 Live personal dashboard |

### 👑 Advanced — Compete Globally

| Goal | How to get there | Reward |
|:---:|:---|:---|
| Join the global leaderboard | PR to clawrecord-leaderboard | 🌍 Global ranking |
| Reach Diamond league | 40,000+ weekly XP | 💎 Diamond status |
| Earn a Legend badge | Max out any achievement | ⭐⭐⭐⭐⭐ Legend tier |
| 30-day streak | Consistent daily usage | 🔥 Unstoppable badge |
| Share profile on X | Click share button | 📢 Social recognition |

---

## ✨ Features

### 🎯 Core Gameplay

| Feature | Description |
|:---|:---|
| 📊 **Auto Data Collection** | Hook + session parser extracts metrics from OpenClaw runtime |
| ⭐ **XP System** | Earn XP from messages, tool calls, multi-turn conversations, skill diversity |
| 📈 **Level & Evolution** | Progress from 🥚 Novice Tamer to 👑 AI Overlord across 8 ranks |
| 🔥 **Streak & HP** | Daily streak with freeze protection, health decay, and recovery mechanics |
| 📋 **Daily Quests** | 3 rotating daily challenges (Combo + Challenge + Streak) with bonus XP |

### 🏅 Gamification & Social

| Feature | Description |
|:---|:---|
| 🏆 **47 Achievements** | 21 badge types with up to 5 tiers each (Bronze → Legend) |
| 🌳 **6 Skill Trees** | 💻 Coding · ✍️ Content · 🔍 Research · 💬 Communication · ⚙️ Automation · 📊 Data |
| 🏟️ **10-Tier Leagues** | 🟤 Bronze → 💎 Diamond with promotion tracking |
| 🌍 **Global Leaderboard** | Decentralized via GitHub — zero infrastructure cost |
| 🐦 **Share to X** | One-click sharing of profile, achievements, streaks, and records |
| 🗺️ **Learning Path** | Guided journey from beginner to advanced with progress tracking |

---

## 📊 Level System

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

---

## 🏟️ League System

<div align="center">

🟤 Bronze → 🥈 Silver → 🥇 Gold → 💠 Sapphire → 🔴 Ruby → 🟢 Emerald → 🟣 Amethyst → ⚪ Pearl → 🖤 Obsidian → 💎 Diamond

</div>

Leagues are determined by your **weekly XP**. The dashboard shows your progress toward the next league with a visual progress bar.

---

## 🐦 Share to X

ClawRecord includes one-click sharing to X (Twitter) throughout the dashboard:

- **Profile share** — Your level, Claw Power, and rank
- **League share** — Your current league and weekly XP
- **Achievement share** — Your badge collection progress
- **Record share** — Your personal best stats

All share links include `#ClawRecord #OpenClaw` hashtags and Open Graph meta tags for rich link previews.

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
│   ├── generate_pages.py    # Static dashboard generator (v3)
│   └── utils.py             # Shared utilities
├── data/
│   ├── config.json          # Game rules, levels, 47 achievements, leagues
│   ├── raw/                 # Auto-collected metrics (do not edit)
│   ├── user_stats.json      # Computed user state
│   ├── tasks.json           # Auto-detected daily tasks
│   ├── check_ins.json       # Daily check-in records
│   └── public_profile.json  # Public data for global leaderboard
├── docs/                    # Generated static dashboard
└── .github/workflows/       # CI/CD pipeline (daily cron)
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
