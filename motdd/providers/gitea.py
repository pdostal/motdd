"""Gitea provider implementation."""

import logging
from datetime import datetime

from motdd.models import Notification, PullRequest
from motdd.providers.base import BaseProvider, ProviderError

logger = logging.getLogger(__name__)


class GiteaProvider(BaseProvider):
    """Gitea provider using tea CLI."""

    async def get_notifications(self) -> list[Notification]:
        """Get Gitea notifications."""
        try:
            # tea notifications list --mine
            data = await self._run_command(
                ["notifications", "list", "--mine", "--output", "json"],
                check_json=True,
            )

            if not isinstance(data, list):
                return []

            notifications = []
            for item in data:
                notif = Notification(
                    id=str(item.get("id", "")),
                    provider=self.name,
                    type=item.get("subject", {}).get("type", "unknown"),
                    title=item.get("subject", {}).get("title", ""),
                    repo=item.get("repository", {}).get("full_name", ""),
                    url=item.get("subject", {}).get("url", ""),
                    updated_at=(
                        datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00"))
                        if item.get("updated_at")
                        else datetime.now()
                    ),
                    unread=item.get("unread", True),
                )
                notifications.append(notif)

            return notifications

        except ProviderError as e:
            logger.error(f"Failed to get Gitea notifications: {e}")
            return []

    async def get_my_prs(self) -> list[PullRequest]:
        """Get my pull requests."""
        try:
            # tea pulls list --author @login
            data = await self._run_command(
                ["pulls", "list", "--author", "@login", "--output", "json"],
                check_json=True,
            )

            if not isinstance(data, list):
                return []

            return [self._parse_pr(item) for item in data]

        except ProviderError as e:
            logger.error(f"Failed to get Gitea PRs: {e}")
            return []

    async def get_prs_to_review(self) -> list[PullRequest]:
        """Get PRs that need my review."""
        try:
            # tea pulls list --assigned-to @login
            data = await self._run_command(
                ["pulls", "list", "--assigned", "@login", "--output", "json"],
                check_json=True,
            )

            if not isinstance(data, list):
                return []

            return [self._parse_pr(item) for item in data]

        except ProviderError as e:
            logger.error(f"Failed to get Gitea review requests: {e}")
            return []

    async def get_user_prs(self, username: str) -> list[PullRequest]:
        """Get PRs for a specific user."""
        try:
            data = await self._run_command(
                ["pulls", "list", "--author", username, "--output", "json"],
                check_json=True,
            )

            if not isinstance(data, list):
                return []

            return [self._parse_pr(item) for item in data]

        except ProviderError as e:
            logger.error(f"Failed to get user PRs: {e}")
            return []

    async def approve_pr(self, pr_id: str) -> None:
        """Approve a PR."""
        try:
            # tea pulls approve <index>
            await self._run_command(
                ["pulls", "approve", pr_id],
                check_json=False,
            )
        except ProviderError as e:
            logger.error(f"Failed to approve PR: {e}")
            raise

    async def comment_on_pr(self, pr_id: str, comment: str) -> None:
        """Comment on a PR."""
        try:
            await self._run_command(
                ["comment", pr_id, comment],
                check_json=False,
            )
        except ProviderError as e:
            logger.error(f"Failed to comment on PR: {e}")
            raise

    async def merge_pr(self, pr_id: str) -> None:
        """Merge a PR."""
        try:
            await self._run_command(
                ["pulls", "merge", pr_id],
                check_json=False,
            )
        except ProviderError as e:
            logger.error(f"Failed to merge PR: {e}")
            raise

    def _parse_pr(self, data: dict) -> PullRequest:
        """Parse PR data from tea CLI."""
        # Parse based on Gitea API structure
        repo = data.get("base", {}).get("repo", {}).get("full_name", "unknown")

        # Determine state
        state = "open"
        if data.get("merged"):
            state = "merged"
        elif data.get("state") == "closed":
            state = "closed"

        return PullRequest(
            id=f"gitea-{repo}-{data.get('number', 0)}",
            provider=self.name,
            number=data.get("number", 0),
            title=data.get("title", ""),
            repo=repo,
            author=data.get("user", {}).get("login", "unknown"),
            url=data.get("html_url", ""),
            state=state,
            updated_at=(
                datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
                if data.get("updated_at")
                else None
            ),
            created_at=(
                datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
                if data.get("created_at")
                else None
            ),
            draft=data.get("draft", False),
        )
