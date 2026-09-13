"""Lap pad, D-014: the nested disc. Stage A -- bottom shell and control plate,
no rim slope, no raised discs, no port facet, no fillets.

Geometry (mm; the API works in cm, every number below reaches Fusion as an
expression string). Disc centre is the world origin; the player sits at -Y.

SHELL (PETG). A blank cylinder shell_dia x shell_h. Three cuts:
  rebate  -- rebate_dia, rebate_h deep from the top: the plate sits here, its
             top 1 mm below the rim lip.
  core    -- core_dia straight down to the floor: the opening the plate covers,
             leaving a ledge ledge_w wide for the plate to rest on.
  under   -- cavity_dia from the floor up to under_h: hollows the shell behind
             the ledge so the wall is wall_t, the ledge ledge_t thick. The
             ledge prints as a bridged annulus (ledge_w + wall gap ~ 18 mm).
PLATE (PLA). rebate_dia less plate_clear a side, plate_t thick, sitting on
the ledge. Through-cut in one sketch: stick shaft hole, four M3 clearance
holes on the axes at stick_bolt_r, six button holes on the Sega arc. Blind
pocket stiff_w x stiff_d x stiff_t on the underside for the steel plate.

PANEL DERIVATION (matches docs/docs/06-enclosure-reference.md, D-014):
  punch column x = stick_x + stick_btn (63); punch row y = stick_y + btn_pitch
  kick column x  = punch x + row_off (8);    kick row y  = stick_y
  index button arc_idx (14) nearer the player than middle, ring arc_ring (6).
Checked against the study coordinates (150,150 origin): stick (94,134),
LK (165,120) MK (205,134) HK (245,128), LP (157,160) MP (197,174) HP (237,168).

Bolt holes are dimensioned FROM THE STICK CENTRE with horizontal/vertical
point constraints, not from the origin: two of them sit on the stick's own
axes and a zero-length origin dimension is not a dimension.
"""
FH_ATTEMPT = 2
FH_OPTS = {
    # Roots only. Every derived parameter is exercised through these.
    "only_params": [
        "shell_dia", "shell_h", "wall_t", "floor_t", "ledge_t", "ledge_w",
        "rebate_dia", "plate_t", "plate_clear",
        "stick_x", "stick_y", "stick_hole", "stick_bolt_r", "bolt_hole",
        "stiff_w", "stiff_d", "stiff_t",
        "btn_hole", "btn_pitch", "stick_btn", "row_off", "arc_idx", "arc_ring",
    ],
    "liveness_budget_s": 120,
}
INTERFERENCE_ALLOWED = []
CLEARANCES = []
# stick_bolt_r moves four holes symmetrically about the stick centre: volume,
# area, face count, bbox AND centroid stay byte-identical, so the signature
# liveness probe reads it as dead (attempt 1, measured). It is live: the
# script proves it by stepping the parameter and reading the hole axes back.
EXPECT_DEAD = ["stick_bolt_r"]
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

MM = 0.1  # cm per mm, seeds only

