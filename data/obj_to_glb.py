"""Converts an EasyEDA 3D export (OBJ + MTL, colours only) into a small GLB for the page.

Usage: python data/obj_to_glb.py <model.obj> <out.glb>
Keeps positions, triangle indices and one flat colour per material. Normals are dropped: the page
shades the board flat. The model is centred and turned from Z-up to Y-up.
"""
import json, pathlib, struct, sys
from array import array

src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])

# materials: name -> (r, g, b, alpha), sRGB as written by EasyEDA
mats, cur = {}, None
for line in src.with_suffix(".mtl").read_text(encoding="utf-8", errors="replace").splitlines():
    p = line.split()
    if not p:
        continue
    if p[0] == "newmtl":
        cur = p[1]; mats[cur] = [0.8, 0.8, 0.8, 1.0]
    elif p[0] == "Kd" and cur:
        mats[cur][:3] = [float(x) for x in p[1:4]]
    elif p[0] == "d" and cur:
        mats[cur][3] = float(p[1])

verts, groups, mat = [], {}, None          # groups: material -> list of global vertex indices (triangles)
for line in src.read_text(encoding="utf-8", errors="replace").splitlines():
    if line.startswith("v "):
        _, x, y, z = line.split()[:4]
        verts.append((float(x), float(y), float(z)))
    elif line.startswith("usemtl "):
        mat = line.split()[1]
    elif line.startswith("f "):
        idx = [int(tok.split("/")[0]) for tok in line.split()[1:]]
        idx = [i - 1 if i > 0 else len(verts) + i for i in idx]
        tri = groups.setdefault(mat, [])
        for k in range(1, len(idx) - 1):          # fan triangulation
            tri += [idx[0], idx[k], idx[k + 1]]

lo = [min(v[i] for v in verts) for i in range(3)]
hi = [max(v[i] for v in verts) for i in range(3)]
mid = [(lo[i] + hi[i]) / 2 for i in range(3)]


def place(v):                                # centre, then Z-up -> Y-up
    x, y, z = (v[i] - mid[i] for i in range(3))
    return (x, z, -y)


def linear(c):                               # sRGB -> linear, as glTF expects
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


binary, views, accessors, materials, prims = bytearray(), [], [], [], []


def add_view(data, target):
    while len(binary) % 4:
        binary.append(0)
    views.append({"buffer": 0, "byteOffset": len(binary), "byteLength": len(data), "target": target})
    binary.extend(data)
    return len(views) - 1


for name, tri in groups.items():
    local, pos = {}, array("f")
    ind = []
    for g in tri:
        if g not in local:
            local[g] = len(local); pos.extend(place(verts[g]))
        ind.append(local[g])
    n = len(local)
    pts = [pos[i:i + 3] for i in range(0, len(pos), 3)]
    accessors.append({"bufferView": add_view(pos.tobytes(), 34962), "componentType": 5126, "count": n, "type": "VEC3",
                      "min": [min(p[i] for p in pts) for i in range(3)], "max": [max(p[i] for p in pts) for i in range(3)]})
    small = n < 65536
    accessors.append({"bufferView": add_view(array("H" if small else "I", ind).tobytes(), 34963),
                      "componentType": 5123 if small else 5125, "count": len(ind), "type": "SCALAR"})
    r, g, b, a = mats.get(name, [0.8, 0.8, 0.8, 1.0])
    m = {"name": name, "doubleSided": True,
         "pbrMetallicRoughness": {"baseColorFactor": [round(linear(r), 4), round(linear(g), 4), round(linear(b), 4), a],
                                  "metallicFactor": 0.0, "roughnessFactor": 0.65}}
    if a < 1:
        m["alphaMode"] = "BLEND"
    materials.append(m)
    prims.append({"attributes": {"POSITION": len(accessors) - 2}, "indices": len(accessors) - 1, "material": len(materials) - 1})

while len(binary) % 4:
    binary.append(0)
doc = {"asset": {"version": "2.0", "generator": "obj_to_glb.py"}, "scene": 0, "scenes": [{"nodes": [0]}],
       "nodes": [{"mesh": 0, "name": "board"}], "meshes": [{"primitives": prims}], "materials": materials,
       "accessors": accessors, "bufferViews": views, "buffers": [{"byteLength": len(binary)}]}
text = json.dumps(doc, separators=(",", ":")).encode("utf-8")
text += b" " * (-len(text) % 4)
total = 12 + 8 + len(text) + 8 + len(binary)
dst.write_bytes(struct.pack("<4sII", b"glTF", 2, total) + struct.pack("<I4s", len(text), b"JSON") + text
                + struct.pack("<I4s", len(binary), b"BIN\x00") + bytes(binary))
size = [round(hi[i] - lo[i], 1) for i in range(3)]
print(f"{len(verts):,} vertices, {sum(len(t) for t in groups.values()) // 3:,} triangles, {len(prims)} materials, "
      f"size {size} mm -> {dst.name} {total:,} bytes")
