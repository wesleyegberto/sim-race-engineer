"""CLI entry point: simracing-analyze <path.parquet> [--port N] [--no-browser]"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="simracing-analyze",
        description="Interactive web viewer for SimRacing session/lap parquet files.",
    )
    parser.add_argument("path", type=Path, help="Path to session.parquet or lap_NN.parquet")
    parser.add_argument("--port", type=int, default=8050, help="HTTP port (default: 8050)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    args = parser.parse_args()

    if not args.path.exists():
        print(f"Error: file not found: {args.path}", file=sys.stderr)
        sys.exit(1)

    try:
        from dash import Dash
    except ImportError:
        print(
            "dash is not installed.\n"
            "Run:  uv pip install -e '.[analysis]'",
            file=sys.stderr,
        )
        sys.exit(1)

    from .loader import load_parquet, lap_quality
    from .layout import create_layout
    from . import callbacks

    print(f"Loading {args.path} …", end=" ", flush=True)
    df, laps = load_parquet(args.path)
    print(f"{len(df):,} frames across {len(laps)} lap(s).")

    for lap_n, lap_df in sorted(laps.items()):
        q = lap_quality(lap_df)
        if not q["timer_active"] and not q["car_moving"]:
            print(
                f"  [AVISO] Lap {lap_n}: timer parado + carro estático "
                f"({q['rows']} frames) — dados sem pilotagem real."
            )

    callbacks.set_data(laps)

    app = Dash(__name__, title="SimRacing Analysis")
    app.layout = create_layout(sorted(laps.keys()), args.path.name)
    callbacks.register(app)

    url = f"http://127.0.0.1:{args.port}"
    print(f"Viewer running at {url}  (Ctrl+C to quit)")

    if not args.no_browser:
        import threading
        import webbrowser
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()

    app.run(host="127.0.0.1", port=args.port, debug=False)


if __name__ == "__main__":
    main()
