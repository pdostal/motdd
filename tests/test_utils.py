"""Tests for utility functions."""

from datetime import datetime, timedelta

from motdd.models import Notification, PullRequest
from motdd.utils import (
    filter_by_age,
    filter_by_repo,
    get_provider_icon,
    get_status_icon,
    osc8_link,
    relative_time,
    truncate_text,
)


def test_relative_time() -> None:
    """Test relative time formatting."""
    now = datetime.now()

    # Just now
    assert relative_time(now) == "just now"

    # Minutes ago
    past = now - timedelta(minutes=30)
    assert "30m" in relative_time(past) or "29m" in relative_time(past)

    # Hours ago
    past = now - timedelta(hours=5)
    assert "5h" in relative_time(past) or "4h" in relative_time(past)

    # Days ago
    past = now - timedelta(days=3)
    assert "3d" in relative_time(past) or "2d" in relative_time(past)


def test_get_status_icon() -> None:
    """Test status icon selection."""
    # PR status
    assert get_status_icon("approved", "pr") == "[✓]"
    assert get_status_icon("merged", "pr") == "[M]"
    assert get_status_icon("draft", "pr") == "[…]"
    assert get_status_icon("changes_requested", "pr") == "[!]"
    assert get_status_icon("failed", "pr") == "[!]"
    assert get_status_icon("closed", "pr") == "[X]"
    assert get_status_icon("pending", "pr") == "[…]"

    # Build status
    assert get_status_icon("succeeded", "build") == "[✓]"
    assert get_status_icon("success", "build") == "[✓]"
    assert get_status_icon("failed", "build") == "[✗]"
    assert get_status_icon("building", "build") == "[…]"
    assert get_status_icon("disabled", "build") == "[-]"

    # Review status
    assert get_status_icon("approved", "review") == "[✓]"
    assert get_status_icon("restarted", "review") == "[↻]"
    assert get_status_icon("pending", "review") == "[…]"

    # Notification status
    assert get_status_icon("review_request", "notification") == "[R]"
    assert get_status_icon("comment", "notification") == "[C]"
    assert get_status_icon("approved", "notification") == "[✓]"
    assert get_status_icon("changes_requested", "notification") == "[!]"


def test_get_provider_icon() -> None:
    """Test provider icon selection."""
    assert get_provider_icon("github") == "gh"
    assert get_provider_icon("gitlab") == "gl"
    assert get_provider_icon("forgejo") == "fj"
    assert get_provider_icon("gitea") == "gt"
    assert get_provider_icon("obs") == "obs"
    assert get_provider_icon("ibs") == "ibs"
    assert get_provider_icon("unknown") == "git"


def test_truncate_text() -> None:
    """Test text truncation."""
    text = "This is a long text that needs to be truncated"

    # No truncation needed
    assert truncate_text(text, 100) == text

    # Truncate
    truncated = truncate_text(text, 20)
    assert len(truncated) == 20
    assert truncated.endswith("...")

    # Custom suffix
    truncated = truncate_text(text, 20, suffix="…")
    assert truncated.endswith("…")


def test_filter_by_repo() -> None:
    """Test repository filtering."""
    pr1 = PullRequest(
        id="1",
        provider="github",
        number=1,
        title="PR 1",
        repo="org1/repo1",
        author="alice",
        url="https://example.com/1",
        state="open",
    )
    pr2 = PullRequest(
        id="2",
        provider="github",
        number=2,
        title="PR 2",
        repo="org2/repo2",
        author="bob",
        url="https://example.com/2",
        state="open",
    )

    items = [pr1, pr2]

    # Filter by repo
    filtered = filter_by_repo(items, "org1/repo1")
    assert len(filtered) == 1
    assert filtered[0].repo == "org1/repo1"

    # No filter
    filtered = filter_by_repo(items, None)
    assert len(filtered) == 2


