"""Tests for motdd/ui/cli_mode.py."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from motdd.cache import Cache
from motdd.config import Config
from motdd.models import Notification, PullRequest
from motdd.ui.cli_mode import CLIMode


@pytest.fixture
def config(tmp_path):
    """Create a test config."""
    config_path = tmp_path / "motdd.toml"
    config_path.write_text("""
[general]
default_provider = "github"

[[providers.github]]
name = "github"
host = "github.com"
cli_tool = "gh"
    """)
    return Config(config_path=config_path)


@pytest.fixture
def cli_mode(config):
    """Create a CLI mode instance."""
    cache = Cache(ttl_seconds=300)
    return CLIMode(config, cache=cache, repo_filter=None, verbose=False)


@pytest.mark.asyncio
async def test_get_all_notifications(cli_mode):
    """Test getting notifications from all providers."""
    now = datetime.now()
    test_notification = Notification(
        id="1",
        provider="github",
        type="pr_review_request",
        title="Review needed",
        repo="owner/repo",
        url="https://github.com/owner/repo/pull/1",
        updated_at=now,
        unread=True,
    )

    with patch(
        "motdd.providers.github.GitHubProvider.get_notifications",
        new_callable=AsyncMock,
        return_value=[test_notification],
    ):
        notifications = await cli_mode._get_all_notifications()

    assert len(notifications) == 1
    assert notifications[0].id == "1"
    assert notifications[0].provider == "github"


@pytest.mark.asyncio
async def test_get_all_notifications_error_handling(cli_mode):
    """Test error handling when getting notifications."""
    with patch(
        "motdd.providers.github.GitHubProvider.get_notifications",
        new_callable=AsyncMock,
        side_effect=Exception("API error"),
    ):
        notifications = await cli_mode._get_all_notifications()

    # Should return empty list on error
    assert notifications == []


@pytest.mark.asyncio
async def test_get_my_prs(cli_mode):
    """Test getting my PRs."""
    now = datetime.now()
    test_pr = PullRequest(
        id="1",
        provider="github",
        number=123,
        title="Test PR",
        repo="owner/repo",
        author="me",
        url="https://github.com/owner/repo/pull/123",
        state="open",
        review_decision=None,
        reviews_by_me=[],
        review_restarted=False,
        ci_status=None,
        updated_at=now,
        created_at=now - timedelta(hours=1),
        draft=False,
    )

    with patch(
        "motdd.providers.github.GitHubProvider.get_my_prs",
        new_callable=AsyncMock,
        return_value=[test_pr],
    ):
        prs = await cli_mode._get_my_prs()

    assert len(prs) == 1
    assert prs[0].number == 123


@pytest.mark.asyncio
async def test_get_prs_to_review(cli_mode):
    """Test getting PRs to review."""
    now = datetime.now()
    test_pr = PullRequest(
        id="2",
        provider="github",
        number=456,
        title="Review this",
        repo="owner/repo",
        author="other",
        url="https://github.com/owner/repo/pull/456",
        state="open",
        review_decision=None,
        reviews_by_me=[],
        review_restarted=False,
        ci_status="pending",
        updated_at=now,
        created_at=now - timedelta(hours=2),
        draft=False,
    )

    with patch(
        "motdd.providers.github.GitHubProvider.get_prs_to_review",
        new_callable=AsyncMock,
        return_value=[test_pr],
    ):
        prs = await cli_mode._get_prs_to_review()

    assert len(prs) == 1
    assert prs[0].number == 456


@pytest.mark.asyncio
async def test_get_reviewed_prs(cli_mode):
    """Test getting reviewed PRs."""
    now = datetime.now()
    test_pr = PullRequest(
        id="3",
        provider="github",
        number=789,
        title="Already reviewed",
        repo="owner/repo",
        author="other",
        url="https://github.com/owner/repo/pull/789",
        state="open",
        review_decision="approved",
        reviews_by_me=["approved"],
        review_restarted=False,
        ci_status="success",
        updated_at=now,
        created_at=now - timedelta(days=2),
        draft=False,
    )

    with patch(
        "motdd.providers.github.GitHubProvider.get_reviewed_prs",
        new_callable=AsyncMock,
        return_value=[test_pr],
    ):
        prs = await cli_mode._get_reviewed_prs()

    assert len(prs) == 1
    assert prs[0].number == 789


@pytest.mark.asyncio
async def test_get_obs_data(cli_mode):
    """Test getting OBS build data."""
    # OBS provider not configured in test config
    builds = await cli_mode._get_obs_data()
    assert builds == []


@pytest.mark.asyncio
async def test_get_ibs_data(cli_mode):
    """Test getting IBS build data."""
    # IBS provider not configured in test config
    builds = await cli_mode._get_ibs_data()
    assert builds == []


@pytest.mark.asyncio
async def test_show_notifications_with_repo_filter(config):
    """Test showing notifications with repo filter."""
    cli_mode = CLIMode(config, repo_filter="owner/repo", verbose=False)

    now = datetime.now()
    test_notification = Notification(
        id="1",
        provider="github",
        type="pr_review_request",
        title="Review needed",
        repo="owner/repo",
        url="https://github.com/owner/repo/pull/1",
        updated_at=now,
        unread=True,
    )

    with (
        patch(
            "motdd.providers.github.GitHubProvider.get_notifications",
            new_callable=AsyncMock,
            return_value=[test_notification],
        ),
        patch("motdd.ui.cli_mode.Console.print") as mock_print,
    ):
        await cli_mode.show_notifications()

    # Should print section header and panel (2 calls)
    assert mock_print.call_count == 2


@pytest.mark.asyncio
async def test_show_my_prs(cli_mode):
    """Test showing my PRs."""
    with (
        patch.object(cli_mode, "_get_my_prs", new_callable=AsyncMock, return_value=[]),
        patch("motdd.ui.cli_mode.Console.print") as mock_print,
    ):
        await cli_mode.show_my_prs()

    # Should print section header and panel (2 calls)
    assert mock_print.call_count == 2


@pytest.mark.asyncio
async def test_show_reviews(cli_mode):
    """Test showing reviews."""
    with (
        patch.object(cli_mode, "_get_prs_to_review", new_callable=AsyncMock, return_value=[]),
        patch.object(cli_mode, "_get_reviewed_prs", new_callable=AsyncMock, return_value=[]),
        patch("motdd.ui.cli_mode.Console.print") as mock_print,
    ):
        await cli_mode.show_reviews()

    # Should print section header and panel (2 calls)
    assert mock_print.call_count == 2


@pytest.mark.asyncio
async def test_show_all(cli_mode):
    """Test showing all sections."""
    with (
        patch.object(cli_mode, "show_reviews", new_callable=AsyncMock) as mock_reviews,
        patch.object(cli_mode, "show_my_prs", new_callable=AsyncMock) as mock_prs,
        patch.object(cli_mode, "show_notifications", new_callable=AsyncMock) as mock_notifs,
        patch.object(cli_mode, "show_obs", new_callable=AsyncMock) as mock_obs,
        patch.object(cli_mode, "show_ibs", new_callable=AsyncMock) as mock_ibs,
    ):
        await cli_mode.show_all()

        # All sections should be called
        mock_reviews.assert_awaited_once()
        mock_prs.assert_awaited_once()
        mock_notifs.assert_awaited_once()
        mock_obs.assert_awaited_once()
        mock_ibs.assert_awaited_once()
