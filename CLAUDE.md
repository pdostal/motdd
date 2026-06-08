# MOTDD Development Guide

This file contains development guidelines and context for working on MOTDD.

## Project Overview

MOTDD (Message Of The Developer Day) is a unified dashboard CLI tool for developers working across multiple platforms. It aggregates notifications, pull requests, reviews, and build statuses from:

- GitHub (via `gh` CLI)
- GitLab (via `glab` CLI)
- Forgejo (via `fj` CLI)
- Gitea (via `tea` CLI)
- OBS/IBS (via `osc` CLI)

## Architecture

### Core Principles

- **Stateless**: No database, uses disk cache for performance
- **CLI-first**: Leverages existing CLI tools for authentication and API access
- **Async**: Parallel API calls for speed
- **Configurable**: TOML config file with multiple provider instances
- **Testable**: Comprehensive test suite with >80% coverage target

### Project Structure

```
motdd/
├── motdd/
│   ├── __init__.py           # Package initialization
│   ├── __main__.py           # CLI entry point (TODO)
│   ├── config.py             # ✅ TOML configuration management
│   ├── cache.py              # ✅ Disk cache with TTL
│   ├── models.py             # ✅ Data models (Notification, PullRequest, BuildStatus)
│   ├── utils.py              # ✅ Helper functions (icons, links, filtering)
│   ├── providers/
│   │   ├── base.py           # TODO: Abstract provider interface
│   │   ├── github.py         # TODO: GitHub integration
│   │   ├── gitlab.py         # TODO: GitLab integration
│   │   ├── forgejo.py        # TODO: Forgejo integration
│   │   ├── gitea.py          # TODO: Gitea integration
│   │   ├── obs.py            # TODO: OBS integration
│   │   └── ibs.py            # TODO: IBS integration
│   └── ui/
│       ├── themes.py         # TODO: Color themes
│       ├── formatter.py      # TODO: Rich renderables
│       ├── cli_mode.py       # TODO: Static CLI output
│       └── interactive.py    # TODO: Textual TUI
└── tests/
    ├── test_config.py        # ✅ Config tests
    ├── test_cache.py         # ✅ Cache tests
    ├── test_models.py        # ✅ Model tests
    ├── test_utils.py         # ✅ Utils tests
    └── fixtures/             # TODO: Mock API responses
```

## Development Workflow

### Running Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=motdd --cov-report=term-missing

# Specific test file
uv run pytest tests/test_config.py -v
```

### Linting and Formatting

```bash
# Format code
uv run black motdd tests

# Lint
uv run ruff check motdd tests

# Type check
uv run mypy motdd
```

### Git Hooks

The project uses git hooks in `.githooks/`:
- `pre-commit`: Runs black and ruff before commits
- `commit-msg`: Validates conventional commit format

### Commit Message Format

Follow conventional commits:
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `test:` - Test additions/changes
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

## Implementation Status

### ✅ Completed (Phases 1-2)

- [x] Project setup with uv
- [x] Git hooks and CI/CD workflows
- [x] Configuration management (TOML)
- [x] Caching system with TTL
- [x] Data models with serialization
- [x] Utility functions (icons, filtering, links)
- [x] Comprehensive test suite (87% coverage)

### 🚧 In Progress (Phase 3)

- [ ] Provider base class and interface
- [ ] GitHub provider implementation
- [ ] GitLab provider implementation
- [ ] Forgejo provider implementation
- [ ] Gitea provider implementation
- [ ] OBS/IBS provider implementations
- [ ] Provider tests with fixtures

### 📋 TODO (Phases 4-9)

- Phase 4: UI Implementation (themes, formatters, CLI mode)
- Phase 5: Interactive Mode (textual TUI, navigation, quick actions)
- Phase 6: CLI Interface (argparse, command wiring)
- Phase 7: Testing (comprehensive coverage)
- Phase 8: Documentation & Polish
- Phase 9: Release Preparation (PyPI publishing)

## Key Design Decisions

### Why CLI tools instead of API libraries?

- Leverage existing authentication (`gh auth`, `glab auth`, etc.)
- No token management in config
- CLI tools handle API versioning
- Simpler error handling

### Why disk cache?

- Improve responsiveness (5-10s API calls → instant)
- Reduce API rate limit usage
- User control via `--clear-cache`
- Conservative: prefer fresh data over stale

### Why TOML config?

- More structured than bash variables
- Native Python 3.11+ support
- Comments in config file
- Industry standard for Python projects

### Why Python 3.11+?

- Native `tomllib` support
- Modern type hints (PEP 604: `X | Y` syntax)
- Better error messages
- Performance improvements

## Provider Integration Guidelines

Each provider must implement the `BaseProvider` interface:

```python
async def get_notifications() -> List[Notification]
async def get_my_prs() -> List[PullRequest]
async def get_prs_to_review() -> List[PullRequest]
async def get_reviewed_prs(days: int) -> List[PullRequest]
async def get_user_prs(username: str) -> List[PullRequest]
async def mark_notification_read(notification_id: str)
async def approve_pr(pr_id: str)
async def comment_on_pr(pr_id: str, comment: str)
async def request_changes(pr_id: str, comment: str)
async def merge_pr(pr_id: str)
```

### Provider Implementation Checklist

- [ ] Call CLI tool via `asyncio.create_subprocess_exec()`
- [ ] Parse JSON output (most tools support `--json`)
- [ ] Implement rate limit detection and retry
- [ ] Handle errors gracefully
- [ ] Cache responses appropriately
- [ ] Write integration tests with fixtures

## Testing Strategy

- **Unit tests**: Core logic (config, cache, models, utils)
- **Integration tests**: Provider API calls with mocked responses
- **Fixtures**: Sample JSON outputs from each CLI tool
- **Coverage goal**: >80% overall

## UI Guidelines

### Static CLI Mode

- Use `rich` for rendering
- Sections as `Panel` widgets
- Tables for lists
- OSC 8 hyperlinks with fallback
- Terminal width auto-detection

### Interactive Mode

- Use `textual` for TUI
- Vim-style navigation (j/k) + arrows
- Auto-refresh with countdown
- Quick actions in detail view
- Visual feedback for async operations

### Color Themes

Available themes: `default`, `light`, `solarized`, `nord`

Each theme defines:
- Status colors (success, warning, error, info)
- UI elements (header, border, highlight)
- PR states (open, merged, closed, draft)

## Release Process

1. Update CHANGELOG.md (automated via git-cliff)
2. Tag version: `git tag v1.0.0`
3. Push tag: `git push --tags`
4. GitHub Actions automatically:
   - Runs tests and linters
   - Builds package
   - Creates GitHub Release
   - Publishes to PyPI

## Useful Commands

```bash
# Install dependencies
uv sync --all-extras

# Run locally
uv run motdd --help

# Build package
uv build

# Clear cache
rm -rf ~/.cache/motdd/
```

## Getting Help

- Issues: https://github.com/pdostal/motdd/issues
- Discussions: https://github.com/pdostal/motdd/discussions
- Author: Pavel Dostal (pdostal@pdostal.cz)
