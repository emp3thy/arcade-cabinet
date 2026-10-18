"""Lap pad, D-014: the nested disc. Stage O -- fixes from the first test print
(owner's photos and measurements, 2026-10-18), in the document that holds
stages A to N. Ring and sled change; the TPU tyre's window follows the port.

Port board (ring):
  pilots        the board's M3 holes are d 3.2 with their EDGES port_hole_gap
                2.1 mm from the board edges (owner), so the hole centres sit
                3.7 mm in, not the 2 mm stage I drilled -- the reason the
                first print's pilots missed the board. port_hole_inset
                becomes port_hole_gap + port_hole_d / 2; stages I and L's
                pilot sketches follow it.
  opening       the plug tunnel must be port_open_h 21.1 mm high (owner; the
                16 mm window hid part of the USB-B socket), width unchanged
                at port_w 22, grown equally about port_cz. A plain 22 x 21.1
                window would run tangent to the upper pilots (window half
                height 10.55 = pilot centre 11.8 - pilot radius 1.25), so the
                opening is notched round the screws instead: the stage C
                window becomes port_w x port_h with port_h stopping
                port_notch_wall short of an M3's major diameter, and a new
                port_slot cut port_slot_w wide takes the middle to the full
                port_open_h. port_slot_w also stops port_notch_wall short of
                the screws. Building it as two cuts keeps the pilots clear
                of the window everywhere in the timeline.
  tyre window   tyre_win_h follows port_open_h, not port_h, so the TPU
                clears the full opening. Tyre to be reprinted.

Antenna (sled):
  hoops         hoop_4 and hoop_5 deleted with their sketches, planes and
                angle parameters; the openings of the three that stay shrink
                from 6 x 5 to hoop_in_d x hoop_in_h 3 x 3. The 1.1-1.4 mm
                cable rattled in the 6 x 5; 3 x 3 still threads the 2 mm U.FL
                plug.
  bracket       ant_ang 60 -> -60 deg (where hoop 4 stood, so the pigtail runs
                Brook -> hoop 1 -> 2 -> 3 -> bracket and the stub antenna points
                into the space hoop 5 left); ant_t 2.5 -> 5 mm. Rebuilt, not
                rotated: stepping ant_ang from 60 to -60 re-frames the
                setByAngle plane, and the bracket sketch came out turned 180
                deg in its plane -- at 120 deg and under the floor, z -20 to
                -2 (measured 2026-10-18, spike). So stage J's bracket, hole
                and plane are deleted and the bracket is drawn fresh on a new
                probed radial plane at the end of the timeline, joined
                straight into the sled.

The hoops and the bracket were joined before the stage J floor split, so
deleting them takes three lumps out of sled_combine's tool list. Fusion marks
the combine "tool body is lost"; the timeline is rolled to just before it and
its tool bodies are reset to the lumps that remain (measured 2026-10-18).

Oracles: every step asserts its analytic volume change on the body it
touches (off: two hoop U-sections and the old plate less its hole; openings:
three (6x5 - 3x3) hoop_w; new bracket: ant_t ant_len ant_h, then its hole;
window: port_w x step x boss_in; slot: port_slot_w x (port_open_h - port_h)
x boss_in). Then
point containment reads back the opening, the notches, the pilots, the old
pilots filled, the tyre window, every hoop and the bracket; and ring and sled
must not interfere.
"""
FH_ATTEMPT = 2
FH_OPTS = {
    "only_params": ["port_open_h", "port_hole_gap", "port_hole_d", "port_screw_d", "port_notch_wall",
                    "hoop_in_d", "hoop_in_h", "ant_t", "ant_ang"],
    "liveness_budget_s": 400,
    "max_bodies": 6,
    # The stage M art sketches fail the constraints check by design, which
    # would otherwise skip liveness here as prior_failure.
    "force_liveness": True,
}
INTERFERENCE_ALLOWED = []
CLEARANCES = []
EXPECT_DEAD = []  # namespace is reused across executes
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

