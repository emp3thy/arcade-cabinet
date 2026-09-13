"""Lap pad, D-014: the nested disc. Stage H -- fit-out (owner, 2026-09-13), in
the document that holds stages A to G.

  stiffener     the steel plate pocket was cut 95 along x, 53 along y; the
                docs (06) and the owner say 53 left-right, 95 front-to-back.
                Parametric fix: stiff_w -> 53 mm, stiff_d -> 95 mm. Oracle:
                plate volume unchanged, pocket face 53 x 95 centred on the
                stick.
  lipo plinth   a plinth_h block filling the tray pocket floor (tray_in_w x
                tray_in_d at the LiPo centre) so the cell sits up off the
                floor, then two zip-tie tunnels tie_w x tie_h through plinth
                and tray walls along y at lipo_cx +/- tie_dx: a tie runs
                under the cell, up the outside of the tray wall, over the
                top and back. Oracle: plinth adds tray_in_w tray_in_d
                plinth_h; each tunnel removes tie_w tie_h (tray_in_d +
                2 tray_wall).
  antenna hoops five cable hoops standing on the floor against the inner
                wall at hoop_ang_1..5 (30, 0, -30, -60, -90 deg from +x, the
                Brook's side round to the antenna bracket at -103 deg). Each
                is an inverted U: hoop_d radial x hoop_h tall x hoop_w along
                the wall, opening hoop_in_d x hoop_in_h from the floor, the
                cable running tangentially. Sketched on a plane through the
                z axis at the hoop's angle (setByAngle; the sign is probed,
                R6) and joined symmetrically by hoop_w. Oracle per hoop:
                (hoop_d hoop_h - hoop_in_d hoop_in_h) hoop_w within 3 % (the
                flat back nicks the round wall by 0.06 mm at its corners).

Every feature is guarded by name; the script is idempotent.
"""
FH_ATTEMPT = 2
FH_OPTS = {
    "only_params": ["hoop_d", "hoop_h", "hoop_w", "hoop_in_d", "hoop_in_h", "hoop_ang_1",
                    "plinth_h", "tie_w", "tie_h", "tie_dx"],
    "liveness_budget_s": 180,
}
INTERFERENCE_ALLOWED = []
CLEARANCES = []
# The two zip-tie tunnels move symmetrically about lipo_cx when tie_dx
# changes: volume, bbox and centroid stay identical, so the signature probe
# reads it as dead (attempt 1, measured). It is live: the script steps tie_dx
# and reads the tunnel ceilings' x positions back.
EXPECT_DEAD = ["tie_dx"]
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

PARAMS_H = (
    ("plinth_h",   "4 mm",   "mm",  "LiPo plinth height above the floor"),
    ("tie_w",      "5 mm",   "mm",  "zip-tie tunnel width; 4.8 mm ties"),
    ("tie_h",      "2 mm",   "mm",  "zip-tie tunnel height"),
    ("tie_dx",     "25 mm",  "mm",  "tunnels at lipo_cx +/- tie_dx"),
    ("tie_len",    "tray_out_d + 2 mm", "mm", "derived: tunnel cut length along y"),
    ("hoop_d",     "6 mm",   "mm",  "hoop depth, radial"),
    ("hoop_h",     "7 mm",   "mm",  "hoop height above the floor"),
    ("hoop_w",     "8 mm",   "mm",  "hoop width along the wall"),
    ("hoop_in_d",  "3.5 mm", "mm",  "cable opening, radial"),
    ("hoop_in_h",  "4.5 mm", "mm",  "cable opening height"),
    ("hoop_rc",    "cavity_dia / 2 - hoop_d / 2", "mm", "derived: hoop centre radius, back against the wall"),
    ("hoop_ang_1", "30 deg",  "deg", "hoop angle from +x"),
    ("hoop_ang_2", "0 deg",   "deg", "hoop angle from +x"),
    ("hoop_ang_3", "-30 deg", "deg", "hoop angle from +x"),
    ("hoop_ang_4", "-60 deg", "deg", "hoop angle from +x"),
    ("hoop_ang_5", "-90 deg", "deg", "hoop angle from +x; the antenna bracket is at -103"),
)
UPDATE = (("stiff_w", "53 mm"), ("stiff_d", "95 mm"))
NEEDED = ("floor_t", "cavity_dia", "lipo_cx", "lipo_cy", "tray_in_w", "tray_in_d", "tray_out_d",
          "tray_wall", "tray_h", "stick_x", "stick_y", "stiff_t", "plate_bot_z", "stiff_w", "stiff_d")
HOOPS = 5


def ensure_params(ctx):
    for name in NEEDED:
        if ctx.up.itemByName(name) is None:
            raise RuntimeError("parameter %s missing: run stages A to G first" % name)
    for name, expr, unit, comment in PARAMS_H:
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


