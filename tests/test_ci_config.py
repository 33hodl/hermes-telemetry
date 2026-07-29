"""Guard: the lint toolchain must be pinned to one version, from one place.

CI installed ruff unpinned (`pip install ruff`), so ruff 0.16.0 — which
graduated Markdown formatting out of preview and started formatting the Python
blocks inside README.md / ONBOARDING.md — turned main red with no repo change
at all. `.ruff-version` is the single source of truth: CI installs exactly that
version and `.githooks/pre-commit` warns when the local ruff differs, which is
what keeps the hook's "green local commit means green CI" promise honest.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUFF_VERSION_FILE = ROOT / ".ruff-version"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
PRE_COMMIT_HOOK = ROOT / ".githooks" / "pre-commit"


def test_ruff_version_file_holds_a_bare_version():
    assert RUFF_VERSION_FILE.exists(), ".ruff-version is the single source of truth for the pin"
    raw = RUFF_VERSION_FILE.read_text().strip()
    assert re.fullmatch(r"\d+\.\d+\.\d+", raw), (
        f".ruff-version must hold a bare x.y.z version, got {raw!r}"
    )


def test_ci_installs_ruff_from_the_pin_file():
    """A bare `pip install ruff` lets any future release break CI on its own."""
    ci = CI_WORKFLOW.read_text()
    assert not re.search(r"pip install ruff\s*$", ci, re.M), (
        "CI installs ruff unpinned; pin it from .ruff-version"
    )
    assert ".ruff-version" in ci, "CI must read the pin from .ruff-version"


def test_ruff_format_excludes_markdown():
    """Docs must not be at the mercy of the formatter's Markdown support.

    The Python blocks in README.md / ONBOARDING.md are hand-aligned reference
    tables; ruff 0.16.0 collapses that alignment and fails the check. Excluding
    them keeps `ruff format --check .` deterministic across ruff versions — and
    unlike the version pin, this takes effect for pull requests too, since
    `pull_request_target` reads the workflow from the base branch but the config
    from the PR checkout.
    """
    pyproject = (ROOT / "pyproject.toml").read_text()
    assert re.search(r"^extend-exclude\s*=\s*\[[^\]]*\"\*\.md\"", pyproject, re.M), (
        "pyproject must exclude *.md from ruff so docs formatting stays a deliberate choice"
    )


def test_pre_commit_hook_checks_the_pinned_ruff():
    """The hook's whole value is matching CI, so it must notice a version skew."""
    hook = PRE_COMMIT_HOOK.read_text()
    assert ".ruff-version" in hook, "the hook must compare local ruff against the pin"
