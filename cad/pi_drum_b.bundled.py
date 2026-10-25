"""Pi console drum, D-021. Stage B -- four socket pads on the back half of
the base (plan task 4), in the document that holds stage A.

Each pad, at pad_ang_n from +x toward +y (the back is 90 deg):
  pad_n_flat    the wall cut flat at pad_r = sqrt(drum_r^2 - (pad_w/2)^2),
                a vertical flat pad_w wide from pad_z0 to pad_z1 -- the chord
                plane, so the sagitta is 1.42 at drum_r 80 / pad_w 30
  pad_n_back    a (pad_w + 4) x (pad_z1 - pad_z0 + 2) block joined inward
                pad_back_t from the chord plane, so the flange screws have
                a 5 mm flat-to-flat wall to bite
  pad_n_cut     the socket cutout <name>_cut_w x <name>_cut_h through the pad
  pad_n_pilot   two pilot_d x pilot_h pilots at +-<name>_screw_pitch / 2

Pads in angle order: RJ45 at 45, USB-C at 75, HDMI at 105, USB-A pair at
135 deg. The socket sizes are PLACEHOLDERS until the parts are measured
(OI-013); every one is a parameter.

How the flat, block and cutout are drawn (attempt 3, 2026-10-22): as
(r, z) rectangles on a RADIAL plane through the z axis at pad_ang_n
(sign probed, stage O's radial_plane_checked), extruded symmetrically
about that plane by the feature's width. The slab {r.n >= pad_r} x {|u| <=
pad_w/2} is exactly the chord region. Attempts 1-3 landed the rectangles
3 mm high in z (and, on the radial plane, at half the radius): the cause
was this script halving a compound size expression without parentheses
("pad_z1 - pad_z0 / 2"), not the kit. Every sketch's lines are mapped back
to model space and asserted against the intended r and z ranges BEFORE
the extrude, which is what pinned it down. The pilots are circles on the chord
plane (tangent plane offset by pad_r, sign probed); their landed centres
are asserted the same way.

Oracles: the flat removes the circular segment (r^2 acos(d/r) - d sqrt(r^2
- d^2)) x height; the block adds its box less the part already inside the
wall (integrated numerically); the cutout removes w x h x pad_back_t; the
pilots remove two cylinders. Containment reads back every pad.
"""
FH_ATTEMPT = 6
FH_OPTS = {
    "only_params": ["pad_w", "pad_back_t", "pad_z0", "pad_z1",
                    "pad_ang_1", "pad_ang_2", "pad_ang_3", "pad_ang_4",
                    "rj45_cut_w", "rj45_cut_h", "rj45_screw_pitch",
                    "usbc_cut_w", "usbc_cut_h", "usbc_screw_pitch",
                    "hdmi_cut_w", "hdmi_cut_h", "hdmi_screw_pitch",
                    "usba_cut_w", "usba_cut_h", "usba_screw_pitch",
                    "pilot_d", "pilot_h"],
    "liveness_budget_s": 400,
    "max_bodies": 1,
    "force_liveness": True,
}
INTERFERENCE_ALLOWED = []
CLEARANCES = []
# A screw pitch moves its two pilots symmetrically about the pad centre, so
# volume, area, face count, bbox and centroid are unchanged and the signature
# probe reads it as dead (stage A's intake_r precedent). prove_live steps each
# one and reads a pilot back.
EXPECT_DEAD = ["rj45_screw_pitch", "usbc_screw_pitch", "hdmi_screw_pitch", "usba_screw_pitch"]
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
TOL_MM = 0.05   # placement assertions

