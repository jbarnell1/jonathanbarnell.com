"""Builds the portfolio page from template.html.

Outputs:
  docs/           - the site GitHub Pages serves at jonathanbarnell.com (full document, images as files)
  portfolio.html  - single file for a Claude artifact (images inlined, no doctype; the host wraps it)
  index.html      - same content with a document skeleton, for opening locally
Run: python build.py
"""
import base64, html, json, pathlib, re, shutil, struct

HERE = pathlib.Path(__file__).parent
GH = "https://github.com/jbarnell1/"

# key, name, label, colour group, years, blurb, facts[(k, v)], links[(text, url)], image, alt
# Live projects come first. The first fact of every project is its state, and it starts with one
# of: Live, Released, In progress, Private, Finished, Past.
PROJECTS = [
 ("buoy", "Buoy Money", "Product", "product", "2025 to now",
  "A budgeting app where each category earns a daily allowance, so the budget counts up as the month goes on. There is a hosted edition and a free self-hosted one.",
  [("State", "Live on the web and Google Play"), ("Built with", "Flutter, .NET 10, PostgreSQL"), ("Connects to", "Plaid, Stripe, MCP"), ("Releases", "78, latest v1.5.37")],
  [("buoymoney.com", "https://buoymoney.com"), ("Source", "https://github.com/BuoyMoney/buoy-money")],
  "buoy-budgets", "Buoy Money budgets screen on desktop"),
 ("scripture", "Scripture Solace", "Media", "play", "2024 to now",
  "A pipeline that picks a passage, narrates it, matches music and footage, burns in word-synced subtitles and uploads to YouTube three mornings a week. Passages come only from a hand-curated table, so a verse is never lifted out of its context.",
  [("State", "Live on YouTube"), ("Built with", "Python, Gemini, ElevenLabs, ffmpeg"), ("Uploads", "417"), ("Views", "About 60,000")],
  [("Watch the channel", "https://www.youtube.com/@scriptureSolace-13354")], None, None),
 ("highlights", "Highlights", "Home", "home", "2026",
  "Highlight videos from a self-hosted Immich photo library. Claude picks the moments from contact sheets, ffmpeg cuts them, and the finished video lands back in Immich.",
  [("State", "Released, in maintenance"), ("Built with", "Python, FastAPI, ffmpeg"), ("Finds trips by", "Distance from the place you are most often"), ("Release", "v0.2.1")],
  [("Source", GH + "highlights")], "highlights-sheets", "Contact sheets of trip photos that the model picks from"),
 ("selfkept", "SelfKept", "Home", "home", "2026",
  "A self-hosted health record for a household. Sleep, activity, heart rate and blood panels from everyone's phones and watches, compared with each person's own 28-day range and described in plain words.",
  [("State", "Released, still changing most weeks"), ("Built with", ".NET 10, Flutter, PostgreSQL"), ("AI", "Local models only, by default")],
  [("Source", GH + "selfkept")], "selfkept-desktop", "SelfKept heart and fitness readings on desktop"),
 ("watchman", "Watchman", "Home", "home", "2026",
  "Self-hosted accountability and real-time image protection. Images are judged on the device, explicit ones are blurred, and chosen partners get a weekly digest. It is open source, because internet safety should not sit behind an $18 a month charge.",
  [("State", "Released, in daily use at home"), ("Server", "Python, FastAPI, ONNX Runtime"), ("Clients", "Android, Windows, browsers; iOS in testing"), ("Licence", "AGPL-3.0")],
  [("Source", GH + "watchman")], "watchman-timeline", "Watchman timeline showing hours protected across three devices"),
 ("stringart", "String Art Studio", "Making", "hard", "2026",
  "Turns a photo into a pin-and-thread build plan, then reads the steps aloud from a phone while you string. One engine solves the whole piece as a single continuous thread.",
  [("State", "In progress: the software works, no physical build yet"), ("Built with", "Python, numpy, Numba"), ("Exports", "True-size templates, a printable drilling jig, DXF"), ("Licence", "MIT")],
  [("Source", GH + "string-art-studio")], "stringart-hero", "A portrait beside two string art renders and the phone build mode"),
 ("listener", "Listener", "Hardware", "hard", "2026",
  "An all-day audio wearable on a circuit board I designed around an ESP32-S3. It uploads to a GPU server at home that transcribes, works out who was speaking and pulls out tasks, so no company holds a recording of my day.",
  [("State", "In progress: board built and working, files not yet published"), ("Board", "Custom two-layer PCB, 87 by 65 mm"), ("Server", "WhisperX, pyannote, Ollama"), ("Decision records", "57")],
  [("Source", GH + "listener")], None, None),
 ("goingdown", "Going Down", "Game", "play", "2026",
  "A co-op suspense game for up to eight players. Convicts ride a lift down through a buried city and are paid for instrument readings taken close to things that each obey one unbreakable rule. There are no weapons.",
  [("State", "In progress: playable in a browser, no ending yet"), ("Built with", "Godot 4, typed GDScript"), ("Characters", "Built and rigged by Blender scripts")],
  [("Source", GH + "going-down"), ("Play the first browser version", "https://jbarnell1.github.io/going-down/")],
  "gd-tape", "In-game view with a tape filter: a gaunt figure in a clinic corridor"),
 ("dockeeper", "Doc Keeper", "Home", "home", "2026",
  "A private archive for a household's important documents, plus a home inventory. A local vision model reads each scan, and search combines full text, trigrams and vectors.",
  [("State", "Private, runs at home"), ("Built with", "Paperless-ngx, FastAPI, SQLite, Ollama"), ("Reads", "Licence barcodes and passport MRZ lines"), ("Backups", "Nightly, with a restore check")],
  [], None, None),
 ("router", "Local model router", "Home", "home", "2026",
  "A small model reads each chat message and sends it to a fast 9B model or a slower 35B one, so the household assistant answers quickly when it can. A guard strips household tools and memories before anything goes to a cloud model.",
  [("State", "Private, runs at home"), ("Runs on", "Ollama, Open WebUI"), ("Hardware", "One 12 GB GPU")],
  [], None, None),
 ("homelab", "The homelab", "Home", "home", "Ongoing",
  "Two machines at home running about 48 containers: photos, media, documents, passwords and monitoring. Everything is reachable only over Tailscale, with no ports forwarded.",
  [("State", "Private, runs at home"), ("Runs on", "Docker, Tailscale, AdGuard Home"), ("GPU", "RTX 4070 Super, for local models"), ("Backups", "Hourly, with restic")],
  [], None, None),
 ("khel", "Kansas pipeline", "Science", "early", "2021",
  "The Python package I wrote at the Kansas state lab to move SARS-CoV-2 sequencing data from the instruments to the epidemiologists.",
  [("State", "Finished, and the code is public"), ("Built with", "Python, pandas, Oracle, SQL Server"), ("Size", "8 workflows, 186 commits"), ("Licence", "MIT")],
  [("Source", GH + "KHEL_WGS_SARS_CoV_2")], None, None),
 ("kismet", "Kismet research", "Science", "early", "2019",
  "Undergraduate research on kismet, the fruit fly counterpart of the human gene CHD7, and its part in muscle growth and development.",
  [("State", "Finished"), ("Lab", "Washburn University"), ("Presented", "ASCB annual meeting, Washington, D.C., 2019")],
  [], None, None),
 ("crickets", "Arbor", "Business", "early", "2018",
  "A startup that six Washburn students formed to farm crickets and sell protein powder. It began as Agrotech Enterprises and became Arbor. I directed research and development. We won the Washburn pitch competition, placed in the top five at regional, national and international contests, and the Associated Press carried the story.",
  [("State", "Past venture"), ("My part", "Research and development"), ("Plan", "A gravity-fed feeder in place of costly robotics"), ("Covered by", "Associated Press, Topeka Capital-Journal")],
  [("AP story", "https://archive.salinapost.com/?p=340116"),
   ("Capital-Journal feature", "https://web.archive.org/web/20190508221648/https://www.cjonline.com/news/20181126/overcoming-ick-factor-topeka-start-up-focuses-on-cricket-based-food"),
   ("Washburn Review on Arbor", "https://washburnreview.org/648/features/foreman-the-cricket-guy/")], None, None),
]

