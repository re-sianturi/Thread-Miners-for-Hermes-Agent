#!/usr/bin/env python3
"""
Usage: scrape.py --query Q --start YYYY-MM-DD --end YYYY-MM-DD --run-dir DIR

Calls scrapecreators.com /v1/threads/search for one keyword.
Handles retries with exponential backoff, response caching by query hash.

Requirements: pip install PyYAML  (for YAML I/O)
"""

import argparse, hashlib, json, os, sys, time, urllib.parse, urllib.request

API_URL = "https://api.scrapecreators.com/v1/threads/search"
CACHE_TTL = 86400  # 24 hours
MAX_RETRIES = 4
BACKOFF = [1, 2, 4, 8]


def cache_key(query, start, end):
    raw = f"{query}|{start}|{end}|trim=false"
    return hashlib.sha256(raw.encode()).hexdigest()


def query_slug(query):
    safe = "".join(c if c.isalnum() else "_" for c in query.lower().strip())
    return safe[:60]


def main():
    parser = argparse.ArgumentParser(description="Scrape Threads for one keyword")
    parser.add_argument("--query", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()

    api_key = os.environ.get("SCRAPECREATORS_API_KEY")
    if not api_key:
        print("FATAL: SCRAPECREATORS_API_KEY is not set", file=sys.stderr)
        sys.exit(1)

    run_dir = os.path.abspath(args.run_dir)
    cache_dir = os.path.join(os.path.dirname(run_dir), "cache")
    os.makedirs(cache_dir, exist_ok=True)
    raw_dir = os.path.join(run_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)

    kh = cache_key(args.query, args.start, args.end)
    cache_path = os.path.join(cache_dir, f"{kh}.json")
    slug = query_slug(args.query)
    out_path = os.path.join(raw_dir, f"{slug}.json")

    # Check cache
    if os.path.exists(cache_path):
        age = time.time() - os.path.getmtime(cache_path)
        if age < CACHE_TTL:
            import shutil
            shutil.copy2(cache_path, out_path)
            with open(out_path) as f:
                data = json.load(f)
            posts = data.get("data", {}).get("items", data.get("items", []))
            print(f"OK {args.query} {len(posts)} (cached)")
            sys.exit(0)

    params = urllib.parse.urlencode({
        "query": args.query,
        "start_date": args.start,
        "end_date": args.end,
    })
    url = f"{API_URL}?{params}"
    req = urllib.request.Request(url, headers={"x-api-key": api_key})

    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
                data = json.loads(raw)
        except urllib.error.HTTPError as e:
            status = e.code
            body = e.read().decode(errors="replace")
            if status == 429 or status >= 500:
                last_err = f"HTTP {status}: {body[:200]}"
                if attempt < MAX_RETRIES - 1:
                    time.sleep(BACKOFF[attempt])
                continue
            else:
                print(f"FATAL: HTTP {status} for query '{args.query}': {body[:300]}", file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            last_err = str(e)
            if attempt < MAX_RETRIES - 1:
                time.sleep(BACKOFF[attempt])
            continue
        else:
            # Success
            with open(cache_path, "w") as f:
                json.dump(data, f)
            import shutil
            shutil.copy2(cache_path, out_path)
            posts = data.get("data", {}).get("items", data.get("items", []))
            print(f"OK {args.query} {len(posts)}")
            sys.exit(0)

    print(f"FATAL: All {MAX_RETRIES} retries exhausted for '{args.query}': {last_err}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
