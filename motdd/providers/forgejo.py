"""Forgejo provider implementation."""

import logging
from datetime import datetime

from motdd.models import Notification, PullRequest
from motdd.providers.base import BaseProvider, ProviderError

logger = logging.getLogger(__name__)


class ForgejoProvider(BaseProvider):
    """Forgejo provider using fj CLI."""

    async def get_notifications(self) -> list[Notification]:
        """Get Forgejo notifications."""
        # Forgejo CLI notifications support depends on the CLI version
        # For now, return empty - can be implemented when CLI supports it
        return []

    async def get_my_prs(self) -> list[PullRequest]:
        """Get my pull requests."""
        try:
            # Note: fj CLI commands may vary, this is based on expected interface
            data = await self._run_command(
                ["pr", "list", "--author", "@me", "--json"],
                check_json=True,
            )

            if not isinstance(data, list):
                return []

            return [self._parse_pr(item) for item in data]

        except ProviderError as e:
            logger.error(f"Failed to get Forgejo PRs: {e}")
            return []

    async def get_prs_to_review(self) -> list[PullRequest]:
        """Get PRs that need my review."""
        try:
            data = await self._run_command(
                ["pr", "list", "--review-requested", "@me", "--json"],
                check_json=True,
            )

            if not isinstance(data, list):
                return []

            return [self._parse_pr(item) for item in data]

        except ProviderError as e:
            logger.error(f"Failed to get Forgejo review requests: {e}")
            return []

    async def get_user_prs(self, username: str) -> list[PullRequest]:
        """Get PRs for a specific user."""
        try:
            data = await self._run_command(
                ["pr", "list", "--author", username, "--json"],
                check_json=True,
            )

            if not isinstance(data, list):
                return []

            return [self._parse_pr(item) for item in data]

        except ProviderError as e:
            logger.error(f"Failed to get user PRs: {e}")
            return []

    def _parse_pr(self, data: dict) -> PullRequest:
        """Parse PR data from fj CLI."""
        # Parse based on Gitea/Forgejo API structure
        repo = data.get("base", {}).get("repo", {}).get("full_name", "unknown")

        # Determine state
        state = "open"
        if data.get("merged"):
            state = "merged"
        elif data.get("state") == "closed":
            state = "closed"

        return PullRequest(
            id=f"forgejo-{repo}-{data.get('number', 0)}",
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
