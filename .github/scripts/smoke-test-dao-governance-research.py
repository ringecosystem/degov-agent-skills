#!/usr/bin/env python3
"""File overview: run deterministic and optional live smoke tests for dao-governance-research.

This script intentionally uses only the Python standard library so it can run in
CI and local environments without installing anything. By default it runs local
deterministic checks; live free-API and paid-402 (zero-cost) checks are explicit
opt-ins.

The skill no longer ships a CLI or local wallet: it documents the Degov Agent API
v2 surface and composes with the MetaMask agent-wallet skill for x402 payments.
The offline checks therefore validate the skill document contract (frontmatter,
references, workflows, no stale TypeScript project) and the x402 offer
compatibility fixture (test_x402_compat).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import NoReturn

USAGE = """Usage: python3 .github/scripts/smoke-test-dao-governance-research.py [--offline] [--free-api] [--paid]

Default/--offline:
  Run deterministic local checks only: skill frontmatter, references/workflows
  presence, no stale TypeScript project, security-skill validator, x402
  compatibility fixture test, and py_compile of every test script.

--free-api:
  Also call free API endpoints: health, v2 meta/data-status, v2 daos, v2 daos/:daoId.
  Uses DEGOV_AGENT_API_BASE_URL when set, otherwise https://agent-api.degov.ai.

--paid:
  Also hit one paid endpoint WITHOUT payment and assert the returned 402
  PAYMENT-REQUIRED offer still satisfies the MetaMask x402_pay.py requirements
  (zero cost - an unpaid 402 never settles). Requires --free-api to have
  validated connectivity first.
