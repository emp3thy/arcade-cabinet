"""Tests for cad/art/drum_art.py: SVG layers to a silhouette DXF, DXF
re-centring and placement for the drum's wrapped debosses."""
import os
import sys

import ezdxf
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import drum_art  # noqa: E402

SVG_HEAD = '<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">'


def _svg(path, d):
    path.write_text(SVG_HEAD + '<path d="%s"/></svg>' % d, encoding="utf-8")


def _dxf(path, pts):
    doc = ezdxf.new()
    doc.modelspace().add_lwpolyline(pts, close=True)
    doc.saveas(path)


def _bbox(path):
    xs, ys = [], []
    for e in ezdxf.readfile(path).modelspace().query("LWPOLYLINE"):
        for x, y, *_ in e.get_points():
            xs.append(x)
            ys.append(y)
    return min(xs), max(xs), min(ys), max(ys)


def test_silhouette_unions_two_overlapping_squares_and_drops_holes(tmp_path):
    _svg(tmp_path / "a.svg", "M0,0 L100,0 L100,100 L0,100 Z")
    # second square 50..150 with a 20 x 20 hole drawn the other way round
    _svg(tmp_path / "b.svg", "M50,50 L150,50 L150,150 L50,150 Z M90,90 L90,110 L110,110 L110,90 Z")
    g = drum_art.silhouette([str(tmp_path / "a.svg"), str(tmp_path / "b.svg")], height=59)
    minx, miny, maxx, maxy = g.bounds
    assert maxy - miny == pytest.approx(59.0, abs=0.01)
    assert maxx - minx == pytest.approx(59.0, abs=0.01)
    assert (minx + maxx) / 2 == pytest.approx(0.0, abs=0.01)
    assert (miny + maxy) / 2 == pytest.approx(0.0, abs=0.01)
    assert g.area == pytest.approx(59 * 59 * 7 / 9, abs=0.5)
    polys = list(g.geoms) if hasattr(g, "geoms") else [g]
    assert all(len(p.interiors) == 0 for p in polys)


def test_silhouette_excludes_classes(tmp_path):
    p = tmp_path / "c.svg"
    p.write_text(SVG_HEAD + '<path class="st0" d="M0,0 L100,0 L100,100 L0,100 Z"/>'
                 '<path class="st3" d="M120,0 L170,0 L170,50 L120,50 Z"/></svg>', encoding="utf-8")
    g = drum_art.silhouette([str(p)], height=59, exclude=("st0",))
    minx, miny, maxx, maxy = g.bounds
    assert maxy - miny == pytest.approx(59.0, abs=0.01)
    assert maxx - minx == pytest.approx(59.0, abs=0.01)   # only the 50 x 50 square is left
    assert g.area == pytest.approx(59 * 59, abs=0.5)


def test_silhouette_closing_merges_hairline_gaps_and_drops_specks(tmp_path):
    p = tmp_path / "d.svg"
    # two 100-unit squares with a 1-unit gap (0.59 mm after scaling to 59 tall)
    # and a 2 x 2 unit speck well away from them
    p.write_text(SVG_HEAD + '<path d="M0,0 L100,0 L100,100 L0,100 Z"/>'
                 '<path d="M101,0 L201,0 L201,100 L101,100 Z"/>'
                 '<path d="M150,150 L152,150 L152,152 L150,152 Z"/></svg>', encoding="utf-8")
    g = drum_art.silhouette([str(p)], height=59, close_mm=0.4, min_piece_mm2=1.0)
    polys = list(g.geoms) if hasattr(g, "geoms") else [g]
    assert len(polys) == 1
    minx, miny, maxx, maxy = g.bounds
    assert maxy - miny == pytest.approx(59.0, abs=0.01)          # the speck no longer sets the height
    assert maxx - minx == pytest.approx(59.0 * 2.01, abs=0.05)


def test_place_flip_and_centre(tmp_path):
    src, dst = tmp_path / "in.dxf", tmp_path / "out.dxf"
    _dxf(src, [(0, 0), (10, 0), (10, 20), (0, 20)])
    drum_art.place(str(src), str(dst), cx=5, cy=-67, flip_y=True)
    assert _bbox(dst) == pytest.approx((0, 10, -77, -57), abs=1e-6)
    pts = [tuple(p[:2]) for p in ezdxf.readfile(dst).modelspace().query("LWPOLYLINE")[0].get_points()]
    assert (0, -77) in [(round(x, 6), round(y, 6)) for x, y in pts]


def test_art_recentres_logo_sized_box(tmp_path):
    src, dst = tmp_path / "in.dxf", tmp_path / "out.dxf"
    _dxf(src, [(-58.5, 43.0), (58.479, 43.0), (58.479, 102.777), (-58.5, 102.777)])
    drum_art.art(str(src), str(dst))
    minx, maxx, miny, maxy = _bbox(dst)
    assert (minx + maxx) / 2 == pytest.approx(0.0, abs=1e-6)
    assert (miny + maxy) / 2 == pytest.approx(0.0, abs=1e-6)
    assert maxx - minx == pytest.approx(116.979, abs=1e-6)
    assert maxy - miny == pytest.approx(59.777, abs=1e-6)
