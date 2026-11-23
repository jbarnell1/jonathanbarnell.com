"""Turns a String Art Studio plan into the small JSON the page draws from.

Usage (from the string-art-studio checkout, with its virtualenv):
  .venv/Scripts/python.exe C:/trifecta/site/data/make_strings.py <plan.json> <source photo>
Writes strings.json (pin positions in 0..1 and the pin sequence) and ../img/strings-source.webp.
"""
import json, pathlib, sys

from PIL import Image
from stringart.board import BoardConfig

HERE = pathlib.Path(__file__).parent
plan = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
board = BoardConfig.from_dict(plan["board"])
size = 10000
pins = [[round(float(x) / size, 4), round(float(y) / size, 4)] for x, y in board.pin_positions_px(size)]
out = {
    "pins": pins,
    "sequence": plan["sequence"],
    "thread_m": round(plan["thread"]["length_mm"] / 1000),
    "thread_mm": board.thread_width_mm,
    "board_mm": board.diameter_mm,
}
(HERE / "strings.json").write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")

im = Image.open(sys.argv[2]).convert("RGB")
side = min(im.size)
left, top = (im.width - side) // 2, (im.height - side) // 2
im.crop((left, top, left + side, top + side)).resize((336, 336), Image.LANCZOS).save(
    HERE.parent / "img" / "strings-source.webp", "WEBP", quality=82)
print(len(pins), "pins,", len(out["sequence"]), "turns,", out["thread_m"], "m of thread;",
      "pin 0 at", pins[0], "source", im.size)
