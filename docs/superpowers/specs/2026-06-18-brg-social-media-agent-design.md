# BRG Social Media Agent — Design Spec
**Date:** 2026-06-18
**Status:** Approved
**Author:** Charles D. Butler (via Claude Code brainstorming)

---

## Overview

An autonomous social media agent for Battle Rhythm Group (BRG) that scrapes the web for trending leadership and coaching content, generates fully branded multi-format content, renders pixel-perfect visuals from code, and posts to all major platforms on an adaptive schedule — with no manual approval required.

**Business context:** BRG is a leadership development and business coaching brand. The agent exists to maintain a consistent, high-quality content presence across 6 platforms without requiring Charles' daily involvement.

---

## Goals

- Generate original, on-brand BRG content daily across LinkedIn, Instagram, Facebook, X, TikTok, and YouTube Shorts
- Scrape web sources (news, Reddit, YouTube, podcasts, competitor accounts, Google Trends) to surface the highest-value topics for the niche
- Produce all content types: thought leadership posts, carousels, video scripts, quote graphics, and story sequences
- Render all visuals from HTML/CSS code — no Canva, no DALL-E, no external design tools
- Post fully autonomously on an adaptive schedule that learns from engagement data
- Maintain a 7-day content buffer at all times

---

## Non-Goals

- No manual approval workflow (fully autonomous by design)
- No web UI or admin dashboard (VS Code + log files is sufficient)
- No video recording or editing (agent posts scripts + thumbnails; recorded video dropped in manually)
- No multi-brand support in v1 (BRG only)
- No paid ad management

---

## Architecture

**Language:** Python (single language, full stack)
**Structure:** Modular package — 4 independent engines with clean interfaces

```
brg_social_agent/
├── main.py                  # Entry point — orchestrates all 4 engines
├── config.py                # API keys, brand config, platform settings
├── engines/
│   ├── intelligence/        # Phase 1: Web scraping + trend detection
│   │   ├── scraper.py
│   │   ├── ranker.py
│   │   └── sources.py
│   ├── generation/          # Phase 2: LLM content creation
│   │   ├── writer.py
│   │   ├── seo.py
│   │   └── templates.py
│   ├── visual/              # Phase 3: HTML/CSS → image rendering
│   │   ├── renderer.py
│   │   ├── layouts/
│   │   └── brand.py
│   └── distribution/        # Phase 4: Posting + smart scheduling
│       ├── scheduler.py
│       ├── poster.py
│       └── analytics.py
├── data/
│   ├── queue/               # Generated content awaiting posting
│   ├── posted/              # Archive of posted content
│   ├── analytics/           # Engagement data per post/platform
│   ├── errors/              # Failed post logs
│   └── logs/                # Daily summary logs (YYYY-MM-DD.txt)
└── tests/                   # Unit tests per engine
```

**How it runs:** `python main.py` starts the full pipeline. APScheduler manages recurring jobs. Each engine is independently testable.

---

## Phase 1: Content Intelligence Engine

**Purpose:** Monitor the web every 6 hours for trending leadership/coaching topics and surface the top 20 highest-value ideas for content generation.

### Sources

| Source | What It Pulls | Library |
|--------|--------------|---------|
| Google Trends | Rising search terms in leadership, coaching, productivity | `pytrends` |
| Reddit | Top posts from r/Entrepreneur, r/leadership, r/selfimprovement | `praw` |
| YouTube | Transcripts from top leadership creators | `youtube-transcript-api` |
| Podcasts | RSS feeds — titles + descriptions from top coaching podcasts | `feedparser` |
| News sites | Forbes, Inc, HBR — leadership & coaching articles | `newspaper3k` |
| LinkedIn | Trending hashtags + top-performing posts | `playwright` |
| Competitor accounts | Post text from 10–20 defined competitor creators | `playwright` |

### Processing

1. Each source returns raw items: `{title, body, url, source, timestamp}`
2. Ranker scores each item on: **recency** (exponential decay), **engagement** (likes/shares where available), **relevance** (keyword overlap with BRG topic taxonomy)
3. Top 20 items per cycle written to `data/trends.json`
4. Duplicate suppression: same topic blocked for 14 days after content is generated from it

### Guardrail

The scraper extracts topics and signals only — never copies content verbatim. All generated content is original BRG material.

---

