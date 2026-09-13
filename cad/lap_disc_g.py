"""Lap pad, D-014: the nested disc. Stage G -- art pocket in the plate, in the
document that holds stages A to F.

A shallow rectangular recess in the plate's top face under the character
art, so the slicer can colour its floor black and the per-colour art layers
(cad/art/layers/) sit inside it:

  art_pocket   pocket_w x pocket_h, art_pocket_d deep from plate_top_z,
               centred at (art_cx, art_cy). pocket_w/h derive from the art's
               placed size (art_w x art_h, the decal of cad/lap_disc_art.py)
               plus art_margin a side.

Layout (owner, 2026-09-13): "2-3 mm bigger than the image". The band in
front of the cluster is tight: with art_margin 2.2 the pocket corners clear
the stick's raised disc by 1.6 mm, the LK disc by 2.8 mm and the plate's
rounded edge by about 1.9 mm of flat. The margin cannot grow without
shrinking the art. Oracle: the cut removes exactly pocket_w * pocket_h *
art_pocket_d -- the pocket lies on flat plate with no raised disc inside it.
"""
FH_ATTEMPT = 3
FH_OPTS = {
    "only_params": ["art_w", "art_h", "art_cx", "art_cy", "art_margin", "art_pocket_d"],
    "liveness_budget_s": 120,
}
INTERFERENCE_ALLOWED = []
CLEARANCES = []
EXPECT_DEAD = []  # namespace is reused across executes
from fusionhelper.buildkit import *

import adsk.core
import adsk.fusion
import math

PARAMS_G = (
    ("art_w",        "45.7 mm", "mm", "character art width on the plate (cad/art/chunli.png, 0.7141 w/h)"),
    ("art_h",        "64 mm",   "mm", "character art height on the plate"),
    ("art_cx",       "0 mm",    "mm", "art centre x"),
    ("art_cy",       "-85 mm",  "mm", "art centre y; the band in front of the cluster"),
    ("art_margin",   "2.2 mm",  "mm", "pocket margin round the art"),
    ("art_pocket_d", "0.6 mm",  "mm", "pocket depth; three 0.2 layers for the black floor"),
    ("pocket_w",     "art_w + 2 * art_margin", "mm", "derived"),
    ("pocket_h",     "art_h + 2 * art_margin", "mm", "derived"),
    ("art_floor_z",  "plate_top_z - art_pocket_d", "mm", "derived: pocket floor"),
)
NEEDED = ("plate_top_z", "plate_dia", "stick_x", "stick_y", "stick_disc_d", "btn_disc_d", "lk_x", "lk_y", "plate_r")
BUTTONS = ("lp", "mp", "hp", "lk", "mk", "hk")


def ensure_params(ctx):
    for name in NEEDED:
        if ctx.up.itemByName(name) is None:
            raise RuntimeError("parameter %s missing: run stages A to F first" % name)
    for name, expr, unit, comment in PARAMS_G:
        existing = ctx.up.itemByName(name)
        if existing is not None:
            if existing.expression.replace(" ", "") != expr.replace(" ", ""):
                raise RuntimeError(
                    "parameter %s already exists with expression %r, wanted %r"
                    % (name, existing.expression, expr))
            continue
        ctx.up.add(name, ctx.cbs(expr), unit, comment)
        adsk.doEvents()


def body_named(ctx, name):
    for b in ctx.root.bRepBodies:
        if b.name == name:
            return b
    raise RuntimeError("no body named %s" % name)


def feature_exists(ctx, name):
    for n in (name, name + " (1)"):
        if ctx.extrudes.itemByName(n) is not None:
            return True
    return False