NEEDED = ("drum_d", "drum_r", "wall_t", "cavity_r", "floor_t", "split_z")
PARAMS = (
    ("pad_w",      "30 mm", "mm", "socket pad flat width"),
    ("pad_back_t", "5 mm",  "mm", "wall thickness behind a pad, flat to flat"),
    ("pad_z0",     "6 mm",  "mm", "pad bottom"),
    ("pad_z1",     "30 mm", "mm", "pad top"),
    ("pad_r",      "sqrt( drum_r ^ 2 - ( pad_w / 2 ) ^ 2 )", "mm", "derived: chord plane distance from the axis"),
    ("pad_ang_1",  "45 deg",  "deg", "RJ45 pad angle from +x toward +y"),
    ("pad_ang_2",  "75 deg",  "deg", "USB-C pad angle"),
    ("pad_ang_3",  "105 deg", "deg", "HDMI pad angle"),
    ("pad_ang_4",  "135 deg", "deg", "USB-A pair pad angle"),
    ("rj45_cut_w", "16 mm", "mm", "PLACEHOLDER (OI-013)"),
    ("rj45_cut_h", "14 mm", "mm", "PLACEHOLDER (OI-013)"),
    ("rj45_screw_pitch", "28 mm", "mm", "PLACEHOLDER (OI-013)"),
    ("usbc_cut_w", "10 mm", "mm", "PLACEHOLDER (OI-013)"),
    ("usbc_cut_h", "5 mm",  "mm", "PLACEHOLDER (OI-013)"),
    ("usbc_screw_pitch", "18 mm", "mm", "PLACEHOLDER (OI-013)"),
    ("hdmi_cut_w", "20 mm", "mm", "PLACEHOLDER (OI-013)"),
    ("hdmi_cut_h", "12 mm", "mm", "PLACEHOLDER (OI-013)"),
    ("hdmi_screw_pitch", "28 mm", "mm", "PLACEHOLDER (OI-013)"),
    ("usba_cut_w", "14 mm", "mm", "PLACEHOLDER (OI-013)"),
    ("usba_cut_h", "16 mm", "mm", "PLACEHOLDER (OI-013)"),
    ("usba_screw_pitch", "28 mm", "mm", "PLACEHOLDER (OI-013)"),
    ("pilot_d",    "2.5 mm", "mm", "flange screw pilot, M3 thread-forming"),
    ("pilot_h",    "4 mm",   "mm", "pilot depth from the pad; blind, 1 mm short of the block's inner face (6 broke through, measured)"),
)
PADS = (("rj45", "pad_ang_1", 45.0), ("usbc", "pad_ang_2", 75.0),
        ("hdmi", "pad_ang_3", 105.0), ("usba", "pad_ang_4", 135.0))


# ---------------------------------------------------------------- helpers (as stage A)

def ensure_params(ctx):
    for name in NEEDED:
        if ctx.up.itemByName(name) is None:
            raise RuntimeError("parameter %s missing: run stage A first" % name)
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


def radial_plane_checked(ctx, ang_expr, name, theta):
    """A plane through the z axis containing the direction theta; the sign of
    setByAngle is probed (R6), from stage O."""
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


def chord_plane_checked(ctx, tangent_plane, dist_expr, name, theta, r_cm):
    """tangent_plane offset by dist_expr so it passes through (r cos, r sin, z);
    the offset sign is probed."""
    pt = ctx.pt(r_cm * math.cos(theta), r_cm * math.sin(theta), 1.5)
    for e in (dist_expr, "-(%s)" % dist_expr):
        pin = ctx.planes.createInput()
        pin.setByOffset(tangent_plane, ctx.cbs(e))
        pl = ctx.planes.add(pin)
        pl.name = name
        sk = ctx.root.sketches.add(pl)
        off = abs(sk.modelToSketchSpace(pt).z)
        sk.deleteMe()
        if off < 0.01:
            return pl
        pl.deleteMe()
        adsk.doEvents()
    raise RuntimeError("chord plane %s never passed through the probe point" % name)


# ---------------------------------------------------------------- sketch recipes

def radial_rect(ctx, sk, theta, r_c, z_c, r_half, z_half, r_size, r_pos, z_size, z_pos):
    """(r, z) rectangle on a radial plane, from stage O. cm seeds, mm expressions."""
    ctx.U = (math.cos(theta), math.sin(theta), 0.0)
    ctx.V = (0.0, 0.0, 1.0)
    try:
        # The half-size is a compound expression: parenthesise it, or
        # "pad_z1 - pad_z0 / 2" halves the wrong term (measured 2026-10-22:
        # the rectangle landed at z 9..33 and r 38..40.5 for exactly that).
        ctx.bound_rect2(sk, (r_c * math.cos(theta), r_c * math.sin(theta), z_c), r_half, z_half,
                        u_size=r_size, v_size=z_size,
                        u_pos=(r_pos, "( %s ) / 2" % r_size), v_pos=(z_pos, "( %s ) / 2" % z_size))
    finally:
        ctx.U = (1.0, 0.0, 0.0)
        ctx.V = (0.0, 1.0, 0.0)


