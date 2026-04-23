"""Pytest configuration for async tests."""

import pytest

# Enable asyncio mode for all tests
pytest_plugins = ("pytest_asyncio",)
