"""Color themes for MOTDD UI."""

from dataclasses import dataclass


@dataclass
class Theme:
    """Color theme definition."""

    # Status colors
    success: str
    warning: str
    error: str
    info: str
    muted: str

    # UI elements
    header: str
    border: str
    highlight: str
    text: str

    # PR/MR states
    pr_open: str
    pr_merged: str
    pr_closed: str
    pr_draft: str


# Default theme - bright colors for dark terminals
DEFAULT_THEME = Theme(
    success="green",
    warning="yellow",
    error="red",
    info="blue",
    muted="bright_black",
    header="bold cyan",
    border="blue",
    highlight="bold yellow",
    text="white",
    pr_open="green",
    pr_merged="magenta",
    pr_closed="red",
    pr_draft="blue",
)

# Light theme - muted colors for light terminals
LIGHT_THEME = Theme(
    success="dark_green",
    warning="dark_orange",
    error="dark_red",
    info="dark_blue",
    muted="grey50",
    header="bold blue",
    border="grey50",
    highlight="bold dark_orange",
    text="black",
    pr_open="dark_green",
    pr_merged="purple",
    pr_closed="dark_red",
    pr_draft="dark_blue",
)

# Solarized Dark theme
SOLARIZED_THEME = Theme(
    success="#859900",  # green
    warning="#b58900",  # yellow
    error="#dc322f",  # red
    info="#268bd2",  # blue
    muted="#586e75",  # base01
    header="bold #268bd2",  # blue
    border="#073642",  # base02
    highlight="bold #b58900",  # yellow
    text="#93a1a1",  # base1
    pr_open="#859900",  # green
    pr_merged="#d33682",  # magenta
    pr_closed="#dc322f",  # red
    pr_draft="#268bd2",  # blue
)

# Nord theme
NORD_THEME = Theme(
    success="#a3be8c",  # nord14 - green
    warning="#ebcb8b",  # nord13 - yellow
    error="#bf616a",  # nord11 - red
    info="#81a1c1",  # nord9 - blue
    muted="#4c566a",  # nord3 - dark gray
    header="bold #88c0d0",  # nord8 - cyan
    border="#3b4252",  # nord1
    highlight="bold #ebcb8b",  # nord13 - yellow
    text="#eceff4",  # nord6 - white
    pr_open="#a3be8c",  # nord14 - green
    pr_merged="#b48ead",  # nord15 - purple
    pr_closed="#bf616a",  # nord11 - red
    pr_draft="#81a1c1",  # nord9 - blue
)


THEMES = {
    "default": DEFAULT_THEME,
    "light": LIGHT_THEME,
    "solarized": SOLARIZED_THEME,
    "nord": NORD_THEME,
}


def get_theme(name: str) -> Theme:
    """
    Get theme by name.

    Args:
        name: Theme name (default, light, solarized, nord)

    Returns:
        Theme instance
    """
    return THEMES.get(name.lower(), DEFAULT_THEME)
