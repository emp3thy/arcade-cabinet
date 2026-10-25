"""Pi console drum, D-021. Stage F -- two fixes from the whole-branch review
(2026-10-22), in the document that holds stages A to E.

1. The Pi re-seated. A Pi 4B's holes sit 3.5 and 61.5 mm from the SD edge
   of the 85 mm board, so stage A's hole pattern centred on the axis put the
   BOARD 10 mm toward its USB edge, and the USB and ethernet plugs ran into
   the two back columns. The board is now centred and turned 90 deg: USB
   edge to the front (-y), HDMI edge to the left (-x), SD edge to the back,
   and the board centre pi_board_y = 10 mm toward the back (centred, the
   USB edge had 34.5 mm to the front wall, under a 35 mm straight plug;
   measured on attempt 1). Bosses at (+-pi_hole_x/2, pi_board_y + pi_off_y
   +- pi_hole_y/2) = (+-24.5, 49) and (+-24.5, -9), pi_off_y being the 10 mm
   the hole pattern sits toward the SD edge. Stage A's pi_boss and pi_insert features, their sketches and the
   pi_hole_px / pi_hole_py parameters are deleted; the new ones are built on
   the same floor_top and boss_top planes. Plug room, asserted analytically:
   USB-A and RJ45 plugs leave the front edge at y -42.5 within |x| <= 28 and
   have the front wall at y -77 with the front columns out at |x| >= 64;
   micro-HDMI / USB-C plugs leave the left edge at x -28 and have 49 mm to
   the left wall with column 2 (x -72..-64, y 21..29) 16 mm beyond a 20 mm
   plug.
2. The column feet lowered. col_foot_z was 6 mm with the comment "on the
   base floor's top face" while the floor top is z 3: the screws crossed a
   3 mm air gap. col_foot_z is now floor_t + 0.3 mm: the feet sit 0.3 above
   the floor, the cup seats on the rim, and an M3 x 10 engages the full
   insert.
Then the stage E audit, exports and renders are repeated (one extra render
with the inlays hidden so the livery recesses show).

Oracles: deleting the old bosses and bores takes exactly their net volume
out; the new ones put it back; the column extension adds 4 x pi r^2 x 2.7;
every circle is asserted at its signed centre before its extrude.
"""
FH_ATTEMPT = 1
FH_OPTS = {
    "only_params": ["pi_hole_x", "pi_hole_y", "pi_off_y", "pi_board_y"],
    "liveness_budget_s": 600,
    "max_bodies": 20,
    "force_liveness": True,
}
INTERFERENCE_ALLOWED = []
CLEARANCES = []
# pi_hole_x and pi_hole_y move the four bosses symmetrically about (0, pi_off_y):
# the signature probe cannot see them (stage A's intake_r precedent); proven live below.
EXPECT_DEAD = ["pi_hole_x", "pi_hole_y"]
# fh-bundle: kit begin v2 00ca86d51507
"""The build kit: one canonical copy of the helpers every Fusion build
script used to copy-paste (measured drift: back_splices.py carried a
stale face-count blind_cut while the volume fixes lived only in
build16.py).

Author scripts do `from fusionhelper.buildkit import *`; the bundler
(fusionhelper.bundle) replaces that line with this file's source so a
single self-contained artifact reaches Fusion. Offline (tests, pyright)
this module imports like any other; inside Fusion the same text runs
inlined.

Validation policy (api-notes S14/S15): volume-threshold is the DEFAULT
for cuts and cut patterns; face-count is opt-in for small isolated holes
only. Pattern seed cuts must cut exactly ONE body (multi-body seeds fail
replication with R-Pattern85/PATTERN_FEATURES_NO_PASTE and no causal
error text).
"""
import adsk.core
import adsk.fusion

KIT_VERSION = "2"

__all__ = ["KIT_VERSION", "BuildCtx"]


