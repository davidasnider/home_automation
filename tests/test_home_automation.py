"""Tests for the home_automation module"""
import pytest

from home_automation import __version__


@pytest.mark.unittest
def test_version():
    """Ensure our version matches what is in home_automation/__init__.py"""
    assert __version__ == "0.1.0"
