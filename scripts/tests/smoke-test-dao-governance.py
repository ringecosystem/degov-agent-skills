#!/usr/bin/env python3
"""File overview: run deterministic and optional live smoke tests for dao-governance.

This script intentionally uses only the Python standard library so it can run in
CI and local environments before the TypeScript helper dependencies are known to
be installed. By default it runs local deterministic checks; live free API,
wallet, and paid endpoint checks are explicit opt-ins.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

USAGE = """Usage: python3 scripts/tests/smoke-test-dao-governance.py [--offline] [--free-api] [--wallet] [--paid]

Default/--offline:
  Run deterministic local checks only: security skill validation, pnpm install,
  format, typecheck, tests, CLI help.

--free-api:
  Also call free production API endpoints: health, budget, daos.

--wallet:
  Also test wallet init/address/balance using isolated /tmp state.

--paid:
  Also call paid endpoints. Requires a funded wallet. Uses normal wallet env and
  cannot be combined with --wallet.
"""

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "skills" / "dao-governance" / "scripts"
OUTPUT_DIR = Path(os.environ.get("TMPDIR", "/tmp")) / "degov-agent-skills-smoke"


def parse_args(argv: list[str]) -> tuple[bool, bool, bool]:
    run_free_api = False
    run_wallet = False
    run_paid = False

    for arg in argv:
        if arg == "--offline":
            continue
        if arg == "--free-api":
            run_free_api = True
            continue
        if arg == "--wallet":
            run_wallet = True
            continue
        if arg == "--paid":
            run_paid = True
            continue
        if arg in {"--help", "-h"}:
            print(USAGE, end="")
            raise SystemExit(0)

        print(f"Unknown option: {arg}", file=sys.stderr)
        print(USAGE, end="", file=sys.stderr)
        raise SystemExit(2)

    if run_wallet and run_paid:
        print(
            "--wallet and --paid cannot be combined because --wallet intentionally uses an unfunded isolated test wallet.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    return run_free_api, run_wallet, run_paid


def run(command: list[str], *, cwd: Path = SCRIPTS_DIR, env: dict[str, str] | None = None) -> None:
    print(f"$ {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=cwd, env=env, check=True)


def run_to_file(
    command: list[str],
    output_path: Path,
    *,
    env: dict[str, str] | None = None,
) -> None:
    print(f"$ {' '.join(command)} > {output_path}", flush=True)
    with output_path.open("w", encoding="utf-8") as output_file:
        subprocess.run(
            command,
            cwd=SCRIPTS_DIR,
            env=env,
            check=True,
            stdout=output_file,
        )


def ensure_non_empty(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise AssertionError(f"Expected non-empty file: {path}")


def run_local_checks() -> None:
    print("== Local checks ==", flush=True)
    run(["python3", "scripts/tests/validate-dao-governance-security.py"], cwd=ROOT)
    run(["pnpm", "--dir", "skills/dao-governance/scripts", "install", "--frozen-lockfile"], cwd=ROOT)
    run(["pnpm", "run", "format:check"], cwd=ROOT)
    run(["pnpm", "--dir", "skills/dao-governance/scripts", "run", "check"], cwd=ROOT)

    help_output = OUTPUT_DIR / "help.txt"
    run_to_file(["pnpm", "exec", "tsx", "degov-client.ts", "help"], help_output)
    print(f"help output: {help_output}", flush=True)


def run_free_api_checks() -> None:
    print("== Free API checks ==", flush=True)
    daos_output = OUTPUT_DIR / "daos.json"
    run_to_file(["pnpm", "exec", "tsx", "degov-client.ts", "health"], OUTPUT_DIR / "health.json")
    run_to_file(["pnpm", "exec", "tsx", "degov-client.ts", "budget", "--usd", "1"], OUTPUT_DIR / "budget.txt")
    run_to_file(["pnpm", "exec", "tsx", "degov-client.ts", "daos"], daos_output)

    with daos_output.open("r", encoding="utf-8") as daos_file:
        payload = json.load(daos_file)
    items = payload.get("data", {}).get("items", [])
    if not items:
        raise AssertionError("DAO discovery returned no items")
    print(f"DAO discovery items: {len(items)}", flush=True)


def run_wallet_checks() -> None:
    print("== Isolated wallet checks ==", flush=True)
    wallet_dir = Path(os.environ.get("TMPDIR", "/tmp")) / "degov-agent-skills-wallet-smoke"
    shutil.rmtree(wallet_dir, ignore_errors=True)
    wallet_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    # Keep the isolated wallet check independent from any user/session wallet
    # passphrase override so it also verifies passphrase-file creation.
    env.pop("DEGOV_AGENT_WALLET_PASSPHRASE", None)
    env["DEGOV_AGENT_WALLET_PATH"] = str(wallet_dir / "wallet.json")
    env["DEGOV_AGENT_WALLET_PASSPHRASE_PATH"] = str(wallet_dir / "wallet-passphrase")

    run_to_file(["pnpm", "exec", "tsx", "degov-client.ts", "wallet", "init"], OUTPUT_DIR / "wallet-init.txt", env=env)
    run_to_file(["pnpm", "exec", "tsx", "degov-client.ts", "wallet", "address"], OUTPUT_DIR / "wallet-address.txt", env=env)
    run_to_file(["pnpm", "exec", "tsx", "degov-client.ts", "wallet", "balance"], OUTPUT_DIR / "wallet-balance.txt", env=env)
    ensure_non_empty(Path(env["DEGOV_AGENT_WALLET_PATH"]))
    ensure_non_empty(Path(env["DEGOV_AGENT_WALLET_PASSPHRASE_PATH"]))
    print(f"isolated wallet path: {env['DEGOV_AGENT_WALLET_PATH']}", flush=True)


def run_paid_checks() -> None:
    print("== Paid API checks ==", flush=True)
    run_to_file(["pnpm", "exec", "tsx", "degov-client.ts", "freshness"], OUTPUT_DIR / "freshness.json")
    run_to_file(
        ["pnpm", "exec", "tsx", "degov-client.ts", "activity", "--hours", "24", "--limit", "10"],
        OUTPUT_DIR / "activity.json",
    )
    run_to_file(
        ["pnpm", "exec", "tsx", "degov-client.ts", "governance-events", "--hours", "24", "--limit", "20"],
        OUTPUT_DIR / "governance-events.json",
    )
    run_to_file(
        ["pnpm", "exec", "tsx", "degov-client.ts", "brief", "ens", "--activity-limit", "3"],
        OUTPUT_DIR / "brief-ens.json",
    )


def main(argv: list[str]) -> int:
    run_free_api, run_wallet, run_paid = parse_args(argv)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    run_local_checks()
    if run_free_api:
        run_free_api_checks()
    if run_wallet:
        run_wallet_checks()
    if run_paid:
        run_paid_checks()

    print(f"Smoke test completed. Outputs: {OUTPUT_DIR}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
