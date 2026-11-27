"""Checks the built site in Chromium. Serve docs/ first, then run in WSL:
  cd /mnt/c/trifecta/site/docs && python3 -m http.server 8766 &
  ~/.venvs/shots/bin/python /mnt/c/trifecta/site/check.py [shots]

Reports: sideways overflow at eight widths, headlines over two lines, console errors, failed and
third-party requests, where a link into the page lands, project links, and what the page does with
script turned off. With the word "shots" it also saves one screenshot per section at three widths.
"""
import pathlib, sys
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8766/"
OUT = pathlib.Path("/mnt/c/trifecta/.taste-skill/inspect/check"); OUT.mkdir(parents=True, exist_ok=True)
SECTIONS = ["top", "story", "order", "alarm", "buoy", "pipeline", "house", "strings", "work", "record", "contact"]
ARGS = ["--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]
bad = []


def note(ok, text):
    print(("ok   " if ok else "FAIL ") + text)
    if not ok:
        bad.append(text)


def settle(page, y=None, wait=500):
    if y is not None:
        page.evaluate("y => window.scrollTo({top: y, behavior: 'instant'})", y)
    page.wait_for_timeout(wait)


def walk(page):
    """Scroll the whole page in steps so every entrance has fired and lazy pictures have loaded."""
    h = page.evaluate("document.documentElement.scrollHeight")
    y = 0
    while y < h:
        settle(page, y, 120)
        y += 500
        h = page.evaluate("document.documentElement.scrollHeight")
    settle(page, 0, 300)


with sync_playwright() as pw:
    b = pw.chromium.launch(args=ARGS)

    # 1. sideways overflow and long headlines
    for w in (390, 640, 768, 820, 900, 1024, 1280, 1440):
        page = b.new_page(viewport={"width": w, "height": 900})
        page.goto(BASE, wait_until="networkidle"); walk(page)
        over = page.evaluate("""() => {
          const vw = document.documentElement.clientWidth, out = [];
          for (const el of document.querySelectorAll('body *')) {
            if (el.closest('[hidden]') || el.closest('.sr') || el.classList.contains('skip')) continue;
            const r = el.getBoundingClientRect();
            if (r.width && r.right > vw + 1 && getComputedStyle(el).position !== 'fixed') out.push(el.tagName + '.' + el.className + ' ' + Math.round(r.right));
          }
          return {scroll: document.documentElement.scrollWidth - vw, els: out.slice(0, 4)};
        }""")
        note(over["scroll"] <= 0, f"{w}px: no sideways scroll {over if over['scroll'] > 0 else ''}")
        lines = page.evaluate("""() => {
          const out = [];
          for (const el of document.querySelectorAll('h1 span, h2:not(.h), h2.h span, .foot h2 span, .panel:not([hidden]) h3, .steps .list b, .poster .w')) {
            const cs = getComputedStyle(el), lh = parseFloat(cs.lineHeight), n = Math.round(el.getBoundingClientRect().height / lh);
            const max = el.matches('span, .poster .w') ? 1 : 2;
            if (n > max) out.push(el.textContent.trim().slice(0, 30) + ' = ' + n + ' lines');
          }
          return out;
        }""")
        note(not lines, f"{w}px: headlines within their lines {lines}")
        page.close()

    # 2. errors and requests on a full scroll
    for w, h in ((390, 844), (1440, 900)):
        page = b.new_page(viewport={"width": w, "height": h})
        errors, failed, reqs = [], [], []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("requestfailed", lambda r: failed.append(r.url))
        page.on("request", lambda r: reqs.append(r.url))
        page.goto(BASE, wait_until="networkidle")
        first = len(reqs)
        walk(page); page.wait_for_timeout(1500)
        third = sorted({u.split('/')[2] for u in reqs if not u.startswith(BASE) and not u.startswith('data:')})
        note(not errors, f"{w}px: no console errors {errors[:3]}")
        note(not failed, f"{w}px: no failed requests {failed[:3]}")
        note(not third, f"{w}px: no third-party requests {third}")
        print(f"     {w}px: {first} requests before scrolling, {len(reqs)} after")
        page.close()

    # 3. links into the page land on their target
    for w, h in ((390, 844), (1440, 900)):
        for target in ("work", "record", "contact", "p-goingdown", "p-scripture"):
            page = b.new_page(viewport={"width": w, "height": h})
            page.goto(BASE + "#" + target, wait_until="load"); page.wait_for_timeout(1800)
            got = page.evaluate("""id => { const t = document.getElementById(id), r = t.getBoundingClientRect();
              const atEnd = window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 2;
              return {top: Math.round(r.top), hidden: !!t.closest('[hidden]'), atEnd}; }""", target)
            ok = not got["hidden"] and (abs(got["top"] - 52) <= 24 or got["atEnd"])
            note(ok, f"{w}px: #{target} lands at {got['top']}px from the top{' (page end)' if got['atEnd'] else ''}")
            page.close()

    # 4. picking a project: address in the bar, panel on screen on a phone, model not drawn off screen
    page = b.new_page(viewport={"width": 390, "height": 844})
    page.goto(BASE, wait_until="networkidle"); walk(page)
    page.evaluate("document.querySelector('#shelf').scrollIntoView({behavior:'instant', block:'center'})"); page.wait_for_timeout(600)
    page.click('a.spine[href="#p-highlights"]'); page.wait_for_timeout(900)
    got = page.evaluate("""() => { const p = document.getElementById('p-highlights'); return {hash: location.hash, hidden: p.hidden,
      top: Math.round(p.getBoundingClientRect().top), say: document.getElementById('shelf-say').textContent}; }""")
    note(got["hash"] == "#p-highlights" and not got["hidden"] and got["top"] < 844 * 0.55, f"phone: tapping a spine opens it in view {got}")
    page.close()

    page = b.new_page(viewport={"width": 1440, "height": 900})
    page.goto(BASE, wait_until="networkidle"); walk(page)
    page.evaluate("document.querySelector('.model').scrollIntoView({behavior:'instant', block:'center'})"); page.wait_for_timeout(2500)
    ready = page.evaluate("document.querySelector('.model').classList.contains('ready')")
    note(ready, "desktop: the 3D board loads from the site's own copy of three.js")
    count = page.evaluate("""async () => {
      const gl = document.querySelector('.model canvas').getContext('webgl2') || document.querySelector('.model canvas').getContext('webgl');
      let n = 0; const orig = gl.drawElements.bind(gl); gl.drawElements = (...a) => { n++; return orig(...a); };
      window.scrollTo({top: 0, behavior: 'instant'}); await new Promise(r => setTimeout(r, 400)); n = 0;
      for (let y = 0; y < 5000; y += 100) { window.scrollTo({top: y, behavior: 'instant'}); await new Promise(r => requestAnimationFrame(r)); }
      return n; }""")
    note(count == 0, f"desktop: the board is not drawn while off screen ({count} draw calls)")
    page.close()

    # 5. without script
    ctx = b.new_context(java_script_enabled=False, viewport={"width": 1440, "height": 900})
    page = ctx.new_page(); page.goto(BASE, wait_until="load")
    got = page.evaluate if False else None
    vids = page.locator("video[controls]").count()
    pic = page.locator("noscript").count()
    shown = page.locator(".panel").count()
    page.locator("#strings").scroll_into_view_if_needed(); page.wait_for_timeout(400)
    page.screenshot(path=str(OUT / "nojs-strings.png"))
    note(vids == 3, f"no script: {vids} films have native controls")
    note(pic == 1, "no script: the string art has a still picture")
    print(f"     no script: {shown} project panels in the page")
    ctx.close()

    # 6. screenshots, one per section
    if "shots" in sys.argv:
        for tag, w, h in (("p", 390, 844), ("t", 820, 1180), ("d", 1440, 900)):
            page = b.new_page(viewport={"width": w, "height": h})
            page.goto(BASE, wait_until="networkidle"); walk(page)
            for name in SECTIONS:
                page.evaluate("id => document.getElementById(id).scrollIntoView({behavior:'instant', block:'start'})", name)
                page.wait_for_timeout(800)
                page.screenshot(path=str(OUT / f"{tag}-{name}.png"))
            # the film part way open, and three panels
            top = page.evaluate("document.querySelector('.scene.film').getBoundingClientRect().top + window.scrollY")
            for pct in (0, 50):
                settle(page, top + h * 1.5 * pct / 100, 700)
                page.screenshot(path=str(OUT / f"{tag}-film-{pct}.png"))
            for key in ("buoy", "scripture", "goingdown", "listener"):
                page.evaluate("document.querySelector('#shelf').scrollIntoView({behavior:'instant', block:'start'})")
                page.click(f'a.spine[href="#p-{key}"]'); page.wait_for_timeout(900)
                page.evaluate("id => document.getElementById(id).scrollIntoView({behavior:'instant', block:'start'})", "p-" + key)
                page.wait_for_timeout(1200 if key == "listener" else 500)
                page.screenshot(path=str(OUT / f"{tag}-panel-{key}.png"))
            page.close()
    b.close()

print("\n%d problem(s)" % len(bad))
for x in bad:
    print(" -", x)
