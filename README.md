# MOTDD - Message Of The Developer Day

> A unified dashboard CLI tool for developers working across multiple platforms

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code Coverage](https://img.shields.io/badge/coverage-62%25-yellow.svg)]()

MOTDD aggregates notifications, pull requests, reviews, and build statuses from multiple git hosting platforms and build systems into a single, colorful terminal interface. Stop switching between GitHub, GitLab, Forgejo, Gitea, OBS, and IBS—see everything in one place.

## Features

- 🌐 **Multi-Platform Support**: GitHub, GitLab, Forgejo, Gitea, OBS, IBS
- 🎨 **Beautiful Terminal UI**: Rich formatting with colors, icons, and clickable links
- 🔄 **Interactive Mode**: Auto-refresh with vim-style navigation
- ⚡ **Smart Caching**: Configurable TTL for fast responses
- 🎭 **Multiple Themes**: Default, Light, Solarized, Nord
- 🔍 **Flexible Filtering**: By repository, date, review status
- 🚀 **Stateless Design**: No database, uses existing CLI tool authentication
- 🔧 **Highly Configurable**: TOML-based configuration with multiple provider instances

## Quick Start

### Installation

```bash
# From PyPI (once published)
pip install motdd

# From source
git clone https://github.com/pdostal/motdd.git
cd motdd
uv sync
uv run motdd --version
```

### First Run

1. Generate a configuration template:
   ```bash
   motdd init
   ```

2. Edit `~/.config/motdd.toml` to add your providers

3. Run MOTDD:
   ```bash
   motdd all
   ```

## Usage

### Commands

```bash
# Show all sections (reviews, PRs, notifications, builds)
motdd all

# Show only notifications
motdd notifications

# Show PRs to review and recently reviewed
motdd review

# Show your pull requests
motdd pr

# Show PRs by a specific user (uses default provider)
motdd pr @username

# Show PRs by a specific user from a specific provider
motdd pr github@username

# Show OBS submit requests and builds
motdd obs

# Show IBS submit requests and builds
motdd ibs

# Generate config template
motdd init
```

### Interactive Mode

```bash
# Launch interactive TUI with auto-refresh
motdd -i all

# Keybindings in interactive mode:
# ↑↓ or j/k    Navigate
# r            Refresh now
# q            Quit
```

### Options

```bash
# Filter by repository
motdd --repo owner/repo all

# Clear cache before running
motdd --clear-cache all

# Verbose output
motdd --verbose all

# Use custom config file
motdd --config /path/to/config.toml all
```

## Configuration

MOTDD uses a TOML configuration file at `~/.config/motdd.toml`. Generate a template with `motdd init`.

### Example Configuration

```toml
[general]
default_provider = "github"
recent_activity_days = 30
reviewed_prs_days = 7
cache_ttl_seconds = 300
theme = "default"

# GitHub configuration
[[providers.github]]
name = "github"
host = "github.com"
cli_tool = "gh"

# GitLab configuration
[[providers.gitlab]]
name = "gitlab"
host = "gitlab.com"
cli_tool = "glab"

# Interactive mode settings
[interactive]
refresh_interval_seconds = 300
enable_vim_keys = true
```

See the [configuration guide](docs/configuration.md) for full details.

## Themes

MOTDD includes 4 built-in color themes:

- **default** - Bright colors for dark terminals
- **light** - Muted colors for light terminals
- **solarized** - Solarized Dark palette
- **nord** - Nord Arctic color scheme

Set your theme in `~/.config/motdd.toml`:
```toml
[general]
theme = "nord"
```

## Prerequisites

MOTDD leverages existing CLI tools for authentication. Install the tools for platforms you use:

### GitHub
```bash
brew install gh  # macOS
gh auth login
```

### GitLab
```bash
brew install glab  # macOS
glab auth login
```

### Forgejo/Gitea
```bash
# See https://code berg.org/forgejo/fj
# See https://gitea.com/gitea/tea
```

### OBS/IBS
```bash
zypper install osc  # openSUSE
# Configure in ~/.oscrc
```

## Status Icons

**Pull Requests:**
- 🟢 Approved / CI passing
- 🟡 Review required / CI pending
- 🔴 Changes requested / CI failed
- 🔵 Draft

**Build Status:**
- ✓ Succeeded
- ⏳ Building
- ✗ Failed

**Review Status:**
- ✓ Already reviewed
- ♺ Review restarted
- ⏳ Review pending

## Terminal Compatibility

Works best with modern terminal emulators:
- ✅ iTerm2, kitty, WezTerm, Alacritty - Full support with clickable links
- ⚠️ GNOME Terminal, Windows Terminal - Basic support

## Development

### Setup

```bash
git clone https://github.com/pdostal/motdd.git
cd motdd
uv sync --all-extras

# Run tests
uv run pytest --cov=motdd

# Format code
uv run black motdd tests

# Lint
uv run ruff check motdd tests
```

### Project Structure

```
motdd/
├── motdd/              # Source code
│   ├── providers/      # Platform integrations
│   └── ui/             # User interface
├── tests/              # Test suite (62% coverage)
├── pyproject.toml      # Project configuration
└── CLAUDE.md           # Development guide
```

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linters
5. Use conventional commits
6. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- **GitHub**: https://github.com/pdostal/motdd
- **Issues**: https://github.com/pdostal/motdd/issues
- **Author**: Pavel Dostal (pdostal@pdostal.cz)

---

**Note**: This project is under active development. Version 1.0 coming soon!