class BuildCtx:
    """Per-run Fusion handles + helper methods. Create once at the top
    of run(): ctx = BuildCtx(adsk.core.Application.get())"""

    def __init__(self, app):
        self.app = app
        self.des = adsk.fusion.Design.cast(app.activeProduct)
        self.root = self.des.rootComponent
        self.up = self.des.userParameters
        self.extrudes = self.root.features.extrudeFeatures
        self.patterns = self.root.features.rectangularPatternFeatures
        self.planes = self.root.constructionPlanes
        self.ops = adsk.fusion.FeatureOperations
        self.dims_or = adsk.fusion.DimensionOrientations
        self.dirs = adsk.fusion.ExtentDirections
        self.pt = adsk.core.Point3D.create
        self.cbs = adsk.core.ValueInput.createByString
        self.x_axis = self.root.xConstructionAxis
        self.y_axis = self.root.yConstructionAxis
        self.U = (1.0, 0.0, 0.0)
        self.V = (0.0, 1.0, 0.0)
        self._resolved = {}
        self._circle_jitter = 0

    def val(self, name):
        return self.up.itemByName(name).value  # cm

    def plane_at_z(self, off_expr, name):
        pin = self.planes.createInput()
        pin.setByOffset(self.root.xYConstructionPlane, self.cbs(off_expr))
        pl = self.planes.add(pin)
        pl.name = name
        return pl

    def all_profiles(self, sk):
        coll = adsk.core.ObjectCollection.create()
        for pr in sk.profiles:  # fusionhelper: allow R11 — collection add, not a document mutation
            coll.add(pr)
        return coll

    def bound_rect2(self, sk, w, hu, hv, u_size=None, v_size=None,
                    u_pos=None, v_pos=None):
        """Constrained rectangle. w = world centre; position expressions
        are (centre_expr, half_size_expr) pairs — base is the CENTRE
        coordinate expression (measured: corner-based baselines snapped
        the board to the wrong quadrant)."""
        pt, U, V = self.pt, self.U, self.V
        dims_or = self.dims_or
        c = sk.modelToSketchSpace(pt(w[0], w[1], w[2]))
        pu = sk.modelToSketchSpace(pt(w[0] + U[0], w[1] + U[1], w[2] + U[2]))
        pv = sk.modelToSketchSpace(pt(w[0] + V[0], w[1] + V[1], w[2] + V[2]))
        if abs(pu.x - c.x) >= abs(pu.y - c.y):
            shx, shy = hu, hv
            ax = (u_size, u_pos, 1 if pu.x > c.x else -1)
            ay = (v_size, v_pos, 1 if pv.y > c.y else -1)
        else:
            shx, shy = hv, hu
            ax = (v_size, v_pos, 1 if pv.x > c.x else -1)
            ay = (u_size, u_pos, 1 if pu.y > c.y else -1)
        lines = sk.sketchCurves.sketchLines.addTwoPointRectangle(
            pt(c.x - shx, c.y - shy, 0), pt(c.x + shx, c.y + shy, 0))
        gc = sk.geometricConstraints
        h_line = None
        v_line = None
        for k in range(lines.count):
            ln = lines.item(k)
            s, e = ln.startSketchPoint.geometry, ln.endSketchPoint.geometry
            if abs(e.x - s.x) >= abs(e.y - s.y):
                gc.addHorizontal(ln)
                if h_line is None:
                    h_line = ln
            else:
                gc.addVertical(ln)
                if v_line is None:
                    v_line = ln
        if h_line is None or v_line is None:
            raise RuntimeError("rect missing axis-aligned line")
        corner = lines.item(0).startSketchPoint
        anchor = pt(c.x + shx + 0.5, c.y - shy - 0.5, 0)
        d = sk.sketchDimensions.addDistanceDimension(
            h_line.startSketchPoint, h_line.endSketchPoint,
            dims_or.HorizontalDimensionOrientation, anchor)
        d.parameter.expression = ax[0] if ax[0] else "%.4f mm" % (shx * 20)
        d = sk.sketchDimensions.addDistanceDimension(
            v_line.startSketchPoint, v_line.endSketchPoint,
            dims_or.VerticalDimensionOrientation, anchor)
        d.parameter.expression = ay[0] if ay[0] else "%.4f mm" % (shy * 20)
        for orient, half_sz, (_, pos, sign), cval in (
                (dims_or.HorizontalDimensionOrientation, shx, ax, c.x),
                (dims_or.VerticalDimensionOrientation, shy, ay, c.y)):
            d = sk.sketchDimensions.addDistanceDimension(
                sk.originPoint, corner, orient, anchor)
            if pos is None:
                d.parameter.expression = "%.4f mm" % (abs(cval - half_sz) * 10)
            else:
                # abs() is load-bearing: a distance dimension is unsigned,
                # so a corner expression that evaluates NEGATIVE (any rect
                # centred on the sketch origin, e.g. '0 mm - (9.65 mm)')
                # is stored negative but SNAPPED POSITIVE by the solver,
                # sliding the whole rectangle sideways by its full width.
                # Measured 2026-08-02; abs() confirmed valid in a Fusion
                # expression and keeps the dimension parametric.
                d.parameter.expression = "abs( %s %s (%s) )" % (
                    pos[0], "-" if sign > 0 else "+", pos[1])

    def bound_circle(self, sk, w, r_cm, dia_expr, x_pos=None, v_pos=None):
        """Jittered creation: coincident-coordinate circles trigger silent
        alignment inference then over-constrain (measured). Dims snap it."""
        pt, U = self.pt, self.U
        dims_or = self.dims_or
        c = sk.modelToSketchSpace(pt(w[0], w[1], w[2]))
        pu = sk.modelToSketchSpace(pt(w[0] + U[0], w[1] + U[1], w[2] + U[2]))
        self._circle_jitter += 1
        j = self._circle_jitter
        circle = sk.sketchCurves.sketchCircles.addByCenterRadius(
            pt(c.x + 0.011 + 0.003 * j, c.y + 0.017 + 0.005 * j, 0), r_cm)
        anchor = pt(c.x + r_cm + 0.4, c.y - 0.4, 0)
        if abs(pu.x - c.x) >= abs(pu.y - c.y):
            h_pos, v_pos_ = x_pos, v_pos
        else:
            h_pos, v_pos_ = v_pos, x_pos
        d = sk.sketchDimensions.addDistanceDimension(
            sk.originPoint, circle.centerSketchPoint,
            dims_or.HorizontalDimensionOrientation, anchor)
        d.parameter.expression = (h_pos if h_pos
                                  else "%.4f mm" % (abs(c.x) * 10))
        d = sk.sketchDimensions.addDistanceDimension(
            sk.originPoint, circle.centerSketchPoint,
            dims_or.VerticalDimensionOrientation, anchor)
        d.parameter.expression = (v_pos_ if v_pos_
                                  else "%.4f mm" % (abs(c.y) * 10))
        d = sk.sketchDimensions.addDiameterDimension(circle, anchor)
        d.parameter.expression = dia_expr
        return circle

    # ---- cuts and joins (volume-threshold validation by default) --------

    def _one_side(self, inp, dist_expr, direction):
        ext = adsk.fusion.DistanceExtentDefinition.create(self.cbs(dist_expr))
        inp.setOneSideExtent(ext, direction)

    def _try_dirs(self, kind):
        if kind in self._resolved:
            return (self._resolved[kind], None)
        return (self.dirs.PositiveExtentDirection,
                self.dirs.NegativeExtentDirection)

    def faces_of(self, bodies):
        return sum(b.faces.count for b in bodies)

    def through_cut(self, profs, depth_expr, participants, *,
                    min_vol_cm3=0.02):
        """Symmetric through-cut. Volume-validated (S14/S15: face counts
        can stay flat or DROP on seam-spanning cuts)."""
        return self.sym_cut(profs, depth_expr, participants,
                            min_vol_cm3=min_vol_cm3)

    def sym_cut(self, profs, depth_expr, participants, *, min_vol_cm3=0.02):
        v0 = sum(b.volume for b in participants)
        inp = self.extrudes.createInput(profs, self.ops.CutFeatureOperation)
        inp.setSymmetricExtent(self.cbs(depth_expr), True)
        inp.participantBodies = participants
        f = self.extrudes.add(inp)
        if v0 - sum(b.volume for b in participants) <= min_vol_cm3:
            f.deleteMe()
            raise RuntimeError("symmetric cut removed no volume")
        return f

    def blind_cut(self, profs, dist_expr, participants, kind="cut", *,
                  min_vol_cm3=0.02):
        v0 = sum(b.volume for b in participants)
        for d in self._try_dirs(kind):
            adsk.doEvents()
            if d is None:
                break
            inp = self.extrudes.createInput(
                profs, self.ops.CutFeatureOperation)
            self._one_side(inp, dist_expr, d)
            inp.participantBodies = participants
            f = self.extrudes.add(inp)
            if v0 - sum(b.volume for b in participants) > min_vol_cm3:
                self._resolved[kind] = d
                return f
            f.deleteMe()
        raise RuntimeError("blind cut cut nothing (%s)" % kind)

    def checked_join(self, profs, dist_expr, target, predicate, kind):
        for d in self._try_dirs(kind):
            adsk.doEvents()
            if d is None:
                break
            inp = self.extrudes.createInput(
                profs, self.ops.JoinFeatureOperation)
            self._one_side(inp, dist_expr, d)
            inp.participantBodies = [target]
            f = self.extrudes.add(inp)
            if predicate(target):
                self._resolved[kind] = d
                return f
            f.deleteMe()
        raise RuntimeError("join never satisfied predicate (%s)" % kind)

    def checked_newbody(self, profs, dist_expr, predicate, kind):
        for d in self._try_dirs(kind):
            adsk.doEvents()
            if d is None:
                break
            inp = self.extrudes.createInput(
                profs, self.ops.NewBodyFeatureOperation)
            self._one_side(inp, dist_expr, d)
            f = self.extrudes.add(inp)
            body = f.bodies.item(0)
            if predicate(body):
                self._resolved[kind] = d
                return f, body
            f.deleteMe()
        raise RuntimeError("new body never satisfied predicate (%s)" % kind)

    # ---- patterns -------------------------------------------------------

    def _pattern(self, coll, ax, n, d, validate, adjust):
        """Direction/compute retry ladder. NOTE (S15, measured): a seed
        CUT that removes material from more than one body never
        replicates (R-Pattern85 / PATTERN_FEATURES_NO_PASTE, no causal
        error text) — reshape the seed to cut exactly one body."""
        healthy = (
            adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,
            adsk.fusion.FeatureHealthStates.WarningFeatureHealthState)
        reasons = []
        perp = self.y_axis if ax == self.x_axis else self.x_axis
        popts = adsk.fusion.PatternComputeOptions
        modes = ((popts.AdjustPatternCompute, popts.IdenticalPatternCompute)
                 if adjust else (None,))
        for dd in (d, "-(%s)" % d):
            adsk.doEvents()
            for mode in modes:
                adsk.doEvents()
                inp = self.patterns.createInput(
                    coll, ax, self.cbs(n), self.cbs(dd),
                    adsk.fusion.PatternDistanceType
                    .SpacingPatternDistanceType)
                inp.setDirectionTwo(perp, self.cbs("1"), self.cbs("0 mm"))
                if mode is not None:
                    inp.patternComputeOption = mode  # pyright: ignore[reportAttributeAccessIssue]
                try:
                    f = self.patterns.add(inp)
                except Exception as e:
                    reasons.append("%s/%s add-raise %s"
                                   % (dd, mode, str(e)[:50]))
                    continue
                if f.healthState in healthy and validate(f):
                    return f
                reasons.append("%s/%s hs=%s" % (dd, mode, f.healthState))
                f.deleteMe()
        raise RuntimeError("pattern never validated: " + " | ".join(reasons))

    def pattern_bodies(self, bodies, ax, n, d, predicate):
        """Body pattern (no compute-option: body patterns reject it).
        predicate(feature) -> bool accepts/rejects the whole pattern —
        e.g. a bounds check that every new body landed inside the part."""
        coll = adsk.core.ObjectCollection.create()
        for b in bodies:  # fusionhelper: allow R11 — collection add, not a document mutation
            coll.add(b)
        f = self._pattern(coll, ax, n, d, predicate, adjust=False)
        out = []
        for i in range(f.bodies.count):
            out.append(f.bodies.item(i))
        return out

    def pattern_cut(self, feats, ax, n, d, watch, *,
                    min_vol_cm3=None, min_new_faces=None):
        """Pattern of cut features. Volume threshold is the default
        choice (S14/S15); face-count is opt-in for small isolated holes.
        Exactly one of min_vol_cm3 / min_new_faces must be given."""
        if (min_vol_cm3 is None) == (min_new_faces is None):
            raise ValueError(
                "pass exactly one of min_vol_cm3 / min_new_faces")
        coll = adsk.core.ObjectCollection.create()
        for f in feats:  # fusionhelper: allow R11 — collection add, not a document mutation
            coll.add(f)
        if min_vol_cm3 is not None:
            v0 = sum(b.volume for b in watch)

            def validate(_f):
                return v0 - sum(b.volume for b in watch) >= min_vol_cm3
        else:
            before = self.faces_of(watch)

            def validate(_f):
                return self.faces_of(watch) - before >= min_new_faces  # pyright: ignore[reportOperatorIssue]
        return self._pattern(coll, ax, n, d, validate, adjust=True)
