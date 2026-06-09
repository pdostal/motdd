"""Data formatting for rich terminal output."""

import os

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

from motdd.models import BuildStatus, Notification, PullRequest
from motdd.ui.themes import get_theme
from motdd.utils import (
    get_provider_icon,
    get_status_icon,
    osc8_link,
    relative_time,
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
    ) -> Text:
        """
        Format notifications as a compact list.

        Args:
            notifications: List of notifications
            title: Section title (unused, kept for compatibility)

        Returns:
            Rich Text with formatted notifications
        """
        if not notifications:
            return Text("No notifications", style=self.theme.muted)

        lines = []
        for notif in notifications:
            icon = get_status_icon(notif.type, "notification")
            provider_icon = get_provider_icon(notif.provider)

            # Get action text from notification type
            action = self._notification_action(notif.type)

            # Format title with link
            if self._supports_links():
                title_display = osc8_link(notif.url, notif.title, fallback=False)
            else:
                title_display = notif.title

            # Format: icon action: title [repo] (time ago)
            time_str = relative_time(notif.updated_at)
            line = f"{icon} {action}: {title_display} [{provider_icon} {notif.repo}] ({time_str})"
            lines.append(line)

        return Text("\n".join(lines))

    def format_pull_requests(self, prs: list[PullRequest], title: str = "Pull Requests") -> Text:
        """
        Format pull requests as a compact list.

        Args:
            prs: List of pull requests
            title: Section title (unused, kept for compatibility)

        Returns:
            Rich Text with formatted PRs
        """
        if not prs:
            return Text("No pull requests", style=self.theme.muted)

        result = Text()
        for pr in prs:
            # Determine status icon
            if pr.draft:
                icon = get_status_icon("draft", "pr")
            elif pr.state == "merged":
                icon = get_status_icon("merged", "pr")
            elif pr.state == "closed":
                icon = get_status_icon("closed", "pr")
            elif pr.review_decision == "approved":
                icon = get_status_icon("approved", "pr")
            elif pr.review_decision == "changes_requested":
                icon = get_status_icon("changes_requested", "pr")
            else:
                icon = get_status_icon("pending", "pr")

            # Format title with link
            if self._supports_links():
                title_display = osc8_link(pr.url, pr.title, fallback=False)
            else:
                title_display = pr.title

            # Format PR number
            provider_icon = get_provider_icon(pr.provider)
            pr_display = f"{provider_icon}#{pr.number}"

            # Format: icon PR#number [repo] title (time ago)
            time_str = relative_time(pr.updated_at) if pr.updated_at else ""
            line = f"{icon} {pr_display} [{pr.repo}] {title_display} ({time_str})\n"
            result.append(line)

        return result

    def format_builds(self, builds: list[BuildStatus], title: str = "Build Status") -> Text:
        """
        Format build statuses as a compact list.

        Args:
            builds: List of build statuses
            title: Section title (unused, kept for compatibility)

        Returns:
            Rich Text with formatted builds
        """
        if not builds:
            return Text("No builds", style=self.theme.muted)

        lines = []
        for build in builds:
            # Determine status icon
            icon = get_status_icon(build.status, "build")

            # Format title with link
            if self._supports_links() and build.url:
                title_display = osc8_link(build.url, build.title, fallback=False)
            else:
                title_display = build.title

            # Format type
            provider_icon = get_provider_icon(build.provider)
            type_display = f"{provider_icon} {build.type}"

            # Format: icon type title [status] (time ago)
            time_str = relative_time(build.updated_at) if build.updated_at else ""
            line = f"{icon} {type_display} {title_display} [{build.status}] ({time_str})"
            lines.append(line)

        return Text("\n".join(lines))

    def format_review_section(
        self, to_review: list[PullRequest], reviewed: list[PullRequest]
    ) -> Text:
        """
        Format review section with PRs to review and reviewed PRs as a compact list.

        Args:
            to_review: PRs needing review
            reviewed: Recently reviewed PRs

        Returns:
            Rich Text with review information
        """
        if not to_review and not reviewed:
            return Text("No reviews", style=self.theme.muted)

        result = Text()

        # Add PRs to review first (highlighted)
        for pr in to_review:
            icon = "[…]"

            if self._supports_links():
                title_display = osc8_link(pr.url, pr.title, fallback=False)
            else:
                title_display = pr.title

            provider_icon = get_provider_icon(pr.provider)
            pr_display = f"{provider_icon}#{pr.number}"

            # Format: icon PR#number [repo] title (time ago)
            time_str = relative_time(pr.updated_at) if pr.updated_at else ""
            line = f"{icon} {pr_display} [{pr.repo}] {title_display} ({time_str})\n"
            result.append(line, style=self.theme.highlight)

        # Add reviewed PRs (muted)
        for pr in reviewed:
            # Determine review icon
            if pr.review_restarted:
                icon = "[↻]"
            else:
                icon = "[✓]"

            if self._supports_links():
                title_display = osc8_link(pr.url, pr.title, fallback=False)
            else:
                title_display = pr.title

            provider_icon = get_provider_icon(pr.provider)
            pr_display = f"{provider_icon}#{pr.number}"

            # Format: icon PR#number [repo] title (time ago)
            time_str = relative_time(pr.updated_at) if pr.updated_at else ""
            line = f"{icon} {pr_display} [{pr.repo}] {title_display} ({time_str})\n"
            result.append(line, style=self.theme.muted)

        return result

    def format_section_header(self, title: str) -> Rule:
        """
        Create a section header rule.

        Args:
            title: Section title

        Returns:
            Rich Rule with section header
        """
        return Rule(title, style=self.theme.header, align="left")

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

    def _notification_action(self, notification_type: str) -> str:
        """
        Convert notification type to action text.

        Args:
            notification_type: Type of notification

        Returns:
            Action description
        """
        type_lower = notification_type.lower()

        if "review" in type_lower and "request" in type_lower:
            return "Review requested"
        elif "mention" in type_lower:
            return "Mentioned"
        elif "comment" in type_lower:
            return "Commented"
        elif "security" in type_lower or "alert" in type_lower:
            return "Security alert"
        elif "approved" in type_lower or "approve" in type_lower:
            return "Approved"
        elif "changes" in type_lower:
            return "Changes requested"
        elif "assigned" in type_lower:
            return "Assigned"
        elif "ci" in type_lower or "check" in type_lower:
            return "CI activity"
        elif "push" in type_lower:
            return "New commits"
        elif "team" in type_lower:
            return "Team mention"
        elif "discussion" in type_lower:
            return "Discussion"
        else:
            # Default: capitalize the type
            return notification_type.replace("_", " ").title()

    def _supports_links(self) -> bool:
        """Check if terminal supports OSC 8 hyperlinks."""
        term = os.environ.get("TERM", "")
        return any(t in term for t in ["kitty", "iterm", "wezterm", "alacritty"])
