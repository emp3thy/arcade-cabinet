"""Split cad/art/chunli.svg into non-overlapping per-colour SVG layers for
Bambu Studio (one modifier per filament).

Why: a Bambu SVG import is one shape, and two modifiers that overlap fight
for the same volume. The poster paints later shapes over earlier ones, so
every layer here has every layer above it (in paint order) subtracted from
it. The frame that keeps all files at one extent is dashed: each layer owns
its own segments of the border, so the frames do not overlap either.

Outputs (same 2160 x 2592 viewBox as the source, so imports align):
  layers/set4/  red, blue, cream, brown           (one AMS)
  layers/set6/  + gold, dark                      (two AMS)
  layers/all/   one file per original class       (reference)
Each folder gets _preview.png. Run: python cad/art/split_layers.py
"""
import io
import os
import re
import sys

import cairosvg
from PIL import Image
from shapely.geometry import MultiPolygon, Polygon, box
from shapely.ops import polygonize, unary_union
from svgelements import SVG, Shape, Path, Move, Close, Line

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "chunli.svg")
OUT = os.path.join(HERE, "layers")
ART_H_MM = 64.0            # printed art height; sets the unit scale below
SAMPLE_UNITS = 1.0         # curve sampling step, viewBox units (0.03 mm)
MIN_PIECE_MM2 = 0.02       # drop slivers smaller than this
FRAME_MARGIN_MM = 1.5
FRAME_WIDTH_MM = 0.6

SETS = {
    "set4": [("1_red_D5392B", "#D5392B", ["st0", "st9"]),
             ("2_blue_4886C5", "#4886C5", ["st3"]),
             ("3_cream_F6F0E7", "#F6F0E7", ["st4", "st5", "st7", "st1", "st8"]),
             ("4_brown_694B30", "#694B30", ["st2", "st10", "st6"])],
    "set6": [("1_red_D5392B", "#D5392B", ["st0", "st9"]),
             ("2_blue_4886C5", "#4886C5", ["st3"]),
             ("3_cream_F6F0E7", "#F6F0E7", ["st4", "st5", "st7"]),
             ("4_gold_F4CF8E", "#F4CF8E", ["st1", "st8"]),
             ("5_brown_997256", "#997256", ["st2", "st10"]),
             ("6_dark_333735", "#333735", ["st6"])],
}


def sample_subpath(sub):
    pts = []
    for seg in sub:
        if isinstance(seg, (Move, Close)):
            continue
        if isinstance(seg, Line):
            pts.append((seg.start.x, seg.start.y))
            continue
        n = max(4, int(seg.length() / SAMPLE_UNITS))
        for i in range(n):
            p = seg.point(i / n)
            pts.append((p.x, p.y))
    # close the ring with the last drawn segment's end point (a trailing
    # Close carries no geometry; skipping it lost every polygon's last vertex)
    for seg in reversed(list(sub)):
        if not isinstance(seg, (Move, Close)):
            pts.append((seg.end.x, seg.end.y))
            break
    return pts


def shape_to_geom(shape):
    """Nonzero-winding fill of a path: polygonize every subpath ring, then
    keep each face whose winding number (sum of signed containments over
    the subpaths) is not zero. Even-odd was wrong here: letters drawn as
    overlapping subpaths cancelled (measured on the I of CHUN-LI)."""
    path = Path(shape)
    path.reify()
    rings = []
    for sub in path.as_subpaths():
        pts = sample_subpath(sub)
        if len(pts) < 3:
            continue
        poly = Polygon(pts)
        if poly.area < 1e-6:
            continue
        rings.append((poly, 1 if poly.exterior.is_ccw else -1))
    if not rings:
        return None
    if len(rings) == 1:
        g = rings[0][0]
        return g if g.is_valid else g.buffer(0)
    boundaries = unary_union([r.exterior for r, _ in rings])
    faces = []
    for face in polygonize(boundaries):
        pt = face.representative_point()
        winding = 0
        for poly, sign in rings:
            if poly.contains(pt):
                winding += sign
        if winding != 0:
            faces.append(face)
    if not faces:
        return None
    g = unary_union(faces)
    return g if g.is_valid else g.buffer(0)


def load_classes():
    svg = SVG.parse(SRC, reify=True)
    src = open(SRC, encoding="utf-8").read()
    colours = dict(re.findall(r"\.(st\d+)\{fill:(#[0-9A-Fa-f]{6});\}", src))
    order = []          # document order of (class, geom)
    for e in svg.elements():
        if not isinstance(e, Shape):
            continue
        cls = e.values.get("class")
        if cls is None:
            continue
        g = shape_to_geom(e)
        if g is None or g.is_empty:
            continue
        order.append((cls, g))
    vb = svg.viewbox
    return colours, order, (vb.x, vb.y, vb.width, vb.height)


def paint(order, groups):
    """groups: list of (name, fill, [classes]) in import order. Returns
    per-group geometry with everything painted later subtracted."""
    per_group = []
    for name, fill, classes in groups:
        g = unary_union([g for cls, g in order if cls in classes])
        per_group.append([name, fill, g])
    for i in range(len(per_group)):
        above = [per_group[j][2] for j in range(i + 1, len(per_group))]
        if above:
            per_group[i][2] = per_group[i][2].difference(unary_union(above))
    return per_group


