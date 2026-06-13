#!/usr/bin/env bash
# build.sh — Package Sim Race Engineer as a macOS .app bundle via PyInstaller
# Usage: ./build.sh [--clean]
set -euo pipefail

APP_NAME="SimRaceEngineer"
ENTRY="simracing_launcher.py"
ICON="src/simracing/img/engineer.png"
OUT_DIR="dist"

# ── Parse args ────────────────────────────────────────────────────────────────
CLEAN=0
for arg in "$@"; do
  [[ "$arg" == "--clean" ]] && CLEAN=1
done

# ── Activate venv ─────────────────────────────────────────────────────────────
if [[ ! -d ".venv" ]]; then
  echo "ERROR: .venv not found. Run: uv venv && uv pip install -e '.[dev]'"
  exit 1
fi
source .venv/bin/activate

# ── Install PyInstaller if needed ─────────────────────────────────────────────
if ! python -m PyInstaller --version &>/dev/null; then
  echo "Installing PyInstaller..."
  uv pip install pyinstaller
fi

# ── Clean previous build ──────────────────────────────────────────────────────
if [[ $CLEAN -eq 1 ]]; then
  echo "Cleaning previous build..."
  rm -rf build dist "${APP_NAME}.spec"
fi

# ── Convert PNG icon to ICNS (macOS requires .icns) ──────────────────────────
ICNS_PATH="build_tmp/${APP_NAME}.icns"
mkdir -p build_tmp
if [[ -f "$ICON" ]]; then
  ICONSET="build_tmp/${APP_NAME}.iconset"
  mkdir -p "$ICONSET"
  sips -z 16  16  "$ICON" --out "${ICONSET}/icon_16x16.png"    &>/dev/null
  sips -z 32  32  "$ICON" --out "${ICONSET}/icon_16x16@2x.png" &>/dev/null
  sips -z 32  32  "$ICON" --out "${ICONSET}/icon_32x32.png"    &>/dev/null
  sips -z 64  64  "$ICON" --out "${ICONSET}/icon_32x32@2x.png" &>/dev/null
  sips -z 128 128 "$ICON" --out "${ICONSET}/icon_128x128.png"  &>/dev/null
  sips -z 256 256 "$ICON" --out "${ICONSET}/icon_128x128@2x.png" &>/dev/null
  sips -z 256 256 "$ICON" --out "${ICONSET}/icon_256x256.png"  &>/dev/null
  sips -z 512 512 "$ICON" --out "${ICONSET}/icon_256x256@2x.png" &>/dev/null
  iconutil -c icns "$ICONSET" -o "$ICNS_PATH" 2>/dev/null || ICNS_PATH=""
fi

# ── Build ─────────────────────────────────────────────────────────────────────
ICON_FLAG=""
[[ -n "${ICNS_PATH:-}" && -f "$ICNS_PATH" ]] && ICON_FLAG="--icon=${ICNS_PATH}"

python -m PyInstaller \
  --name "${APP_NAME}" \
  --windowed \
  --onedir \
  --noconfirm \
  ${ICON_FLAG} \
  --paths "src" \
  --add-data "src/simracing/img:simracing/img" \
  --collect-submodules "Crypto" \
  --hidden-import "pandas" \
  --hidden-import "pyarrow" \
  --hidden-import "pyarrow.vendored.version" \
  --collect-all "pygame" \
  --exclude-module "pyarrow.tests" \
  --exclude-module "pygame.tests" \
  --exclude-module "pygame.examples" \
  --exclude-module "setuptools" \
  --exclude-module "distutils" \
  --distpath "${OUT_DIR}" \
  --workpath "build" \
  "${ENTRY}"

# ── Cleanup temp icon files ───────────────────────────────────────────────────
rm -rf build_tmp

# ── Strip unnecessary data files from bundle ──────────────────────────────────
RSRC="${OUT_DIR}/${APP_NAME}.app/Contents/Resources"
for BLOAT in \
  pyarrow/tests pyarrow/src pyarrow/include pyarrow/includes \
  pygame/tests pygame/examples pygame/docs \
  pandas/tests pandas/io/tests; do
  rm -rf "${RSRC}/${BLOAT}"
done

# ── Summary ───────────────────────────────────────────────────────────────────
APP_PATH="${OUT_DIR}/${APP_NAME}.app"
if [[ -d "$APP_PATH" ]]; then
  SIZE=$(du -sh "$APP_PATH" | cut -f1)
  echo ""
  echo "Build complete: ${APP_PATH}  (${SIZE})"
  echo "Run: open '${APP_PATH}'"
else
  echo "ERROR: .app bundle not found at ${APP_PATH}"
  exit 1
fi
