"""Make the PhantomWiki Harbor adapter modules importable from the tests.

The adapter lives outside the installed ``phantom_wiki``/``phantom_eval`` packages (it is
plain scripts copied into Docker build contexts), so we add its directories to sys.path.
"""

import sys
from pathlib import Path

ADAPTER_DIR = Path(__file__).resolve().parents[2] / "harbor" / "adapters" / "phantom-wiki"

for path in (ADAPTER_DIR, ADAPTER_DIR / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
