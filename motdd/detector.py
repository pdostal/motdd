"""Auto-detection of authenticated CLI tools."""

import asyncio
import logging
import shutil
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


async def _run_command(cmd: list[str]) -> tuple[str, str, int]:
    """
    Run a command and return (stdout, stderr, returncode).

    Args:
        cmd: Command and arguments as list

    Returns:
        Tuple of (stdout, stderr, returncode)
    """
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        return (
            stdout.decode("utf-8", errors="replace"),
            stderr.decode("utf-8", errors="replace"),
            process.returncode or 0,
        )
    except Exception as e:
        logger.debug(f"Command {cmd[0]} failed: {e}")
        return ("", "", 1)


async def _detect_github() -> list[dict[str, Any]]:
    """Detect authenticated GitHub instances via gh CLI."""
    if not shutil.which("gh"):
        logger.debug("gh CLI not found in PATH")
        return []

    stdout, stderr, returncode = await _run_command(["gh", "auth", "status"])
    output = stdout + stderr

    # Check for authentication success marker
    if "✓ Logged in to" not in output:
        logger.debug("gh CLI not authenticated")
        return []

    # Extract hostname (first line of output)
    lines = output.strip().split("\n")
    host = "github.com"
    if lines:
        # First line is usually the hostname
        first_line = lines[0].strip()
        if first_line and not first_line.startswith("✓"):
            host = first_line

    logger.info(f"Detected authenticated GitHub: {host}")
    return [{"name": "github", "host": host, "cli_tool": "gh"}]


async def _detect_gitlab() -> list[dict[str, Any]]:
    """Detect authenticated GitLab instances via glab CLI."""
    if not shutil.which("glab"):
        logger.debug("glab CLI not found in PATH")
        return []

    stdout, stderr, returncode = await _run_command(["glab", "auth", "status"])
    output = stdout + stderr

    # Check for authentication error markers
    if "x " in output and ("401" in output or "Unauthorized" in output):
        logger.debug("glab CLI not authenticated")
        return []

    # Extract hostname (first line of output)
    lines = output.strip().split("\n")
    host = "gitlab.com"
    if lines:
        first_line = lines[0].strip()
        if first_line and not first_line.startswith("✓") and not first_line.startswith("x"):
            host = first_line

    logger.info(f"Detected authenticated GitLab: {host}")
    return [{"name": "gitlab", "host": host, "cli_tool": "glab"}]


async def _detect_osc() -> dict[str, list[dict[str, Any]]]:
    """
    Detect authenticated OBS/IBS instances via osc CLI.

    Returns:
        Dict with "obs" and "ibs" keys, each containing list of configs
    """
    if not shutil.which("osc"):
        logger.debug("osc CLI not found in PATH")
        return {"obs": [], "ibs": []}

    stdout, stderr, returncode = await _run_command(["osc", "user"])
    output = stdout + stderr

    # Check for "not configured" message
    if "not configured" in output.lower():
        logger.debug("osc CLI not configured")
        return {"obs": [], "ibs": []}

    # Parse oscrc to find API URLs
    oscrc_path = Path.home() / ".config" / "osc" / "oscrc"
    obs_configs = []
    ibs_configs = []

    if oscrc_path.exists():
        try:
            content = oscrc_path.read_text()
            # Check for OBS and IBS API URLs in config
            if "api.opensuse.org" in content:
                obs_configs.append(
                    {
                        "name": "obs",
                        "cli_tool": "osc",
                        "api_url": "https://api.opensuse.org",
                    }
                )
                logger.info("Detected authenticated OBS")

            if "api.suse.de" in content:
                ibs_configs.append(
                    {
                        "name": "ibs",
                        "cli_tool": "osc",
                        "api_url": "https://api.suse.de",
                    }
                )
                logger.info("Detected authenticated IBS")

        except Exception as e:
            logger.debug(f"Failed to parse oscrc: {e}")

    return {"obs": obs_configs, "ibs": ibs_configs}


async def _detect_forgejo() -> list[dict[str, Any]]:
    """Detect authenticated Forgejo instances via fj CLI."""
    if not shutil.which("fj"):
        logger.debug("fj CLI not found in PATH")
        return []

    # Forgejo CLI detection is tool-dependent and may vary
    # Skip for now, users can manually configure
    logger.debug("Forgejo auto-detection not yet implemented")
    return []


async def _detect_gitea() -> list[dict[str, Any]]:
    """Detect authenticated Gitea instances via tea CLI."""
    if not shutil.which("tea"):
        logger.debug("tea CLI not found in PATH")
        return []

    stdout, stderr, returncode = await _run_command(["tea", "login", "list"])
    output = stdout + stderr

    # Check if there are any configured logins (table has data rows)
    # The output is a table, check for non-header content
    lines = output.strip().split("\n")
    # If there are more than 3 lines (header, separator, data), logins exist
    # Or check if output contains "│" and actual data
    has_logins = any(
        line.strip()
        and "│" in line
        and not line.startswith("┌")
        and not line.startswith("└")
        and "NAME" not in line
        for line in lines
    )

    if has_logins:
        logger.info("Detected authenticated Gitea")
        return [{"name": "gitea", "host": "gitea.io", "cli_tool": "tea"}]

    logger.debug("tea CLI not authenticated")
    return []


async def detect_authenticated_providers() -> dict[str, list[dict[str, Any]]]:
    """
    Auto-detect installed and authenticated CLI tools.

    Returns:
        Dict mapping provider types to list of provider configs:
        {
            "github": [{"name": "github", "host": "github.com", "cli_tool": "gh"}],
            "gitlab": [{"name": "gitlab", "host": "gitlab.com", "cli_tool": "glab"}],
            "obs": [{"name": "obs", "cli_tool": "osc", "api_url": "..."}],
            "ibs": [{"name": "ibs", "cli_tool": "osc", "api_url": "..."}],
            "forgejo": [],
            "gitea": [{"name": "gitea", "host": "gitea.io", "cli_tool": "tea"}]
        }
    """
    logger.debug("Starting auto-detection of authenticated providers")

    # Run all detections in parallel
    github_task = _detect_github()
    gitlab_task = _detect_gitlab()
    osc_task = _detect_osc()
    forgejo_task = _detect_forgejo()
    gitea_task = _detect_gitea()

    github, gitlab, osc, forgejo, gitea = await asyncio.gather(
        github_task,
        gitlab_task,
        osc_task,
        forgejo_task,
        gitea_task,
        return_exceptions=True,
    )

    # Handle exceptions
    if isinstance(github, Exception):
        logger.warning(f"GitHub detection failed: {github}")
        github = []
    if isinstance(gitlab, Exception):
        logger.warning(f"GitLab detection failed: {gitlab}")
        gitlab = []
    if isinstance(osc, Exception):
        logger.warning(f"OBS/IBS detection failed: {osc}")
        osc = {"obs": [], "ibs": []}
    if isinstance(forgejo, Exception):
        logger.warning(f"Forgejo detection failed: {forgejo}")
        forgejo = []
    if isinstance(gitea, Exception):
        logger.warning(f"Gitea detection failed: {gitea}")
        gitea = []

    providers = {
        "github": github,
        "gitlab": gitlab,
        "obs": osc["obs"],
        "ibs": osc["ibs"],
        "forgejo": forgejo,
        "gitea": gitea,
    }

    # Count detected providers
    total = sum(len(v) for v in providers.values())
    logger.info(f"Auto-detection complete: found {total} authenticated provider(s)")

    return providers
