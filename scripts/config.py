"""Everything the profile says. build.py turns this into the SVG panels and README.md.

Icons are Nerd Font codepoints (https://www.nerdfonts.com/cheat-sheet). A new icon needs
scripts/subset-font.sh to be run again so the embedded font contains it.
"""

USERNAME = "lidoliver"
NAME = "Oliver"
TAGLINE = "bachelor in computer engineering"
PROMPT = "currently learning C"

# The memory card: one save per project.
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

# (title, tag, line)
NOW = [
    ("learning C", "C", "Pointers and memory, compiled and run from Neovim with one key."),
    ("ps2-install", "Bash · C", "A patched hdl_dump for faster installs, with KDE and Hyprland frontends."),
    ("PS2 modding", "OPL · MX4SIO", "Games from SD card and internal HDD on real hardware."),
    ("this profile", "Python · SVG", "A script that draws these panels, PS2 boot-screen style."),
]

STACK = {
    "languages": [("Kotlin", 0xE634), ("Java", 0xE738), ("JavaScript", 0xE74E), ("C", 0xF0671), ("Bash", 0xE760)],
    "build": [("Jetpack Compose", 0xE809), ("Android", 0xE70E), ("React", 0xE7BA), ("Node.js", 0xE718),
              ("Express", 0xE7D3), ("Firebase", 0xE787)],
    "data": [("PostgreSQL", 0xE76E), ("MongoDB", 0xE7A4)],
    "system": [("Arch Linux", 0xF303), ("Hyprland", 0xF359), ("Docker", 0xE7B0), ("Neovim", 0xF36F), ("Git", 0xE702)],
}

# Panel header icons.
ICON_CARD = 0xEF61
ICON_NOW = 0xF018D
ICON_STACK = 0xF1B3


def icons() -> list[int]:
    out = {p["icon"] for p in PROJECTS} | {i for group in STACK.values() for _, i in group}
    return sorted(out | {ICON_CARD, ICON_NOW, ICON_STACK})