# extra pictures under a panel: key -> [(image, alt, caption)]
MORE = {
 "listener": [
  ("listener-board", "3D render of the Listener circuit board: an ESP32-S3 module, USB-C port, battery connector, flash chip and five buttons", "The board, rendered from the layout."),
  ("listener-dashboard", "Listener review queue on desktop", "The review queue, with invented data."),
  ("listener-sch-power", "Listener power schematic: USB-C connector, ESD protection, charger, load sharing, regulator and battery sensing", "Power: USB-C in, charger, load sharing, regulator, battery sense."),
  ("listener-sch-mcu", "Listener schematic of the ESP32-S3 module, its switches and the NAND flash chip", "The ESP32-S3 and the flash chip that holds a day of audio."),
 ],
}

# a 3D model shown over one of the MORE pictures: image name -> (GLB in media/, spoken label, caption once it is live)
MODELS = {
 "listener-board": ("listener-board.glb",
                    "The Listener circuit board in 3D. Drag, or use the left and right arrow keys, to turn it.",
                    "The board in 3D, exported from the layout. Drag to turn it."),
}

# a film in a panel's picture slot: key -> (media stem, width, height, spoken label, caption)
FILMS = {
 "scripture": ("scripture", 540, 960, "A Scripture Solace short: a psalm narrated over footage, with subtitles that follow each word",
               "One of the shorts, as uploaded. Muted here."),
}

