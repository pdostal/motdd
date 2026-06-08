"""Utility functions for MOTDD."""

import os
import webbrowser
from datetime import datetime, timedelta


def osc8_link(url: str, text: str, fallback: bool = True) -> str:
    """
    Create an OSC 8 hyperlink.

    Args:
        url: The URL to link to
        text: The text to display
        fallback: If True, show URL in parentheses if terminal doesn't support OSC 8

    Returns:
        Formatted link string
    """
    # Check if terminal supports OSC 8
    term = os.environ.get("TERM", "")
    supports_osc8 = any(t in term for t in ["kitty", "iterm", "wezterm", "alacritty"])

    if supports_osc8 or not fallback:
        # OSC 8 format: \x1b]8;;URL\x1b\\TEXT\x1b]8;;\x1b\\
        return f"\x1b]8;;{url}\x1b\\{text}\x1b]8;;\x1b\\"
    else:
        # Fallback: just show text with URL
        return f"{text} ({url})"


def relative_time(dt: datetime) -> str:
    """
    Convert datetime to relative time string.

    Args:
        dt: Datetime to convert

    Returns:
        Relative time string like "2 hours ago" or "3 days ago"
    """
    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    diff = now - dt

    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes}m ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours}h ago"
    elif diff < timedelta(days=7):
        days = diff.days
        return f"{days}d ago"
    elif diff < timedelta(days=30):
        weeks = diff.days // 7
        return f"{weeks}w ago"
    elif diff < timedelta(days=365):
        months = diff.days // 30
        return f"{months}mo ago"
    else:
        years = diff.days // 365
        return f"{years}y ago"


def get_status_icon(status: str, status_type: str = "pr") -> str:
    """
    Get icon for a status.

    Args:
        status: Status string
        status_type: Type of status (pr, build, review, notification)

    Returns:
        Icon string
    """
    if status_type == "pr":
        status_lower = status.lower()
        if "approved" in status_lower or "merged" in status_lower:
            return "🟢"
        elif "draft" in status_lower:
            return "🔵"
        elif "changes" in status_lower or "failed" in status_lower:
            return "🔴"
        else:
            return "🟡"

    elif status_type == "build":
        status_lower = status.lower()
        if "succeed" in status_lower or "success" in status_lower:
            return "✓"
        elif "fail" in status_lower or "error" in status_lower:
            return "✗"
        elif "building" in status_lower or "pending" in status_lower:
            return "⏳"
        elif "disabled" in status_lower:
            return "⊘"
        else:
            return "?"

    elif status_type == "review":
        status_lower = status.lower()
        if "approved" in status_lower or "reviewed" in status_lower:
            return "✓"
        elif "restart" in status_lower or "dismiss" in status_lower:
            return "♺"
        elif "pending" in status_lower or "requested" in status_lower:
            return "⏳"
        else:
            return "?"

    elif status_type == "notification":
        status_lower = status.lower()
        if "review" in status_lower:
            return "👁"
        elif "mention" in status_lower or "comment" in status_lower:
            return "💬"
        elif "approv" in status_lower:
            return "✅"
        elif "changes" in status_lower:
            return "❌"
        else:
            return "📬"

    return "?"


def get_provider_icon(provider: str) -> str:
    """
    Get icon for a provider.

    Args:
        provider: Provider name

    Returns:
        Icon string
    """
    provider_lower = provider.lower()
    if "github" in provider_lower:
        return "🐙"
    elif "gitlab" in provider_lower:
        return "🦊"
    elif "forgejo" in provider_lower:
        return "🍵"
    elif "gitea" in provider_lower:
        return "🍃"
    elif "obs" in provider_lower or "ibs" in provider_lower:
        return "📦"
    else:
        return "🔧"


def open_in_browser(url: str) -> None:
    """
    Open URL in default browser.

    Args:
        url: URL to open
    """
    webbrowser.open(url)


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def filter_by_repo(items: list, repo_filter: str | None) -> list:
    """
    Filter items by repository.

    Args:
        items: List of items with 'repo' attribute
        repo_filter: Repository filter string (e.g., "org/repo")

    Returns:
        Filtered list
    """
    if not repo_filter:
        return items

    return [item for item in items if hasattr(item, "repo") and item.repo == repo_filter]


def filter_by_age(items: list, max_days: int, date_field: str = "updated_at") -> list:
    """
    Filter items by age.

    Args:
        items: List of items with datetime attribute
        max_days: Maximum age in days
        date_field: Name of the date field to check

    Returns:
        Filtered list
    """
    cutoff = datetime.now() - timedelta(days=max_days)
    result = []

    for item in items:
        if not hasattr(item, date_field):
            continue

        item_date = getattr(item, date_field)
        if item_date is None:
            continue

        # Handle both aware and naive datetimes
        if item_date.tzinfo is None:
            compare_date = item_date
        else:
            compare_date = item_date.replace(tzinfo=None)

        if compare_date >= cutoff:
            result.append(item)

    return result
