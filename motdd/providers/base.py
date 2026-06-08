"""Base provider class for all integrations."""

import asyncio
import json
import logging
import shutil
from abc import ABC, abstractmethod

from motdd.models import BuildStatus, Notification, PullRequest

logger = logging.getLogger(__name__)


class ProviderError(Exception):
    """Provider-specific error."""

    pass


class BaseProvider(ABC):
    """Abstract base class for all providers."""

    def __init__(self, name: str, config: dict):
        """
        Initialize provider.

        Args:
            name: Provider instance name
            config: Provider configuration from TOML
        """
        self.name = name
        self.config = config
        self.cli_tool = config.get("cli_tool", "")

    def _check_cli_available(self) -> bool:
        """
        Check if CLI tool is available.

        Returns:
            True if CLI tool is found in PATH
        """
        return shutil.which(self.cli_tool) is not None

    async def _run_command(
        self,
        args: list[str],
        timeout: int = 30,
        check_json: bool = True,
    ) -> dict | list | str:
        """
        Run CLI command and return output.

        Args:
            args: Command arguments (CLI tool will be prepended)
            timeout: Command timeout in seconds
            check_json: If True, parse output as JSON

        Returns:
            Command output (parsed JSON or raw string)

        Raises:
            ProviderError: If command fails or times out
        """
        if not self._check_cli_available():
            raise ProviderError(f"CLI tool '{self.cli_tool}' not found in PATH")

        cmd = [self.cli_tool] + args

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
            except TimeoutError:
                process.kill()
                raise ProviderError(f"Command timed out after {timeout}s: {' '.join(cmd)}")

            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                raise ProviderError(f"Command failed with code {process.returncode}: {error_msg}")

            output = stdout.decode().strip()

            if check_json and output:
                try:
                    return json.loads(output)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON output: {e}")
                    raise ProviderError(f"Invalid JSON output: {e}")

            return output

        except FileNotFoundError:
            raise ProviderError(f"CLI tool '{self.cli_tool}' not found")
        except Exception as e:
            if isinstance(e, ProviderError):
                raise
            raise ProviderError(f"Command execution failed: {e}")

    @abstractmethod
    async def get_notifications(self) -> list[Notification]:
        """
        Get notifications.

        Returns:
            List of notifications
        """
        pass

    @abstractmethod
    async def get_my_prs(self) -> list[PullRequest]:
        """
        Get my pull requests.

        Returns:
            List of pull requests
        """
        pass

    @abstractmethod
    async def get_prs_to_review(self) -> list[PullRequest]:
        """
        Get pull requests to review.

        Returns:
            List of pull requests needing review
        """
        pass

    async def get_reviewed_prs(self, days: int = 7) -> list[PullRequest]:
        """
        Get recently reviewed pull requests.

        Args:
            days: Number of days to look back

        Returns:
            List of reviewed pull requests
        """
        # Default implementation - providers can override
        return []

    async def get_user_prs(self, username: str) -> list[PullRequest]:
        """
        Get pull requests for a specific user.

        Args:
            username: Username to query

        Returns:
            List of pull requests
        """
        # Default implementation - providers can override
        return []

    async def mark_notification_read(self, notification_id: str) -> None:
        """
        Mark notification as read.

        Args:
            notification_id: Notification ID
        """
        # Default implementation - providers can override
        pass

    async def approve_pr(self, pr_id: str) -> None:
        """
        Approve a pull request.

        Args:
            pr_id: Pull request ID
        """
        # Default implementation - providers can override
        raise NotImplementedError(f"{self.name} does not support approving PRs")

    async def comment_on_pr(self, pr_id: str, comment: str) -> None:
        """
        Add comment to pull request.

        Args:
            pr_id: Pull request ID
            comment: Comment text
        """
        # Default implementation - providers can override
        raise NotImplementedError(f"{self.name} does not support commenting on PRs")

    async def request_changes(self, pr_id: str, comment: str) -> None:
        """
        Request changes on pull request.

        Args:
            pr_id: Pull request ID
            comment: Comment text
        """
        # Default implementation - providers can override
        raise NotImplementedError(f"{self.name} does not support requesting changes")

    async def merge_pr(self, pr_id: str) -> None:
        """
        Merge a pull request.

        Args:
            pr_id: Pull request ID
        """
        # Default implementation - providers can override
        raise NotImplementedError(f"{self.name} does not support merging PRs")


class BuildProvider(BaseProvider):
    """Base class for build service providers (OBS/IBS)."""

    @abstractmethod
    async def get_submit_requests(self) -> list[BuildStatus]:
        """
        Get submit requests.

        Returns:
            List of submit requests
        """
        pass

    @abstractmethod
    async def get_builds(self) -> list[BuildStatus]:
        """
        Get build statuses.

        Returns:
            List of build statuses
        """
        pass

    async def get_incidents(self) -> list[BuildStatus]:
        """
        Get maintenance incidents.

        Returns:
            List of incidents
        """
        # Default implementation - providers can override
        return []

    # Build providers don't have notifications/PRs
    async def get_notifications(self) -> list[Notification]:
        """Build providers don't have notifications."""
        return []

    async def get_my_prs(self) -> list[PullRequest]:
        """Build providers don't have PRs."""
        return []

    async def get_prs_to_review(self) -> list[PullRequest]:
        """Build providers don't have PRs."""
        return []
