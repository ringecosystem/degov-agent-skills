#!/usr/bin/env python3
"""File overview: regression-test the public API method and pagination smoke checks."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


spec = importlib.util.spec_from_file_location(
    "research_smoke", Path(__file__).with_name("smoke-test-dao-governance-research.py")
)
assert spec is not None and spec.loader is not None
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


def public_openapi() -> dict:
    paths = {
        path: {"get": {}}
        for path in (
            "/v2/daos",
            "/v2/daos/{daoId}",
            "/v2/daos/{daoId}/participants",
            "/v2/proposals",
            "/v2/proposals/{proposalId}",
            "/v2/proposals/{proposalId}/vote-summary",
            "/v2/proposals/{proposalId}/votes",
            "/v2/forum-topics",
            "/v2/voters/{voterId}",
            "/v2/voters/{voterId}/votes",
        )
    }
    paths["/v2/proposals/resolve"] = {"post": {}}
    for path in ("/v2/daos", "/v2/proposals", "/v2/forum-topics"):
        paths[path]["get"]["parameters"] = [{"name": "query", "in": "query"}]
    return {"paths": paths}


class PublicOpenApiTest(unittest.TestCase):
    def test_accepts_current_operations_with_path_metadata(self) -> None:
        payload = public_openapi()
        payload["paths"]["/v2/proposals/resolve"]["summary"] = "Exact proposal lookup"
        smoke.validate_public_openapi(payload)

    def test_rejects_get_resolver_even_when_paths_match(self) -> None:
        payload = public_openapi()
        payload["paths"]["/v2/proposals/resolve"] = {"get": {}}
        with self.assertRaisesRegex(AssertionError, "expected only POST"):
            smoke.validate_public_openapi(payload)

    def test_rejects_extra_resolver_method(self) -> None:
        payload = public_openapi()
        payload["paths"]["/v2/proposals/resolve"]["get"] = {}
        with self.assertRaisesRegex(AssertionError, "expected only POST"):
            smoke.validate_public_openapi(payload)

    def test_rejects_missing_or_malformed_operation(self) -> None:
        for path_item in ({}, {"post": None}, None):
            with self.subTest(path_item=path_item):
                payload = public_openapi()
                payload["paths"]["/v2/proposals/resolve"] = path_item
                with self.assertRaises(AssertionError):
                    smoke.validate_public_openapi(payload)

    def test_rejects_missing_or_extra_path(self) -> None:
        missing = public_openapi()
        del missing["paths"]["/v2/proposals/resolve"]
        extra = public_openapi()
        extra["paths"]["/v2/removed-resource"] = {"get": {}}
        for payload in (missing, extra):
            with self.subTest(paths=sorted(payload["paths"])):
                with self.assertRaisesRegex(AssertionError, "route set"):
                    smoke.validate_public_openapi(payload)

    def test_rejects_missing_search_parameter(self) -> None:
        payload = public_openapi()
        payload["paths"]["/v2/proposals"]["get"]["parameters"] = []
        with self.assertRaisesRegex(AssertionError, "missing query parameter"):
            smoke.validate_public_openapi(payload)


class CollectionPageTest(unittest.TestCase):
    def test_accepts_next_and_terminal_pages(self) -> None:
        for page in (
            {"hasMore": True, "nextCursor": "opaque_cursor"},
            {"hasMore": False, "nextCursor": None},
        ):
            with self.subTest(page=page):
                smoke.validate_collection_page({"data": [], "page": page})

    def test_rejects_missing_page_fields(self) -> None:
        for page in ({}, {"hasMore": False}, {"nextCursor": None}, None):
            with self.subTest(page=page):
                with self.assertRaises(AssertionError):
                    smoke.validate_collection_page({"data": [], "page": page})

    def test_rejects_non_boolean_has_more(self) -> None:
        for value in (0, 1, "false", None):
            with self.subTest(has_more=value):
                with self.assertRaisesRegex(AssertionError, "must be a boolean"):
                    smoke.validate_collection_page({
                        "data": [], "page": {"hasMore": value, "nextCursor": None}
                    })

    def test_rejects_missing_or_invalid_next_cursor(self) -> None:
        for cursor in (None, "", " ", 123, False):
            with self.subTest(cursor=cursor):
                with self.assertRaisesRegex(AssertionError, "non-empty string"):
                    smoke.validate_collection_page({
                        "data": [], "page": {"hasMore": True, "nextCursor": cursor}
                    })

    def test_rejects_cursor_on_terminal_page(self) -> None:
        for cursor in ("opaque_cursor", "", False):
            with self.subTest(cursor=cursor):
                with self.assertRaisesRegex(AssertionError, "must be null"):
                    smoke.validate_collection_page({
                        "data": [], "page": {"hasMore": False, "nextCursor": cursor}
                    })

    def test_rejects_old_or_malformed_collection_envelopes(self) -> None:
        page = {"hasMore": False, "nextCursor": None}
        for payload in (
            {"data": {"items": []}, "page": page},
            {"data": [], "meta": {"page": page}},
            {"data": [], "page": page, "meta": {}},
            {"data": []},
            None,
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(AssertionError):
                    smoke.validate_collection_page(payload)


if __name__ == "__main__":
    unittest.main(verbosity=2)