PARAMS_O = (
    ("port_hole_gap",   "2.1 mm",  "mm", "board M3 hole edge to each board edge (owner, 2026-10-18)"),
    ("port_hole_d",     "3.2 mm",  "mm", "board M3 hole diameter (owner, 2026-10-18)"),
    ("port_screw_d",    "3 mm",    "mm", "M3 major diameter, what a thread-forming screw cuts to"),
    ("port_notch_wall", "1 mm",    "mm", "wall left between an M3 thread and the port opening"),
    ("port_open_h",     "21.1 mm", "mm", "port opening height (owner, 2026-10-18); width stays port_w"),
    ("port_slot_w",     "2 * ( port_hole_dx - port_screw_d / 2 - port_notch_wall )", "mm",
     "derived: width of the opening's full-height middle, clear of the screws"),
)
UPDATE_PORT = (
    ("port_hole_inset", "port_hole_gap + port_hole_d / 2"),
    ("port_h",          "2 * ( port_hole_dz - port_screw_d / 2 - port_notch_wall )"),
    ("tyre_win_h",      "port_open_h + 2 * tyre_win_clear"),
)
UPDATE_HOOP = (("hoop_in_d", "3 mm"), ("hoop_in_h", "3 mm"))
UPDATE_ANT_T = (("ant_t", "5 mm"),)
UPDATE_ANT_ANG = (("ant_ang", "-60 deg"),)
GONE_HOOPS = (4, 5)
KEPT_HOOPS = (1, 2, 3)
OLD_ANT_DEG = 60.0
NEEDED = ("port_w", "port_h", "port_cz", "port_hole_inset", "port_hole_dx", "port_hole_dz", "port_pilot",
          "port_pilot_depth", "port_plate_w", "port_plate_h", "boss_in", "boss_y0", "boss_w", "floor_t",
          "under_h", "cavity_dia", "facet_y", "tyre_win_w", "tyre_win_h", "tyre_win_clear", "tyre_od",
          "ant_ang", "ant_t", "ant_len", "ant_h", "ant_hole", "ant_hole_z", "ant_rc", "hoop_d", "hoop_h",
          "hoop_w", "hoop_in_d", "hoop_in_h", "hoop_rc", "hoop_ang_1", "hoop_ang_2", "hoop_ang_3", "shell_h")
PI = math.pi
EPS = 0.02        # cm, containment probes
N_LUMPS = 4 + 1 + len(KEPT_HOOPS)   # standoffs, tray+plinth, hoops; the bracket now joins after the split


def ensure_params(ctx):
    for name in NEEDED:
        if ctx.up.itemByName(name) is None:
            raise RuntimeError("parameter %s missing: run stages A to N first" % name)
    for name, expr, unit, comment in PARAMS_O:
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


def pending(ctx, updates):
    """The (name, expr) pairs whose parameter is not yet at expr."""
    return [(n, e) for n, e in updates
            if ctx.up.itemByName(n).expression.replace(" ", "") != e.replace(" ", "")]


def write_params(ctx, updates):
    for name, expr in updates:
        ctx.up.itemByName(name).expression = expr  # fusionhelper: allow R5 — no BRep handle held across this write; bodies re-resolved by name after
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


def lumps_now(ctx):
    """Bodies between the floor split and the combine: everything that is not
    a named part. Only meaningful with the timeline rolled before the combine."""
    named = ("plate", "tpu_ring", "tpu_tyre", "ring", "sled")
    return [b for b in ctx.root.bRepBodies if b.name not in named]


def delete_named(ctx, feature, sketch, plane):
    for n in (feature, feature + " (1)"):
        f = ctx.extrudes.itemByName(n)
        if f is not None:
            f.deleteMe()
            adsk.doEvents()
    sk = ctx.root.sketches.itemByName(sketch)
    if sk is not None:
        sk.deleteMe()
        adsk.doEvents()
    if plane is not None:
        pl = ctx.planes.itemByName(plane)
        if pl is not None:
            pl.deleteMe()
            adsk.doEvents()


