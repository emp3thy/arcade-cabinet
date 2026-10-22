"""Art preparation for the console drum's wrapped debosses (D-021).

Three commands, all run with
    uv run --no-project --python 3.12 --with shapely --with svgelements --with ezdxf --with pillow python cad/art/drum_art.py ...

  silhouette <svg> [<svg> ...] <out.dxf> --height H
      Union of every closed path in the SVG files, outer boundaries only
      (holes dropped), scaled so the bounding box is H mm tall, centred on
      (0, 0), y up. Writes closed LWPOLYLINEs plus a PNG preview beside it.
  art <in.dxf> <out.dxf>
      Re-centre a DXF's bounding box on (0, 0); no scale, no mirror. Turns
      the pad's placement-baked logo DXFs into art-space files.
  place <in.dxf> <out.dxf> --cx CX --cy CY [--flip-y]
      Optional mirror about the x axis, then translate the bounding-box
      centre to (CX, CY): the placement for one sketch plane of the drum,
      chosen after the stage D mapping probe.

Every command prints `bbox: xmin xmax ymin ymax` as its last line.

The SVG fill rule (nonzero winding over sampled subpaths) is the one
cad/art/split_layers.py measured against the Chun-Li art; it is repeated
here rather than imported because that module imports cairosvg, which has
no cairo on this machine.
"""
import argparse
import os
import sys

import ezdxf
from PIL import Image, ImageDraw
from shapely.affinity import scale, translate
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import polygonize, unary_union
from svgelements import SVG, Shape, Path, Move, Close, Line

SAMPLE_UNITS = 1.0      # curve sampling step in SVG user units
SIMPLIFY_MM = 0.03      # vertex thinning after scaling to mm
PREVIEW_PX_PER_MM = 4


# ---------------------------------------------------------------- SVG -> geometry

def _sample_subpath(sub):
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
    for seg in reversed(list(sub)):
        if not isinstance(seg, (Move, Close)):
            pts.append((seg.end.x, seg.end.y))
            break
    return pts


def _shape_to_geom(shape):
    """Nonzero-winding fill of one SVG shape, as split_layers.shape_to_geom."""
    path = Path(shape)
    path.reify()
    rings = []
    for sub in path.as_subpaths():
        pts = _sample_subpath(sub)
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
        winding = sum(sign for poly, sign in rings if poly.contains(pt))
        if winding != 0:
            faces.append(face)
    if not faces:
        return None
    g = unary_union(faces)
    return g if g.is_valid else g.buffer(0)


def load_svg_geoms(svg_path, exclude=()):
    """Every filled shape in the file, minus those whose CSS class is in
    `exclude` (the poster's title, stripes and lettering are one class)."""
    svg = SVG.parse(svg_path, reify=True)
    geoms = []
    for el in svg.elements():
        if isinstance(el, Shape):
            if el.values.get("class") in exclude:
                continue
            g = _shape_to_geom(el)
            if g is not None and not g.is_empty:
                geoms.append(g)
    return geoms


def _polys(geom):
    if isinstance(geom, Polygon):
        return [geom]
    if isinstance(geom, MultiPolygon):
        return list(geom.geoms)
    return [g for g in getattr(geom, "geoms", []) if isinstance(g, Polygon)]


def _outer(geom):
    return unary_union([Polygon(p.exterior) for p in _polys(geom)])


def _fit_height(geom, height):
    minx, miny, maxx, maxy = geom.bounds
    k = height / (maxy - miny)
    return scale(geom, xfact=k, yfact=k, origin=(0, 0))


def silhouette(svg_paths, height, exclude=(), close_mm=0.0, min_piece_mm2=0.0):
    """Outer boundary of everything drawn, H mm tall, centred, y up.
    close_mm: morphological closing (dilate then erode) that fills gaps
    narrower than twice it, such as the hairlines left where excluded
    outline strokes sat. min_piece_mm2: drop islands smaller than this."""
    union = unary_union([g for p in svg_paths for g in load_svg_geoms(p, exclude)])
    outer = _outer(union)
    minx, miny, maxx, maxy = outer.bounds
    k = height / (maxy - miny)
    # SVG y runs down the page; the drum frame wants y up.
    g = scale(outer, xfact=k, yfact=-k, origin=(0, 0))
    if close_mm > 0:
        g = _outer(g.buffer(close_mm, join_style=2).buffer(-close_mm, join_style=2))
    if min_piece_mm2 > 0:
        g = unary_union([p for p in _polys(g) if p.area >= min_piece_mm2])
    g = _fit_height(g, height)          # the dropped specks no longer set the height
    g = g.simplify(SIMPLIFY_MM, preserve_topology=True)
    minx, miny, maxx, maxy = g.bounds
    return translate(g, xoff=-(minx + maxx) / 2, yoff=-(miny + maxy) / 2)


