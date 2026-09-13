"""Lap pad, D-014: the nested disc. Stage I -- port board mount (OI-011), in
the document that holds stages A to H.

The port board (owner's photos and measurements, 2026-09-13) is Brook's
panel-mount board B-C16046: a black faceplate port_plate_w x port_plate_h x
port_plate_t carrying a USB Type-B socket and a 3.5 mm jack, a rear board
port_board_len deep behind it with a 5-pin cable to the Brook, and two M3
holes at diagonal corners port_hole_inset from the edges.

Mount: the faceplate sits flat against the INSIDE face of the port boss
(y = boss_y0), centred on x = 0, z = port_cz, and screws into the boss from
inside. The stage C window through the boss becomes the plug tunnel: port_w
x port_h shrink to 22 x 16 so the plug's overmould passes and the screw
holes land in solid boss (the stage E tyre window follows, to 23 x 17).
Four port_pilot holes port_pilot_depth deep are drilled into the boss's
inner face at the plate's four corners, so either diagonal fits.

Oracles: window faces read back at port_w x port_h; the four pilots remove
4 pi (port_pilot / 2)^2 port_pilot_depth; the plate outline sits inside
the boss face and the window inside the plate; the rear board's reach
(y = boss_y0 - port_board_len) clears the Brook standoffs.
"""
FH_ATTEMPT = 2
FH_OPTS = {
    "only_params": ["port_plate_w", "port_plate_h", "port_hole_inset", "port_pilot", "port_pilot_depth"],
    "liveness_budget_s": 120,
}
INTERFERENCE_ALLOWED = []
CLEARANCES = []
# The four pilots move symmetrically about the window centre when the plate
# size or hole inset changes: volume, bbox and centroid stay identical, so
# the signature probe reads all three as dead (attempt 1, measured). They are
# live: the script steps port_hole_inset and reads the pilot axes back.
EXPECT_DEAD = ["port_plate_w", "port_plate_h", "port_hole_inset"]
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

PARAMS_I = (
    ("port_plate_w",     "26.1 mm", "mm", "Brook panel board faceplate width (x)"),
    ("port_plate_h",     "31 mm",   "mm", "faceplate height (z)"),
    ("port_plate_t",     "1.5 mm",  "mm", "faceplate thickness"),
    ("port_board_len",   "28.3 mm", "mm", "rear board depth behind the faceplate"),
    ("port_hole_inset",  "3 mm",    "mm", "M3 hole centre from each plate edge (owner: 2 mm from the corner)"),
    ("port_pilot",       "2.5 mm",  "mm", "M3 thread-forming pilot in the boss"),
    ("port_pilot_depth", "6 mm",    "mm", "pilot depth into the boss_in 8 mm boss"),
    ("port_hole_dx",     "port_plate_w / 2 - port_hole_inset", "mm", "derived"),
    ("port_hole_dz",     "port_plate_h / 2 - port_hole_inset", "mm", "derived"),
)
UPDATE = (("port_w", "22 mm"), ("port_h", "16 mm"))
NEEDED = ("boss_y0", "boss_in", "port_cz", "port_w", "port_h", "floor_t", "under_h",
          "brook_cx", "brook_cy", "brook_pitch_y", "so_od", "boss_w")


def ensure_params(ctx):
    for name in NEEDED:
        if ctx.up.itemByName(name) is None:
            raise RuntimeError("parameter %s missing: run stages A to H first" % name)
    for name, expr, unit, comment in PARAMS_I:
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


def window_size(ctx, feature_name):
    """x and z extent of the port window from the cut feature's own faces."""
    f = None
    for n in (feature_name, feature_name + " (1)"):
        f = ctx.extrudes.itemByName(n)
        if f is not None:
            break
    if f is None:
        raise RuntimeError("%s missing" % feature_name)
    xs, zs = [], []
    for i in range(f.faces.count):
        bb = f.faces.item(i).boundingBox
        xs += [bb.minPoint.x, bb.maxPoint.x]
        zs += [bb.minPoint.z, bb.maxPoint.z]
    return (max(xs) - min(xs)) * 10, (max(zs) - min(zs)) * 10, (min(zs) + max(zs)) / 2 * 10


