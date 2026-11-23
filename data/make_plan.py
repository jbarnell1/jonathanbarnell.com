"""Makes a String Art Studio plan the way the app does on its default "Soft" look.

The app's own command line predates that look, so this mirrors the web job instead: the face is
found and framed ("Frame the face"), levels are left alone with the brightest white at 0.8, faces
and edges are weighted, and the board and engine use their defaults.

Usage (from the string-art-studio checkout, with its virtualenv):
  PYTHONPATH=. .venv/Scripts/python.exe C:/trifecta/site/data/make_plan.py <photo> <out stem> [engine a|b]
Writes <out>.json (same shape as `string-art-studio generate`), <out>.png and <out>-target.jpg.
"""
import json, sys, time
from pathlib import Path

import numpy as np

from stringart.board import BoardConfig, thread_estimate
from stringart.engine.greedy import run_greedy
from stringart.engine.render import encode_png, render_rgb
from stringart.engine.setcover import run_setcover
from stringart.engine.state import EngineParams, RenderState
from stringart.faces import auto_importance, detect_faces, portrait_frame
from stringart.prep import PrepSettings, board_weight, load_source, prepare_target

photo, out = Path(sys.argv[1]), Path(sys.argv[2])
engine = sys.argv[3] if len(sys.argv) > 3 else "a"

rgb = load_source(photo.read_bytes())
h, w = rgb.shape[:2]
faces = detect_faces(rgb)
prep = PrepSettings(**portrait_frame(faces, w, h))          # every other setting is the Soft default
board = BoardConfig()
params = EngineParams(engine=engine)
res = board.work_res

gray = prepare_target(rgb, prep, board, res)
auto = auto_importance(faces, prep, w, h, res, prep.face_emphasis) if faces and prep.face_emphasis > 0 else None
weight = board_weight(board, res, None, prep.mask_strength, auto_importance=auto, gray=gray,
                      structure_weight=prep.structure_weight)
state = RenderState(gray, weight, board, light_protection=params.light_protection, objective=params.objective)

t0 = time.time()


def progress(ev):
    ev.pop("preview", None)
    sys.stderr.write(f"\r{ev.get('phase', '')}: {ev.get('lines', 0)} lines, {time.time() - t0:.0f}s   ")


result = run_greedy(state, params, progress) if engine == "a" else run_setcover(state, params, progress)
sys.stderr.write("\n")
est = thread_estimate(board, result.sequence)
out.with_suffix(".json").write_text(json.dumps({
    "board": board.to_dict(), "prep": prep.to_dict(), "sequence": result.sequence,
    "metrics": result.to_dict(), "thread": est.to_dict()}), encoding="utf-8")
out.with_suffix(".png").write_bytes(encode_png(render_rgb(board, result.sequence, 1000)))
from PIL import Image
Image.fromarray((np.clip(gray, 0, 1) * 255).astype(np.uint8)).save(str(out) + "-target.jpg", quality=88)
print(f"{photo.name} engine {engine}: faces {len(faces)}, crop {prep.crop_size}, {result.line_count} lines, "
      f"error {result.error:.4f}, thread {est.length_mm / 1000:.0f} m, {result.elapsed_s:.0f}s")
