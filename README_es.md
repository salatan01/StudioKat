**English** | [Português (Brasil)](README_pt-BR.md) | **Español** | [简体中文](README_zh-CN.md)

# StudioKat

**Producción de video agente — orquestada por tu asistente de codificación IA.**

StudioKat convierte tu asistente de codificación IA (OpenCode, Claude Code, Cursor, Copilot, Windsurf, Codex) en un estudio completo de producción de video. Describes lo que quieres en lenguaje natural; el agente maneja la investigación, guion, generación de assets, edición y composición final — con controles de calidad y presupuesto en cada paso.

> **Nota:** Esta es una página de aterrizaje localizada. La documentación autoritativa está en el [README en inglés](README.md).

---

## Inicio Rápido

```bash
git clone https://github.com/salatan01/StudioKat.git
cd OpenMontage
make setup
```

Luego abre el proyecto en tu asistente de IA y dile lo que quieres:

```
"Haz un explicador animado de 60 segundos sobre cómo aprenden las redes neuronales"
```

### Requisitos
- **Python 3.10+**
- **FFmpeg**
- **Node.js** 22.x / 24.x / 26.x (parcheado)
- **NixOS / Nix** — `nix develop` (recomendado)
- **Asistente de codificación IA** — OpenCode, Claude Code, Cursor, Copilot, Windsurf, Codex

Ver [README.md](README.md#quick-start) para instrucciones completas, claves API opcionales y rutas sin claves.

---

## Qué Obtienes Sin Claves API

| Capacidad | Herramienta Gratuita | Qué Hace |
|-----------|---------------------|----------|
| Narración | Piper TTS | Texto-a-voz offline gratuito |
| Metraje abierto | Archive.org + NASA + Wikimedia | Metraje de archivo gratuito/abierto |
| Stock extra | Pexels + Unsplash + Pixabay | Metraje/imágenes stock gratuitas |
| Composición (React) | Remotion | Renderizado basado en React |
| Composición (HTML/GSAP) | HyperFrames | Tipografía cinética, promos, rigs SVG |
| Post-producción | FFmpeg | Codificación, subtítulos, mezcla de audio |
| Subtítulos | Integrado | Subtítulos automáticos palabra por palabra |

---

## Pipelines (14)

| Pipeline | Qué Produce |
|----------|-------------|
| **Animated Explainer** | Explicadores con investigación, narración, visuales, música |
| **Animation** | Gráficos en movimiento, tipografía cinética |
| **Avatar Spokesperson** | Videos con presentador avatar |
| **Character Animation** | Personajes de dibujos animados riggeados, timelines GSAP |
| **Cinematic** | Trailers, teasers, ediciones guiadas por el estado de ánimo |
| **Clip Factory** | Lotes de clips cortos rankeados desde una fuente larga |
| **Documentary Montage** | Montajes temáticos desde metraje real gratuito/abierto |
| **Faceless Short** | Shorts verticales con tipografía cinética, TTS, música, stock — sin cara, sin cámara |
| **Hybrid** | Metraje fuente + visuales generados por IA de soporte |
| **Localization & Dub** | Subtítulos, doblaje y traducción de video existente |
| **Podcast Repurpose** | Highlights de podcast a video |
| **Screen Demo** | Grabaciones de pantalla pulidas y walkthroughs |
| **Talking Head** | Videos guiados por metraje de orador |
| **Framework Smoke** | Test de humo mínimo para desarrolladores de pipelines |

---

## Faceless Shorts

Pipeline `faceless-short` para shorts verticales (9:16, ≤60s) con tipografía cinética, narración TTS, música de fondo y metraje stock — **sin cara, sin cámara, sin claves API requeridas**.

**6 estilos integrados:** `deep-dive`, `inside-out`, `night-file`, `paper-atlas`, `stick-story`, `tall-tale`

Pídeselo directamente a tu agente — el pipeline `faceless-short` maneja el motor vendorizado mediante la herramienta `faceless_render`:

```text
"Haz un faceless short de 45 segundos sobre la historia del café. Estilo: paper-atlas."
```

El primer uso descarga los modelos locales una vez (voz Kokoro + Whisper, ~850 MB) en `~/.faceless-shorts/`. Después, cada render es offline y gratis. La salida queda en `projects/<project-id>/renders/final.mp4`.

---

## Backlot — Storyboard Vivo Local

Backlot muestra lo que la producción *está haciendo realmente* — un tablero local que se auto-rellena mientras corre el pipeline. Etapas se iluminan, el guion aterriza como página de guion, tarjetas de escena brillan mientras se generan assets, cada decisión de proveedor y dólar gastado en la pared.

```bash
python -m backlot open                  # biblioteca — todos los proyectos en disco
python -m backlot open <project-id>     # tablero en vivo de una producción
python scripts/backlot_simulate_run.py  # sin producción aún? mira una simulada en vivo
```

Ver [backlot/README.md](backlot/README.md).

---

## Gobernanza de Producción

- **Puertas de aprobación humana** — propuesta, guion, plan de escena, assets generados y publicación requieren tu firma
- **Validación pre-composición** — bloquea render si se viola la promesa de entrega o riesgo de "slideshow"
- **Auto-revisión post-render** — ffprobe, extracción de frames, análisis de audio, verificación de promesa, chequeo de subtítulos
- **Selección de proveedores puntuada** — 7 dimensiones: ajuste a la tarea (30%), calidad (20%), control (15%), fiabilidad (15%), eficiencia de costo (10%), latencia (5%), continuidad (5%)
- **Rastro de auditoría de decisiones** — cada elección importante registrada con alternativas, confianza y razonamiento
- **Controles de presupuesto** — estimación antes de ejecutar, límites de gasto, umbrales de aprobación por acción (default $0.50)

---

## Compatibilidad de Agentes

| Plataforma | Archivo de Config |
|-----------|----------------|
| **OpenCode** | `AGENTS.md` + `.agents/skills/` + `opencode.jsonc` |
| **Claude Code** | `CLAUDE.md` |
| **Cursor** | `CURSOR.md` + `.cursor/rules/` |
| **GitHub Copilot** | `COPILOT.md` + `.github/copilot-instructions.md` |
| **Codex** | `CODEX.md` |
| **Windsurf** | `.windsurfrules` |

Todos apuntan a `AGENT_GUIDE.md` (guía operativa y contrato de agente) y `PROJECT_CONTEXT.md` (referencia de arquitectura).

---

## Atribución

StudioKat es un fork de **OpenMontage** (AGPLv3, `github.com/calesthio/OpenMontage`). El nombre del directorio `OpenMontage/` e identificadores internos (`OpenMontageConfig`, `OPENMONTAGE_*` vars de entorno, caché `~/.openmontage`, `provider="openmontage"`) se preservan para que instalaciones, cachés y artifacts existentes sigan funcionando. Ver [`NOTICE`](NOTICE) para la atribución completa y aviso de licencia.

---

## Licencia

[GNU AGPLv3](LICENSE)

---

**StudioKat** — Video con calidad de producción y enforcement real, orquestado por tu asistente IA.