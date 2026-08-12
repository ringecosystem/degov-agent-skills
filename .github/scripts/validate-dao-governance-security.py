#!/usr/bin/env python3
"""File overview: validate the dao-governance-security skill and examples.

This script intentionally uses only the Python standard library so it can run in
CI and local smoke tests without installing extra packages. It validates the
same properties that matter for a Hermes skill load at a repository level:
frontmatter shape, non-empty body, required final-output sections, and example
outputs that exercise both benign and high-risk proposal analysis paths. It
also checks that required output markers render as Markdown instead of being
accidentally indented into code blocks.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import NoReturn

ROOT = Path(__file__).resolve().parents[2]
SKILL_PATH = ROOT / 'skills' / 'dao-governance-security' / 'SKILL.md'
EXAMPLES_DIR = ROOT / 'skills' / 'dao-governance-security' / 'examples'

REQUIRED_OUTPUT_MARKERS = [
    'Overall risk:',
    'Confidence:',
    'Recommendation:',
    '### Bottom line',
    '### Risk summary',
    '### Proposal and evidence reviewed',
    '### Executable actions checked',
    '### Findings',
    '### Uncertainties and assumptions',
    '### Recommended user actions',
]

EXAMPLE_EXPECTATIONS = {
    'benign-operational-budget.md': {
        'risk': 'Low',
        'terms': [
            '25,000 USDC',
            'Bug Bounty Ops multisig',
            'none identified',
            'No role grants',
            'support is reasonable',
        ],
    },
    'risky-treasury-drain-and-admin-grant.md': {
        'risk': 'Critical',
        'terms': [
            '2,500,000 USDC',
            '25,000 USDC',
            'unknown EOA',
            'DEFAULT_ADMIN_ROLE',
            'new proposer',
            'oppose',
            'do not execute',
        ],
    },
}


def fail(message: str) -> NoReturn:
    raise AssertionError(message)


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding='utf-8')
    if not text.startswith('---\n'):
        fail(f'{path}: missing opening frontmatter delimiter at byte 0')
    try:
        raw_frontmatter, body = text[4:].split('\n---\n', 1)
    except ValueError as exc:
        raise AssertionError(f'{path}: missing closing frontmatter delimiter') from exc

    fields: dict[str, str] = {}
    current_key: str | None = None
    for line in raw_frontmatter.splitlines():
        if not line.strip():
            continue
        if line.startswith(' ') or line.startswith('\t'):
            # Indented line: either a block-scalar continuation of the current
            # key (prettier wraps long descriptions) or a nested key. Nested
            # keys are promoted loosely so version checks keep working.
            stripped = line.strip()
            if ':' in stripped:
                k, v = stripped.split(':', 1)
                fields[k.strip()] = v.strip().strip('"\'')
            elif current_key is not None:
                fields[current_key] = (fields.get(current_key, '') + ' ' + stripped).strip()
            continue
        match = re.match(r'^([A-Za-z0-9_-]+):\s*(.*)$', line)
        if match:
            current_key = match.group(1)
            fields[current_key] = match.group(2).strip().strip('"\'')

    if not body.strip():
        fail(f'{path}: body is empty')
    return fields, body


def assert_contains_all(text: str, markers: list[str], label: str) -> None:
    missing = [marker for marker in markers if marker not in text]
    if missing:
        fail(f'{label}: missing required markers: {missing}')


def assert_markers_start_lines(text: str, markers: list[str], label: str) -> None:
    """Ensure required Markdown markers are not hidden inside code blocks.

    Four leading spaces turn headings, fields, lists, and tables into literal
    code blocks in Markdown. A plain substring check can pass even though the
    rendered analysis is unreadable and fails the skill's final-output contract.
    """

    missing_at_column_zero = []
    for marker in markers:
        if not re.search(rf'^{re.escape(marker)}', text, flags=re.MULTILINE):
            missing_at_column_zero.append(marker)
    if missing_at_column_zero:
        fail(f'{label}: required Markdown markers must start at column 0: {missing_at_column_zero}')


def assert_no_indented_markdown_blocks(text: str, label: str) -> None:
    bad_lines = []
    markdown_start = re.compile(
        r' {4}(?:#{1,6} |[-*] |\| |Overall risk:|Confidence:|Recommendation:)'
    )
    for line_number, line in enumerate(text.splitlines(), start=1):
        if markdown_start.match(line):
            bad_lines.append(f'{line_number}: {line[:80]}')
    if bad_lines:
        preview = '; '.join(bad_lines[:5])
        fail(f'{label}: Markdown appears indented as a code block: {preview}')


def validate_skill() -> None:
    fields, body = parse_frontmatter(SKILL_PATH)
    if fields.get('name') != 'dao-governance-security':
        fail(f'{SKILL_PATH}: expected name dao-governance-security, found {fields.get("name")!r}')
    description = fields.get('description', '')
    if not description:
        fail(f'{SKILL_PATH}: missing description')
    if len(description) > 1024:
        fail(f'{SKILL_PATH}: description exceeds 1024 characters')
    assert_contains_all(body, REQUIRED_OUTPUT_MARKERS, str(SKILL_PATH))
    template_match = re.search(r'```(?:markdown|text)\n(?P<template>.*?)\n```', body, flags=re.DOTALL)
    if not template_match:
        fail(f'{SKILL_PATH}: final-output template fence is missing')
    template = template_match.group('template')
    assert_contains_all(template, REQUIRED_OUTPUT_MARKERS, f'{SKILL_PATH} final-output template')
    assert_markers_start_lines(template, REQUIRED_OUTPUT_MARKERS, f'{SKILL_PATH} final-output template')
    assert_no_indented_markdown_blocks(template, f'{SKILL_PATH} final-output template')

    if 'Required sections are:' not in body:
        fail(f'{SKILL_PATH}: required-section contract intro is missing')
    for section_name in [
        'Overall risk',
        'Confidence',
        'Recommendation',
        'Bottom line',
        'Risk summary',
        'Proposal and evidence reviewed',
        'Executable actions checked',
        'Findings',
        'Uncertainties and assumptions',
        'Recommended user actions',
    ]:
        if f'`{section_name}`' not in body:
            fail(f'{SKILL_PATH}: required-section contract missing `{section_name}`')


def validate_examples() -> None:
    if not EXAMPLES_DIR.is_dir():
        fail(f'{EXAMPLES_DIR}: examples directory is missing')

    for filename, expectation in EXAMPLE_EXPECTATIONS.items():
        path = EXAMPLES_DIR / filename
        if not path.is_file():
            fail(f'{path}: expected example file is missing')
        text = path.read_text(encoding='utf-8')
        assert_contains_all(text, REQUIRED_OUTPUT_MARKERS, str(path))
        assert_markers_start_lines(text, REQUIRED_OUTPUT_MARKERS, str(path))
        assert_no_indented_markdown_blocks(text, str(path))
        expected_risk = expectation['risk']
        if f'Overall risk: {expected_risk}' not in text:
            fail(f'{path}: expected Overall risk: {expected_risk}')
        assert_contains_all(text, expectation['terms'], str(path))

    risky_text = (EXAMPLES_DIR / 'risky-treasury-drain-and-admin-grant.md').read_text(encoding='utf-8')
    risky_categories = {
        'malicious_or_contradictory_action': 'materially contradicts the proposal text',
        'incorrect_amount': '100x the proposal text',
        'suspicious_recipient': 'unknown EOA',
        'suspicious_proposer': 'new proposer',
        'dangerous_permission': 'DEFAULT_ADMIN_ROLE',
    }
    assert_contains_all(risky_text, list(risky_categories.values()), 'risky example coverage')


def main() -> int:
    validate_skill()
    validate_examples()
    print('dao-governance-security validation: ok')
    print(f'- skill loadable: {SKILL_PATH}')
    print(f'- examples checked: {len(EXAMPLE_EXPECTATIONS)}')
    print('- structured output markers present in skill template and examples')
    print('- Markdown markers render at column 0, not as indented code blocks')
    print('- risky example covers malicious/contradictory action, incorrect amount, suspicious recipient/proposer, and dangerous permission')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f'dao-governance-security validation: failed: {exc}', file=sys.stderr)
        raise SystemExit(1)
