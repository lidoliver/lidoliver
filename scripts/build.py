#!/usr/bin/env python3
"""Draw the profile: SVG panels into assets/, the page into README.md. Standard library only.

    python3 scripts/build.py                     # images + README pointing at GitHub
    python3 scripts/build.py --base assets       # README pointing at the local images (preview)
    python3 scripts/build.py --offline           # use scripts/repos.json instead of the GitHub API

The memory card's saves are your public repos, fetched from the GitHub API (set GITHUB_TOKEN to
avoid the rate limit), with config.PROJECTS merged on top. Each fetch is saved to
scripts/repos.json, which is used when the API can't be reached.

The look borrows from the PS2 boot screen and memory card browser: towers of light in a dark
blue fog, and saves that float above the card. Every image shares one background colour and is
as wide as the page, so the rows join into one surface. Rows of two panels get a second,
stacked image for phones.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import random
import sys
import textwrap
import urllib.request
from html import escape
from pathlib import Path

import config as C

ROOT = Path(__file__).resolve().parent.parent
ASSETS = Path(__file__).resolve().parent / "assets"
REPOS_CACHE = Path(__file__).resolve().parent / "repos.json"
RAW = f"https://raw.githubusercontent.com/{C.USERNAME}/{C.USERNAME}/main/assets"
PROFILE = f"https://github.com/{C.USERNAME}"

# GitHub's profile column is one wide column at these widths; below them the stacked image is used.
WIDE = "(min-width: 1012px), (min-width: 600px) and (max-width: 767px)"

BG = "#04050f"
TEXT = "#e9eeff"
MUTED = "#8f9bc8"
DIM = "#5b6794"
CYAN = "#9fd9ff"
BLUE = "#4f7dff"
EDGE = "#25356f"
CW = 0.6  # JetBrains Mono advance, in em


# ---------------------------------------------------------------- primitives

def font_css() -> str:
    def face(weight: int, file: str) -> str:
        data = base64.b64encode((ASSETS / file).read_bytes()).decode()
        return (f"@font-face{{font-family:J;font-weight:{weight};"
                f"src:url(data:font/woff2;base64,{data}) format('woff2')}}")
    return face(400, "jbm-regular.woff2") + face(700, "jbm-bold.woff2")


STYLE = """
text{font-family:J,ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;fill:%s}
.b{font-weight:700}.m{fill:%s}.d{fill:%s}.c{fill:%s}
.pulse{animation:pulse 5s ease-in-out infinite}
@keyframes pulse{0%%,100%%{opacity:.45}50%%{opacity:1}}
.blink{animation:blink 1.1s steps(1) infinite}
@keyframes blink{50%%{opacity:0}}
.bob{animation:bob 4s ease-in-out infinite}
@keyframes bob{0%%,100%%{transform:translateY(0)}50%%{transform:translateY(-4px)}}
.rise{animation:rise 9s linear infinite;opacity:0}
@keyframes rise{0%%{transform:translateY(0);opacity:0}15%%{opacity:.9}100%%{transform:translateY(-90px);opacity:0}}
""" % (TEXT, MUTED, DIM, CYAN)

DEFS = f"""<defs>
<linearGradient id="panel" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0d1540"/><stop offset="1" stop-color="#070a20"/></linearGradient>
<linearGradient id="rule" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{BLUE}" stop-opacity="0"/><stop offset=".5" stop-color="{CYAN}" stop-opacity=".55"/><stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></linearGradient>
<linearGradient id="tower" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#b9dcff" stop-opacity=".75"/><stop offset=".35" stop-color="#4f7dff" stop-opacity=".35"/><stop offset="1" stop-color="#1b2a6b" stop-opacity="0"/></linearGradient>
<linearGradient id="tower2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7fb6ff" stop-opacity=".55"/><stop offset=".4" stop-color="#2f56d6" stop-opacity=".25"/><stop offset="1" stop-color="#101b4d" stop-opacity="0"/></linearGradient>
<radialGradient id="fog" cx=".5" cy=".55" r=".5"><stop offset="0" stop-color="#2a4bd0" stop-opacity=".38"/><stop offset=".6" stop-color="#16287a" stop-opacity=".14"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></radialGradient>
<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG}" stop-opacity="0"/><stop offset="1" stop-color="{BG}"/></linearGradient>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="7"/></filter>
</defs>"""


def svg(width: int, height: int, body: str, label: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" '
            f'height="{height}" role="img" aria-label="{escape(label)}">'
            f"<title>{escape(label)}</title><style>{font_css()}{STYLE}</style>{DEFS}"
            f'<rect width="{width}" height="{height}" fill="{BG}"/>{body}</svg>\n')


def t(x: float, y: float, s: str, size: float = 14, cls: str = "", anchor: str = "start", extra: str = "") -> str:
    c = f' class="{cls}"' if cls else ""
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}"{c}{a}{extra}>{escape(s)}</text>'


def icon(x: float, y: float, code: int, size: float = 15, fill: str = CYAN) -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" style="fill:{fill}">&#x{code:X};</text>'


def width_of(s: str, size: float) -> float:
    return len(s) * size * CW


def clip(s: str, size: float, room: float) -> str:
    n = int(room / (size * CW))
    return s if len(s) <= n else s[: max(n - 1, 1)].rstrip() + "…"


def wrap(s: str, size: float, room: float) -> list[str]:
    return textwrap.wrap(s, max(int(room / (size * CW)), 8))


def cube(cx: float, cy: float, s: float, tint: str, glow: bool = True) -> str:
    """An isometric cube: s is the distance from the centre to the top corner."""
    a = s * 0.866
    top = f"{cx},{cy - s} {cx + a},{cy - s / 2} {cx},{cy} {cx - a},{cy - s / 2}"
    left = f"{cx - a},{cy - s / 2} {cx},{cy} {cx},{cy + s} {cx - a},{cy + s / 2}"
    right = f"{cx},{cy} {cx + a},{cy - s / 2} {cx + a},{cy + s / 2} {cx},{cy + s}"
    halo = f'<circle cx="{cx}" cy="{cy}" r="{s * 1.3:.1f}" fill="{tint}" opacity=".22" filter="url(#soft)"/>' if glow else ""
    edge = f'stroke="{tint}" stroke-opacity=".9" stroke-width="1" stroke-linejoin="round"'
    return (f"{halo}<polygon points='{top}' fill='{tint}' fill-opacity='.55' {edge}/>"
            f"<polygon points='{left}' fill='{tint}' fill-opacity='.28' {edge}/>"
            f"<polygon points='{right}' fill='{tint}' fill-opacity='.12' {edge}/>")


def frame(x: float, y: float, w: float, h: float, title: str, note: str, code: int) -> str:
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="url(#panel)" stroke="{EDGE}"/>'
            f'<rect x="{x + 18}" y="{y}" width="{w - 36}" height="1" fill="url(#rule)"/>'
            + icon(x + 20, y + 31, code)
            + t(x + 44, y + 31, title, 15, "b")
            + t(x + w - 20, y + 31, note, 12.5, "d", "end")
            + f'<rect x="{x + 20}" y="{y + 46}" width="{w - 40}" height="1" fill="url(#rule)" opacity=".6"/>')


# ---------------------------------------------------------------- projects

def fetch_repos() -> list[dict]:
    """Public repos owned by the user, from the GitHub API. Keeps only the fields used."""
    url = f"https://api.github.com/users/{C.USERNAME}/repos?type=owner&per_page=100"
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    if os.environ.get("GITHUB_TOKEN"):
        request.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    with urllib.request.urlopen(request, timeout=20) as response:
        repos = json.load(response)
    keep = ("name", "html_url", "description", "language", "topics", "fork", "archived", "created_at")
    return sorted(({k: r.get(k) for k in keep} for r in repos), key=lambda r: r["created_at"])


def load_repos(offline: bool) -> list[dict]:
    """Fresh from GitHub when possible (and cached), else the last cached copy."""
    if not offline:
        try:
            repos = fetch_repos()
            REPOS_CACHE.write_text(json.dumps(repos, indent=2) + "\n", encoding="utf-8")
            return repos
        except OSError as error:
            print(f"GitHub API unreachable ({error}); using {REPOS_CACHE.name}", file=sys.stderr)
    return json.loads(REPOS_CACHE.read_text(encoding="utf-8")) if REPOS_CACHE.exists() else []


def github_save(repo: dict) -> dict:
    """A save made from what GitHub knows about a repo."""
    lang = repo["language"] or "Code"
    topics = repo["topics"] or []
    stack = [label for topic, label in C.STACK_TOPICS.items() if topic in topics][:2]
    return {
        "name": repo["name"],
        "url": repo["html_url"],
        "icon": C.LANGUAGE_ICONS.get(lang, C.DEFAULT_ICON),
        "lang": lang,
        "desc": repo["description"],
        "stack": " · ".join(stack) or lang,
    }


def projects(repos: list[dict]) -> list[dict]:
    """config.PROJECTS in their order, each filled in from GitHub where it has a repo there,
    then the repos config doesn't mention, oldest first. Forks, archived repos, repos without
    a description and HIDDEN_REPOS are left out."""
    shown = [r for r in repos if not r["fork"] and not r["archived"] and r["description"]
             and r["name"] not in C.HIDDEN_REPOS]
    from_github = {r["name"]: github_save(r) for r in shown}
    saves = [{**from_github.get(p["name"], {}), **p} for p in C.PROJECTS]
    named = {p["name"] for p in C.PROJECTS}
    for name, save in from_github.items():
        if name in named:
            continue
        # The tint used least so far, so a new save stands apart from its neighbours.
        used = [s["tint"] for s in saves]
        save["tint"] = min(C.TINTS, key=used.count)
        saves.append(save)
    return saves


# ---------------------------------------------------------------- hero

def towers(ox: float, oy: float, n: int, unit: float, seed: int, ceiling: float) -> str:
    rnd = random.Random(seed)
    a, b = unit * 0.27, unit * 0.16
    cells = sorted(((i, j) for i in range(n) for j in range(n)), key=lambda c: c[0] + c[1])
    out = []
    for k, (i, j) in enumerate(cells):
        if rnd.random() < 0.42:
            continue
        bx, by = ox + (i - j) * unit * 0.866, oy + (i + j) * unit * 0.5
        middle = 1 - abs(i - j) / n
        h = min(by - ceiling, 10 + rnd.random() ** 2 * 85 + middle * 35)
        if h < 12:
            continue
        lx, rx, fy, ty = bx - a, bx + a, by + b, by - h
        grad = "tower" if rnd.random() < 0.5 else "tower2"
        delay = f"animation-delay:-{rnd.random() * 5:.2f}s"
        out.append(
            f'<g class="pulse" style="{delay}">'
            f"<polygon points='{lx},{by} {bx},{fy} {bx},{fy - h} {lx},{by - h}' fill='url(#{grad})'/>"
            f"<polygon points='{bx},{fy} {rx},{by} {rx},{by - h} {bx},{fy - h}' fill='url(#{grad})' opacity='.6'/>"
            f"<polygon points='{lx},{ty} {bx},{ty + b} {rx},{ty} {bx},{ty - b}' fill='#d6ecff' opacity='.85'/>"
            "</g>")
    return "".join(out)


def motes(x0: float, x1: float, y: float, count: int, seed: int) -> str:
    rnd = random.Random(seed)
    out = []
    for _ in range(count):
        x = x0 + rnd.random() * (x1 - x0)
        yy = y + rnd.random() * 40
        delay = rnd.random() * 9
        out.append(f'<g class="rise" style="animation-delay:-{delay:.2f}s">{cube(x, yy, 3.2 + rnd.random() * 2, CYAN, glow=False)}</g>')
    return "".join(out)


def hero(width: int, phone: bool) -> str:
    h = 250 if phone else 230
    if phone:
        scene_x, unit, n = width - 78, 17, 6
        field = towers(scene_x, 96, n, unit, 11, 36)
        name_size, x0 = 44, 22
    else:
        scene_x, unit, n = 800, 31, 8
        field = towers(scene_x, 52, n, unit, 11, 16)
        name_size, x0 = 58, 40
    fog = f'<ellipse cx="{scene_x}" cy="{h * 0.62}" rx="{unit * n * 1.3}" ry="{h * 0.62}" fill="url(#fog)"/>'
    scene = f'<g opacity="{.45 if phone else 1}">{fog}{field}{motes(scene_x - unit * n * .8, scene_x + unit * n * .8, h - 70, 9, 3)}</g>'
    logo_y = 70 if phone else 78
    name_y = logo_y + name_size * 0.35
    text_x = x0 + 52
    lines = [
        f'<g class="bob">{cube(x0 + 20, logo_y, 19, CYAN)}</g>',
        t(text_x, name_y, C.NAME, name_size, "b", extra=' filter="url(#glow)"'),
        t(text_x + width_of(C.NAME, name_size) + 14, name_y, "@" + C.USERNAME, 15, "d"),
    ]
    y = name_y + (46 if phone else 50)
    lines.append(t(x0, y, C.TAGLINE, 16, "m"))
    y += 36
    prompt = "› " + C.PROMPT
    lines.append(t(x0, y, prompt, 16, "c"))
    lines.append(f'<rect class="blink" x="{x0 + width_of(prompt, 16) + 4:.1f}" y="{y - 14}" width="9" height="17" fill="{CYAN}"/>')
    fade = f'<rect y="{h - 40}" width="{width}" height="40" fill="url(#fade)"/>'
    return svg(width, h, scene + fade + "".join(lines),
               f"{C.NAME} ({C.USERNAME}): {C.TAGLINE}, {C.PROMPT}.")


# ---------------------------------------------------------------- memory card

TILE_H, GAP = 214, 14


def save(x: float, y: float, p: dict, TILE_W: float) -> str:
    tint = p["tint"]
    out = [f'<rect x="{x}" y="{y}" width="{TILE_W}" height="{TILE_H}" rx="12" fill="{tint}" fill-opacity=".05" stroke="{tint}" stroke-opacity=".3"/>',
           f'<g class="bob" style="animation-delay:-{(x % 4):.1f}s">{cube(x + 34, y + 40, 17, tint)}</g>',
           icon(x + 30, y + 46, p["icon"], 13, "#ffffff"),
           t(x + 64, y + 36, clip(p["name"], 14, TILE_W - 76), 14, "b"),
           t(x + 64, y + 54, p["lang"], 12, extra=f' style="fill:{tint}"')]
    yy = y + 88
    for line in wrap(p["desc"], 12.5, TILE_W - 32)[:5]:
        out.append(t(x + 16, yy, line, 12.5, "m"))
        yy += 18
    out.append(f'<rect x="{x + 16}" y="{y + TILE_H - 38}" width="{TILE_W - 32}" height="1" fill="{tint}" opacity=".25"/>')
    out.append(t(x + 16, y + TILE_H - 16, clip(p["stack"], 11.5, TILE_W - 32), 11.5, "d"))
    return "".join(out)


def memory_card(saves: list[dict], phone: bool) -> str:
    cols, width = (2, 520) if phone else (4, 1000)
    rows = -(-len(saves) // cols)
    pw = width - 32
    tile_w = (pw - 40 - (cols - 1) * GAP) / cols
    ph = 62 + rows * TILE_H + (rows - 1) * GAP + 22
    body = [frame(16, 0, pw, ph, "memory card", f"slot 1 · {len(saves)} saves", C.ICON_CARD)]
    for k, p in enumerate(saves):
        r, c = divmod(k, cols)
        # A last row that isn't full is centred under the others.
        in_row = min(cols, len(saves) - r * cols)
        offset = (cols - in_row) * (tile_w + GAP) / 2
        body.append(save(36 + offset + c * (tile_w + GAP), 62 + r * (TILE_H + GAP), p, tile_w))
    return svg(width, ph + 16, "".join(body), "Projects: " + ", ".join(p["name"] for p in saves))


# ---------------------------------------------------------------- now + stack

def now_body(x: float, y: float, w: float) -> tuple[str, float]:
    out, yy, rail = [], y + 80, x + 30
    first = last = yy
    for k, (title, tag, line) in enumerate(C.NOW):
        dot = (f'<circle cx="{rail}" cy="{yy - 5}" r="5" fill="{CYAN}" class="pulse" filter="url(#glow)"/>' if k == 0
               else f'<circle cx="{rail}" cy="{yy - 5}" r="4" fill="{BG}" stroke="{MUTED}"/>')
        out += [dot, t(x + 48, yy, title, 14, "b"), t(x + w - 20, yy, tag, 12, "d", "end")]
        last = yy
        for part in wrap(line, 12.5, w - 70)[:2]:
            yy += 19
            out.append(t(x + 48, yy, part, 12.5, "m"))
        yy += 40
    rail_line = f'<rect x="{rail - .5}" y="{first - 5}" width="1" height="{last - first:.0f}" fill="{EDGE}"/>'
    return rail_line + "".join(out), yy - 40


def chips(x: float, y: float, w: float, items: list[tuple[str, int]]) -> tuple[str, float]:
    out, cx, cy = [], x, y
    for label, code in items:
        cwid = 36 + width_of(label, 12.5)
        if cx + cwid > x + w:
            cx, cy = x, cy + 34
        out.append(f'<rect x="{cx}" y="{cy}" width="{cwid:.1f}" height="26" rx="7" fill="{BLUE}" fill-opacity=".1" stroke="#3a55b0" stroke-opacity=".6"/>')
        out.append(icon(cx + 10, cy + 18, code, 13))
        out.append(t(cx + 28, cy + 17.5, label, 12.5))
        cx += cwid + 8
    return "".join(out), cy + 26


def stack_body(x: float, y: float, w: float) -> tuple[str, float]:
    out, yy = [], y + 72
    for group, items in C.STACK.items():
        out.append(t(x + 20, yy, group, 12, "d"))
        markup, bottom = chips(x + 20, yy + 10, w - 40, items)
        out.append(markup)
        yy = bottom + 28
    return "".join(out), yy - 28


NOW_HEAD = ("now", "on my desk", C.ICON_NOW)
STACK_HEAD = ("stack", "what I build with", C.ICON_STACK)
LABEL = "What I'm working on now, and the tools I use"


def desk_row(phone: bool) -> str:
    if phone:
        w = 488
        now, b1 = now_body(16, 0, w)
        h1 = b1 + 26
        stack, b2 = stack_body(16, h1 + 16, w)
        h2 = b2 + 22 - (h1 + 16)
        body = frame(16, 0, w, h1, *NOW_HEAD) + now + frame(16, h1 + 16, w, h2, *STACK_HEAD) + stack
        return svg(520, h1 + h2 + 32, body, LABEL)
    w = 476
    now, b1 = now_body(16, 0, w)
    stack, b2 = stack_body(16 + w + 16, 0, w)
    h = max(b1 + 26, b2 + 22)
    body = frame(16, 0, w, h, *NOW_HEAD) + now + frame(16 + w + 16, 0, w, h, *STACK_HEAD) + stack
    return svg(1000, h + 16, body, LABEL)


# ---------------------------------------------------------------- README

def readme(saves: list[dict], base: str) -> str:
    def pair(name: str, alt: str, href: str) -> str:
        return (f'<a href="{href}"><picture><source media="{WIDE}" srcset="{base}/{name}.svg" />'
                f'<img src="{base}/{name}-phone.svg" width="100%" align="top" alt="{alt}" /></picture></a>')

    def tech(p: dict) -> str:
        return p["stack"] if p["lang"] in p["stack"] else f"{p['lang']} · {p['stack']}"
    projects = "\n".join(f"- [{p['name']}]({p['url']}): {p['desc']} ({tech(p)})" for p in saves)
    now = "\n".join(f"- **{title}** ({tag}): {line}" for title, tag, line in C.NOW)
    stack = "\n".join(f"- {g.capitalize()}: {', '.join(n for n, _ in items)}" for g, items in C.STACK.items())
    return f"""<!-- Generated by scripts/build.py. Edit scripts/config.py, then run it. -->

