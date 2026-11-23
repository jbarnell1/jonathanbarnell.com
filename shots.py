"""Full-page screenshots and basic measurements of index.html at three widths.
Run in WSL: ~/.venvs/shots/bin/python /mnt/c/trifecta/site/shots.py
Writes PNG slices to /mnt/c/trifecta/.taste-skill/inspect/.
"""
import json, pathlib, sys
from playwright.sync_api import sync_playwright

OUT = pathlib.Path("/mnt/c/trifecta/.taste-skill/inspect"); OUT.mkdir(parents=True, exist_ok=True)
URL = "file:///mnt/c/trifecta/site/index.html"
SIZES = {"desktop": (1440, 900), "tablet": (768, 1024), "phone": (390, 844)}
only = sys.argv[1:] or list(SIZES)

MEASURE = """() => {
  const out = {overflow: document.documentElement.scrollWidth - window.innerWidth,
               display: document.fonts.check('900 40px "Red Hat Display"'), text: document.fonts.check('400 16px "Red Hat Text"'),
               height: document.documentElement.scrollHeight, heads: [], hidden: 0, wide: []};
  document.querySelectorAll('h1,h2,h3,.poster .w,.fig b').forEach(h => {
    if (!h.offsetParent) return;
    const cs = getComputedStyle(h), lh = parseFloat(cs.lineHeight), r = h.getBoundingClientRect();
    const spans = h.querySelectorAll(':scope > span, :scope > a > span');
    const lines = spans.length ? Array.from(spans).reduce((n, s) => n + Math.round(s.getBoundingClientRect().height / lh), 0) : Math.round(r.height / lh);
    out.heads.push([h.textContent.trim().slice(0, 32), lines, Math.round(parseFloat(cs.fontSize)), Math.round(r.right)]);
  });
  document.querySelectorAll('.rv').forEach(el => { if (el.offsetParent && getComputedStyle(el).opacity < 0.99) out.hidden++; });
  document.querySelectorAll('body *').forEach(el => { const r = el.getBoundingClientRect(); if (r.width && r.right > window.innerWidth + 1) out.wide.push(el.tagName + '.' + el.className + ' ' + Math.round(r.right)); });
  out.wide = out.wide.slice(0, 8);
  return out;
}"""

with sync_playwright() as pw:
    b = pw.chromium.launch()
    for name in only:
        w, h = SIZES[name]
        ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=1, is_mobile=(name == "phone"), has_touch=(name == "phone"))
        page = ctx.new_page()
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(900)
        page.screenshot(path=str(OUT / f"{name}-first.png"))
        total = page.evaluate("document.documentElement.scrollHeight")
        y = 0
        while y < total:
            page.evaluate(f"window.scrollTo(0,{y})"); page.wait_for_timeout(220); y += int(h * 0.7)
        page.wait_for_timeout(900)
        m = page.evaluate(MEASURE)
        print(name, json.dumps(m))
        page.evaluate("document.querySelector('.bar').style.position='absolute'; window.scrollTo(0,0)")
        page.wait_for_timeout(300)
        page.screenshot(path=str(OUT / f"{name}-full.png"), full_page=True)
        ctx.close()
    b.close()