"""

ROOT = Path(__file__).resolve().parents[2]
TESTS_DIR = ROOT / ".github" / "scripts"
RESEARCH_SKILL_PATH = ROOT / "skills" / "dao-governance-research" / "SKILL.md"
REFERENCES_DIR = ROOT / "skills" / "dao-governance-research" / "references"
WORKFLOWS_DIR = ROOT / "skills" / "dao-governance-research" / "workflows"
SKILL_SCRIPTS_DIR = ROOT / "skills" / "dao-governance-research" / "scripts"
OUTPUT_DIR = Path(os.environ.get("TMPDIR", "/tmp")) / "degov-agent-skills-smoke"

API_BASE_URL = os.environ.get("DEGOV_AGENT_API_BASE_URL", "https://agent-api.degov.ai")

REQUIRED_REFERENCES = [
    "api-v2.md",
    "pricing.md",
    "errors.md",
    "x402.md",
    "payment.md",
]
REQUIRED_WORKFLOWS = [
    "discovery.md",
    "recent-activity.md",
    "explain-proposal.md",
    "proposal-security.md",
    "evidence.md",
    "payment-setup.md",
    "troubleshooting.md",
]

# Imported from the fixture test so the live --paid check and the offline fixture
# share exactly one compatibility gate.
sys.path.insert(0, str(TESTS_DIR))
from test_x402_compat import (  # noqa: E402
    assert_offer_compatible,
    parse_payment_required,
)


def fail(message: str) -> NoReturn:
    raise AssertionError(message)


def run(command: list[str], *, cwd: Path | None = None) -> None:
    print(f"$ {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def validate_research_skill() -> None:
    content = RESEARCH_SKILL_PATH.read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        fail(f"{RESEARCH_SKILL_PATH}: missing frontmatter start")
    try:
        _, frontmatter, body = content.split("---\n", 2)
    except ValueError as exc:
        fail(f"{RESEARCH_SKILL_PATH}: malformed frontmatter")
    fields = {}
    for line in frontmatter.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"')
    if fields.get("name") != "dao-governance-research":
        fail(f"{RESEARCH_SKILL_PATH}: expected name dao-governance-research, found {fields.get('name')!r}")
    if not fields.get("description"):
        fail(f"{RESEARCH_SKILL_PATH}: missing description")
    if fields.get("version") != "1.0.0":
        fail(f"{RESEARCH_SKILL_PATH}: expected version 1.0.0, found {fields.get('version')!r}")
    if not body.strip():
        fail(f"{RESEARCH_SKILL_PATH}: missing body")

    skill_text = content
    for reference in REQUIRED_REFERENCES:
        path = REFERENCES_DIR / reference
        if not path.is_file() or path.stat().st_size == 0:
            fail(f"{path}: required reference is missing or empty")
        if reference not in skill_text:
            fail(f"{RESEARCH_SKILL_PATH}: does not reference {reference}")
    for workflow in REQUIRED_WORKFLOWS:
        path = WORKFLOWS_DIR / workflow
        if not path.is_file() or path.stat().st_size == 0:
            fail(f"{path}: required workflow is missing or empty")
        if workflow not in skill_text:
            fail(f"{RESEARCH_SKILL_PATH}: does not reference {workflow}")

    # The TypeScript CLI project must be gone: no package.json, no .ts files.
    if (SKILL_SCRIPTS_DIR / "package.json").exists():
        fail(f"{SKILL_SCRIPTS_DIR / 'package.json'}: stale TypeScript project must be removed")
    stale_ts = sorted(SKILL_SCRIPTS_DIR.rglob("*.ts")) if SKILL_SCRIPTS_DIR.exists() else []
    if stale_ts:
        fail(f"stale TypeScript files must be removed: {[str(p.relative_to(ROOT)) for p in stale_ts]}")


def run_local_checks() -> None:
    print("== Local checks ==", flush=True)
    validate_research_skill()
    run(["python3", str(TESTS_DIR / "validate-dao-governance-security.py")], cwd=ROOT)
    run(["python3", str(TESTS_DIR / "test_x402_compat.py")], cwd=ROOT)
    for path in sorted(TESTS_DIR.glob("*.py")):
        run(["python3", "-m", "py_compile", str(path)], cwd=ROOT)


def http_get_json(url: str) -> tuple[int, dict | None, dict[str, str]]:
    """GET a URL and return (status, json, headers)."""
    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            status = response.status
            headers = dict(response.headers.items())
            body = response.read().decode("utf-8")
            return status, json.loads(body), headers
    except urllib.error.HTTPError as exc:
        headers = dict(exc.headers.items())
        body = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = None
        return exc.code, payload, headers


def run_free_api_checks() -> None:
    print("== Free API checks ==", flush=True)
    print(f"API base: {API_BASE_URL}", flush=True)

    status, payload, _ = http_get_json(f"{API_BASE_URL}/health")
    if status != 200 or not (payload or {}).get("ok"):
        fail(f"/health failed: status={status} payload={payload}")

    status, payload, _ = http_get_json(f"{API_BASE_URL}/v2/meta/data-status")
    if status != 200:
        fail(f"/v2/meta/data-status failed: status={status} payload={payload}")
    counts = (payload or {}).get("data", {}).get("counts")
    if not counts or counts.get("daos", 0) <= 0:
        fail(f"/v2/meta/data-status: expected global dao counts, got {payload}")

    status, payload, _ = http_get_json(f"{API_BASE_URL}/v2/meta/pricing")
    if status != 200:
        fail(f"/v2/meta/pricing failed: status={status} payload={payload}")
    routes = (payload or {}).get("data", {}).get("routes")
    if not routes:
        fail(f"/v2/meta/pricing: expected a route table, got {payload}")

    status, payload, _ = http_get_json(f"{API_BASE_URL}/v2/daos?limit=5")
    if status != 200:
        fail(f"/v2/daos failed: status={status} payload={payload}")
    items = (payload or {}).get("data", {}).get("items")
    if not items:
        fail(f"/v2/daos: expected items, got {payload}")
    dao_id = items[0].get("daoId")
    if not dao_id:
        fail(f"/v2/daos: item missing daoId: {items[0]}")

    status, payload, _ = http_get_json(f"{API_BASE_URL}/v2/daos/{dao_id}")
    if status != 200:
        fail(f"/v2/daos/{dao_id} failed: status={status} payload={payload}")
    if (payload or {}).get("data", {}).get("daoId") != dao_id:
        fail(f"/v2/daos/{dao_id}: unexpected payload {payload}")

    print(f"free API checks ok (dao sample: {dao_id})", flush=True)


def run_paid_offer_checks() -> None:
    print("== Paid-offer (zero-cost) checks ==", flush=True)
    # events requires from/to; an unpaid request must 402 without settling anything.
    url = f"{API_BASE_URL}/v2/events?from=2026-08-01T00:00:00Z&to=2026-08-07T00:00:00Z&limit=1"
    status, payload, headers = http_get_json(url)
    if status != 402:
        fail(f"expected 402 for unpaid paid endpoint, got status={status} payload={payload}")

    raw = headers.get("payment-required") or headers.get("PAYMENT-REQUIRED")
    if not raw:
        fail(f"402 response missing PAYMENT-REQUIRED header: {sorted(headers)}")
    offer = parse_payment_required(raw)
    assert_offer_compatible(offer)
    print("live 402 offer is payable by the MetaMask x402_pay.py requirements (zero cost)", flush=True)

    # Key-param routes must reach the payment gate (402), not 414. v2 proposalKey
    # values are ~190 chars; an old deployment with the default Fastify
    # maxParamLength (100) rejects them with 414 before payment is even offered.
    # A fake ~190-char key is enough to exercise the route: unpaid it must 402
    # (route matched, payment gate reached) and never settle anything.
    fake_key = "v2:test-dao:snapshot:" + "a" * 170
    url = f"{API_BASE_URL}/v2/proposals/{fake_key}"
    status, payload, headers = http_get_json(url)
    if status == 414:
        fail(
            f"key-param route still 414 (maxParamLength fix missing): {url}\n"
            "degov-agent-api raised maxParamLength so ~190-char v2 keys stay routable; "
            "deploy that fix (PR #292) before running this check."
        )
    if status != 402:
        fail(f"expected 402 for unpaid key-param route, got status={status} payload={payload}")
    print("key-param route accepts ~190-char keys and reaches the payment gate (414 fix verified, zero cost)", flush=True)


def parse_args(argv: list[str]) -> tuple[bool, bool]:
    run_free_api = False
    run_paid = False
    for arg in argv:
        if arg == "--offline":
            continue
        if arg == "--free-api":
            run_free_api = True
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
    if run_paid and not run_free_api:
        print("--paid implies --free-api (connectivity is verified first).", file=sys.stderr)
        raise SystemExit(2)
    return run_free_api, run_paid


def main(argv: list[str]) -> int:
    run_free_api, run_paid = parse_args(argv)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    run_local_checks()
    if run_free_api:
        run_free_api_checks()
    if run_paid:
        run_paid_offer_checks()

    print(f"Smoke test completed. Outputs: {OUTPUT_DIR}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
