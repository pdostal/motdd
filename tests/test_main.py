"""Tests for motdd/__main__.py."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from motdd.__main__ import (
    async_main,
    cmd_all,
    cmd_ibs,
    cmd_init,
    cmd_notifications,
    cmd_obs,
    cmd_pr,
    cmd_review,
    create_parser,
)
from motdd.config import Config
from motdd.ui.cli_mode import CLIMode


def test_create_parser():
    """Test argument parser creation."""
    parser = create_parser()
    assert parser is not None

    # Test default command
    args = parser.parse_args([])
    assert args.command == "all"
    assert not args.interactive
    assert not args.verbose
    assert not args.debug
    assert not args.clear_cache
    assert args.repo is None

    # Test all command
    args = parser.parse_args(["all"])
    assert args.command == "all"

    # Test notifications command
    args = parser.parse_args(["notifications"])
    assert args.command == "notifications"

    # Test review command
    args = parser.parse_args(["review"])
    assert args.command == "review"

    # Test pr command
    args = parser.parse_args(["pr"])
    assert args.command == "pr"
    assert args.args == []

    # Test pr command with username
    args = parser.parse_args(["pr", "@torvalds"])
    assert args.command == "pr"
    assert args.args == ["@torvalds"]

    # Test obs command
    args = parser.parse_args(["obs"])
    assert args.command == "obs"

    # Test ibs command
    args = parser.parse_args(["ibs"])
    assert args.command == "ibs"

    # Test init command
    args = parser.parse_args(["init"])
    assert args.command == "init"

    # Test flags
    args = parser.parse_args(["-i", "all"])
    assert args.interactive
    assert args.command == "all"

    args = parser.parse_args(["--verbose", "all"])
    assert args.verbose

    args = parser.parse_args(["--debug", "all"])
    assert args.debug

    args = parser.parse_args(["--clear-cache", "all"])
    assert args.clear_cache

    args = parser.parse_args(["--repo", "owner/repo", "all"])
    assert args.repo == "owner/repo"


@pytest.mark.asyncio
async def test_cmd_init(tmp_path):
    """Test init command."""
    config_path = tmp_path / "test_motdd.toml"

    with patch("motdd.config.Config.save_template", return_value=config_path):
        config = Config()
        result = await cmd_init(config)

    assert result == 0


@pytest.mark.asyncio
async def test_cmd_all():
    """Test all command."""
    cli_mode = MagicMock(spec=CLIMode)
    cli_mode.show_all = AsyncMock()

    result = await cmd_all(cli_mode)

    assert result == 0
    cli_mode.show_all.assert_awaited_once()


@pytest.mark.asyncio
async def test_cmd_notifications():
    """Test notifications command."""
    cli_mode = MagicMock(spec=CLIMode)
    cli_mode.show_notifications = AsyncMock()

    result = await cmd_notifications(cli_mode)

    assert result == 0
    cli_mode.show_notifications.assert_awaited_once()


@pytest.mark.asyncio
async def test_cmd_review():
    """Test review command."""
    cli_mode = MagicMock(spec=CLIMode)
    cli_mode.show_reviews = AsyncMock()

    result = await cmd_review(cli_mode)

    assert result == 0
    cli_mode.show_reviews.assert_awaited_once()


@pytest.mark.asyncio
async def test_cmd_pr_no_args():
    """Test pr command with no arguments."""
    cli_mode = MagicMock(spec=CLIMode)
    cli_mode.show_my_prs = AsyncMock()

    result = await cmd_pr(cli_mode, [])

    assert result == 0
    cli_mode.show_my_prs.assert_awaited_once()


@pytest.mark.asyncio
async def test_cmd_pr_with_username():
    """Test pr command with @username."""
    cli_mode = MagicMock(spec=CLIMode)
    cli_mode.show_user_prs = AsyncMock()

    # @username format
    result = await cmd_pr(cli_mode, ["@torvalds"])
    assert result == 0
    cli_mode.show_user_prs.assert_awaited_once_with("torvalds", None)

    cli_mode.reset_mock()

    # provider@username format - note: show_user_prs(username, provider)
    result = await cmd_pr(cli_mode, ["github@torvalds"])
    assert result == 0
    cli_mode.show_user_prs.assert_awaited_once_with("torvalds", "github")

    cli_mode.reset_mock()

    # @provider@username format
    result = await cmd_pr(cli_mode, ["@github@torvalds"])
    assert result == 0
    cli_mode.show_user_prs.assert_awaited_once_with("torvalds", "github")

    cli_mode.reset_mock()

    # Plain username (no @)
    result = await cmd_pr(cli_mode, ["torvalds"])
    assert result == 0
    cli_mode.show_user_prs.assert_awaited_once_with("torvalds", None)


@pytest.mark.asyncio
async def test_cmd_obs():
    """Test obs command."""
    cli_mode = MagicMock(spec=CLIMode)
    cli_mode.show_obs = AsyncMock()

    result = await cmd_obs(cli_mode)

    assert result == 0
    cli_mode.show_obs.assert_awaited_once()


@pytest.mark.asyncio
async def test_cmd_ibs():
    """Test ibs command."""
    cli_mode = MagicMock(spec=CLIMode)
    cli_mode.show_ibs = AsyncMock()

    result = await cmd_ibs(cli_mode)

    assert result == 0
    cli_mode.show_ibs.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_main_init(tmp_path):
    """Test async_main with init command."""
    config_path = tmp_path / "test_motdd.toml"

    with (
        patch("sys.argv", ["motdd", "init"]),
        patch("motdd.config.Config.save_template", return_value=config_path),
    ):
        result = await async_main()

    assert result == 0


@pytest.mark.asyncio
async def test_async_main_all_command(tmp_path):
    """Test async_main with all command."""
    config_path = tmp_path / "motdd.toml"
    config_path.write_text("""
