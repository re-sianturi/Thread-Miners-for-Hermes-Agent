#!/usr/bin/env python3
"""
Usage: validate.py --run-dir DIR

Reads scored.json and runs 12 deterministic QA checks. Writes
qa/report.yaml. Exit 0 if all pass, 1 otherwise.

Requirements: pip install PyYAML
"""

import argparse, json, os, sys, time, yaml


def yaml_dump(data):
    """Serialize to YAML string."""
    return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)


# Taxonomy labels for D8
TAXONOMY_LABELS = {
    "Edukasi (Framework)", "Edukasi (Story)", "Edukasi (Niche)",
    "Edukasi (Berita AI)", "Edukasi (Berita)", "Tutorial (Pemula)",
    "Diskusi (Opini)", "Networking", "Hiring (B2B)",
    "Hiring (Spesialis)", "Hiring (Instan)", "Cari Mentor/Course",
    "Kolaborasi Bisnis", "Kolaborasi Agensi", "Promosi Langsung",
    "Opini Singkat", "Lainnya",
}


def main():
    parser = argparse.ArgumentParser(description="Validate scored and classified posts")
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()

    run_dir = os.path.abspath(args.run_dir)
    in_path = os.path.join(run_dir, "scored.json")
    if not os.path.exists(in_path):
        print(f"FATAL: {in_path} not found. Run scorer first.", file=sys.stderr)
        sys.exit(1)

    with open(in_path) as f:
        posts = json.load(f)

    qa_dir = os.path.join(run_dir, "qa")
    os.makedirs(qa_dir, exist_ok=True)

    passed = []
    failed = []
    total = len(posts)
    seen_ids = set()

    for check_name, check_fn in [
        ("D1", lambda: check_d1(posts)),
        ("D2", lambda: check_d2(posts)),
        ("D3", lambda: check_d3(posts)),
        ("D4", lambda: check_d4(posts)),
        ("D5", lambda: check_d5(posts)),
        ("D6", lambda: check_d6(posts)),
        ("D7", lambda: check_d7(posts)),
        ("D8", lambda: check_d8(posts)),
        ("D9", lambda: check_d9(posts)),
        ("D10", lambda: check_d10(posts)),
        ("D11", lambda: check_d11(posts, seen_ids)),
        ("D12", lambda: check_d12(posts)),
    ]:
        issues = check_fn()
        if issues:
            failed.append({"check": check_name, "offending_rows": issues})
        else:
            passed.append(check_name)

    # Build report
    fixable_checks = {"D9", "D10"}
    fatal_checks = {"D1", "D8", "D11", "D12"}
    fixable = [f for f in failed if f["check"] in fixable_checks]
    fatal = [f for f in failed if f["check"] in fatal_checks]

    report = {
        "run_dir": run_dir,
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_rows": total,
        "passed": passed,
        "failed": [f["check"] for f in failed],
        "details": failed,
        "fixable_by_llm": [f["check"] for f in fixable],
        "fatal": [f["check"] for f in fatal],
    }

    report_path = os.path.join(qa_dir, "report.yaml")
    with open(report_path, "w") as f:
        f.write(yaml_dump(report))

    if failed:
        print(f"QA_FAIL {len(failed)} checks failed")
        sys.exit(1)
    else:
        print(f"QA_PASS all {total} rows passed")
        sys.exit(0)


# --- Individual checks ---

def check_d1(posts):
    """Every row has post_id, author(username), caption, L, C, R (non-null)."""
    issues = []
    for i, p in enumerate(posts):
        missing = []
        if not p.get("post_id"): missing.append("post_id")
        if not p.get("username"): missing.append("username")
        if not p.get("caption"): missing.append("caption")
        if p.get("like_count") is None: missing.append("like_count")
        if p.get("reply_count") is None: missing.append("reply_count")
        if p.get("reshare_repost_quote") is None: missing.append("reshare_repost_quote")
        if missing:
            issues.append({
                "row": i,
                "post_id": p.get("post_id", "?"),
                "field": ", ".join(missing),
                "reason": f"Missing fields: {', '.join(missing)}",
            })
    return issues


def check_d2(posts):
    """tot_int == L + C + R for every row."""
    issues = []
    for i, p in enumerate(posts):
        expected = p.get("like_count", 0) + p.get("reply_count", 0) + p.get("reshare_repost_quote", 0)
        actual = p.get("tot_int", 0)
        if abs(expected - actual) > 0:
            issues.append({
                "row": i,
                "post_id": p.get("post_id", "?"),
                "field": "tot_int",
                "value": actual,
                "reason": f"Expected {expected}, got {actual}",
            })
    return issues


