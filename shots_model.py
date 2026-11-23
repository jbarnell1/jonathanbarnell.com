"""Checks the 3D board in the Listener panel over a local server (fetch does not work from file://).
Run in WSL after build.py: ~/.venvs/shots/bin/python /mnt/c/trifecta/site/shots_model.py
Writes model-*.png to /mnt/c/trifecta/.taste-skill/inspect/.
"""
import json, subprocess, sys, time
from playwright.sync_api import sync_playwright

OUT = "/mnt/c/trifecta/.taste-skill/inspect/"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8766", "--directory", "/mnt/c/trifecta/site/docs"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
try:
    with sync_playwright() as pw:
        b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        for name, w, h, reduced in (("desktop", 1440, 900, False), ("phone", 390, 844, False), ("reduced", 1440, 900, True)):
            ctx = b.new_context(viewport={"width": w, "height": h}, is_mobile=(name == "phone"), has_touch=(name == "phone"),
                                reduced_motion="reduce" if reduced else "no-preference")
            page = ctx.new_page()
            errs, bad = [], []
            page.on("pageerror", lambda e: errs.append(str(e)))
            page.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            page.on("response", lambda r: bad.append((r.status, r.url)) if r.status >= 400 else None)
            page.goto("http://localhost:8766/", wait_until="networkidle")
            page.evaluate("document.querySelector('.model').scrollIntoView({behavior: 'instant', block: 'center'})")
            page.wait_for_timeout(6000)
            ready = page.evaluate("document.querySelector('.model').classList.contains('ready')")
            page.locator(".model").screenshot(path=OUT + f"model-{name}.png")
            if name == "desktop":
                box = page.locator(".model canvas").bounding_box()
                page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                page.mouse.down(); page.mouse.move(box["x"] + box["width"] / 2 + 160, box["y"] + box["height"] / 2, steps=6); page.mouse.up()
                page.wait_for_timeout(400)
                page.locator(".model").screenshot(path=OUT + "model-desktop-dragged.png")
            print(name, json.dumps({"ready": ready, "errors": errs[:4], "failed": bad[:4],
                                    "overflow": page.evaluate("document.documentElement.scrollWidth - innerWidth")}))
            ctx.close()
        b.close()
finally:
    srv.terminate()
