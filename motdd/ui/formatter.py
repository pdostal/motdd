"""Data formatting for rich terminal output."""

import os

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from motdd.models import BuildStatus, Notification, PullRequest
from motdd.ui.themes import get_theme
from motdd.utils import (
    get_provider_icon,
    get_status_icon,
    osc8_link,
    relative_time,
    truncate_text,
)


class Formatter:
    """Format data for rich terminal output."""

    def __init__(self, theme_name: str = "default", terminal_width: int | None = None):
        """
        Initialize formatter.

        Args:
            theme_name: Theme name to use
            terminal_width: Terminal width (auto-detected if None)
        """
        self.theme = get_theme(theme_name)
        self.console = Console(width=terminal_width)
        self.terminal_width = terminal_width or self.console.width

    def format_notifications(
        self, notifications: list[Notification], title: str = "Notifications"
    ) -> Panel:
        """
        Format notifications as a table panel.

        Args:
            notifications: List of notifications
            title: Panel title

        Returns:
            Rich Panel with formatted notifications
        """
        if not notifications:
            return Panel(
                Text("No notifications", style=self.theme.muted),
                title=title,
                border_style=self.theme.border,
            )

        table = Table(show_header=True, header_style=self.theme.header, box=None)
        table.add_column("", width=2)  # Icon
        table.add_column("Repository", style=self.theme.info)
        table.add_column("Title", style=self.theme.text)
        table.add_column("Updated", style=self.theme.muted, justify="right")

        for notif in notifications:
            icon = get_status_icon(notif.type, "notification")
            provider_icon = get_provider_icon(notif.provider)

            # Format title with link
            title_text = truncate_text(notif.title, self.terminal_width // 3)
            if self._supports_links():
                title_display = osc8_link(notif.url, title_text, fallback=False)
            else:
                title_display = title_text

            # Format repository
            repo_display = f"{provider_icon} {notif.repo}"

            table.add_row(
                icon,
                repo_display,
                title_display,
                relative_time(notif.updated_at),
            )

        return Panel(
            table,
            title=f"{title} ({len(notifications)})",
            border_style=self.theme.border,
        )

    def format_pull_requests(self, prs: list[PullRequest], title: str = "Pull Requests") -> Panel:
        """
        Format pull requests as a table panel.

        Args:
            prs: List of pull requests
            title: Panel title

        Returns:
            Rich Panel with formatted PRs
        """
        if not prs:
            return Panel(
                Text("No pull requests", style=self.theme.muted),
                title=title,
                border_style=self.theme.border,
            )

        table = Table(show_header=True, header_style=self.theme.header, box=None)
        table.add_column("", width=2)  # Status icon
        table.add_column("PR", width=6, style=self.theme.info)
        table.add_column("Repository", style=self.theme.info)
        table.add_column("Title", style=self.theme.text)
        table.add_column("Author", style=self.theme.muted)
        table.add_column("Updated", style=self.theme.muted, justify="right")

        for pr in prs:
            # Determine status icon and color
            if pr.draft:
                icon = get_status_icon("draft", "pr")
                title_style = self.theme.pr_draft
            elif pr.state == "merged":
                icon = get_status_icon("merged", "pr")
                title_style = self.theme.pr_merged
            elif pr.state == "closed":
                icon = get_status_icon("closed", "pr")
                title_style = self.theme.pr_closed
            elif pr.review_decision == "approved":
                icon = get_status_icon("approved", "pr")
                title_style = self.theme.success
            elif pr.review_decision == "changes_requested":
                icon = get_status_icon("changes_requested", "pr")
                title_style = self.theme.error
            else:
                icon = get_status_icon("pending", "pr")
                title_style = self.theme.pr_open

            # Format title with link
            title_text = truncate_text(pr.title, self.terminal_width // 3)
            if self._supports_links():
                title_display = osc8_link(pr.url, title_text, fallback=False)
            else:
                title_display = title_text

            # Format PR number
            provider_icon = get_provider_icon(pr.provider)
            pr_display = f"{provider_icon}#{pr.number}"

            table.add_row(
                icon,
                pr_display,
                pr.repo,
                Text(title_display, style=title_style),
                pr.author,
                relative_time(pr.updated_at) if pr.updated_at else "",
            )

        return Panel(
            table,
            title=f"{title} ({len(prs)})",
            border_style=self.theme.border,
        )

    def format_builds(self, builds: list[BuildStatus], title: str = "Build Status") -> Panel:
        """
        Format build statuses as a table panel.

        Args:
            builds: List of build statuses
            title: Panel title

        Returns:
            Rich Panel with formatted builds
        """
        if not builds:
            return Panel(
                Text("No builds", style=self.theme.muted),
                title=title,
                border_style=self.theme.border,
            )

        table = Table(show_header=True, header_style=self.theme.header, box=None)
        table.add_column("", width=2)  # Status icon
        table.add_column("Type", width=10, style=self.theme.info)
        table.add_column("Title", style=self.theme.text)
        table.add_column("Status", style=self.theme.text)
        table.add_column("Updated", style=self.theme.muted, justify="right")

        for build in builds:
            # Determine status icon and color
            icon = get_status_icon(build.status, "build")

            if build.status in ["succeeded", "success"]:
                status_style = self.theme.success
            elif build.status in ["failed", "broken"]:
                status_style = self.theme.error
            elif build.status in ["building", "pending"]:
                status_style = self.theme.warning
            else:
                status_style = self.theme.muted

            # Format title with link
            title_text = truncate_text(build.title, self.terminal_width // 3)
            if self._supports_links() and build.url:
                title_display = osc8_link(build.url, title_text, fallback=False)
            else:
                title_display = title_text

            # Format type
            provider_icon = get_provider_icon(build.provider)
            type_display = f"{provider_icon} {build.type}"

            table.add_row(
                icon,
                type_display,
                title_display,
                Text(build.status.upper(), style=status_style),
                relative_time(build.updated_at) if build.updated_at else "",
            )

        return Panel(
            table,
            title=f"{title} ({len(builds)})",
            border_style=self.theme.border,
        )

    def format_review_section(
        self, to_review: list[PullRequest], reviewed: list[PullRequest]
    ) -> Panel:
        """
        Format review section with PRs to review and reviewed PRs.

        Args:
            to_review: PRs needing review
            reviewed: Recently reviewed PRs

        Returns:
            Rich Panel with review information
        """
        if not to_review and not reviewed:
            return Panel(
                Text("No reviews", style=self.theme.muted),
                title="Reviews",
                border_style=self.theme.border,
            )

        table = Table(show_header=True, header_style=self.theme.header, box=None)
        table.add_column("", width=2)  # Review status icon
        table.add_column("PR", width=6, style=self.theme.info)
        table.add_column("Repository", style=self.theme.info)
        table.add_column("Title", style=self.theme.text)
        table.add_column("Author", style=self.theme.muted)
        table.add_column("Updated", style=self.theme.muted, justify="right")

        # Add PRs to review first (highlighted)
        for pr in to_review:
            icon = "⏳"
            title_text = truncate_text(pr.title, self.terminal_width // 3)

            if self._supports_links():
                title_display = osc8_link(pr.url, title_text, fallback=False)
            else:
                title_display = title_text

            provider_icon = get_provider_icon(pr.provider)
            pr_display = f"{provider_icon}#{pr.number}"

            table.add_row(
                icon,
                pr_display,
                pr.repo,
                Text(title_display, style=self.theme.highlight),
                pr.author,
                relative_time(pr.updated_at) if pr.updated_at else "",
            )

        # Add reviewed PRs (muted)
        for pr in reviewed:
            # Determine review icon
            if pr.review_restarted:
                icon = "♺"
            else:
                icon = "✓"

            title_text = truncate_text(pr.title, self.terminal_width // 3)

            if self._supports_links():
                title_display = osc8_link(pr.url, title_text, fallback=False)
            else:
                title_display = title_text

            provider_icon = get_provider_icon(pr.provider)
            pr_display = f"{provider_icon}#{pr.number}"

            table.add_row(
                icon,
                pr_display,
                pr.repo,
                Text(title_display, style=self.theme.muted),
                pr.author,
                relative_time(pr.updated_at) if pr.updated_at else "",
            )

        total = len(to_review) + len(reviewed)
        return Panel(
            table,
            title=f"Reviews ({len(to_review)} pending, {len(reviewed)} reviewed, {total} total)",
            border_style=self.theme.border,
        )

    def format_error(self, provider: str, error_msg: str) -> Panel:
        """
        Format error message as a panel.

        Args:
            provider: Provider name
            error_msg: Error message

        Returns:
            Rich Panel with error
        """
        return Panel(
            Text(f"Error: {error_msg}", style=self.theme.error),
            title=f"{provider} (Error)",
            border_style=self.theme.error,
        )

    def _supports_links(self) -> bool:
        """Check if terminal supports OSC 8 hyperlinks."""
        term = os.environ.get("TERM", "")
        return any(t in term for t in ["kitty", "iterm", "wezterm", "alacritty"])
