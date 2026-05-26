# Hermes Threads Miner

Bundle of 6 skills for mining Threads content into reel-ready scripts.
Scrapes, scores, classifies, validates, and drafts reel scripts — one
command, one timestamped output folder.

## Install

```bash
bash install.sh
hermes config set skills.config.threads_miner.output_dir ~/threads-miner-runs
hermes config set-env SCRAPECREATORS_API_KEY <your scrapecreators.com key>
hermes skills reload
```

## Usage

```
hermes chat --toolsets skills -q "cari ide reel dari threads tentang AI untuk pemula, 2-28 Mei 2026"
```

Or in any session, just say:

- "cari ide reel dari threads"
- "mining threads untuk konten"
- "scrape threads keyword bisnis, 2026-04-01 sampai 2026-05-01"

## Output

Every run creates a timestamped folder under your configured output dir:

```
~/threads-miner-runs/
├── cache/                              # API response cache (24h TTL)
├── 2026-05-26T14-30-bisnis/
│   ├── config.yaml
│   ├── scored.csv                      # Human-readable, open in Excel/Sheets
│   ├── scored.json                     # Machine-readable, full fields
│   ├── classified.json
│   ├── top.json                        # Reel-ready candidates
│   ├── reels/reel-001.md              # Draft scripts
│   └── run-summary.md                  # One-page recap
```

## API Key

Get one at https://scrapecreators.com. Set via:

```bash
hermes config set-env SCRAPECREATORS_API_KEY sk-xxxx
```
