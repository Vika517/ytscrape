"""Shared pytest configuration.

Tests marked ``@pytest.mark.network`` hit the real YouTube. They are skipped
unless ``--run-network`` is passed::

    uv run pytest --run-network -m network
"""

from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-network",
        action="store_true",
        default=False,
        help="run tests that make requests to the real YouTube",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if config.getoption("--run-network"):
        return
    skip = pytest.mark.skip(reason="needs --run-network (real YouTube requests)")
    for item in items:
        if "network" in item.keywords:
            item.add_marker(skip)
