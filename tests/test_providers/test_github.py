"""Tests for GitHub provider."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from motdd.providers.github import GitHubProvider


@pytest.fixture
def github_config() -> dict:
    """GitHub provider configuration."""
    return {
        "name": "github",
        "host": "github.com",
        "cli_tool": "gh",
    }


@pytest.fixture
def github_provider(github_config: dict) -> GitHubProvider:
    """Create GitHub provider instance."""
    return GitHubProvider("github", github_config)


@pytest.fixture
def sample_prs() -> list:
    """Load sample PR data from fixtures."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "github_prs.json"
    with open(fixture_path) as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_github_provider_init(github_provider: GitHubProvider) -> None:
    """Test GitHub provider initialization."""
    assert github_provider.name == "github"
    assert github_provider.cli_tool == "gh"


@pytest.mark.asyncio
async def test_get_my_prs(github_provider: GitHubProvider, sample_prs: list) -> None:
    """Test getting my PRs."""
    with patch.object(github_provider, "_run_command", new_callable=AsyncMock) as mock_cmd:
        mock_cmd.return_value = sample_prs

        prs = await github_provider.get_my_prs()

        assert len(prs) == 2
        assert prs[0].number == 123
        assert prs[0].title == "Add new feature"
        assert prs[0].state == "open"
        assert prs[0].draft is False
        assert prs[0].ci_status == "success"
        assert prs[0].review_decision == "approved"

        assert prs[1].number == 124
        assert prs[1].draft is True
        assert prs[1].ci_status == "pending"


@pytest.mark.asyncio
async def test_get_my_prs_empty(github_provider: GitHubProvider) -> None:
    """Test getting my PRs when there are none."""
    with patch.object(github_provider, "_run_command", new_callable=AsyncMock) as mock_cmd:
        mock_cmd.return_value = []

        prs = await github_provider.get_my_prs()

        assert prs == []


@pytest.mark.asyncio
async def test_parse_pr(github_provider: GitHubProvider, sample_prs: list) -> None:
    """Test PR parsing."""
    pr = github_provider._parse_pr(sample_prs[0])

    assert pr.id == "github-owner/repo-123"
    assert pr.provider == "github"
    assert pr.number == 123
    assert pr.repo == "owner/repo"
    assert pr.author == "developer"
    assert pr.ci_status == "success"