def assert_rect_landed(sk, theta, r_lo, r_hi, z_lo, z_hi, label):
    """Map the sketch's line endpoints to model space and check the r (along
    the radial direction) and z ranges, mm."""
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


def sym_cut_checked(ctx, sk, width_expr, body, want, label, min_vol=0.01):
    v0 = body.volume
    f = ctx.sym_cut(ctx.all_profiles(sk), width_expr, [body], min_vol_cm3=min_vol)
    f.name = label
    check_delta(label, v0, body.volume, -want, tol_rel=0.02)
    return f


def sym_join_checked(ctx, sk, width_expr, body, want, label):
    v0 = body.volume
    inp = ctx.extrudes.createInput(ctx.all_profiles(sk), ctx.ops.JoinFeatureOperation)
    inp.setSymmetricExtent(ctx.cbs(width_expr), True)
    inp.participantBodies = [body]
    f = ctx.extrudes.add(inp)
    f.name = label
    check_delta(label, v0, body.volume, want, tol_rel=0.03)
    return f


def tangent_circle(ctx, sk, theta, r_c, z_c, u_off_cm, r_seed, dia_expr, u_expr, z_expr):
    ctx.U = (-math.sin(theta), math.cos(theta), 0.0)
    try:
        w = (r_c * math.cos(theta) - u_off_cm * math.sin(theta),
             r_c * math.sin(theta) + u_off_cm * math.cos(theta), z_c)
        return ctx.bound_circle(sk, w, r_seed, dia_expr, x_pos=u_expr, v_pos=z_expr)
    finally:
        ctx.U = (1.0, 0.0, 0.0)


def assert_circle_landed(sk, circle, theta, u_want, z_want, label):
    m = sk.sketchToModelSpace(circle.centerSketchPoint.geometry)
    u = (-m.x * math.sin(theta) + m.y * math.cos(theta)) * 10
    z = m.z * 10
    if abs(u - u_want) > TOL_MM or abs(z - z_want) > TOL_MM:
        raise RuntimeError("%s: circle landed u %.2f z %.2f, wanted u %.2f z %.2f" % (label, u, z, u_want, z_want))
    print("%s: circle at u %.2f z %.2f" % (label, u, z))


# ---------------------------------------------------------------- oracles

def segment_area(r, d):
    """Area between a chord at distance d from the centre and the arc."""
    return r * r * math.acos(d / r) - d * math.sqrt(r * r - d * d)


def block_added(ctx, half_u, h):
    """Volume a block (2 half_u wide, h tall, from the chord plane at pad_r
    inward pad_back_t) adds to the wall: its box less the part already
    inside the wall, which lies between the inner-wall circle (cavity_r)
    and the chord plane. cm."""
    v = ctx.val
    pad_r, t, ri = v("pad_r"), v("pad_back_t"), v("cavity_r")
    n = 400
    overlap = 0.0
    for i in range(n):
        u = -half_u + (i + 0.5) * (2 * half_u / n)
        r_in = math.sqrt(ri * ri - u * u) if abs(u) < ri else 0.0
        overlap += max(0.0, pad_r - max(r_in, pad_r - t)) * (2 * half_u / n)
    return (2 * half_u * t - overlap) * h


# ---------------------------------------------------------------- build