## Phase 2: Content Generation Engine

**Purpose:** Transform trend signals into a full suite of platform-optimized BRG content using Claude as the LLM.

### Content Types Generated Per Trend

| Type | Platforms | Format |
|------|-----------|--------|
| Carousel (5–10 slides) | Instagram, LinkedIn, Facebook | Slide text array + speaker notes |
| Short-form post | LinkedIn, Facebook, X | 150–300 words |
| Hook + script | TikTok, YouTube Shorts, Reels | 30–60 sec script: hook / body / CTA |
| Quote graphic | All platforms | Single extracted power quote |
| Story sequence | Instagram, Facebook | 3 frames: hook → insight → CTA |

### Generation Flow

1. `writer.py` receives a trend item from `data/trends.json`
2. Selects prompt template from `templates.py` for each content type
3. Calls `claude-sonnet-4-6` with a structured prompt containing:
   - Trend topic and context
   - BRG brand voice: authoritative, direct, faith-integrated leadership
   - Charles' name and credentials
   - Platform format constraints (character limits, structure)
4. Claude returns validated JSON — each field maps to a slide, section, or frame. JSON includes a `mood` field (`"light"` or `"dark"`) used by Phase 3 to select the correct visual template variant
5. Output validated with `pydantic` before passing to Phase 3

### SEO / GEO Optimization (`seo.py`)

- Top-ranking keywords injected naturally into post copy
- 10–15 platform-appropriate hashtags generated per post (ranked by volume + niche relevance)
- Location signals added to LinkedIn/Facebook copy for BRG target geographies
- All keywords and hashtags stored per post for analytics correlation

### Brand Voice Guardrails

- System prompt enforces BRG voice: no generic motivational filler, no clichés, direct and actionable, faith-integrated where appropriate
- Each generated piece runs a one-pass voice quality check; fails regenerate once before being flagged and skipped

### Key Libraries

`anthropic`, `pydantic`, `jinja2`

---

## Phase 3: Visual Rendering Engine

**Purpose:** Render structured Phase 2 content into pixel-perfect, BRG-branded images using HTML/CSS templates and a headless Playwright browser.

### Rendering Pipeline

1. `renderer.py` receives content package from Phase 2
2. Selects layout template from `engines/visual/layouts/`
3. `brand.py` injects BRG values: colors, fonts, logo SVG, Charles' headshot, dynamic text
4. Playwright launches headless Chromium, loads HTML, screenshots each frame at exact platform dimensions
5. Images saved to `data/queue/[post_id]/`

### Layout Templates

| Template | Dimensions | Notes |
|----------|-----------|-------|
| `carousel.html` | 1080×1080px per slide | Cover + content slides + CTA slide |
| `quote.html` | 1080×1080px | Bold quote with BRG branding |
| `story.html` | 1080×1920px | 3 frames rendered separately |
| `thumbnail.html` | 1280×720px | YouTube Shorts / TikTok cover |

### Brand System

- Color palette defined as CSS custom properties (configured once in `config.py`)
- Typography: Google Fonts loaded locally — no network dependency at render time
- Logo: SVG injected at render time — crisp at any resolution
- Charles' headshot: optional overlay on quote and carousel cover slides
- Dark and light template variants — selected based on content mood signal from Phase 2

### Platform Sizing

| Platform | Dimensions |
|----------|-----------|
| Instagram feed / LinkedIn / Facebook | 1080×1080px |
| Instagram Story / Facebook Story | 1080×1920px |
| X (Twitter) | 1600×900px |
| TikTok / YouTube Shorts cover | 1280×720px |

### Key Libraries

`playwright`, `jinja2`, `Pillow`

---

## Phase 4: Distribution + Smart Scheduling Engine

**Purpose:** Post finished content to all 6 platforms at optimally timed intervals, then learn from engagement data to improve cadence weekly.

### Platform API Connections

| Platform | API | Posts |
|----------|-----|-------|
| LinkedIn | LinkedIn API v2 | Text posts + image carousels |
| Instagram | Meta Graph API | Feed, carousels, Reels, Stories |
| Facebook | Meta Graph API | Posts, carousels, Stories |
| X (Twitter) | Twitter API v2 | Text + image attachments |
| TikTok | TikTok Content Posting API | Auto-post when video file present; otherwise queued |
| YouTube Shorts | YouTube Data API v3 | Upload when video file present; otherwise thumbnail + description |