def repair_combine(ctx):
    """Re-point sled_combine at the lumps the floor split now yields."""
    healthy = adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState
    cf = ctx.root.features.combineFeatures.itemByName("sled_combine")
    if cf is None:
        raise RuntimeError("sled_combine missing")
    print("sled_combine: health %s %s" % (cf.healthState, cf.errorOrWarningMessage))
    if cf.healthState == healthy:
        return
    cf.timelineObject.rollTo(True)
    adsk.doEvents()
    cf = ctx.root.features.combineFeatures.itemByName("sled_combine")
    target = cf.targetBody
    tb = target.boundingBox
    if target.name != "sled" or tb.maxPoint.z > ctx.val("floor_t") + 0.001:
        ctx.des.timeline.moveToEnd()
        raise RuntimeError("sled_combine's target is %s, z to %.2f mm, not the floor slab"
                           % (target.name, tb.maxPoint.z * 10))
    lumps = lumps_now(ctx)
    print("lumps before the combine: %d %s" % (len(lumps), sorted(b.name for b in lumps)))
    if len(lumps) != N_LUMPS:
        ctx.des.timeline.moveToEnd()
        raise RuntimeError("expected %d floor lumps before sled_combine, found %d" % (N_LUMPS, len(lumps)))
    tools = adsk.core.ObjectCollection.create()
    for b in lumps:  # fusionhelper: allow R11 — collection add, not a document mutation
        tools.add(b)
    cf.toolBodies = tools  # pyright: ignore[reportAttributeAccessIssue] — CombineFeature.toolBodies is read/write in the API
    adsk.doEvents()
    ctx.des.timeline.moveToEnd()
    adsk.doEvents()


# ---- sled: hoops and the old bracket off ------------------------------------------

def remove_old(ctx):
    v = ctx.val
    hoops_left = [k for k in GONE_HOOPS if ctx.up.itemByName("hoop_ang_%d" % k) is not None]
    old_bracket = ctx.extrudes.itemByName("ant_bracket (1)") is not None
    if not hoops_left and not old_bracket:
        print("hoops %s and the stage J bracket already gone" % (GONE_HOOPS,))
        return
    want = 0.0
    if hoops_left:
        u_vol = (v("hoop_d") * v("hoop_h") - v("hoop_in_d") * v("hoop_in_h")) * v("hoop_w")
        want -= len(hoops_left) * u_vol
    if old_bracket:
        want -= v("ant_t") * (v("ant_len") * v("ant_h") - PI * (v("ant_hole") / 2) ** 2)
    v0 = body_named(ctx, "sled").volume
    for k in hoops_left:
        name = "hoop_%d" % k
        delete_named(ctx, name, name, name + "_plane")
        p = ctx.up.itemByName("hoop_ang_%d" % k)
        if p is not None and not p.deleteMe():
            raise RuntimeError("hoop_ang_%d still referenced" % k)
        adsk.doEvents()
    if old_bracket:
        delete_named(ctx, "ant_hole", "ant_hole", None)
        delete_named(ctx, "ant_bracket", "ant_bracket", "ant_plane")
    repair_combine(ctx)
    healthy_or_raise(ctx, "removing hoops %s and the stage J bracket" % (hoops_left,))
    check_delta("hoops %s and the old bracket off the sled" % (hoops_left,), v0,
                body_named(ctx, "sled").volume, want)


def shrink_hoops(ctx):
    v = ctx.val
    todo = pending(ctx, UPDATE_HOOP)
    if not todo:
        print("hoop openings already %.1f x %.1f mm" % (v("hoop_in_d") * 10, v("hoop_in_h") * 10))
        return
    old = v("hoop_in_d") * v("hoop_in_h")
    v0 = body_named(ctx, "sled").volume
    write_params(ctx, todo)
    new = v("hoop_in_d") * v("hoop_in_h")
    check_delta("hoop openings to %.1f x %.1f" % (v("hoop_in_d") * 10, v("hoop_in_h") * 10),
                v0, body_named(ctx, "sled").volume, len(KEPT_HOOPS) * (old - new) * v("hoop_w"))


