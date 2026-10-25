"""Pi console drum, D-021. Stage C -- the cup (plan task 5), in the document
that holds stages A and B.

  cup_wall       ring drum_d / 2 cavity_r from split_z up to drum_h - lid_t,
                 new body "cup"
  cup_lid        disc drum_d x lid_t from drum_h down, joined
  btn_holes      six btn_hole holes through the lid at btn_ring_r: Starts at
                 -90 deg -+ 1.5 and 0.5 btn_arc_pitch (P1..P4 left to right
                 across the front), SEL at 160, HK at 20 deg
  art_pocket     pocket_w x pocket_h x art_pocket_d into the lid top, centred
                 (0, art_cy)
  web_n          four ribs web_w wide (tangential) from col_r to cavity_r + 1
                 (into the wall), z split_z..web_z1, joined -- built BEFORE
                 the columns so the columns have something to join to (a
                 join whose tool does not touch its target adds nothing,
                 measured)
  col_n          four col_d columns at col_r on +-20, +-160 deg from web_z1
                 down to col_foot_z, joined into the webs
  col_insert     insert_hole_d x insert_hole_h bores up from the column feet
  vent_groove    a vent_groove_d x (vent_z1 - vent_z0) ring revolved out of
                 the outside at z vent_z0..vent_z1
  vent_slot      one vent_w x vent_h slot through the wall in the groove, then
                 a circular pattern of vent_n
  joint_chamfer  a joint_chamfer right triangle revolved off the base's top
                 outer edge and the cup's bottom outer edge (revolved cuts,
                 not chamfer features: no edge references to go stale)

Every (r, z) rectangle is drawn on a radial plane with the stage B recipe
and asserted in model space before its extrude; the half-size expressions
are parenthesised. Circles use abs() position expressions with the seed on
the signed side and are read back at the SIGNED coordinates.

Oracles: ring, disc, six holes, pocket, webs less their wall overlap,
columns less their web overlap, bores, groove (Pappus), slot and pattern
by face count, chamfers (Pappus). Then containment reads back every hole
at its signed centre, the pocket floor and corners, the webs at r 77.2,
the columns at their feet, the 0.2 gap to the base wall, the vents, and
the interference check between cup and base runs in the verify block.
"""
FH_ATTEMPT = 1
FH_OPTS = {
    "only_params": ["drum_h", "lid_t", "btn_hole", "btn_ring_r", "btn_arc_pitch",
                    "art_w", "art_h", "art_margin", "art_pocket_d", "art_cy",
                    "col_d", "col_foot_z", "web_w", "web_z1", "insert_hole_d", "insert_hole_h",
                    "vent_z0", "vent_z1", "vent_groove_d", "vent_n", "vent_w", "vent_h",
                    "joint_chamfer"],
    "liveness_budget_s": 900,
    "max_bodies": 2,
    "force_liveness": True,
}
INTERFERENCE_ALLOWED = []
CLEARANCES = []
# btn_ring_r moves six holes with no volume, area or face-count change;
# opted out of the signature probe and proven live in-script (prove_ring_radius).
EXPECT_DEAD = ["btn_ring_r"]
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
RENDER_DIR = r"C:/Users/gethi/sources/arcade-cabinet/.claude/worktrees/pi-drum/cad/renders"
PI = math.pi
MM = 0.1
TOL_MM = 0.05