> **TikTok / YouTube Shorts:** Agent posts script + thumbnail automatically. For recorded video, drop `video.mp4` into `data/queue/[post_id]/` and the agent uploads it on next scheduler cycle.

### Smart Scheduling

**Baseline defaults (week 1):**

| Platform | Frequency | Default Times |
|----------|-----------|--------------|
| LinkedIn | 1x weekdays | 7–9am or 12–1pm CT |
| Instagram | 2x daily | 6–9am and 6–9pm CT |
| Facebook | 1x daily | 1–4pm CT |
| X | 3–5x daily | Morning / afternoon / evening spread |
| TikTok | 2x daily | 7–9am and 7–9pm CT |
| YouTube Shorts | 1x daily | 12–3pm CT |

**Adaptive learning:**
- `analytics.py` polls each platform API after each post for: likes, comments, shares, saves, reach, click-throughs
- Every Sunday: 4-week rolling analysis identifies highest-engagement days, times, and content types per platform
- Next week's schedule adjusted using weighted average of recent performance
- No ML library required — implemented as simple statistical scoring

### Queue Management

- Agent maintains a 7-day buffer of ready-to-post content in `data/queue/`
- When buffer drops below 3 days, it triggers Phase 1 → 2 → 3 automatically to refill
- Posted content archived to `data/posted/` with full metadata

### Autonomous Guardrails

- Rate limit awareness: respects each platform's API limits with automatic exponential backoff
- Failure handling: failed posts retry 3x, then log to `data/errors/` and skip — no silent drops
- Daily summary log: what posted, what performed, what's queued — saved to `data/logs/YYYY-MM-DD.txt`

### Key Libraries

`APScheduler`, `httpx`, `tweepy`, `google-api-python-client`, `praw`

---

## Data Flow (End to End)

```
[Web Sources]
     ↓
Phase 1: Intelligence Engine
  → data/trends.json (top 20 ranked topics)
     ↓
Phase 2: Generation Engine
  → data/queue/[post_id]/content.json (structured post text, scripts, hashtags)
     ↓
Phase 3: Visual Engine
  → data/queue/[post_id]/*.png (branded images per platform)
     ↓
Phase 4: Distribution Engine
  → Posts to LinkedIn, Instagram, Facebook, X, TikTok, YouTube Shorts
  → data/posted/[post_id]/ (archive)
  → data/analytics/[post_id].json (engagement results)
     ↓
Scheduler reads analytics → adjusts next week's cadence
```

---

## Setup Requirements

Before first run, configure in `config.py`:

- BRG brand colors (hex codes)
- BRG logo file path
- Charles' headshot file path
- Google Fonts family names
- API credentials for all 6 platforms
- Reddit API credentials (for `praw`)
- Anthropic API key
- Competitor account handles to monitor
- Target geographies for GEO signals

---

## Implementation Phases

| Phase | Deliverable | Dependencies |
|-------|-------------|-------------|
| 1 | Content Intelligence Engine | `playwright`, `praw`, `pytrends`, `feedparser`, `newspaper3k`, `youtube-transcript-api` |
| 2 | Content Generation Engine | Phase 1 output, `anthropic`, `pydantic`, `jinja2` |
| 3 | Visual Rendering Engine | Phase 2 output, `playwright`, `Pillow` |
| 4 | Distribution + Scheduling | Phase 3 output, all platform APIs, `APScheduler` |

Each phase is independently runnable and testable before the next phase begins.

---

## Testing Strategy

- Unit tests per engine in `tests/`
- Phase 1: mock HTTP responses, assert ranker scoring logic
- Phase 2: mock Claude responses, assert output JSON schema validation
- Phase 3: render a sample template, assert output image dimensions
- Phase 4: mock platform API calls, assert scheduler cadence adjustments
- Integration test: run full pipeline end-to-end with test credentials against sandbox/staging accounts

---

## Open Questions (Resolved)

| Question | Decision |
|----------|---------|
| Approval workflow | Fully autonomous — no manual review |
| Image generation | HTML/CSS rendered via Playwright — no external design tools |
| Tech stack | Python only |
| Posting cadence | Adaptive, learned from engagement data |
| Content sources | All: news, Reddit, YouTube, podcasts, competitors, Google Trends |
