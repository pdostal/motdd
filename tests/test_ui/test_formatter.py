"""Tests for data formatter."""

from datetime import datetime

from rich.panel import Panel

from motdd.models import BuildStatus, Notification, PullRequest
from motdd.ui.formatter import Formatter


def test_formatter_init() -> None:
    """Test formatter initialization."""
    formatter = Formatter("default", terminal_width=120)
    assert formatter.theme.success == "green"
    assert formatter.terminal_width == 120


def test_format_notifications_empty() -> None:
    """Test formatting empty notifications."""
    formatter = Formatter()
    panel = formatter.format_notifications([])

    assert isinstance(panel, Panel)
    assert panel.title == "Notifications"


def test_format_notifications() -> None:
    """Test formatting notifications."""
    formatter = Formatter()

    notifications = [
        Notification(
            id="1",
            provider="github",
            type="pr_review_request",
            title="Review my PR",
            repo="org/repo",
            url="https://github.com/org/repo/pull/1",
            updated_at=datetime.now(),
        )
    ]

    panel = formatter.format_notifications(notifications)

    assert isinstance(panel, Panel)
    assert "Notifications (1)" in panel.title


def test_format_pull_requests_empty() -> None:
    """Test formatting empty pull requests."""
    formatter = Formatter()
    panel = formatter.format_pull_requests([])

    assert isinstance(panel, Panel)
    assert panel.title == "Pull Requests"


def test_format_pull_requests() -> None:
    """Test formatting pull requests."""
    formatter = Formatter()

    prs = [
        PullRequest(
            id="pr-1",
            provider="github",
            number=123,
            title="Add new feature",
            repo="org/repo",
            author="developer",
            url="https://github.com/org/repo/pull/123",
            state="open",
            updated_at=datetime.now(),
        )
    ]

    panel = formatter.format_pull_requests(prs)

    assert isinstance(panel, Panel)
    assert "Pull Requests (1)" in panel.title


def test_format_builds_empty() -> None:
    """Test formatting empty builds."""
    formatter = Formatter()
    panel = formatter.format_builds([])

    assert isinstance(panel, Panel)
    assert panel.title == "Build Status"


def test_format_builds() -> None:
    """Test formatting build statuses."""
    formatter = Formatter()

    builds = [
        BuildStatus(
            id="build-1",
            provider="obs",
            type="submit_request",
            title="Submit package update",
            status="succeeded",
            url="https://build.opensuse.org/request/123",
        )
    ]

    panel = formatter.format_builds(builds)

    assert isinstance(panel, Panel)
    assert "Build Status (1)" in panel.title


def test_format_review_section_empty() -> None:
    """Test formatting empty review section."""
    formatter = Formatter()
    panel = formatter.format_review_section([], [])

    assert isinstance(panel, Panel)
    assert panel.title == "Reviews"


def test_format_review_section() -> None:
    """Test formatting review section."""
    formatter = Formatter()

    to_review = [
        PullRequest(
            id="pr-1",
            provider="github",
            number=123,
            title="Needs review",
            repo="org/repo",
            author="developer",
            url="https://github.com/org/repo/pull/123",
            state="open",
            updated_at=datetime.now(),
        )
    ]

    reviewed = [
        PullRequest(
            id="pr-2",
            provider="github",
            number=124,
            title="Already reviewed",
            repo="org/repo",
            author="developer",
            url="https://github.com/org/repo/pull/124",
            state="open",
            updated_at=datetime.now(),
        )
    ]

    panel = formatter.format_review_section(to_review, reviewed)

    assert isinstance(panel, Panel)
    assert "1 pending" in panel.title
    assert "1 reviewed" in panel.title


def test_format_error() -> None:
    """Test formatting error message."""
    formatter = Formatter()
    panel = formatter.format_error("github", "Connection failed")

    assert isinstance(panel, Panel)
    assert "Error" in panel.title
    assert "github" in panel.title