NEEDED = ("drum_d", "drum_r", "wall_t", "cavity_r", "floor_t", "split_z", "col_r")
PARAMS = (
    ("drum_h",        "115 mm", "mm", "overall height, floor underside to lid top"),
    ("lid_t",         "5 mm",   "mm", "cup lid"),
    ("btn_hole",      "30.5 mm", "mm", "30 mm screw-in button hole, as the pad"),
    ("btn_ring_r",    "57 mm",  "mm", "button centre radius"),
    ("btn_arc_pitch", "41 deg", "deg", "Start-to-Start angle; chord 2 * 57 * sin(20.5 deg) = 39.9"),
    ("btn_ang_p1",    "-90 deg - 1.5 * btn_arc_pitch", "deg", "derived: P1, player's left"),
    ("btn_ang_p2",    "-90 deg - 0.5 * btn_arc_pitch", "deg", "derived"),
    ("btn_ang_p3",    "-90 deg + 0.5 * btn_arc_pitch", "deg", "derived"),
    ("btn_ang_p4",    "-90 deg + 1.5 * btn_arc_pitch", "deg", "derived: P4, player's right"),
    ("btn_ang_sel",   "160 deg", "deg", "Select, rear left"),
    ("btn_ang_hk",    "20 deg",  "deg", "Hotkey, rear right"),
    ("art_w",         "45.7 mm", "mm", "the pad's Chun-Li width (cad/lap_disc_g.py)"),
    ("art_h",         "64 mm",   "mm", "art height"),
    ("art_margin",    "2.2 mm",  "mm", "pocket margin round the art"),
    ("art_pocket_d",  "0.6 mm",  "mm", "three 0.2 layers"),
    ("art_cy",        "20 mm",   "mm", "pocket centre on the y axis, behind the middle"),
    ("pocket_w",      "art_w + 2 * art_margin", "mm", "derived"),
    ("pocket_h",      "art_h + 2 * art_margin", "mm", "derived"),
    ("col_d",         "8 mm",   "mm", "column diameter"),
    ("col_foot_z",    "6 mm",   "mm", "column foot, on the base floor's top face"),
    ("web_w",         "8 mm",   "mm", "web width, tangential"),
    ("web_z1",        "40 mm",  "mm", "web and column top"),
    ("insert_hole_d", "4 mm",   "mm", "M3 heat-set bore, as the pad (D-016)"),
    ("insert_hole_h", "4.2 mm", "mm", "bore depth"),
    ("vent_z0",       "101 mm", "mm", "exhaust groove bottom"),
    ("vent_z1",       "105 mm", "mm", "exhaust groove top"),
    ("vent_groove_d", "1.2 mm", "mm", "groove depth into the outside"),
    ("vent_n",        "16",     "",   "exhaust slots"),
    ("vent_w",        "8 mm",   "mm", "slot width, tangential"),
    ("vent_h",        "2.5 mm", "mm", "slot height"),
    ("joint_chamfer", "0.8 mm", "mm", "45 deg on both outer edges at the parting line"),
)
BUTTONS = (("p1", "btn_ang_p1", -151.5), ("p2", "btn_ang_p2", -110.5), ("p3", "btn_ang_p3", -69.5),
           ("p4", "btn_ang_p4", -28.5), ("sel", "btn_ang_sel", 160.0), ("hk", "btn_ang_hk", 20.0))
COL_ANGLES = (("1", "20 deg", 20.0), ("2", "160 deg", 160.0), ("3", "-160 deg", -160.0), ("4", "-20 deg", -20.0))


# ---------------------------------------------------------------- helpers (as stages A and B)

def ensure_params(ctx):
    for name in NEEDED:
        if ctx.up.itemByName(name) is None:
            raise RuntimeError("parameter %s missing: run stages A and B first" % name)
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


def inside(body, x_mm, y_mm, z_mm):
    return body.pointContainment(adsk.core.Point3D.create(x_mm * MM, y_mm * MM, z_mm * MM)) \
        == adsk.fusion.PointContainment.PointInsidePointContainment


def probe(body, pts, want_inside, label):
    for (x, y, z) in pts:
        if inside(body, x, y, z) != want_inside:
            raise RuntimeError("%s: (%.1f, %.1f, %.1f) should be %s" % (
                label, x, y, z, "solid" if want_inside else "empty"))
    print("%s: %d probes %s" % (label, len(pts), "solid" if want_inside else "empty"))


def centred_circle(ctx, sk, r_seed_cm, dia_expr, jitter):
    c = sk.sketchCurves.sketchCircles.addByCenterRadius(
        ctx.pt(0.011 + 0.003 * jitter, 0.017 + 0.005 * jitter, 0), r_seed_cm)
    sk.geometricConstraints.addCoincident(c.centerSketchPoint, sk.originPoint)
    d = sk.sketchDimensions.addDiameterDimension(c, ctx.pt(r_seed_cm + 0.4, -0.4, 0))
    d.parameter.expression = dia_expr
    return c


def polar_circle(ctx, sk, r_cm, theta_deg, z_cm, r_seed_cm, dia_expr, r_expr, ang_expr):
    """A bound circle at (r_expr, ang_expr) polar on a horizontal sketch at
    z_cm; abs() position expressions, seed on the signed side."""
    t = math.radians(theta_deg)
    w = (r_cm * math.cos(t), r_cm * math.sin(t), z_cm)
    return ctx.bound_circle(sk, w, r_seed_cm, dia_expr,
                            x_pos="abs( %s * cos( %s ) )" % (r_expr, ang_expr),
                            v_pos="abs( %s * sin( %s ) )" % (r_expr, ang_expr))


def assert_circle_xy(sk, circle, x_want, y_want, label):
    m = sk.sketchToModelSpace(circle.centerSketchPoint.geometry)
    if abs(m.x * 10 - x_want) > TOL_MM or abs(m.y * 10 - y_want) > TOL_MM:
        raise RuntimeError("%s: circle landed (%.2f, %.2f), wanted (%.2f, %.2f)" % (
            label, m.x * 10, m.y * 10, x_want, y_want))


def profile_by_area(sk, want_cm2, tol=0.05):
    for p in sk.profiles:
        if abs(p.areaProperties().area - want_cm2) < tol * want_cm2:
            return p
    raise RuntimeError("no profile of area %.3f cm2 in %s" % (want_cm2, sk.name))