def offset_plane_checked(ctx, base, expr, name, axis, want_cm):
    for e in (expr, "-(%s)" % expr):
        pin = ctx.planes.createInput()
        pin.setByOffset(base, ctx.cbs(e))
        pl = ctx.planes.add(pin)
        pl.name = name
        sk = ctx.root.sketches.add(pl)
        o = sk.sketchToModelSpace(ctx.pt(0, 0, 0))
        got = (o.x, o.y, o.z)[axis]
        if abs(got - want_cm) < 0.01:
            sk.deleteMe()
            return pl
        sk.deleteMe()
        pl.deleteMe()
        adsk.doEvents()
    raise RuntimeError("offset plane %s never landed at %.3f cm on axis %d" % (name, want_cm, axis))


def radial_plane_checked(ctx, ang_param, name, theta):
    """Vertical plane through the z axis at angle theta (rad) from +x, built
    by rotating the XZ plane about z by ang_param. setByAngle's sign is
    probed: the point (cos t, sin t, 1) must lie in the plane (R6)."""
    probe = ctx.pt(10 * math.cos(theta), 10 * math.sin(theta), 1.0)
    for e in (ang_param, "-(%s)" % ang_param):
        pin = ctx.planes.createInput()
        pin.setByAngle(ctx.root.zConstructionAxis, ctx.cbs(e), ctx.root.xZConstructionPlane)
        pl = ctx.planes.add(pin)
        pl.name = name
        sk = ctx.root.sketches.add(pl)
        p = sk.modelToSketchSpace(probe)
        off = abs(p.z)
        sk.deleteMe()
        if off < 0.01:
            return pl
        pl.deleteMe()
        adsk.doEvents()
    raise RuntimeError("radial plane %s never contained the probe point" % name)


def profile_by_area(sk, want_cm2, tol, z_min_cm):
    coll = adsk.core.ObjectCollection.create()
    seen = []
    for pr in sk.profiles:  # fusionhelper: allow R11 — collection add, not a document mutation
        props = pr.areaProperties(adsk.fusion.CalculationAccuracy.HighCalculationAccuracy)
        c = sk.sketchToModelSpace(props.centroid)
        seen.append((round(props.area, 4), round(c.z * 10, 2)))
        if abs(props.area - want_cm2) < tol * want_cm2 and c.z > z_min_cm:
            coll.add(pr)
    if coll.count != 1:
        raise RuntimeError("%s: want one profile of %.4f cm2 above z, matched %d of %s"
                           % (sk.name, want_cm2, coll.count, seen))
    return coll


def sym_join(ctx, profs, dist_expr, target, want_cm3, tol, label):
    v0 = target.volume
    inp = ctx.extrudes.createInput(profs, ctx.ops.JoinFeatureOperation)
    inp.setSymmetricExtent(ctx.cbs(dist_expr), True)
    inp.participantBodies = [target]
    f = ctx.extrudes.add(inp)
    adsk.doEvents()
    added = target.volume - v0
    if abs(added - want_cm3) > tol * want_cm3:
        f.deleteMe()
        raise RuntimeError("%s: joined %.4f cm3, wanted %.4f" % (label, added, want_cm3))
    return f, added


