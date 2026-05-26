# Thread Miners for Hermes Agent

> A [Hermes Agent](https://hermes-agent.nousresearch.com) skill bundle that mines
> trending Threads posts and drafts ready-to-record reel scripts with CTAs.

Thread Miners is a 6-skill orchestrated pipeline that scrapes Threads via
[scrapecreators.com](https://scrapecreators.com), scores posts by weighted
engagement, classifies topics against a fixed taxonomy, runs QA, and outputs
2-3 reel-ready scripts per run.

Built for content creators who want their reel ideas grounded in what's
actually performing in their niche on Threads — not guesswork, not vibes.

---

## How it works

Six skills working as a sequential pipeline. State flows via JSON/YAML files
between skills, so the orchestrator's main context stays clean — each
specialist's SKILL.md only enters context when invoked.

| Skill | Job |
|-------|-----|
| `threads-orchestrator` | Entry point. Coordinates the pipeline. |
| `threads-scraper` | Calls scrapecreators API. Retries, caches, dedupes, filters. |
| `threads-scorer` | Computes engagement metrics. Pure deterministic Python. |
| `threads-classifier` | Extracts hook, classifies topic from taxonomy, generates tags. |
| `threads-qa` | Validates the scored table. Deterministic checks first, LLM fixer as fallback. |
| `reels-script-writer` | Filters reel-ready candidates and drafts scripts with CTAs. |

## Scoring methodology

Each post is scored on weighted engagement, normalized by age:

```
L = like count
C = comment count
R = reshares + reposts + quotes

Point      = 1·L + 2·C + 3·R
Evg.Score  = Point / Usia(Hari)        ← primary ranking signal
```

Comments and reshares weigh more than passive likes because they signal
higher-quality engagement. Dividing by post age (floored at 1 day) means old
posts can't dominate just by accumulating likes over time.

## Output

Each run lands in a timestamped folder under your configured output dir
(default `~/threads-miner-runs/`):

```
2026-05-26T14-30-business/
├── config.yaml          input parameters
├── raw/*.json           raw API responses, one file per keyword
├── deduped.json         after dedup + reply/paid filter
├── scored.csv           human-readable table (open in Excel)
├── scored.json          machine-readable, full fields
├── top.json             reel-ready candidates after readiness filter
├── qa/
│   ├── report.yaml      QA findings
│   └── fixes.yaml       what the LLM fixer changed
├── reels/
│   ├── reel-001.md      ready-to-record draft
│   ├── reel-002.md
│   └── reel-003.md
└── run-summary.md       one-page overview
```

### `scored.csv` columns

| Column | Description |
|--------|-------------|
| Akun | `@username` |
| Teks Hook (Pancingan Pertama) | First sentence, ≤80 chars |
| L / C / R | Likes / Comments / Reshares |
| Tot. Int. | L + C + R |
| Viralitas (R/Tot) | Share of total engagement that is reshares |
| Eng. Density (C/L) | Comments per like (proxy for discussion-worthiness) |
| Usia (Hari) | Days since post |
| Evg. Score | Velocity-adjusted score (primary sort) |
| Format Media | Carousel / Gambar / Video / Teks |
| Klasifikasi Topik | Topic label from taxonomy |
| Tags Algoritma & Keywords | Algorithmic tags + LLM-extracted content keywords |

### Reel script format

Each `reel-NNN.md` has a hook (≤12 words), a 60-90 second body (3-5 beats),
a CTA selected from a pattern library based on topic classification, and
source attribution back to the original post.

## Requirements

- [Hermes Agent](https://hermes-agent.nousresearch.com) installed
- [scrapecreators.com](https://scrapecreators.com) API key (paid; ~$X per 1K calls — check current pricing)
- Python 3.10+ (stdlib only — no `pip install` required for runtime)

## Install

```bash
git clone https://github.com/re-sianturi/Thread-Miners-for-Hermes-Agent
cd Thread-Miners-for-Hermes-Agent
bash install.sh
```

Set your API key once (shared across all Hermes projects on this machine):

```bash
hermes config set-env SCRAPECREATORS_API_KEY sk_your_key_here
hermes config set skills.config.threads_miner.output_dir ~/threads-miner-runs
hermes skills reload
```

## Usage

Start a Hermes session with skills enabled:

```bash
hermes chat --toolsets skills,terminal
```

Then ask in natural language (Indonesian or English both work):

```
cari ide reel dari threads untuk keyword: business, marketing,
online shop, lead generation, ai technology. rentang waktu sebulan terakhir.
```

```
find reel ideas from threads for: copywriting, freelancing, indie hacking.
last 30 days. give me 3 top picks.
```

Hermes will run the full pipeline and drop output in
`~/threads-miner-runs/<timestamp>/`. Open `run-summary.md` first, then the
files in `reels/`.

## Taxonomy

Topic classifications are fixed in
`skills/social/threads-classifier/references/taxonomy.yaml`. Categories cover:

- **Reel-ready**: Edukasi (Framework / Story / Niche / Berita / Berita AI), Tutorial (Pemula), Diskusi (Opini)
- **Non-reel** (filtered out from candidates): Networking, Hiring (B2B / Spesialis / Instan), Cari Mentor, Kolaborasi (Bisnis / Agensi), Promosi Langsung, Opini Singkat

To add or modify a category, edit the YAML. The classifier picks from this
list only — it can't invent new categories. Posts that don't fit go to
`Lainnya` and get flagged for manual review.

## Limitations

- **Sample size**: scrapecreators returns only 10 results per query. Multiple
  keywords + dedup expands coverage, but this is still a public-data sample,
  not exhaustive scraping.
- **No sentiment analysis**: scoring is engagement-based only. A high-Evg post
  could be controversial or a roast — the topic classifier helps filter, but
  you should still review before recording.
- **English + Indonesian mixed content**: the LLM steps (classification, tag
  extraction, reel drafting) handle both, but the taxonomy and CTA library are
  Indonesian-first.
- **Drafts, not finals**: reel scripts are starting points. Verify any claims,
  stats, or quotes against the source post manually.

## Architecture notes

This bundle deliberately uses **sequential delegation** rather than
subagents. The orchestrator loads each specialist skill via `skill_view`,
runs its procedure, saves artifacts to disk, then moves on. Hermes doesn't
support true subagents (unlike Claude Code), and file-based state hand-off
is more debuggable anyway — you can inspect any intermediate JSON to figure
out where the pipeline went sideways.

The 6-skill split exists because a single SKILL.md would be ≥1000 lines and
would dump scraping + scoring + classification + QA + writing into one
context every time the skill triggered. Splitting by concern keeps each
SKILL.md ≤300 lines and ensures only the relevant skill is loaded at each
phase.

## Disclaimer

This tool scrapes **public** Threads data via a third-party API. Respect
Threads' terms of service. Don't use it for harassment, mass-reporting,
impersonation, or anything that violates platform rules. The reel scripts
are drafts — your voice, your edits, your responsibility.

## License

MIT