def radial_plane_checked(ctx, ang_expr, name, theta):
    pt = ctx.pt(10 * math.cos(theta), 10 * math.sin(theta), 1.0)
    for e in (ang_expr, "-(%s)" % ang_expr):
        pin = ctx.planes.createInput()
        pin.setByAngle(ctx.root.zConstructionAxis, ctx.cbs(e), ctx.root.xZConstructionPlane)
        pl = ctx.planes.add(pin)
        pl.name = name
        sk = ctx.root.sketches.add(pl)
        off = abs(sk.modelToSketchSpace(pt).z)
        sk.deleteMe()
        if off < 0.01:
            return pl
        pl.deleteMe()
        adsk.doEvents()
    raise RuntimeError("radial plane %s never contained the probe point" % name)


def radial_rect(ctx, sk, theta, r_c, z_c, r_half, z_half, r_size, r_pos, z_size, z_pos):
    """(r, z) rectangle on a radial plane; half-size expressions parenthesised."""
    ctx.U = (math.cos(theta), math.sin(theta), 0.0)
    ctx.V = (0.0, 0.0, 1.0)
    try:
        ctx.bound_rect2(sk, (r_c * math.cos(theta), r_c * math.sin(theta), z_c), r_half, z_half,
                        u_size=r_size, v_size=z_size,
                        u_pos=(r_pos, "( %s ) / 2" % r_size), v_pos=(z_pos, "( %s ) / 2" % z_size))
    finally:
        ctx.U = (1.0, 0.0, 0.0)
        ctx.V = (0.0, 1.0, 0.0)


def assert_rect_landed(sk, theta, r_lo, r_hi, z_lo, z_hi, label):
    n = (math.cos(theta), math.sin(theta))
    rs, zs = [], []
    for i in range(sk.sketchCurves.sketchLines.count):
        ln = sk.sketchCurves.sketchLines.item(i)
        for p in (ln.startSketchPoint.geometry, ln.endSketchPoint.geometry):
            m = sk.sketchToModelSpace(p)
            rs.append((m.x * n[0] + m.y * n[1]) * 10)
            zs.append(m.z * 10)
    got = (min(rs), max(rs), min(zs), max(zs))
    want = (r_lo, r_hi, z_lo, z_hi)
    if any(abs(g - w) > TOL_MM for g, w in zip(got, want)):
        raise RuntimeError("%s: rectangle landed r %.2f..%.2f z %.2f..%.2f, wanted r %.2f..%.2f z %.2f..%.2f"
                           % ((label,) + got + want))
    print("%s: rectangle at r %.2f..%.2f z %.2f..%.2f" % ((label,) + got))


def sym_cut_checked(ctx, sk, width_expr, body, want, label, min_vol=0.01, tol_rel=0.02):
    v0 = body.volume
    f = ctx.sym_cut(ctx.all_profiles(sk), width_expr, [body], min_vol_cm3=min_vol)
    f.name = label
    check_delta(label, v0, body.volume, -want, tol_rel=tol_rel)
    return f


def sym_join_checked(ctx, sk, width_expr, body, want, label, tol_rel=0.03):
    v0 = body.volume
    inp = ctx.extrudes.createInput(ctx.all_profiles(sk), ctx.ops.JoinFeatureOperation)
    inp.setSymmetricExtent(ctx.cbs(width_expr), True)
    inp.participantBodies = [body]
    f = ctx.extrudes.add(inp)
    f.name = label
    check_delta(label, v0, body.volume, want, tol_rel=tol_rel)
    return f


def revolve_cut_checked(ctx, sk, body, want, label, tol_rel=0.02):
    v0 = body.volume
    rev = ctx.root.features.revolveFeatures
    inp = rev.createInput(ctx.all_profiles(sk), ctx.root.zConstructionAxis, ctx.ops.CutFeatureOperation)
    inp.setAngleExtent(False, ctx.cbs("360 deg"))
    inp.participantBodies = [body]
    f = rev.add(inp)
    f.name = label
    check_delta(label, v0, body.volume, -want, tol_rel=tol_rel)
    return f


def circular_pattern_cut(ctx, feat, n_expr, watch, min_new_faces, name):
    healthy = (adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,
               adsk.fusion.FeatureHealthStates.WarningFeatureHealthState)
    popts = adsk.fusion.PatternComputeOptions
    cp = ctx.root.features.circularPatternFeatures
    coll = adsk.core.ObjectCollection.create()
    coll.add(feat)
    before = ctx.faces_of(watch)
    reasons = []
    for mode in (popts.AdjustPatternCompute, popts.IdenticalPatternCompute):
        adsk.doEvents()
        inp = cp.createInput(coll, ctx.root.zConstructionAxis)
        inp.quantity = ctx.cbs(n_expr)
        inp.totalAngle = ctx.cbs("360 deg")
        inp.isSymmetric = False
        inp.patternComputeOption = mode  # pyright: ignore[reportAttributeAccessIssue]
        f = cp.add(inp)
        if f.healthState in healthy and ctx.faces_of(watch) - before >= min_new_faces:
            f.name = name
            return f
        reasons.append("%s hs=%s faces+%d" % (mode, f.healthState, ctx.faces_of(watch) - before))
        f.deleteMe()
    raise RuntimeError("circular pattern %s never validated: %s" % (name, " | ".join(reasons)))


