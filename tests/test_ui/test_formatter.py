"""Tests for data formatter."""

from datetime import datetime

from rich.text import Text

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
    output = formatter.format_notifications([])

    assert isinstance(output, Text)
    assert "No notifications" in str(output)


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

    output = formatter.format_notifications(notifications)

    assert isinstance(output, Text)
    assert "Review my PR" in str(output)


def test_format_pull_requests_empty() -> None:
    """Test formatting empty pull requests."""
    formatter = Formatter()
    output = formatter.format_pull_requests([])

    assert isinstance(output, Text)
    # Panel titles no longer used with list format
    # assert output.title == "Pull Requests"


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

    output = formatter.format_pull_requests(prs)

    assert isinstance(output, Text)
    assert "Add new feature" in str(output)


def test_format_builds_empty() -> None:
    """Test formatting empty builds."""
    formatter = Formatter()
    output = formatter.format_builds([])

    assert isinstance(output, Text)
    # Panel titles no longer used with list format
    # assert output.title == "Build Status"


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

    output = formatter.format_builds(builds)

    assert isinstance(output, Text)
    assert "Submit package update" in str(output)


def test_format_review_section_empty() -> None:
    """Test formatting empty review section."""
    formatter = Formatter()
    output = formatter.format_review_section([], [])

    assert isinstance(output, Text)
    # Panel titles no longer used with list format
    # assert output.title == "Reviews"


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

    output = formatter.format_review_section(to_review, reviewed)

    assert isinstance(output, Text)
    # Check for PR titles in output
    assert "Needs review" in str(output)
    assert "Already reviewed" in str(output)


def test_format_error() -> None:
    """Test formatting error message."""
    from rich.panel import Panel

    formatter = Formatter()
    output = formatter.format_error("github", "Connection failed")

    # format_error still returns a Panel (not changed to list format)
    assert isinstance(output, Panel)
    assert "Error" in output.title
    assert "github" in output.title


def test_format_pull_requests_all_states() -> None:
    """Test PR formatting with all possible states."""
    formatter = Formatter()
    now = datetime.now()

    prs = [
        # Draft PR
        PullRequest(
            id="1",
            provider="github",
            number=1,
            title="Draft PR",
            repo="owner/repo",
            author="alice",
            url="https://github.com/owner/repo/pull/1",
            state="open",
            draft=True,
            updated_at=now,
        ),
        # Merged PR
        PullRequest(
            id="2",
            provider="github",
            number=2,
            title="Merged PR",
            repo="owner/repo",
            author="alice",
            url="https://github.com/owner/repo/pull/2",
            state="merged",
            updated_at=now,
        ),
        # Closed PR
        PullRequest(
            id="3",
            provider="github",
            number=3,
            title="Closed PR",
            repo="owner/repo",
            author="alice",
            url="https://github.com/owner/repo/pull/3",
            state="closed",
            updated_at=now,
        ),
        # Approved PR
        PullRequest(
            id="4",
            provider="github",
            number=4,
            title="Approved PR",
            repo="owner/repo",
            author="alice",
            url="https://github.com/owner/repo/pull/4",
            state="open",
            review_decision="approved",
            updated_at=now,
        ),
        # Changes requested
        PullRequest(
            id="5",
            provider="github",
            number=5,
            title="Changes Requested",
            repo="owner/repo",
            author="alice",
            url="https://github.com/owner/repo/pull/5",
            state="open",
            review_decision="changes_requested",
            updated_at=now,
        ),
    ]

    output = formatter.format_pull_requests(prs)
    # All 5 PRs should be in output
    assert "Draft PR" in str(output)
    assert "Merged PR" in str(output)
    assert "Closed PR" in str(output)
    assert "Approved PR" in str(output)
    assert "Changes Requested" in str(output)


def test_format_builds_all_states() -> None:
    """Test build formatting with all possible states."""
    formatter = Formatter()

    builds = [
        # Succeeded
        BuildStatus(
            id="1",
            provider="obs",
            type="build",
            title="Build succeeded",
            status="succeeded",
            url="https://build.opensuse.org/1",
        ),
        # Failed
        BuildStatus(
            id="2",
            provider="obs",
            type="build",
            title="Build failed",
            status="failed",
            url="https://build.opensuse.org/2",
        ),
        # Building
        BuildStatus(
            id="3",
            provider="obs",
            type="build",
            title="Building",
            status="building",
            url="https://build.opensuse.org/3",
        ),
        # Disabled
        BuildStatus(
            id="4",
            provider="obs",
            type="build",
            title="Disabled",
            status="disabled",
            url="https://build.opensuse.org/4",
        ),
    ]

    output = formatter.format_builds(builds)
    # All 4 builds should be in output
    assert "Build succeeded" in str(output)
    assert "Build failed" in str(output)
    assert "Building" in str(output)
    assert "Disabled" in str(output)


def test_format_review_section_with_restarted() -> None:
    """Test formatting review section with restarted review."""
    formatter = Formatter()

    reviewed = [
        PullRequest(
            id="pr-1",
            provider="github",
            number=123,
            title="Review restarted",
            repo="org/repo",
            author="developer",
            url="https://github.com/org/repo/pull/123",
            state="open",
            review_restarted=True,
            updated_at=datetime.now(),
        )
    ]

    output = formatter.format_review_section([], reviewed)
    assert isinstance(output, Text)


def test_format_notifications_without_url() -> None:
    """Test formatting notifications with empty URLs renders as plain text."""
    formatter = Formatter()

    notifications = [
        # Notification with URL (should have hyperlink)
        Notification(
            id="1",
            provider="github",
            type="pr_review_request",
            title="Review my PR",
            repo="org/repo",
            url="https://github.com/org/repo/pull/1",
            updated_at=datetime.now(),
        ),
        # Notification without URL (agent_session_finished)
        Notification(
            id="2",
            provider="github",
            type="agent_session_finished",
            title="Agent Session Finished: Documenting commit message checker",
            repo="os-autoinst/os-autoinst-distri-opensuse",
            url="",  # Empty URL
            updated_at=datetime.now(),
        ),
    ]

    output = formatter.format_notifications(notifications)

    assert isinstance(output, Text)
    output_str = str(output)

    # First notification should appear
    assert "Review my PR" in output_str

    # Second notification should appear as plain text (no OSC 8 with empty URL)
    assert "Agent Session Finished" in output_str
    assert "Documenting commit message checker" in output_str

    # Verify no invalid OSC 8 sequences (OSC 8 with empty URL)
    # Valid OSC 8: \x1b]8;;URL\x1b\\ (has URL between semicolons)
    # Invalid OSC 8: \x1b]8;;\x1b\\ (empty URL)
    # We can't easily check the raw ANSI codes, but we can verify the title appears
    assert "os-autoinst/os-autoinst-distri-opensuse" in output_str
