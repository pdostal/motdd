"""Tests for color themes."""

from motdd.ui.themes import Theme, get_theme


def test_get_theme_default() -> None:
    """Test getting default theme."""
    theme = get_theme("default")
    assert isinstance(theme, Theme)
    assert theme.success == "green"
    assert theme.error == "red"


def test_get_theme_light() -> None:
    """Test getting light theme."""
    theme = get_theme("light")
    assert isinstance(theme, Theme)
    assert theme.success == "dark_green"


def test_get_theme_solarized() -> None:
    """Test getting solarized theme."""
    theme = get_theme("solarized")
    assert isinstance(theme, Theme)
    assert theme.success == "#859900"


def test_get_theme_nord() -> None:
    """Test getting nord theme."""
    theme = get_theme("nord")
    assert isinstance(theme, Theme)
    assert theme.success == "#a3be8c"


def test_get_theme_unknown() -> None:
    """Test getting unknown theme returns default."""
    theme = get_theme("unknown_theme")
    assert isinstance(theme, Theme)
    assert theme.success == "green"  # Should be default


def test_theme_has_all_colors() -> None:
    """Test that themes have all required colors."""
    theme = get_theme("default")

    # Status colors
    assert hasattr(theme, "success")
    assert hasattr(theme, "warning")
    assert hasattr(theme, "error")
    assert hasattr(theme, "info")
    assert hasattr(theme, "muted")

    # UI elements
    assert hasattr(theme, "header")
    assert hasattr(theme, "border")
    assert hasattr(theme, "highlight")
    assert hasattr(theme, "text")

    # PR states
    assert hasattr(theme, "pr_open")
    assert hasattr(theme, "pr_merged")
    assert hasattr(theme, "pr_closed")
    assert hasattr(theme, "pr_draft")