# a live frame that loads only when asked: key -> (url, poster image, frame title, button, caption)
EMBEDS = {
 "goingdown": ("https://jbarnell1.github.io/going-down/", "gd-lineup", "Going Down, the first browser version", "Play it here",
               "The first browser version. It loads from GitHub Pages when you press the button, and it is a large download."),
}

e = html.escape


def webp_size(name):
    """Width and height of img/<name>.webp, read from the file header, so pictures hold their place before they load."""
    b = (HERE / "img" / f"{name}.webp").read_bytes()[:40]
    kind = b[12:16]
    if kind == b"VP8X":
        return 1 + int.from_bytes(b[24:27], "little"), 1 + int.from_bytes(b[27:30], "little")
    if kind == b"VP8 ":
        w, h = struct.unpack("<HH", b[26:30])
        return w & 0x3FFF, h & 0x3FFF
    if kind == b"VP8L":
        bits = int.from_bytes(b[21:25], "little")
        return 1 + (bits & 0x3FFF), 1 + ((bits >> 14) & 0x3FFF)
    raise ValueError(f"not a WebP header: {name}")


def img(name, alt):
    w, h = webp_size(name)
    return f'<img src="img/{name}.webp" width="{w}" height="{h}" loading="lazy" alt="{e(alt)}">'


def spines():
    out = []
    for k, name, label, group, *_ in PROJECTS:
        out.append(f'      <a class="spine" href="#p-{k}" aria-controls="p-{k}" data-g="{group}"><span class="nm">{e(name)}</span><span class="dc">{e(label)}</span></a>')
    return "\n".join(out)


def more_figure(name, alt, cap):
    """One picture under a panel. A picture with a 3D model keeps the still as the fallback."""
    if name in MODELS:
        glb, say, cap3d = MODELS[name]
        return (f'<figure class="model" data-model="media/{glb}"><div class="frame3d">'
                f'{img(name, alt)}'
                f'<canvas role="img" aria-label="{e(say)}"></canvas></div>'
                f'<figcaption><span class="still">{e(cap)}</span><span class="turn">{e(cap3d)}</span></figcaption></figure>')
    return f'<figure>{img(name, alt)}<figcaption>{e(cap)}</figcaption></figure>'