def run(_context: str):
    app = adsk.core.Application.get()
    if not app.activeDocument.name.startswith("Arcade Controller"):
        raise RuntimeError("wrong document " + app.activeDocument.name)
    ctx = BuildCtx(app)
    ensure_params(ctx)
    v = ctx.val
    shell = body_named(ctx, "shell")
    plate = body_named(ctx, "plate")
    floor_plane = ctx.planes.itemByName("floor_plane")
    if floor_plane is None:
        raise RuntimeError("floor_plane missing")

    # ---- stiffener pocket: 53 along x, 95 along y ------------------------------
    plate_v0 = plate.volume
    for name, expr in UPDATE:
        p = ctx.up.itemByName(name)
        if p.expression.replace(" ", "") != expr.replace(" ", ""):
            p.expression = expr  # fusionhelper: allow R5 — every body handle is re-resolved by name on the next two lines
            adsk.doEvents()
    plate = body_named(ctx, "plate")
    shell = body_named(ctx, "shell")
    z_pocket = v("plate_bot_z") + v("stiff_t")
    pocket = None
    for f in plate.faces:
        pl = adsk.core.Plane.cast(f.geometry)
        if pl is None or abs(pl.normal.z) < 0.999:
            continue
        bb = f.boundingBox
        if abs(bb.maxPoint.z - z_pocket) < 0.001 and abs((bb.minPoint.x + bb.maxPoint.x) / 2 - v("stick_x")) < 0.01:
            pocket = f
    if pocket is None:
        raise RuntimeError("stiffener pocket face not found at z=%.2f mm" % (z_pocket * 10))
    bb = pocket.boundingBox
    px, py = (bb.maxPoint.x - bb.minPoint.x) * 10, (bb.maxPoint.y - bb.minPoint.y) * 10
    if abs(px - 53) > 0.05 or abs(py - 95) > 0.05:
        raise RuntimeError("stiffener pocket reads %.2f x %.2f mm, wanted 53 x 95" % (px, py))
    if abs(plate.volume - plate_v0) > 0.01:
        raise RuntimeError("plate volume moved by %.4f cm3 on the stiffener swap" % (plate.volume - plate_v0))
    print("stiffener pocket: %.1f x %.1f mm (x by y), plate volume unchanged" % (px, py))
    adsk.doEvents()

    # ---- LiPo plinth ------------------------------------------------------------
    if not feature_exists(ctx, "lipo_plinth"):
        sk = ctx.root.sketches.add(floor_plane)
        sk.name = "lipo_plinth"
        ctx.bound_rect2(
            sk, (v("lipo_cx"), v("lipo_cy"), v("floor_t")),
            v("tray_in_w") / 2, v("tray_in_d") / 2,
            u_size="tray_in_w", v_size="tray_in_d",
            u_pos=("lipo_cx", "tray_in_w / 2"), v_pos=("lipo_cy", "tray_in_d / 2"))
        if not sk.isFullyConstrained:
            raise RuntimeError("lipo_plinth sketch not fully constrained")
        want = v("tray_in_w") * v("tray_in_d") * v("plinth_h")
        v0 = shell.volume
        f = ctx.checked_join(ctx.all_profiles(sk), "plinth_h", shell,
                             lambda b: abs((b.volume - v0) - want) < 0.01 * want, "plinth")
        f.name = "lipo_plinth"
        shell = body_named(ctx, "shell")
        print("lipo plinth: +%.3f cm3 (want %.3f)" % (shell.volume - v0, want))
    adsk.doEvents()

    # ---- zip-tie tunnels through plinth and tray walls, along y ----------------
    if not feature_exists(ctx, "tie_tunnels"):
        pl = ctx.planes.itemByName("lipo_plane")
        if pl is None:
            pl = offset_plane_checked(ctx, ctx.root.xZConstructionPlane, "lipo_cy", "lipo_plane", 1, v("lipo_cy"))
        sk = ctx.root.sketches.add(pl)
        sk.name = "tie_tunnels"
        ctx.V = (0.0, 0.0, 1.0)
        for sgn, cx_expr in ((-1, "lipo_cx - tie_dx"), (1, "lipo_cx + tie_dx")):
            ctx.bound_rect2(
                sk, (v("lipo_cx") + sgn * v("tie_dx"), v("lipo_cy"), v("floor_t") + v("tie_h") / 2),
                v("tie_w") / 2, v("tie_h") / 2,
                u_size="tie_w", v_size="tie_h",
                u_pos=(cx_expr, "tie_w / 2"), v_pos=("floor_t + tie_h / 2", "tie_h / 2"))
            adsk.doEvents()
        ctx.V = (0.0, 1.0, 0.0)
        if not sk.isFullyConstrained:
            raise RuntimeError("tie_tunnels sketch not fully constrained")
        want = 2 * v("tie_w") * v("tie_h") * (v("tray_in_d") + 2 * v("tray_wall"))
        v0 = shell.volume
        f = ctx.sym_cut(ctx.all_profiles(sk), "tie_len", [shell], min_vol_cm3=0.5 * want)
        f.name = "tie_tunnels"
        shell = body_named(ctx, "shell")
        removed = v0 - shell.volume
        if abs(removed - want) > 0.02 * want:
            raise RuntimeError("tie_tunnels removed %.4f cm3, wanted %.4f" % (removed, want))
        print("zip-tie tunnels: -%.4f cm3 (want %.4f)" % (removed, want))
    adsk.doEvents()

    # ---- antenna cable hoops --------------------------------------------------
    hoop_want = (v("hoop_d") * v("hoop_h") - v("hoop_in_d") * v("hoop_in_h")) * v("hoop_w")
    for k in range(1, HOOPS + 1):
        name = "hoop_%d" % k
        if feature_exists(ctx, name):
            continue
        ang = "hoop_ang_%d" % k
        theta = v(ang)  # radians
        pl = ctx.planes.itemByName(name + "_plane")
        if pl is None:
            pl = radial_plane_checked(ctx, ang, name + "_plane", theta)
        sk = ctx.root.sketches.add(pl)
        sk.name = name
        rc = v("hoop_rc")
        cx, cy = rc * math.cos(theta), rc * math.sin(theta)
        ctx.U = (math.cos(theta), math.sin(theta), 0.0)
        ctx.V = (0.0, 0.0, 1.0)
        ctx.bound_rect2(
            sk, (cx, cy, v("floor_t") + v("hoop_h") / 2), v("hoop_d") / 2, v("hoop_h") / 2,
            u_size="hoop_d", v_size="hoop_h",
            u_pos=("hoop_rc", "hoop_d / 2"), v_pos=("floor_t + hoop_h / 2", "hoop_h / 2"))
        # the opening: from 1 mm below the floor up to hoop_in_h, so it splits
        # the outer rectangle cleanly and the inverted U is one profile
        ctx.bound_rect2(
            sk, (cx, cy, v("floor_t") + (v("hoop_in_h") - 0.1) / 2), v("hoop_in_d") / 2, (v("hoop_in_h") + 0.1) / 2,
            u_size="hoop_in_d", v_size="hoop_in_h + 1 mm",
            u_pos=("hoop_rc", "hoop_in_d / 2"), v_pos=("floor_t + (hoop_in_h - 1 mm) / 2", "(hoop_in_h + 1 mm) / 2"))
        ctx.U = (1.0, 0.0, 0.0)
        ctx.V = (0.0, 1.0, 0.0)
        if not sk.isFullyConstrained:
            raise RuntimeError("%s sketch not fully constrained" % name)
        u_area = v("hoop_d") * v("hoop_h") - v("hoop_in_d") * v("hoop_in_h")
        profs = profile_by_area(sk, u_area, 0.02, v("floor_t") + 0.01)
        f, added = sym_join(ctx, profs, "hoop_w", shell, hoop_want, 0.03, name)
        f.name = name
        shell = body_named(ctx, "shell")
        print("%s at %.0f deg (%.1f, %.1f): +%.4f cm3 (want %.4f)" % (name, math.degrees(theta), cx * 10, cy * 10, added, hoop_want))
        adsk.doEvents()

    # ---- read-back: cable path open through every hoop --------------------------
    P = adsk.core.Point3D.create
    inside = adsk.fusion.PointContainment.PointInsidePointContainment
    for k in range(1, HOOPS + 1):
        theta = v("hoop_ang_%d" % k)
        rc = v("hoop_rc")
        z = v("floor_t") + v("hoop_in_h") / 2
        if shell.pointContainment(P(rc * math.cos(theta), rc * math.sin(theta), z)) == inside:
            raise RuntimeError("hoop_%d opening is blocked" % k)
        top = v("floor_t") + v("hoop_h") - 0.05
        if shell.pointContainment(P(rc * math.cos(theta), rc * math.sin(theta), top)) != inside:
            raise RuntimeError("hoop_%d bridge missing" % k)
    print("hoops: openings clear, bridges solid")

    # ---- tie_dx liveness, read back from the tunnel ceilings -----------------
    def tunnel_dx():
        sh = body_named(ctx, "shell")
        z_ceil = v("floor_t") + v("tie_h")
        xs = []
        for face in sh.faces:
            pl = adsk.core.Plane.cast(face.geometry)
            if pl is None or abs(pl.normal.z) < 0.999:
                continue
            bb = face.boundingBox
            if abs(bb.maxPoint.z - z_ceil) > 0.001 or abs((bb.maxPoint.x - bb.minPoint.x) - v("tie_w")) > 0.01:
                continue
            xs.append(abs((bb.minPoint.x + bb.maxPoint.x) / 2 - v("lipo_cx")) * 10)
        return sorted(set(round(x, 2) for x in xs))

    d0 = tunnel_dx()
    if d0 != [round(v("tie_dx") * 10, 2)]:
        raise RuntimeError("tunnel offset read %s, wanted %.2f" % (d0, v("tie_dx") * 10))
    ctx.up.itemByName("tie_dx").expression = "27 mm"  # fusionhelper: allow R5 — tunnel_dx re-resolves the shell by name; shell re-resolved below
    adsk.doEvents()
    d1 = tunnel_dx()
    ctx.up.itemByName("tie_dx").expression = "25 mm"  # fusionhelper: allow R5 — tunnel_dx re-resolves the shell by name; shell re-resolved below
    adsk.doEvents()
    d2 = tunnel_dx()
    if d1 != [27.0] or d2 != [25.0]:
        raise RuntimeError("tie_dx not live: %s -> %s -> %s" % (d0, d1, d2))
    shell = body_named(ctx, "shell")
    print("tie_dx live: tunnel offset %.1f -> %.1f -> %.1f mm" % (d0[0], d1[0], d2[0]))

    tl = ctx.des.timeline
    bad = []
    for i in range(tl.count):
        it = tl.item(i)
        if it.isRolledBack:
            continue
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