# ---------------------------------------------------------------- DXF in / out

def read_polylines(path):
    """[(points, closed)] for every LWPOLYLINE in the model space."""
    out = []
    for e in ezdxf.readfile(path).modelspace().query("LWPOLYLINE"):
        out.append(([(x, y) for x, y, *_ in e.get_points()], bool(e.closed)))
    return out


def write_polylines(path, polylines):
    doc = ezdxf.new()
    doc.header["$INSUNITS"] = 4  # millimetres
    msp = doc.modelspace()
    for pts, closed in polylines:
        msp.add_lwpolyline(pts, close=closed)
    doc.saveas(path)


def geom_polylines(geom):
    return [(list(p.exterior.coords)[:-1], True) for p in _polys(geom)]


def bbox(polylines):
    xs = [x for pts, _ in polylines for x, _ in pts]
    ys = [y for pts, _ in polylines for _, y in pts]
    return min(xs), max(xs), min(ys), max(ys)


def transform(polylines, cx, cy, flip_y=False):
    """Mirror about the x axis if asked, then move the bbox centre to (cx, cy)."""
    pl = [([(x, -y if flip_y else y) for x, y in pts], c) for pts, c in polylines]
    minx, maxx, miny, maxy = bbox(pl)
    dx, dy = cx - (minx + maxx) / 2, cy - (miny + maxy) / 2
    return [([(x + dx, y + dy) for x, y in pts], c) for pts, c in pl]


def preview(geom, png_path):
    minx, miny, maxx, maxy = geom.bounds
    w = int((maxx - minx) * PREVIEW_PX_PER_MM) + 8
    h = int((maxy - miny) * PREVIEW_PX_PER_MM) + 8
    img = Image.new("RGB", (w, h), (24, 24, 24))
    draw = ImageDraw.Draw(img)
    for p in _polys(geom):
        draw.polygon([((x - minx) * PREVIEW_PX_PER_MM + 4, (maxy - y) * PREVIEW_PX_PER_MM + 4)
                      for x, y in p.exterior.coords], fill=(213, 57, 43))
    img.save(png_path)


# ---------------------------------------------------------------- commands

def _report(polylines):
    print("bbox: %.3f %.3f %.3f %.3f" % bbox(polylines))


def silhouette_cmd(svg_paths, out_path, height, exclude=(), close_mm=0.0, min_piece_mm2=0.0):
    g = silhouette(svg_paths, height, exclude, close_mm, min_piece_mm2)
    pl = geom_polylines(g)
    write_polylines(out_path, pl)
    preview(g, os.path.splitext(out_path)[0] + ".png")
    print("pieces: %d, vertices: %d" % (len(pl), sum(len(p) for p, _ in pl)))
    _report(pl)


def art(in_path, out_path):
    pl = transform(read_polylines(in_path), 0.0, 0.0, flip_y=False)
    write_polylines(out_path, pl)
    _report(pl)


def place(in_path, out_path, cx, cy, flip_y=False):
    pl = transform(read_polylines(in_path), cx, cy, flip_y)
    write_polylines(out_path, pl)
    _report(pl)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("silhouette")
    s.add_argument("paths", nargs="+", help="one or more SVG files, then the output DXF")
    s.add_argument("--height", type=float, required=True)
    s.add_argument("--exclude", default="", help="comma-separated CSS classes to leave out, e.g. st0,st9")
    s.add_argument("--close", type=float, default=0.0, help="closing radius in mm; fills gaps narrower than twice this")
    s.add_argument("--min-piece", type=float, default=0.0, help="drop islands smaller than this many mm2")
    a = sub.add_parser("art")
    a.add_argument("src")
    a.add_argument("dst")
    p = sub.add_parser("place")
    p.add_argument("src")
    p.add_argument("dst")
    p.add_argument("--cx", type=float, required=True)
    p.add_argument("--cy", type=float, required=True)
    p.add_argument("--flip-y", action="store_true")
    ns = ap.parse_args(argv)
    if ns.cmd == "silhouette":
        silhouette_cmd(ns.paths[:-1], ns.paths[-1], ns.height,
                       tuple(c for c in ns.exclude.split(",") if c), ns.close, ns.min_piece)
    elif ns.cmd == "art":
        art(ns.src, ns.dst)
    else:
        place(ns.src, ns.dst, ns.cx, ns.cy, ns.flip_y)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
