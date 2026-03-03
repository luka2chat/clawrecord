# ClawRecord

[English](./README.md) | [简体中文](./README_CN.md)

> OpenClaw 游戏化记录系统 — 为你的 AI 助手打造的多邻国。

ClawRecord 自动追踪你的 [OpenClaw](https://github.com/openclaw/openclaw) 使用数据，将其转化为游戏化体验：经验值、等级、成就、技能树、连续打卡、联赛和全球排行榜。

**你的 AI 在成长，勋章属于你。无法作弊。**

## 功能

- **自动数据采集** — Hook + 会话解析器从 OpenClaw 运行时提取指标
- **XP 系统** — 通过消息、工具调用、多轮对话、技能多样性获得 XP
- **等级与进化** — 从新手驯兽师（🥚）进化到 AI 领主（👑）
- **47 项成就** — 里程碑、连续打卡、技能、工具、效率、时间、特殊成就
- **6 大技能树** — 编程、内容创作、研究调查、通信协作、自动化、数据分析
- **打卡与生命值** — 每日 Streak + 冻结保护 + HP 衰减机制
- **联赛系统** — 青铜 → 白银 → 黄金 → 钻石 → 黑曜石（按周 XP 排名）
- **活动热力图** — 90 天可视化活动记录
- **全球排行榜** — 基于 GitHub 的去中心化方案，零基础设施成本
- **多语言** — 支持中英文

## 架构

```
OpenClaw 运行时 → Hook（实时）→ collect.py → score.py → generate_pages.py → GitHub Pages
                  会话 JSONL ──↗                ↓
                                       public_profile.json → 全球 Registry → 排行榜
```

## 快速开始

### 1. 安装 Hook

```bash
cp -r hooks/clawrecord-hook ~/.openclaw/hooks/
openclaw hooks enable clawrecord-hook
openclaw gateway restart
```

### 2. 采集与计分

```bash
python3 scripts/collect.py         # 解析 OpenClaw 数据 → data/raw/metrics.json
python3 scripts/score.py           # 计算 XP、等级、成就 → data/*.json
python3 scripts/generate_pages.py  # 生成看板 → docs/
```

### 3. 部署

推送到 GitHub，Action 每天自动运行流水线并部署到 Pages。

### 4. 加入全球排行榜

向 [clawrecord-leaderboard](https://github.com/luka2chat/clawrecord-leaderboard) 提交 PR 注册你的仓库。

## 防作弊机制

- 所有 XP 均从经过验证的 OpenClaw 运行时日志计算
- `data/raw/` 由机器生成 — 手动编辑会被流水线忽略
- `public_profile.json` 包含 SHA-256 签名用于完整性验证
- 全球 Registry 检查 XP 增长速率异常

---

Powered by OpenClaw & GitHub Actions
