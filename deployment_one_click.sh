#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

STAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
ARTIFACT_DIR="${ROOT_DIR}/.artifacts"
DRIVE_DIR="${FIORELLIA_DRIVE_DIR:-${HOME}/Library/CloudStorage/GoogleDrive-sfn.gns@gmail.com/Il mio Drive/regulatory-insight-engine}"
DIST_ZIP="${ARTIFACT_DIR}/dist-${STAMP}.zip"

mkdir -p "$ARTIFACT_DIR"

echo "==> Checking source tree"
git status --short

echo "==> Building React frontend"
npm run build

echo "==> Creating dist zip"
rm -f "$DIST_ZIP"
(cd "$ROOT_DIR" && zip -qr "$DIST_ZIP" dist)
ls -lh "$DIST_ZIP"

if [[ -d "$DRIVE_DIR" ]]; then
  echo "==> Syncing dist zip to Google Drive project folder"
  mkdir -p "${DRIVE_DIR}/dist"
  cp "$DIST_ZIP" "${DRIVE_DIR}/dist/"

  if compgen -G "${ROOT_DIR}/history_export_*.json" >/dev/null; then
    echo "==> Copying exported history JSON files to Google Drive project folder"
    cp "${ROOT_DIR}"/history_export_*.json "$DRIVE_DIR/"
  fi
else
  echo "==> Google Drive folder not found: $DRIVE_DIR"
  echo "    Dist zip kept at: $DIST_ZIP"
fi

echo "==> Running Fiorell.IA app smoke test"
python3 fiorellia_app.py --smoke-test

echo "==> Done"
