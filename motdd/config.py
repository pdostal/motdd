"""Configuration management for MOTDD."""

import tomllib
from pathlib import Path
from typing import Any


class ConfigError(Exception):
    """Configuration error."""

    pass


class Config:
    """Configuration manager."""

    DEFAULT_CONFIG_PATH = Path.home() / ".config" / "motdd.toml"

    DEFAULT_VALUES = {
        "general": {
            "default_provider": "github",
            "recent_activity_days": 30,
            "reviewed_prs_days": 5,
            "cache_ttl_seconds": 300,
            "theme": "default",
        },
        "interactive": {
            "refresh_interval_seconds": 300,
            "enable_vim_keys": True,
            "enable_quick_actions": True,
        },
    }

    def __init__(self, config_path: Path | None = None, auto_detect: bool = True):
        """
        Initialize configuration.

        Args:
            config_path: Path to config file (defaults to ~/.config/motdd.toml)
            auto_detect: If True and config file doesn't exist, auto-detect providers
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.auto_detected = False
        self.data: dict[str, Any] = {}
        self._load(auto_detect=auto_detect)

    def _load(self, auto_detect: bool = True) -> None:
        """Load configuration from file (auto-detection handled separately)."""
        if not self.config_path.exists():
            # Use default configuration (no providers)
            # Auto-detection will be handled by load_with_autodetect() if needed
            self.data = self.DEFAULT_VALUES.copy()
            return

        try:
            with open(self.config_path, "rb") as f:
                loaded_data = tomllib.load(f)

            # Merge with defaults
            self.data = self._merge_with_defaults(loaded_data)

        except Exception as e:
            raise ConfigError(f"Failed to load config from {self.config_path}: {e}")

    async def load_with_autodetect(self) -> None:
        """Auto-detect and load providers if config file doesn't exist."""
        if self.config_path.exists():
            return  # Config already loaded from file

        try:
            from motdd.detector import detect_authenticated_providers

            detected = await detect_authenticated_providers()
            self.data["providers"] = detected
            self.auto_detected = True
        except Exception as e:
            import logging

            logging.getLogger(__name__).warning(f"Auto-detection failed: {e}, using defaults")

    def _merge_with_defaults(self, loaded_data: dict) -> dict:
        """Merge loaded data with default values."""
        result = self.DEFAULT_VALUES.copy()

        # Update general settings
        if "general" in loaded_data:
            result["general"].update(loaded_data["general"])

        # Update interactive settings
        if "interactive" in loaded_data:
            result["interactive"].update(loaded_data["interactive"])

        # Add providers
        if "providers" in loaded_data:
            result["providers"] = loaded_data["providers"]
        else:
            result["providers"] = {}

        return result

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key (supports dot notation like 'general.theme')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self.data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_providers(self, provider_type: str | None = None) -> list[dict]:
        """
        Get provider configurations.

        Args:
            provider_type: Optional provider type to filter (github, gitlab, etc.)

        Returns:
            List of provider configurations
        """
        providers_config = self.data.get("providers", {})

        if provider_type:
            return providers_config.get(provider_type, [])

        # Return all providers
        all_providers = []
        for ptype, plist in providers_config.items():
            if isinstance(plist, list):
                for provider in plist:
                    provider["type"] = ptype
                    all_providers.append(provider)

        return all_providers

    def get_theme(self) -> str:
        """Get configured theme name."""
        return self.get("general.theme", "default")

    def get_cache_ttl(self) -> int:
        """Get cache TTL in seconds."""
        return self.get("general.cache_ttl_seconds", 300)

    def get_default_provider(self) -> str:
        """Get default provider name."""
        return self.get("general.default_provider", "github")

    def get_recent_activity_days(self) -> int:
        """Get recent activity threshold in days."""
        return self.get("general.recent_activity_days", 30)

    def get_reviewed_prs_days(self) -> int:
        """Get reviewed PRs threshold in days."""
        return self.get("general.reviewed_prs_days", 7)

    def get_refresh_interval(self) -> int:
        """Get interactive mode refresh interval in seconds."""
        return self.get("interactive.refresh_interval_seconds", 300)

    def enable_vim_keys(self) -> bool:
        """Check if vim keys are enabled."""
        return self.get("interactive.enable_vim_keys", True)

    def enable_quick_actions(self) -> bool:
        """Check if quick actions are enabled."""
        return self.get("interactive.enable_quick_actions", True)

    @staticmethod
    def generate_template() -> str:
        """
        Generate a template configuration file.

        Returns:
            Template configuration as string
        """
        return """# MOTDD Configuration File
# See https://github.com/pdostal/motdd for full documentation

[general]
# Default provider for @username syntax
default_provider = "github"

# Number of days to consider for "recent" activity filtering
recent_activity_days = 30

# Number of days to show already-reviewed PRs
reviewed_prs_days = 5

# Cache TTL in seconds (default: 5 minutes)
cache_ttl_seconds = 300

# Color theme: default, light, solarized, nord
theme = "default"

# GitHub configuration (supports multiple instances)
[[providers.github]]
name = "github"
host = "github.com"
cli_tool = "gh"

# Example: GitHub Enterprise
# [[providers.github]]
# name = "github-enterprise"
# host = "github.company.com"
# cli_tool = "gh"

# GitLab configuration
[[providers.gitlab]]
name = "gitlab"
host = "gitlab.com"
cli_tool = "glab"

# Example: Self-hosted GitLab
# [[providers.gitlab]]
# name = "gitlab-selfhosted"
# host = "gitlab.internal.com"
# cli_tool = "glab"

# Forgejo configuration
# [[providers.forgejo]]
# name = "forgejo"
# host = "git.forgejo.org"
# cli_tool = "fj"

# Gitea configuration
# [[providers.gitea]]
# name = "gitea"
# host = "gitea.io"
# cli_tool = "tea"

# OBS (OpenBuildService) configuration
# [[providers.obs]]
# name = "obs"
# api_url = "https://api.opensuse.org"
# cli_tool = "osc"

# IBS (Internal Build Service - SUSE)
# [[providers.ibs]]
# name = "ibs"
# api_url = "https://api.suse.de"
# cli_tool = "osc"

# Interactive mode settings
[interactive]
# Auto-refresh interval in seconds (default: 5 minutes)
refresh_interval_seconds = 300

# Enable vim-style navigation keys (j/k)
enable_vim_keys = true

# Enable quick actions in detail view
enable_quick_actions = true
"""

    def save_template(self, path: Path | None = None) -> Path:
        """
        Save template configuration file.

        Args:
            path: Path to save template (defaults to ~/.config/motdd.toml)

        Returns:
            Path where template was saved
        """
        save_path = path or self.config_path
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "w") as f:
            f.write(self.generate_template())

        return save_path

    def save_with_detected_providers(
        self, providers: dict[str, list[dict[str, Any]]], path: Path | None = None
    ) -> Path:
        """
        Save configuration file with auto-detected providers.

        Args:
            providers: Dict mapping provider types to list of provider configs
            path: Path to save config (defaults to ~/.config/motdd.toml)

        Returns:
            Path where config was saved
        """
        save_path = path or self.config_path
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Start with general settings
        config_lines = [
            "# MOTDD Configuration File (Auto-Generated)",
            "# See https://github.com/pdostal/motdd for full documentation",
            "",
            "[general]",
            "# Default provider for @username syntax",
            'default_provider = "github"',
            "",
            '# Number of days to consider for "recent" activity filtering',
            "recent_activity_days = 30",
            "",
            "# Number of days to show already-reviewed PRs",
            "reviewed_prs_days = 5",
            "",
            "# Cache TTL in seconds (default: 5 minutes)",
            "cache_ttl_seconds = 300",
            "",
            "# Color theme: default, light, solarized, nord",
            'theme = "default"',
            "",
        ]

        # Add detected providers
        for provider_type, configs in providers.items():
            if not configs:
                continue

            config_lines.append(f"# {provider_type.capitalize()} configuration")
            for config in configs:
                config_lines.append(f"[[providers.{provider_type}]]")
                config_lines.append(f'name = "{config["name"]}"')
                if "host" in config:
                    config_lines.append(f'host = "{config["host"]}"')
                if "cli_tool" in config:
                    config_lines.append(f'cli_tool = "{config["cli_tool"]}"')
                if "api_url" in config:
                    config_lines.append(f'api_url = "{config["api_url"]}"')
                config_lines.append("")

        # Add interactive mode settings
        config_lines.extend(
            [
                "# Interactive mode settings",
                "[interactive]",
                "# Auto-refresh interval in seconds (default: 5 minutes)",
                "refresh_interval_seconds = 300",
                "",
                "# Enable vim-style navigation keys (j/k)",
                "enable_vim_keys = true",
                "",
                "# Enable quick actions in detail view",
                "enable_quick_actions = true",
                "",
            ]
        )

        with open(save_path, "w") as f:
            f.write("\n".join(config_lines))

        return save_path