def clean(geom, units_per_mm):
    min_area = MIN_PIECE_MM2 * units_per_mm ** 2
    polys = []
    if geom.geom_type == "Polygon":
        geom = MultiPolygon([geom])
    if geom.geom_type == "MultiPolygon":
        for p in geom.geoms:
            if p.area >= min_area:
                polys.append(p)
    elif geom.geom_type == "GeometryCollection":
        for g in geom.geoms:
            polys += clean(g, units_per_mm)
    return polys


def ring_d(ring):
    pts = list(ring.coords)
    return "M" + " ".join("%.2f,%.2f" % (x, y) for x, y in pts[:-1]) + "Z"


def poly_d(p):
    return ring_d(p.exterior) + "".join(ring_d(r) for r in p.interiors)


def frame_segments(bounds, units_per_mm, n):
    """Dashed frame: n segments per side, segment k for layer k. Top and
    bottom span the full outer width; left and right sit between them."""
    x0, y0, x1, y1 = bounds
    m, w = FRAME_MARGIN_MM * units_per_mm, FRAME_WIDTH_MM * units_per_mm
    ox0, oy0, ox1, oy1 = x0 - m - w, y0 - m - w, x1 + m + w, y1 + m + w
    ix0, iy0, ix1, iy1 = x0 - m, y0 - m, x1 + m, y1 + m
    per_layer = [[] for _ in range(n)]
    for k in range(n):
        xa, xb = ox0 + (ox1 - ox0) * k / n, ox0 + (ox1 - ox0) * (k + 1) / n
        per_layer[k].append(box(xa, oy0, xb, iy0))                       # top
        per_layer[(k + n // 2) % n].append(box(xa, iy1, xb, oy1))        # bottom, offset colours
        ya, yb = iy0 + (iy1 - iy0) * k / n, iy0 + (iy1 - iy0) * (k + 1) / n
        per_layer[(k + 1) % n].append(box(ox0, ya, ix0, yb))             # left
        per_layer[(k + 3) % n].append(box(ix1, ya, ox1, yb))             # right
    return [unary_union(b) for b in per_layer], (ox0, oy0, ox1, oy1)


def write_svg(path, vb, fill, polys, cls):
    d = "".join(poly_d(p) for p in polys)
    svg = ('<?xml version="1.0" encoding="utf-8"?>\n'
           '<svg version="1.1" xmlns="http://www.w3.org/2000/svg" x="0px" y="0px" viewBox="%g %g %g %g">\n'
           '<style type="text/css">.%s{fill:%s;}</style>\n'
           '<path class="%s" fill-rule="evenodd" d="%s"/>\n</svg>\n' % (vb[0], vb[1], vb[2], vb[3], cls, fill, cls, d))
    open(path, "w", encoding="utf-8").write(svg)


def preview(folder, files, vb):
    base = Image.new("RGBA", (540, 648), (245, 245, 245, 255))
    for f in files:
        png = cairosvg.svg2png(url=os.path.join(folder, f), output_height=648)
        base.alpha_composite(Image.open(io.BytesIO(png)).convert("RGBA"))
    base.save(os.path.join(folder, "_preview.png"))


def emit(folder, groups, order, vb, units_per_mm, art_bounds):
    os.makedirs(folder, exist_ok=True)
    painted = paint(order, groups)
    frames, outer = frame_segments(art_bounds, units_per_mm, len(groups))
    results = []
    for (name, fill, geom), frame in zip(painted, frames):
        polys = clean(unary_union([geom, frame]), units_per_mm)
        cls = "c_" + name.split("_")[1]
        write_svg(os.path.join(folder, name + ".svg"), vb, fill, polys, cls)
        results.append((name, unary_union(polys)))
    # verification: pairwise overlap and identical extents
    worst = 0.0
    for i in range(len(results)):
        for j in range(i + 1, len(results)):
            worst = max(worst, results[i][1].intersection(results[j][1]).area)
    extents = {tuple(round(b, 1) for b in g.bounds) for _, g in results}
    print("%s: %d layers, worst pairwise overlap %.4f mm2, distinct extents %d, outer %.1f x %.1f mm"
          % (os.path.basename(folder), len(results), worst / units_per_mm ** 2, len(extents),
             (outer[2] - outer[0]) / units_per_mm, (outer[3] - outer[1]) / units_per_mm))
    for name, g in results:
        print("   %-18s %8.1f mm2" % (name, g.area / units_per_mm ** 2))
    preview(folder, [n + ".svg" for n, _, _ in groups], vb)
    return worst


def main():
    colours, order, vb = load_classes()
    art = unary_union([g for _, g in order])
    art_bounds = art.bounds
    units_per_mm = (art_bounds[3] - art_bounds[1]) / ART_H_MM
    print("parsed %d shapes, art %.0f x %.0f units, %.2f units/mm" % (
        len(order), art_bounds[2] - art_bounds[0], art_bounds[3] - art_bounds[1], units_per_mm))
    worst = 0.0
    for name, groups in SETS.items():
        worst = max(worst, emit(os.path.join(OUT, name), groups, order, vb, units_per_mm, art_bounds))
    all_groups = [("%s_%s" % (cls, colours[cls][1:]), colours[cls], [cls]) for cls in colours]
    worst = max(worst, emit(os.path.join(OUT, "all"), all_groups, order, vb, units_per_mm, art_bounds))
    if worst / units_per_mm ** 2 > 0.001:
        print("OVERLAP REMAINS", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
