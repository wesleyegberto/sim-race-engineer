"""PyInstaller entry point — uses absolute imports so the bundle can load correctly."""
import os
import sys

_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if os.path.isdir(_src) and _src not in sys.path:
    sys.path.insert(0, _src)

from simracing.main import main  # noqa: E402

if __name__ == "__main__":
    main()
