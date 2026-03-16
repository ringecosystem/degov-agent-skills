#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

pnpm install
chmod +x degov-client.js

echo "Installed dao-governance scripts."
echo "Next: node degov-client.js wallet init"
