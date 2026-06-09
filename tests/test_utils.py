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
    assert "30m ago" in relative_time(past) or "29m ago" in relative_time(past)

    # Hours ago
    past = now - timedelta(hours=5)
    assert "5h ago" in relative_time(past) or "4h ago" in relative_time(past)

    # Days ago
    past = now - timedelta(days=3)
    assert "3d ago" in relative_time(past) or "2d ago" in relative_time(past)


def test_get_status_icon() -> None:
    """Test status icon selection."""
    # PR status
    assert get_status_icon("approved", "pr") == "[✓]"
    assert get_status_icon("merged", "pr") == "[M]"
    assert get_status_icon("draft", "pr") == "[D]"
    assert get_status_icon("changes_requested", "pr") == "[!]"
    assert get_status_icon("failed", "pr") == "[!]"
    assert get_status_icon("closed", "pr") == "[X]"
    assert get_status_icon("pending", "pr") == "[○]"

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
    url = "https://github.com/owner/repo/pull/123"
    text = "PR #123"

    # With fallback enabled (default)
    link = osc8_link(url, text, fallback=True)
    assert text in link
    assert url in link

    # Without fallback
    link = osc8_link(url, text, fallback=False)
    assert text in link

    # Empty text - should return URL with parentheses
    link = osc8_link(url, "", fallback=True)
    assert url in link


def test_relative_time_edge_cases() -> None:
    """Test relative time edge cases."""
    now = datetime.now()

    # Weeks ago - should show weeks
    past = now - timedelta(weeks=2)
    result = relative_time(past)
    assert "2w ago" in result or "1w ago" in result

    # Months ago (more than 30 days)
    past = now - timedelta(days=45)
    result = relative_time(past)
    assert "6w ago" in result or "1mo ago" in result or "45d ago" in result
