#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/smoke-test-dao-governance.sh [--offline] [--free-api] [--wallet] [--paid]

Default/--offline:
  Run deterministic local checks only: pnpm install, format, typecheck, CLI help.

--free-api:
  Also call free production API endpoints: health, budget, daos.

--wallet:
  Also test wallet init/address/balance using isolated /tmp state.

--paid:
  Also call paid endpoints. Requires a funded wallet. Uses normal wallet env and
  cannot be combined with --wallet.
EOF
}

run_free_api=false
run_wallet=false
run_paid=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --offline)
      ;;
    --free-api)
      run_free_api=true
      ;;
    --wallet)
      run_wallet=true
      ;;
    --paid)
      run_paid=true
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if [[ "$run_wallet" == true && "$run_paid" == true ]]; then
  echo "--wallet and --paid cannot be combined because --wallet intentionally uses an unfunded isolated test wallet." >&2
  exit 2
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
scripts_dir="${repo_root}/skills/dao-governance/scripts"
output_dir="${TMPDIR:-/tmp}/degov-agent-skills-smoke"
mkdir -p "$output_dir"

cd "$scripts_dir"

echo "== Local checks =="
pnpm install --frozen-lockfile
pnpm run format:check
pnpm run typecheck
pnpm exec tsx degov-client.ts help >"${output_dir}/help.txt"
echo "help output: ${output_dir}/help.txt"

if [[ "$run_free_api" == true ]]; then
  echo "== Free API checks =="
  pnpm exec tsx degov-client.ts health >"${output_dir}/health.json"
  pnpm exec tsx degov-client.ts budget --usd 1 >"${output_dir}/budget.txt"
  pnpm exec tsx degov-client.ts daos >"${output_dir}/daos.json"
  python3 - "${output_dir}/daos.json" <<'PY'
import json, sys
with open(sys.argv[1], 'r', encoding='utf-8') as fh:
    payload = json.load(fh)
items = payload.get('data', {}).get('items', [])
if not items:
    raise SystemExit('DAO discovery returned no items')
print(f"DAO discovery items: {len(items)}")
PY
fi

if [[ "$run_wallet" == true ]]; then
  echo "== Isolated wallet checks =="
  wallet_dir="${TMPDIR:-/tmp}/degov-agent-skills-wallet-smoke"
  rm -rf "$wallet_dir"
  mkdir -p "$wallet_dir"
  export DEGOV_AGENT_WALLET_PATH="${wallet_dir}/wallet.json"
  export DEGOV_AGENT_WALLET_PASSPHRASE_PATH="${wallet_dir}/wallet-passphrase"
  pnpm exec tsx degov-client.ts wallet init >"${output_dir}/wallet-init.txt"
  pnpm exec tsx degov-client.ts wallet address >"${output_dir}/wallet-address.txt"
  pnpm exec tsx degov-client.ts wallet balance >"${output_dir}/wallet-balance.txt"
  test -s "$DEGOV_AGENT_WALLET_PATH"
  test -s "$DEGOV_AGENT_WALLET_PASSPHRASE_PATH"
  echo "isolated wallet path: ${DEGOV_AGENT_WALLET_PATH}"
fi

if [[ "$run_paid" == true ]]; then
  echo "== Paid API checks =="
  pnpm exec tsx degov-client.ts freshness >"${output_dir}/freshness.json"
  pnpm exec tsx degov-client.ts activity --hours 24 --limit 10 >"${output_dir}/activity.json"
  pnpm exec tsx degov-client.ts governance-events --hours 24 --limit 20 >"${output_dir}/governance-events.json"
  pnpm exec tsx degov-client.ts brief ens --activity-limit 3 >"${output_dir}/brief-ens.json"
fi

echo "Smoke test completed. Outputs: ${output_dir}"
