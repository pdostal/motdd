"""Provider integrations for various platforms."""

from motdd.providers.base import BaseProvider, BuildProvider, ProviderError
from motdd.providers.forgejo import ForgejoProvider
from motdd.providers.gitea import GiteaProvider
from motdd.providers.github import GitHubProvider
from motdd.providers.gitlab import GitLabProvider
from motdd.providers.ibs import IBSProvider
from motdd.providers.obs import OBSProvider

__all__ = [
    "BaseProvider",
    "BuildProvider",
    "ProviderError",
    "GitHubProvider",
    "GitLabProvider",
    "ForgejoProvider",
    "GiteaProvider",
    "OBSProvider",
    "IBSProvider",
]
