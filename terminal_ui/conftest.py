"""Configure sys.path for tests to include the library source."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "library"))