# ---- sled: antenna bracket ---------------------------------------------------------

def radial_plane_checked(ctx, ang_param, name, theta):
    """A plane through the z axis at ang_param; the sign of setByAngle is
    probed (R6), from stage J."""
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


def radial_rect(ctx, sk, theta, rc, r_half, z_c, z_half, r_size, r_pos, z_size, z_pos):
    ctx.U = (math.cos(theta), math.sin(theta), 0.0)
    ctx.V = (0.0, 0.0, 1.0)
    ctx.bound_rect2(sk, (rc * math.cos(theta), rc * math.sin(theta), z_c), r_half, z_half,
                    u_size=r_size, v_size=z_size, u_pos=(r_pos, "%s / 2" % r_size), v_pos=(z_pos, "%s / 2" % z_size))
    ctx.U = (1.0, 0.0, 0.0)
    ctx.V = (0.0, 1.0, 0.0)


def build_bracket(ctx):
    v = ctx.val
    write_params(ctx, pending(ctx, UPDATE_ANT_T + UPDATE_ANT_ANG))
    if feature_exists(ctx, "ant_bracket_join"):
        print("antenna bracket already rebuilt")
        return
    theta = v("ant_ang")
    pl = radial_plane_checked(ctx, "ant_ang", "ant_plane", theta)
    sk = ctx.root.sketches.add(pl)
    sk.name = "ant_bracket"
    radial_rect(ctx, sk, theta, v("ant_rc"), v("ant_len") / 2, v("floor_t") + v("ant_h") / 2, v("ant_h") / 2,
                "ant_len", "ant_rc", "ant_h", "floor_t + ant_h / 2")
    if not sk.isFullyConstrained:
        raise RuntimeError("ant_bracket sketch not fully constrained")
    want = v("ant_t") * v("ant_len") * v("ant_h")
    v0 = body_named(ctx, "sled").volume
    inp = ctx.extrudes.createInput(ctx.all_profiles(sk), ctx.ops.JoinFeatureOperation)
    inp.setSymmetricExtent(ctx.cbs("ant_t"), True)
    inp.participantBodies = [body_named(ctx, "sled")]
    f = ctx.extrudes.add(inp)
    adsk.doEvents()
    f.name = "ant_bracket_join"
    check_delta("antenna bracket at %.0f deg, %.1f mm thick" % (math.degrees(theta), v("ant_t") * 10),
                v0, body_named(ctx, "sled").volume, want)
    if ctx.root.bRepBodies.count != 5:
        raise RuntimeError("bracket did not merge into the sled: %d bodies" % ctx.root.bRepBodies.count)

    sk = ctx.root.sketches.add(pl)
    sk.name = "ant_hole"
    ctx.U = (math.cos(theta), math.sin(theta), 0.0)
    ctx.V = (0.0, 0.0, 1.0)
    ctx.bound_circle(sk, (v("ant_rc") * math.cos(theta), v("ant_rc") * math.sin(theta), v("floor_t") + v("ant_hole_z")),
                     v("ant_hole") / 2, "ant_hole", x_pos="ant_rc", v_pos="floor_t + ant_hole_z")
    ctx.U = (1.0, 0.0, 0.0)
    ctx.V = (0.0, 1.0, 0.0)
    if not sk.isFullyConstrained:
        raise RuntimeError("ant_hole sketch not fully constrained")
    want = PI * (v("ant_hole") / 2) ** 2 * v("ant_t")
    v0 = body_named(ctx, "sled").volume
    inp = ctx.extrudes.createInput(ctx.all_profiles(sk), ctx.ops.CutFeatureOperation)
    inp.setSymmetricExtent(ctx.cbs("ant_t * 3"), True)
    inp.participantBodies = [body_named(ctx, "sled")]
    f = ctx.extrudes.add(inp)
    adsk.doEvents()
    f.name = "ant_hole_cut"
    check_delta("antenna hole d %.1f" % (v("ant_hole") * 10), v0, body_named(ctx, "sled").volume, -want)


# ---- ring: port opening -------------------------------------------------------------

