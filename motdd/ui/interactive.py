"""Interactive mode with textual TUI."""

import asyncio
from datetime import datetime

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Footer, Header, Static

from motdd.config import Config
from motdd.models import BuildStatus, Notification, PullRequest
from motdd.ui.cli_mode import CLIMode


class InteractiveApp(App):
    """Interactive TUI application."""

    CSS = """
    Screen {
        background: $surface;
    }

    #content {
        width: 100%;
        height: 100%;
        overflow-y: scroll;
    }

    .section {
        margin: 1;
        padding: 1;
    }

    .highlighted {
        background: $accent;
    }

    #status-bar {
        dock: bottom;
        height: 1;
        background: $panel;
        color: $text;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("up,k", "cursor_up", "Up", show=False),
        Binding("down,j", "cursor_down", "Down", show=False),
        Binding("enter", "select", "Select"),
        Binding("space", "mark_read", "Mark Read"),
        Binding("a", "approve", "Approve", show=False),
        Binding("c", "comment", "Comment", show=False),
        Binding("m", "merge", "Merge", show=False),
        Binding("o", "open_browser", "Open", show=False),
    ]

    def __init__(
        self,
        config: Config,
        repo_filter: str | None = None,
        verbose: bool = False,
    ):
        """
        Initialize interactive app.

        Args:
            config: Configuration instance
            repo_filter: Optional repository filter
            verbose: Enable verbose output
        """
        super().__init__()
        self.config = config
        self.repo_filter = repo_filter
        self.verbose = verbose
        self.cli_mode = CLIMode(config, repo_filter=repo_filter, verbose=verbose)

        self.last_refresh: datetime | None = None
        self.refresh_interval = config.get_refresh_interval()
        self.auto_refresh_task: asyncio.Task | None = None

        # Data storage
        self.notifications: list[Notification] = []
        self.my_prs: list[PullRequest] = []
        self.to_review: list[PullRequest] = []
        self.reviewed: list[PullRequest] = []
        self.obs_builds: list[BuildStatus] = []
        self.ibs_builds: list[BuildStatus] = []

    def compose(self) -> ComposeResult:
        """Compose the UI."""
        yield Header()
        yield Container(
            Static(id="content"),
            id="main",
        )
        yield Static(id="status-bar")
        yield Footer()

    async def on_mount(self) -> None:
        """Handle mount event."""
        self.title = "MOTDD - Message Of The Developer Day"
        await self.action_refresh()

        # Start auto-refresh if enabled
        if self.refresh_interval > 0:
            self.auto_refresh_task = asyncio.create_task(self._auto_refresh_loop())

    async def on_unmount(self) -> None:
        """Handle unmount event."""
        if self.auto_refresh_task:
            self.auto_refresh_task.cancel()
            try:
                await self.auto_refresh_task
            except asyncio.CancelledError:
                pass

    async def action_refresh(self) -> None:
        """Refresh all data."""
        self._update_status("Refreshing...")

        try:
            # Fetch all data in parallel
            self.notifications = await self.cli_mode._get_all_notifications()
            self.my_prs = await self.cli_mode._get_my_prs()
            self.to_review = await self.cli_mode._get_prs_to_review()
            self.reviewed = await self.cli_mode._get_reviewed_prs()
            self.obs_builds = await self.cli_mode._get_obs_data()
            self.ibs_builds = await self.cli_mode._get_ibs_data()

            self.last_refresh = datetime.now()
            self._update_display()
            self._update_status("Ready")

        except Exception as e:
            self._update_status(f"Error: {e}")

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()

    async def action_select(self) -> None:
        """Select current item (show details)."""
        # TODO: Implement detail view
        self._update_status("Detail view not yet implemented")

    async def action_mark_read(self) -> None:
        """Mark current notification as read."""
        # TODO: Implement mark as read
        self._update_status("Mark as read not yet implemented")

    async def action_approve(self) -> None:
        """Approve current PR."""
        # TODO: Implement approve
        self._update_status("Approve not yet implemented")

    async def action_comment(self) -> None:
        """Comment on current item."""
        # TODO: Implement comment
        self._update_status("Comment not yet implemented")

    async def action_merge(self) -> None:
        """Merge current PR."""
        # TODO: Implement merge
        self._update_status("Merge not yet implemented")

    async def action_open_browser(self) -> None:
        """Open current item in browser."""
        # TODO: Implement open in browser
        self._update_status("Open in browser not yet implemented")

    def action_cursor_up(self) -> None:
        """Move cursor up."""
        # TODO: Implement navigation
        pass

    def action_cursor_down(self) -> None:
        """Move cursor down."""
        # TODO: Implement navigation
        pass

    def _update_display(self) -> None:
        """Update the display with current data."""
        content = self.query_one("#content", Static)

        # Build display text using rich renderables
        from io import StringIO

        from rich.console import Console

        console = Console(file=StringIO(), force_terminal=True, width=self.console.width)

        # Render sections
        console.print(self.cli_mode.formatter.format_review_section(self.to_review, self.reviewed))
        console.print(self.cli_mode.formatter.format_pull_requests(self.my_prs, "My Pull Requests"))
        console.print(self.cli_mode.formatter.format_notifications(self.notifications))
        console.print(self.cli_mode.formatter.format_builds(self.obs_builds, "OBS"))
        console.print(self.cli_mode.formatter.format_builds(self.ibs_builds, "IBS"))

        # Get the rendered output
        output = console.file.getvalue()
        content.update(output)

    def _update_status(self, message: str) -> None:
        """Update status bar."""
        status_bar = self.query_one("#status-bar", Static)

        if self.last_refresh:
            refresh_time = self.last_refresh.strftime("%H:%M:%S")
            status_text = f"{message} | Last refresh: {refresh_time}"
        else:
            status_text = message

        status_bar.update(status_text)

    async def _auto_refresh_loop(self) -> None:
        """Auto-refresh loop."""
        while True:
            try:
                await asyncio.sleep(self.refresh_interval)
                await self.action_refresh()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._update_status(f"Auto-refresh error: {e}")


async def run_interactive(
    config: Config,
    repo_filter: str | None = None,
    verbose: bool = False,
) -> None:
    """
    Run interactive mode.

    Args:
        config: Configuration instance
        repo_filter: Optional repository filter
        verbose: Enable verbose output
    """
    app = InteractiveApp(config, repo_filter, verbose)
    await app.run_async()