# ---------------------------------------------------------------- build

def build_wall_and_lid(ctx):
    v = ctx.val
    split = None
    for i in range(ctx.planes.count):
        if ctx.planes.item(i).name == "split":
            split = ctx.planes.item(i)
    if split is None:
        split = ctx.plane_at_z("split_z", "split")
    sk = ctx.root.sketches.add(split)
    sk.name = "cup_wall_sk"
    centred_circle(ctx, sk, v("drum_r"), "drum_d", 1)
    centred_circle(ctx, sk, v("cavity_r"), "2 * cavity_r", 2)
    ring = profile_by_area(sk, PI * (v("drum_r") ** 2 - v("cavity_r") ** 2))
    coll = adsk.core.ObjectCollection.create()
    coll.add(ring)
    wall_h = v("drum_h") - v("lid_t") - v("split_z")
    want = PI * (v("drum_r") ** 2 - v("cavity_r") ** 2) * wall_h
    f, cup = ctx.checked_newbody(coll, "drum_h - lid_t - split_z",
                                 lambda b: abs(b.volume - want) < 0.01 * want and b.boundingBox.maxPoint.z > v("split_z") + 1,
                                 "cup_wall")
    f.name = "cup_wall"
    cup.name = "cup"
    print("cup_wall: %.4f cm3 (want %.4f)" % (cup.volume, want))

    lid_top = ctx.plane_at_z("drum_h", "lid_top")
    sk = ctx.root.sketches.add(lid_top)
    sk.name = "cup_lid_sk"
    centred_circle(ctx, sk, v("drum_r"), "drum_d", 3)
    v0 = cup.volume
    want = PI * v("drum_r") ** 2 * v("lid_t")
    f = ctx.checked_join(ctx.all_profiles(sk), "lid_t", cup,
                         lambda b: abs(b.volume - v0 - want) < 0.01 * want, "cup_lid")
    f.name = "cup_lid"
    check_delta("cup_lid", v0, cup.volume, want)
    return cup, lid_top


def cut_buttons(ctx, cup, lid_top):
    v = ctx.val
    sk = ctx.root.sketches.add(lid_top)
    sk.name = "btn_holes_sk"
    r = v("btn_ring_r")
    for name, ang_param, theta in BUTTONS:
        c = polar_circle(ctx, sk, r, theta, v("drum_h"), v("btn_hole") / 2, "btn_hole", "btn_ring_r", ang_param)
        assert_circle_xy(sk, c, r * 10 * math.cos(math.radians(theta)), r * 10 * math.sin(math.radians(theta)),
                         "btn_holes %s" % name)
        adsk.doEvents()
    v0 = cup.volume
    faces0 = cup.faces.count
    f = ctx.through_cut(ctx.all_profiles(sk), "lid_t * 2 + 2 mm", [cup])
    f.name = "btn_holes"
    check_delta("btn_holes", v0, cup.volume, -6 * PI * (v("btn_hole") / 2) ** 2 * v("lid_t"))
    if cup.faces.count - faces0 < 6:
        raise RuntimeError("btn_holes: only %d new faces" % (cup.faces.count - faces0))


def cut_art_pocket(ctx, cup, lid_top):
    v = ctx.val
    sk = ctx.root.sketches.add(lid_top)
    sk.name = "art_pocket_sk"
    ctx.bound_rect2(sk, (0.0, v("art_cy"), v("drum_h")), v("pocket_w") / 2, v("pocket_h") / 2,
                    u_size="pocket_w", v_size="pocket_h",
                    u_pos=("0 mm", "pocket_w / 2"), v_pos=("art_cy", "pocket_h / 2"))
    # assert in model space: x symmetric about 0, y about art_cy
    xs, ys = [], []
    for i in range(sk.sketchCurves.sketchLines.count):
        ln = sk.sketchCurves.sketchLines.item(i)
        for p in (ln.startSketchPoint.geometry, ln.endSketchPoint.geometry):
            m = sk.sketchToModelSpace(p)
            xs.append(m.x * 10)
            ys.append(m.y * 10)
    got = (min(xs), max(xs), min(ys), max(ys))
    want = (-v("pocket_w") * 5, v("pocket_w") * 5, (v("art_cy") - v("pocket_h") / 2) * 10, (v("art_cy") + v("pocket_h") / 2) * 10)
    if any(abs(g - w) > TOL_MM for g, w in zip(got, want)):
        raise RuntimeError("art_pocket: rectangle landed x %.2f..%.2f y %.2f..%.2f, wanted x %.2f..%.2f y %.2f..%.2f" % (got + want))
    print("art_pocket: rectangle at x %.2f..%.2f y %.2f..%.2f" % got)
    v0 = cup.volume
    f = ctx.blind_cut(ctx.all_profiles(sk), "art_pocket_d", [cup], "pocket", min_vol_cm3=0.5)
    f.name = "art_pocket"
    check_delta("art_pocket", v0, cup.volume, -v("pocket_w") * v("pocket_h") * v("art_pocket_d"))