def check_port_layout(ctx):
    """Everything the notched opening must satisfy, asserted on parameter
    values before any geometry is read back."""
    v = ctx.val
    dx, dz = v("port_hole_dx"), v("port_hole_dz")
    rs = v("port_screw_d") / 2
    hw, hh = v("port_w") / 2, v("port_h") / 2
    sw, sh = v("port_slot_w") / 2, v("port_open_h") / 2
    if hh > sh:
        raise RuntimeError("full-width window %.2f mm taller than the opening %.2f" % (hh * 20, sh * 20))
    if sw > hw:
        raise RuntimeError("slot %.2f mm wider than the window %.2f" % (sw * 20, hw * 20))
    # thread to window: the window's top edge, under the screw
    gap_win = dz - rs - hh
    # thread to slot: the slot's side, beside the screw (slot reaches past dz - rs?)
    gap_slot = dx - rs - sw
    # thread to the window's corner when the screw sits above it (dx < hw)
    gap_corner = math.hypot(max(dx - hw, 0.0), dz - hh) - rs if dx > hw else gap_win
    gap_slot_corner = math.hypot(dx - sw, max(dz - sh, 0.0)) - rs
    wall = v("port_notch_wall") - 0.001
    for label, g in (("window top", gap_win), ("slot side", gap_slot),
                     ("window corner", gap_corner), ("slot corner", gap_slot_corner)):
        if g < wall:
            raise RuntimeError("M3 thread %.2f mm from the %s, wanted %.2f" % (g * 10, label, wall * 10))
    if v("port_plate_w") / 2 < hw + 0.1 or v("port_plate_h") / 2 < sh + 0.1:
        raise RuntimeError("opening not covered by the faceplate")
    if v("port_hole_inset") < v("port_hole_d") / 2:
        raise RuntimeError("board hole breaks the board edge")
    print("opening %.1f wide x %.1f high, middle %.1f wide to %.1f high; pilots at (+-%.2f, +-%.2f); "
          "M3 thread %.2f mm from the window, %.2f from the slot"
          % (hw * 20, hh * 20, sw * 20, sh * 20, dx * 10, dz * 10, gap_win * 10, gap_slot * 10))


def grow_window(ctx):
    v = ctx.val
    todo = pending(ctx, UPDATE_PORT)
    if not todo:
        print("port window already %.1f x %.1f" % (v("port_w") * 10, v("port_h") * 10))
        return
    h0 = v("port_h")
    r0 = body_named(ctx, "ring").volume
    t0 = body_named(ctx, "tpu_tyre").volume
    write_params(ctx, todo)
    check_port_layout(ctx)
    healthy_or_raise(ctx, "port parameters")
    # pilots move but keep their volume; only the window grows in the ring
    check_delta("window %.1f -> %.1f mm high" % (h0 * 10, v("port_h") * 10), r0,
                body_named(ctx, "ring").volume, -v("port_w") * (v("port_h") - h0) * v("boss_in"))
    print("tyre: %.3f -> %.3f cm3 (window now %.1f x %.1f)" % (
        t0, body_named(ctx, "tpu_tyre").volume, v("tyre_win_w") * 10, v("tyre_win_h") * 10))


