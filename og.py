"""Link preview image (1200 x 630) taken from the hero of the hosted page.
Run in WSL after build.py: ~/.venvs/shots/bin/python /mnt/c/trifecta/site/og.py
Also saves a phone and a desktop first screen of docs/index.html next to the other screenshots.
"""
import pathlib
from playwright.sync_api import sync_playwright

URL = "file:///mnt/c/trifecta/site/docs/index.html"
OUT = pathlib.Path("/mnt/c/trifecta/.taste-skill/inspect"); OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as pw:
    b = pw.chromium.launch()
    page = b.new_page(viewport={"width": 1200, "height": 630})
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(1800)
    page.evaluate("document.querySelector('.bar nav').style.visibility='hidden'")
    page.screenshot(path="/mnt/c/trifecta/site/docs/og.png")
    for name, w, h in (("docs-desktop", 1440, 900), ("docs-phone", 390, 844)):
        p = b.new_page(viewport={"width": w, "height": h})
        p.goto(URL, wait_until="networkidle"); p.wait_for_timeout(1800)
        p.screenshot(path=str(OUT / f"{name}.png"))
    b.close()
