"""Pictures made from the page itself. Run in WSL after build.py:
  ~/.venvs/shots/bin/python /mnt/c/trifecta/site/assets.py

  img/strings-final.webp        the finished string art plan, shown when there is no script
  static/favicon-32.png         PNG copies of static/icon.svg for browsers that want one
  static/apple-touch-icon.png
"""
import base64, pathlib
from playwright.sync_api import sync_playwright

SITE = pathlib.Path("/mnt/c/trifecta/site")
URL = "file://" + str(SITE / "docs" / "index.html")

with sync_playwright() as pw:
    b = pw.chromium.launch()
    page = b.new_page(viewport={"width": 1200, "height": 900})
    page.goto(URL, wait_until="load")
    data = page.evaluate("""() => {
      const seek = document.getElementById('st-seek');
      seek.value = seek.max; seek.dispatchEvent(new Event('input'));
      const c = document.createElement('canvas'); c.width = c.height = 900;
      c.getContext('2d').drawImage(document.getElementById('st-canvas'), 0, 0, 900, 900);
      return c.toDataURL('image/webp', 0.72);
    }""")
    (SITE / "img" / "strings-final.webp").write_bytes(base64.b64decode(data.split(",", 1)[1]))
    svg = (SITE / "static" / "icon.svg").read_text()
    for name, size in (("favicon-32.png", 32), ("apple-touch-icon.png", 180)):
        p = b.new_page(viewport={"width": size, "height": size})
        p.set_content(f"<style>*{{margin:0}}svg{{display:block;width:{size}px;height:{size}px}}</style>{svg}")
        p.screenshot(path=str(SITE / "static" / name))
    b.close()
print("wrote strings-final.webp, favicon-32.png, apple-touch-icon.png")
