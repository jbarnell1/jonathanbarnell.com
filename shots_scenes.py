"""Frames of the scroll scenes, the string art canvas and the films, at desktop, phone and reduced motion.
Run in WSL after build.py: ~/.venvs/shots/bin/python /mnt/c/trifecta/site/shots_scenes.py
Writes PNGs named scene-*.png to /mnt/c/trifecta/.taste-skill/inspect/ and prints measurements.
"""
import json, pathlib
from playwright.sync_api import sync_playwright

OUT = pathlib.Path("/mnt/c/trifecta/.taste-skill/inspect"); OUT.mkdir(parents=True, exist_ok=True)
URL = "file:///mnt/c/trifecta/site/docs/index.html"

STATE = """() => ({
  overflow: document.documentElement.scrollWidth - innerWidth,
  height: document.documentElement.scrollHeight,
  scenes: Array.from(document.querySelectorAll('.scene')).map(s => [s.dataset.scene, s.classList.contains('live'), Math.round(s.getBoundingClientRect().height)]),
  films: Array.from(document.querySelectorAll('video')).map(v => [v.currentSrc.split('/').pop(), v.readyState, v.paused, v.controls, !!v.closest('[hidden]')]),
  turns: document.getElementById('st-n').textContent,
  errors: window.__errs || []
})"""


def at(page, sel, p):
    """Scroll so the scene is p of the way through its hold."""
    page.evaluate("""([sel, p]) => { const s = document.querySelector(sel), r = s.getBoundingClientRect();
        scrollTo({top: scrollY + r.top + (r.height - innerHeight) * p, behavior: "instant"}); }""", [sel, p])
    page.wait_for_timeout(900)


with sync_playwright() as pw:
    b = pw.chromium.launch()
    for name, w, h, reduced in (("desktop", 1440, 900, False), ("phone", 390, 844, False), ("reduced", 1440, 900, True)):
        ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=1,
                            is_mobile=(name == "phone"), has_touch=(name == "phone"),
                            reduced_motion="reduce" if reduced else "no-preference")
        page = ctx.new_page()
        page.add_init_script("window.__errs=[]; addEventListener('error', e => window.__errs.push(String(e.message)))")
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(800)
        if name == "desktop":
            for p in (0.0, 0.3, 0.62, 1.0):
                at(page, ".film", p); page.screenshot(path=str(OUT / f"scene-film-{int(p * 100):03d}.png"))
            for p in (0.02, 0.45, 0.97):
                at(page, ".steps", p); page.screenshot(path=str(OUT / f"scene-steps-{int(p * 100):03d}.png"))
        else:
            for sel in (".steps", ".film"):
                at(page, sel, 0.3 if name == "phone" else 0.0)
                page.screenshot(path=str(OUT / f"scene-{name}-{sel[1:]}.png"))
        page.evaluate("document.querySelector('#strings').scrollIntoView({behavior: 'instant'})"); page.wait_for_timeout(5000)
        page.screenshot(path=str(OUT / f"scene-{name}-strings.png"))
        page.evaluate("document.querySelector('.buoy .rest').scrollIntoView({behavior: 'instant'})"); page.wait_for_timeout(1500)
        page.screenshot(path=str(OUT / f"scene-{name}-buoyrest.png"))
        page.evaluate("document.querySelector('#house').scrollIntoView({behavior: 'instant'})"); page.wait_for_timeout(900)
        page.screenshot(path=str(OUT / f"scene-{name}-house.png"))
        for key in ("scripture", "goingdown"):
            page.evaluate("k => document.querySelector('.spine[href=\"#p-' + k + '\"]').click()", key)
            page.wait_for_timeout(1200)
            page.locator(f"#p-{key}").screenshot(path=str(OUT / f"scene-{name}-{key}.png"))
        print(name, json.dumps(page.evaluate(STATE)))
        ctx.close()
    b.close()
