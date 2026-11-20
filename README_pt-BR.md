**English** | **Português (Brasil)** | [Español](README_es.md) | [简体中文](README_zh-CN.md)

# StudioKat

**Produção de vídeo agente — orquestrada pelo seu assistente de codificação IA.**

StudioKat transforma seu assistente de codificação IA (OpenCode, Claude Code, Cursor, Copilot, Windsurf, Codex) em um estúdio completo de produção de vídeo. Você descreve o que quer em linguagem natural; o agente cuida de pesquisa, roteiro, geração de assets, edição e composição final — com portões de qualidade e controles de orçamento em cada etapa.

> **Nota:** Esta é uma página de aterrissagem localizada. A documentação autoritativa está no [README em inglês](README.md).

---

## Início Rápido

```bash
git clone https://github.com/salatan01/StudioKat.git
cd OpenMontage
make setup
```

Abra o projeto no seu assistente de IA e diga o que quer:

```
"Faça um explicador animado de 60 segundos sobre como redes neurais aprendem"
```

### Pré-requisitos
- **Python 3.10+**
- **FFmpeg**
- **Node.js** 22.x / 24.x / 26.x (patched)
- **NixOS / Nix** — `nix develop` (recomendado)
- **Assistente de codificação IA** — OpenCode, Claude Code, Cursor, Copilot, Windsurf, Codex

Veja [README.md](README.md#quick-start) para instruções completas, chaves API opcionais e caminhos sem chaves.

---

## O Que Você Obtém Sem Chaves API

| Capacidade | Ferramenta Gratuita | O Que Faz |
|-----------|---------------------|-----------|
| Narração | Piper TTS | Texto-para-voz offline gratuito |
| Metragem aberta | Archive.org + NASA + Wikimedia | Metragem de arquivo gratuita/aberta |
| Stock extra | Pexels + Unsplash + Pixabay | Metragem/imagens stock gratuitas |
| Composição (React) | Remotion | Renderização baseada em React |
| Composição (HTML/GSAP) | HyperFrames | Tipografia cinética, promos, rigs SVG |
| Pós-produção | FFmpeg | Codificação, queima de legendas, mixagem de áudio |
| Legendas | Integrado | Legendas automáticas palavra por palavra |

---

## Pipelines (14)

| Pipeline | O Que Produz |
|----------|--------------|
| **Animated Explainer** | Explicadores com pesquisa, narração, visuais, música |
| **Animation** | Motion graphics, tipografia cinética |
| **Avatar Spokesperson** | Vídeos com apresentador avatar |
| **Character Animation** | Personagens de desenho animado riggeados, timelines GSAP |
| **Cinematic** | Trailers, teasers, edições guiadas pelo clima |
| **Clip Factory** | Lotes de clipes curtos rankeados de uma fonte longa |
| **Documentary Montage** | Montagens temáticas de metragem real gratuita/aberta |
| **Faceless Short** | Shorts verticais com tipografia cinética, TTS, música, stock — sem rosto, sem câmera |
| **Hybrid** | Metragem fonte + visuais gerados por IA de suporte |
| **Localization & Dub** | Legendas, dublagem e tradução de vídeo existente |
| **Podcast Repurpose** | Destaques de podcast para vídeo |
| **Screen Demo** | Gravações de tela polidas e walkthroughs |
| **Talking Head** | Vídeos guiados por metragem de orador |
| **Framework Smoke** | Teste de fumaça mínimo para desenvolvedores de pipeline |

---

## Faceless Shorts

Pipeline `faceless-short` para shorts verticais (9:16, ≤60s) com tipografia cinética, narração TTS, música de fundo e metragem stock — **sem rosto, sem câmera, sem chaves API necessárias**.

**6 estilos integrados:** `deep-dive`, `inside-out`, `night-file`, `paper-atlas`, `stick-story`, `tall-tale`

Peça diretamente ao seu agente — o pipeline `faceless-short` conduz o motor vendorizado pela ferramenta `faceless_render`:

```text
"Faça um faceless short de 45 segundos sobre a história do café. Estilo: paper-atlas."
```

O primeiro uso baixa os modelos locais uma vez (voz Kokoro + Whisper, ~850 MB) em `~/.faceless-shorts/`. Depois disso, cada render é offline e gratuito. A saída fica em `projects/<project-id>/renders/final.mp4`.

---

## Backlot — Storyboard Vivo Local

Backlot mostra o que a produção *está realmente fazendo* — um painel local que se auto-preenche enquanto o pipeline roda. Estágios acendem, o roteiro chega como página de screenplay, cards de cena brilham enquanto assets geram, cada decisão de provedor e dólar gasto na parede.

```bash
python -m backlot open                  # biblioteca — todos os projetos no disco
python -m backlot open <project-id>     # painel ao vivo de uma produção
python scripts/backlot_simulate_run.py  # sem produção ainda? assista uma simulada ao vivo
```

Ver [backlot/README.md](backlot/README.md).

---

## Governança de Produção

- **Portões de aprovação humana** — proposta, roteiro, plano de cena, assets gerados e publicação requerem sua assinatura
- **Validação pré-composição** — bloqueia render se a promessa de entrega é violada ou risco de "slideshow"
- **Auto-revisão pós-render** — ffprobe, extração de frames, análise de áudio, verificação de promessa, checagem de legendas
- **Seleção de provedores pontuada** — 7 dimensões: adequação à tarefa (30%), qualidade (20%), controle (15%), confiabilidade (15%), eficiência de custo (10%), latência (5%), continuidade (5%)
- **Rastro de auditoria de decisões** — cada escolha importante registrada com alternativas, confiança e raciocínio
- **Controles de orçamento** — estimativa antes de executar, limites de gasto, limiares de aprovação por ação (default $0.50)

---

## Compatibilidade de Agentes

| Plataforma | Arquivo de Config |
|-----------|----------------|
| **OpenCode** | `AGENTS.md` + `.agents/skills/` + `opencode.jsonc` |
| **Claude Code** | `CLAUDE.md` |
| **Cursor** | `CURSOR.md` + `.cursor/rules/` |
| **GitHub Copilot** | `COPILOT.md` + `.github/copilot-instructions.md` |
| **Codex** | `CODEX.md` |
| **Windsurf** | `.windsurfrules` |

Todos apontam para `AGENT_GUIDE.md` (guia operacional e contrato do agente) e `PROJECT_CONTEXT.md` (referência de arquitetura).

---

## Atribuição

StudioKat é um fork do **OpenMontage** (AGPLv3, `github.com/calesthio/OpenMontage`). O nome do diretório `OpenMontage/` e identificadores internos (`OpenMontageConfig`, `OPENMONTAGE_*` vars de ambiente, cache `~/.openmontage`, `provider="openmontage"`) são preservados para que instalações, caches e artifacts existentes continuem funcionando. Ver [`NOTICE`](NOTICE) para a atribuição completa e aviso de licença.

---

## Licença

[GNU AGPLv3](LICENSE)

---

**StudioKat** — Vídeo com qualidade de produção e enforcement real, orquestrado pelo seu assistente IA.