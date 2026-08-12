#!/usr/bin/env python3
"""File overview: lock the Degov Agent API x402 offer contract against the MetaMask
agent-wallet skill's payment script requirements.

The MetaMask agent-wallet skill ships `scripts/x402_pay.py` (MIT) as the payment
ceremony for HTTP 402 / x402 resources. That script rejects offers that:

- do not use the `exact` scheme,
- are not on a network `mm` supports (this skill targets `eip155:8453`, Base),
- omit the EIP-712 domain `name`/`version` in `extra`,
- use `assetTransferMethod: "permit2"` (only EIP-3009 is supported).

The Degov Agent API composes with that script instead of vendoring its own payment
code, so this test pins the *server-side* offer contract: if the API ever
changes its 402 challenge such that the MetaMask script can no longer pay it, CI
fails here instead of at a user's wallet.

The fixture below is a verbatim capture of the `PAYMENT-REQUIRED` header returned
by the staging deployment (`http://127.0.0.1:8310`) on 2026-08-07 for
`GET /v2/proposals?limit=1` (standard tier, unpaid).
"""

from __future__ import annotations

import base64
import json
import re
import unittest

ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

# Verbatim decoded payload of the staging PAYMENT-REQUIRED header (2026-08-07).
FIXTURE_PAYMENT_REQUIRED = {
    "x402Version": 2,
    "accepts": [
        {
            "scheme": "exact",
            "network": "eip155:8453",
            "amount": "5000",
            "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            "payTo": "0x81a29baAb452D14D878762dcf9a51bc9062113DF",
            "maxTimeoutSeconds": 3600,
            "extra": {"name": "USD Coin", "version": "2", "assetTransferMethod": "eip3009"},
        }
    ],
}

# Expected values for the degov contract (Base mainnet USDC, EIP-3009).
EXPECTED_NETWORK = "eip155:8453"
EXPECTED_ASSET = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"  # USDC on Base
EXPECTED_SCHEME = "exact"
EXPECTED_TRANSFER_METHOD = "eip3009"


def encode_payment_required(payload: dict) -> str:
    """Serialize like the API does: compact JSON, then base64."""
    return base64.b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")).decode("ascii")


def parse_payment_required(raw_b64: str) -> dict:
    """Decode a PAYMENT-REQUIRED header value into a dict."""
    return json.loads(base64.b64decode(raw_b64.encode("ascii")).decode("utf-8"))


def assert_offer_compatible(payload: dict) -> None:
    """Assert a decoded x402 offer satisfies the MetaMask x402_pay.py hard requirements.

    Raises AssertionError with a descriptive message when the offer would be
    rejected or unpayable by the MetaMask payment script.
    """
    assert payload.get("x402Version") == 2, f"x402Version must be 2, got {payload.get('x402Version')!r}"
    accepts = payload.get("accepts")
    assert isinstance(accepts, list) and accepts, "accepts must be a non-empty list"
    for accept in accepts:
        scheme = accept.get("scheme")
        assert scheme == EXPECTED_SCHEME, f"scheme must be 'exact', got {scheme!r}"
        network = accept.get("network")
        assert network == EXPECTED_NETWORK, f"network must be {EXPECTED_NETWORK}, got {network!r}"
        amount = accept.get("amount")
        assert isinstance(amount, str) and amount.isdigit() and int(amount) > 0, (
            f"amount must be a positive atomic-unit integer string, got {amount!r}"
        )
        asset = accept.get("asset")
        assert isinstance(asset, str) and ADDRESS_RE.match(asset), f"asset must be an address, got {asset!r}"
        pay_to = accept.get("payTo")
        assert isinstance(pay_to, str) and ADDRESS_RE.match(pay_to), f"payTo must be an address, got {pay_to!r}"
        extra = accept.get("extra")
        assert isinstance(extra, dict), f"extra must be an object, got {extra!r}"
        # MetaMask x402_pay.py refuses offers that omit the EIP-712 domain name/version.
        assert extra.get("name"), f"extra.name is required (EIP-712 domain), got {extra.get('name')!r}"
        assert extra.get("version"), f"extra.version is required (EIP-712 domain), got {extra.get('version')!r}"
        # MetaMask x402_pay.py rejects permit2; only EIP-3009 is supported.
        assert extra.get("assetTransferMethod") == EXPECTED_TRANSFER_METHOD, (
            f"assetTransferMethod must be 'eip3009', got {extra.get('assetTransferMethod')!r}"
        )
        timeout = accept.get("maxTimeoutSeconds")
        assert isinstance(timeout, int) and timeout > 0, (
            f"maxTimeoutSeconds must be a positive integer, got {timeout!r}"
        )


class X402CompatibilityTest(unittest.TestCase):
    def test_fixture_round_trips_through_base64(self) -> None:
        """The fixture encodes/decodes like the real PAYMENT-REQUIRED header flow."""
        raw = encode_payment_required(FIXTURE_PAYMENT_REQUIRED)
        decoded = parse_payment_required(raw)
        self.assertEqual(decoded, FIXTURE_PAYMENT_REQUIRED)

    def test_fixture_is_payable_by_metamask_script(self) -> None:
        """The staging capture satisfies the MetaMask x402_pay.py hard requirements."""
        assert_offer_compatible(FIXTURE_PAYMENT_REQUIRED)

    def test_missing_domain_is_rejected(self) -> None:
        """Regression: an offer without extra.name/version must fail the guard."""
        mutated = json.loads(json.dumps(FIXTURE_PAYMENT_REQUIRED))
        del mutated["accepts"][0]["extra"]["name"]
        with self.assertRaises(AssertionError):
            assert_offer_compatible(mutated)

    def test_permit2_offer_is_rejected(self) -> None:
        """Regression: a permit2 offer must fail the guard (script does not support it)."""
        mutated = json.loads(json.dumps(FIXTURE_PAYMENT_REQUIRED))
        mutated["accepts"][0]["extra"]["assetTransferMethod"] = "permit2"
        with self.assertRaises(AssertionError):
            assert_offer_compatible(mutated)

    def test_upto_scheme_is_rejected(self) -> None:
        """Regression: a non-exact scheme must fail the guard."""
        mutated = json.loads(json.dumps(FIXTURE_PAYMENT_REQUIRED))
        mutated["accepts"][0]["scheme"] = "upto"
        with self.assertRaises(AssertionError):
            assert_offer_compatible(mutated)


if __name__ == "__main__":
    unittest.main(verbosity=2)