def run(_context: str):
    app = adsk.core.Application.get()
    if not app.activeDocument.name.startswith("Arcade Controller"):
        raise RuntimeError("wrong document " + app.activeDocument.name)
    ctx = BuildCtx(app)
    ensure_params(ctx)
    v = ctx.val

    # ---- layout check before cutting: pocket clear of discs and plate edge ----
    hw, hh = v("pocket_w") / 2, v("pocket_h") / 2
    cx, cy = v("art_cx"), v("art_cy")
    corners = [(cx + sx * hw, cy + sy * hh) for sx in (-1, 1) for sy in (-1, 1)]
    flat_r = v("plate_dia") / 2 - v("plate_r")
    edge = min(flat_r - math.hypot(x, y) for x, y in corners)
    if edge < 0.1:
        raise RuntimeError("pocket corner within %.2f mm of the plate's rounded edge" % (edge * 10))
    discs = [(v("stick_x"), v("stick_y"), v("stick_disc_d") / 2)]
    discs += [(v(n + "_x"), v(n + "_y"), v("btn_disc_d") / 2) for n in BUTTONS]
    clear = []
    for dcx, dcy, r in discs:
        dx = max(cx - hw - dcx, 0, dcx - (cx + hw))
        dy = max(cy - hh - dcy, 0, dcy - (cy + hh))
        clear.append(math.hypot(dx, dy) - r)
    if min(clear) < 0.1:
        raise RuntimeError("pocket within %.2f mm of a raised disc" % (min(clear) * 10))
    print("pocket %.1f x %.1f mm at (%.1f, %.1f); flat-edge margin %.2f mm, nearest disc %.2f mm" % (
        hw * 20, hh * 20, cx * 10, cy * 10, edge * 10, min(clear) * 10))

    # ---- the pocket ---------------------------------------------------------
    plate = body_named(ctx, "plate")
    if not feature_exists(ctx, "art_pocket"):
        top = ctx.planes.itemByName("plate_top_plane")
        if top is None:
            raise RuntimeError("plate_top_plane missing")
        sk = ctx.root.sketches.add(top)
        sk.name = "art_pocket"
        ctx.bound_rect2(
            sk, (cx, cy, v("plate_top_z")), hw, hh,
            u_size="pocket_w", v_size="pocket_h",
            u_pos=("art_cx", "pocket_w / 2"), v_pos=("art_cy", "pocket_h / 2"))
        if not sk.isFullyConstrained:
            raise RuntimeError("art_pocket sketch not fully constrained")
        want = v("pocket_w") * v("pocket_h") * v("art_pocket_d")
        v0 = plate.volume
        f = ctx.blind_cut(ctx.all_profiles(sk), "art_pocket_d", [plate], "pocket", min_vol_cm3=0.5 * want)
        f.name = "art_pocket"
        plate = body_named(ctx, "plate")
        removed = v0 - plate.volume
        if abs(removed - want) > 0.01 * want:
            raise RuntimeError("art_pocket removed %.4f cm3, wanted %.4f" % (removed, want))
        print("art pocket: -%.4f cm3 (want %.4f)" % (removed, want))
    adsk.doEvents()

    # ---- read-back: a flat floor at art_floor_z under the art centre ----------
    floor = None
    for f in plate.faces:
        pl = adsk.core.Plane.cast(f.geometry)
        # a cut's floor can report its surface normal flipped (measured, attempt 1):
        # test |normal.z|; z and position pick the floor unambiguously
        if pl is None or abs(pl.normal.z) < 0.999:
            continue
        bb = f.boundingBox
        if abs(bb.maxPoint.z - v("art_floor_z")) < 0.001 and bb.minPoint.x <= cx <= bb.maxPoint.x and bb.minPoint.y <= cy <= bb.maxPoint.y:
            floor = f
    if floor is None:
        raise RuntimeError("no pocket floor face at z=%.2f mm" % (v("art_floor_z") * 10))
    fb = floor.boundingBox
    print("pocket floor: %.1f x %.1f mm at z %.2f" % ((fb.maxPoint.x - fb.minPoint.x) * 10, (fb.maxPoint.y - fb.minPoint.y) * 10, fb.maxPoint.z * 10))

    tl = ctx.des.timeline
    bad = []
    for i in range(tl.count):
        it = tl.item(i)
        if it.isRolledBack:
            continue  # the owner's rolled-back UI experiments (Sketch27 / Scale1, 2026-09-13) are not part of the model
        feat = adsk.fusion.Feature.cast(it.entity)
        if feat is not None and feat.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:
            bad.append(feat.name)
    if bad:
        raise RuntimeError("unhealthy timeline entries: %s" % bad)

    for name in ("shell", "plate", "tpu_ring", "tpu_tyre"):
        b = body_named(ctx, name)
        bb = b.boundingBox
        print("%s: %.1f x %.1f x %.1f mm, z %.1f..%.1f, %.2f cm3, %d faces" % (
            b.name,
            (bb.maxPoint.x - bb.minPoint.x) * 10,
            (bb.maxPoint.y - bb.minPoint.y) * 10,
            (bb.maxPoint.z - bb.minPoint.z) * 10,
            bb.minPoint.z * 10, bb.maxPoint.z * 10,
            b.volume, b.faces.count))
    print("done")
