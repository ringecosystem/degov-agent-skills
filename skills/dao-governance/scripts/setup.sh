#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

pnpm install
chmod +x degov-client.ts

echo "Installed dao-governance scripts."
echo "Next: export DEGOV_AGENT_WALLET_PASSPHRASE=\"choose-a-strong-passphrase\""
echo "Then: pnpm exec tsx degov-client.ts wallet init"
