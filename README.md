<p align="center">
  <h1 align="center">StudioKat</h1>
</p>

<p align="center"><strong>Agentic video production — orchestrated by your AI coding assistant.</strong></p>

<p align="center">
  <a href="#quick-start">Quick Start</a> &nbsp;·&nbsp;
  <a href="#pipelines">Pipelines</a> &nbsp;·&nbsp;
  <a href="#style-system">Styles</a> &nbsp;·&nbsp;
  <a href="#try-these-prompts">Try These Prompts</a> &nbsp;·&nbsp;
  <a href="docs/PROVIDERS.md">Providers</a> &nbsp;·&nbsp;
  <a href="docs/ARCHITECTURE.md">Architecture</a> &nbsp;·&nbsp;
  <a href="AGENT_GUIDE.md">Agent Guide</a>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-AGPLv3-blue.svg" alt="License"></a>
</p>

---

> **What this is:** StudioKat turns your AI coding assistant (OpenCode, Claude Code, Cursor, Copilot, Windsurf, Codex) into a full video production studio. You describe what you want in plain language; the agent handles research, scripting, asset generation, editing, and final composition — with quality gates and budget controls at every step.

> **What this is not:** A SaaS, a hosted service, or a "one-prompt video" wrapper. StudioKat runs locally, uses your API keys, and gives you an auditable production pipeline with human approval at every creative decision.

---

## Quick Start

### Prerequisites