def run(_context: str):
    app = adsk.core.Application.get()
    if not app.activeDocument.name.startswith("Arcade Controller"):
        raise RuntimeError("wrong document " + app.activeDocument.name)
    ctx = BuildCtx(app)
    ensure_params(ctx)
    v = ctx.val

    # ---- window becomes the plug tunnel -----------------------------------------
    for name, expr in UPDATE:
        p = ctx.up.itemByName(name)
        if p.expression.replace(" ", "") != expr.replace(" ", ""):
            p.expression = expr  # fusionhelper: allow R5 — no BRep handle is held yet; bodies resolved by name below
            adsk.doEvents()
    shell = body_named(ctx, "shell")
    w, h, zc = window_size(ctx, "port_window")
    if abs(w - v("port_w") * 10) > 0.05 or abs(h - v("port_h") * 10) > 0.05 or abs(zc - v("port_cz") * 10) > 0.05:
        raise RuntimeError("port window reads %.2f x %.2f at z %.2f, wanted %.1f x %.1f at %.1f"
                           % (w, h, zc, v("port_w") * 10, v("port_h") * 10, v("port_cz") * 10))
    tw, th, _ = window_size(ctx, "tyre_window")
    print("port window %.1f x %.1f mm at z %.1f; tyre window %.1f x %.1f" % (w, h, zc, tw, th))

    # ---- layout checks --------------------------------------------------------
    hw, hh = v("port_plate_w") / 2, v("port_plate_h") / 2
    z_lo, z_hi = v("port_cz") - hh, v("port_cz") + hh
    if z_lo < v("floor_t") + 0.1 or z_hi > v("under_h") - 0.1:
        raise RuntimeError("faceplate z %.1f..%.1f mm does not sit on the boss face (%.1f..%.1f)"
                           % (z_lo * 10, z_hi * 10, v("floor_t") * 10, v("under_h") * 10))
    if hw > v("boss_w") / 2 - 0.1:
        raise RuntimeError("faceplate wider than the boss")
    if v("port_w") / 2 > hw or v("port_h") / 2 > hh:
        raise RuntimeError("window larger than the faceplate")
    dx, dz = v("port_hole_dx"), v("port_hole_dz")
    gap_z = dz - v("port_h") / 2 - v("port_pilot") / 2
    if gap_z < 0.15:
        raise RuntimeError("pilot holes only %.2f mm from the window" % (gap_z * 10))
    reach = v("boss_y0") - v("port_board_len")
    so_far = v("brook_cy") + v("brook_pitch_y") / 2 + v("so_od") / 2
    if reach < so_far + 0.1:
        raise RuntimeError("rear board reaches y=%.1f, Brook standoffs end at y=%.1f" % (reach * 10, so_far * 10))
    print("faceplate %.1f x %.1f at z %.1f..%.1f on boss face y=%.2f; pilots %.1f mm from the window; rear board to y=%.1f (standoffs end %.1f)"
          % (hw * 20, hh * 20, z_lo * 10, z_hi * 10, v("boss_y0") * 10, gap_z * 10, reach * 10, so_far * 10))

    # ---- four pilot holes into the boss's inner face -----------------------------
    if not feature_exists(ctx, "port_pilots"):
        pl = ctx.planes.itemByName("boss_in_plane")
        if pl is None:
            pl = offset_plane_checked(ctx, ctx.root.xZConstructionPlane, "boss_y0", "boss_in_plane", 1, v("boss_y0"))
        sk = ctx.root.sketches.add(pl)
        sk.name = "port_pilots"
        ctx.V = (0.0, 0.0, 1.0)
        for sx, sz in ((-1, 1), (1, 1), (-1, -1), (1, -1)):
            ctx.bound_circle(
                sk, (sx * dx, v("boss_y0"), v("port_cz") + sz * dz), v("port_pilot") / 2, "port_pilot",
                x_pos="port_hole_dx", v_pos="port_cz %s port_hole_dz" % ("+" if sz > 0 else "-"))
            adsk.doEvents()
        ctx.V = (0.0, 1.0, 0.0)
        if not sk.isFullyConstrained:
            raise RuntimeError("port_pilots sketch not fully constrained")
        want = 4 * math.pi * (v("port_pilot") / 2) ** 2 * v("port_pilot_depth")
        v0 = shell.volume
        f = ctx.blind_cut(ctx.all_profiles(sk), "port_pilot_depth", [shell], "pilots", min_vol_cm3=0.5 * want)
        f.name = "port_pilots"
        shell = body_named(ctx, "shell")
        removed = v0 - shell.volume
        if abs(removed - want) > 0.02 * want:
            raise RuntimeError("port_pilots removed %.4f cm3, wanted %.4f" % (removed, want))
        print("port pilots: -%.4f cm3 (want %.4f)" % (removed, want))
    adsk.doEvents()

    # ---- read-back: pilots open at the boss face, closed short of the facet -------
    P = adsk.core.Point3D.create
    inside = adsk.fusion.PointContainment.PointInsidePointContainment
    for sx, sz in ((-1, 1), (1, 1), (-1, -1), (1, -1)):
        x, z = sx * dx, v("port_cz") + sz * dz
        if shell.pointContainment(P(x, v("boss_y0") + 0.1, z)) == inside:
            raise RuntimeError("pilot at (%.1f, %.1f) not open" % (x * 10, z * 10))
        if shell.pointContainment(P(x, v("boss_y0") + v("port_pilot_depth") + 0.05, z)) != inside:
            raise RuntimeError("pilot at (%.1f, %.1f) broke through" % (x * 10, z * 10))
    print("pilots: open %.1f mm, solid beyond" % (v("port_pilot_depth") * 10))

    # ---- liveness read-back: pilot axes follow port_hole_inset -------------------
    def pilot_offsets():
        sh = body_named(ctx, "shell")
        xs = set()
        for face in sh.faces:
            cyl = adsk.core.Cylinder.cast(face.geometry)
            if cyl is None or abs(cyl.radius - v("port_pilot") / 2) > 0.005:
                continue
            o = cyl.origin
            if abs(o.y - v("boss_y0")) > v("port_pilot_depth") + 0.1 or o.y < v("boss_y0") - 0.1:
                continue
            xs.add(round(abs(o.x) * 10, 2))
        return sorted(xs)

    d0 = pilot_offsets()
    if d0 != [round(v("port_hole_dx") * 10, 2)]:
        raise RuntimeError("pilot x offsets read %s, wanted %.2f" % (d0, v("port_hole_dx") * 10))
    ctx.up.itemByName("port_hole_inset").expression = "4 mm"  # fusionhelper: allow R5 — pilot_offsets re-resolves the shell by name; shell re-resolved below
    adsk.doEvents()
    d1 = pilot_offsets()
    ctx.up.itemByName("port_hole_inset").expression = "3 mm"  # fusionhelper: allow R5 — pilot_offsets re-resolves the shell by name; shell re-resolved below
    adsk.doEvents()
    d2 = pilot_offsets()
    shell = body_named(ctx, "shell")
    if d1 != [round((v("port_plate_w") / 2 - 0.4) * 10, 2)] or d2 != d0:
        raise RuntimeError("port_hole_inset not live: %s -> %s -> %s" % (d0, d1, d2))
    print("port_hole_inset live: pilot |x| %.2f -> %.2f -> %.2f mm" % (d0[0], d1[0], d2[0]))

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
