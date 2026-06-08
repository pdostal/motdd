"""Tests for data models."""

from datetime import datetime

from motdd.models import BuildStatus, Notification, PullRequest


def test_notification_serialization() -> None:
    """Test notification serialization and deserialization."""
    now = datetime.now()
    notif = Notification(
        id="123",
        provider="github",
        type="pr_review_request",
        title="Review my PR",
        repo="org/repo",
        url="https://github.com/org/repo/pull/1",
        updated_at=now,
        unread=True,
    )

    # Serialize
    data = notif.to_dict()
    assert data["id"] == "123"
    assert data["provider"] == "github"
    assert data["unread"] is True

    # Deserialize
    restored = Notification.from_dict(data)
    assert restored.id == notif.id
    assert restored.provider == notif.provider
    assert restored.updated_at == notif.updated_at


def test_pullrequest_serialization() -> None:
    """Test pull request serialization and deserialization."""
    now = datetime.now()
    pr = PullRequest(
        id="pr-456",
        provider="gitlab",
        number=456,
        title="Add new feature",
        repo="org/project",
        author="developer",
        url="https://gitlab.com/org/project/-/merge_requests/456",
        state="open",
        review_decision="approved",
        reviews_by_me=["approved"],
        review_restarted=False,
        ci_status="success",
        updated_at=now,
        created_at=now,
        draft=False,
    )

    # Serialize
    data = pr.to_dict()
    assert data["number"] == 456
    assert data["state"] == "open"
    assert data["reviews_by_me"] == ["approved"]

    # Deserialize
    restored = PullRequest.from_dict(data)
    assert restored.id == pr.id
    assert restored.number == pr.number
    assert restored.updated_at == pr.updated_at


def test_buildstatus_serialization() -> None:
    """Test build status serialization and deserialization."""
    now = datetime.now()
    build = BuildStatus(
        id="build-789",
        provider="obs",
        type="submit_request",
        title="Submit package update",
        status="building",
        packages=["package1", "package2"],
        url="https://build.opensuse.org/request/show/789",
        updated_at=now,
        incident_number="12345",
        build_results={"package1": "succeeded", "package2": "building"},
        approval_status="pending",
    )

    # Serialize
    data = build.to_dict()
    assert data["type"] == "submit_request"
    assert data["status"] == "building"
    assert len(data["packages"]) == 2

    # Deserialize
    restored = BuildStatus.from_dict(data)
    assert restored.id == build.id
    assert restored.packages == build.packages
    assert restored.build_results == build.build_results


def test_pullrequest_defaults() -> None:
    """Test pull request with default values."""
    pr = PullRequest(
        id="pr-1",
        provider="github",
        number=1,
        title="Test PR",
        repo="test/repo",
        author="tester",
        url="https://example.com",
        state="open",
    )

    assert pr.review_decision is None
    assert pr.reviews_by_me == []
    assert pr.review_restarted is False
    assert pr.ci_status is None
    assert pr.draft is False
