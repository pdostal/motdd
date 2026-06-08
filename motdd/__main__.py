"""MOTDD CLI entry point."""

import argparse
import asyncio
import sys
from pathlib import Path

from motdd import __version__
from motdd.cache import Cache
from motdd.config import Config
from motdd.ui.cli_mode import CLIMode
from motdd.ui.interactive import run_interactive


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="motdd",
        description="Message Of The Developer Day - unified dashboard for developers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  motdd all                    Show all sections
  motdd notifications          Show notifications only
  motdd review                 Show PRs to review
  motdd pr                     Show my PRs
  motdd pr @username           Show PRs by username (default provider)
  motdd pr github@username     Show PRs by username from GitHub
  motdd obs                    Show OBS submit requests and builds
  motdd ibs                    Show IBS submit requests and builds
  motdd init                   Generate config template
  motdd -i all                 Interactive mode

For more information: https://github.com/pdostal/motdd
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Run in interactive mode with auto-refresh",
    )

    parser.add_argument(
        "--config",
        type=Path,
        help="Path to config file (default: ~/.config/motdd.toml)",
    )

    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear cache before running",
    )

    parser.add_argument(
        "--repo",
        type=str,
        metavar="ORG/REPO",
        help="Filter by repository (e.g., owner/repo)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output",
    )

    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto-detect authenticated CLI tools (use with init command)",
    )

    # Subcommands
    parser.add_argument(
        "command",
        nargs="?",
        choices=["all", "notifications", "review", "pr", "obs", "ibs", "init"],
        default="all",
        help="Command to run (default: all)",
    )

    parser.add_argument(
        "args",
        nargs="*",
        help="Additional arguments for the command",
    )

    return parser


async def cmd_init(config: Config, auto: bool = False) -> int:
    """Initialize configuration file."""
    if auto:
        # Auto-detect and save providers
        from motdd.detector import detect_authenticated_providers

        detected = await detect_authenticated_providers()
        total_providers = sum(len(v) for v in detected.values())

        if total_providers == 0:
            print("No authenticated CLI tools detected.", file=sys.stderr)
            print("\nMake sure you have authenticated with at least one CLI tool:")
            print("  gh auth login      # GitHub")
            print("  glab auth login    # GitLab")
            print("  osc                # OBS/IBS (interactive setup)")
            print("  tea login          # Gitea")
            return 1

        config_path = config.save_with_detected_providers(detected)
        print(f"Created config at: {config_path}")
        print(f"\nAuto-detected {total_providers} authenticated provider(s):")
        for provider_type, configs in detected.items():
            for cfg in configs:
                host = cfg.get("host", cfg.get("api_url", ""))
                print(f"  - {provider_type}: {cfg['name']} ({host})")
        print("\nYou can now run:")
        print("  motdd all")
        return 0
    else:
        # Create template
        config_path = config.save_template()
        print(f"Created config template at: {config_path}")
        print("\nEdit the config file to add your provider settings, then run:")
        print("  motdd all")
        print("\nTip: Use 'motdd init --auto' to auto-detect authenticated CLI tools")
        return 0


async def cmd_all(cli_mode: CLIMode) -> int:
    """Show all sections."""
    await cli_mode.show_all()
    return 0


async def cmd_notifications(cli_mode: CLIMode) -> int:
    """Show notifications."""
    await cli_mode.show_notifications()
    return 0


async def cmd_review(cli_mode: CLIMode) -> int:
    """Show review requests."""
    await cli_mode.show_reviews()
    return 0


async def cmd_pr(cli_mode: CLIMode, args: list[str]) -> int:
    """Show pull requests."""
    if not args:
        # Show my PRs
        await cli_mode.show_my_prs()
    else:
        # Parse user argument: [@provider]@username or @username
        user_arg = args[0]

        if "@" in user_arg:
            parts = user_arg.split("@")
            if len(parts) == 2 and parts[0] == "":
                # @username (default provider)
                username = parts[1]
                provider = None
            elif len(parts) == 3 and parts[0] == "":
                # @provider@username
                provider = parts[1]
                username = parts[2]
            elif len(parts) == 2:
                # provider@username
                provider = parts[0]
                username = parts[1]
            else:
                # Shouldn't happen, but default to treating as plain username
                username = user_arg
                provider = None

            await cli_mode.show_user_prs(username, provider)
        else:
            # Assume it's just a username
            await cli_mode.show_user_prs(user_arg, None)

    return 0


async def cmd_obs(cli_mode: CLIMode) -> int:
    """Show OBS data."""
    await cli_mode.show_obs()
    return 0


async def cmd_ibs(cli_mode: CLIMode) -> int:
    """Show IBS data."""
    await cli_mode.show_ibs()
    return 0


async def async_main() -> int:
    """Async main function."""
    parser = create_parser()
    args = parser.parse_args()

    # Configure logging based on verbosity
    import logging

    if args.debug:
        # Debug mode: show all logs including DEBUG
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    elif args.verbose:
        # Verbose mode: show INFO and above
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    else:
        # Normal mode: suppress ERROR and below (only show CRITICAL)
        logging.basicConfig(level=logging.CRITICAL)

    # Load config
    try:
        config = Config(config_path=args.config, auto_detect=False)
    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        print("\nRun 'motdd init' to create a config file.", file=sys.stderr)
        return 1

    # Handle init command specially (doesn't need cache or CLI mode)
    if args.command == "init":
        return await cmd_init(config, auto=args.auto)

    # Auto-detect providers if no config file exists
    if not config.config_path.exists():
        await config.load_with_autodetect()

    # Set up cache
    cache = Cache(ttl_seconds=config.get_cache_ttl())

    if args.clear_cache:
        cache.clear()
        if args.verbose:
            print("Cache cleared")

    # Interactive mode
    if args.interactive:
        await run_interactive(config, repo_filter=args.repo, verbose=args.verbose)
        return 0

    # CLI mode
    cli_mode = CLIMode(
        config,
        cache=cache,
        repo_filter=args.repo,
        verbose=args.verbose or args.debug,
    )

    # Route to command handler
    command_map = {
        "all": cmd_all,
        "notifications": cmd_notifications,
        "review": cmd_review,
        "pr": cmd_pr,
        "obs": cmd_obs,
        "ibs": cmd_ibs,
    }

    handler = command_map.get(args.command)
    if not handler:
        parser.print_help()
        return 1

    try:
        # Some commands take additional args
        if args.command == "pr":
            return await handler(cli_mode, args.args)
        else:
            return await handler(cli_mode)
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        return 130
    except Exception as e:
        if args.debug:
            raise
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main() -> None:
    """Main entry point."""
    try:
        sys.exit(asyncio.run(async_main()))
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
