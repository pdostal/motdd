"""Tests for configuration management."""

from pathlib import Path
from tempfile import TemporaryDirectory

from motdd.config import Config


def test_config_defaults() -> None:
    """Test configuration with default values."""
    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "motdd.toml"
        config = Config(config_path=config_path)

        assert config.get_default_provider() == "github"
        assert config.get_theme() == "default"
        assert config.get_cache_ttl() == 300
        assert config.get_recent_activity_days() == 30
        assert config.get_reviewed_prs_days() == 5


def test_config_loading() -> None:
    """Test loading configuration from file."""
    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "motdd.toml"

        # Write config file
        config_path.write_text("""
[general]
default_provider = "gitlab"
theme = "nord"
cache_ttl_seconds = 600

[[providers.github]]
name = "github"
host = "github.com"

[[providers.gitlab]]
name = "gitlab"
host = "gitlab.com"
""")

        config = Config(config_path=config_path)

        assert config.get_default_provider() == "gitlab"
        assert config.get_theme() == "nord"
        assert config.get_cache_ttl() == 600


def test_config_providers() -> None:
    """Test provider configuration."""
    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "motdd.toml"

        config_path.write_text("""
[[providers.github]]
name = "github"
host = "github.com"
cli_tool = "gh"

[[providers.github]]
name = "github-enterprise"
host = "github.company.com"
cli_tool = "gh"

[[providers.gitlab]]
name = "gitlab"
host = "gitlab.com"
cli_tool = "glab"
""")

        config = Config(config_path=config_path)

        # Get all GitHub providers
        github_providers = config.get_providers("github")
        assert len(github_providers) == 2
        assert github_providers[0]["name"] == "github"
        assert github_providers[1]["name"] == "github-enterprise"

        # Get all providers
        all_providers = config.get_providers()
        assert len(all_providers) == 3


def test_config_get_with_dot_notation() -> None:
    """Test get() with dot notation."""
    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "motdd.toml"

        config_path.write_text("""
[general]
theme = "solarized"

[interactive]
refresh_interval_seconds = 120
""")

        config = Config(config_path=config_path)

        assert config.get("general.theme") == "solarized"
        assert config.get("interactive.refresh_interval_seconds") == 120
        assert config.get("nonexistent.key", default="default_value") == "default_value"


def test_config_interactive_settings() -> None:
    """Test interactive mode settings."""
    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "motdd.toml"

        config_path.write_text("""
[interactive]
refresh_interval_seconds = 600
enable_vim_keys = false
enable_quick_actions = false
""")

        config = Config(config_path=config_path)

        assert config.get_refresh_interval() == 600
        assert config.enable_vim_keys() is False
        assert config.enable_quick_actions() is False


def test_config_template_generation() -> None:
    """Test configuration template generation."""
    template = Config.generate_template()

    assert "general" in template
    assert "providers.github" in template
    assert "interactive" in template
    assert "default_provider" in template


def test_config_save_template() -> None:
    """Test saving configuration template."""
    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "motdd.toml"
        config = Config(config_path=config_path)

        saved_path = config.save_template()

        assert saved_path.exists()
        content = saved_path.read_text()
        assert "[general]" in content
        assert "[[providers.github]]" in content