# fh-bundle: kit end

import adsk.core
import adsk.fusion
import math
import os

DOC_PREFIX = "arcade unit v1"
ROOT = r"C:/Users/gethi/sources/arcade-cabinet/.claude/worktrees/pi-drum/cad"
RENDER_DIR = ROOT + "/renders"
EXPORT_DIR = ROOT + "/exports"
PI = math.pi
MM = 0.1
TOL_MM = 0.05
OVERHANG_NZ = -0.7075
LEDGE_MM, BRIDGE_MM = 1.5, 20.0
PLUG_LONG_MM, PLUG_SHORT_MM, PLUG_HALF_W_MM = 35.0, 20.0, 8.0   # USB-A/RJ45, micro-HDMI/USB-C, half width

NEEDED = ("drum_r", "cavity_r", "floor_t", "drum_h", "col_r", "col_d", "col_foot_z", "web_z1",
          "pi_hole_px", "pi_hole_py", "pi_boss_d", "pi_boss_h", "pi_insert_hole", "pi_insert_h", "art_pocket_d")
PARAMS = (
    ("pi_hole_x", "49 mm", "mm", "Pi 4B hole pitch across x (the board's 56 mm width runs along x)"),
    ("pi_hole_y", "58 mm", "mm", "Pi 4B hole pitch along y (the 85 mm length runs along y, USB edge at -y)"),
    ("pi_off_y",  "10 mm", "mm", "hole-pattern centre sits this far toward the SD edge (+y) from the board centre"),
    ("pi_board_y", "10 mm", "mm", "board centre toward the back: the USB edge then has 44.5 mm to the front wall for a straight plug (34.5 centred, measured)"),
)
COL_FOOT_NEW = "floor_t + 0.3 mm"
COL_ANGLES = ((20.0), (160.0), (-160.0), (-20.0))
BOSSES = ((1, 1), (-1, 1), (-1, -1), (1, -1))        # (sign x, which y: +1 -> pi_off_y + pi_hole_y/2, -1 -> pi_off_y - pi_hole_y/2)