def build_pad(ctx, base, name, ang_param, theta_deg):
    v = ctx.val
    th = math.radians(theta_deg)
    pad_r, dr, w, t = v("pad_r"), v("drum_r"), v("pad_w"), v("pad_back_t")
    z0, z1 = v("pad_z0"), v("pad_z1")
    h, zc = z1 - z0, (z0 + z1) / 2
    mm = lambda cm: cm * 10  # noqa: E731

    radial = radial_plane_checked(ctx, ang_param, "pad_%s_radial" % name, th)

    # the flat: (r, z) rectangle from pad_r to drum_r + 1, z0..z1, symmetric pad_w wide
    sk = ctx.root.sketches.add(radial)
    sk.name = "pad_%s_flat_sk" % name
    r_hi = dr + 0.1
    radial_rect(ctx, sk, th, (pad_r + r_hi) / 2, zc, (r_hi - pad_r) / 2, h / 2,
                "drum_r + 1 mm - pad_r", "( pad_r + drum_r + 1 mm ) / 2", "pad_z1 - pad_z0", "( pad_z0 + pad_z1 ) / 2")
    assert_rect_landed(sk, th, mm(pad_r), mm(r_hi), mm(z0), mm(z1), "pad_%s_flat" % name)
    sym_cut_checked(ctx, sk, "pad_w", base, segment_area(dr, pad_r) * h, "pad_%s_flat" % name)

    # the block behind it: from pad_r - t to pad_r, z0-1..z1+1, symmetric pad_w + 4 wide
    sk = ctx.root.sketches.add(radial)
    sk.name = "pad_%s_back_sk" % name
    radial_rect(ctx, sk, th, pad_r - t / 2, zc, t / 2, h / 2 + 0.1,
                "pad_back_t", "pad_r - pad_back_t / 2", "pad_z1 - pad_z0 + 2 mm", "( pad_z0 + pad_z1 ) / 2")
    assert_rect_landed(sk, th, mm(pad_r - t), mm(pad_r), mm(z0) - 1, mm(z1) + 1, "pad_%s_back" % name)
    sym_join_checked(ctx, sk, "pad_w + 4 mm", base, block_added(ctx, w / 2 + 0.2, h + 0.2), "pad_%s_back" % name)

    # the socket cutout: from pad_r - t - 1 to pad_r + 1, cut_h tall, symmetric cut_w wide
    sk = ctx.root.sketches.add(radial)
    sk.name = "pad_%s_cut_sk" % name
    cw, chh = v("%s_cut_w" % name), v("%s_cut_h" % name)
    radial_rect(ctx, sk, th, pad_r - t / 2, zc, t / 2 + 0.1, chh / 2,
                "pad_back_t + 2 mm", "pad_r - pad_back_t / 2", "%s_cut_h" % name, "( pad_z0 + pad_z1 ) / 2")
    assert_rect_landed(sk, th, mm(pad_r - t) - 1, mm(pad_r) + 1, mm(zc - chh / 2), mm(zc + chh / 2), "pad_%s_cut" % name)
    sym_cut_checked(ctx, sk, "%s_cut_w" % name, base, cw * chh * t, "pad_%s_cut" % name)

    # the pilots: circles on the chord plane at +-pitch/2 along the tangent
    tangent = radial_plane_checked(ctx, "%s + 90 deg" % ang_param, "pad_%s_tangent" % name, th + PI / 2)
    chord = chord_plane_checked(ctx, tangent, "pad_r", "pad_%s_chord" % name, th, pad_r)
    sk = ctx.root.sketches.add(chord)
    sk.name = "pad_%s_pilot_sk" % name
    pitch = v("%s_screw_pitch" % name)
    for sgn in (1, -1):
        c = tangent_circle(ctx, sk, th, pad_r, zc, sgn * pitch / 2, v("pilot_d") / 2, "pilot_d",
                           "%s_screw_pitch / 2" % name, "( pad_z0 + pad_z1 ) / 2")
        assert_circle_landed(sk, c, th, sgn * mm(pitch) / 2, mm(zc), "pad_%s_pilot" % name)
        adsk.doEvents()
    v0 = base.volume
    f = ctx.blind_cut(ctx.all_profiles(sk), "pilot_h", [base], "pilot_%s" % name, min_vol_cm3=0.003)
    f.name = "pad_%s_pilot" % name
    check_delta("pad_%s_pilot" % name, v0, base.volume, -2 * PI * (v("pilot_d") / 2) ** 2 * v("pilot_h"),
                tol_rel=0.03, tol_abs=0.001)


