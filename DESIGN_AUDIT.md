# ClawRecord 设计审计报告

> 基于 [impeccable.style](https://impeccable.style) 设计规范的全面审计
> 日期: 2026-03-08

---

## 项目概述

**ClawRecord** — OpenClaw 的游戏化追踪系统，将 AI 助手的使用数据转化为类似 Duolingo 的体验：XP、等级、成就、全球排行榜。

**核心目标**: 让用户在使用 AI 助手的过程中获得成就感和持续动力。

**技术栈**: 纯静态 HTML/CSS（由 Python 生成），部署在 GitHub Pages。

---

## 当前设计问题诊断

### 1. "AI Slop" 典型特征 — 最严重的问题

当前设计几乎命中了 impeccable.style 定义的所有 AI 生成设计反模式：

| 反模式 | 当前状态 | 严重程度 |
|--------|---------|---------|
| 青色+暗背景（cyan-on-dark） | `--cyan: #06b6d4` 作为主要强调色 | 🔴 高 |
| 紫蓝渐变 | `linear-gradient(135deg, var(--g), var(--cyan))` 到处使用 | 🔴 高 |
| 暗模式+发光强调色 | 默认深色背景 + 绿色/青色辉光 | 🔴 高 |
| 渐变文字用于"冲击力" | `.power-num` 使用渐变填充 | 🔴 高 |
| 玻璃拟态效果 | noise overlay + glow borders + box-shadow glow | 🟡 中 |

**impeccable 原文**: *"DON'T: Use the AI color palette: cyan-on-dark, purple-to-blue gradients, neon accents on dark backgrounds"*

### 2. 排版问题

| 问题 | 说明 |
|------|------|
| 等宽字体滥用 | JetBrains Mono 用于几乎所有数据展示，作为"技术感"的懒惰捷径 |
| 字号层级不清 | 存在过多相近的字号（.6em, .65em, .7em, .72em, .75em, .78em...） |
| 缺乏模块化比例 | 字号之间没有明确的数学关系 |
| Space Grotesk 过于安全 | 虽然不是 Inter/Roboto，但已成为 AI 项目的常见选择 |

**impeccable 原文**: *"DON'T: Use monospace typography as lazy shorthand for 'technical/developer' vibes"*

### 3. 布局问题 — Card-itis（卡片过度症）

| 问题 | 说明 |
|------|------|
| 一切皆卡片 | 每个内容区域都被 `.card` 包裹 |
| 卡片嵌套卡片 | 技能卡片在技能区域卡片内，成就在成就区域卡片内 |
| 同质化网格 | 所有卡片使用相同的背景色、边框、圆角 |
| Hero 指标模板 | 大数字 + 小标签 + 支持统计 + 渐变强调 = 经典 AI dashboard |
| 全局居中 | 几乎所有内容居中对齐 |
| 间距单调 | 所有卡片使用相同的 `padding: 24px` 和 `margin-bottom: 20px` |

**impeccable 原文**: 
- *"DON'T: Wrap everything in cards—not everything needs a container"*
- *"DON'T: Nest cards inside cards—visual noise, flatten the hierarchy"*
- *"DON'T: Use the hero metric layout template—big number, small label, supporting stats, gradient accent"*

### 4. 色彩问题

| 问题 | 说明 |
|------|------|
| 接近纯黑背景 | `--bg: #050a18` 接近纯黑 |
| 使用 HSL/Hex | 没有使用 OKLCH 等现代色彩空间 |
| rgba 过度使用 | 大量 `rgba(34,197,94,.1)` 等透明度值 |
| 色彩比例失调 | 绿色强调色使用过多，失去强调效果 |
| 灰色文字在有色背景上 | `.sub: #94a3b8` 在深色卡片上显得苍白 |

### 5. 动效问题

| 问题 | 说明 |
|------|------|
| 无限旋转动画 | `.av-ring` 持续 8s 旋转动画，分散注意力 |
| 脉冲动画滥用 | `.q-pulse` 无限脉冲 |
| 缺少 reduced-motion 支持 | 没有 `prefers-reduced-motion` 媒体查询 |
| 使用 `ease` 默认缓动 | 应使用指数缓动曲线 |
| 只有入场动画 | fadeUp 用于所有卡片，但没有交互反馈 |

### 6. 可访问性问题

| 问题 | 说明 |
|------|------|
| 无焦点样式 | 没有 `:focus-visible` 样式 |
| 无跳过链接 | 没有 skip-to-content 链接 |
| Emoji 作为语义图标 | 依赖 emoji 传达含义，屏幕阅读器体验差 |
| 对比度不足 | `.muted: #475569` 在深色背景上可能不达标 |

---

## 重新设计方向建议

### 设计原则

1. **有意识的克制** — 每个视觉元素都要有目的，不要因为"看起来酷"就添加
2. **排版驱动层级** — 用字体大小、粗细、颜色建立层级，而非全靠卡片容器
3. **独特的品牌标识** — 摆脱 AI 生成设计的视觉套路
4. **数据优先** — 这是一个数据仪表板，让数据本身成为设计的焦点

### 风格方向探索

**方向 A: 编辑/杂志风格（Editorial）**
- 强排版层级，大标题，紧凑数据
- 浅色/暖色基调，有别于千篇一律的暗色 dashboard
- 衬线+无衬线字体配对
- 参考: Linear changelog, Stripe 文档

**方向 B: 极简工具风格（Utilitarian）**
- 工业感，无装饰，功能驱动
- 高密度数据展示，像终端但更精致
- 黑白+单一强调色
- 参考: Things 3, iA Writer

**方向 C: 游戏化但不俗套（Playful-yet-refined）**
- 保持游戏化元素但提升品质感
- 自定义插画/图标代替 emoji
- 温暖的色彩而非冷酷的青色/霓虹
- 参考: Duolingo 自身的设计（实际上很克制和有品味）

### 具体改进建议

#### 色彩

```
当前: 深暗背景 + 霓虹绿/青色 → 典型 AI slop
建议:
- 考虑浅色方案，或至少提供 light/dark 切换
- 使用 OKLCH 色彩空间
- 中性色带品牌色倾向（tinted neutrals）
- 单一强调色，遵循 60-30-10 规则
- 移除所有渐变文字
```

#### 排版

```
当前: Space Grotesk + JetBrains Mono 全覆盖
建议:
- 更独特的字体选择（如 Instrument Sans, Fraunces, Outfit）
- 限制等宽字体仅用于真正的代码/数据
- 建立 5 级模块化字号体系
- 使用 clamp() 实现流体排版
```

#### 布局

```
当前: 全卡片 + 全居中 + 统一间距
建议:
- 移除大部分卡片容器，用间距和排版建立分组
- 左对齐为主，非对称布局
- 建立变化的间距节奏
- 重新设计 Hero 区域，避免"大数字+小标签"模板
```

#### 动效

```
当前: 无限旋转 + 脉冲 + fadeUp
建议:
- 移除所有无限循环动画
- 使用 ease-out-quart 缓动
- 添加 prefers-reduced-motion 支持
- 仅在页面加载时使用编排好的入场动画
```

---

## 下一步行动

1. [ ] 确定设计方向（A/B/C 或其他）
2. [ ] 创建色彩/排版/间距的 design tokens
3. [ ] 重新设计 Hero 区域
4. [ ] 重构 CSS，从 card-based 转向 typography-driven layout
5. [ ] 添加可访问性基础设施
6. [ ] 实现 light/dark 主题切换

---

*此审计基于 [impeccable.style](https://impeccable.style) v1.2.0 设计规范。该规范强调避免 AI 生成设计的常见反模式，追求有意识的、独特的视觉方向。*
