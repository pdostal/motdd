"""Tests for base provider."""


import pytest

from motdd.providers.base import BaseProvider, ProviderError


class TestProvider(BaseProvider):
    """Test provider implementation."""

    async def get_notifications(self):
        """Get notifications."""
        return []

    async def get_my_prs(self):
        """Get my PRs."""
        return []

    async def get_prs_to_review(self):
        """Get PRs to review."""
        return []


@pytest.fixture
def test_config() -> dict:
    """Test provider configuration."""
    return {
        "name": "test",
        "cli_tool": "test_cli",
    }


@pytest.fixture
def test_provider(test_config: dict) -> TestProvider:
    """Create test provider instance."""
    return TestProvider("test", test_config)


def test_provider_init(test_provider: TestProvider) -> None:
    """Test provider initialization."""
    assert test_provider.name == "test"
    assert test_provider.cli_tool == "test_cli"


@pytest.mark.asyncio
async def test_check_cli_available_not_found(test_provider: TestProvider) -> None:
    """Test CLI availability check when tool not found."""
    assert test_provider._check_cli_available() is False


@pytest.mark.asyncio
async def test_run_command_cli_not_found(test_provider: TestProvider) -> None:
    """Test running command when CLI tool not found."""
    with pytest.raises(ProviderError, match="not found in PATH"):
        await test_provider._run_command(["--version"])


@pytest.mark.asyncio
async def test_default_implementations(test_provider: TestProvider) -> None:
    """Test default method implementations."""
    # These should return empty or raise NotImplementedError
    assert await test_provider.get_reviewed_prs() == []
    assert await test_provider.get_user_prs("user") == []

    await test_provider.mark_notification_read("123")  # Should not raise

    with pytest.raises(NotImplementedError):
        await test_provider.approve_pr("123")

    with pytest.raises(NotImplementedError):
        await test_provider.comment_on_pr("123", "test")

    with pytest.raises(NotImplementedError):
        await test_provider.request_changes("123", "test")

    with pytest.raises(NotImplementedError):
        await test_provider.merge_pr("123")