# ---------------------------------------------------------------- helpers

def ensure_params(ctx):
    for name in NEEDED:
        if ctx.up.itemByName(name) is None:
            raise RuntimeError("parameter %s missing: run stages A to E first" % name)
    for name, expr, unit, comment in PARAMS:
        existing = ctx.up.itemByName(name)
        if existing is not None:
            if existing.expression.replace(" ", "") != expr.replace(" ", ""):
                raise RuntimeError("parameter %s already exists with expression %r, wanted %r"
                                   % (name, existing.expression, expr))
            continue
        ctx.up.add(name, ctx.cbs(expr), unit, comment)
        adsk.doEvents()


def check_delta(label, before, after, want, tol_rel=0.02, tol_abs=0.002):
    got = after - before
    if abs(got - want) > max(tol_rel * abs(want), tol_abs):
        raise RuntimeError("%s: volume changed %.4f cm3, wanted %.4f" % (label, got, want))
    print("%s: %+.4f cm3 (want %+.4f)" % (label, got, want))


def healthy_or_raise(ctx, what):
    healthy = adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState
    tl = ctx.des.timeline
    bad = []
    for i in range(tl.count):
        it = tl.item(i)
        if it.isRolledBack:
            continue
        feat = adsk.fusion.Feature.cast(it.entity)
        if feat is not None and feat.healthState != healthy:
            bad.append("%s (%s)" % (feat.name, feat.errorOrWarningMessage))
    if bad:
        raise RuntimeError("after %s, unhealthy timeline entries: %s" % (what, bad))


