#!/usr/bin/env python3
"""Diagnostic script to test if hyperlinks work in your terminal."""
import sys
import os
from rich.console import Console
from rich.text import Text

print("=" * 80)
print("HYPERLINK DIAGNOSTIC TEST")
print("=" * 80)
print()

# Show environment
print("Environment:")
print(f"  TERM: {os.environ.get('TERM', 'not set')}")
print(f"  TERM_PROGRAM: {os.environ.get('TERM_PROGRAM', 'not set')}")
print(f"  LC_TERMINAL: {os.environ.get('LC_TERMINAL', 'not set')}")
print()

# Show terminal detection
print("Terminal Detection:")
print(f"  sys.stdout.isatty(): {sys.stdout.isatty()}")
console = Console()
print(f"  Rich Console.is_terminal: {console.is_terminal}")
print(f"  Rich Console.legacy_windows: {console.legacy_windows}")
print()

# Test hyperlink
print("Hyperlink Test:")
print("The following line should be clickable (Cmd+Click in iTerm2):")
print()

text = Text(">>> Click this link to open github.com <<<")
text.stylize("bold link https://github.com")
console.print(text)

print()
print("If the line above is NOT clickable:")
print("1. Make sure you're running this directly in iTerm2 (not via SSH or tmux)")
print("2. Check iTerm2 Preferences > Profiles > Terminal > 'Enable mouse reporting'")
print("3. Try running without 'uv run': python3 test_links_diagnostic.py")
print()
print("=" * 80)