def web_overlap_with_wall(ctx, half_w):
    """Area (cm2, in plan) of a web rectangle from col_r to cavity_r + 1 mm
    that lies inside the wall (r >= cavity_r), integrated across its width."""
    v = ctx.val
    ri, r_hi = v("cavity_r"), v("cavity_r") + 0.1
    n = 200
    a = 0.0
    for i in range(n):
        u = -half_w + (i + 0.5) * (2 * half_w / n)
        r_in = math.sqrt(ri * ri - u * u)
        a += max(0.0, r_hi - r_in) * (2 * half_w / n)
    return a


def build_webs_and_columns(ctx, cup):
    v = ctx.val
    col_r, cav = v("col_r"), v("cavity_r")
    web_h = v("web_z1") - v("split_z")
    r_hi = cav + 0.1
    for n, ang_expr, theta_deg in COL_ANGLES:
        th = math.radians(theta_deg)
        plane = radial_plane_checked(ctx, ang_expr, "web_%s_plane" % n, th)
        sk = ctx.root.sketches.add(plane)
        sk.name = "web_%s_sk" % n
        zc = (v("split_z") + v("web_z1")) / 2
        radial_rect(ctx, sk, th, (col_r + r_hi) / 2, zc, (r_hi - col_r) / 2, web_h / 2,
                    "cavity_r + 1 mm - col_r", "( col_r + cavity_r + 1 mm ) / 2",
                    "web_z1 - split_z", "( split_z + web_z1 ) / 2")
        assert_rect_landed(sk, th, col_r * 10, r_hi * 10, v("split_z") * 10, v("web_z1") * 10, "web_%s" % n)
        want = (v("web_w") * (r_hi - col_r) - web_overlap_with_wall(ctx, v("web_w") / 2)) * web_h
        sym_join_checked(ctx, sk, "web_w", cup, want, "web_%s" % n)
        cup = body_named(ctx, "cup")
        adsk.doEvents()

    top = ctx.plane_at_z("web_z1", "web_top")
    sk = ctx.root.sketches.add(top)
    sk.name = "col_sk"
    for n, ang_expr, theta_deg in COL_ANGLES:
        c = polar_circle(ctx, sk, col_r, theta_deg, v("web_z1"), v("col_d") / 2, "col_d", "col_r", ang_expr)
        assert_circle_xy(sk, c, col_r * 10 * math.cos(math.radians(theta_deg)),
                         col_r * 10 * math.sin(math.radians(theta_deg)), "col_%s" % n)
        adsk.doEvents()
    col_h = v("web_z1") - v("col_foot_z")
    r_col = v("col_d") / 2
    # overlap of a column with its web over the web's height: the web spans
    # r col_r..cavity_r + 1 within |u| <= web_w / 2 >= r_col, so the overlap
    # is the half-disc beyond r = col_r, over web_h
    overlap = 4 * (PI * r_col ** 2 / 2) * web_h
    want = 4 * PI * r_col ** 2 * col_h - overlap
    v0 = cup.volume
    f = ctx.checked_join(ctx.all_profiles(sk), "web_z1 - col_foot_z", cup,
                         lambda b: abs(b.volume - v0 - want) < 0.02 * want, "col")
    f.name = "col"
    check_delta("col", v0, cup.volume, want)
    if ctx.root.bRepBodies.count != 2:
        raise RuntimeError("after the columns, %d bodies (a column failed to join)" % ctx.root.bRepBodies.count)

    foot = ctx.plane_at_z("col_foot_z", "col_foot")
    sk = ctx.root.sketches.add(foot)
    sk.name = "col_insert_sk"
    for n, ang_expr, theta_deg in COL_ANGLES:
        polar_circle(ctx, sk, col_r, theta_deg, v("col_foot_z"), v("insert_hole_d") / 2, "insert_hole_d", "col_r", ang_expr)
        adsk.doEvents()
    v0 = cup.volume
    f = ctx.blind_cut(ctx.all_profiles(sk), "insert_hole_h", [cup], "insert", min_vol_cm3=0.01)
    f.name = "col_insert"
    check_delta("col_insert", v0, cup.volume, -4 * PI * (v("insert_hole_d") / 2) ** 2 * v("insert_hole_h"))
    return body_named(ctx, "cup")


