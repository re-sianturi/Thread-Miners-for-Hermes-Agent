#!/usr/bin/env python3
"""
Usage: run_summary.py --run-dir DIR

Reads all artifacts in the run dir and produces run-summary.md.
Prints the summary to stdout (redirect to run-summary.md).

Requirements: pip install PyYAML
"""

import argparse, json, os, sys, time, yaml

UNSTABLE_DAYS = 7  # posts younger than this flagged as unstable


def main():
    parser = argparse.ArgumentParser(description="Generate run summary")
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()

    run_dir = os.path.abspath(args.run_dir)

    # Read config
    config = {}
    config_path = os.path.join(run_dir, "config.yaml")
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}

    # Read scored.json for counts
    scored = []
    scored_path = os.path.join(run_dir, "scored.json")
    if os.path.exists(scored_path):
        with open(scored_path) as f:
            scored = json.load(f)

    # Read top.json
    top = []
    top_path = os.path.join(run_dir, "top.json")
    if os.path.exists(top_path):
        with open(top_path) as f:
            top = json.load(f)

    # Read raw files
    raw_dir = os.path.join(run_dir, "raw")
    raw_count = 0
    if os.path.isdir(raw_dir):
        raw_count = len([f for f in os.listdir(raw_dir) if f.endswith(".json")])

    # Read deduped files
    deduped_pre = 0
    deduped_pre_path = os.path.join(run_dir, "deduped-pre-filter.json")
    if os.path.exists(deduped_pre_path):
        with open(deduped_pre_path) as f:
            deduped_pre = len(json.load(f))

    deduped = 0
    deduped_path = os.path.join(run_dir, "deduped.json")
    if os.path.exists(deduped_path):
        with open(deduped_path) as f:
            deduped = len(json.load(f))

    # Count reel files
    reel_dir = os.path.join(run_dir, "reels")
    reel_files = []
    if os.path.isdir(reel_dir):
        reel_files = sorted([f for f in os.listdir(reel_dir) if f.endswith(".md")])

    # Read QA report
    qa_issues = []
    qa_fixes = 0
    qa_report_path = os.path.join(run_dir, "qa", "report.yaml")
    if os.path.exists(qa_report_path):
        with open(qa_report_path) as f:
            qa_report = yaml.safe_load(f) or {}
        qa_issues = qa_report.get("failed", [])
    fixes_path = os.path.join(run_dir, "qa", "fixes.yaml")
    if os.path.exists(fixes_path):
        with open(fixes_path) as f:
            fixes = yaml.safe_load(f) or []
            qa_fixes = len(fixes) if isinstance(fixes, list) else 0

    # Count API calls (trace files with "classifier" or "writer" prefix)
    trace_dir = os.path.join(run_dir, "trace")
    api_calls = 0
    if os.path.isdir(trace_dir):
        api_calls = len([f for f in os.listdir(trace_dir) if f.endswith(".json")])
    api_calls += raw_count  # each raw file = 1 API call (or cache hit)

    # Build summary
    lines = []
    lines.append(f"# Run Summary: {config.get('run_name', os.path.basename(run_dir))}")
    lines.append(f"")
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"")

    # Config recap
    kws = config.get("keywords", [])
    dr = config.get("date_range", {})
    lines.append(f"## Configuration")
    lines.append(f"- Keywords: {', '.join(kws)}")
    lines.append(f"- Date range: {dr.get('start', '?')} to {dr.get('end', '?')}")
    lines.append(f"- Formula version: {config.get('formula_version', '?')}")
    lines.append(f"")

    # Counts
    lines.append(f"## Pipeline Counts")
    lines.append(f"| Stage | Count |")
    lines.append(f"|-------|-------|")
    lines.append(f"| API calls (or cache hits) | {api_calls} |")
    n_scored = len(scored)
    lines.append(f"| Raw (total across keywords) | {raw_count} files |")
    lines.append(f"| After dedup | {deduped_pre} |")
    lines.append(f"| After filter | {deduped} |")
    lines.append(f"| After scoring+classification | {n_scored} |")
    lines.append(f"| After QA | {n_scored - len(qa_issues)} clean, {len(qa_issues)} flagged |")
    lines.append(f"| Reels generated | {len(reel_files)} |")
    lines.append(f"")

    # Top 3 table
    lines.append(f"## Top {min(3, len(top))} Candidates")
    lines.append(f"| # | Akun | Evg.Score | Classification | Hook |")
    lines.append(f"|---|------|-----------|----------------|------|")
    for i, t in enumerate(top[:3], 1):
        username = t.get("username", "?")
        evg = t.get("evg_score", 0)
        cls = t.get("classification", "?")
        hook = t.get("hook", "")[:50]
        lines.append(f"| {i} | @{username} | {evg:.2f} | {cls} | {hook} |")
    lines.append(f"")

    # QA summary
    if qa_issues:
        lines.append(f"## QA Issues")
        for issue in qa_issues:
            lines.append(f"- **{issue}**: See qa/report.yaml for details")
        if qa_fixes > 0:
            lines.append(f"- {qa_fixes} fixes applied via LLM fixer")
    else:
        lines.append(f"## QA")
        lines.append(f"- All checks passed (no issues)")
    lines.append(f"")

    # Reel files
    if reel_files:
        lines.append(f"## Reel Files")
        for rf in reel_files:
            lines.append(f"- `reels/{rf}`")
    lines.append(f"")

    # Warnings
    warnings = []
    unstable_count = sum(1 for s in scored if s.get("age_days", 999) < UNSTABLE_DAYS)
    if unstable_count > 0:
        warnings.append(f"⚠️  {unstable_count} posts are younger than {UNSTABLE_DAYS} days "
                        f"— their engagement scores are unstable and may change.")

    if qa_issues and qa_fixes == 0:
        warnings.append(f"⚠️  {len(qa_issues)} QA issues remain unresolved after fix cycles.")

    shortfall = max(0, 3 - len(reel_files))
    if shortfall > 0:
        warnings.append(f"⚠️  Shortfall: only {len(reel_files)} reel(s) generated "
                        f"(target 3). Consider widening the date range or lowering "
                        f"the evg_score/tot_int floor.")

    if warnings:
        lines.append(f"## Warnings")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append(f"")

    summary_text = "\n".join(lines)

    # Write to file
    summary_path = os.path.join(run_dir, "run-summary.md")
    with open(summary_path, "w") as f:
        f.write(summary_text)

    print(summary_text)


if __name__ == "__main__":
    main()
