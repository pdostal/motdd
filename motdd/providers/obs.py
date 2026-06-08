"""OBS (OpenBuildService) provider implementation."""

import logging
import re

from motdd.models import BuildStatus
from motdd.providers.base import BuildProvider, ProviderError

logger = logging.getLogger(__name__)


class OBSProvider(BuildProvider):
    """OBS provider using osc CLI."""

    def __init__(self, name: str, config: dict):
        """Initialize OBS provider."""
        super().__init__(name, config)
        self.api_url = config.get("api_url", "https://api.opensuse.org")

    async def get_submit_requests(self) -> list[BuildStatus]:
        """Get submit requests."""
        try:
            # Get submit requests for me to review
            output = await self._run_command(
                ["-A", self.api_url, "request", "list", "--type", "submit", "--state", "review"],
                check_json=False,
            )

            if not output:
                return []

            return self._parse_request_list(output, "submit_request")

        except ProviderError as e:
            logger.error(f"Failed to get OBS submit requests: {e}")
            return []

    async def get_builds(self) -> list[BuildStatus]:
        """Get build statuses."""
        try:
            # Get my projects/packages
            output = await self._run_command(
                ["-A", self.api_url, "my", "pkg"],
                check_json=False,
            )

            if not output:
                return []

            # Parse and get build status for each
            builds = []
            for line in output.strip().split("\n"):
                if not line.strip():
                    continue

                # Format: project/package
                parts = line.strip().split("/")
                if len(parts) == 2:
                    project, package = parts
                    try:
                        build_output = await self._run_command(
                            ["-A", self.api_url, "results", project, package],
                            check_json=False,
                        )
                        build_status = self._parse_build_results(build_output, project, package)
                        if build_status:
                            builds.append(build_status)
                    except ProviderError:
                        continue

            return builds

        except ProviderError as e:
            logger.error(f"Failed to get OBS builds: {e}")
            return []

    async def get_incidents(self) -> list[BuildStatus]:
        """Get maintenance incidents."""
        try:
            # Get maintenance incidents
            output = await self._run_command(
                ["-A", self.api_url, "my", "incidents"],
                check_json=False,
            )

            if not output:
                return []

            incidents = []
            # Parse incident list
            for line in output.strip().split("\n"):
                if not line.strip():
                    continue

                # Extract incident info
                match = re.search(r"openSUSE:Maintenance:(\d+)", line)
                if match:
                    incident_num = match.group(1)
                    incident = BuildStatus(
                        id=f"obs-incident-{incident_num}",
                        provider=self.name,
                        type="incident",
                        title=f"Maintenance Incident {incident_num}",
                        status="active",
                        incident_number=incident_num,
                        url=f"{self.api_url.replace('api.', '')}/incident/{incident_num}",
                    )
                    incidents.append(incident)

            return incidents

        except ProviderError as e:
            logger.error(f"Failed to get OBS incidents: {e}")
            return []

    def _parse_request_list(self, output: str, req_type: str) -> list[BuildStatus]:
        """Parse request list output."""
        requests = []

        # Parse osc request list output
        # Format: ID  State        Author           Created    Title
        for line in output.strip().split("\n"):
            if not line.strip() or line.startswith("ID"):
                continue

            # Extract request ID and info
            match = re.match(r"^\s*(\d+)\s+(\w+)\s+(\S+)\s+(.+)", line)
            if match:
                req_id = match.group(1)
                state = match.group(2)
                author = match.group(3)

                request = BuildStatus(
                    id=f"obs-request-{req_id}",
                    provider=self.name,
                    type=req_type,
                    title=f"Submit Request #{req_id} by {author}",
                    status=state.lower(),
                    url=f"{self.api_url.replace('api.', '')}/request/show/{req_id}",
                )
                requests.append(request)

        return requests

    def _parse_build_results(self, output: str, project: str, package: str) -> BuildStatus | None:
        """Parse build results output."""
        if not output:
            return None

        build_results = {}
        overall_status = "unknown"

        # Parse build results
        # Format: repository        arch           status
        for line in output.strip().split("\n"):
            if not line.strip():
                continue

            parts = line.split()
            if len(parts) >= 3:
                repo = parts[0]
                arch = parts[1]
                status = parts[2].lower()

                build_results[f"{repo}/{arch}"] = status

                # Determine overall status
                if status in ["failed", "broken"]:
                    overall_status = "failed"
                elif status == "building" and overall_status != "failed":
                    overall_status = "building"
                elif status == "succeeded" and overall_status not in ["failed", "building"]:
                    overall_status = "succeeded"

        return BuildStatus(
            id=f"obs-build-{project}-{package}",
            provider=self.name,
            type="build",
            title=f"{project}/{package}",
            status=overall_status,
            packages=[package],
            build_results=build_results,
            url=f"{self.api_url.replace('api.', '')}/package/show/{project}/{package}",
        )
