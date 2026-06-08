"""Data models for MOTDD."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Notification:
    """Notification from a provider."""

    id: str
    provider: str
    type: str  # pr_review_request, issue_mention, etc.
    title: str
    repo: str
    url: str
    updated_at: datetime
    unread: bool = True

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "provider": self.provider,
            "type": self.type,
            "title": self.title,
            "repo": self.repo,
            "url": self.url,
            "updated_at": self.updated_at.isoformat(),
            "unread": self.unread,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Notification":
        """Create from dictionary."""
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)


@dataclass
class PullRequest:
    """Pull request from a provider."""

    id: str
    provider: str
    number: int
    title: str
    repo: str
    author: str
    url: str
    state: str  # open, merged, closed
    review_decision: str | None = None  # approved, changes_requested, review_required
    reviews_by_me: list[str] = field(default_factory=list)  # ['approved', 'changes_requested']
    review_restarted: bool = False  # True if review was dismissed and re-requested
    ci_status: str | None = None
    updated_at: datetime | None = None
    created_at: datetime | None = None
    draft: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "provider": self.provider,
            "number": self.number,
            "title": self.title,
            "repo": self.repo,
            "author": self.author,
            "url": self.url,
            "state": self.state,
            "review_decision": self.review_decision,
            "reviews_by_me": self.reviews_by_me,
            "review_restarted": self.review_restarted,
            "ci_status": self.ci_status,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "draft": self.draft,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PullRequest":
        """Create from dictionary."""
        if data.get("updated_at"):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


@dataclass
class BuildStatus:
    """Build or submit request status from OBS/IBS."""

    id: str
    provider: str  # obs, ibs
    type: str  # submit_request, build, incident
    title: str
    status: str  # building, succeeded, failed, disabled, etc.
    packages: list[str] = field(default_factory=list)
    url: str = ""
    updated_at: datetime | None = None
    # Additional metadata for incidents
    incident_number: str | None = None
    build_results: dict[str, str] = field(default_factory=dict)  # package -> status
    approval_status: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "provider": self.provider,
            "type": self.type,
            "title": self.title,
            "status": self.status,
            "packages": self.packages,
            "url": self.url,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "incident_number": self.incident_number,
            "build_results": self.build_results,
            "approval_status": self.approval_status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BuildStatus":
        """Create from dictionary."""
        if data.get("updated_at"):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)
