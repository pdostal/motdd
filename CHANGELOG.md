# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - TBD

Initial release of MOTDD - Message Of The Developer Day

### Added
- **Multi-platform Support**: GitHub, GitLab, Forgejo, Gitea, OBS, and IBS integration
- **Beautiful Terminal UI**: Rich formatting with colors, UTF-8 icons, and clickable links (OSC 8)
- **Interactive Mode**: Auto-refresh TUI with vim-style navigation (j/k keys)
- **Smart Caching**: Configurable TTL-based disk cache for improved performance
- **Color Themes**: Four built-in themes (default, light, solarized, nord)
- **Flexible Filtering**: By repository, date, and review status
- **TOML Configuration**: Multi-instance provider support with ~/.config/motdd.toml
- **CLI Commands**:
  - `motdd all` - Show all sections
  - `motdd notifications` - Show notifications only
  - `motdd review` - Show PRs to review and recently reviewed
  - `motdd pr` - Show your pull requests
  - `motdd pr @username` - Show PRs by specific user
  - `motdd pr provider@username` - Show PRs from specific provider
  - `motdd obs/ibs` - Show OBS/IBS build statuses
  - `motdd init` - Generate configuration template
- **Options**: --interactive, --repo, --clear-cache, --verbose, --debug
- **Provider Support**: Uses CLI tools (gh, glab, fj, tea, osc) for authentication
- **Async Design**: Parallel API calls using asyncio for faster data fetching

### Testing
- 81 comprehensive tests with 62% code coverage
- Core modules at 85-100% coverage:
  - config.py: 97%
  - formatter.py: 96%
  - utils.py: 91%
  - cache.py: 85%
  - __main__.py: 83%
  - models.py: 100%
  - themes.py: 100%

### Documentation
- Comprehensive README with installation, usage, and configuration guide
- Development guide in CLAUDE.md
- Example configuration file
- Status icons reference
- Terminal compatibility notes

### Infrastructure
- Project setup with uv for dependency management
- GitHub Actions workflows for CI/CD
- Git hooks (pre-commit formatting, commit-msg validation)
- Conventional commit format enforcement
- MIT License

[Unreleased]: https://github.com/pdostal/motdd/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/pdostal/motdd/releases/tag/v1.0.0
