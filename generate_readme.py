#!/usr/bin/env python3
"""Genera los SVGs del perfil con estética de terminal Matrix (paleta Vault-Tec).

Archivos de salida:
  dark_mode.svg / light_mode.svg  → hero neofetch con logo Arch + FX CRT
  project-<slug>.svg             → un SVG por proyecto (clicables vía <a>)
  contact.svg                    → contacto + contador de visitas

Usa solo la API REST pública (sin token): repos, stars y followers.
"""
import os
import re
import urllib.request
import json
import random
import textwrap

USER_NAME = os.environ.get("USER_NAME", "AndresBlancoSierra")
RAW = f"https://raw.githubusercontent.com/{USER_NAME}/{USER_NAME}/main"

GREEN = "#00ff41"
DIM = "#00cc33"
ACCENT = "#39ff14"
FG = "#d9ffe2"
BG = "#050a07"
PANEL = "#0a140d"
BORDER = "#00ff41"
MAGENTA = "#ea36af"
SPLIT = "#75fa69"
MONO = "Consolas,Menlo,monospace"
CW = 9.6  # ancho de caracter monospace a 16px

ARCH_LOGO = """\
      _nnnn_
     dGGGGMMb
    @p~qp~~qMb
    M|@||@) M|
    @,----.JM|
   JS^\\__/  qKL
  dZP        qKRb
 dZP          qKKb
fZP            SMMb
HZM            MMMM
FqM            MMMM
__| ".        |\\dS"qML
|    `.       | `' \\Zq
_)      \\___,      .
\\____   )MMMMMP   .
     `-'       `--'
       ARCH LINUX""".splitlines()

LANG_ICONS = {
    "Python": "python",
    "TypeScript": "typescript",
    "JavaScript": "javascript",
    "C++": "cplusplus",
    "C": "c",
    "Java": "java",
    "Go": "go",
    "Rust": "rust",
    "HTML": "html5",
    "CSS": "css",
    "Shell": "gnubash",
    "Arduino": "arduino",
    "Vue": "vuedotjs",
    "Dart": "dart",
}

CONTACT = [
    ("EMAIL", "andresfelipeblancos15@gmail.com"),
    ("LOCATION", "Bogotá, Colombia · open to remote"),
]