def panels():
    """Every project has the same layout: words on the left, facts on the right, pictures full width under them.
    A project whose picture is a tall film puts the film on the left, the way the Buoy section does."""
    out = []
    for k, name, label, group, years, blurb, facts, links, pic_name, alt in PROJECTS:
        film = FILMS.get(k)
        cls = "panel tallpic" if film else "panel"
        fl = "".join(f"<div><dt>{e(a)}</dt><dd>{e(b)}</dd></div>" for a, b in [("When", years)] + facts)
        ll = "".join(f'<a class="link" href="{e(u)}">{e(t)}</a>' for t, u in links)
        ll = f'<p class="links">{ll}</p>' if ll else ""
        pic = f'<figure class="pic">{img(pic_name, alt)}</figure>' if pic_name else ""
        if film:
            stem, w, h, say, cap = film
            pic = (f'<figure class="pic"><video class="lazy" controls muted loop playsinline preload="none" '
                   f'poster="media/{stem}.webp" width="{w}" height="{h}" aria-label="{e(say)}">'
                   f'<source src="media/{stem}.webm" type="video/webm"><source src="media/{stem}.mp4" type="video/mp4">'
                   f'</video><figcaption>{e(cap)}</figcaption></figure>')
        more = MORE.get(k, [])
        grid = ('<div class="more">' + "".join(more_figure(i, a, c) for i, a, c in more) + '</div>') if more else ""
        if k in EMBEDS:
            url, poster, title, button, cap = EMBEDS[k]
            pw, ph = webp_size(poster)
            grid += (f'<div class="more one"><figure class="embed" data-src="{e(url)}" data-title="{e(title)}">'
                     f'<div class="frame"><img src="img/{poster}.webp" width="{pw}" height="{ph}" loading="lazy" alt="">'
                     f'<button class="btn" type="button">{e(button)}</button></div>'
                     f'<figcaption>{e(cap)}</figcaption></figure></div>')
        out.append(
            f'      <article class="{cls}" id="p-{k}">\n'
            f'        <h3>{e(name)}</h3>\n'
            f'        <div class="blurb"><p class="lead">{e(blurb)}</p>{ll}</div>\n'
            f'        <dl class="pf kv">{fl}</dl>\n'
            f'        {pic}{grid}\n'
            f'      </article>')
    return "\n".join(out)


def inline_images(page):
    def repl(m):
        p = HERE / "img" / m.group(1)
        data = base64.b64encode(p.read_bytes()).decode()
        return f'src="data:image/webp;base64,{data}"'
    return re.sub(r'src="img/([\w.-]+\.webp)"', repl, page)


SITE = "https://jonathanbarnell.com/"
DESC = ("Senior software engineer in Topeka, Kansas. From a state public health lab to AI agent systems, "
        "a live budgeting app and a shelf of self-hosted projects.")
PERSON = {
    "@context": "https://schema.org", "@type": "Person", "name": "Jonathan Barnell", "url": SITE,
    "image": SITE + "img/headshot.webp", "jobTitle": "Senior software engineer",
    "worksFor": {"@type": "Organization", "name": "Alarm.com"},
    "address": {"@type": "PostalAddress", "addressLocality": "Topeka", "addressRegion": "KS", "addressCountry": "US"},
    "sameAs": ["https://www.linkedin.com/in/jonathanbarnell", "https://github.com/jbarnell1"],
}


def hosted(page):
    """The page as a full document for jonathanbarnell.com: real head, description, link preview."""
    head, body = page.split('<header class="bar">', 1)
    meta = "\n".join([
        f'<meta name="description" content="{e(DESC)}">',
        '<meta name="theme-color" content="#2436ff">',
        f'<link rel="canonical" href="{SITE}">',
        '<link rel="icon" href="icon.svg" type="image/svg+xml">',
        '<link rel="icon" href="favicon-32.png" sizes="32x32" type="image/png">',
        '<link rel="apple-touch-icon" href="apple-touch-icon.png">',
        '<link rel="preload" href="fonts/red-hat-display-900.woff2" as="font" type="font/woff2" crossorigin>',
        '<link rel="preload" href="fonts/red-hat-text.woff2" as="font" type="font/woff2" crossorigin>',
        '<meta property="og:type" content="website">',
        f'<meta property="og:url" content="{SITE}">',
        '<meta property="og:title" content="Jonathan Barnell">',
        f'<meta property="og:description" content="{e(DESC)}">',
        f'<meta property="og:image" content="{SITE}og.png">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta property="og:image:alt" content="Jonathan Barnell, senior software engineer in Topeka, Kansas">',
        '<meta name="twitter:card" content="summary_large_image">',
        '<script type="application/ld+json">' + json.dumps(PERSON, separators=(",", ":")) + '</script>',
    ]) + "\n"
    head = head.replace("<title>Jonathan Barnell Portfolio</title>", "<title>Jonathan Barnell</title>")
    head = head.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
    return (SKELETON + meta + head + '</head>\n<body>\n<header class="bar">' + body + "\n</body>\n</html>\n")


SKELETON = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n')

