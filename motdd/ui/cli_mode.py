"""CLI mode output rendering."""

import asyncio

from rich.console import Console

from motdd.cache import Cache
from motdd.config import Config
from motdd.models import BuildStatus, Notification, PullRequest
from motdd.providers import (
    ForgejoProvider,
    GiteaProvider,
    GitHubProvider,
    GitLabProvider,
    IBSProvider,
    OBSProvider,
)
from motdd.ui.formatter import Formatter
from motdd.utils import filter_by_age, filter_by_repo


class CLIMode:
    """CLI mode output handler."""

    def __init__(
        self,
        config: Config,
        cache: Cache | None = None,
        repo_filter: str | None = None,
        verbose: bool = False,
    ):
        """
        Initialize CLI mode.

        Args:
            config: Configuration instance
            cache: Cache instance (optional)
            repo_filter: Repository filter (e.g., "org/repo")
            verbose: Enable verbose output
        """
        self.config = config
        self.cache = cache
        self.repo_filter = repo_filter
        self.verbose = verbose
        self.formatter = Formatter(theme_name=config.get_theme())
        self.console = Console()

    async def show_all(self) -> None:
        """Show all sections in priority order."""
        # Section order: reviews, PRs, notifications, OBS, IBS
        await self.show_reviews()
        await self.show_my_prs()
        await self.show_notifications()
        await self.show_obs()
        await self.show_ibs()

    async def show_notifications(self) -> None:
        """Show notifications section."""
        self.console.print(self.formatter.format_section_header("Notifications"))
        notifications = await self._get_all_notifications()

        if self.repo_filter:
            notifications = filter_by_repo(notifications, self.repo_filter)

        output = self.formatter.format_notifications(notifications)
        self.console.print(output)

    async def show_my_prs(self) -> None:
        """Show my PRs section."""
        self.console.print(self.formatter.format_section_header("Pull Requests"))
        prs = await self._get_my_prs()

        if self.repo_filter:
            prs = filter_by_repo(prs, self.repo_filter)

        output = self.formatter.format_pull_requests(prs, title="My Pull Requests")
        self.console.print(output)

    async def show_reviews(self) -> None:
        """Show reviews section."""
        self.console.print(self.formatter.format_section_header("Reviews"))
        to_review = await self._get_prs_to_review()
        reviewed = await self._get_reviewed_prs()

        if self.repo_filter:
            to_review = filter_by_repo(to_review, self.repo_filter)
            reviewed = filter_by_repo(reviewed, self.repo_filter)

        output = self.formatter.format_review_section(to_review, reviewed)
        self.console.print(output)

    async def show_user_prs(self, username: str, provider: str | None = None) -> None:
        """
        Show PRs for a specific user.

        Args:
            username: Username to query
            provider: Optional provider name (uses default if None)
        """
        if provider is None:
            provider = self.config.get_default_provider()

        prs = await self._get_user_prs(username, provider)

        if self.repo_filter:
            prs = filter_by_repo(prs, self.repo_filter)

        panel = self.formatter.format_pull_requests(prs, title=f"Pull Requests by {username}")
        self.console.print(panel)

    async def show_obs(self) -> None:
        """Show OBS section."""
        self.console.print(self.formatter.format_section_header("Submit Requests (OBS)"))
        builds = await self._get_obs_data()
        output = self.formatter.format_builds(builds, title="OBS")
        self.console.print(output)

    async def show_ibs(self) -> None:
        """Show IBS section."""
        self.console.print(self.formatter.format_section_header("Submit Requests (IBS)"))
        builds = await self._get_ibs_data()
        output = self.formatter.format_builds(builds, title="IBS")
        self.console.print(output)

    async def _get_all_notifications(self) -> list[Notification]:
        """Get notifications from all providers."""
        providers = self._get_git_providers()

        # Run in parallel
        tasks = [provider.get_notifications() for provider in providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_notifications = []
        for provider, result in zip(providers, results):
            if isinstance(result, Exception):
                if self.verbose:
                    self.console.print(self.formatter.format_error(provider.name, str(result)))
            else:
                all_notifications.extend(result)

        # Sort by updated_at descending
        all_notifications.sort(key=lambda x: x.updated_at, reverse=True)
        return all_notifications

    async def _get_my_prs(self) -> list[PullRequest]:
        """Get my PRs from all providers."""
        providers = self._get_git_providers()

        tasks = [provider.get_my_prs() for provider in providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_prs = []
        for provider, result in zip(providers, results):
            if isinstance(result, Exception):
                if self.verbose:
                    self.console.print(self.formatter.format_error(provider.name, str(result)))
            else:
                all_prs.extend(result)

        # Filter to only active PRs (open or draft, not merged or closed)
        all_prs = [pr for pr in all_prs if pr.state == "open"]

        # Sort by updated_at descending
        all_prs.sort(key=lambda x: x.updated_at or x.created_at, reverse=True)
        return all_prs

    async def _get_prs_to_review(self) -> list[PullRequest]:
        """Get PRs to review from all providers."""
        providers = self._get_git_providers()

        tasks = [provider.get_prs_to_review() for provider in providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_prs = []
        for provider, result in zip(providers, results):
            if isinstance(result, Exception):
                if self.verbose:
                    self.console.print(self.formatter.format_error(provider.name, str(result)))
            else:
                all_prs.extend(result)

        # Filter out merged PRs (only show open PRs needing review)
        all_prs = [pr for pr in all_prs if pr.state != "merged"]

        # Sort by updated_at descending
        all_prs.sort(key=lambda x: x.updated_at or x.created_at, reverse=True)
        return all_prs

    async def _get_reviewed_prs(self) -> list[PullRequest]:
        """Get recently reviewed PRs."""
        providers = self._get_git_providers()
        days = self.config.get_reviewed_prs_days()

        tasks = [provider.get_reviewed_prs(days) for provider in providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_prs = []
        for provider, result in zip(providers, results):
            if isinstance(result, Exception):
                if self.verbose:
                    self.console.print(self.formatter.format_error(provider.name, str(result)))
            else:
                all_prs.extend(result)

        # Filter by age
        all_prs = filter_by_age(all_prs, days)

        # Filter out merged PRs
        all_prs = [pr for pr in all_prs if pr.state != "merged"]

        # Sort by updated_at descending
        all_prs.sort(key=lambda x: x.updated_at or x.created_at, reverse=True)
        return all_prs

    async def _get_user_prs(self, username: str, provider_name: str) -> list[PullRequest]:
        """Get PRs for a specific user."""
        providers = [
            p for p in self._get_git_providers() if p.name.lower() == provider_name.lower()
        ]

        if not providers:
            return []

        provider = providers[0]
        try:
            return await provider.get_user_prs(username)
        except Exception as e:
            if self.verbose:
                self.console.print(self.formatter.format_error(provider.name, str(e)))
            return []

    async def _get_obs_data(self) -> list[BuildStatus]:
        """Get OBS build data."""
        providers = self._get_build_providers("obs")

        all_builds = []
        for provider in providers:
            try:
                srs = await provider.get_submit_requests()
                builds = await provider.get_builds()
                incidents = await provider.get_incidents()
                all_builds.extend(srs + builds + incidents)
            except Exception as e:
                if self.verbose:
                    self.console.print(self.formatter.format_error(provider.name, str(e)))

        # Sort by updated_at if available
        all_builds.sort(key=lambda x: x.updated_at if x.updated_at else x.id, reverse=True)
        return all_builds

    async def _get_ibs_data(self) -> list[BuildStatus]:
        """Get IBS build data."""
        providers = self._get_build_providers("ibs")

        all_builds = []
        for provider in providers:
            try:
                srs = await provider.get_submit_requests()
                builds = await provider.get_builds()
                incidents = await provider.get_incidents()
                all_builds.extend(srs + builds + incidents)
            except Exception as e:
                if self.verbose:
                    self.console.print(self.formatter.format_error(provider.name, str(e)))

        # Sort by updated_at if available
        all_builds.sort(key=lambda x: x.updated_at if x.updated_at else x.id, reverse=True)
        return all_builds

    def _get_git_providers(self) -> list:
        """Get all git providers (GitHub, GitLab, etc.)."""
        providers = []

        # GitHub providers
        for config in self.config.get_providers("github"):
            providers.append(GitHubProvider(config["name"], config))

        # GitLab providers
        for config in self.config.get_providers("gitlab"):
            providers.append(GitLabProvider(config["name"], config))

        # Forgejo providers
        for config in self.config.get_providers("forgejo"):
            providers.append(ForgejoProvider(config["name"], config))

        # Gitea providers
        for config in self.config.get_providers("gitea"):
            providers.append(GiteaProvider(config["name"], config))

        return providers

    def _get_build_providers(self, provider_type: str) -> list:
        """Get build providers (OBS/IBS)."""
        providers = []

        for config in self.config.get_providers(provider_type):
            if provider_type == "obs":
                providers.append(OBSProvider(config["name"], config))
            elif provider_type == "ibs":
                providers.append(IBSProvider(config["name"], config))

        return providers