def cut_slot(ctx):
    v = ctx.val
    if feature_exists(ctx, "port_slot_cut"):
        print("port slot already cut")
        return
    pl = ctx.planes.itemByName("facet_plane")
    if pl is None:
        raise RuntimeError("facet_plane missing: run stages A to N first")
    sk = ctx.root.sketches.add(pl)
    sk.name = "port_slot"
    ctx.V = (0.0, 0.0, 1.0)
    ctx.bound_rect2(
        sk, (0, v("facet_y"), v("port_cz")),
        v("port_slot_w") / 2, v("port_open_h") / 2,
        u_size="port_slot_w", v_size="port_open_h",
        u_pos=("0 mm", "port_slot_w / 2"), v_pos=("port_cz", "port_open_h / 2"))
    ctx.V = (0.0, 1.0, 0.0)
    if not sk.isFullyConstrained:
        raise RuntimeError("port_slot sketch not fully constrained")
    want = v("port_slot_w") * (v("port_open_h") - v("port_h")) * v("boss_in")
    r0 = body_named(ctx, "ring").volume
    for d in ctx._try_dirs("port_slot"):
        adsk.doEvents()
        if d is None:
            break
        inp = ctx.extrudes.createInput(ctx.all_profiles(sk), ctx.ops.CutFeatureOperation)
        ctx._one_side(inp, "boss_in + 2 mm", d)
        inp.participantBodies = [body_named(ctx, "ring")]
        f = ctx.extrudes.add(inp)
        adsk.doEvents()
        removed = r0 - body_named(ctx, "ring").volume
        if abs(removed - want) < 0.02 * want:
            ctx._resolved["port_slot"] = d
            # sketches and features share one namespace; suffix the feature
            f.name = "port_slot_cut"
            print("port_slot: -%.4f cm3 (want %.4f)" % (removed, want))
            return
        f.deleteMe()
        adsk.doEvents()
    raise RuntimeError("port_slot: no direction removed %.4f cm3" % want)


# ---- read-back ----------------------------------------------------------------------

def probe(body, pts, want_inside, label):
    inside = adsk.fusion.PointContainment.PointInsidePointContainment
    for p in pts:
        got = body.pointContainment(p) == inside
        if got != want_inside:
            raise RuntimeError("%s: (%.2f, %.2f, %.2f) mm is %s" % (
                label, p.x * 10, p.y * 10, p.z * 10, "solid" if got else "open"))