def test_filter_by_age() -> None:
    """Test age-based filtering."""
    now = datetime.now()

    notif1 = Notification(
        id="1",
        provider="github",
        type="pr_review",
        title="Review PR",
        repo="org/repo",
        url="https://example.com",
        updated_at=now - timedelta(days=5),
    )
    notif2 = Notification(
        id="2",
        provider="github",
        type="pr_review",
        title="Review PR",
        repo="org/repo",
        url="https://example.com",
        updated_at=now - timedelta(days=35),
    )

    items = [notif1, notif2]

    # Filter to last 30 days
    filtered = filter_by_age(items, 30)
    assert len(filtered) == 1
    assert filtered[0].id == "1"

    # Filter to last 40 days
    filtered = filter_by_age(items, 40)
    assert len(filtered) == 2


def test_osc8_link() -> None:
    """Test OSC 8 hyperlink generation."""
    import os

    url = "https://github.com/owner/repo/pull/123"
    text = "PR #123"

    # Save original environment
    orig_term = os.environ.get("TERM")
    orig_term_program = os.environ.get("TERM_PROGRAM")
    orig_lc_terminal = os.environ.get("LC_TERMINAL")

    try:
        # Test with iTerm2 (via TERM_PROGRAM)
        os.environ["TERM"] = "xterm-256color"
        os.environ["TERM_PROGRAM"] = "iTerm.app"
        link = osc8_link(url, text, fallback=False)
        assert "\x1b]8;;" in link
        assert text in link
        assert url in link

        # Test with iTerm2 (via LC_TERMINAL)
        os.environ.pop("TERM_PROGRAM", None)
        os.environ["LC_TERMINAL"] = "iTerm2"
        link = osc8_link(url, text, fallback=False)
        assert "\x1b]8;;" in link

        # Test with kitty (via TERM)
        os.environ.pop("LC_TERMINAL", None)
        os.environ["TERM"] = "xterm-kitty"
        link = osc8_link(url, text, fallback=False)
        assert "\x1b]8;;" in link

        # Test with unsupported terminal and fallback
        os.environ["TERM"] = "xterm"
        os.environ.pop("TERM_PROGRAM", None)
        link = osc8_link(url, text, fallback=True)
        assert text in link
        assert url in link
        assert "(" in link and ")" in link  # Fallback format

        # Test without fallback on unsupported terminal
        link = osc8_link(url, text, fallback=False)
        assert "\x1b]8;;" in link  # Still generates OSC 8

    finally:
        # Restore original environment
        if orig_term:
            os.environ["TERM"] = orig_term
        else:
            os.environ.pop("TERM", None)

        if orig_term_program:
            os.environ["TERM_PROGRAM"] = orig_term_program
        else:
            os.environ.pop("TERM_PROGRAM", None)

        if orig_lc_terminal:
            os.environ["LC_TERMINAL"] = orig_lc_terminal
        else:
            os.environ.pop("LC_TERMINAL", None)


def test_relative_time_edge_cases() -> None:
    """Test relative time edge cases."""
    now = datetime.now()

    # Weeks ago - should show weeks
    past = now - timedelta(weeks=2)
    result = relative_time(past)
    assert "2w" in result or "1w" in result

    # Months ago (more than 30 days)
    past = now - timedelta(days=45)
    result = relative_time(past)
    assert "6w" in result or "1mo" in result or "45d" in result


def test_osc8_link_empty_url() -> None:
    """Test OSC 8 hyperlink with empty URL returns plain text."""
    text = "Agent Session Finished"

    # Empty string URL
    result = osc8_link("", text, fallback=False)
    assert result == text
    assert "\x1b]8;;" not in result  # No OSC 8 sequences

    # Empty string URL with fallback
    result = osc8_link("", text, fallback=True)
    assert result == text
    assert "\x1b]8;;" not in result


def test_osc8_link_none_url() -> None:
    """Test OSC 8 hyperlink with None URL returns plain text."""
    text = "Notification without URL"

    # None URL (falsy value)
    result = osc8_link(None, text, fallback=False)  # type: ignore
    assert result == text
    assert "\x1b]8;;" not in result
