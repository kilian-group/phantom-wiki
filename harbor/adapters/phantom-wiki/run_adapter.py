#!/usr/bin/env python
"""CLI entry point for the PhantomWiki Harbor adapter.

Harbor invokes adapters with at least ``--output-dir`` (and optionally ``--split``).

Examples:
    # Directly, to materialize a dataset you can point `harbor run` at:
    python run_adapter.py --output-dir ./out --num-tasks 50

    # Larger universe (passes flags through to pw-generate inside Docker):
    python run_adapter.py --output-dir ./out --num-tasks 100 \\
        --gen-flags "--num-family-trees 10 --max-family-tree-size 50 --question-depth 20"
"""

from __future__ import annotations

from adapter import main

if __name__ == "__main__":
    main()
