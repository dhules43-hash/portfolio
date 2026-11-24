"""Reference-style shot list (fast cuts, macro/low/top-down cameras, lime x-ray highlights).
Usage: python3 shots.py <shot#|all> render | python3 shots.py <shot#> stills t1,t2 /tmp/prefix"""
import sys, os, math, random, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from core import *
import scenes as S
import bpy, bmesh
from mathutils import Vector, Euler

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
T0 = 0.
LIME = (.45, 1., .08)


def F(t):
    return int(round((t - T0) * FPS)) + 1


# (start, end) in seconds — aligned to the narration word timings
SHOTS = [
    (0.00, 1.75), (1.75, 2.90), (2.90, 4.20), (4.20, 5.60), (5.60, 6.95), (6.95, 8.80), (8.80, 10.90), (10.90, 12.95), (12.95, 15.00),
    (15.00, 16.05), (16.05, 17.60), (17.60, 19.00), (19.00, 20.35), (20.35, 21.50), (21.50, 23.45), (23.45, 24.95), (24.95, 26.40), (26.40, 29.10)]


def nfr(i):
    a, b = SHOTS[i - 1]; return int(round(b * FPS)) - int(round(a * FPS))


def beats(t0, t1, period=.82):
    k = math.ceil(t0 / period); out = []
    while k * period < t1: out.append(k * period); k += 1
    return out


def highlight_mat(name="hl", col=LIME, alpha=.55, strength=3.):
    """Zack-style glowing translucent highlight on the object being explained."""
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); mix = nt.nodes.new("ShaderNodeMixShader"); tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = (*col, 1); em.inputs[1].default_value = strength
    mix.inputs[0].default_value = alpha
    nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(em.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], out.inputs["Surface"])
    m["em"] = em.name
    return m