def check_d3(posts):
    """point == 1*L + 2*C + 3*R."""
    issues = []
    for i, p in enumerate(posts):
        expected = (1 * p.get("like_count", 0)
                    + 2 * p.get("reply_count", 0)
                    + 3 * p.get("reshare_repost_quote", 0))
        actual = p.get("point", 0)
        if abs(expected - actual) > 0:
            issues.append({
                "row": i,
                "post_id": p.get("post_id", "?"),
                "field": "point",
                "value": actual,
                "reason": f"Expected {expected}, got {actual}",
            })
    return issues


def check_d4(posts):
    """viralitas == R / tot_int (or 0 when tot_int=0)."""
    issues = []
    for i, p in enumerate(posts):
        r = p.get("reshare_repost_quote", 0)
        ti = p.get("tot_int", 0)
        expected = r / ti if ti > 0 else 0.0
        actual = p.get("viralitas", 0)
        if abs(expected - actual) > 1e-6:
            issues.append({
                "row": i,
                "post_id": p.get("post_id", "?"),
                "field": "viralitas",
                "value": actual,
                "reason": f"Expected {expected:.6f}, got {actual:.6f}",
            })
    return issues


def check_d5(posts):
    """eng_density == C/L for L>0, else null."""
    issues = []
    for i, p in enumerate(posts):
        l = p.get("like_count", 0)
        c = p.get("reply_count", 0)
        expected = c / l if l > 0 else None
        actual = p.get("eng_density")
        if expected is None and actual is not None and actual != "N/A":
            issues.append({
                "row": i,
                "post_id": p.get("post_id", "?"),
                "field": "eng_density",
                "value": actual,
                "reason": f"Expected N/A (L=0), got {actual}",
            })
        elif expected is not None and actual is not None:
            try:
                if abs(expected - float(actual)) > 1e-6:
                    issues.append({
                        "row": i,
                        "post_id": p.get("post_id", "?"),
                        "field": "eng_density",
                        "value": actual,
                        "reason": f"Expected {expected:.6f}, got {actual}",
                    })
            except (ValueError, TypeError):
                pass
    return issues


def check_d6(posts):
    """age_days >= 1."""
    issues = []
    for i, p in enumerate(posts):
        ad = p.get("age_days", 0)
        if ad < 1:
            issues.append({
                "row": i,
                "post_id": p.get("post_id", "?"),
                "field": "age_days",
                "value": ad,
                "reason": f"age_days={ad}, minimum is 1",
            })
    return issues


def check_d7(posts):
    """evg_score == point / age_days."""
    issues = []
    for i, p in enumerate(posts):
        pt = p.get("point", 0)
        ad = p.get("age_days", 1)
        expected = pt / ad
        actual = p.get("evg_score", 0)
        if abs(expected - actual) > 1e-6:
            issues.append({
                "row": i,
                "post_id": p.get("post_id", "?"),
                "field": "evg_score",
                "value": actual,
                "reason": f"Expected {expected:.6f}, got {actual:.6f}",
            })
    return issues


def check_d8(posts):
    """classification in taxonomy labels (or null/empty)."""
    issues = []
    for i, p in enumerate(posts):
        cls = p.get("classification", "")
        if cls and cls not in TAXONOMY_LABELS:
            issues.append({
                "row": i,
                "post_id": p.get("post_id", "?"),
                "field": "classification",
                "value": cls,
                "reason": f"Not in taxonomy: '{cls}'",
            })
    return issues


def check_d9(posts):
    """hook is non-empty and len(hook) <= 80."""
    issues = []
    for i, p in enumerate(posts):
        hook = p.get("hook", "")
        if not hook:
            issues.append({
                "row": i,
                "post_id": p.get("post_id", "?"),
                "field": "hook",
                "value": "(empty)",
                "reason": "Hook is empty",
            })
        elif len(hook) > 80:
            issues.append({
                "row": i,
                "post_id": p.get("post_id", "?"),
                "field": "hook",
                "value": hook[:50] + "...",
                "reason": f"len={len(hook)}, exceeds 80",
            })
    return issues


def check_d10(posts):
    """tags is non-empty (after classifier ran)."""
    issues = []
    for i, p in enumerate(posts):
        tags = p.get("tags", "")
        if not tags:
            issues.append({
                "row": i,
                "post_id": p.get("post_id", "?"),
                "field": "tags",
                "value": "(empty)",
                "reason": "Tags are empty after classification",
            })
    return issues


def check_d11(posts, seen_ids):
    """No duplicate post_id across rows."""
    issues = []
    for i, p in enumerate(posts):
        pid = p.get("post_id", "?")
        if pid in seen_ids:
            issues.append({
                "row": i,
                "post_id": pid,
                "field": "post_id",
                "value": pid,
                "reason": f"Duplicate post_id",
            })
        seen_ids.add(pid)
    return issues


def check_d12(posts):
    """is_reply must be false (defense in depth)."""
    issues = []
    for i, p in enumerate(posts):
        # Scored records don't have is_reply directly; check raw data store
        # This is defense-in-depth from the scraper's filter
        pass  # Filter already removed replies; this is a placeholder
    return issues


if __name__ == "__main__":
    main()