<div align="center">
<p>
  {pair("hero", f"{C.NAME}: {C.TAGLINE}, {C.PROMPT}", PROFILE)}
  {pair("memory", "Projects on the memory card", f"{PROFILE}?tab=repositories")}
  {pair("desk", "What I'm working on now, and my stack", PROFILE)}
</p>
</div>

<details>
<summary>Text version, with links</summary>

**Projects**

{projects}

**Now**

{now}

**Stack**

{stack}

</details>

<div align="center">
  <sub>Drawn by <a href="{PROFILE}/{C.USERNAME}/tree/main/scripts">scripts/build.py</a></sub>
</div>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base", default=RAW, help="URL or path the README loads the images from")
    parser.add_argument("--readme", type=Path, default=ROOT / "README.md")
    parser.add_argument("--offline", action="store_true", help="use scripts/repos.json, don't call GitHub")
    args = parser.parse_args()
    saves = projects(load_repos(args.offline))

    out = ROOT / "assets"
    out.mkdir(exist_ok=True)
    files = {
        "hero.svg": hero(1000, False), "hero-phone.svg": hero(520, True),
        "memory.svg": memory_card(saves, False), "memory-phone.svg": memory_card(saves, True),
        "desk.svg": desk_row(False), "desk-phone.svg": desk_row(True),
    }
    for name, content in files.items():
        (out / name).write_text(content, encoding="utf-8", newline="\n")
    args.readme.write_text(readme(saves, args.base), encoding="utf-8", newline="\n")
    print(f"wrote {len(files)} images to {out} and {args.readme} ({len(saves)} saves: "
          + ", ".join(p["name"] for p in saves) + ")")


if __name__ == "__main__":
    main()