def pulse(m, f0, f1, lo=1.5, hi=5., period=12):
    em = m.node_tree.nodes[m["em"]].inputs[1]
    for f in range(f0, f1 + 1, period // 2):
        em.default_value = hi if ((f - f0) // (period // 2)) % 2 == 0 else lo; em.keyframe_insert("default_value", frame=f)


def bright_grade():
    sc = bpy.context.scene
    try: sc.view_settings.look = 'AgX - Punchy'
    except Exception: pass
    sc.view_settings.exposure = .25


# ------------------------------------------------------------------ sets
def op_room():
    tile = S.tile_mat("otile", (.45, .75, .78), scale=7)
    rbox((0, 2.2, 1.6), (8, .1, 3.2), tile, 0); rbox((-2.4, 0, 1.6), (.1, 8, 3.2), tile, 0)
    rbox((0, 0, -.05), (8, 8, .1), S.checker_mat("ofloor", (.85, .85, .8), (.15, .2, .2), 18), 0)
    steel = mat("steel", (.75, .75, .78), .25, metal=1)
    rbox((0, .55, .85), (1.9, .7, .08), steel, .01)
    rbox((0, .55, .89), (1.85, .66, .02), mat("sheet", (.15, .5, .45), .7, sheen=.5), .01)
    for x in (-.8, .8): prim("cylinder", (x, .55, .42), (.03, .03, .42), steel, vertices=16)
    prim("cylinder", (.2, -.05, .25), (.2, .2, .025), steel, vertices=32)
    win = rbox((-2.34, .4, 1.8), (.02, 1.4, 1.2), mat("osky", (.6, .85, 1.), emit=5.), 0)
    light('SUN', (-6, 1, 4), 5., (1, .93, .82), .04, target=(0, .5, .9), name="sun")
    light('AREA', (1.5, -1.5, 2.2), 120, (1, .97, .92), 2.5, target=(0, .4, 1.), name="fill")
    S.world_color((.5, .7, .9), .8) if hasattr(S, "world_color") else world_color((.5, .7, .9), .8)
    return steel


def corridor():
    rbox((0, 0, -.05), (40, 3.2, .1), S.checker_mat("cfloor", (.86, .84, .76), (.12, .3, .3), 1.6, .15, .7), 0)
    wl = mat("cwall", (.62, .8, .88), .6, bump=.05); wd = mat("cwainscot", (.1, .32, .42), .35, coat=.5)
    for y, sg in ((1.6, 1), (-1.6, -1)):
        rbox((0, y, 1.7), (40, .1, 3.4), wl, 0); rbox((0, y - sg * .06, .6), (40, .04, 1.2), wd, 0)
    rbox((0, 0, 3.4), (40, 3.2, .1), mat("ceil", (.9, .9, .88), .8), 0)
    for x in range(-18, 19, 3):
        prim("cylinder", (x, 0, 3.3), (.18, .18, .05), mat("clamp", (1, .95, .85), emit=10), vertices=24)
        light('POINT', (x, 0, 3.1), 70, (1, .93, .8), .3)
    for x in range(-17, 18, 3):
        rbox((x, 1.53, 1.05), (.9, .06, 2.1), S.wood_mat("cdoor", (.35, .17, .07), 1.5), .01)
    for x in range(-16, 19, 3):
        rbox((x, -1.56, 1.9), (1.0, .02, 1.3), mat("cwin", (.7, .9, 1.), emit=4), 0)
    light('SUN', (0, -5, 4), 6., (1, .88, .7), .03, target=(1, 1, 0), name="sun")
    world_color((.5, .7, .9), .6)


def xray_room():
    rbox((0, 0, -.05), (10, 10, .1), mat("xfloor", (.12, .13, .14), .3, coat=.4), 0)
    wall = S.tile_mat("xtile", (.2, .3, .36), scale=5)
    rbox((0, 2.5, 1.6), (10, .1, 3.2), wall, 0); rbox((-2.5, 0, 1.6), (.1, 10, 3.2), wall, 0)
    world_color((.01, .02, .03), .5)
    metal = mat("xmetal", (.25, .27, .3), .3, metal=.9); cream = mat("xcream", (.75, .72, .62), .45, coat=.3)
    prim("cylinder", (-1.3, .6, 1.2), (.06, .06, 1.2), metal, vertices=24); rbox((-1.3, .6, .05), (.6, .6, .1), metal, .02)
    rbox((-.95, .6, 1.55), (.75, .1, .1), metal, .02)
    bulb = prim("uv_sphere", (-.55, .6, 1.5), (.16, .16, .13), mat("bulb", (.6, .8, 1.), .05, trans=.8), sub=1)
    prim("cylinder", (-.55, .6, 1.5), (.05, .05, .25), cream, rot=(0, math.pi / 2, 0), vertices=24)
    for x in (-.85, -.25):
        for k in range(6):
            o = prim("torus", (x + k * .02, .6, 1.5), (.05, .05, .05), mat("coil", (.75, .45, .15), .3, metal=1), rot=(0, math.pi / 2, 0), major_radius=1, minor_radius=.2, sub=0)
    light('AREA', (1.5, -1.5, 2.5), 90, (.6, .75, 1.), 2., target=(.4, .4, 1.2), name="cool")
    light('AREA', (-1, 2.2, 2.6), 70, (.4, .6, 1.), 1.5, target=(.4, .4, 1.2), name="rimx")
    return bulb


def stage():
    rbox((0, 0, .25), (6, 3, .5), mat("stage", (.2, .08, .05), .2, coat=.8), .02)
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=120, y_segments=4, size=1.)
    for v in bm.verts: v.co = Vector((v.co.x * 4, .08 * math.sin(v.co.x * 40), (v.co.y + 1) * 2.2 + .5))
    me = bpy.data.meshes.new("curtain"); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    cu = bpy.data.objects.new("curtain", me); link(cu); cu.location = (0, 1.4, 0); me.materials.append(mat("curtain", (.55, .03, .05), .55, sheen=.8))
    text("NOBEL PRIZE  1956", (0, 1.25, 3.4), .32, mat("banner", (1., .78, .35), .2, metal=1., emit=.6, emit_col=(1, .7, .3)), extrude=.03)
    light('SPOT', (0, -2.5, 5.5), 2500, (1, .92, .8), .3, target=(0, 0, 1.4), spot=math.radians(24), name="spot")
    light('AREA', (0, 1.0, 3.5), 300, (1, .8, .5), 2, target=(0, 0, 1.4), name="back")
    light('AREA', (3, -2, 2), 120, (.5, .6, 1.), 2, target=(0, 0, 1.4), name="cfill")
    world_color((.005, .01, .03), 1.)


def seated_doc(loc=(.2, -.05, -.43)):
    doc = doctor("Doc", loc, math.pi)
    for f in (1, 400):
        doc.pose(f, thigh_L=(-88, 0, 0), thigh_R=(-88, 0, 0), shin_L=(88, 0, 0), shin_R=(88, 0, 0))
    return doc


def macro_arm(O, ghost=False):
    """Thicker, rounder forearm prop for macro shots; optional translucent skin + lime vein highlight."""
    skin = skin_mat("armskin", (.74, .44, .3))
    arm, gh, vp = S.arm_prop(O, skin)
    me = arm.data
    for i, r in enumerate(me.skin_vertices[0].data):
        r.radius = (r.radius[0] * 1.15, max(r.radius[1], r.radius[0] * .82) * 1.1)
    rbox(Vector(O) + Vector((.3, 0, -.065)), (1.8, 1.2, .02), mat("cloth", (.1, .42, .38), .85, sheen=.6, bump=.4, bump_scale=300), .005)
    if ghost:
        arm.hide_render = True; gh.data = me.copy(); gh.data.materials.clear(); gh.data.materials.append(S.ghost_mat("armghost", (1., .72, .55), .32, .3))
    else:
        gh.hide_render = True
    return arm, gh, vp


def catheter_on(vp, extra=True):
    pts = ([vp[0] + Vector((-.14, -.035, .07)), vp[0] + Vector((-.03, -.012, .012))] if extra else []) + vp[1:]
    return curve_tube(pts, .0042, mat("cath", (1., .6, .2), .25, coat=.8, emit=4., emit_col=(1, .55, .1)), "cath")


# ------------------------------------------------------------------ shots
def shot1():          # HOOK: doctor holds up a long tube, low wide angle, bright window
    S.office(); n = nfr(1)
    light('AREA', (0, -1.6, 2.3), 220, (1, .95, .88), 2.5, target=(0, 0, 1.6), name="key2")
    doc = doctor("Doc", (0, 0, 0), 0)
    rub = mat("rubber", (.8, .48, .16), .3, coat=.7, sss=.2)
    hd = Vector(JOINTS["hd.R"])
    tube = curve_tube([hd + Vector((0, -.02, .02)), hd + Vector((.05, -.06, -.2)), hd + Vector((.12, -.05, -.45)), hd + Vector((.2, -.02, -.5)), hd + Vector((.25, .0, -.3))], .0055, rub, "tube")
    doc.attach(tube, "hand.R", rest_space=True)
    doc.pose(1, uarm_R=(-40, 0, 20), farm_R=(-70, 0, 0), head=(-6, 0, 0), chest=(-3, 0, 0))
    doc.pose(F(.6), uarm_R=(-52, 0, 30), farm_R=(-70, 0, 0), head=(-6, -18, 0))
    doc.pose(n, uarm_R=(-55, 0, 32), farm_R=(-72, 0, 0), head=(-6, -22, 0))
    doc.brows(1, .4); doc.brows(F(.7), .9); doc.mouth(1, .1, 1.3); doc.blink([F(1.2)])
    cam = Cam(fstop=1.6)
    cam.shot(1, n, (.3, -1.15, 1.2), (.2, -.9, 1.28), (.05, 0, 1.5), (.03, 0, 1.55), 24, 26)
    cam.handheld(.01); bright_grade()


def shot2():          # top-down: hands with the tube beside the bare forearm
    op_room(); n = nfr(2)
    doc = seated_doc()
    doc.pose(1, uarm_L=(-62, 0, -8), farm_L=(-25, 0, 0), uarm_R=(-58, 0, 12), farm_R=(-45, 0, 0), head=(30, 0, 0), chest=(18, 0, 0))
    doc.pose(n, uarm_R=(-60, 0, 14), farm_R=(-55, 0, 0))
    rub = mat("rubber", (.8, .48, .16), .3, coat=.7, sss=.2)
    for k in range(3): prim("torus", (.05 + k * .004, .45, .91 + k * .006), (.07, .07, .07), rub, major_radius=1, minor_radius=.05, sub=0, major_segments=48)
    cam = Cam(fstop=2.8)
    cam.shot(1, n, (.95, .95, 1.95), (.85, .85, 1.85), (.2, .3, 1.0), (.2, .32, .98), 22, 24)
    cam.handheld(.004); bright_grade()


def _arm_set(ghost):
    O = Vector((0, 0, 1.0))
    three_point(O + Vector((.25, 0, 0)), 40, 12, 40, scale=.5)
    light('SPOT', O + Vector((.2, -.1, 1.2)), 350, (1, .96, .9), .2, target=O + Vector((.25, 0, 0)), spot=math.radians(55))
    world_color((.35, .55, .7), .5)
    arm, gh, vp = macro_arm(O, ghost)
    return O, arm, gh, vp


def shot3():          # macro cutaway: lime vein, catheter tip slides in
    n = nfr(3); O, arm, gh, vp = _arm_set(True)
    hl = highlight_mat("veinhl"); vein = curve_tube(vp, .0075, hl, "vein"); pulse(hl, 1, n)
    cath = catheter_on(vp); grow(cath, 1, n, .12, .42)
    cam = Cam(fstop=4.)
    cam.shot(1, n, O + Vector((.0, -.26, .15)), O + Vector((.12, -.24, .16)), vp[0] + Vector((-.02, 0, 0)), vp[1] + Vector((.04, 0, 0)), 26, 28)
    cam.handheld(.003); bright_grade()


def shot4():          # boss forbids: low wide angle, finger at lens
    S.office(); n = nfr(4)
    light('AREA', (0, -1.5, 2.4), 200, (1, .95, .88), 2.5, target=(-.3, 0, 1.6), name="key2")
    b = boss("Boss", (-.2, .3, 0), 0)
    b.pose(1, uarm_R=(-30, 0, -5), farm_R=(-60, 0, 0), chest=(6, 0, 0), head=(-10, 0, 0))
    b.pose(F(4.45), uarm_R=(-88, 0, -6), farm_R=(-6, 0, 0), chest=(12, 0, 0), head=(-14, 0, 0))
    for k, f in enumerate(range(F(4.6), n, 5)): b.pose(f, farm_R=(-6 - 10 * (k % 2), 0, 0))
    b.brows(1, -1.); b.talk(F(4.3), F(5.45), 1.); b.blink([8])
    cam = Cam(fstop=2.)
    cam.shot(1, n, (.12, -.75, 1.05), (.06, -.62, 1.1), (-.2, .3, 1.55), (-.2, .3, 1.6), 18, 20)
    cam.handheld(.012); bright_grade()


def shot5():          # numbing injection macro
    n = nfr(5); O, arm, gh, vp = _arm_set(False)
    steel = mat("steel", (.8, .8, .82), .2, metal=1)
    syr = empty("syringe"); glass = mat("glass", (.9, .97, 1.), .03, trans=1., coat=1.)
    for p, s_, m_ in (((0, 0, .07), (.011, .011, .055), glass), ((0, 0, .008), (.006, .006, .008), mat("hub", (.1, .6, .5), .3)), ((0, 0, -.03), (.0011, .0011, .03), steel)):
        o = prim("cylinder", p, s_, m_, vertices=24); o.parent = syr
    liq = prim("cylinder", (0, 0, .06), (.009, .009, .04), mat("liq", (.85, .95, 1.), .05, trans=.9, emit=.2), vertices=24); liq.parent = syr
    pl = prim("cylinder", (0, 0, .16), (.0045, .0045, .06), mat("plunger", (.9, .9, .9), .4), vertices=16); pl.parent = syr
    tip = vp[0] + Vector((.06, 0, .0)); syr.scale = (.6,) * 3; syr.rotation_euler = (math.radians(-35), math.radians(-30), 0)
    key(syr, 1, location=tip + Vector((.08, -.12, .16))); key(syr, F(6.05), location=tip + Vector((.035, -.045, .05)))
    key(syr, n, location=tip + Vector((.035, -.045, .05)))
    key(liq, F(6.1), scale=(.009, .009, .04)); key(liq, n, scale=(.009, .009, .01))
    key(pl, F(6.1), location=(0, 0, .16)); key(pl, n, location=(0, 0, .11))
    hl = highlight_mat("numb", (.4, .85, 1.), .5, 3.)
    glow = prim("uv_sphere", tip + Vector((0, 0, .005)), (.001,) * 3, hl, sub=1)
    key(glow, F(6.1), scale=(.001,) * 3); key(glow, n, scale=(.035, .035, .012))
    cam = Cam(fstop=3.5)
    cam.shot(1, n, tip + Vector((.12, -.2, .07)), tip + Vector((.09, -.16, .06)), tip + Vector((.01, 0, .02)), tip + Vector((0, 0, .015)), 24, 28)
    cam.handheld(.003); bright_grade()


def shot6():          # cutaway at the elbow: vein highlight pulses, catheter advances
    n = nfr(6); O, arm, gh, vp = _arm_set(True)
    hl = highlight_mat("veinhl"); curve_tube(vp, .0075, hl, "vein"); pulse(hl, 1, n)
    cath = catheter_on(vp); grow(cath, 1, n, .4, .62)
    art = curve_tube([p + Vector((0, .02, -.01)) for p in vp], .005, mat("art", (.8, .06, .06), .3, coat=.6, emit=.6, emit_col=(.8, .05, .05)), "artery")
    cam = Cam(fstop=4.5)
    cam.shot(1, n, vp[1] + Vector((-.08, -.2, .14)), vp[1] + Vector((.02, -.17, .12)), vp[1], vp[2], 24, 26)
    cam.handheld(.003); bright_grade()


def shot7():          # long slide along the translucent arm as the catheter travels
    n = nfr(7); O, arm, gh, vp = _arm_set(True)
    hl = highlight_mat("veinhl", alpha=.45); curve_tube(vp, .0075, hl, "vein")
    cath = catheter_on(vp); grow(cath, 1, n, .6, 1.)
    cam = Cam(fstop=5.)
    cam.shot(1, n, vp[1] + Vector((0, -.22, .13)), vp[-1] + Vector((-.02, -.2, .14)), vp[2], vp[-1], 22, 22)
    cam.handheld(.003); bright_grade()


def shot8():          # inside the vein: catheter tip leads, cells stream past
    n = nfr(8)
    path = [Vector((i * 2.0, math.sin(i * .9) * .35, math.cos(i * .6) * .25)) for i in range(12)]
    wall = mat("veinwall", (.5, .04, .06), .35, sss=.6, sss_rad=(1, .2, .1), coat=.5, bump=1.2, bump_scale=6)
    curve_tube(path, 1.0, wall, "tunnel", res=12)
    cell_m = mat("rbc", (.75, .04, .05), .3, sss=.5, sss_rad=(1, .2, .1), coat=.6)
    rnd = random.Random(3)
    seg = lambda u: (lambda i: path[i].lerp(path[i + 1], u * 11 - i))(min(10, int(u * 11)))
    for i in range(70):
        c = seg(rnd.uniform(0, .95)); off = Vector((0, rnd.uniform(-.6, .6), rnd.uniform(-.6, .6)))
        if off.length > .7: off *= .7 / off.length
        o = prim("torus", c + off, (.13, .13, .09), cell_m, rot=(rnd.random() * 3, rnd.random() * 3, 0), major_radius=1, minor_radius=.55, sub=1, major_segments=24, minor_segments=12)
        key(o, 1, location=c + off); key(o, n, location=c + off + Vector((-3.5, 0, 0)))
    cath = curve_tube([p + Vector((0, 0, -.35)) for p in path], .07, mat("cath", (1., .6, .2), .25, coat=.8, emit=3., emit_col=(1, .5, .1)), "cath3")
    grow(cath, 1, n, .1, .62)
    tl = light('POINT', path[1], 140, (1, .65, .35), .2)
    for f in range(1, n + 1, 6): key(tl, f, location=seg(.1 + .52 * (f - 1) / max(1, n - 1)) + Vector((0, 0, -.05)))
    light('POINT', path[0], 40, (1, .4, .3), .5)
    cam = Cam(fstop=2.8)
    cam.shot(1, n, seg(.03) + Vector((0, 0, .12)), seg(.5) + Vector((0, 0, .12)), seg(.1) + Vector((0, 0, -.2)), seg(.62) + Vector((0, 0, -.25)), 18, 18)
    bright_grade()


def shot9():          # ghost body: lime path up the arm, past the shoulder
    n = nfr(9); G = Vector((0, 0, 0))
    world_color((.0, .02, .05), 1.)
    d = doctor("Ghost", tuple(G), 0)
    gm = S.ghost_mat("ghostbody", (.4, .75, 1.), .05, .3)
    for o in bpy.data.objects:
        if o.type == 'MESH' and (o == d.body or o.parent == d.rig or (o.parent and o.parent.parent == d.rig)):
            o.data.materials.clear(); o.data.materials.append(gm)
    d.pose(1, uarm_L=(-10, 0, -25), farm_L=(-10, 0, 0)); d.pose(n, uarm_L=(-10, 0, -25), farm_L=(-10, 0, 0))
    hp = Vector((.04, -.02, 1.3))
    hroot, hv = S.heart_model(hp, .085, mat("hglow", (.8, .05, .08), .3, sss=.3, coat=.6, emit=1.5, emit_col=(1, .05, .1)))
    beat(hroot, (1, 1, 1), [F(t) for t in beats(12.95, 15.0)], .1)
    bpy.context.view_layer.update()
    W = lambda j: d.rig.matrix_world @ Vector(JOINTS[j])
    sh, el, wr = W("sh.L"), W("el.L"), W("wr.L")
    pts = [el + (wr - el) * .1, el + Vector((0, -.01, 0)), (el + sh) / 2, sh + Vector((-.02, 0, 0)), Vector(JOINTS["chest"]) + Vector((.1, -.02, .08)), hp + Vector((-.03, -.01, .05)), hp + Vector((-.02, -.01, 0))]
    hl = highlight_mat("pathhl", alpha=.85, strength=6.)
    gc = curve_tube(pts, .007, hl, "gcath"); grow(gc, 1, n, .15, 1.)
    cam = Cam(fstop=2.4)
    cam.shot(1, n, (.75, -1.15, 1.45), (.35, -.62, 1.36), (.22, 0, 1.28), hp, 24, 30)
    bright_grade()


def shot10():         # beating heart macro, catheter tip arrives
    n = nfr(10); world_color((.02, .0, .01), 1.)
    hp = Vector((0, 0, 1.))
    hroot, hv = S.heart_model(hp, .5)
    beat(hroot, (1, 1, 1), [F(t) for t in beats(15.0, 16.05, .55)], .09)
    cath = curve_tube([hp + Vector((-.14, .03, 1.2)), hp + Vector((-.14, .03, .62)), hp + Vector((-.12, .0, .3)), hp + Vector((-.06, -.05, .1))], .012,
                      mat("cath", (1., .6, .2), .25, coat=.8, emit=4., emit_col=(1, .55, .1)), "cath")
    grow(cath, 1, F(15.7), .3, 1.)
    three_point(hp, 260, 60, 400)
    light('POINT', hp + Vector((0, -.6, .2)), 60, (1, .3, .25), .3)
    cam = Cam(fstop=2.2)
    cam.shot(1, n, hp + Vector((.75, -1.15, .45)), hp + Vector((.25, -.95, .35)), hp + Vector((-.05, 0, .25)), hp + Vector((-.08, 0, .2)), 30, 34)
    cam.handheld(.006); bright_grade()


def _walker(n, x0, speed, cadence=2.1):
    doc = doctor("Doc")
    rub = mat("rubber", (.8, .48, .16), .3, coat=.7, sss=.2)
    el = Vector(JOINTS["el.L"]); wr = Vector(JOINTS["wr.L"]); p0 = el + (wr - el) * .15 + Vector((-.03, -.035, 0))
    hang = curve_tube([p0, p0 + Vector((-.01, -.04, -.12)), p0 + Vector((0, -.03, -.3)), p0 + Vector((.02, 0, -.42))], .0045, rub, "hang")
    doc.attach(hang, "farm.L", rest_space=True)
    tape = prim("cube", tuple(p0 + Vector((.012, -.012, 0))), (.025, .004, .02), mat("tape", (.95, .93, .85), .7), smooth=False); doc.attach(tape, "farm.L", rest_space=True)
    x1 = x0 + speed * n / FPS
    doc.walk(1, n, (x0, 0, 0), (x1, 0, 0), cadence=cadence, arm=14)
    for f in range(1, n + 1, 2): doc.pose(f, uarm_L=(-8, 0, -6), farm_L=(-35, 0, 0))
    doc.brows(1, .5); doc.blink([20])
    return doc, x1


def shot11():         # ground-level: feet + dangling tube walking at the lens
    corridor(); n = nfr(11)
    doc, x1 = _walker(n, -1.2, 1.1)
    cam = Cam(fstop=2.)
    cam.shot(1, n, (1.2, -.12, .1), (1.7, -.12, .11), (-1.0, 0, .45), (x1 - .2, 0, .55), 16, 16)
    set_interp(cam.o, 'LINEAR'); set_interp(cam.t, 'LINEAR'); cam.handheld(.01); bright_grade()


def shot12():         # side tracking
    corridor(); n = nfr(12)
    doc, x1 = _walker(n, 3., 1.3)
    cam = Cam(fstop=2.2)
    cam.shot(1, n, (3.1, -1.3, 1.2), (x1 + .1, -1.3, 1.25), (3.25, 0, 1.15), (x1 + .25, 0, 1.2), 22, 22)
    set_interp(cam.o, 'LINEAR'); set_interp(cam.t, 'LINEAR'); cam.handheld(.01); bright_grade()


def shot13():         # over-shoulder push into the X-RAY door, door swings open
    corridor(); n = nfr(13)
    rbox((19.5, 0, 2.85), (.02, 1.1, .45), mat("signbg", (.02, .03, .05), .3), .01)
    text("X-RAY", (19.47, 0, 2.85), .32, mat("xsign", (.4, .85, 1.), emit=10), rot=(math.pi / 2, 0, -math.pi / 2), extrude=.01)
    hinge = empty("hinge", (19.55, -.7, 0))
    door = rbox((19.55, 0, 1.2), (.08, 1.4, 2.4), mat("xdoor", (.75, .8, .8), .4, coat=.4), .01); door.parent = hinge; door.location = (0, .7, 1.2)
    rbox((21.5, 0, 1.3), (3.5, 3, .02), mat("xglow", (.35, .7, 1.), emit=6), 0, rot=(0, math.pi / 2, 0))
    key(hinge, 1, rotation_euler=(0, 0, 0)); key(hinge, F(19.7), rotation_euler=(0, 0, 0)); key(hinge, n, rotation_euler=(0, 0, math.radians(-75)))
    doc, x1 = _walker(n, 16.4, 1.1)
    cam = Cam(fstop=2.6)
    cam.shot(1, n, (15.6, -.45, 1.75), (17.2, -.35, 1.7), (19.4, 0, 1.9), (19.6, 0, 1.6), 22, 26)
    set_interp(cam.o, 'LINEAR'); cam.handheld(.01); bright_grade()


def shot14():         # machine powers up, bulb overload, flash
    n = nfr(14); bulb = xray_room()
    b = bsdf(bulb.data.materials[0]); es = b.inputs["Emission Strength"]; b.inputs["Emission Color"].default_value = (.5, .75, 1, 1)
    for f, v in ((1, .5), (F(21.1), 6.), (F(21.35), 12.)): es.default_value = v; es.keyframe_insert("default_value", frame=f)
    fl = light('AREA', (-.2, -.8, 1.6), 0, (.7, .85, 1.), 3., target=(-.55, .6, 1.5), name="flash")
    for f, e in ((1, 0), (F(21.3), 0), (F(21.4), 3000), (n, 600)): key(fl.data, f, energy=e)
    cam = Cam(fstop=2.)
    cam.shot(1, n, (.1, -.75, 1.4), (-.1, -.5, 1.45), (-.6, .6, 1.5), (-.58, .6, 1.5), 22, 26)
    cam.handheld(.008); bright_grade()


def shot15():         # the fluoroscope image: catheter highlighted inside the heart
    n = nfr(15); xray_room()
    Sx = Vector((.45, .35, 1.32))
    rbox(Sx, (.75, .05, .85), mat("frame", (.05, .05, .06), .4), .01)
    rbox(Sx + Vector((0, -.03, 0)), (.66, .01, .76), mat("screen", (.0, .04, .06), .2, emit=.5, emit_col=(.05, .25, .35)), 0)
    imgs, xh, xc = S.xray_image(Sx + Vector((0, -.04, -.02)), .55, 1.)
    beat(xh, xh.scale[:], [F(t) for t in beats(21.5, 23.45)], .08)
    hl = highlight_mat("xhl", alpha=.9, strength=7.)
    xc.data.materials.clear(); xc.data.materials.append(hl); pulse(hl, F(22.0), n, 3, 9, 10)
    grow(xc, 1, F(22.4), .35, 1.)
    cam = Cam(fstop=4.)
    cam.shot(1, n, Sx + Vector((.12, -.7, .02)), Sx + Vector((-.02, -.36, .1)), Sx + Vector((0, 0, .02)), Sx + Vector((-.03, 0, .1)), 26, 28)
    cam.handheld(.004)


def shot16():         # boss furious, red light, low close-up
    S.office(red=.4); n = nfr(16)
    light('AREA', (-.3, -1.2, 2.3), 160, (1, .15, .1), 2, target=(-.5, 0, 1.6), name="redkey")
    b = boss("Boss", (-.45, .1, 0), math.pi / 2 - .45)
    sb = bsdf(b.mats["skin"]).inputs["Base Color"]
    sb.default_value = (.74, .44, .33, 1); sb.keyframe_insert("default_value", frame=1); sb.default_value = (.88, .2, .14, 1); sb.keyframe_insert("default_value", frame=F(24.4))
    b.brows(1, -1.); b.talk(2, n - 3, 1.1)
    b.pose(1, chest=(10, 0, 0), head=(-8, 0, 0), uarm_R=(-75, 0, -10), farm_R=(-15, 0, 0))
    for k, f in enumerate(range(3, n, 4)): b.pose(f, farm_R=(-10 - 15 * (k % 2), 0, 0), head=(-12 + 5 * (k % 2), 0, 0))
    cam = Cam(fstop=1.8)
    cam.shot(1, n, (.12, -.7, 1.45), (.04, -.55, 1.52), (-.45, .1, 1.68), (-.45, .1, 1.72), 20, 22)
    cam.handheld(.016); bright_grade()


def shot17():         # gold medal macro "1956"
    n = nfr(17); world_color((.005, .01, .03), 1.)
    gold = mat("gold", (1., .72, .3), .16, metal=1., bump=.15, bump_scale=300)
    M = Vector((0, 0, 1.0)); med = empty("medal", M)
    for kind, sc, kw in (("cylinder", (.1, .1, .008), dict(vertices=96)),):
        disc = prim(kind, (0, 0, 0), sc, gold, rot=(math.pi / 2, 0, 0), **kw); disc.parent = med; disc.location = (0, 0, 0)
    rim = prim("torus", (0, 0, 0), (.1, .1, .1), gold, rot=(math.pi / 2, 0, 0), major_radius=1, minor_radius=.06, sub=1, major_segments=96); rim.parent = med; rim.location = (0, 0, 0)
    prof = prim("uv_sphere", (0, 0, 0), (.035, .012, .045), gold, sub=1); prof.parent = med; prof.location = (-.01, -.008, .015)
    t = text("1956", (0, 0, 0), .028, gold, extrude=.002); t.parent = med; t.location = (0, -.009, -.045)
    t2 = text("NOBEL", (0, 0, 0), .018, gold, extrude=.0015); t2.parent = med; t2.location = (0, -.009, .072)
    key(med, 1, rotation_euler=(0, 0, math.radians(-50))); key(med, n, rotation_euler=(0, 0, math.radians(25)))
    light('AREA', M + Vector((-.4, -.5, .4)), 45, (1, .9, .75), .6, target=M)
    light('AREA', M + Vector((.5, -.3, -.1)), 18, (.6, .7, 1.), .5, target=M)
    light('AREA', M + Vector((0, .4, .3)), 30, (1, 1, 1), .3, target=M)
    rnd = random.Random(9); sp = mat("sparkle", (1, .85, .5), emit=20)
    for i in range(35):
        p = M + Vector((rnd.uniform(-.3, .3), rnd.uniform(-.1, .35), rnd.uniform(-.35, .35)))
        o = prim("ico_sphere", p, (.002,) * 3, sp, subdivisions=1, smooth=False)
        f0 = rnd.randint(1, max(2, n - 10)); key(o, 1, scale=(0, 0, 0)); key(o, f0, scale=(0, 0, 0)); key(o, f0 + 5, scale=(.003,) * 3); key(o, f0 + 14, scale=(0, 0, 0))
    cam = Cam(fstop=2.8)
    cam.shot(1, n, M + Vector((.12, -.28, .03)), M + Vector((-.04, -.22, 0)), M, M, 40, 50)
    cam.handheld(.002)


def shot18():         # stage reveal, confetti, applause
    stage(); n = nfr(18)
    gold = mat("gold", (1., .72, .3), .16, metal=1.)
    old = doctor("Old", (0, 0, .5), 0, old=True)
    m2 = prim("cylinder", (0, 0, 0), (.05, .05, .006), gold, rot=(math.pi / 2, 0, 0), vertices=64)
    m2.location = Vector(JOINTS["hd.R"]) + Vector((0, -.03, -.02)); old.attach(m2, "hand.R", rest_space=True)
    old.pose(1, uarm_R=(-20, 0, 8), farm_R=(-40, 0, 0), chest=(-4, 0, 0))
    old.pose(F(27.2), uarm_R=(-100, 0, 30), farm_R=(-40, 0, 0), head=(-8, 0, 0), uarm_L=(-10, 0, -10))
    old.pose(n, uarm_R=(-110, 0, 32), farm_R=(-35, 0, 0), head=(-10, 0, 0))
    old.mouth(1, .3, 1.5); old.brows(1, .5); old.lids(1, -18); old.blink([F(28.0)])
    rnd = random.Random(4)
    cm = [mat(f"conf{i}", c, .3, metal=.6, emit=.3) for i, c in enumerate(((1, .75, .25), (1, 1, 1), (.9, .2, .25), (.25, .45, 1)))]
    for i in range(110):
        p = Vector((rnd.uniform(-2.2, 2.2), rnd.uniform(-1.8, .9), rnd.uniform(2.5, 5.)))
        o = prim("plane", p, (.018, .01, 1), rnd.choice(cm), smooth=False); r0 = Euler((rnd.random() * 6, rnd.random() * 6, 0))
        key(o, 1, location=p, rotation_euler=r0); key(o, n, location=p + Vector((rnd.uniform(-.3, .3), 0, -rnd.uniform(2., 3.2))), rotation_euler=Euler((r0.x + 9, r0.y + 6, 0)))
    cam = Cam(fstop=2.6)
    cam.shot(1, n, (.3, -1.1, 1.95), (.15, -4.4, 2.3), (0, 0, 2.0), (0, 0, 1.95), 24, 30)
    cam.handheld(.006)


def beat(o, base, fbeats, amp=.07):
    S.beat(o, base, fbeats, amp)


SHOT_FUNCS = [shot1, shot2, shot3, shot4, shot5, shot6, shot7, shot8, shot9, shot10, shot11, shot12, shot13, shot14, shot15, shot16, shot17, shot18]


def build(i):
    global T0
    T0 = SHOTS[i - 1][0]
    reset(nfr(i)); SHOT_FUNCS[i - 1]()
    return bpy.context.scene


if __name__ == "__main__":
    i = int(sys.argv[1]); mode = sys.argv[2]
    build(i)
    if mode == "render":
        render(os.path.join(ROOT, "renders", "shots", f"sh{i:02d}"))
    elif mode == "stills":
        for t in sys.argv[3].split(","): still(f"{sys.argv[4]}_{i:02d}_{t}.png", min(nfr(i), F(float(t))))
