**English** | [Português (Brasil)](README_pt-BR.md) | [Español](README_es.md) | **简体中文**

# StudioKat

**代理式视频制作 — 由您的 AI 编码助手编排。**

StudioKat 将您的 AI 编码助手（OpenCode、Claude Code、Cursor、Copilot、Windsurf、Codex）变成一个完整的视频制作工作室。您用自然语言描述想要的内容；代理处理研究、脚本、素材生成、编辑和最终合成 — 每一步都有质量关卡和预算控制。

> **注意：** 这是一个本地化着陆页。权威文档请参阅 [英文 README](README.md)。

---

## 快速开始

```bash
git clone https://github.com/salatan01/StudioKat.git
cd OpenMontage
make setup
```

在 AI 编码助手中打开项目，告诉它您想要什么：

```
"制作一个 60 秒的动画解释视频，讲解神经网络如何学习"
```

### 前置要求
- **Python 3.10+**
- **FFmpeg**
- **Node.js** 22.x / 24.x / 26.x (patched 版本)
- **NixOS / Nix** — `nix develop`（推荐）
- **AI 编码助手** — OpenCode、Claude Code、Cursor、Copilot、Windsurf、Codex

完整说明、可选 API 密钥和零密钥路径请见 [README.md](README.md#quick-start)。

---

## 零 API 密钥也能得到的能力

| 能力 | 免费工具 | 作用 |
|-----------|---------------------|----------|
| 旁白 | Piper TTS | 完全免费的离线文本转语音 |
| 开放素材 | Archive.org + NASA + Wikimedia | 免费/开放的档案素材、教育媒体 |
| 额外素材库 | Pexels + Unsplash + Pixabay | 免费素材视频/图片（开发者密钥免费申请） |
| 合成 | Remotion | 基于 React 的程序化视频 |
| 合成 | HyperFrames | 动态排版、产品宣传片、SVG 角色动画 |
| 后期制作 | FFmpeg | 编码、烧入字幕、音频混合、调色 |
| 字幕 | 内置 | 自动生成逐词计时字幕 |

---

## Pipelines（14 条）

| Pipeline | 产出内容 |
|----------|--------------|
| **Animated Explainer** | 带研究、旁白、视觉、音乐的解释视频 |
| **Animation** | 动态图形、动态排版、动画序列 |
| **Avatar Spokesperson** | 数字人主播视频 |
| **Character Animation** | 带骨骼的卡通角色、姿势库、GSAP 时间轴、SVG/Canvas/Remotion/HyperFrames 渲染 |
| **Cinematic** | 预告片、Teaser、情绪驱动剪辑 |
| **Clip Factory** | 从长视频批量产出排序后的短视频 |
| **Documentary Montage** | 从免费/开放素材库（Pexels、Archive.org、NASA、Wikimedia、Unsplash）语义检索剪辑的主题蒙太奇 |
| **Faceless Short** | 竖版短视频：动态排版 + TTS 旁白 + BGM + 素材库 — **无真人、无摄像、无需 API 密钥** |
| **Hybrid** | 实拍素材 + AI 生成辅助视觉 |
| **Localization & Dub** | 现有视频的字幕、配音、翻译 |
| **Podcast Repurpose** | 播客亮点转视频 |
| **Screen Demo** | 打磨过的软件屏幕录制与演示 |
| **Talking Head** | 实拍主导的讲话者视频 |
| **Framework Smoke** | 给 pipeline 开发者用的最小端到端冒烟测试 |

---

## Faceless Shorts（无真人短视频）

`faceless-short` pipeline 产出竖版短视频（9:16，≤60s），包含动态排版、TTS 旁白、背景音乐、素材库视频 — **无真人、无摄像、无需 API 密钥**。

**6 个内置风格：** `deep-dive`、`inside-out`、`night-file`、`paper-atlas`、`stick-story`、`tall-tale`

直接向您的代理提出需求 — `faceless-short` pipeline 通过 `faceless_render` 工具驱动内置引擎：

```text
"制作一个 45 秒的无真人短视频，主题是咖啡的历史。风格：paper-atlas。"
```

首次使用会一次性下载本地模型（Kokoro 语音 + Whisper，约 850 MB）到 `~/.faceless-shorts/`。之后每次渲染都离线且免费。输出位于 `projects/<project-id>/renders/final.mp4`。

---

## Backlot — 本地实时分镜板

聊天只告诉您代理*说了什么*。**Backlot 显示制作*实际在做什么*** — 一个本地看板，随管线运行自动填充。阶段点亮、脚本落地为剧本页、场景卡在素材生成时闪烁、每个提供商决策和每一美元支出都在墙上。

```bash
python -m backlot open                  # 素材库 — 磁盘上所有项目
python -m backlot open <project-id>     # 单个制作的实时看板
python scripts/backlot_simulate_run.py  # 还没制作？看模拟运行
```

详见 [backlot/README.md](backlot/README.md)。

---

## 制作治理

- **人工审批关卡强制执行** — 提案、脚本、场景计划、生成素材、发布均需您签名确认
- **合成前验证** — 违背交付承诺（如「动作为主」却 80% 静止画面）、幻灯片风险过高、渲染器缺失时阻断渲染
- **渲染后自检** — ffprobe 验证、4 位置抽帧检查黑帧/异常叠加、音频电平分析静音/削波、验证交付承诺、检查字幕存在性；自检失败不交付
- **幻灯片风险评分** — 6 维度（重复、装饰性视觉、弱动作、镜头意图、过度依赖排版、不支持的电影感声明）防止「动画版 PPT」
- **源素材审查** — 用户自带素材时，系统探测每个文件（分辨率、编码、音频声道、时长）并在任何创意决策前建立规划含义
- **评分制提供商选择** — 7 维度：任务适配度 (30%)、输出质量 (20%)、控制特性 (15%)、可靠性 (15%)、成本效率 (10%)、延迟 (5%)、连续性 (5%)；胜出者及分数连同备选方案记录在决策日志中
- **决策审计追踪** — 每个重要创意/技术选择（提供商、风格/手册、音乐、音色、渲染器、任何降级）均记录备选、置信度、推理；累积决策日志贯穿所有阶段
- **预算控制** — 执行前估算、锁定预算、事后对账；模式：`observe`/`warn`/`cap`；单动作审批阈值（默认 $0.50）；总预算上限（默认 $10，可配置）

**无惊喜账单。代理在花钱前告诉您成本。**

---

## 代理兼容性

| 平台 | 配置文件 |
|----------|------------|
| **OpenCode** | `AGENTS.md` + `.agents/skills/` + `opencode.jsonc` |
| **Claude Code** | `CLAUDE.md` |
| **Cursor** | `CURSOR.md` + `.cursor/rules/` |
| **GitHub Copilot** | `COPILOT.md` + `.github/copilot-instructions.md` |
| **Codex** | `CODEX.md` |
| **Windsurf** | `.windsurfrules` |

均指向共享的 `AGENT_GUIDE.md`（运营指南与代理契约）和 `PROJECT_CONTEXT.md`（架构参考）。

---

## 归属

StudioKat 是 **OpenMontage** 的一个分支（AGPLv3，`github.com/calesthio/OpenMontage`）。保留 `OpenMontage/` 目录名和内部标识符（`OpenMontageConfig`、`OPENMONTAGE_*` 环境变量、`~/.openmontage` 缓存、`provider="openmontage"`），以保持现有安装、缓存和制品持续工作。完整归属与许可证声明见 [`NOTICE`](NOTICE)。

---

## 许可证

[GNU AGPLv3](LICENSE)

---

**StudioKat** — 具有真实质量强制的生产级视频，由您的 AI 助手编排。

如果这个项目对您有用，给个 ⭐ 吧 — 帮助更多人发现它。