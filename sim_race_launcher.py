"""PyInstaller entry point — uses absolute imports so the bundle can load correctly."""
import os
import sys
import traceback
from pathlib import Path

# With --windowed (console=False) stdout/stderr are /dev/null. Write startup
# errors to a file so crashes before logging is configured are not silent.
_EARLY_LOG = Path.home() / "sim-race-engineer" / "startup_crash.log"


def _write_early_crash(msg: str) -> None:
    try:
        _EARLY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with _EARLY_LOG.open("a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass


def _early_excepthook(exc_type, exc_value, exc_tb) -> None:
    _write_early_crash(
        "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    )
    sys.__excepthook__(exc_type, exc_value, exc_tb)


sys.excepthook = _early_excepthook

_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if os.path.isdir(_src) and _src not in sys.path:
    sys.path.insert(0, _src)

try:
    from simraceengineer.main import main  # noqa: E402
except Exception:
    _write_early_crash("Import failed:\n" + traceback.format_exc())
    sys.exit(1)

if __name__ == "__main__":
    main()