# GitHub Pages serves 404.html for any address that is not a file. Absolute paths, since it can be asked for at any depth.
NOT_FOUND = (SKELETON + '''<title>Not here. Jonathan Barnell</title>
<meta name="robots" content="noindex">
<link rel="icon" href="/icon.svg" type="image/svg+xml">
<style>
@font-face{font-family:"Red Hat Display";font-weight:900;font-display:swap;src:url(/fonts/red-hat-display-900.woff2) format("woff2")}
@font-face{font-family:"Red Hat Text";font-weight:400 500;font-display:swap;src:url(/fonts/red-hat-text.woff2) format("woff2")}
*{box-sizing:border-box}
body{margin:0;min-height:100svh;display:grid;align-content:end;gap:24px;padding:clamp(16px,3vw,44px);background:#2436ff;color:#fff;font-family:"Red Hat Text",system-ui,sans-serif;font-size:1.125rem;line-height:1.5}
h1{margin:0;font-family:"Red Hat Display","Arial Black",system-ui,sans-serif;font-weight:900;text-transform:uppercase;letter-spacing:-0.035em;line-height:0.84;font-size:clamp(3.25rem,15.2vw,15.5rem)}
h1 span{display:block}
h1 .l2{color:#0a0a0a}
p{margin:0;max-width:27rem}
a{display:inline-flex;align-items:center;min-height:48px;padding:0 22px;background:#0a0a0a;color:#fff;font-weight:500;text-decoration:none;justify-self:start}
a:focus-visible{outline:3px solid currentColor;outline-offset:3px}
</style>
</head>
<body>
<h1><span>Not</span><span class="l2">here</span></h1>
<p>There is no page at this address. Everything on this site is on one page.</p>
<a href="/">Go to the page</a>
</body>
</html>
''')


def main():
    t = (HERE / "template.html").read_text(encoding="utf-8")
    strings = (HERE / "data" / "strings.json").read_text(encoding="utf-8").strip()
    page = t.replace("{{SPINES}}", spines()).replace("{{PANELS}}", panels()).replace("{{STRINGS}}", strings)
    local = SKELETON + "</head>\n<body>\n" + page + "\n</body>\n</html>\n"
    (HERE / "index.html").write_text(local, encoding="utf-8")
    single = inline_images(page)
    (HERE / "portfolio.html").write_text(single, encoding="utf-8")
    # docs/ is what GitHub Pages serves at jonathanbarnell.com
    docs = HERE / "docs"
    (docs / "img").mkdir(parents=True, exist_ok=True)
    (docs / "index.html").write_text(hosted(page), encoding="utf-8", newline="\n")
    (docs / "404.html").write_text(NOT_FOUND, encoding="utf-8", newline="\n")
    (docs / "CNAME").write_text("jonathanbarnell.com\n", encoding="utf-8", newline="\n")
    (docs / ".nojekyll").write_text("", encoding="utf-8")
    (docs / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}sitemap.xml\n", encoding="utf-8", newline="\n")
    (docs / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'  <url><loc>{SITE}</loc></url>\n</urlset>\n', encoding="utf-8", newline="\n")
    used = sorted(set(re.findall(r'src="img/([\w.-]+\.webp)"', page)))
    for old in (docs / "img").glob("*.webp"):
        if old.name not in used:
            old.unlink()
    for name in used:
        shutil.copyfile(HERE / "img" / name, docs / "img" / name)
    # films and their posters
    (docs / "media").mkdir(exist_ok=True)
    clips = sorted(set(re.findall(r'"media/([\w.-]+\.(?:webm|mp4|webp|glb))"', page)))
    for old in (docs / "media").iterdir():
        if old.name not in clips:
            old.unlink()
    for name in clips:
        shutil.copyfile(HERE / "media" / name, docs / "media" / name)
    # fonts, three.js and the icons are served from the site itself, so nothing loads from a third party
    for folder in ("fonts", "vendor"):
        shutil.copytree(HERE / folder, docs / folder, dirs_exist_ok=True)
    for f in (HERE / "static").iterdir():
        shutil.copyfile(f, docs / f.name)
    print(f"index.html {len(local):,} bytes; portfolio.html {len(single):,} bytes; "
          f"docs/ with {len(used)} images; {len(PROJECTS)} projects")


if __name__ == "__main__":
    main()