def body_named(ctx, name):
    for b in ctx.root.bRepBodies:
        if b.name == name:
            return b
    raise RuntimeError("no body named %s" % name)


def group(ctx, name):
    return [b for b in ctx.root.bRepBodies if b.name == name or b.name.startswith(name + " (")]


def plane_named(ctx, name):
    for i in range(ctx.planes.count):
        if ctx.planes.item(i).name == name:
            return ctx.planes.item(i)
    raise RuntimeError("no construction plane named %s" % name)


def sketch_named(ctx, name):
    for s in ctx.root.sketches:
        if s.name == name:
            return s
    raise RuntimeError("no sketch named %s" % name)


def inside(body, x_mm, y_mm, z_mm):
    return body.pointContainment(adsk.core.Point3D.create(x_mm * MM, y_mm * MM, z_mm * MM)) \
        == adsk.fusion.PointContainment.PointInsidePointContainment


def probe(body, pts, want_inside, label):
    for (x, y, z) in pts:
        if inside(body, x, y, z) != want_inside:
            raise RuntimeError("%s: (%.1f, %.1f, %.1f) should be %s" % (
                label, x, y, z, "solid" if want_inside else "empty"))
    print("%s: %d probes %s" % (label, len(pts), "solid" if want_inside else "empty"))


def assert_circle_xy(sk, circle, x_want, y_want, label):
    m = sk.sketchToModelSpace(circle.centerSketchPoint.geometry)
    if abs(m.x * 10 - x_want) > TOL_MM or abs(m.y * 10 - y_want) > TOL_MM:
        raise RuntimeError("%s: circle landed (%.2f, %.2f), wanted (%.2f, %.2f)" % (
            label, m.x * 10, m.y * 10, x_want, y_want))


def boss_positions_cm(ctx):
    v = ctx.val
    hx, hy, off = v("pi_hole_x") / 2, v("pi_hole_y") / 2, v("pi_off_y") + v("pi_board_y")
    return [(sx * hx, off + sy * hy) for sx, sy in BOSSES]


def boss_circles(ctx, sk, z_cm, r_seed, dia_expr):
    for (x, y), (sx, sy) in zip(boss_positions_cm(ctx), BOSSES):
        c = ctx.bound_circle(sk, (x, y, z_cm), r_seed, dia_expr, x_pos="pi_hole_x / 2",
                             v_pos="abs( pi_board_y + pi_off_y %s pi_hole_y / 2 )" % ("+" if sy > 0 else "-"))
        assert_circle_xy(sk, c, x * 10, y * 10, sk.name)
        adsk.doEvents()


# ---------------------------------------------------------------- build

def reseat_pi(ctx):
    v = ctx.val
    base = body_named(ctx, "base")
    v0 = base.volume
    boss_vol = 4 * PI * (v("pi_boss_d") / 2) ** 2 * v("pi_boss_h")
    bore_vol = 4 * PI * (v("pi_insert_hole") / 2) ** 2 * v("pi_insert_h")
    for feat_name, sk_name in (("pi_insert", "pi_insert_sk"), ("pi_boss", "pi_boss_sk")):
        f = ctx.extrudes.itemByName(feat_name)
        if f is None:
            raise RuntimeError("feature %s not found" % feat_name)
        f.deleteMe()
        adsk.doEvents()
        sketch_named(ctx, sk_name).deleteMe()
        adsk.doEvents()
    healthy_or_raise(ctx, "old bosses removed")
    base = body_named(ctx, "base")
    check_delta("old bosses and bores removed", v0, base.volume, -(boss_vol - bore_vol))
    for name in ("pi_hole_px", "pi_hole_py"):
        if not ctx.up.itemByName(name).deleteMe():
            raise RuntimeError("could not delete parameter %s (still referenced?)" % name)
        adsk.doEvents()

    sk = ctx.root.sketches.add(plane_named(ctx, "floor_top"))
    sk.name = "pi_boss2_sk"
    boss_circles(ctx, sk, v("floor_t"), v("pi_boss_d") / 2, "pi_boss_d")
    v1 = base.volume
    f = ctx.checked_join(ctx.all_profiles(sk), "pi_boss_h", base,
                         lambda b: abs(b.volume - v1 - boss_vol) < 0.02 * boss_vol, "boss2")
    f.name = "pi_boss2"
    check_delta("pi_boss2", v1, base.volume, boss_vol)

    sk = ctx.root.sketches.add(plane_named(ctx, "boss_top"))
    sk.name = "pi_insert2_sk"
    boss_circles(ctx, sk, v("floor_t") + v("pi_boss_h"), v("pi_insert_hole") / 2, "pi_insert_hole")
    v2 = base.volume
    f = ctx.blind_cut(ctx.all_profiles(sk), "pi_insert_h", [base], "insert2", min_vol_cm3=0.01)
    f.name = "pi_insert2"
    check_delta("pi_insert2", v2, base.volume, -bore_vol, tol_rel=0.03)


