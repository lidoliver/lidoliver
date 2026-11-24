"""Everything the profile says. build.py turns this into the SVG panels and README.md.

Icons are Nerd Font codepoints (https://www.nerdfonts.com/cheat-sheet). A new icon needs
scripts/subset-font.sh to be run again so the embedded font contains it.

Projects also come from GitHub: see PROJECTS below.
"""

USERNAME = "lidoliver"
NAME = "Oliver"
TAGLINE = "bachelor in computer engineering"
PROMPT = "currently learning C"

# The memory card: one save per project.
#
# Saves are found automatically: every public repo of yours that isn't a fork, isn't
# archived and has a description becomes a save (build.py: github_saves()). The entries
# below are merged on top of them by name, and anything set here wins over what GitHub
# says, so they control the wording and the order. Projects that live in someone else's
# account are listed here in full. Repos found only on GitHub come after these, oldest first.
PROJECTS = [
    {
        "name": "Gruppe11_MOB3000",
        "url": "https://github.com/lidoliver/Gruppe11_MOB3000",
        "icon": 0xE634, "tint": "#a98dff", "lang": "Kotlin",
        "desc": "Disc golf app. I built multiplayer game sessions, the friends system and push messaging.",
        "stack": "Compose · Firebase · Node",
    },
    {
        "name": "ps2-install",
        "url": "https://github.com/lidoliver/ps2-install",
        "icon": 0xE760, "tint": "#7fe3a6", "lang": "Shell",
        "desc": "Installs PS2 games onto the console's internal HDD over the network, from Linux.",
        "stack": "Bash · C · NBD",
    },
    {
        "name": "traffic-simulator",
        "url": "https://github.com/Vanguardium/traffic-simulator",
        "icon": 0xE738, "tint": "#ffb36b", "lang": "Java",
        "desc": "Traffic simulation, built as a group project.",
        "stack": "Java",
    },
    {
        "name": "APP2000_G10_25",
        "url": "https://github.com/MarcusWHE/APP2000_G10_25",
        "icon": 0xE7BA, "tint": "#ffdd6b", "lang": "JavaScript",
        "desc": "Web app built by a team of six, run with Scrum.",
        "stack": "MongoDB · Express · React · Node",
    },
]

# The "now" panel: the repos you pushed to most recently, newest first, each with the date
# and its latest commit message (build.py: now_entries()). Same repos as the memory card,
# so HIDDEN_REPOS and repos without a description stay out. Hand-written entries in
# NOW_PINNED, as (title, tag, line), go above them.
NOW_COUNT = 3
NOW_PINNED: list[tuple[str, str, str]] = []

STACK = {
    "languages": [("Kotlin", 0xE634), ("Java", 0xE738), ("JavaScript", 0xE74E), ("C", 0xF0671), ("Bash", 0xE760)],
    "build": [("Jetpack Compose", 0xE809), ("Android", 0xE70E), ("React", 0xE7BA), ("Node.js", 0xE718),
              ("Express", 0xE7D3), ("Firebase", 0xE787)],
    "data": [("PostgreSQL", 0xE76E), ("MongoDB", 0xE7A4)],
    "system": [("Arch Linux", 0xF303), ("Hyprland", 0xF359), ("Docker", 0xE7B0), ("Neovim", 0xF36F), ("Git", 0xE702)],
}

# Repos that never become a save.
HIDDEN_REPOS = {USERNAME}

# For saves made from GitHub: an icon per language, the tints to pick from (each new save
# gets the one used least so far), and the topics that count as the stack, in the order
# they are shown (two at most). Other topics are ignored; without any, the stack is the
# language.
LANGUAGE_ICONS = {
    "Shell": 0xE760, "C": 0xF0671, "C++": 0xE61D, "C#": 0xF031B, "Java": 0xE738,
    "Kotlin": 0xE634, "JavaScript": 0xE74E, "TypeScript": 0xE628, "Python": 0xE73C,
    "Go": 0xE627, "Rust": 0xE7A8, "Lua": 0xE620, "HTML": 0xE736, "CSS": 0xE749,
    "QML": 0xF375, "Dart": 0xE798, "Swift": 0xE755, "PHP": 0xE73D, "Ruby": 0xE739,
    "Vue": 0xE6A0, "Svelte": 0xE697, "Nix": 0xF313, "Dockerfile": 0xE7B0,
}
DEFAULT_ICON = 0xEA62
TINTS = ["#a98dff", "#7fe3a6", "#ffb36b", "#ffdd6b", "#7fd3ff", "#ff8fb1"]
STACK_TOPICS = {
    "quickshell": "Quickshell", "omarchy": "Omarchy", "hyprland": "Hyprland",
    "easyeffects": "Easy Effects", "pipewire": "PipeWire", "neovim": "Neovim",
    "android": "Android", "jetpack-compose": "Compose", "firebase": "Firebase",
    "react": "React", "nodejs": "Node", "express": "Express", "mongodb": "MongoDB",
    "postgresql": "PostgreSQL", "docker": "Docker", "nbd": "NBD", "ps2": "PS2",
}

# Panel header icons.
ICON_CARD = 0xEF61
ICON_NOW = 0xF018D
ICON_STACK = 0xF1B3


def icons() -> list[int]:
    """Every icon the images can use, for subset-font.sh. Includes all language icons so a
    new repo never needs a font rebuild unless its language is missing from LANGUAGE_ICONS."""
    out = {p["icon"] for p in PROJECTS} | {i for group in STACK.values() for _, i in group}
    out |= set(LANGUAGE_ICONS.values()) | {DEFAULT_ICON}
    return sorted(out | {ICON_CARD, ICON_NOW, ICON_STACK})
