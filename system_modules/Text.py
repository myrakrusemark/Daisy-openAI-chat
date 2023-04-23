from typing import Dict, List, Optional
import sys

from ruamel.yaml import YAML
yaml = YAML()

# Define global variables
yaml_print_text = True
with open("configs.yaml", "r") as f:
    configs = yaml.load(f)
if "print_text" in configs:
    yaml_print_text = configs["print_text"]

TEXT_COLOR_MAPPING = {
    "blue": "36;1",
    "yellow": "33;1",
    "pink": "38;5;200",
    "green": "32;1",
    "red": "31;1",
}

TEXT_STYLE_MAPPING = {
    "bold": "1",
    "italic": "3",
}


def get_color_mapping(
    items: List[str], excluded_colors: Optional[List] = None
) -> Dict[str, str]:
    """Get mapping for items to a support color."""
    colors = list(TEXT_COLOR_MAPPING.keys())
    if excluded_colors is not None:
        colors = [c for c in colors if c not in excluded_colors]
    color_mapping = {item: colors[i % len(colors)] for i, item in enumerate(items)}
    return color_mapping

def get_colored_text(text: str, color:[str] = None, style: Optional[str] = None) -> str:
    """Get colored text."""
    color_str = TEXT_COLOR_MAPPING[color]
    if style is not None:
        style_str = TEXT_STYLE_MAPPING[style]
        return f"\u001b[{color_str}m\033[{style_str}m{text}\u001b[0m"
    else:
        return f"\u001b[{color_str}m{text}\u001b[0m"

def print_text(text: str, color: Optional[str] = None, end: str = "", style: Optional[str] = None) -> None:
    """Print text with highlighting and optional styling."""
    if yaml_print_text:
        if color is None:
            text_to_print = text
        else:
            text_to_print = get_colored_text(text, color, style)
        print(text_to_print, end=end)


def delete_last_lines(n=1): 
    for _ in range(n): 
        sys.stdout.write('\r\x1b[2K') #Erase the line and move the cursor to the start
