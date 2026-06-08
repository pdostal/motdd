"""IBS (Internal Build Service - SUSE) provider implementation."""

import logging

from motdd.providers.obs import OBSProvider

logger = logging.getLogger(__name__)


class IBSProvider(OBSProvider):
    """
    IBS provider using osc CLI.

    IBS is essentially OBS with a different API URL, so we inherit
    from OBSProvider and just use a different default API URL.
    """

    def __init__(self, name: str, config: dict):
        """Initialize IBS provider."""
        # Set default IBS API URL if not specified
        if "api_url" not in config:
            config["api_url"] = "https://api.suse.de"

        super().__init__(name, config)