def read_back(ctx, base):
    v = ctx.val
    pad_r, t = v("pad_r") * 10, v("pad_back_t") * 10
    zc = (v("pad_z0") + v("pad_z1")) * 5
    for name, _, theta_deg in PADS:
        th = math.radians(theta_deg)
        tan = (-math.sin(th), math.cos(th))
        cw, pitch = v("%s_cut_w" % name) * 10, v("%s_screw_pitch" % name) * 10

        def at(r, u, z):
            return (r * math.cos(th) + u * tan[0], r * math.sin(th) + u * tan[1], z)
        probe(base, [at(pad_r + 0.7, 0, zc), at(pad_r + 0.7, cw / 2 + 2, zc)], False, "pad %s: outside the flat" % name)
        probe(base, [at(pad_r - 1, 0, zc), at(pad_r - t + 0.5, 0, zc)], False, "pad %s: cutout open through" % name)
        probe(base, [at(pad_r - 1, cw / 2 + 2, zc), at(pad_r - t + 0.5, cw / 2 + 2, zc)], True, "pad %s: block beside the cutout" % name)
        probe(base, [at(pad_r - t - 1.5, cw / 2 + 2, zc)], False, "pad %s: cavity behind the block" % name)
        probe(base, [at(pad_r - 2, pitch / 2, zc), at(pad_r - 2, -pitch / 2, zc)], False, "pad %s: pilots" % name)
        probe(base, [at(pad_r - 2, pitch / 2 + 2.5, zc)], True, "pad %s: beside a pilot" % name)
        probe(base, [at(pad_r - 1, 0, v("pad_z0") * 10 - 2), at(pad_r - 1, 0, v("pad_z1") * 10 + 1.5)], True,
              "pad %s: wall below and above the flat" % name)
    probe(base, [(0, -78.5, 20), (78.5, 0, 20)], True, "front and right wall intact")


def prove_live(ctx, name, stepped_expr, point_mm, restore_expr):
    """Step a parameter the signature probe cannot see, check that a point
    which was empty (a pilot centre) becomes solid, and restore. The body is
    re-resolved by name after every write (R5)."""
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
        raise RuntimeError("prove_live %s: pilot did not move when stepped to %s" % (name, stepped_expr))
    healthy_or_raise(ctx, "prove_live " + name)
    print("prove_live %s: stepped to %s, pilot moved, restored to %s" % (name, stepped_expr, restore_expr))


def prove_symmetric_params(ctx):
    v = ctx.val
    r_probe = v("pad_r") * 10 - 2
    zc = (v("pad_z0") + v("pad_z1")) * 5
    for name, _, theta_deg in PADS:
        th = math.radians(theta_deg)
        pname = "%s_screw_pitch" % name
        pitch = v(pname) * 10
        u = pitch / 2
        pt = (r_probe * math.cos(th) - u * math.sin(th), r_probe * math.sin(th) + u * math.cos(th), zc)
        prove_live(ctx, pname, "%g mm" % (pitch + 4), pt, "%g mm" % pitch)


def render(ctx, tag):
    os.makedirs(RENDER_DIR, exist_ok=True)
    vp = ctx.app.activeViewport
    for name, orient in (("rear", adsk.core.ViewOrientations.BackViewOrientation),
                         ("iso", adsk.core.ViewOrientations.IsoTopLeftViewOrientation)):
        cam = vp.camera
        cam.viewOrientation = orient
        cam.isFitView = True
        vp.camera = cam
        adsk.doEvents()
        vp.saveAsImageFile(os.path.join(RENDER_DIR, "pi_drum_stage%s_%s.png" % (tag, name)), 1600, 1200)


def run(_context: str):
    app = adsk.core.Application.get()
    if not app.activeDocument.name.startswith(DOC_PREFIX):
        raise RuntimeError("wrong document %r" % app.activeDocument.name)
    ctx = BuildCtx(app)
    ensure_params(ctx)
    base = body_named(ctx, "base")
    for name, ang_param, theta in PADS:
        build_pad(ctx, base, name, ang_param, theta)
        base = body_named(ctx, "base")
        adsk.doEvents()
    healthy_or_raise(ctx, "stage B")
    base = body_named(ctx, "base")
    read_back(ctx, base)
    prove_symmetric_params(ctx)
    base = body_named(ctx, "base")
    if ctx.root.bRepBodies.count != 1:
        raise RuntimeError("expected 1 body, found %d" % ctx.root.bRepBodies.count)
    print("base: %.4f cm3, %d faces" % (base.volume, base.faces.count))
    render(ctx, "B")
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
