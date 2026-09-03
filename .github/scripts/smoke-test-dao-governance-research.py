#!/usr/bin/env python3
"""File overview: run deterministic and optional live smoke tests for dao-governance-research.

This script intentionally uses only the Python standard library so it can run in
CI and local environments without installing anything. By default it runs local
deterministic checks; live free-API and paid-402 (zero-cost) checks are explicit
opt-ins.

The skill no longer ships a CLI or local wallet: it documents the current Degov
Agent API contract and delegates x402 authorization and signing to the MetaMask
agent-wallet skill. The offline checks validate the compact skill document
contract, the absence of stale workflow/TypeScript structure, and the x402 offer
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
  Run deterministic local checks only: skill frontmatter and references,
  no stale routes, workflow, or TypeScript project, security-skill validator,
  x402 compatibility fixture test, and py_compile of every test script.

--free-api:
  Also validate the public OpenAPI route set, DAO list, and DAO detail.
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
    "api.md",
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
    current_key = None
    for line in frontmatter.splitlines():
        if not line.strip():
            continue
        if line.startswith(" ") or line.startswith("\t"):
            # prettier wraps long frontmatter values (e.g. description) as YAML
            # block scalars; fold continuation lines back into the current key.
            stripped = line.strip()
            if ":" in stripped:
                key, value = stripped.split(":", 1)
                fields[key.strip()] = value.strip().strip('"')
            elif current_key is not None:
                fields[current_key] = (fields.get(current_key, "") + " " + stripped).strip()
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        current_key = key.strip()
        fields[current_key] = value.strip().strip('"')
    if fields.get("name") != "dao-governance-research":
        fail(f"{RESEARCH_SKILL_PATH}: expected name dao-governance-research, found {fields.get('name')!r}")
    if not fields.get("description"):
        fail(f"{RESEARCH_SKILL_PATH}: missing description")
    if fields.get("version") != "1.0.0":
        fail(f"{RESEARCH_SKILL_PATH}: expected version 1.0.0, found {fields.get('version')!r}")
    if not body.strip():
        fail(f"{RESEARCH_SKILL_PATH}: missing body")

    # Keep payment authorization in the wallet capability and keep API migration
    # history out of the user-facing skill contract.
    forbidden_skill_phrases = (
        "paid-call consent",
        "query plan",
        "approved plan",
        "production v1",
        "v1 → v2",
    )
    for phrase in forbidden_skill_phrases:
        if phrase.lower() in content.lower():
            fail(f"{RESEARCH_SKILL_PATH}: stale workflow or migration wording {phrase!r}")

    skill_text = content
    for reference in REQUIRED_REFERENCES:
        path = REFERENCES_DIR / reference
        if not path.is_file() or path.stat().st_size == 0:
            fail(f"{path}: required reference is missing or empty")
        if reference not in skill_text:
            fail(f"{RESEARCH_SKILL_PATH}: does not reference {reference}")

    api_reference = (REFERENCES_DIR / "api.md").read_text(encoding="utf-8")
    if "/v1/" in api_reference.lower() or "v1 → v2" in api_reference.lower():
        fail(f"{REFERENCES_DIR / 'api.md'}: removed route or migration history remains in the current contract")
    if "v2:ens-dao:snapshot:" in api_reference or "v2:uniswap:forum:" in api_reference:
        fail(f"{REFERENCES_DIR / 'api.md'}: key examples must remain opaque")
    removed_contract_terms = (
        "/v2/meta/data-status",
        "/v2/meta/pricing",
        "/v2/events",
        "/v2/signals",
        "/timeline",
        "/evidence",
        "/votes/summary",
        "/daos/:daoId/voters",
        "proposalKey",
        "topicKey",
        "voterIdentity",
        '"readiness":',
        '"coverageStatus":',
    )
    combined_research_docs = content + "\n" + api_reference + "\n" + (
        REFERENCES_DIR / "troubleshooting.md"
    ).read_text(encoding="utf-8")
    for stale_term in removed_contract_terms:
        if stale_term in combined_research_docs:
            fail(f"research skill still references removed contract term {stale_term!r}")

    required_contract_terms = (
        "/v2/daos/{daoId}/participants",
        "/v2/proposals/{proposalId}/vote-summary",
        "/v2/proposals/{proposalId}/votes",
        "/v2/forum-topics",
        "/v2/voters/{voterId}/votes",
        "proposalId",
        "topicId",
        "voterId",
        "rawChoice",
        "knownVotingPower",
    )
    for required_term in required_contract_terms:
        if required_term not in api_reference:
            fail(f"{REFERENCES_DIR / 'api.md'}: missing current contract term {required_term!r}")

    stale_workflows = sorted(WORKFLOWS_DIR.glob("*.md")) if WORKFLOWS_DIR.exists() else []
    if stale_workflows:
        fail(f"redundant workflow files must be removed: {[str(p.relative_to(ROOT)) for p in stale_workflows]}")

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
    # Production may reject urllib's default Python-urllib user agent. Use an
    # explicit, stable identifier so the live smoke exercises the public API in
    # the same way as curl and normal HTTP clients.
    request = urllib.request.Request(url, headers={"User-Agent": "degov-agent-skills-smoke/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
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

    status, payload, _ = http_get_json(f"{API_BASE_URL}/openapi.json")
    if status != 200:
        fail(f"/openapi.json failed: status={status} payload={payload}")
    expected_paths = {
        "/v2/daos",
        "/v2/daos/{daoId}",
        "/v2/daos/{daoId}/participants",
        "/v2/proposals",
        "/v2/proposals/resolve",
        "/v2/proposals/{proposalId}",
        "/v2/proposals/{proposalId}/vote-summary",
        "/v2/proposals/{proposalId}/votes",
        "/v2/forum-topics",
        "/v2/voters/{voterId}",
        "/v2/voters/{voterId}/votes",
    }
    actual_paths = set((payload or {}).get("paths", {}))
    if actual_paths != expected_paths:
        fail(f"unexpected public OpenAPI route set: expected={sorted(expected_paths)} actual={sorted(actual_paths)}")

    status, payload, _ = http_get_json(f"{API_BASE_URL}/v2/daos?limit=5")
    if status != 200:
        fail(f"/v2/daos failed: status={status} payload={payload}")
    items = (payload or {}).get("data")
    page = (payload or {}).get("page")
    if not isinstance(items, list) or not items or not isinstance(page, dict):
        fail(f"/v2/daos: expected data array and page object, got {payload}")
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
    # Proposal list is paid; an unpaid request must 402 without settling anything.
    url = f"{API_BASE_URL}/v2/proposals?limit=1"
    status, payload, headers = http_get_json(url)
    if status != 402:
        fail(f"expected 402 for unpaid paid endpoint, got status={status} payload={payload}")

    raw = headers.get("payment-required") or headers.get("PAYMENT-REQUIRED")
    if not raw:
        fail(f"402 response missing PAYMENT-REQUIRED header: {sorted(headers)}")
    offer = parse_payment_required(raw)
    assert_offer_compatible(offer)
    print("live 402 offer is payable by the MetaMask x402_pay.py requirements (zero cost)", flush=True)

    # Key-param routes must reach the payment gate (402), not 414. proposalId
    # values are ~190 chars; an old deployment with the default Fastify
    # maxParamLength (100) rejects them with 414 before payment is even offered.
    # A fake ~190-char key is enough to exercise the route: unpaid it must 402
    # (route matched, payment gate reached) and never settle anything.
    fake_key = "p1_" + "a" * 187
    url = f"{API_BASE_URL}/v2/proposals/{fake_key}"
    status, payload, headers = http_get_json(url)
    if status == 414:
        fail(
            f"key-param route still 414 (maxParamLength fix missing): {url}\n"
            "degov-agent-api raised maxParamLength so ~190-char keys stay routable; "
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