def read_back(ctx):
    v = ctx.val
    P = ctx.pt
    ring = body_named(ctx, "ring")
    cz = v("port_cz")
    y_mid = v("boss_y0") + v("boss_in") / 2
    hw, hh = v("port_w") / 2, v("port_h") / 2
    sw, sh = v("port_slot_w") / 2, v("port_open_h") / 2
    dx, dz = v("port_hole_dx"), v("port_hole_dz")
    quad = [(sx, sz) for sx in (-1, 1) for sz in (-1, 1)]

    probe(ring, [P(sx * (hw - EPS), y_mid, cz + sz * (hh - EPS)) for sx, sz in quad], False, "window corner open")
    probe(ring, [P(sx * (hw + EPS), y_mid, cz) for sx in (-1, 1)], True, "window side solid")
    probe(ring, [P(sx * (sw - EPS), y_mid, cz + sz * (sh - EPS)) for sx, sz in quad], False, "slot corner open")
    probe(ring, [P(0, y_mid, cz + sz * (sh + EPS)) for sz in (-1, 1)], True, "above and below the slot solid")
    # the notch: beside the slot, above the window, clear of the pilot
    nx = (sw + hw) / 2
    nz = (hh + sh) / 2
    probe(ring, [P(sx * nx, y_mid, cz + sz * nz) for sx, sz in quad], True, "notch solid")
    probe(ring, [P(sx * dx, v("boss_y0") + 0.1, cz + sz * dz) for sx, sz in quad], False, "pilot open")
    probe(ring, [P(sx * dx, v("boss_y0") + v("port_pilot_depth") + EPS, cz + sz * dz) for sx, sz in quad], True,
          "pilot bottom solid")
    old_dx = v("port_plate_w") / 2 - 0.2
    old_dz = v("port_plate_h") / 2 - 0.2
    probe(ring, [P(sx * old_dx, v("boss_y0") + 0.1, cz + sz * old_dz) for sx, sz in quad], True,
          "stage I pilot positions filled")
    print("port: window, slot, notches, pilots and filled old pilots read back")

    tyre = body_named(ctx, "tpu_tyre")
    y_t = v("facet_y") + 0.5
    tw, th = v("tyre_win_w") / 2, v("tyre_win_h") / 2
    probe(tyre, [P(sx * (tw - EPS), y_t, cz + sz * (th - EPS)) for sx, sz in quad], False, "tyre window open")
    probe(tyre, [P(0, y_t, cz + sz * (th + EPS)) for sz in (-1, 1)], True, "tyre bridges solid")
    print("tyre window %.1f x %.1f read back" % (tw * 20, th * 20))

    sled = body_named(ctx, "sled")
    rc = v("hoop_rc")
    z_open = v("floor_t") + v("hoop_in_h") / 2
    for k in KEPT_HOOPS:
        t = v("hoop_ang_%d" % k)
        c, s = math.cos(t), math.sin(t)
        probe(sled, [P(rc * c, rc * s, z_open)], False, "hoop_%d opening" % k)
        probe(sled, [P(rc * c, rc * s, v("floor_t") + v("hoop_in_h") + EPS)], True, "hoop_%d bridge" % k)
        r_side = rc + v("hoop_in_d") / 2 + EPS
        probe(sled, [P(r_side * c, r_side * s, z_open)], True, "hoop_%d side wall" % k)
    for k, deg in zip(GONE_HOOPS, (-60.0, -90.0)):
        t = math.radians(deg)
        # off the bracket's mid-plane by more than its half thickness
        off = v("ant_t") / 2 + 0.1 if deg == -60.0 else 0.0
        x = rc * math.cos(t) - off * math.sin(t)
        y = rc * math.sin(t) + off * math.cos(t)
        probe(sled, [P(x, y, v("floor_t") + v("hoop_h") - 0.1)], False, "hoop_%d gone" % k)
    print("hoops %s open %.1f x %.1f; hoops %s gone" % (
        KEPT_HOOPS, v("hoop_in_d") * 10, v("hoop_in_h") * 10, GONE_HOOPS))

    t = v("ant_ang")
    c, s = math.cos(t), math.sin(t)
    ar = v("ant_rc")
    z_lo = v("floor_t") + 0.3
    half = v("ant_t") / 2
    probe(sled, [P(ar * c - k * (half - EPS) * s, ar * s + k * (half - EPS) * c, z_lo) for k in (-1, 1)], True,
          "bracket faces")
    probe(sled, [P(ar * c - k * (half + EPS) * s, ar * s + k * (half + EPS) * c, z_lo) for k in (-1, 1)], False,
          "bracket thickness")
    probe(sled, [P(ar * c, ar * s, v("floor_t") + v("ant_hole_z"))], False, "antenna hole")
    t_old = math.radians(OLD_ANT_DEG)
    probe(sled, [P(ar * math.cos(t_old), ar * math.sin(t_old), z_lo)], False, "old bracket position")
    reach = math.sqrt((v("cavity_dia") / 2) ** 2 - ar ** 2)
    print("bracket at %.0f deg, %.1f mm thick; a straight antenna along its hole axis meets the wall %.1f mm "
          "from the hole" % (math.degrees(t), v("ant_t") * 10, reach * 10))

    tbm = adsk.fusion.TemporaryBRepManager.get()
    a = tbm.copy(body_named(ctx, "sled"))
    b = tbm.copy(body_named(ctx, "ring"))
    tbm.booleanOperation(a, b, adsk.fusion.BooleanTypes.IntersectionBooleanType)
    if a.volume > 0.001:
        raise RuntimeError("sled and ring interfere by %.4f cm3" % a.volume)
    print("sled / ring interference %.5f cm3" % a.volume)


def run(_context: str):
    app = adsk.core.Application.get()
    if not app.activeDocument.name.startswith("Arcade Controller"):
        raise RuntimeError("wrong document " + app.activeDocument.name)
    ctx = BuildCtx(app)
    ensure_params(ctx)

    remove_old(ctx)
    shrink_hoops(ctx)
    build_bracket(ctx)
    grow_window(ctx)
    check_port_layout(ctx)
    cut_slot(ctx)
    adsk.doEvents()

    healthy_or_raise(ctx, "stage O")
    read_back(ctx)

    if ctx.root.bRepBodies.count != 5:
        raise RuntimeError("expected 5 bodies, found %d" % ctx.root.bRepBodies.count)
    for name in ("ring", "sled", "plate", "tpu_ring", "tpu_tyre"):
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