- **Python 3.10+** — [python.org](https://www.python.org/downloads/)
- **FFmpeg** — `brew install ffmpeg` / `sudo apt install ffmpeg` / [ffmpeg.org](https://ffmpeg.org/download.html)
- **Node.js** — patched release on 22.x (22.23.4+), 24.x (24.22.1+), or 26.x (26.12.1+); `.node-version` selects 22.23.4 — [nodejs.org](https://nodejs.org/)
- **NixOS / Nix** — `nix develop`. The first interactive entry installs dependencies and activates `.venv` automatically; the shell supplies Python 3.11, Node 22, FFmpeg, and a Chromium that HyperFrames and Remotion can launch; see [docs/NIXOS.md](docs/NIXOS.md)
- **An AI coding assistant** — OpenCode, Claude Code, Cursor, Copilot, Windsurf, or Codex

### Install & Run

#### 1. Clone

```bash
git clone https://github.com/salatan01/StudioKat.git
cd StudioKat
```

#### 2. Install

```bash
make setup
```

That one command does the whole install:

| Step | What it does |
|------|--------------|
| `ensure-venv` | Creates `.venv` with Python 3.10+ (uses `uv` if available) |
| `bootstrap` | Upgrades pip so the CA bundle is current |
| deps | Installs `requirements.txt` into `.venv` |
| composer | Runs `npm install` in `remotion-composer/` |
| voice | Downloads the free offline Piper voice (`~/.piper/models`) |
| runtime | Cache-warms the HyperFrames CLI via `npx` (~20 MB) |
| config | Copies `.env.example` → `.env` if you don't have one |

**On NixOS / any machine with Nix, run `nix develop` instead** — the first interactive entry calls `make setup` for you and supplies Python 3.11, Node 22, FFmpeg, and the Chromium both render runtimes need. See [docs/NIXOS.md](docs/NIXOS.md).

#### 3. Start the engine and verify it

Activate the environment, then run the smoke checks. Each one proves a different part of the engine is alive:

```bash
source .venv/bin/activate

make preflight        # registry discovers every tool; prints providers + availability
make demo-list        # lists the zero-key demos you can render offline
make demo             # renders them — proves the Remotion/FFmpeg path works end to end
```

`make preflight` is the important one: it loads all **166 registered tools** and reports which providers are configured. If it prints JSON with a `total` count, the engine is up.

To confirm the faceless engine (local voice + captions, no API keys):

```text
"Run faceless_render with operation='selftest'."
```

The first faceless run downloads ~850 MB of local models into `~/.faceless-shorts/`; after that it is fully offline.

To open the live production board:

```bash
python -m backlot open       # library — every project on disk
```

#### 4. Open your agent

Open the project in your AI coding assistant and tell it what you want:

```
"Make a 60-second animated explainer about how neural networks learn"
```

Or if you want the real-footage path:

```text
"Make a 75-second documentary montage about city life in the rain. Use real footage only, no narration, elegiac tone, with music."
```

That's it. The agent researches your topic with live web search, generates AI images, writes and narrates the script with voice direction, finds royalty-free background music automatically, burns in word-level subtitles, and renders the final video. Before you see anything, the system runs a multi-point self-review — ffprobe validation, frame sampling, audio level analysis, delivery promise verification, and subtitle checks. Every provider selection is scored across 7 dimensions with an auditable decision log. Every creative decision gets your approval.

> **No `make`?** macOS/Linux: `python3 -m venv .venv && source .venv/bin/activate && python -m pip install 'pip>=26.2.2' && python -m pip install -r requirements.txt && cd remotion-composer && npm install && cd .. && python -m pip install piper-tts && cp .env.example .env`
>
> Windows PowerShell: `py -3 -m venv .venv; .\.venv\Scripts\Activate.ps1; python -m pip install 'pip>=26.2.2'; python -m pip install -r requirements.txt; cd remotion-composer; npm install; cd ..; python -m pip install piper-tts; Copy-Item .env.example .env`
>
> **Windows:** If `npm install` fails with `ERR_INVALID_ARG_TYPE`, use `npx --yes npm install` instead.
>
> **Non-interactive Nix shells** skip the auto-install, so run `make setup` once there.

#### 5. Keep it current

After pulling changes, re-sync the environment:

```bash
source .venv/bin/activate
python -m pip install --upgrade 'pip>=26.2.2' 'certifi>=2026.10.19'
make install          # or make install-dev / make install-gpu
make hyperframes-warm # refresh the HyperFrames npx cache to the latest release
```

These versions update both the application CA bundle and pip's separate bundled CA store for the eMudhra intermediate CA compromise. Update the operating system's trust store too: pip may also use system certificates, and custom CA bundles need separate maintenance. `make install` and `make install-dev` enforce the Python package minimums on subsequent installs.

### Add API Keys (optional — more keys = more tools)

```bash
# .env — every key is optional, add what you have

# Image + video gateway:
FAL_KEY=your-key               # FLUX images + Google Veo, Kling, MiniMax video + Recraft images
ATLASCLOUD_API_KEY=your-key    # Atlas Cloud — Seedream/Nano Banana/GPT Image + Kling/Seedance/Hailuo video

# Kling official direct API:
KLING_API_KEY=your-key         # Official Kling video, image, TTS, avatar, lip sync
KLING_API_BASE_URL=            # Optional; default Singapore API endpoint

# Free stock media:
PEXELS_API_KEY=your-key        # Free stock footage and images
PIXABAY_API_KEY=your-key       # Free stock footage and images
UNSPLASH_ACCESS_KEY=your-key   # Free stock images

# Music:
SUNO_API_KEY=your-key          # Full songs, instrumentals, any genre

# Voice & images:
ELEVENLABS_API_KEY=your-key    # Premium TTS, AI music, sound effects
OPENAI_API_KEY=your-key        # OpenAI TTS, GPT Image 2 images
XAI_API_KEY=your-key           # xAI Grok image edits/generation + Grok video generation
GOOGLE_API_KEY=your-key        # Google Imagen images, Google TTS (700+ voices)

# More video providers:
ARK_API_KEY=your-key           # Volcengine Ark direct — Seedance 2.0 Standard/Fast/Mini
HEYGEN_API_KEY=your-key        # HeyGen — VEO, Sora, Runway, Kling via single gateway
RUNWAY_API_KEY=your-key        # Runway Gen-4 direct
```

<details>
<summary><strong>Have a GPU? Unlock free local video generation</strong></summary>

```bash
make install-gpu

# Then add to .env:
VIDEO_GEN_LOCAL_ENABLED=true
VIDEO_GEN_LOCAL_MODEL=wan2.2-ti2v-5b  # or wan2.1-1.3b, wan2.1-14b, hunyuan-1.5, ltx2-local, cogvideo-5b
```

</details>

---

## What You Get With Zero API Keys

You don't need paid API keys to make real videos. Out of the box, `make setup` gives you:

| Capability | Free Tool | What It Does |
|-----------|-----------|-------------|
| **Narration** | Piper TTS | Free offline text-to-speech — real human-sounding narration |
| **Open footage** | Archive.org + NASA + Wikimedia Commons | Free/open archival footage, educational media, and documentary texture |
| **Extra stock** | Pexels + Unsplash + Pixabay | Free stock footage/images (developer keys are free to get) |
| **Composition (React)** | Remotion | React-based rendering — spring-animated image scenes, text cards, stat cards, charts, TikTok-style word-level captions, TalkingHead |
| **Composition (HTML/GSAP)** | HyperFrames | HTML/CSS/GSAP rendering — kinetic typography, product promos, launch reels, registry blocks, website-to-video, rigged SVG character animation |
| **Post-production** | FFmpeg | Encoding, subtitle burn-in, audio mixing, color grading |
| **Subtitles** | Built-in | Auto-generated captions with word-level timing |

StudioKat picks between Remotion and HyperFrames at proposal time (locked as `render_runtime`). Remotion is the default for data-driven explainers and anything using the existing React scene stack; HyperFrames is the default for motion-graphics-heavy briefs that express naturally as HTML + GSAP, including the `character-animation` pipeline's SVG/GSAP rig output. See `skills/core/hyperframes.md` for the full decision matrix.

**Three free-ish paths:**

- **Image-based video:** Piper narrates your script, images provide the visuals, and Remotion animates them into a polished edit.
- **Local character animation:** SVG rigs, pose libraries, GSAP timelines, and HyperFrames render cartoon character acting to `projects/<project-name>/renders/final.mp4`.
- **Real-footage video:** the documentary montage pipeline builds a CLIP-searchable corpus from Archive.org, NASA, Wikimedia Commons, and optional free-key sources like Pexels and Unsplash, then cuts together actual motion footage into a finished video.
- **Faceless shorts:** vertical short-form videos with kinetic typography, TTS narration, BGM, and stock footage — no face, no camera, no API keys required.

If you want the real-footage path, prompt for a **documentary montage**, **tone poem**, or **stock-footage collage**, and explicitly say **use real footage only**.

---

## Try These Prompts

Copy any of these into your AI coding assistant after setup. Each one runs a full production pipeline.

### Start from a reference video

> "Here's a YouTube short I love. Make me something like this, but about CRISPR for high school students."

> "Analyze this Reel and give me 3 original variants I could make for my own product launch."

> "I like the pacing and hook in this video. Keep that energy, but turn it into a 45-second explainer about black holes."

### Zero keys needed

> "Make a 45-second animated explainer about why the sky is blue"

> "Create a 60-second video about the history of the internet, with narration and captions"

> "Make a data-driven explainer about coffee consumption around the world"

### Free real-footage documentary path

> "Make a 90-second documentary montage about what a city feels like at 4am. Use real footage only, no narration, elegiac tone."

> "Create a 60-second Adam-Curtis-style archival collage about 1950s consumer optimism. Prefer Archive.org and Wikimedia footage."

> "Cut together a dreamlike montage about coming home in the rain using real stock footage only. Music yes, narration no."

### Faceless shorts (vertical, under 60s)

> "Make a 45-second faceless short about the history of coffee. Style: paper-atlas. No API keys."

> "Create a 30-second faceless short: 5 weird facts about octopuses. Style: deep-dive. Use Piper TTS."

> "Make a faceless short explaining compound interest. Style: tall-tale. 60 seconds max."

### With an image/video provider configured (~$0.15–$1.50)

> "Create a 30-second Ghibli-style animated video of a magical floating library in the clouds at golden hour"

> "Make a 30-second anime-style animation of an underwater temple with bioluminescent coral and ancient ruins"

> "Create an animated explainer about how CRISPR gene editing works, using AI-generated visuals"

> "Make a product launch teaser for a fictional smart water bottle called AquaPulse"

### Full setup (~$1–$3)

> "Create a cinematic 30-second trailer for a sci-fi concept: humanity receives a warning from 1000 years in the future"

> "Make a 90-second animated explainer about quantum computing for middle school students, with a fun narrator voice and custom soundtrack"

Want more? See the full **[Prompt Gallery](PROMPT_GALLERY.md)** for tested prompts with expected costs and output examples, or run `make demo` to render zero-key demo videos instantly.

---

## Pipelines

Each pipeline is a complete production workflow, from idea to finished video.

| Pipeline | What It Produces | Best For |
|----------|-----------------|----------|
| **Animated Explainer** | AI-generated explainer with research, narration, visuals, music | Educational content, tutorials, topic breakdowns |
| **Animation** | Motion graphics, kinetic typography, animated sequences | Social media, product demos, abstract concepts |
| **Avatar Spokesperson** | Avatar-driven presenter videos | Corporate comms, training, announcements |
| **Character Animation** | Rigged local cartoon characters, pose libraries, action timelines, SVG/Canvas/Remotion/HyperFrames rendering | Animated series, character-driven storytelling, mascot videos |
| **Cinematic** | Trailer, teaser, and mood-driven edits | Brand films, teasers, promotional content |
| **Clip Factory** | Batch of ranked short-form clips from one long source | Repurposing long content for social media |
| **Documentary Montage** | Thematic montage cut from a CLIP-indexed corpus of free stock footage and open archives (Pexels, Archive.org, NASA, Wikimedia, Unsplash) | Video essays, mood pieces, retrieval-first B-roll edits, real-footage videos without paid generation APIs |
| **Faceless Short** | Vertical short-form with kinetic typography, TTS narration, BGM, stock footage — no face, no camera | TikTok/Reels/Shorts, educational shorts, fact videos, storytelling |
| **Editor** | Raw talking-head footage edited with style-locked motion graphics (7 canvas styles, English/Bangla, 16:9/9:16/3:4) | Editing raw footage with code-drawn styles, WebResearch-free talking-head edits |
| **Hybrid** | Source footage + AI-generated support visuals | Enhancing existing footage with graphics |
| **Localization & Dub** | Subtitle, dub, and translate existing video | Multi-language distribution |
| **Podcast Repurpose** | Podcast highlights to video | Podcast marketing, audiogram videos |
| **Screen Demo** | Polished software screen recordings and walkthroughs | Product demos, tutorials, documentation |
| **Talking Head** | Footage-led speaker videos | Presentations, vlogs, interviews |
| **Framework Smoke** | Minimal end-to-end smoke test for pipeline developers | CI verification, new pipeline development |

**15 pipelines total.** Every pipeline follows the same structured flow:

```
research -> proposal -> script -> scene_plan -> assets -> edit -> compose
```

Each stage has a dedicated **director skill** — a markdown instruction file that teaches the agent exactly how to execute that stage. The agent reads the skill, uses the tools, self-reviews, checkpoints state, and asks for human approval at creative decision points.

> **Web research is a first-class stage.** Before writing a single word of script, the agent searches YouTube, Reddit, Hacker News, news sites, and academic sources. It gathers data points, audience questions, trending angles, and visual references — then cites everything in a structured research brief. Your videos are grounded in real, current information, not hallucinated facts.

---

## Faceless Shorts

The `faceless-short` pipeline produces vertical short-form videos (9:16, ≤60s) with kinetic typography, TTS narration, background music, and stock footage — no face, no camera, no API keys required.

**6 built-in styles:** `deep-dive`, `inside-out`, `night-file`, `paper-atlas`, `stick-story`, `tall-tale`

Ask your agent for one directly — the `faceless-short` pipeline drives the vendored engine through the `faceless_render` tool:

```text
"Make a 45-second faceless short about the history of coffee. Style: paper-atlas."
```

First use downloads the local models once (Kokoro voice + Whisper, ~850 MB) into `~/.faceless-shorts/`. After that every render is offline and free. Output lands at `projects/<project-id>/renders/final.mp4`.

The faceless skill is vendored at `.agents/skills/faceless-shorts/` and runs through the `faceless_render` tool. See `.agents/skills/faceless-shorts/SKILL.md` for the full contract.

---

## Watch It Happen — The Backlot Living Storyboard

Chat tells you what the agent *said*. **Backlot shows you what the production is actually doing** — a local board that fills itself in as the pipeline runs. Stages light up, the script lands as a screenplay page, scene cards shimmer while assets generate, and every provider decision and dollar spent is on the wall.

When a production starts, the agent opens it for you automatically. No setup, no reporting — the board derives everything from the project files the pipeline already writes.

<p align="center"><img src="docs/images/backlot/board-live.png" alt="Backlot live board — assets generating" width="920"></p>

**The storyboard is now a real approval gate.** Asset generation pauses on a scene-by-scene contact sheet — takes, prompts, per-asset cost, quality scores — so you approve the visuals *before* the render, not after it's too late:

<p align="center"><img src="docs/images/backlot/storyboard.png" alt="Backlot storyboard — filmstrip with takes and renders" width="920"></p>

Creative gates hold until you answer. The board shows what's waiting and why; you reply in chat:

<p align="center"><img src="docs/images/backlot/script-gate.png" alt="Backlot script gate — awaiting approval" width="920"></p>

Every production on your machine, live-first, in the library:

<p align="center"><img src="docs/images/backlot/library.png" alt="Backlot library" width="920"></p>

```bash
python -m backlot open                  # the library — every project on disk
python -m backlot open <project-id>     # one production's live board
python scripts/backlot_simulate_run.py  # no production yet? watch a simulated one live
```

And when a run is done, hit **▶ REPLAY RUN** — the whole production replays from its timestamps, scrubbable end to end. See [`backlot/README.md`](backlot/README.md) for how it works.

---

## Why StudioKat?

Most AI video tools give you a single clip from a prompt. StudioKat gives you an **end-to-end production pipeline** — the same structured process a real production team follows, automated by your AI agent.

Most "free AI video" stacks quietly mean "animate still images." StudioKat can do that too, but it can also build a finished video from **real footage** pulled from free/open sources, ranked semantically, edited intentionally, and rendered as a proper timeline.

Edit your own talking-head footage. Generate a fully animated explainer from scratch. Cut a 2-hour podcast into a dozen social clips. Translate and dub your content into 10 languages. Build a cinematic brand teaser from stock footage and AI-generated scenes. Animate rigged cartoon characters with GSAP. **If a production team can make it, StudioKat can orchestrate it.**

- **14 production pipelines** — explainers, talking heads, screen demos, cinematic trailers, animations, podcasts, localization, documentary montages, character animation, faceless shorts, and more
- **166 registered tools** — spanning video generation, image creation, text-to-speech, music, audio mixing, subtitles, enhancement, and analysis
- **103 stage-director skills** — per-pipeline stage instructions with quality rubrics and self-evaluation criteria
- **95 agent skills** — deep technology knowledge packs (Layer 3) teaching the agent how to use every provider like an expert
- **5 YAML style playbooks + 6 faceless styles** — visual language, typography, motion, audio, and asset generation constraints
- **Reference-driven creation** — paste a video you like and the agent turns it into a grounded, differentiated production plan instead of forcing you to invent the perfect prompt from scratch
- **Real-footage documentary creation without paid video models** — build actual edited videos from free/open motion footage and archival sources, not just Ken Burns over images
- **Live web research built in** — before writing a single word of script, the agent runs 15–25+ web searches across YouTube, Reddit, news sites, and academic sources to ground your video in real, current data
- **Both free/local AND cloud providers** — every capability supports open-source local alternatives alongside premium APIs. Use what you have.
- **No vendor lock-in** — swap providers freely. The scored selector ranks every provider across 7 dimensions (task fit, output quality, control, reliability, cost efficiency, latency, continuity) and picks the best match automatically.
- **Production-grade quality gates** — delivery promise enforcement blocks slideshow-looking renders, pre-compose validation catches broken plans before wasting GPU time, and mandatory post-render self-review (ffprobe + frame extraction + audio analysis) ensures the agent never presents garbage. Every provider choice, style decision, and fallback gets logged in an auditable decision trail.
- **Budget governance built in** — cost estimation before execution, spend caps, per-action approval thresholds. No surprise bills.

---

## How It Works

StudioKat uses an **agent-first architecture**. There is no code orchestrator. Your AI coding assistant IS the orchestrator.

```
You: "Make an explainer video about how black holes form"
 |
 v
Agent reads pipeline manifest (YAML) -- stages, tools, review criteria, success gates
 |
 v
Agent reads stage director skill (Markdown) -- HOW to execute each stage
 |
 v
Agent calls Python tools -- scored provider selection ranks every tool across 7 dimensions
 |
 v
Agent self-reviews using reviewer skill -- schema validation, playbook compliance, quality checks
 |
 v
Agent checkpoints state (JSON) -- resumable, with decision log and cost snapshot
 |
 v
Agent presents for your approval -- you stay in control at every creative decision
 |
 v
Pre-compose validation gate -- delivery promise, slideshow risk, renderer governance
 |
 v
Render (Remotion or FFmpeg) -- composition engine matched to visual grammar
 |
 v
Post-render self-review -- ffprobe, frame extraction, audio analysis, promise verification
 |
 v
Final video output -- only if self-review passes
```

**Python provides tools and persistence.** All creative decisions, orchestration logic, review criteria, and quality standards live in readable instruction files (YAML manifests + Markdown skills) that you can inspect and customize. Every decision is logged with alternatives considered, confidence scores, and the reasoning behind each choice.

---

## Architecture

```
StudioKat/            # the local checkout — this directory is still named
│                     # OpenMontage/ on existing installs (see NOTICE)
├── tools/              # 165 registered production tools (the agent's hands)
│   ├── video/          # 20+ generation providers + compose, stitch, trim
│   ├── audio/          # 10+ speech providers + music, mixing, enhancement
│   ├── graphics/       # 15+ image providers + diagrams, code snippets, math
│   ├── enhancement/    # Upscale, bg remove, face enhance, color grade
│   ├── analysis/       # Transcription, scene detect, frame sampling
│   ├── avatar/         # Talking head, lip sync
│   └── subtitle/       # SRT/VTT generation
│
├── pipeline_defs/      # YAML pipeline manifests (the agent's playbook)
├── skills/             # Markdown skill files (the agent's knowledge)
│   ├── pipelines/      # Per-pipeline stage director skills (97)
│   ├── creative/       # Creative technique skills
│   ├── core/           # Core tool skills
│   └── meta/           # Reviewer, checkpoint protocol
│
├── schemas/            # 20+ JSON Schemas (contract validation)
├── styles/             # Visual style playbooks (YAML) + faceless styles
├── remotion-composer/  # React/Remotion video composition engine
├── lib/                # Core infrastructure (config, checkpoints, pipeline loader)
└── tests/              # Contract tests, QA integration tests, eval harness
```

### Three-Layer Knowledge Architecture

```
Layer 1: tools/ + pipeline_defs/     "What exists" — executable capabilities + orchestration
Layer 2: skills/                     "How to use it" — StudioKat conventions and quality bars
Layer 3: .agents/skills/             "How it works" — external technology knowledge packs
```

Each tool declares which Layer 3 skills it relies on. The agent reads Layer 1 to know what's available, Layer 2 to know how StudioKat wants it used, and Layer 3 for deep technical knowledge when needed.

---

## Supported Providers

> **Full setup guide with pricing and free tiers:** [`docs/PROVIDERS.md`](docs/PROVIDERS.md)

<details>
<summary><strong>Video Generation — 20+ providers</strong></summary>

| Provider | Type | Notes |
|----------|------|-------|
| **Kling (fal.ai)** | Cloud API | High quality, fast via fal.ai gateway |
| **Kling Official** | Cloud API | Official direct API with separate `kling_official` provider |
| **Atlas Cloud** | Cloud API | Unified gateway for Seedance, MiniMax, Hunyuan, and other multimodal models |
| **Seedance 2.0 (Volcengine Ark)** | Cloud API | Official direct API with separate `seedance_ark` provider |
| **Seedance 2.5 / 2.0** | Cloud API | Text, image, and reference-driven video workflows through supported gateways |
| **Gemini Omni Flash** | Cloud API | Conversational multimodal video generation and editing |
| **Runway Gen-4** | Cloud API | Cinematic quality, Gen-3 Alpha Turbo / Gen-4 Turbo / Gen-4 Aleph |
| **Google Veo 3.1** | Cloud API | Premium cinematic video via Google GenAI or fal.ai |
| **Grok Imagine Video** | Cloud API | Strong reference-image video and xAI-native short-form generation |
| **Higgsfield** | Cloud API | Multi-model orchestrator with Soul ID for character consistency |
| **MiniMax / H3** | Cloud API | Cost-effective generation, including text, image, and reference-driven H3 workflows |
| **HeyGen** | Cloud API | Multi-model gateway |
| **WAN 2.1 / 2.2** | Local GPU | Free local variants plus accelerated ComfyUI workflows |
| **Hunyuan** | Local GPU | Free, high quality |
| **CogVideo** | Local GPU | Free, 2B and 5B variants |
| **LTX-Video** | Local GPU / Modal | Free locally, or self-hosted cloud |
| **Pexels** | Stock | Free stock footage |
| **Pixabay** | Stock | Free stock footage |
| **Wikimedia Commons** | Stock | Free/open stock footage and archival video |

</details>

<details>
<summary><strong>Image Generation — 15+ providers</strong></summary>

| Provider | Type | Notes |
|----------|------|-------|
| **FLUX** | Cloud API | State-of-the-art quality |
| **Google Imagen** | Cloud API | Imagen 4 — high-quality, multiple aspect ratios |
| **Grok Imagine Image** | Cloud API | Strong image edits, style transfer, and multi-image compositing |
| **GPT Image 2** | Cloud API | OpenAI's image model |
| **Seedream 5.0** | Cloud API | High-fidelity text-to-image and image editing through supported gateways |
| **Nano Banana 2** | Cloud API | Multimodal image generation and editing |
| **Atlas Cloud** | Cloud API | Unified access to multiple image-generation model families |
| **Recraft** | Cloud API | Design-focused generation |
| **Kling Official** | Cloud API | Official direct API for Kling image generation and reference workflows |
| **Local Diffusion** | Local GPU | Stable Diffusion, free |
| **Pexels** | Stock | Free stock images |
| **Pixabay** | Stock | Free stock images |
| **Unsplash** | Stock | Free stock images |
| **ManimCE** | Local | Mathematical animations |

</details>

<details>
<summary><strong>Text-to-Speech — 10+ providers</strong></summary>

| Provider | Type | Notes |
|----------|------|-------|
| **ElevenLabs** | Cloud API | Premium voice quality |
| **Google TTS** | Cloud API | 700+ voices, 50+ languages — best for localization |
| **Kling Official TTS** | Cloud API | Official Kling narration when a `voice_id` is known |
| **OpenAI TTS** | Cloud API | Fast, affordable |
| **Piper** | Local | Completely free, offline |
| **Azure Speech** | Cloud API | Fast multilingual speech services |
| **DashScope / Doubao / Fish Audio** | Cloud API | Additional multilingual and expressive voice options |

</details>

<details>
<summary><strong>Music, Sound & Post-Production</strong></summary>

**Music & Sound:**

| Provider | Type | Notes |
|----------|------|-------|
| **Suno AI** | Cloud API | Full song generation with vocals, lyrics, any genre. Up to 8 minutes. |
| **ElevenLabs Music** | Cloud API | AI music generation |
| **ElevenLabs SFX** | Cloud API | Sound effect generation |

**Post-Production (always available, always free):**

| Tool | What It Does |
|------|-------------|
| **FFmpeg** | Video composition, encoding, subtitle burn-in, audio muxing |
| **Video Stitch** | Multi-clip assembly, crossfades, picture-in-picture, spatial layouts |
| **Video Trimmer** | Precision cutting and extraction |
| **Audio Mixer** | Multi-track mixing, ducking, fades |
| **Audio Enhance** | Noise reduction, normalization |
| **Color Grade** | LUT-based color grading |
| **Subtitle Gen** | SRT/VTT generation from timestamps |

**Enhancement:**

| Tool | What It Does |
|------|-------------|
| **Upscale** | Real-ESRGAN image/video upscaling |
| **Background Remove** | rembg / U2Net background removal |
| **Face Enhance** | Face quality enhancement |
| **Face Restore** | CodeFormer / GFPGAN face restoration |

**Analysis:**

| Tool | What It Does |
|------|-------------|
| **Transcriber** | WhisperX speech-to-text with word-level timestamps |
| **Scene Detect** | Automatic scene boundary detection |
| **Frame Sampler** | Intelligent frame extraction |
| **Video Understand** | CLIP/BLIP-2 vision-language analysis |

**Avatar & Lip Sync:**

| Tool | What It Does |
|------|-------------|
| **Talking Head** | SadTalker / MuseTalk avatar animation |
| **Lip Sync** | Wav2Lip audio-driven lip synchronization |
| **Kling Avatar** | Official Kling cloud avatar presenter generation |
| **Kling Lip Sync** | Official Kling cloud lip-sync with explicit face selection |

**Composition & Rendering:**

| Engine | Type | What It Does |
|--------|------|-------------|
| **Remotion** | Local (Node.js) | React-based programmatic video — spring-animated image scenes, stat reveals, section titles, hero cards, TikTok-style word-by-word captions, scene transitions (fade/slide/wipe/flip), Google Fonts, audio with fade curves, and the TalkingHead avatar composition. **When no video generation providers are configured, the agent generates still images and Remotion turns them into fully animated video.** |
| **HyperFrames** | Local (Node.js ≥ 22) | HTML/CSS/GSAP programmatic video — kinetic typography, product promos, launch reels, custom motion graphics, registry blocks (data charts, grain overlays, shader transitions), website-to-video workflows, and rigged SVG character animation. Consumed via `npx hyperframes`; no monorepo checkout needed. |
| **FFmpeg** | Local | Core video assembly, encoding, subtitle burn, audio muxing, color grading |

Runtime is chosen at proposal (`render_runtime`) and locked through `edit_decisions`. Silent swaps between runtimes are a governance violation — see `skills/core/hyperframes.md`.

</details>

---

## Style System

Styles are split into three independent catalogs: **playbooks** for the general pipelines, **faceless styles** for the `faceless-short` pipeline, and **editor canvas styles** for the `editor` pipeline. The agent picks one, locks it, and applies it consistently across every generated asset.

### Style Playbooks (6)

Loaded from `styles/*.yaml` (plus generated playbooks in `styles/custom/`) via `styles/playbook_loader.py`. `list_playbooks()` is the authoritative list.

| Playbook | Name | Category | Mood | Pace | Heading font | Palette | Best for |
|----------|------|----------|------|------|--------------|---------|----------|
| `clean-professional` | Clean Professional | motion-graphics | polished, trustworthy, clear | moderate | Inter | `#2563EB` `#1E40AF` on white | Corporate explainers, educational content, SaaS demos, conference talks |
| `premium-minimalist` | Premium Minimalist | minimalist | calm, editorial, precise | deliberate | Inter | `#111827` `#374151` on `#F9FAFB` | Investor updates, expert explainers, product narratives, high-trust launches |
| `flat-motion-graphics` | Flat Motion Graphics | motion-graphics | energetic, modern, bold | fast | Space Grotesk | `#7C3AED` `#4F46E5` on `#0F172A` | Social media explainers, TikTok/Reels, product launches, startup pitches |
| `minimalist-diagram` | Minimalist Diagram | whiteboard | focused, technical, precise | deliberate | IBM Plex Sans | `#1A1A2E` `#16213E` on `#FAFAFA` | Technical deep-dives, architecture, math/CS concepts, documentation |
| `anime-ghibli` | Anime Ghibli | custom | warm, whimsical, contemplative, magical | slow | Noto Serif JP | `#2D5016` `#1B4332` on `#0A0A1A` | Narrative animations, nature stories, emotional storytelling, fantasy |
| `sky-spectrum` | sky-spectrum | minimalist | curious, bright, clear-headed | moderate | Space Grotesk | `#3B8BEB` `#1E5FB8` on `#0B1D3A` | Science explainers about light, colour, and the atmosphere |

`sky-spectrum` is a generated playbook living in `styles/custom/` — the same directory `lib/playbook_generator.save_playbook()` writes to, so agent-authored playbooks appear here automatically.

### Faceless Styles (6)

Defined in `styles/faceless/*.json`, each backed by a `STYLE.md` manual, a `style-sheet.png` look reference, and a runnable `example/`. All render **9:16 at 1080×1920, 30 fps**.

| Style | Name | Engine | Length | Genre | What it makes |
|-------|------|--------|--------|-------|---------------|
| `deep-dive` | Deep Dive 3D | threejs | 30–45 s | body, health, science | The flagship, Zack D. Films-like: sculpted 3D people in sunlit sets, glowing x-ray bodies, camera journeys through blood vessels. "What happens if…?" |
| `night-file` | Night File 3D | threejs | 30–45 s | true crime, mystery, unsolved | Dark 3D places with one light, faceless people (the subject glows red), typewriter dates, case-file inserts |
| `inside-out` | Inside Out | canvas-2d | 25–45 s | body, health, science | Flat 2D "what happens if…?" explainer: a simple hero, x-ray cutaways, bold 1–3 word captions, punchy cuts |
| `stick-story` | Stick Story | canvas-2d | 30–45 s | survival, how-to, safety | "What would you do if…?" survival steps: stick people with acting eyes, flat rooms day/night, gold step cards |
| `paper-atlas` | Paper Atlas | canvas-2d | 30–45 s | history, maps, historical | History in cut paper: parchment maps, crimson routes, gold date ribbons, period figures |
| `tall-tale` | Tall Tale 3D | threejs | 40–60 s | funny, true story, storytime | Funny true stories: flat 2D cartoon people in a sunny 3D small-town world, camera always moving, one-word captions |

Resolve a style from a plain-language request:

```bash
.venv/bin/python -m styles.faceless.loader list
.venv/bin/python -m styles.faceless.loader resolve "a creepy unsolved mystery from 1971"
```

The resolver matches ids and aliases (`zack d films` → `deep-dive`, `true crime` → `night-file`, `cut paper` → `paper-atlas`) and reports ambiguity rather than guessing.

### Also: Ink Theater

`ink-sketch` is a **style id**, not a YAML playbook — a hand-drawn black-ink-on-white "moving art" engine in `ink-theater/`, rendered through HyperFrames in atelier mode. It runs on the `animation` pipeline. See `skills/creative/ink-theater.md`.

Playbooks control typography, color palettes, motion styles, audio profiles, and quality rules. The agent reads the chosen style and applies it consistently across all generated assets.

---

## Platform Output Profiles

Built-in render profiles for every major platform:

| Profile | Resolution | Aspect Ratio |
|---------|-----------|--------------|
| YouTube Landscape | 1920x1080 | 16:9 |
| YouTube 4K | 3840x2160 | 16:9 |
| YouTube Shorts | 1080x1920 | 9:16 |
| Instagram Reels | 1080x1920 | 9:16 |
| Instagram Feed | 1080x1080 | 1:1 |
| TikTok | 1080x1920 | 9:16 |
| LinkedIn | 1920x1080 | 16:9 |
| Cinematic | 2560x1080 | 21:9 |

---

## Production Governance

StudioKat treats video production like real engineering — with quality gates, audit trails, and enforcement at every stage.

### Quality Gates

- **Human approval gates are enforced, not suggested** — proposal, script, scene plan, generated assets, and publish all pause for your sign-off. The checkpoint writer rejects a "completed" gated stage without recorded approval, and every superseded checkpoint is archived so the audit trail (including gate transitions) survives revisions. Review happens visually on the [Backlot board](#watch-it-happen--the-backlot-living-storyboard).
- **Pre-compose validation** — blocks render if the delivery promise is violated (e.g. "motion-led" video with 80% still images), slideshow risk score is critical, or renderer family is missing. Catches broken plans before wasting GPU time.
- **Post-render self-review** — after every render, the runtime runs ffprobe validation, extracts frames at 4 positions to check for black frames and broken overlays, analyzes audio levels for silence and clipping, verifies the delivery promise was honored, and checks subtitle presence. If the review fails, the video is not presented.
- **Slideshow risk scoring** — 6-dimension analysis (repetition, decorative visuals, weak motion, shot intent, typography overreliance, unsupported cinematic claims) prevents "animated PowerPoint" outputs.
- **Source media inspection** — when users supply their own footage, the system probes every file (resolution, codec, audio channels, duration) and builds planning implications before a single creative decision is made. No hallucinating content from filenames.

### Scored Provider Selection

Every tool selection (video generation, image generation, TTS, music) runs through a 7-dimension scoring engine: task fit (30%), output quality (20%), control features (15%), reliability (15%), cost efficiency (10%), latency (5%), continuity (5%). The winning provider and its score are logged in the decision trail with all alternatives considered.

Selectors normalize loose brief context before scoring. If the agent only knows something like "Pixar-style animated short with character consistency," the selector expands that into scorer-friendly intent and style signals instead of requiring a perfectly pre-shaped `task_context`.

Selector outputs also surface the chosen provider's `agent_skills`, so the agent can immediately read the right Layer 3 provider skill before writing prompts.

### Decision Audit Trail

Every major creative and technical choice — provider selection, style/playbook choice, music track, voice selection, renderer family, any fallback or downgrade — is logged with alternatives considered, confidence scores, and reasoning. The cumulative decision log persists across all stages so you can trace exactly why the output looks the way it does.

### Budget Controls

- **Estimate** before execution — see what it will cost
- **Reserve** budget — lock funds before the call
- **Reconcile** after — record actual spend
- **Configurable modes** — `observe` (track only), `warn` (log overruns), `cap` (hard limit)
- **Per-action approval** — pause for confirmation above a threshold (default: $0.50)
- **Total budget cap** — default $10, fully configurable

No surprise bills. The agent tells you what it will cost before it spends.

---

## Agent Compatibility

StudioKat works with any AI coding assistant that can read files and execute Python. Dedicated instruction files are included for:

| Platform | Config File | Slash commands |
|----------|------------|----------------|
| **OpenCode** | `AGENTS.md` + `.agents/skills/` + `opencode.jsonc` | `.opencode/commands/` |
| **Claude Code** | `CLAUDE.md` + `.claude/skills/` | `.claude/commands/` |
| **Cursor** | `CURSOR.md` + `.cursor/rules/` | — |
| **GitHub Copilot** | `COPILOT.md` + `.github/copilot-instructions.md` | — |
| **Codex** | `CODEX.md` | `.codex/prompts/` (copy to `~/.codex/prompts/`) |
| **Windsurf** | `.windsurfrules` | — |

All platform files point to the shared `AGENT_GUIDE.md` (operating guide and agent contract) and `PROJECT_CONTEXT.md` (architecture reference).

**Skills** come from `.agents/skills/` — the single source of truth. OpenCode discovers it natively; Claude Code reads its own `.claude/skills/` mirror. Never add a third editable copy.

### OpenCode

OpenCode is not installed by `make setup` or the Nix flake; install the V2 CLI once per machine:

```bash
curl -fsSL https://opencode.ai/v2/install | bash
# or: npm install -g @opencode/cli
```

Run `opencode` from the repository root. It reads `AGENTS.md`, discovers the Layer 3 skills in `.agents/skills/`, loads the slash commands in `.opencode/commands/`, and loads the `superpowers` plugin declared in `opencode.jsonc`. Provider/model selection and API keys stay machine-local in `~/.config/opencode/opencode.jsonc` or environment variables; never commit them.

Available commands: `/reel` (produce or work on a video), `/backlot` (open the live storyboard), `/ink-art` (ink-doodle animation), `/animated-drawing` (mocap-animate a supplied drawing).

On NixOS, launch OpenCode from inside `nix develop` so the agent inherits the project `.venv`, Chromium override, and library path. See [docs/NIXOS.md](docs/NIXOS.md#running-the-opencode-agent).

---

## Contributing

StudioKat is built to be extended. The two most common contributions:

### Adding a New Tool

1. Create a Python file in the appropriate `tools/` subdirectory
2. Inherit from `BaseTool` and implement the tool contract
3. The registry auto-discovers it — no manual registration needed
4. Add a skill file if the tool needs usage guidance

### Adding a New Pipeline

1. Create a YAML manifest in `pipeline_defs/`
2. Create stage director skills in `skills/pipelines/<your-pipeline>/`
3. Reference existing tools — or add new ones if needed

See `docs/ARCHITECTURE.md` for the full technical reference, `docs/PROVIDERS.md` for the complete provider guide (setup, pricing, free tiers), and `AGENT_GUIDE.md` for the agent contract.

---

## Attribution

StudioKat is a fork of **OpenMontage** (AGPLv3, `github.com/calesthio/OpenMontage`). The `OpenMontage/` directory name and internal identifiers (`OpenMontageConfig`, `OPENMONTAGE_*` env vars, `~/.openmontage` cache, `provider="openmontage"`) are preserved so existing installations, caches, and artifacts keep working. See [`NOTICE`](NOTICE) for the full attribution and license notice.

---

## License

[GNU AGPLv3](LICENSE)

---

**StudioKat** — Production-grade video with real quality enforcement, orchestrated by your AI assistant.

If this project looks useful to you, a ⭐ would really mean a lot — it helps others discover it too.