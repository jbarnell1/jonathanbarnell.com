"""Screenshots of single sections of index.html, by CSS selector.
Run in WSL: ~/.venvs/shots/bin/python /mnt/c/trifecta/site/shots_sections.py '#alarm' '#p-listener'
Writes PNGs to /mnt/c/trifecta/.taste-skill/inspect/ and prints basic measurements.
"""
import json, pathlib, re, sys
from playwright.sync_api import sync_playwright

OUT = pathlib.Path("/mnt/c/trifecta/.taste-skill/inspect"); OUT.mkdir(parents=True, exist_ok=True)
URL = "file:///mnt/c/trifecta/site/index.html"
SIZES = {"desktop": (1440, 900), "phone": (390, 844)}
sels = sys.argv[1:] or ["#alarm"]

MEASURE = """() => {
  const out = {overflow: document.documentElement.scrollWidth - window.innerWidth, height: document.documentElement.scrollHeight, heads: [], hidden: 0, wide: []};
  document.querySelectorAll('h1,h2,h3,.poster .w,.fig b').forEach(h => {
    if (!h.offsetParent) return;
    const cs = getComputedStyle(h), lh = parseFloat(cs.lineHeight), r = h.getBoundingClientRect();
    const spans = h.querySelectorAll(':scope > span, :scope > a > span');
    const lines = spans.length ? Array.from(spans).reduce((n, s) => n + Math.round(s.getBoundingClientRect().height / lh), 0) : Math.round(r.height / lh);
    out.heads.push([h.textContent.trim().slice(0, 28), lines]);
  });
  document.querySelectorAll('.rv').forEach(el => { if (el.offsetParent && getComputedStyle(el).opacity < 0.99) out.hidden++; });
  document.querySelectorAll('body *').forEach(el => { const r = el.getBoundingClientRect(); if (r.width && r.right > window.innerWidth + 1) out.wide.push(el.tagName + '.' + el.className + ' ' + Math.round(r.right)); });
  out.wide = out.wide.slice(0, 8);
  return out;
}"""

with sync_playwright() as pw:
    b = pw.chromium.launch()
    for name, (w, h) in SIZES.items():
        ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=1, is_mobile=(name == "phone"), has_touch=(name == "phone"))
        page = ctx.new_page()
        page.goto(URL, wait_until="networkidle")
        total = page.evaluate("document.documentElement.scrollHeight")
        y = 0
        while y < total:
            page.evaluate(f"window.scrollTo(0,{y})"); page.wait_for_timeout(200); y += int(h * 0.7)
        page.wait_for_timeout(900)
        print(name, json.dumps(page.evaluate(MEASURE)))
        page.evaluate("document.querySelector('.bar').style.display='none'")
        for s in sels:
            if s.startswith("#p-"):
                page.evaluate("s => document.querySelector('.spine[href=\"' + s + '\"]').click()", s); page.wait_for_timeout(500)
            el = page.locator(s).first
            el.scroll_into_view_if_needed(); page.wait_for_timeout(400)
            el.screenshot(path=str(OUT / f"sec-{name}-{re.sub(r'[^a-z0-9]+', '', s.lower())}.png"))
        ctx.close()
    b.close()