def lower_column_feet(ctx):
    v = ctx.val
    cup = body_named(ctx, "cup")
    v0 = cup.volume
    old = v("col_foot_z")
    p = ctx.up.itemByName("col_foot_z")
    p.expression = COL_FOOT_NEW  # fusionhelper: allow R5 — bodies re-resolved by name after the write
    adsk.doEvents()
    healthy_or_raise(ctx, "col_foot_z lowered")
    cup = body_named(ctx, "cup")
    want = 4 * PI * (v("col_d") / 2) ** 2 * (old - v("col_foot_z"))
    check_delta("col_foot_z %.1f -> %.1f" % (old * 10, v("col_foot_z") * 10), v0, cup.volume, want)


def plug_room(ctx):
    """Analytic plug clearances for the rotated, centred board. mm."""
    v = ctx.val
    cav, col_r, r_col = v("cavity_r") * 10, v("col_r") * 10, v("col_d") * 5
    cols = [(col_r * math.cos(math.radians(a)), col_r * math.sin(math.radians(a))) for a in COL_ANGLES]
    by = v("pi_board_y") * 10
    # USB edge at y by - 42.5, plugs run -y within |x| <= 28 + half width, to the front wall
    front_room = cav - (42.5 - by)
    blocking = [c for c in cols if c[1] < 0 and abs(c[0]) - r_col < 28 + PLUG_HALF_W_MM]
    print("plug room, USB/RJ45 edge at y %.1f: %.1f mm to the front wall, columns in the plug band: %d" % (
        by - 42.5, front_room, len(blocking)))
    if front_room < PLUG_LONG_MM or blocking:
        raise RuntimeError("USB edge plugs do not fit")
    print("SD edge at y %.1f: %.1f mm to the back wall" % (by + 42.5, cav - (by + 42.5)))
    # HDMI edge at x -28, ports at y by + 42.5 - u for u in 11.2, 26, 39.5, 54, plugs run -x
    y_lo, y_hi = by + 42.5 - 54 - PLUG_HALF_W_MM, by + 42.5 - 11.2 + PLUG_HALF_W_MM
    left_room = cav - 28
    plug_end_x = -28 - PLUG_SHORT_MM
    in_band = [c for c in cols if c[0] < 0 and y_lo <= c[1] <= y_hi]
    nearest = min(abs(c[0]) - r_col for c in in_band) if in_band else None
    print("plug room, HDMI edge: %.1f mm to the left wall; plug ends at x %.1f; nearest column edge at x %s" % (
        left_room, plug_end_x, ("-%.1f" % nearest) if nearest is not None else "none in band"))
    if left_room < PLUG_SHORT_MM or (nearest is not None and nearest < -plug_end_x + 5):
        raise RuntimeError("HDMI edge plugs do not fit")


def read_back(ctx):
    v = ctx.val
    base, cup = body_named(ctx, "base"), body_named(ctx, "cup")
    bz = (v("floor_t") + v("pi_boss_h")) * 10
    pts = [(x * 10, y * 10) for x, y in boss_positions_cm(ctx)]
    probe(base, [(x, y, bz - 1) for x, y in pts], False, "new insert bores at their signed centres")
    probe(base, [(x + 2.5, y, bz - 1) for x, y in pts], True, "new boss walls")
    probe(base, [(29, 24.5, 7), (-29, -24.5, 7), (29, -24.5, 7), (-29, 24.5, 7)], False, "old boss positions clear")
    probe(base, [(x, y, 2.5) for x, y in pts], True, "floor under the new bosses")
    fz = v("col_foot_z") * 10
    cr = v("col_r") * 10
    feet = [(cr * math.cos(math.radians(a)), cr * math.sin(math.radians(a))) for a in COL_ANGLES]
    # the axis is inside the insert bore, so the foot is probed 3.5 mm off-axis, in the column wall
    wall = [(x * (cr - 3.5) / cr, y * (cr - 3.5) / cr) for x, y in feet]
    probe(cup, [(x, y, fz + 0.2) for x, y in wall], True, "column feet just above col_foot_z (in the wall)")
    probe(cup, [(x, y, fz - 0.2) for x, y in wall], False, "air under the column feet")
    probe(base, [(x, y, 2.5) for x, y in wall], True, "floor under the column feet (beside the screw hole)")
    probe(base, [(x, y, 2.5) for x, y in feet], False, "screw holes under the column axes")
    probe(cup, [(x, y, fz + v("insert_hole_h") * 10 - 0.5) for x, y in feet], False, "insert bores moved with the feet")