def cut_vents(ctx, cup):
    v = ctx.val
    plane = radial_plane_checked(ctx, "0 deg", "vent_plane", 0.0)
    # groove: (r, z) rect from drum_r - vent_groove_d to drum_r, vent_z0..vent_z1, revolved
    sk = ctx.root.sketches.add(plane)
    sk.name = "vent_groove_sk"
    dr, gd = v("drum_r"), v("vent_groove_d")
    zc = (v("vent_z0") + v("vent_z1")) / 2
    gh = v("vent_z1") - v("vent_z0")
    radial_rect(ctx, sk, 0.0, dr - gd / 2, zc, gd / 2, gh / 2,
                "vent_groove_d", "drum_r - vent_groove_d / 2", "vent_z1 - vent_z0", "( vent_z0 + vent_z1 ) / 2")
    assert_rect_landed(sk, 0.0, (dr - gd) * 10, dr * 10, v("vent_z0") * 10, v("vent_z1") * 10, "vent_groove")
    want = PI * (dr ** 2 - (dr - gd) ** 2) * gh
    revolve_cut_checked(ctx, sk, cup, want, "vent_groove")

    # slot: (r, z) rect from cavity_r - 1 to drum_r + 1, vent_h tall, symmetric vent_w, then pattern
    sk = ctx.root.sketches.add(plane)
    sk.name = "vent_slot_sk"
    r_lo, r_hi = v("cavity_r") - 0.1, dr + 0.1
    radial_rect(ctx, sk, 0.0, (r_lo + r_hi) / 2, zc, (r_hi - r_lo) / 2, v("vent_h") / 2,
                "drum_r + 2 mm - cavity_r", "( cavity_r + drum_r ) / 2", "vent_h", "( vent_z0 + vent_z1 ) / 2")
    assert_rect_landed(sk, 0.0, r_lo * 10, r_hi * 10, (zc - v("vent_h") / 2) * 10, (zc + v("vent_h") / 2) * 10, "vent_slot")
    want = v("vent_w") * v("vent_h") * (v("wall_t") - gd)     # through the wall left under the groove
    f = sym_cut_checked(ctx, sk, "vent_w", cup, want, "vent_slot", min_vol=0.005, tol_rel=0.05)
    n = int(round(v("vent_n")))
    v0 = cup.volume
    circular_pattern_cut(ctx, f, "vent_n", [cup], 3 * (n - 1), "vent_slot_pattern")
    check_delta("vent_slot_pattern", v0, cup.volume, -want * (n - 1), tol_rel=0.05)


def cut_joint_chamfers(ctx, cup, base):
    """Revolved right triangles off the two outer edges at split_z."""
    v = ctx.val
    c, dr, sz = v("joint_chamfer"), v("drum_r"), v("split_z")
    plane = radial_plane_checked(ctx, "0 deg", "chamfer_plane", 0.0)
    for body, name, up in ((base, "joint_chamfer_base", -1), (cup, "joint_chamfer_cup", 1)):
        sk = ctx.root.sketches.add(plane)
        sk.name = name + "_sk"
        # triangle: corner at (drum_r, split_z), legs joint_chamfer inward and up/down
        corner = sk.modelToSketchSpace(ctx.pt(dr, 0, sz))
        p_in = sk.modelToSketchSpace(ctx.pt(dr - c, 0, sz))
        p_z = sk.modelToSketchSpace(ctx.pt(dr, 0, sz + up * c))
        lines = sk.sketchCurves.sketchLines
        l1 = lines.addByTwoPoints(corner, p_in)
        l2 = lines.addByTwoPoints(l1.endSketchPoint, p_z)
        l3 = lines.addByTwoPoints(l2.endSketchPoint, l1.startSketchPoint)
        gc = sk.geometricConstraints
        # pin the corner to the rim: the two legs are bound by dimensions; the
        # corner point sits on the wall's outer edge by its distances from the origin
        anchor = ctx.pt(corner.x + 0.5, corner.y + 0.5, 0)
        d = sk.sketchDimensions.addDistanceDimension(l1.startSketchPoint, l1.endSketchPoint,
                                                     ctx.dims_or.AlignedDimensionOrientation, anchor)
        d.parameter.expression = "joint_chamfer"
        d = sk.sketchDimensions.addDistanceDimension(l2.startSketchPoint, l2.endSketchPoint,
                                                     ctx.dims_or.AlignedDimensionOrientation, anchor)
        d.parameter.expression = "joint_chamfer"
        gc.addPerpendicular(l1, l2)
        o = sk.sketchToModelSpace(ctx.pt(0, 0, 0))
        ex = sk.sketchToModelSpace(ctx.pt(1, 0, 0))
        # which sketch axis is radial? dimension the corner from the origin along both
        if abs(ex.x - o.x) > abs(ex.z - o.z):
            h_expr, v_expr = "drum_r", "split_z"
        else:
            h_expr, v_expr = "split_z", "drum_r"
        d = sk.sketchDimensions.addDistanceDimension(sk.originPoint, l1.startSketchPoint,
                                                     ctx.dims_or.HorizontalDimensionOrientation, anchor)
        d.parameter.expression = h_expr
        d = sk.sketchDimensions.addDistanceDimension(sk.originPoint, l1.startSketchPoint,
                                                     ctx.dims_or.VerticalDimensionOrientation, anchor)
        d.parameter.expression = v_expr
        # the inward leg is horizontal (radial) in model space
        gc.addHorizontal(l1) if abs(ex.x - o.x) > abs(ex.z - o.z) else gc.addVertical(l1)
        # assert the triangle in model space
        pts = [sk.sketchToModelSpace(p.geometry) for p in (l1.startSketchPoint, l1.endSketchPoint, l2.endSketchPoint)]
        rs = sorted(p.x * 10 for p in pts)
        zs = sorted(p.z * 10 for p in pts)
        if abs(rs[-1] - dr * 10) > TOL_MM or abs(rs[0] - (dr - c) * 10) > TOL_MM or \
                abs(min(zs) - min(sz, sz + up * c) * 10) > TOL_MM or abs(max(zs) - max(sz, sz + up * c) * 10) > TOL_MM:
            raise RuntimeError("%s: triangle landed r %.2f..%.2f z %.2f..%.2f" % (name, rs[0], rs[-1], zs[0], zs[-1]))
        want = (c * c / 2) * 2 * PI * (dr - c / 3)
        revolve_cut_checked(ctx, sk, body, want, name)
        adsk.doEvents()


