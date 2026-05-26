#!/usr/bin/env bash
set -euo pipefail
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"
HERMES_SKILLS="${HERMES_SKILLS_DIR:-$HOME/.hermes/skills}"
mkdir -p "$HERMES_SKILLS/social"
for skill in threads-orchestrator threads-scraper threads-scorer \
             threads-classifier threads-qa reels-script-writer; do
  rm -rf "$HERMES_SKILLS/social/$skill"
  cp -r "$SOURCE_DIR/skills/social/$skill" "$HERMES_SKILLS/social/"
done
echo "Installed 6 skills to $HERMES_SKILLS/social/"
echo ""
echo "Next steps:"
echo "  hermes config set skills.config.threads_miner.output_dir ~/threads-miner-runs"
echo "  hermes config set-env SCRAPECREATORS_API_KEY <your key>"
echo "  hermes skills reload"
echo ""
echo "Then run:"
echo '  hermes chat --toolsets skills -q "cari ide reel dari threads ..."'
