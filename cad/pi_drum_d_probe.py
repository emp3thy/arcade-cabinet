"""Stage D mapping probe (plan task 6 step 1), kept for the record. Creates
the three art planes the livery sketches use, reads where sketch (0,0),
(1,0) and (0,1) land in model space on each, prints FH_RESULT, and deletes
the sketches and planes again. Run through cad/fusion_run.py's client
(scratchpad launcher); it prints no verdict because it changes nothing.

Measured 2026-10-22 (document arcade unit v1, after stage C):
  front  XZ offset -drum_r: origin (0, -80, 0), sketch x -> +x, sketch y -> -z
  left   YZ offset -drum_r: origin (-80, 0, 0), sketch x -> -z, sketch y -> +y
  right  YZ offset +drum_r: origin (+80, 0, 0), sketch x -> -z, sketch y -> +y
So the front art is placed as (u, -v) centred (0, -logo_z); a side figure
that faces the front (toward the player) is placed as (-v, u) centred
(-sil_z, 0) on both sides, since the two sides are mirror images.
"""
import json

import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    cbs = adsk.core.ValueInput.createByString
    out = {}
    made = []
    for name, base, off in (("front", root.xZConstructionPlane, "-drum_r"),
                            ("left", root.yZConstructionPlane, "-drum_r"),
                            ("right", root.yZConstructionPlane, "drum_r")):
        pin = root.constructionPlanes.createInput()
        pin.setByOffset(base, cbs(off))
        pl = root.constructionPlanes.add(pin)
        sk = root.sketches.add(pl)
        o = sk.sketchToModelSpace(adsk.core.Point3D.create(0, 0, 0))
        ex = sk.sketchToModelSpace(adsk.core.Point3D.create(1, 0, 0))
        ey = sk.sketchToModelSpace(adsk.core.Point3D.create(0, 1, 0))
        out[name] = {"origin_mm": [round(o.x * 10, 3), round(o.y * 10, 3), round(o.z * 10, 3)],
                     "sk_x": [round(ex.x - o.x, 3), round(ex.y - o.y, 3), round(ex.z - o.z, 3)],
                     "sk_y": [round(ey.x - o.x, 3), round(ey.y - o.y, 3), round(ey.z - o.z, 3)]}
        made.append((sk, pl))
    for sk, pl in made:
        sk.deleteMe()
        pl.deleteMe()
    out["bodies"] = root.bRepBodies.count
    out["timeline"] = des.timeline.count
    print("FH_RESULT " + json.dumps(out))
