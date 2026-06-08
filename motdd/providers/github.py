"""GitHub provider implementation."""

import logging
from datetime import datetime

from motdd.models import Notification, PullRequest
from motdd.providers.base import BaseProvider, ProviderError

logger = logging.getLogger(__name__)


class GitHubProvider(BaseProvider):
    """GitHub provider using gh CLI."""

    async def get_notifications(self) -> list[Notification]:
        """Get GitHub notifications."""
        try:
            data = await self._run_command(
                ["api", "notifications", "--paginate"],
                check_json=True,
            )

            if not isinstance(data, list):
                return []

            notifications = []
            for item in data:
                # Skip notifications that will be shown in other sections
                reason = item.get("reason", "")
                if reason in ["author", "review_requested"]:
                    # author = shown in "My Pull Requests" section
                    # review_requested = shown in "Reviews" section
                    title = item.get("subject", {}).get("title", "")
                    logger.debug(f"Skipping notification (reason={reason}): {title}")
                    continue

                # Show all other notifications (security_alert, agent_session_finished,
                # comment, mention, push, ci_activity, team_mention, discussion, etc.)
                subject = item.get("subject", {})

                # Get URL (some notifications like agent_session_finished don't have URLs)
                url = subject.get("url", "") or ""
                if url:
                    url = url.replace("api.github.com/repos", "github.com")

                notif = Notification(
                    id=item["id"],
                    provider=self.name,
                    type=self._map_notification_type(reason),
                    title=subject.get("title", ""),
                    repo=item.get("repository", {}).get("full_name", ""),
                    url=url,
                    updated_at=datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00")),
                    unread=item.get("unread", True),
                )
                notifications.append(notif)

            return notifications

        except ProviderError as e:
            logger.error(f"Failed to get GitHub notifications: {e}")
            return []

    async def get_my_prs(self) -> list[PullRequest]:
        """Get my pull requests."""
        try:
            # Use search instead of list to get repository info
            data = await self._run_command(
                [
                    "search",
                    "prs",
                    "--author",
                    "@me",
                    "--json",
                    "number,title,url,state,isDraft,repository,createdAt,updatedAt,author",
                    "--limit",
                    "100",
                ],
                check_json=True,
            )

            if not isinstance(data, list):
                return []

            return [self._parse_pr(item) for item in data]

        except ProviderError as e:
            logger.error(f"Failed to get GitHub PRs: {e}")
            return []

    async def get_prs_to_review(self) -> list[PullRequest]:
        """Get PRs that need my review."""
        try:
            data = await self._run_command(
                [
                    "search",
                    "prs",
                    "--review-requested",
                    "@me",
                    "--json",
                    "number,title,url,state,isDraft,repository,createdAt,updatedAt,author",
                    "--limit",
                    "100",
                ],
                check_json=True,
            )

            if not isinstance(data, list):
                return []

            return [self._parse_pr(item) for item in data]

        except ProviderError as e:
            logger.error(f"Failed to get GitHub review requests: {e}")
            return []

    async def get_reviewed_prs(self, days: int = 7) -> list[PullRequest]:
        """Get recently reviewed PRs."""
        try:
            # Search for PRs I've reviewed in the last N days
            data = await self._run_command(
                [
                    "search",
                    "prs",
                    "--reviewed-by",
                    "@me",
                    "--json",
                    "number,title,url,state,isDraft,repository,createdAt,updatedAt,author",
                    "--limit",
                    "50",
                ],
                check_json=True,
            )

            if not isinstance(data, list):
                return []

            # Filter by age will be done by the caller using utils.filter_by_age
            return [self._parse_pr(item) for item in data]

        except ProviderError as e:
            logger.error(f"Failed to get reviewed PRs: {e}")
            return []

    async def get_user_prs(self, username: str) -> list[PullRequest]:
        """Get PRs for a specific user."""
        try:
            data = await self._run_command(
                [
                    "search",
                    "prs",
                    "--author",
                    username,
                    "--json",
                    "number,title,url,state,isDraft,repository,createdAt,updatedAt,author",
                    "--limit",
                    "100",
                ],
                check_json=True,
            )

            if not isinstance(data, list):
                return []

            return [self._parse_pr(item) for item in data]

        except ProviderError as e:
            logger.error(f"Failed to get user PRs: {e}")
            return []

    async def mark_notification_read(self, notification_id: str) -> None:
        """Mark notification as read."""
        try:
            await self._run_command(
                ["api", "-X", "PATCH", f"notifications/threads/{notification_id}"],
                check_json=False,
            )
        except ProviderError as e:
            logger.error(f"Failed to mark notification as read: {e}")

    async def approve_pr(self, pr_id: str) -> None:
        """Approve a PR."""
        try:
            # pr_id format: "owner/repo#number"
            await self._run_command(
                ["pr", "review", pr_id, "--approve"],
                check_json=False,
            )
        except ProviderError as e:
            logger.error(f"Failed to approve PR: {e}")
            raise

    async def comment_on_pr(self, pr_id: str, comment: str) -> None:
        """Comment on a PR."""
        try:
            await self._run_command(
                ["pr", "comment", pr_id, "--body", comment],
                check_json=False,
            )
        except ProviderError as e:
            logger.error(f"Failed to comment on PR: {e}")
            raise

    async def request_changes(self, pr_id: str, comment: str) -> None:
        """Request changes on a PR."""
        try:
            await self._run_command(
                ["pr", "review", pr_id, "--request-changes", "--body", comment],
                check_json=False,
            )
        except ProviderError as e:
            logger.error(f"Failed to request changes: {e}")
            raise

    async def merge_pr(self, pr_id: str) -> None:
        """Merge a PR."""
        try:
            await self._run_command(
                ["pr", "merge", pr_id, "--auto"],
                check_json=False,
            )
        except ProviderError as e:
            logger.error(f"Failed to merge PR: {e}")
            raise

    def _parse_pr(self, data: dict) -> PullRequest:
        """Parse PR data from gh CLI."""
        # Get repository name (from repository object or fall back to unknown)
        repo_data = data.get("repository", {})
        if isinstance(repo_data, dict):
            repo_name = repo_data.get("nameWithOwner", "unknown")
        else:
            repo_name = "unknown"

        # Parse CI status (not available in gh search prs, only in gh pr list)
        ci_status = None
        rollup = data.get("statusCheckRollup")
        if rollup:
            states = rollup.get("contexts", [])
            if states:
                # Get overall status
                statuses = [s.get("state", "").upper() for s in states if s.get("state")]
                if "FAILURE" in statuses or "ERROR" in statuses:
                    ci_status = "failed"
                elif "PENDING" in statuses or "IN_PROGRESS" in statuses:
                    ci_status = "pending"
                elif all(s == "SUCCESS" for s in statuses):
                    ci_status = "success"

        # Get author (structure differs between gh pr list and gh search prs)
        author_data = data.get("author")
        if isinstance(author_data, dict):
            author = author_data.get("login", "unknown")
        elif isinstance(author_data, str):
            author = author_data
        else:
            author = "unknown"

        return PullRequest(
            id=f"github-{repo_name}-{data['number']}",
            provider=self.name,
            number=data["number"],
            title=data["title"],
            repo=repo_name,
            author=author,
            url=data["url"],
            state=data.get("state", "OPEN").lower(),
            review_decision=(
                data.get("reviewDecision", "").lower() if data.get("reviewDecision") else None
            ),
            ci_status=ci_status,
            updated_at=datetime.fromisoformat(data["updatedAt"].replace("Z", "+00:00")),
            created_at=datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00")),
            draft=data.get("isDraft", False),
        )

    def _map_notification_type(self, reason: str) -> str:
        """Map GitHub notification reason to our type."""
        mapping = {
            "review_requested": "pr_review_request",
            "mention": "mention",
            "author": "pr_activity",
            "comment": "comment",
            "security_alert": "security_alert",
        }
        return mapping.get(reason, reason)
