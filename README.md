# MOTDD - Message Of The Developer Day

> A unified dashboard for developers working across multiple platforms

MOTDD aggregates your work from GitHub, GitLab, Forgejo, Gitea, and OBS/IBS into a single, beautiful terminal interface.

## Features

- 🎯 **Unified Dashboard** - See all your notifications, PRs, and reviews in one place
- 🎨 **Beautiful UI** - Color themes, UTF-8 icons, clickable links
- ⚡ **Fast** - Smart caching and parallel API calls
- 🔄 **Interactive Mode** - Auto-refresh, keyboard navigation, quick actions
- 🔧 **Highly Configurable** - TOML config file with multiple provider instances
- 🌈 **Multiple Themes** - Default, light, Solarized, Nord

## Installation

### Via pip (recommended)

```bash
pip install motdd
```

###From source

```bash
git clone https://github.com/pdostal/motdd.git
cd motdd
uv sync
uv run motdd --help
```

## Quick Start

1. Initialize configuration:
   ```bash
   motdd init
   ```

2. Edit `~/.config/motdd.toml` with your provider settings

3. Run MOTDD:
   ```bash
   # Show everything
   motdd all
   
   # Just notifications
   motdd notifications
   
   # PRs to review
   motdd review
   
   # Interactive mode
   motdd --interactive
   ```

## Usage

### Commands

- `motdd all` - Show all sections
- `motdd notifications` - Show notifications
- `motdd review` - Show PRs to review
- `motdd pr` - Show your PRs
- `motdd pr @username` - Show someone else's PRs
- `motdd pr provider@username` - Show PRs from specific provider
- `motdd obs` - Show OBS submit requests and builds
- `motdd ibs` - Show IBS submit requests and builds

### Flags

- `--interactive, -i` - Interactive mode with auto-refresh
- `--repo=org/name` - Filter by specific repository
- `--clear-cache` - Clear cache before running
- `--verbose` - Show API calls and timing
- `--debug` - Show full debug traces
- `--version` - Show version

## Configuration

Configuration is stored in `~/.config/motdd.toml`. Example:

```toml
[general]
default_provider = "github"
theme = "default"
cache_ttl_seconds = 300

[[providers.github]]
name = "github"
host = "github.com"
cli_tool = "gh"

[[providers.gitlab]]
name = "gitlab"
host = "gitlab.com"
cli_tool = "glab"
```

See [example config](docs/config.example.toml) for full documentation.

## Requirements

MOTDD uses CLI tools for authentication and API access:

- [gh](https://cli.github.com/) - GitHub CLI
- [glab](https://gitlab.com/gitlab-org/cli) - GitLab CLI
- [fj](https://codeberg.org/forgejo/forgejo-cli) - Forgejo CLI
- [tea](https://gitea.com/gitea/tea) - Gitea CLI
- [osc](https://github.com/openSUSE/osc) - OpenBuildService CLI

Install and authenticate the tools you need before using MOTDD.

## Development

```bash
# Clone repository
git clone https://github.com/pdostal/motdd.git
cd motdd

# Install dependencies
uv sync

# Run tests
uv run pytest

# Run linters
uv run ruff check .
uv run black .
uv run mypy motdd

# Run locally
uv run motdd --help
```

## License

MIT License - see [LICENSE](LICENSE) for details

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## Author

Created by [Pavel Dostal](https://github.com/pdostal)
