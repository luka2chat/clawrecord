<div align="center">

# 🎮 ClawRecord

[![GitHub stars](https://img.shields.io/github/stars/luka2chat/clawrecord?style=social)](https://github.com/luka2chat/clawrecord/stargazers)
[![License](https://img.shields.io/github/license/luka2chat/clawrecord?color=blue)](LICENSE)
[![Last Updated](https://img.shields.io/github/last-commit/luka2chat/clawrecord?label=last%20updated&color=green)](https://github.com/luka2chat/clawrecord/commits/main)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-兼容-orange?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJMNCAyMGgyMEwxMiAyeiIgZmlsbD0id2hpdGUiLz48L3N2Zz4=)](https://github.com/openclaw/openclaw)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-16+-339933?logo=node.js&logoColor=white)](https://nodejs.org)

**游戏化 OpenClaw 追踪 — 经验值、等级、成就、全球排行榜**

[English](./README.md) | [简体中文](./README_CN.md) | [在线演示 →](https://luka2chat.github.io/clawrecord/)

</div>

---

> 🕹️ 为你的 AI 助手打造的多邻国 — ClawRecord 自动追踪你的 [OpenClaw](https://github.com/openclaw/openclaw) 使用数据，将其转化为游戏化体验。

**你的 AI 在成长，勋章属于你。无法作弊。**

---

## 📸 截图预览

<!-- TODO: 替换占位图为实际截图/GIF -->

<div align="center">

| 仪表盘概览 | 成就墙 | 活动热力图 |
|:---:|:---:|:---:|
| ![仪表盘](https://via.placeholder.com/350x220/1a1a2e/e94560?text=Dashboard+Overview) | ![成就](https://via.placeholder.com/350x220/16213e/0f3460?text=Achievement+Wall) | ![热力图](https://via.placeholder.com/350x220/1a1a2e/53a653?text=Activity+Heatmap) |
| XP、等级、连续打卡、HP 一览 | 7 大类 47 项成就 | 90 天可视化活动记录 |

| 技能卡牌 | 联赛排名 | 每日任务 |
|:---:|:---:|:---:|
| ![技能](https://via.placeholder.com/350x220/0f3460/e94560?text=Skill+Cards) | ![联赛](https://via.placeholder.com/350x220/533483/e94560?text=League+Ranking) | ![任务](https://via.placeholder.com/350x220/1a1a2e/f0a500?text=Daily+Quests) |
| 6 大技能树及等级进度 | 青铜 → 钻石竞技联赛 | 3 个每日挑战 + 组合奖励 |

</div>

> 📌 **截图即将添加** — 部署你自己的实例，欢迎提交截图 PR！

---

## ⚡ 快速开始

> ⏱️ 预计耗时：**约 5 分钟**

### 前置条件

开始前请确认：
- ✅ 已安装并运行 [OpenClaw](https://github.com/openclaw/openclaw)
- ✅ Python 3.8+
- ✅ Node.js 16+（Hook 需要）
- ✅ GitHub 账户（用于 Pages 部署和排行榜）

### 第 1 步 — 安装 Hook

```bash
# 复制 Hook 到 OpenClaw 目录
cp -r hooks/clawrecord-hook ~/.openclaw/hooks/

# 启用 Hook
openclaw hooks enable clawrecord-hook

# 重启 Gateway 以激活
openclaw gateway restart
```

> ✅ **验证：** 运行 `openclaw hooks list`，应看到 `clawrecord-hook` 状态为 `enabled`。

### 第 2 步 — 采集与计分

```bash
# 解析 OpenClaw 运行时数据
python3 scripts/collect.py

# 计算 XP、等级、成就
python3 scripts/score.py

# 生成看板页面
python3 scripts/generate_pages.py
```

> ✅ **验证：** 检查 `docs/index.html` 是否存在，用浏览器打开查看。

### 第 3 步 — 部署到 GitHub Pages

```bash
# 推送到 GitHub — Action 每天自动运行流水线
git add . && git commit -m "init clawrecord" && git push
```

然后在 **Settings → Pages → Source: `docs/`** 中启用 GitHub Pages。

> ✅ **验证：** 访问 `https://<你的用户名>.github.io/clawrecord/`

### 第 4 步 — 加入全球排行榜

向 [clawrecord-leaderboard](https://github.com/luka2chat/clawrecord-leaderboard) 提交 PR 注册你的仓库。

> 🏆 合并后，你将出现在全球排行榜上！

---

## ✨ 功能特性

### 🎯 核心玩法

| 功能 | 描述 |
|:---|:---|
| 📊 **自动数据采集** | Hook + 会话解析器从 OpenClaw 运行时提取指标 |
| ⭐ **XP 系统** | 通过消息、工具调用、多轮对话、技能多样性获得 XP |
| 📈 **等级与进化** | 从 🥚 新手驯兽师进化到 👑 AI 领主，共 8 个段位 |
| 🔥 **打卡与生命值** | 每日 Streak + 冻结保护 + HP 衰减与恢复机制 |
| 📋 **每日任务** | 3 个轮换每日挑战 + 组合奖励获取额外 XP |

### 🏅 游戏化与成长

| 功能 | 描述 |
|:---|:---|
| 🏆 **47 项成就** | 里程碑、连续打卡、技能、工具、效率、时间、特殊成就 |
| 🌳 **6 大技能树** | 💻 编程 · ✍️ 内容创作 · 🔍 研究调查 · 💬 通信协作 · ⚙️ 自动化 · 📊 数据分析 |
| 🎖️ **5 级徽章** | 铜 → 银 → 金 → 钻 → 传奇，每项成就均可升级 |
| ⬆️ **龙虾战力** | 综合评分 = XP + 连胜 + 徽章 + 技能等级 |

### 🌐 社交与竞技

| 功能 | 描述 |
|:---|:---|
| 🏟️ **联赛系统** | 🟤 青铜 → 🥈 白银 → 🥇 黄金 → 💠 蓝宝石 → 💎 钻石（共 10 级） |
| 🗺️ **活动热力图** | 90 天可视化活动记录 |
| 🌍 **全球排行榜** | 基于 GitHub 的去中心化方案，零基础设施成本 |
| 🌏 **多语言** | 支持中英文（i18n） |

---

## 🏆 成就预览

<div align="center">

| 类别 | 成就列表 | 示例 |
|:---|:---|:---|
| 📍 **里程碑** | 👣 会话达人 · 💬 信使 · 💰 Token 消耗者 | *"百夫长" — 完成 100 次会话* |
| 🔥 **连续打卡** | 🔥 连胜大师 | *"传奇连胜" — 连续 90 天* |
| 🧠 **技能** | 🧙 代码巫师 · 📝 妙笔生花 · 🌈 全能之爪 | *"架构师" — 编程技能等级 8* |
| 🔧 **工具** | 🔧 工具使者 · 🗡️ 瑞士军刀 · 🖥️ 命令行指挥官 · 🖊️ 笔耕不辍 · 🌐 网络探险家 | *"全副武装" — 使用 15 种不同工具* |
| 🚀 **效率** | 🚀 效率怪兽 · 🏃 马拉松 | *"势不可挡" — 一天发送 200 条消息* |
| ⏰ **时间** | 🦉 夜猫子 · 🐦 早起鸟 | *"吸血鬼" — 深夜发送 200 条消息* |
| 🎁 **特殊** | 📱 Telegram 先锋 · 📡 多渠道 · 🔬 模型探险家 · ⬆️ 等级大师 · 🔄 王者归来 | *"全渠道" — 使用 5 种不同渠道* |

</div>

---

## 📊 等级系统

<div align="center">

| 等级 | 段位 | 图标 | 所需 XP |
|:---:|:---|:---:|---:|
| 1 | 新手驯兽师 | 🥚 | 0 |
| 3 | 学徒驯兽师 | 🐣 | 500 |
| 5 | 助理驯兽师 | 🐥 | 1,500 |
| 10 | 高级驯兽师 | 🦅 | 5,000 |
| 20 | Claw 大师 | 🦉 | 15,000 |
| 35 | AI 专家 | 🤖 | 40,000 |
| 50 | AI 贤者 | 🧠 | 80,000 |
| 100 | AI 领主 | 👑 | 200,000 |

</div>

---

## 🏟️ 联赛系统

<div align="center">

🟤 青铜 → 🥈 白银 → 🥇 黄金 → 💠 蓝宝石 → 🔴 红宝石 → 🟢 翡翠 → 🟣 紫水晶 → ⚪ 珍珠 → 🖤 黑曜石 → 💎 钻石

</div>

联赛由你的**周 XP** 决定。与其他 ClawRecord 用户竞争，攀登排名！

| 联赛 | 所需周 XP |
|:---|---:|
| 🟤 青铜 | 0 |
| 🥈 白银 | 500 |
| 🥇 黄金 | 1,500 |
| 💠 蓝宝石 | 3,000 |
| 💎 钻石 | 40,000 |

---

## 🏗️ 架构

```
OpenClaw 运行时 → Hook（实时）→ collect.py → score.py → generate_pages.py → GitHub Pages
                  会话 JSONL ──↗                ↓
                                       public_profile.json → 全球 Registry → 排行榜
```

## 📂 项目结构

```
clawrecord/
├── hooks/clawrecord-hook/   # OpenClaw Hook，实时事件捕获
├── scripts/
│   ├── collect.py           # 从 OpenClaw 运行时采集数据
│   ├── score.py             # XP / 成就 / 等级计算引擎
│   ├── generate_pages.py    # 静态看板生成器
│   └── utils.py             # 公共工具函数
├── data/
│   ├── config.json          # 游戏规则、等级、47 项成就、联赛
│   ├── raw/                 # 自动采集的指标（请勿手动编辑）
│   ├── user_stats.json      # 计算后的用户状态
│   ├── tasks.json           # 自动检测的每日任务
│   ├── check_ins.json       # 每日签到记录
│   └── public_profile.json  # 用于全球排行榜的公开数据
├── registry/                # 全球排行榜聚合器（独立仓库）
├── docs/                    # 生成的静态看板
└── .github/workflows/       # CI/CD 流水线
```

## 🛡️ 防作弊机制

- 所有 XP 均从经过验证的 OpenClaw 运行时日志计算
- `data/raw/` 由机器生成 — 手动编辑会被流水线忽略
- `public_profile.json` 包含 SHA-256 签名用于完整性验证
- 全球 Registry 检查 XP 增长速率异常

## 🤝 参与贡献

欢迎贡献！你可以：
- 🐛 通过 [Issues](https://github.com/luka2chat/clawrecord/issues) 报告 Bug
- 💡 通过 [Discussions](https://github.com/luka2chat/clawrecord/discussions) 建议新功能
- 🔧 提交 PR 改进项目

## 📄 许可证

本项目开源，详见 [LICENSE](LICENSE)。

---

<div align="center">

**Powered by [OpenClaw](https://github.com/openclaw/openclaw) & GitHub Actions**

⭐ 觉得有用的话，给个 Star 吧！

</div>