def prove_live(ctx, name, stepped_expr, point_mm, restore_expr):
    base = body_named(ctx, "base")
    if inside(base, *point_mm):
        raise RuntimeError("prove_live %s: probe point should start empty" % name)
    ctx.up.itemByName(name).expression = stepped_expr  # fusionhelper: allow R5 — body re-resolved by name after the write
    adsk.doEvents()
    base = body_named(ctx, "base")
    moved = inside(base, *point_mm)
    ctx.up.itemByName(name).expression = restore_expr  # fusionhelper: allow R5 — body re-resolved by name after the write
    adsk.doEvents()
    if not moved:
        raise RuntimeError("prove_live %s: bore did not move when stepped to %s" % (name, stepped_expr))
    healthy_or_raise(ctx, "prove_live " + name)
    print("prove_live %s: stepped to %s, bore moved, restored to %s" % (name, stepped_expr, restore_expr))


def prove_symmetric_params(ctx):
    v = ctx.val
    bz = (v("floor_t") + v("pi_boss_h")) * 10 - 1
    x, y = boss_positions_cm(ctx)[0]
    prove_live(ctx, "pi_hole_x", "53 mm", (x * 10, y * 10, bz), "49 mm")
    prove_live(ctx, "pi_hole_y", "62 mm", (x * 10, y * 10, bz), "58 mm")


# ---------------------------------------------------------------- audit (as stage E)

def face_normal(face):
    ev = face.evaluator
    rng = ev.parametricRange()
    if rng is None:
        return None
    pmin, pmax = rng.minPoint, rng.maxPoint
    mid = adsk.core.Point2D.create((pmin.x + pmax.x) / 2, (pmin.y + pmax.y) / 2)
    ok, normals = ev.getNormalsAtParameters([mid])
    if not ok or not normals:
        return None
    return normals[0]


def classify(ctx, face, inverted):
    v = ctx.val
    n = face_normal(face)
    if n is None:
        return False, "no-normal"
    nz = -n.z if inverted else n.z
    if nz >= OVERHANG_NZ:
        return False, "ok"
    bb = face.boundingBox
    z0, z1 = bb.minPoint.z * 10, bb.maxPoint.z * 10
    dx, dy = (bb.maxPoint.x - bb.minPoint.x) * 10, (bb.maxPoint.y - bb.minPoint.y) * 10
    cx, cy = (bb.minPoint.x + bb.maxPoint.x) * 5, (bb.minPoint.y + bb.maxPoint.y) * 5
    bed = v("drum_h") * 10 if inverted else 0.0
    if abs(z0 - bed) < 0.01 and abs(z1 - bed) < 0.01:
        return True, "bed"
    g = face.geometry
    if g.surfaceType == adsk.core.SurfaceTypes.CylinderSurfaceType and adsk.core.Cylinder.cast(g).radius * 10 <= 2.0:
        return True, "small hole"
    if g.surfaceType == adsk.core.SurfaceTypes.CylinderSurfaceType or g.surfaceType == adsk.core.SurfaceTypes.ConeSurfaceType:
        return True, "curved, sampled normal only"
    if inverted and abs(z0 - (v("drum_h") - v("art_pocket_d")) * 10) < 0.01:
        return True, "pocket floor (art fill rule)"
    longest = max(dx, dy, 1e-6)
    thin = face.area * 100 / longest
    if abs(cx) < 1.0 and abs(cy) < 1.0 and dx > 150 and dy > 150:
        thin = face.area * 100 / (PI * (dx + dy) / 2)
    if thin <= LEDGE_MM:
        return True, "ledge <= 1.5 mm"
    if thin <= BRIDGE_MM:
        return True, "bridge <= 20 mm"
    return True, "UNCLASSIFIED"


