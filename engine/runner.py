"""Forrest Analysis Engine — Main Runner

Usage:
    python -m engine.runner              # Run all passes, print findings
    python -m engine.runner --top 5      # Show top 5 findings
    python -m engine.runner --json       # Output as JSON
"""

import sqlite3
import os
import sys
import json
import time
import importlib
import pkgutil
from pathlib import Path

from .findings import Finding, RunResult
from .scoring import score_finding


def get_db_path():
    """Resolve the SQLite database path."""
    # Walk up from engine/ to find data/onetag.db
    here = Path(__file__).resolve().parent
    repo_root = here.parent
    db_path = repo_root / 'data' / 'onetag.db'
    
    # Also try relative to CWD
    if not db_path.exists():
        alt = Path.cwd() / 'data' / 'onetag.db'
        if alt.exists():
            return str(alt)
    
    return str(db_path)


def discover_passes():
    """Auto-discover all analysis pass modules in engine/passes/."""
    passes_dir = Path(__file__).resolve().parent / 'passes'
    passes = []
    
    for importer, modname, ispkg in pkgutil.iter_modules([str(passes_dir)]):
        if modname.startswith('_'):
            continue
        module = importlib.import_module(f'engine.passes.{modname}')
        if hasattr(module, 'run'):
            passes.append((modname, module.run))
    
    return passes


def run_all(conn) -> RunResult:
    """Run all discovered analysis passes and return ranked findings."""
    start = time.time()
    passes = discover_passes()
    
    all_findings = []
    for name, pass_fn in passes:
        try:
            findings = pass_fn(conn)
            all_findings.extend(findings)
        except Exception as e:
            print(f"  ⚠️  Pass '{name}' failed: {e}", file=sys.stderr)
    
    # Sort by score descending
    all_findings.sort(key=lambda f: f.score, reverse=True)
    
    elapsed = time.time() - start
    return RunResult(
        passes_run=len(passes),
        total_findings=len(all_findings),
        findings=all_findings,
        duration_seconds=round(elapsed, 2),
    )


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Forrest Analysis Engine')
    parser.add_argument('--top', type=int, default=0, help='Show only top N findings')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--db', type=str, default=None, help='Path to SQLite database')
    args = parser.parse_args()
    
    db_path = args.db or get_db_path()
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}", file=sys.stderr)
        print(f"   Run 'python scripts/seed_data.py' first to create it.", file=sys.stderr)
        sys.exit(1)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    result = run_all(conn)
    conn.close()
    
    if args.json:
        top = result.top(args.top) if args.top else result.findings
        print(json.dumps([f.to_dict() for f in top], indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"  FORREST ANALYSIS ENGINE")
        print(f"  {result.passes_run} analysis passes | {result.total_findings} findings | {result.duration_seconds}s")
        print(f"{'='*60}\n")
        
        if result.total_findings == 0:
            print("  No findings generated. Try running with more data.")
        else:
            top = result.top(args.top) if args.top else result.findings
            for i, f in enumerate(top, 1):
                print(f"  #{i}  {f}")
                print()
        
        print(f"{'='*60}")


if __name__ == '__main__':
    main()
