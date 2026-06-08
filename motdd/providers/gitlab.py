"""GitLab provider implementation."""

import logging
from datetime import datetime

from motdd.models import Notification, PullRequest
from motdd.providers.base import BaseProvider, ProviderError

logger = logging.getLogger(__name__)


class GitLabProvider(BaseProvider):
    """GitLab provider using glab CLI."""

    async def get_notifications(self) -> list[Notification]:
        """Get GitLab notifications (todos)."""
        try:
            # GitLab doesn't have notifications API via glab, use todos instead
            # This would require glab api call
            return []
        except ProviderError as e:
            logger.error(f"Failed to get GitLab notifications: {e}")
            return []

    async def get_my_prs(self) -> list[PullRequest]:
        """Get my merge requests."""
        try:
            data = await self._run_command(
                ["mr", "list", "--author", "@me", "--per-page", "100"],
                check_json=True,
            )

            if not isinstance(data, list):
                return []

            return [self._parse_mr(item) for item in data]

        except ProviderError as e:
            logger.error(f"Failed to get GitLab MRs: {e}")
            return []

    async def get_prs_to_review(self) -> list[PullRequest]:
        """Get MRs that need my review."""
        try:
            data = await self._run_command(
                ["mr", "list", "--reviewer", "@me", "--per-page", "100"],
                check_json=True,
            )

            if not isinstance(data, list):
                return []

            return [self._parse_mr(item) for item in data]

        except ProviderError as e:
            logger.error(f"Failed to get GitLab review requests: {e}")
            return []

    async def get_reviewed_prs(self, days: int = 7) -> list[PullRequest]:
        """Get recently reviewed MRs."""
        # GitLab CLI doesn't have a direct way to query reviewed MRs
        # Would need to use API directly
        return []

    async def get_user_prs(self, username: str) -> list[PullRequest]:
        """Get MRs for a specific user."""
        try:
            data = await self._run_command(
                ["mr", "list", "--author", username, "--per-page", "100"],
                check_json=True,
            )

            if not isinstance(data, list):
                return []

            return [self._parse_mr(item) for item in data]

        except ProviderError as e:
            logger.error(f"Failed to get user MRs: {e}")
            return []

    async def approve_pr(self, pr_id: str) -> None:
        """Approve an MR."""
        try:
            await self._run_command(
                ["mr", "approve", pr_id],
                check_json=False,
            )
        except ProviderError as e:
            logger.error(f"Failed to approve MR: {e}")
            raise

    async def comment_on_pr(self, pr_id: str, comment: str) -> None:
        """Comment on an MR."""
        try:
            await self._run_command(
                ["mr", "note", pr_id, "-m", comment],
                check_json=False,
            )
        except ProviderError as e:
            logger.error(f"Failed to comment on MR: {e}")
            raise

    async def merge_pr(self, pr_id: str) -> None:
        """Merge an MR."""
        try:
            await self._run_command(
                ["mr", "merge", pr_id],
                check_json=False,
            )
        except ProviderError as e:
            logger.error(f"Failed to merge MR: {e}")
            raise

    def _parse_mr(self, data: dict) -> PullRequest:
        """Parse MR data from glab CLI."""
        # Extract repo from web_url or references
        web_url = data.get("web_url", "")
        repo = "unknown"
        if web_url:
            # Extract project path from URL
            # Example: https://gitlab.com/group/project/-/merge_requests/123
            parts = web_url.split("/-/merge_requests")
            if len(parts) == 2:
                repo = parts[0].split("/")[-2] + "/" + parts[0].split("/")[-1]

        # Map GitLab pipeline status to CI status
        ci_status = None
        pipeline = data.get("pipeline", {})
        if pipeline:
            status = pipeline.get("status", "").lower()
            if status == "success":
                ci_status = "success"
            elif status in ["failed", "canceled"]:
                ci_status = "failed"
            elif status in ["running", "pending"]:
                ci_status = "pending"

        # Parse review decision from approvals
        review_decision = None
        if data.get("merge_status") == "can_be_merged":
            review_decision = "approved"
        elif data.get("blocking_discussions_resolved") is False:
            review_decision = "changes_requested"

        return PullRequest(
            id=f"gitlab-{data.get('iid', 0)}",
            provider=self.name,
            number=data.get("iid", 0),
            title=data.get("title", ""),
            repo=repo,
            author=data.get("author", {}).get("username", "unknown"),
            url=web_url,
            state=data.get("state", "opened").lower(),
            review_decision=review_decision,
            ci_status=ci_status,
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
            draft=data.get("draft", False) or data.get("work_in_progress", False),
        )
