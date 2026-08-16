#!/usr/bin/env bash
# release.sh — Build and publish a GitHub release for SimRaceEngineer
# Usage: ./release.sh [--skip-build] [--draft] [--notes "message"]
set -euo pipefail

APP_NAME="SimRaceEngineer"
OUT_DIR="dist"
APP_PATH="${OUT_DIR}/${APP_NAME}.app"

# ── Parse args ────────────────────────────────────────────────────────────────
SKIP_BUILD=0
DRAFT_FLAG=""
NOTES=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-build) SKIP_BUILD=1 ;;
    --draft)      DRAFT_FLAG="--draft" ;;
    --notes)      NOTES="$2"; shift ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
  shift
done

# ── Read version from pyproject.toml ─────────────────────────────────────────
VERSION=$(grep '^version' pyproject.toml | head -1 | sed 's/.*= *"\(.*\)"/\1/')
if [[ -z "$VERSION" ]]; then
  echo "ERROR: could not read version from pyproject.toml"
  exit 1
fi
TAG="v${VERSION}"
ZIP_NAME="${APP_NAME}-${TAG}-macos.zip"
ZIP_PATH="${OUT_DIR}/${ZIP_NAME}"

echo "Release: ${TAG}"

# ── Build ─────────────────────────────────────────────────────────────────────
if [[ $SKIP_BUILD -eq 0 ]]; then
  echo "Building..."
  ./build.sh
else
  echo "Skipping build (--skip-build)"
  if [[ ! -d "$APP_PATH" ]]; then
    echo "ERROR: ${APP_PATH} not found. Run without --skip-build first."
    exit 1
  fi
fi

# ── Zip .app bundle ───────────────────────────────────────────────────────────
echo "Zipping ${APP_PATH} → ${ZIP_PATH}..."
rm -f "$ZIP_PATH"
(cd "$OUT_DIR" && zip -r "$ZIP_NAME" "${APP_NAME}.app" -x "*.DS_Store")
SIZE=$(du -sh "$ZIP_PATH" | cut -f1)
echo "Archive: ${ZIP_PATH} (${SIZE})"

# ── Check tag doesn't already exist ──────────────────────────────────────────
if gh release view "$TAG" &>/dev/null; then
  echo "ERROR: release ${TAG} already exists. Bump version in pyproject.toml first."
  exit 1
fi

# ── Release notes ─────────────────────────────────────────────────────────────
if [[ -z "$NOTES" ]]; then
  NOTES="macOS .app bundle — requires macOS 12+ (Apple Silicon and Intel)."
fi

# ── Publish GitHub release ────────────────────────────────────────────────────
echo "Publishing GitHub release ${TAG}..."
gh release create "$TAG" "$ZIP_PATH" \
  --title "${APP_NAME} ${TAG}" \
  --notes "$NOTES" \
  $DRAFT_FLAG

echo ""
echo "Done. Release: https://github.com/wesleyegberto/sim-race-engineer/releases/tag/${TAG}"
