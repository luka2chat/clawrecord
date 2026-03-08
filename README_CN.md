<div align="center">

# 🐾 ClawRecord

**AI 助手的多邻国 — 游戏化 OpenClaw 追踪系统**

[![GitHub stars](https://img.shields.io/github/stars/luka2chat/clawrecord?style=social)](https://github.com/luka2chat/clawrecord/stargazers)
[![License](https://img.shields.io/github/license/luka2chat/clawrecord?color=blue)](LICENSE)
[![Last Updated](https://img.shields.io/github/last-commit/luka2chat/clawrecord?label=last%20updated&color=green)](https://github.com/luka2chat/clawrecord/commits/main)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-兼容-orange)](https://github.com/openclaw/openclaw)

[English](./README.md) | [简体中文](./README_CN.md) | [在线演示 →](https://luka2chat.github.io/clawrecord/)

</div>

---

> **你的 AI 在成长，你获得荣誉。ClawRecord 自动追踪你的 [OpenClaw](https://github.com/openclaw/openclaw) 使用数据，将其转化为经验值、成就、联赛和个人面板 — 全部可分享到 X。**

---

## 🚀 30 秒快速安装

```bash
# 1. 克隆到 OpenClaw 目录
git clone https://github.com/luka2chat/clawrecord.git
cd clawrecord

# 2. 安装 Hook
cp -r hooks/clawrecord-hook ~/.openclaw/hooks/
openclaw hooks enable clawrecord-hook && openclaw gateway restart

# 3. 生成仪表盘
python3 scripts/collect.py && python3 scripts/score.py && python3 scripts/generate_pages.py

# 4. 打开查看！
open docs/index.html  # macOS，Linux 用 xdg-open
```

就这么简单，你的 ClawRecord 个人仪表盘已就绪。

---

## 🎮 为每种玩家量身打造

ClawRecord 提供引导式学习路径，适配你的经验水平：

### 🌱 新手入门 — 学会使用 OpenClaw

| 步骤 | 学习内容 | 奖励 |
|:---:|:---|:---|
| 1 | 发送第一条消息 | 🥚 第一步徽章 |
| 2 | 使用一次工具调用 | 🔧 工具使者徽章 |
| 3 | 完成一次会话 | 👣 会话达人徽章 |
| 4 | 解锁第一个成就 | ⭐ 第一颗星 |
| 5 | 达到等级 3 | 🐣 学徒驯兽师称号 |

### 🚀 进阶提升 — 记录与成长

| 目标 | 达成方式 | 奖励 |
|:---:|:---|:---|
| 连续打卡 7 天 | 每天使用 OpenClaw | 🔥 火力全开徽章 |
| 进入黄金联赛 | 每周 1,500+ XP | 🥇 黄金联赛身份 |
| 技能升至 Lv.5 | 专注某一技能领域 | 🧙 技能专精徽章 |
| 解锁 10 个成就 | 探索不同功能 | 🏅 成就陈列墙 |
| 部署仪表盘 | 推送到 GitHub Pages | 📊 在线个人仪表盘 |

### 👑 资深玩家 — 全球竞技

| 目标 | 达成方式 | 奖励 |
|:---:|:---|:---|
| 加入全球排行榜 | 向 clawrecord-leaderboard 提 PR | 🌍 全球排名 |
| 进入钻石联赛 | 每周 40,000+ XP | 💎 钻石身份 |
| 获得传奇徽章 | 任一成就达到最高等级 | ⭐⭐⭐⭐⭐ 传奇段位 |
| 连续打卡 30 天 | 持续每日使用 | 🔥 势不可挡徽章 |
| 分享到 X | 点击分享按钮 | 📢 社交影响力 |

---

## ✨ 功能特性

### 🎯 核心玩法

| 功能 | 说明 |
|:---|:---|
| 📊 **自动数据采集** | Hook + 会话解析器从 OpenClaw 运行时提取指标 |
| ⭐ **经验值系统** | 通过消息、工具调用、多轮对话、技能多样性获得 XP |
| 📈 **等级与进化** | 从 🥚 新手驯兽师 进化到 👑 AI 领主，共 8 个段位 |
| 🔥 **连胜与生命值** | 每日打卡连胜 + 冻结保护 + 生命值衰减与恢复 |
| 📋 **每日三件套** | 每日组合 + 每日挑战 + 每日打卡，额外 XP 奖励 |

### 🏅 游戏化与社交

| 功能 | 说明 |
|:---|:---|
| 🏆 **47 个成就** | 21 种徽章，每种最多 5 个等级（铜 → 传奇） |
| 🌳 **6 棵技能树** | 💻 编程 · ✍️ 内容 · 🔍 研究 · 💬 通信 · ⚙️ 自动化 · 📊 数据 |
| 🏟️ **10 级联赛** | 🟤 青铜 → 💎 钻石，含晋级进度条 |
| 🌍 **全球排行榜** | 基于 GitHub 去中心化，零基础设施成本 |
| 🐦 **分享到 X** | 一键分享档案、成就、连胜和纪录到 X (Twitter) |
| 🗺️ **学习路径** | 从新手到资深的引导式旅程，含进度追踪 |

---

## 📊 等级体系

| 等级 | 称号 | 图标 | 需要 XP |
|:---:|:---|:---:|---:|
| 1 | 新手驯兽师 | 🥚 | 0 |
| 3 | 学徒驯兽师 | 🐣 | 500 |
| 5 | 助理驯兽师 | 🐥 | 1,500 |
| 10 | 高级驯兽师 | 🦅 | 5,000 |
| 20 | Claw 大师 | 🦉 | 15,000 |
| 35 | AI 专家 | 🤖 | 40,000 |
| 50 | AI 贤者 | 🧠 | 80,000 |
| 100 | AI 领主 | 👑 | 200,000 |

---

## 🏟️ 联赛体系

<div align="center">

🟤 青铜 → 🥈 白银 → 🥇 黄金 → 💠 蓝宝石 → 🔴 红宝石 → 🟢 翡翠 → 🟣 紫水晶 → ⚪ 珍珠 → 🖤 黑曜石 → 💎 钻石

</div>

联赛由你的**每周 XP** 决定。仪表盘会显示你向下一联赛的进度条。

---

## 🐦 分享到 X

ClawRecord 在仪表盘各关键位置提供一键分享到 X (Twitter) 功能：

- **档案分享** — 你的等级、龙虾战力和称号
- **联赛分享** — 你当前的联赛和每周 XP
- **成就分享** — 你的徽章收集进度
- **纪录分享** — 你的个人最佳数据

所有分享链接包含 `#ClawRecord #OpenClaw` 标签和 Open Graph 元数据，支持富链接预览。

---

## 🏗️ 架构

```
OpenClaw 运行时 → Hook (实时) → collect.py → score.py → generate_pages.py → GitHub Pages
                  Session JSONL ──↗                ↓
                                          public_profile.json → 全球注册 → 排行榜
```

## 🛡️ 防作弊机制

- 所有 XP 均从经过验证的 OpenClaw 运行时日志计算
- `data/raw/` 由机器生成 — 手动编辑会被流水线忽略
- `public_profile.json` 包含 SHA-256 签名用于完整性验证
- 全球注册表检查 XP 增长率异常

## 🤝 参与贡献

欢迎贡献！你可以：
- 🐛 通过 [Issues](https://github.com/luka2chat/clawrecord/issues) 报告 Bug
- 💡 通过 [Discussions](https://github.com/luka2chat/clawrecord/discussions) 建议新功能
- 🔧 提交 PR 进行改进

## 📄 许可证

本项目开源。详见 [LICENSE](LICENSE)。

---

<div align="center">

**由 [OpenClaw](https://github.com/openclaw/openclaw) 和 GitHub Actions 驱动**

⭐ 觉得有用请 Star 本仓库！

</div>