# ---------------------------------------------------------------- read-back

def read_back(ctx, cup, base):
    v = ctx.val
    mm = lambda cm: cm * 10  # noqa: E731
    zl = mm(v("drum_h")) - mm(v("lid_t")) / 2
    r = mm(v("btn_ring_r"))
    centres = [(r * math.cos(math.radians(t)), r * math.sin(math.radians(t)), zl) for _, _, t in BUTTONS]
    probe(cup, centres, False, "button holes at their signed centres")
    probe(cup, [(x + 16, y, z) for x, y, z in centres], True, "lid beside each hole")
    # the layout is dense (a mirrored Start lands in SEL or HK), so the sign
    # check is the midpoints between neighbours and the lid centre
    mids = [((centres[i][0] + centres[j][0]) / 2, (centres[i][1] + centres[j][1]) / 2, zl)
            for i, j in ((0, 1), (1, 2), (2, 3), (0, 4), (3, 5))]
    probe(cup, mids + [(0, 0, zl)], True, "lid between neighbouring holes and at the centre")
    # pocket: floor face at drum_h - art_pocket_d, corners solid below and empty above
    pw, ph, cy = mm(v("pocket_w")), mm(v("pocket_h")), mm(v("art_cy"))
    top = mm(v("drum_h"))
    corners = [(sx * (pw / 2 - 0.3), cy + sy * (ph / 2 - 0.3)) for sx in (-1, 1) for sy in (-1, 1)]
    probe(cup, [(x, y, top - 0.2) for x, y in corners], False, "pocket corners at z top-0.2")
    probe(cup, [(x, y, top - mm(v("art_pocket_d")) - 0.2) for x, y in corners], True, "under the pocket floor")
    probe(cup, [(0, cy - ph / 2 - 1, top - 0.2)], True, "lid just outside the pocket")
    floor_faces = [f for f in cup.faces
                   if f.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType
                   and abs(f.boundingBox.minPoint.z * 10 - (top - mm(v("art_pocket_d")))) < 0.01
                   and abs(f.boundingBox.maxPoint.z * 10 - (top - mm(v("art_pocket_d")))) < 0.01]
    if len(floor_faces) != 1 or abs(floor_faces[0].area - v("pocket_w") * v("pocket_h")) > 0.01 * v("pocket_w") * v("pocket_h"):
        raise RuntimeError("pocket floor: %d faces, areas %s" % (len(floor_faces), [f.area for f in floor_faces]))
    print("pocket floor: one planar face, %.3f cm2" % floor_faces[0].area)
    # webs, columns, gap
    cr = mm(v("col_r"))
    for n, _, t in COL_ANGLES:
        th = math.radians(t)
        ax = (math.cos(th), math.sin(th))
        probe(cup, [(77.2 * ax[0], 77.2 * ax[1], 36)], True, "web %s in the wall at r 77.2" % n)
        probe(cup, [(cr * ax[0], cr * ax[1], 20)], True, "column %s at z 20" % n)
        probe(cup, [(cr * ax[0], cr * ax[1], mm(v("col_foot_z")) + 1)], False, "column %s insert bore" % n)
        probe(cup, [(76.7 * ax[0], 76.7 * ax[1], 20)], True, "column %s outer skin at r 76.7" % n)
        probe(cup, [(76.9 * ax[0], 76.9 * ax[1], 20)], False, "gap at r 76.9 (cup)")
        probe(base, [(76.9 * ax[0], 76.9 * ax[1], 20)], False, "gap at r 76.9 (base)")
        probe(base, [(77.1 * ax[0], 77.1 * ax[1], 20)], True, "base wall at r 77.1")
    # vents
    zc = (mm(v("vent_z0")) + mm(v("vent_z1"))) / 2
    n = int(round(v("vent_n")))
    probe(cup, [(78.5 * math.cos(2 * PI * i / n), 78.5 * math.sin(2 * PI * i / n), zc) for i in range(n)], False,
          "vent slots through the wall")
    probe(cup, [(78.5 * math.cos(2 * PI * (i + 0.5) / n), 78.5 * math.sin(2 * PI * (i + 0.5) / n), zc) for i in range(n)],
          True, "wall between the slots")
    a = 2 * PI * 0.5 / n          # half a slot pitch: in the groove, between slots
    probe(cup, [(79.5 * math.cos(a), 79.5 * math.sin(a), zc)], False, "groove at r 79.5 between slots")
    probe(cup, [(79.5 * math.cos(a), 79.5 * math.sin(a), zc + 3.5), (79.5 * math.cos(a), 79.5 * math.sin(a), zc - 3.5)],
          True, "wall above and below the groove at r 79.5")