PARAMS = (
    # shell
    ("shell_dia",   "276 mm", "shell outer diameter; the TPU tyre wraps outside this"),
    ("shell_h",     "53 mm",  "rim lip height"),
    ("wall_t",      "2.4 mm", "shell wall"),
    ("floor_t",     "2 mm",   "shell floor"),
    ("ledge_t",     "3.5 mm", "plate ledge thickness"),
    ("ledge_w",     "8 mm",   "plate ledge width"),
    ("rebate_dia",  "250 mm", "plate rebate diameter"),
    ("plate_t",     "3.5 mm", "plate thickness"),
    ("plate_clear", "0.35 mm", "plate radial clearance in the rebate"),
    ("rebate_h",    "plate_t + 1 mm", "derived: plate top sits 1 mm below the lip"),
    ("plate_dia",   "rebate_dia - 2 * plate_clear", "derived"),
    ("core_dia",    "rebate_dia - 2 * ledge_w", "derived: the opening inside the ledge"),
    ("cavity_dia",  "shell_dia - 2 * wall_t", "derived"),
    ("under_h",     "shell_h - rebate_h - ledge_t", "derived: cavity ceiling height"),
    ("plate_bot_z", "shell_h - rebate_h", "derived"),
    ("plate_top_z", "plate_bot_z + plate_t", "derived"),
    # panel
    ("stick_x",      "-56 mm", "stick centre x from the disc centre"),
    ("stick_y",      "-16 mm", "stick centre y from the disc centre, player at -y"),
    ("stick_hole",   "22 mm",  "shaft hole in the plate; steel plate is 21"),
    ("stick_bolt_r", "16 mm",  "M3 holes on the axes, from the stick centre"),
    ("bolt_hole",    "3.4 mm", "M3 clearance"),
    ("stiff_w",      "95 mm",  "steel stiffener, along x"),
    ("stiff_d",      "53 mm",  "steel stiffener, along y"),
    ("stiff_t",      "1 mm",   "steel stiffener pocket depth"),
    ("btn_hole",     "30.5 mm", "30 mm screw-in button hole"),
    ("btn_pitch",    "40 mm",  "button pitch, both directions"),
    ("stick_btn",    "63 mm",  "stick centre to punch column, horizontal"),
    ("row_off",      "8 mm",   "kick row sits this far right of the punch row"),
    ("arc_idx",      "14 mm",  "index button nearer the player than middle"),
    ("arc_ring",     "6 mm",   "ring button nearer the player than middle"),
    ("lp_x", "stick_x + stick_btn",            "derived"),
    ("lp_y", "stick_y + btn_pitch - arc_idx",  "derived"),
    ("mp_x", "lp_x + btn_pitch",               "derived"),
    ("mp_y", "stick_y + btn_pitch",            "derived"),
    ("hp_x", "mp_x + btn_pitch",               "derived"),
    ("hp_y", "stick_y + btn_pitch - arc_ring", "derived"),
    ("lk_x", "lp_x + row_off",                 "derived"),
    ("lk_y", "stick_y - arc_idx",              "derived"),
    ("mk_x", "lk_x + btn_pitch",               "derived"),
    ("mk_y", "stick_y",                        "derived"),
    ("hk_x", "mk_x + btn_pitch",               "derived"),
    ("hk_y", "stick_y - arc_ring",             "derived"),
)

BUTTONS = ("lp", "mp", "hp", "lk", "mk", "hk")


def ensure_params(ctx):
    for name, expr, comment in PARAMS:
        existing = ctx.up.itemByName(name)
        if existing is not None:
            if existing.expression.replace(" ", "") != expr.replace(" ", ""):
                raise RuntimeError(
                    "parameter %s already exists with expression %r, wanted %r"
                    % (name, existing.expression, expr))
            continue
        ctx.up.add(name, ctx.cbs(expr), "mm", comment)
        adsk.doEvents()


def centred_circle(ctx, sk, r_seed_cm, dia_expr, jitter):
    """Circle pinned to the sketch origin by a coincident constraint and a
    bound diameter. Jittered seed (measured: coincident-coordinate circles
    over-constrain)."""
    circles = sk.sketchCurves.sketchCircles
    c = circles.addByCenterRadius(
        ctx.pt(0.011 + 0.003 * jitter, 0.017 + 0.005 * jitter, 0), r_seed_cm)
    sk.geometricConstraints.addCoincident(c.centerSketchPoint, sk.originPoint)
    d = sk.sketchDimensions.addDiameterDimension(
        c, ctx.pt(r_seed_cm + 0.4, -0.4, 0))
    d.parameter.expression = dia_expr
    return c