def audit(ctx):
    bad = []
    for b in ctx.root.bRepBodies:
        inverted = b.name != "base"
        counts = {}
        for f in b.faces:
            flagged, cls = classify(ctx, f, inverted)
            if not flagged:
                continue
            counts[cls] = counts.get(cls, 0) + 1
            if cls == "UNCLASSIFIED":
                bb = f.boundingBox
                bad.append("%s: face area %.2f mm2, x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f" % (
                    b.name, f.area * 100, bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
                    bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
        print("audit %s (%s): %s" % (b.name, "inverted" if inverted else "as modelled",
                                     ", ".join("%s x%d" % kv for kv in sorted(counts.items())) or "no down-facing faces"))
    for line in bad:
        print("UNCLASSIFIED " + line)
    if bad:
        raise RuntimeError("overhang audit: %d unclassified down-facing faces" % len(bad))


# ---------------------------------------------------------------- exports and renders

def export(ctx):
    os.makedirs(EXPORT_DIR, exist_ok=True)
    em = ctx.des.exportManager
    if not em.execute(em.createSTEPExportOptions(EXPORT_DIR + "/pi_drum.step")):
        raise RuntimeError("STEP export returned False")
    if not em.execute(em.createC3MFExportOptions(ctx.root, EXPORT_DIR + "/pi_drum.3mf")):
        raise RuntimeError("3MF export returned False")
    for name in ("pi_drum.step", "pi_drum.3mf"):
        p = os.path.join(EXPORT_DIR, name)
        if not os.path.exists(p) or os.path.getsize(p) < 10000:
            raise RuntimeError("export %s missing or tiny" % name)
        print("export %s: %d bytes" % (name, os.path.getsize(p)))


def render(ctx):
    os.makedirs(RENDER_DIR, exist_ok=True)
    vp = ctx.app.activeViewport
    base, cup = body_named(ctx, "base"), body_named(ctx, "cup")
    inlays = [b for n in ("inlay_logo", "inlay_left", "inlay_right") for b in group(ctx, n)]
    views = (("iso", (30, -30, 25), True, True, True), ("front", (0, -40, 6), True, True, True),
             ("front_recess", (0, -40, 6), True, True, False), ("left_recess", (-40, 0, 6), True, True, False),
             ("top", (0, 0, 40), True, True, True), ("base_above", (0.01, 0, 40), False, True, False),
             ("cup_below", (0.01, 0, -40), True, False, True))
    for name, eye, show_cup, show_base, show_inlays in views:
        cup.isVisible, base.isVisible = show_cup, show_base
        for b in inlays:
            b.isVisible = show_inlays
        cam = vp.camera
        cam.eye = ctx.pt(*eye)
        cam.target = ctx.pt(0, 0, 6 if abs(eye[2]) < 30 else 0)
        cam.upVector = adsk.core.Vector3D.create(0, 0, 1)  # fusionhelper: allow R6 — camera up vector for a render, not geometry
        cam.isFitView = True
        vp.camera = cam
        adsk.doEvents()
        vp.saveAsImageFile(os.path.join(RENDER_DIR, "pi_drum_stageF_%s.png" % name), 1600, 1200)
    cup.isVisible, base.isVisible = True, True
    for b in inlays:
        b.isVisible = True


def run(_context: str):
    app = adsk.core.Application.get()
    if not app.activeDocument.name.startswith(DOC_PREFIX):
        raise RuntimeError("wrong document %r" % app.activeDocument.name)
    ctx = BuildCtx(app)
    ensure_params(ctx)

    reseat_pi(ctx)
    lower_column_feet(ctx)
    adsk.doEvents()
    healthy_or_raise(ctx, "stage F")
    plug_room(ctx)
    read_back(ctx)
    prove_symmetric_params(ctx)
    names = sorted(b.name for b in ctx.root.bRepBodies)
    print("bodies (%d): %s" % (len(names), names))
    audit(ctx)
    for b in ctx.root.bRepBodies:
        print("%s: %.4f cm3, %d faces" % (b.name, b.volume, b.faces.count))
    export(ctx)
    render(ctx)
    print("done")


# fusionhelper: verification stub v1
def _fh_verify_entry():
    import os, json, traceback
    home = os.environ.get('FUSIONHELPER_HOME') or os.path.join(
        os.environ.get('LOCALAPPDATA', ''), 'FusionHelper')

    def _bail(code, msg):
        return 'FH_VERDICT1 ' + json.dumps(
            {'v': 1, 'status': 'error', 'code': code, 'msg': msg, 'home': home},
            separators=(',', ':'))

    try:
        with open(os.path.join(home, 'fh_verify.py'), encoding='utf-8') as f:
            src = f.read()
    except Exception as e:
        return _bail('verify.block_missing', str(e))
    ns: dict = {'__name__': 'fh_verify'}   # annotated: else pyright infers dict[str, str]
    try:
        exec(compile(src, 'fh_verify.py', 'exec'), ns)
        g = globals()
        return ns['fh_verify'](
            clearances=g.get('CLEARANCES'),
            face_specs=g.get('FACE_SPECS'),
            datum_heights_cm=g.get('DATUM_HEIGHTS_CM'),
            digest=g.get('DIGEST'),
            interference_allowed=g.get('INTERFERENCE_ALLOWED'),
            expect_dead=g.get('EXPECT_DEAD'),
            refs=g.get('FH_REFS', {}),
            attempt=g.get('FH_ATTEMPT', 1),
            **g.get('FH_OPTS', {}))
    except Exception:
        return _bail('verify.internal', traceback.format_exc()[-600:])


def _fh_wrap(inner):
    def _wrapped(_context: str):
        inner(_context)                 # NOT wrapped: build exceptions must escape
        print(_fh_verify_entry())
    return _wrapped


run = _fh_wrap(run)