def public_stats():
    stats = {"repos": 0, "stars": 0, "followers": 0}
    try:
        req = urllib.request.Request(
            f"https://api.github.com/users/{USER_NAME}",
            headers={"User-Agent": "profile-readme", "Accept": "application/vnd.github+json"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            user = json.loads(r.read())
        stats["repos"] = int(user.get("public_repos", 0))
        stats["followers"] = int(user.get("followers", 0))
        page = 1
        while True:
            req = urllib.request.Request(
                f"https://api.github.com/users/{USER_NAME}/repos?per_page=100&page={page}&type=owner",
                headers={"User-Agent": "profile-readme", "Accept": "application/vnd.github+json"},
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                repos = json.loads(r.read())
            if not repos:
                break
            stats["stars"] += sum(int(rp.get("stargazers_count", 0)) for rp in repos)
            if len(repos) < 100:
                break
            page += 1
    except Exception as e:
        print(f"[warn] no se pudieron obtener stats públicas: {e}")
    return stats


def graphql(query):
    """Ejecuta una consulta GraphQL con el token disponible (GITHUB_TOKEN o fallback)."""
    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {"User-Agent": "profile-readme", "Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers=headers,
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def pinned_projects():
    """Lee los proyectos fijados del perfil (pinnedItems) vía GraphQL."""
    q = """{ user(login: "USER") {
      pinnedItems(first: 6, types: REPOSITORY) {
        nodes { ... on Repository { name description primaryLanguage { name } } }
      } } }""".replace("USER", USER_NAME)
    try:
        data = graphql(q)
        nodes = data["data"]["user"]["pinnedItems"]["nodes"]
    except Exception as e:
        print(f"[warn] no se pudieron leer proyectos fijados: {e}")
        return []
    out = []
    for n in nodes:
        lang = (n.get("primaryLanguage") or {}).get("name", "")
        icon = LANG_ICONS.get(lang, "")
        out.append((n["name"], n["name"], n.get("description") or "", icon))
    return out


def visitor_count():
    """Lee el contador de visitas (visitorbadge.io) y devuelve el número."""
    try:
        req = urllib.request.Request(
            f"https://api.visitorbadge.io/api/visitors?path={USER_NAME}",
            headers={"User-Agent": "profile-readme"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            svg = r.read().decode()
        m = re.search(r'<title>VISITORS:?\s*(\d+)</title>', svg)
        if m:
            return m.group(1)
    except Exception as e:
        print(f"[warn] no se pudo obtener el contador de visitas: {e}")
    return ""


_ICON_CACHE = {}


def icon_path(name):
    """Devuelve el <path> de un icono de simple-icons recoloreado a verde."""
    if name in _ICON_CACHE:
        return _ICON_CACHE[name]
    path = ""
    try:
        req = urllib.request.Request(
            f"https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/{name}.svg",
            headers={"User-Agent": "profile-readme"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read().decode()
        m = re.search(r'<path[^>]*d="([^"]+)"', raw)
        if m:
            path = f'<path d="{m.group(1)}" fill="{GREEN}"/>'
    except Exception as e:
        print(f"[warn] no se pudo descargar el icono {name}: {e}")
    _ICON_CACHE[name] = path
    return path


# ================= CSS compartido (FX Vault-Tec) =================

def fx_css(svg_h):
    return f"""
text {{ white-space: pre; }}
.glitch {{ animation: glitch 3s steps(1) 1; }}
@keyframes glitch {{
  0%   {{ transform: translate(0); }}
  5%   {{ transform: translate(-2px, 1px); }}
  10%  {{ transform: translate(2px, -1px); }}
  15%  {{ transform: translate(-1px, 0); }}
  20%  {{ transform: translate(0); }}
  100% {{ transform: translate(0); }}
}}
.gfx {{ animation: glitchfx 11s steps(1) infinite; }}
@keyframes glitchfx {{
  0%, 38% {{ transform: translate(0,0) skewX(0); }}
  39%     {{ transform: translate(-3px,1px) skewX(-2deg); }}
  41%     {{ transform: translate(4px,-2px) skewX(3deg); }}
  43%     {{ transform: translate(-2px,2px) skewX(-1deg); }}
  45%     {{ transform: translate(0,0) skewX(0); }}
  68%     {{ transform: translate(0,0) skewX(0); }}
  69%     {{ transform: translate(3px,-1px) skewX(2deg); }}
  71%     {{ transform: translate(-4px,1px) skewX(-3deg); }}
  73%     {{ transform: translate(0,0) skewX(0); }}
  100%    {{ transform: translate(0,0) skewX(0); }}
}}
.chan {{ animation: chsplit 11s steps(1) infinite; }}
@keyframes chsplit {{
  0%, 38% {{ opacity: 0; }}
  39%     {{ opacity: 0.9; }}
  45%     {{ opacity: 0; }}
  68%     {{ opacity: 0; }}
  69%     {{ opacity: 0.9; }}
  73%     {{ opacity: 0; }}
  100%    {{ opacity: 0; }}
}}
.flicker {{ animation: screenflicker .15s infinite; }}
@keyframes screenflicker {{
  0% {{ opacity: .04; }} 5% {{ opacity: .07; }} 10% {{ opacity: .04; }} 15% {{ opacity: .08; }}
  20% {{ opacity: .05; }} 25% {{ opacity: .07; }} 30% {{ opacity: .04; }} 35% {{ opacity: .06; }}
  40% {{ opacity: .08; }} 45% {{ opacity: .05; }} 50% {{ opacity: .06; }} 55% {{ opacity: .04; }}
  60% {{ opacity: .07; }} 65% {{ opacity: .05; }} 70% {{ opacity: .07; }} 75% {{ opacity: .04; }}
  80% {{ opacity: .06; }} 85% {{ opacity: .05; }} 90% {{ opacity: .07; }} 95% {{ opacity: .04; }}
  100% {{ opacity: .06; }}
}}
.noise {{ animation: noisejump .35s steps(3) infinite; }}
@keyframes noisejump {{
  0%   {{ transform: translate(0,0); }}
  33%  {{ transform: translate(-6px,3px); }}
  66%  {{ transform: translate(4px,-5px); }}
  100% {{ transform: translate(-2px,2px); }}
}}
.scanbar {{ animation: scanbar 7s linear infinite; }}
@keyframes scanbar {{
  0%   {{ transform: translateY(-90px); }}
  100% {{ transform: translateY({svg_h + 20}px); }}
}}
"""


def fx_overlays(svg_w, svg_h):
    return f"""<rect width="{svg_w}" height="{svg_h}" fill="url(#scan)" opacity="0.5"/>
<rect class="flicker" width="{svg_w}" height="{svg_h}" fill="#000000" opacity="0.04"/>
<rect class="noise" width="{svg_w}" height="{svg_h}" filter="url(#noise)" opacity="0.05"/>
<rect class="scanbar" width="{svg_w}" height="60" fill="url(#sbg)" opacity="0.3"/>"""


def crt_head(svg_w, svg_h):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{svg_w}px" height="{svg_h}px" font-family="{MONO}" font-size="16px">
<defs>
<style>{fx_css(svg_h)}</style>
<filter id="noise" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="2"/>
  <feColorMatrix type="saturate" values="0"/>
</filter>
<pattern id="scan" width="3" height="3" patternUnits="userSpaceOnUse">
  <rect width="3" height="1" fill="#000000"/>
</pattern>
<linearGradient id="sbg" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="{GREEN}" stop-opacity="0"/>
  <stop offset="0.5" stop-color="{GREEN}" stop-opacity="0.3"/>
  <stop offset="1" stop-color="{GREEN}" stop-opacity="0"/>
</linearGradient>
</defs>
<rect width="100%" height="100%" fill="{PANEL}" rx="12"/>
<rect x="3" y="3" width="{svg_w - 6}" height="{svg_h - 6}" fill="none" stroke="{BORDER}" stroke-width="1" rx="10" opacity="0.35"/>
"""


def plain_css():
    """CSS mínimo para secciones transparentes (sin glitch)."""
    return """
text {{ white-space: pre; }}
"""


def plain_head(svg_w, svg_h):
    """Cabecera sin fondo, sin borde y sin overlays: solo texto Matrix sobre transparente."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{svg_w}px" height="{svg_h}px" font-family="{MONO}" font-size="16px">
<defs>
<style>{plain_css()}</style>
</defs>
"""


def glitch_text(x, y, text, size=16):
    """Render texto con canal RGB + burst periódico (estilo Fallout)."""
    base = f'<text x="{x}" y="{y}" fill="{GREEN}" font-size="{size}">{text}</text>'
    a = f'<text class="chan" x="{x - 3}" y="{y + 1}" fill="{MAGENTA}" font-size="{size}">{text}</text>'
    b = f'<text class="chan" x="{x + 3}" y="{y - 1}" fill="{SPLIT}" font-size="{size}">{text}</text>'
    return f'<g class="gfx">{base}{a}{b}</g>'


def header_line(x, y, label):
    """Título de sección en negrita, sin glitch, con salto de línea después."""
    return (f'<text x="{x}" y="{y}" fill="{GREEN}" font-weight="bold">andres@arch</text>'
            f'<text x="{x + len("andres@arch") * CW}" y="{y}" fill="{DIM}" font-weight="bold">:~$ </text>'
            f'<text x="{x + len("andres@arch:~$ ") * CW}" y="{y}" fill="{ACCENT}" font-weight="bold"># {label}</text>')


# ================= Hero (dark/light) =================

def build_hero(theme):
    fg = FG if theme == "dark" else "#0a1f10"
    bg = BG if theme == "dark" else "#f0faf3"
    panel = PANEL if theme == "dark" else "#e6f5ea"

    s = stats
    art_width = max(len(l) for l in ARCH_LOGO)
    art_height = len(ARCH_LOGO)

    info_x = 15 + art_width * CW + 45
    svg_w = int(info_x + 430)

    tspans = []
    y = 25
    for line in ARCH_LOGO:
        tspans.append(f'<tspan x="15" y="{y}">{line}</tspan>')
        y += 22

    random.seed(7)
    rain_cols = []
    rain_chars = "01アイウエオカキクケコサシスセソ$#%*+=-~^"
    for _ in range(14):
        x = random.randint(10, svg_w - 10)
        dur = round(random.uniform(4.5, 9.0), 1)
        delay = round(random.uniform(-9.0, 0.0), 1)
        col = "".join(random.choice(rain_chars) for _ in range(random.randint(6, 14)))
        tsp = "".join(
            f'<tspan x="{x}" y="{24 + r_idx * 22}">{c}</tspan>'
            for r_idx, c in enumerate(col)
        )
        rain_cols.append(
            f'<g class="rain" style="animation-duration:{dur}s;animation-delay:{delay}s">{tsp}</g>'
        )

    info = []
    info.append(f'<text x="{info_x}" y="25" fill="{fg}" font-size="16" font-family="{MONO}">')
    info.append(f'<tspan x="{info_x}" y="25" class="glitch" fill="{GREEN}">andres@arch</tspan>'
                f'<tspan class="cursor" fill="{ACCENT}">▌</tspan>'
                f'<tspan fill="{DIM}"> ─────────────────────────────</tspan>')
    rows = [
        ("OS", "Arch Linux + Hyprland"),
        ("WM", "Hyprland (Wayland)"),
        ("Shell", "bash/zsh"),
        ("Role", "Systems Engineer — EAN, Bogotá"),
        ("English", "B2"),
        ("Languages", "Python · TypeScript · C++ · Bash"),
        ("AI/ML", "Whisper · CLIP · OCR · InsightFace"),
        ("Backend", "FastAPI · SQLAlchemy"),
        ("Frontend", "React · Vite · Tailwind"),
        ("DevOps", "Docker · systemd · GitHub Actions"),
        ("Hardware", "Arduino · uinput · Wine"),
        ("Focus", "Applied AI + cyberpunk aesthetics"),
    ]
    yy = 55
    for k, v in rows:
        info.append(f'<tspan x="{info_x}" y="{yy}" fill="{DIM}">.</tspan>'
                    f'<tspan fill="{GREEN}">{k}</tspan>'
                    f'<tspan fill="{DIM}">: </tspan>'
                    f'<tspan fill="{fg}">{v}</tspan>')
        yy += 24

    yy += 6
    info.append(f'<tspan x="{info_x}" y="{yy}" fill="{GREEN}"> ─── GitHub Stats ───</tspan>')
    yy += 24
    info.append(f'<tspan x="{info_x}" y="{yy}" fill="{DIM}">.</tspan>'
                f'<tspan fill="{GREEN}">Repos</tspan><tspan fill="{DIM}">: {s["repos"]:>4}</tspan>'
                f'<tspan fill="{DIM}">   </tspan><tspan fill="{GREEN}">Stars</tspan><tspan fill="{DIM}">: {s["stars"]:>4}</tspan>')
    yy += 24
    info.append(f'<tspan x="{info_x}" y="{yy}" fill="{DIM}">.</tspan>'
                f'<tspan fill="{GREEN}">Followers</tspan><tspan fill="{DIM}">: {s["followers"]:>4}</tspan>'
                f'<tspan fill="{DIM}">   </tspan><tspan fill="{GREEN}">Status</tspan><tspan fill="{ACCENT}">: OPEN TO WORK</tspan>')
    info.append('</text>')

    svg_h = yy + 40

    logo_block = (
        f'<g class="gfx">'
        f'<text fill="{GREEN}">{"".join(tspans)}</text>'
        f'<text class="chan" fill="{MAGENTA}" transform="translate(-3,1)">{"".join(tspans)}</text>'
        f'<text class="chan" fill="{SPLIT}" transform="translate(3,-1)">{"".join(tspans)}</text>'
        f'</g>'
    )

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}px" height="{svg_h}px" font-family="{MONO}" font-size="16px">
<defs>
<style>
text {{ white-space: pre; }}
.cursor {{ animation: blink 1.1s step-end infinite; }}
@keyframes blink {{ 50% {{ opacity: 0; }} }}
.rain {{ animation-name: fall; animation-timing-function: linear; animation-iteration-count: infinite; fill: {GREEN}; opacity: 0; }}
@keyframes fall {{
  0%   {{ transform: translateY(-120%); opacity: 0; }}
  10%  {{ opacity: 0.35; }}
  90%  {{ opacity: 0.25; }}
  100% {{ transform: translateY(120%); opacity: 0; }}
}}
.glitch {{ animation: glitch 3s steps(1) 1; }}
@keyframes glitch {{
  0%   {{ transform: translate(0); }}
  5%   {{ transform: translate(-2px, 1px); }}
  10%  {{ transform: translate(2px, -1px); }}
  15%  {{ transform: translate(-1px, 0); }}
  20%  {{ transform: translate(0); }}
  100% {{ transform: translate(0); }}
}}
.gfx {{ animation: glitchfx 11s steps(1) infinite; }}
@keyframes glitchfx {{
  0%, 38% {{ transform: translate(0,0) skewX(0); }}
  39%     {{ transform: translate(-3px,1px) skewX(-2deg); }}
  41%     {{ transform: translate(4px,-2px) skewX(3deg); }}
  43%     {{ transform: translate(-2px,2px) skewX(-1deg); }}
  45%     {{ transform: translate(0,0) skewX(0); }}
  68%     {{ transform: translate(0,0) skewX(0); }}
  69%     {{ transform: translate(3px,-1px) skewX(2deg); }}
  71%     {{ transform: translate(-4px,1px) skewX(-3deg); }}
  73%     {{ transform: translate(0,0) skewX(0); }}
  100%    {{ transform: translate(0,0) skewX(0); }}
}}
.chan {{ animation: chsplit 11s steps(1) infinite; }}
@keyframes chsplit {{
  0%, 38% {{ opacity: 0; }}
  39%     {{ opacity: 0.9; }}
  45%     {{ opacity: 0; }}
  68%     {{ opacity: 0; }}
  69%     {{ opacity: 0.9; }}
  73%     {{ opacity: 0; }}
  100%    {{ opacity: 0; }}
}}
.flicker {{ animation: screenflicker .15s infinite; }}
@keyframes screenflicker {{
  0% {{ opacity: .04; }} 5% {{ opacity: .07; }} 10% {{ opacity: .04; }} 15% {{ opacity: .08; }}
  20% {{ opacity: .05; }} 25% {{ opacity: .07; }} 30% {{ opacity: .04; }} 35% {{ opacity: .06; }}
  40% {{ opacity: .08; }} 45% {{ opacity: .05; }} 50% {{ opacity: .06; }} 55% {{ opacity: .04; }}
  60% {{ opacity: .07; }} 65% {{ opacity: .05; }} 70% {{ opacity: .07; }} 75% {{ opacity: .04; }}
  80% {{ opacity: .06; }} 85% {{ opacity: .05; }} 90% {{ opacity: .07; }} 95% {{ opacity: .04; }}
  100% {{ opacity: .06; }}
}}
.noise {{ animation: noisejump .35s steps(3) infinite; }}
@keyframes noisejump {{
  0%   {{ transform: translate(0,0); }}
  33%  {{ transform: translate(-6px,3px); }}
  66%  {{ transform: translate(4px,-5px); }}
  100% {{ transform: translate(-2px,2px); }}
}}
.scanbar {{ animation: scanbar 7s linear infinite; }}
@keyframes scanbar {{
  0%   {{ transform: translateY(-90px); }}
  100% {{ transform: translateY({svg_h + 20}px); }}
}}
</style>
</defs>
<filter id="noise" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="2"/>
  <feColorMatrix type="saturate" values="0"/>
</filter>
<pattern id="scan" width="3" height="3" patternUnits="userSpaceOnUse">
  <rect width="3" height="1" fill="#000000"/>
</pattern>
<linearGradient id="sbg" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="{GREEN}" stop-opacity="0"/>
  <stop offset="0.5" stop-color="{GREEN}" stop-opacity="0.3"/>
  <stop offset="1" stop-color="{GREEN}" stop-opacity="0"/>
</linearGradient>
<rect width="100%" height="100%" fill="{panel}" rx="12"/>
<rect x="4" y="4" width="{svg_w - 8}" height="{svg_h - 8}" fill="none" stroke="{BORDER}" stroke-width="1" rx="10" opacity="0.35"/>
<g id="rain">{"".join(rain_cols)}</g>
{logo_block}
{"".join(info)}
<rect width="100%" height="100%" fill="url(#scan)" opacity="0.5"/>
<rect class="flicker" width="100%" height="100%" fill="#000000" opacity="0.04"/>
<rect class="noise" width="100%" height="100%" filter="url(#noise)" opacity="0.05"/>
<rect class="scanbar" width="100%" height="70" fill="url(#sbg)" opacity="0.35"/>
</svg>
'''
    return svg


# ================= Projects (un SVG por fila, clicables) =================

def build_project(name, slug, desc, icon_name, width):
    pad_x = 18
    icon_size = 22
    wrap = 78
    lines = textwrap.wrap(desc, wrap) or [desc]
    url = f"→ https://github.com/{USER_NAME}/{slug}"

    y = 24
    body = [header_line(pad_x, y, f"ls {slug}")]
    y += 24

    icon = icon_path(icon_name)
    icon_x = pad_x
    icon_y = y - icon_size + 6
    if icon:
        body.append(
            f'<g transform="translate({icon_x}, {icon_y})">'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{icon_size}" height="{icon_size}" '
            f'viewBox="0 0 24 24">{icon}</svg></g>'
        )

    text_x = icon_x + (icon_size + 8 if icon else 0)
    body.append(f'<text x="{text_x}" y="{y}" fill="{ACCENT}">▸ </text>'
                f'<text x="{text_x + 2 * CW}" y="{y}" fill="{GREEN}">{name}</text>')
    y += 24
    for l in lines:
        body.append(f'<text x="{text_x}" y="{y}" fill="{DIM}">{l}</text>')
        y += 24
    body.append(f'<text x="{text_x}" y="{y}" fill="{DIM}">{url}</text>')
    y += 24

    svg = (plain_head(width, y) + "".join(body) + "</svg>\n")
    return svg


# ================= Contact =================

def build_contact(visitors):
    pad_x = 18
    rows = CONTACT + [("VISITORS", visitors or "?"), ("STATUS", "open to remote worldwide")]
    max_chars = max(len(k) + 3 + len(v) for k, v in rows)
    width = int(pad_x * 2 + max_chars * CW + 10)

    body = [header_line(pad_x, 24, "contact")]
    y = 48
    for k, v in rows:
        body.append(f'<text x="{pad_x}" y="{y}" fill="{ACCENT}">{k}</text>'
                    f'<text x="{pad_x + (len(k) + 3) * CW}" y="{y}" fill="{GREEN}">{v}</text>')
        y += 24
    y += 10

    svg = (plain_head(width, y) + "".join(body) + "</svg>\n")
    return svg


# ================= Streak =================

def streak_stats():
    """Computa total, current y longest streak desde la creación de la cuenta."""
    total = 0
    cur_streak = 0
    longest = 0
    try:
        from datetime import datetime, timedelta
        today = datetime.now().date()
        start = datetime(2023, 3, 16).date()
        all_days = {}
        cursor = start
        while cursor < today:
            end = min(cursor + timedelta(days=364), today)
            q = ('{ user(login: "U") { contributionsCollection('
                 f'from: "{cursor}T00:00:00Z", to: "{end}T00:00:00Z") '
                 '{ contributionCalendar { totalContributions '
                 'weeks { contributionDays { contributionCount date } } } } } }').replace("U", USER_NAME)
            data = graphql(q)
            cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
            total += cal["totalContributions"]
            for w in cal["weeks"]:
                for dd in w["contributionDays"]:
                    all_days[dd["date"]] = dd["contributionCount"]
            cursor = end + timedelta(days=1)

        run = 0
        for date_str, count in sorted(all_days.items()):
            run = run + 1 if count > 0 else 0
            longest = max(longest, run)
        # current streak: hoy hacia atrás (o ayer si hoy es 0)
        today_str = today.isoformat()
        cur = 0
        day = today
        if all_days.get(today_str, 0) == 0:
            day = today - timedelta(days=1)
        while day.isoformat() in all_days and all_days[day.isoformat()] > 0:
            cur += 1
            day -= timedelta(days=1)
        cur_streak = cur
    except Exception as e:
        print(f"[warn] no se pudo calcular el streak: {e}")
    return {"total": total, "current": cur_streak, "longest": longest}


def build_streak(streak):
    pad_x = 18
    rows = [
        ("TOTAL", f"{streak['total']:,} contributions"),
        ("CURRENT", f"▸ {streak['current']} day{'s' if streak['current'] != 1 else ''}"),
        ("LONGEST", f"▸ {streak['longest']} day{'s' if streak['longest'] != 1 else ''}"),
    ]
    max_chars = max(len(k) + 3 + len(v) for k, v in rows)
    width = int(pad_x * 2 + max_chars * CW + 10)

    body = [header_line(pad_x, 24, "streak")]
    y = 48
    for k, v in rows:
        body.append(f'<text x="{pad_x}" y="{y}" fill="{ACCENT}">{k}</text>'
                    f'<text x="{pad_x + (len(k) + 3) * CW}" y="{y}" fill="{GREEN}">{v}</text>')
        y += 24
    y += 10

    svg = (plain_head(width, y) + "".join(body) + "</svg>\n")
    return svg


if __name__ == "__main__":
    stats = public_stats()
    out = {}

    dark = build_hero("dark")
    light = build_hero("light")
    out["dark_mode.svg"] = dark
    out["light_mode.svg"] = light

    projects = pinned_projects()
    if not projects:
        print("[warn] no hay proyectos fijados, se usa la lista por defecto")
        projects = [
            ("what", "what", "Learn languages with songs.", "python"),
            ("cp2077-ui-react", "cp2077-ui-react", "Cyberpunk 2077 UI replica.", "react"),
        ]
    max_width = 0
    for _, slug, desc, _ in projects:
        lines = textwrap.wrap(desc or "", 78) or [desc or ""]
        url = f"→ https://github.com/{USER_NAME}/{slug}"
        longest = max(len(slug) + 2, max(len(l) for l in lines), len(url), len("andres@arch:~$ ls"))
        max_width = max(max_width, int(18 * 2 + longest * CW + 30))

    for name, slug, desc, icon in projects:
        out[f"project-{slug}.svg"] = build_project(name, slug, desc, icon, max_width)

    out["contact.svg"] = build_contact(visitor_count())
    out["streak.svg"] = build_streak(streak_stats())

    for name, content in out.items():
        with open(name, "w") as f:
            f.write(content)
        print(f"✓ {name} ({len(content)} bytes)")
    print(f"stats: repos={stats['repos']} stars={stats['stars']} followers={stats['followers']}")