def axis_circle(ctx, sk, ref_circle, dx_cm, dy_cm, r_seed_cm, dia_expr,
                dist_expr, jitter):
    """Circle on one of ref_circle's axes: horizontal-points or
    vertical-points constraint to the reference centre, one bound distance,
    bound diameter."""
    gc = sk.geometricConstraints
    rc = ref_circle.centerSketchPoint.geometry
    c = sk.sketchCurves.sketchCircles.addByCenterRadius(
        ctx.pt(rc.x + dx_cm + 0.002 * jitter, rc.y + dy_cm + 0.003 * jitter, 0),
        r_seed_cm)
    anchor = ctx.pt(rc.x + dx_cm + r_seed_cm + 0.3, rc.y + dy_cm - 0.3, 0)
    if abs(dx_cm) >= abs(dy_cm):
        gc.addHorizontalPoints(ref_circle.centerSketchPoint, c.centerSketchPoint)
        orient = ctx.dims_or.HorizontalDimensionOrientation
    else:
        gc.addVerticalPoints(ref_circle.centerSketchPoint, c.centerSketchPoint)
        orient = ctx.dims_or.VerticalDimensionOrientation
    d = sk.sketchDimensions.addDistanceDimension(
        ref_circle.centerSketchPoint, c.centerSketchPoint, orient, anchor)
    d.parameter.expression = dist_expr
    d = sk.sketchDimensions.addDiameterDimension(c, anchor)
    d.parameter.expression = dia_expr
    return c


def body_named(ctx, name):
    for b in ctx.root.bRepBodies:
        if b.name == name:
            return b
    raise RuntimeError("no body named %s" % name)