def prove_live(ctx, name, stepped_expr, point_mm, restore_expr, solid_before):
    """Step a parameter the signature probe may not see, check that a point
    flips containment, restore. Body re-resolved by name after each write (R5)."""
    cup = body_named(ctx, "cup")
    if inside(cup, *point_mm) != solid_before:
        raise RuntimeError("prove_live %s: probe point should start %s" % (name, "solid" if solid_before else "empty"))
    ctx.up.itemByName(name).expression = stepped_expr  # fusionhelper: allow R5 — body re-resolved by name after the write
    adsk.doEvents()
    cup = body_named(ctx, "cup")
    flipped = inside(cup, *point_mm) != solid_before
    ctx.up.itemByName(name).expression = restore_expr  # fusionhelper: allow R5 — body re-resolved by name after the write
    adsk.doEvents()
    if not flipped:
        raise RuntimeError("prove_live %s: geometry did not move when stepped to %s" % (name, stepped_expr))
    healthy_or_raise(ctx, "prove_live " + name)
    print("prove_live %s: stepped to %s, geometry moved, restored to %s" % (name, stepped_expr, restore_expr))


def prove_ring_radius(ctx):
    """btn_ring_r moves six holes with no volume change: step it +4 mm and
    watch a point just outside P2's rim fall inside the moved hole."""
    v = ctx.val
    r_edge = (v("btn_ring_r") + v("btn_hole") / 2) * 10 + 1.0
    th = math.radians(-110.5)
    zl = (v("drum_h") - v("lid_t") / 2) * 10
    prove_live(ctx, "btn_ring_r", "61 mm", (r_edge * math.cos(th), r_edge * math.sin(th), zl), "57 mm", True)


def render(ctx, tag, cup, base):
    os.makedirs(RENDER_DIR, exist_ok=True)
    vp = ctx.app.activeViewport
    views = (("iso", adsk.core.ViewOrientations.IsoTopRightViewOrientation, True, True),
             ("top", adsk.core.ViewOrientations.TopViewOrientation, True, True),
             ("under", adsk.core.ViewOrientations.BottomViewOrientation, True, False))
    for name, orient, show_cup, show_base in views:
        cup.isVisible, base.isVisible = show_cup, show_base
        cam = vp.camera
        cam.viewOrientation = orient
        cam.isFitView = True
        vp.camera = cam
        adsk.doEvents()
        vp.saveAsImageFile(os.path.join(RENDER_DIR, "pi_drum_stage%s_%s.png" % (tag, name)), 1600, 1200)
    cup.isVisible, base.isVisible = True, True


def run(_context: str):
    app = adsk.core.Application.get()
    if not app.activeDocument.name.startswith(DOC_PREFIX):
        raise RuntimeError("wrong document %r" % app.activeDocument.name)
    ctx = BuildCtx(app)
    ensure_params(ctx)
    base = body_named(ctx, "base")

    cup, lid_top = build_wall_and_lid(ctx)
    cut_buttons(ctx, cup, lid_top)
    cut_art_pocket(ctx, cup, lid_top)
    cup = build_webs_and_columns(ctx, cup)
    cut_vents(ctx, cup)
    cup, base = body_named(ctx, "cup"), body_named(ctx, "base")
    cut_joint_chamfers(ctx, cup, base)
    adsk.doEvents()

    healthy_or_raise(ctx, "stage C")
    cup, base = body_named(ctx, "cup"), body_named(ctx, "base")
    read_back(ctx, cup, base)
    prove_ring_radius(ctx)
    cup, base = body_named(ctx, "cup"), body_named(ctx, "base")
    if ctx.root.bRepBodies.count != 2:
        raise RuntimeError("expected 2 bodies, found %d" % ctx.root.bRepBodies.count)
    for b in (base, cup):
        bb = b.boundingBox
        print("%s: %.1f x %.1f x %.1f mm, z %.1f..%.1f, %.4f cm3, %d faces" % (
            b.name, (bb.maxPoint.x - bb.minPoint.x) * 10, (bb.maxPoint.y - bb.minPoint.y) * 10,
            (bb.maxPoint.z - bb.minPoint.z) * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10, b.volume, b.faces.count))
    render(ctx, "C", cup, base)
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