[general]
default_provider = "github"
    """)

    with (
        patch("sys.argv", ["motdd", "--config", str(config_path), "all"]),
        patch("motdd.ui.cli_mode.CLIMode.show_all", new_callable=AsyncMock),
    ):
        result = await async_main()

    assert result == 0


@pytest.mark.asyncio
async def test_async_main_clear_cache(tmp_path):
    """Test async_main with --clear-cache flag."""
    config_path = tmp_path / "motdd.toml"
    config_path.write_text("""
[general]
default_provider = "github"
    """)

    with (
        patch("sys.argv", ["motdd", "--config", str(config_path), "--clear-cache", "all"]),
        patch("motdd.ui.cli_mode.CLIMode.show_all", new_callable=AsyncMock),
        patch("motdd.cache.Cache.clear") as mock_clear,
    ):
        result = await async_main()

    assert result == 0
    mock_clear.assert_called_once()


@pytest.mark.asyncio
async def test_async_main_verbose(tmp_path):
    """Test async_main with --verbose flag."""
    config_path = tmp_path / "motdd.toml"
    config_path.write_text("""
[general]
default_provider = "github"
    """)

    with (
        patch("sys.argv", ["motdd", "--config", str(config_path), "--verbose", "all"]),
        patch("motdd.ui.cli_mode.CLIMode.show_all", new_callable=AsyncMock),
    ):
        result = await async_main()

    assert result == 0


@pytest.mark.asyncio
async def test_async_main_repo_filter(tmp_path):
    """Test async_main with --repo filter."""
    config_path = tmp_path / "motdd.toml"
    config_path.write_text("""
[general]
default_provider = "github"
    """)

    with (
        patch("sys.argv", ["motdd", "--config", str(config_path), "--repo", "owner/repo", "all"]),
        patch("motdd.ui.cli_mode.CLIMode.show_all", new_callable=AsyncMock),
    ):
        result = await async_main()

    assert result == 0


@pytest.mark.asyncio
async def test_async_main_keyboard_interrupt(tmp_path):
    """Test async_main handles KeyboardInterrupt."""
    config_path = tmp_path / "motdd.toml"
    config_path.write_text("""
[general]
default_provider = "github"
    """)

    with (
        patch("sys.argv", ["motdd", "--config", str(config_path), "all"]),
        patch(
            "motdd.ui.cli_mode.CLIMode.show_all",
            new_callable=AsyncMock,
            side_effect=KeyboardInterrupt,
        ),
    ):
        result = await async_main()

    assert result == 130


@pytest.mark.asyncio
async def test_async_main_exception_debug(tmp_path):
    """Test async_main re-raises exceptions in debug mode."""
    config_path = tmp_path / "motdd.toml"
    config_path.write_text("""
[general]
default_provider = "github"
    """)

    with (
        patch("sys.argv", ["motdd", "--config", str(config_path), "--debug", "all"]),
        patch(
            "motdd.ui.cli_mode.CLIMode.show_all",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Test error"),
        ),
        pytest.raises(RuntimeError, match="Test error"),
    ):
        await async_main()


@pytest.mark.asyncio
async def test_async_main_exception_no_debug(tmp_path):
    """Test async_main catches exceptions without debug mode."""
    config_path = tmp_path / "motdd.toml"
    config_path.write_text("""
[general]
default_provider = "github"
    """)

    with (
        patch("sys.argv", ["motdd", "--config", str(config_path), "all"]),
        patch(
            "motdd.ui.cli_mode.CLIMode.show_all",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Test error"),
        ),
    ):
        result = await async_main()

    assert result == 1