def run(_context: str):
    ctx = BuildCtx(adsk.core.Application.get())
    ensure_params(ctx)
    v = ctx.val  # cm

    # ---- datums ---------------------------------------------------------
    top_plane = ctx.plane_at_z("shell_h", "top_plane")
    floor_plane = ctx.plane_at_z("floor_t", "floor_plane")
    plate_bot_plane = ctx.plane_at_z("plate_bot_z", "plate_bot_plane")
    plate_top_plane = ctx.plane_at_z("plate_top_z", "plate_top_plane")

    # ---- shell blank ----------------------------------------------------
    sk = ctx.root.sketches.add(ctx.root.xYConstructionPlane)
    sk.name = "shell_blank"
    centred_circle(ctx, sk, v("shell_dia") / 2, "shell_dia", 1)
    if not sk.isFullyConstrained:
        raise RuntimeError("shell_blank sketch not fully constrained")
    h_cm = v("shell_h")
    f, shell = ctx.checked_newbody(
        ctx.all_profiles(sk), "shell_h",
        lambda b: (b.boundingBox.maxPoint.z > h_cm - 0.01
                   and b.boundingBox.minPoint.z > -0.01),
        "shell_blank")
    f.name = "shell_blank"
    shell.name = "shell"
    adsk.doEvents()

    # ---- rebate (from the top, down rebate_h) ---------------------------
    sk = ctx.root.sketches.add(top_plane)
    sk.name = "rebate"
    centred_circle(ctx, sk, v("rebate_dia") / 2, "rebate_dia", 2)
    f = ctx.blind_cut(ctx.all_profiles(sk), "rebate_h", [shell], "rebate")
    f.name = "rebate"
    shell = body_named(ctx, "shell")

    # ---- core (from the top, down to the floor) -------------------------
    sk = ctx.root.sketches.add(top_plane)
    sk.name = "core"
    centred_circle(ctx, sk, v("core_dia") / 2, "core_dia", 3)
    f = ctx.blind_cut(ctx.all_profiles(sk), "shell_h - floor_t", [shell], "core")
    f.name = "core"
    shell = body_named(ctx, "shell")

    # ---- undercut (from the floor, up to the ledge underside) -----------
    sk = ctx.root.sketches.add(floor_plane)
    sk.name = "undercut"
    centred_circle(ctx, sk, v("cavity_dia") / 2, "cavity_dia", 4)
    f = ctx.blind_cut(ctx.all_profiles(sk), "under_h - floor_t", [shell], "under")
    f.name = "undercut"
    shell = body_named(ctx, "shell")
    adsk.doEvents()

    # ---- plate blank ----------------------------------------------------
    sk = ctx.root.sketches.add(plate_bot_plane)
    sk.name = "plate_blank"
    centred_circle(ctx, sk, v("plate_dia") / 2, "plate_dia", 5)
    top_cm = v("plate_top_z")
    f, plate = ctx.checked_newbody(
        ctx.all_profiles(sk), "plate_t",
        lambda b: abs(b.boundingBox.maxPoint.z - top_cm) < 0.01,
        "plate_blank")
    f.name = "plate_blank"
    plate.name = "plate"
    adsk.doEvents()

    # ---- panel holes: stick, four bolts, six buttons, one sketch --------
    sk = ctx.root.sketches.add(plate_top_plane)
    sk.name = "panel_holes"
    z = top_cm
    stick = ctx.bound_circle(
        sk, (v("stick_x"), v("stick_y"), z), v("stick_hole") / 2, "stick_hole",
        x_pos="abs(stick_x)", v_pos="abs(stick_y)")
    r_bolt = v("bolt_hole") / 2
    br = v("stick_bolt_r")
    for k, (dx, dy) in enumerate(((br, 0), (-br, 0), (0, br), (0, -br))):
        axis_circle(ctx, sk, stick, dx, dy, r_bolt, "bolt_hole", "stick_bolt_r", k + 1)
    r_btn = v("btn_hole") / 2
    for name in BUTTONS:
        ctx.bound_circle(
            sk, (v(name + "_x"), v(name + "_y"), z), r_btn, "btn_hole",
            x_pos="abs(%s_x)" % name, v_pos="abs(%s_y)" % name)
        adsk.doEvents()
    if not sk.isFullyConstrained:
        loose = [i for i, c in enumerate(sk.sketchCurves.sketchCircles)
                 if not c.isFullyConstrained]
        raise RuntimeError("panel_holes loose circles: %s" % loose)
    if sk.profiles.count != 11:
        raise RuntimeError("panel_holes expected 11 profiles, got %d" % sk.profiles.count)
    f = ctx.sym_cut(ctx.all_profiles(sk), "plate_t * 3", [plate])
    f.name = "panel_holes"
    plate = body_named(ctx, "plate")
    adsk.doEvents()

    # ---- stiffener pocket on the plate underside ------------------------
    sk = ctx.root.sketches.add(plate_bot_plane)
    sk.name = "stiffener_pocket"
    ctx.bound_rect2(
        sk, (v("stick_x"), v("stick_y"), v("plate_bot_z")),
        v("stiff_w") / 2, v("stiff_d") / 2,
        u_size="stiff_w", v_size="stiff_d",
        u_pos=("stick_x", "stiff_w / 2"), v_pos=("stick_y", "stiff_d / 2"))
    if not sk.isFullyConstrained:
        raise RuntimeError("stiffener_pocket sketch not fully constrained")
    f = ctx.blind_cut(ctx.all_profiles(sk), "stiff_t", [plate], "pocket")
    f.name = "stiffener_pocket"
    plate = body_named(ctx, "plate")

    # ---- bolt-radius liveness, read back from the hole axes -------------
    def bolt_radii():
        pl = body_named(ctx, "plate")
        sx, sy = v("stick_x"), v("stick_y")
        out = []
        for face in pl.faces:
            cyl = adsk.core.Cylinder.cast(face.geometry)
            if cyl is None or abs(cyl.radius - v("bolt_hole") / 2) > 0.005:
                continue
            o = cyl.origin
            out.append(((o.x - sx) ** 2 + (o.y - sy) ** 2) ** 0.5 * 10)
        return sorted(out)

    r0 = bolt_radii()
    if len(r0) != 4 or any(abs(r - 16.0) > 0.01 for r in r0):
        raise RuntimeError("bolt holes at %s, wanted four at 16 mm" % r0)
    ctx.up.itemByName("stick_bolt_r").expression = "18 mm"
    adsk.doEvents()
    r1 = bolt_radii()
    ctx.up.itemByName("stick_bolt_r").expression = "16 mm"
    adsk.doEvents()
    r2 = bolt_radii()
    if any(abs(r - 18.0) > 0.01 for r in r1) or any(abs(r - 16.0) > 0.01 for r in r2):
        raise RuntimeError("stick_bolt_r not live: %s -> %s -> %s" % (r0, r1, r2))
    print("stick_bolt_r live: holes at %.2f -> %.2f -> %.2f mm" % (r0[0], r1[0], r2[0]))
    shell = body_named(ctx, "shell")
    plate = body_named(ctx, "plate")

    # ---- read-back ------------------------------------------------------
    for b in (shell, plate):
        bb = b.boundingBox
        print("%s: %.3f x %.3f x %.3f mm, z %.3f..%.3f, %.2f cm3, %d faces" % (
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
