"""Deterministic offline chrome hero. Run with Blender --background --python.

Nothing in this scene runs in the website. All motion is periodic over 384 frames.
"""
import bpy, math, random, os, sys, json
from mathutils import Vector, Euler, Matrix
from pathlib import Path

ROOT = Path(os.environ.get("ALI_HERO_RENDER_DIR", str(Path(__file__).resolve().parent.parent / "work" / "hero-render"))).resolve()
(ROOT / "frames").mkdir(parents=True, exist_ok=True)
TAU = 2 * math.pi
FRAMES = 384
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
mode = args[0] if args else 'preview'
size = int(args[1]) if len(args) > 1 else 768
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 32 if mode == 'preview' else 24
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 8
scene.cycles.transmission_bounces = 5
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'METAL'
    prefs.get_devices()
    for device in prefs.devices:
        device.use = device.type == 'METAL'
    if any(d.type == 'METAL' for d in prefs.devices):
        scene.cycles.device = 'GPU'
except Exception as err:
    print('CPU fallback', err)
scene.render.resolution_x = size
scene.render.resolution_y = size
scene.render.resolution_percentage = 100
scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = FRAMES
scene.render.film_transparent = True
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.image_settings.color_depth = '8'
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.view_settings.exposure = -.1
scene.world.use_nodes = True
world = scene.world.node_tree.nodes.get('Background')
world.inputs['Color'].default_value = (0.065, 0.071, 0.092, 1)
world.inputs['Strength'].default_value = 0.35

def principled(name, color, metal=0, rough=.1):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Metallic'].default_value = metal
    shader.inputs['Roughness'].default_value = rough
    return material, shader

silver, silver_bsdf = principled('Forged mirror silver', (.76, .78, .85), 1, .085)
silver_bsdf.inputs['Coat Weight'].default_value = .3
silver_bsdf.inputs['Coat Roughness'].default_value = .075
dark_chrome, _ = principled('Silver in the folded gutters', (.39, .4, .47), 1, .12)
cage_material, _ = principled('Fine chrome cage', (.59, .55, .73), 1, .09)
glass, glass_bsdf = principled('Violet crystal shell', (.24, .035, .54), .18, .115)
glass_bsdf.inputs['Transmission Weight'].default_value = .85
glass_bsdf.inputs['IOR'].default_value = 1.46
glass_bsdf.inputs['Coat Weight'].default_value = .08
glass_bsdf.inputs['Coat Roughness'].default_value = .055
absorption = glass.node_tree.nodes.new('ShaderNodeVolumeAbsorption')
absorption.inputs['Color'].default_value = (.74,.025,.80,1)
absorption.inputs['Density'].default_value = .9
glass.node_tree.links.new(absorption.outputs[0], glass.node_tree.nodes.get('Material Output').inputs['Volume'])
glass_shader = glass.node_tree.nodes.new('ShaderNodeBsdfGlass')
glass_shader.inputs['Color'].default_value = (.88,.045,.90,1)
glass_shader.inputs['Roughness'].default_value = .035
glass_shader.inputs['IOR'].default_value = 1.38
glass.node_tree.links.new(glass_shader.outputs[0], glass.node_tree.nodes.get('Material Output').inputs['Surface'])

def emission(name, color, strength):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    shader = nodes.new('ShaderNodeEmission')
    shader.inputs['Color'].default_value = (*color, 1)
    shader.inputs['Strength'].default_value = strength
    out = nodes.new('ShaderNodeOutputMaterial')
    mat.node_tree.links.new(shader.outputs[0], out.inputs['Surface'])
    return mat, shader

plasma, plasma_shader = emission('Violet plasma filaments', (.60, .012, 1), 4.5)
hot, hot_shader = emission('White violet plasma heart', (.68, .24, 1), 9)

def periodic_driver(target, prop, index, expression):
    curve = target.driver_add(prop, index) if index is not None else target.driver_add(prop)
    curve.driver.expression = expression

def phase(cycles=1, offset=0):
    return f'({TAU:.16f}*(frame-1+96)/{FRAMES}*{cycles}+{offset:.12f})'

def create_band(name, radius, width, depth, orientation, horns, speed, offset=0, ellipticity=1.0, material=silver):
    """A closed swept lens with integral curved blade tips, not attached cones."""
    n, m = 720, 20
    vertices, faces = [], []
    for i in range(n):
        t = TAU * i/n
        spike = 0
        curl = 0
        warped = radius * (1 + .055*math.sin(3*t+offset) + .035*math.cos(2*t-.7))
        band_width = width*(.85 + .24*math.cos(2*t+offset) + .15*math.sin(3*t))
        radial = Vector((math.cos(t), math.sin(t)*ellipticity, 0)).normalized()
        tangent = Vector((-math.sin(t), math.cos(t)*ellipticity, 0)).normalized()
        center = Vector((warped*math.cos(t)*1.15, warped*math.sin(t)*ellipticity,
                         .12*math.sin(2*t+offset)+.05*math.cos(3*t)))
        center += radial * spike*.48 + tangent*curl
        twist = .45*math.sin(2*t+offset)+.18*math.cos(3*t)
        for j in range(m):
            p = TAU*j/m
            u = math.cos(p)*(band_width+spike*.48)
            # Rounded flattened lens. Small groove creates folded reflections.
            v = math.sin(p)*depth*(1+.18*math.cos(3*t))
            v -= .015*math.exp(-((math.cos(p)-.28)/.22)**2)*math.sin(p)
            rotated_u = u*math.cos(twist)-v*math.sin(twist)
            rotated_v = u*math.sin(twist)+v*math.cos(twist)
            pos = center + radial*rotated_u + Vector((0,0,rotated_v))
            vertices.append(tuple(pos))
    for i in range(n):
        for j in range(m):
            faces.append((i*m+j, ((i+1)%n)*m+j, ((i+1)%n)*m+(j+1)%m, i*m+(j+1)%m))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    for poly in mesh.polygons:
        poly.use_smooth = True
    axis = bpy.data.objects.new(name+' axis', None)
    scene.collection.objects.link(axis)
    camera_basis = Vector((0,-10,5.8)).to_track_quat('Z','Y').to_matrix().to_4x4()
    axis.matrix_world = camera_basis @ Euler(tuple(math.radians(x) for x in orientation)).to_matrix().to_4x4()
    obj.parent = axis
    # A complete turn about each band's own axis: position and velocity match.
    periodic_driver(obj, 'rotation_euler', 2, phase(speed, offset))
    # Continuous blade lofts grow out of the outer folded edge and taper to a
    # needle. Their bases overlap the ribbon; their shading uses the same metal.
    for horn_index, (t, reach, sigma, direction) in enumerate(horns):
        radial = Vector((math.cos(t),math.sin(t)*ellipticity,0)).normalized()
        tangent = Vector((-math.sin(t),math.cos(t)*ellipticity,0)).normalized()
        warped = radius*(1+.055*math.sin(3*t+offset)+.035*math.cos(2*t-.7))
        root = Vector((warped*math.cos(t)*1.15,warped*math.sin(t)*ellipticity,
                       .12*math.sin(2*t+offset)+.05*math.cos(3*t)))+radial*width*.7
        hv, hf = [], []
        sections, circumference = 44, 16
        for h in range(sections):
            u = h/(sections-1)
            center = root+radial*reach*u+tangent*direction*reach*(.1*u+.42*u*u)
            center += Vector((0,0,.13*math.sin(u*math.pi)))
            hw = max(.0006,width*.65*(1-u)**1.4)
            hd = max(.0004,depth*.8*(1-u)**1.7)
            for j in range(circumference):
                p = TAU*j/circumference
                hv.append(tuple(center+tangent*hw*math.cos(p)+Vector((0,0,hd*math.sin(p)))))
        for h in range(sections-1):
            for j in range(circumference):
                hf.append((h*circumference+j,(h+1)*circumference+j,
                           (h+1)*circumference+(j+1)%circumference,h*circumference+(j+1)%circumference))
        hm = bpy.data.meshes.new(name+' blade')
        hm.from_pydata(hv,[],hf)
        hm.update()
        horn = bpy.data.objects.new(name+f' integral tip {horn_index}',hm)
        scene.collection.objects.link(horn)
        horn.parent = obj
        horn.data.materials.append(material)
        for poly in hm.polygons:
            poly.use_smooth = True
    return obj

# The initial broad face is a diagonal oval; smaller bands weave under it.
create_band('Broad front ribbon', 1.94, .30, .115, (37, -20, -30),
            [(.48, 1.0, .065, 1), (3.24, .80, .06, -1)], 1, .2, .90)
create_band('Diagonal blade ribbon', 1.80, .17, .072, (-55, 26, 24),
            [(1.45, 1.12, .05, 1), (4.50, .72, .065, -1), (5.85,.35,.05,1)], -1, 1.15, 1.04)
create_band('Lower wrapping ribbon', 1.64, .22, .085, (63, 12, -24),
            [(2.45,.88,.057,-1),(5.45,.94,.055,1)], 1, 2.3, 1.06)
create_band('Inner thorn cage A', 1.01, .045, .026, (48, 27, 22),
            [(.82,.28,.05,1),(3.7,.22,.06,-1)], -1, .35, 1.0, cage_material)
create_band('Inner thorn cage B', 1.04, .037, .021, (-45, 55, -10),
            [(2.1,.26,.055,-1),(5.5,.20,.05,1)], 1, 1.5, .95, cage_material)

def uv_sphere(name, radius, material, location=(0,0,0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=64, radius=radius, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj

shell = uv_sphere('Violet glass core', .83, glass)
inner, shader = principled('Clouded amethyst beneath the glass', (.07,.005,.21), .32, .23)
shader.inputs['Emission Color'].default_value = (.11,.008,.38,1)
shader.inputs['Emission Strength'].default_value = .20
nodes, links = inner.node_tree.nodes, inner.node_tree.links
tex = nodes.new('ShaderNodeTexNoise')
tex.inputs['Scale'].default_value = 6
tex.inputs['Detail'].default_value = 4
tex.inputs['Roughness'].default_value = .68
coord = nodes.new('ShaderNodeTexCoord')
mapping = nodes.new('ShaderNodeMapping')
links.new(coord.outputs['Generated'], mapping.inputs['Vector'])
links.new(mapping.outputs['Vector'], tex.inputs['Vector'])
periodic_driver(mapping.inputs['Rotation'], 'default_value', 2, phase())
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = .30
ramp.color_ramp.elements[0].color = (.007,.001,.025,1)
ramp.color_ramp.elements[1].position = .72
ramp.color_ramp.elements[1].color = (.30,.002,.52,1)
links.new(tex.outputs['Fac'], ramp.inputs['Fac'])
links.new(ramp.outputs['Color'], shader.inputs['Base Color'])
links.new(ramp.outputs['Color'], shader.inputs['Emission Color'])
uv_sphere('Inner amethyst volume', .72, inner)

def filament(name, points, radius, material):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 2
    curve.bevel_depth = radius
    curve.bevel_resolution = 2
    spline = curve.splines.new('POLY')
    spline.points.add(len(points)-1)
    for point, vec in zip(spline.points, points):
        point.co = (*vec, 1)
    obj = bpy.data.objects.new(name, curve)
    scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj

random.seed(48)
plasma_axis = bpy.data.objects.new('Slow internal plasma drift', None)
scene.collection.objects.link(plasma_axis)
periodic_driver(plasma_axis, 'rotation_euler', 2, phase())
hub = Vector((.13,-.58,.35)).normalized()
for k in range(30):
    end = Vector((random.uniform(-1,1),random.uniform(-1,1),random.uniform(-1,1))).normalized()
    points = []
    for j in range(22):
        f = j/21
        direction = (hub*(1-f)+end*f).normalized()
        wiggle = Vector((random.uniform(-.035,.035),random.uniform(-.035,.035),random.uniform(-.035,.035)))
        points.append(tuple(direction*(.755+.025*math.sin(f*9+k))+wiggle))
    obj = filament('Branching plasma %02d'%k, points, random.uniform(.003,.008), hot if k%5==0 else plasma)
    obj.parent = plasma_axis
    if k%3 == 0:
        start = Vector(points[10])
        branch = [tuple((start*(1-f)+end*.77*f).normalized()*.77 +
                        Vector((0,.017*math.sin(f*20),.018*math.cos(f*18)))) for f in [j/15 for j in range(16)]]
        filament('Small fork %02d'%k, branch, .0025, plasma).parent = plasma_axis
uv_sphere('Bright plasma junction', .065, hot, tuple(hub*.76)).parent = plasma_axis
periodic_driver(plasma_shader.inputs['Strength'], 'default_value', None, f'4.5+.6*sin({phase(2)})')
periodic_driver(hot_shader.inputs['Strength'], 'default_value', None, f'8.5+1*sin({phase(2)})')

def aim(obj, at=(0,0,0)):
    obj.rotation_euler = (Vector(at)-obj.location).to_track_quat('-Z','Y').to_euler()

def area(name, location, color, energy, scale, scale_y=None):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = energy
    data.color = color
    data.shape = 'RECTANGLE'
    data.size = scale
    data.size_y = scale_y if scale_y else scale
    obj = bpy.data.objects.new(name,data)
    scene.collection.objects.link(obj)
    obj.location = location
    aim(obj)
    return obj

area('Long cream softbox', (-3,-4,5), (1,.96,.88), 1550, 4.0, 1.5)
area('Right silver strip', (4,-2,2), (.90,.93,1), 1750, 2.8, .85)
area('Broad lower front reflection', (3,-5,-1), (.94,.93,1), 700, 4.0, 2.5)
area('Low silver reflection', (-1,-2,-4), (.91,.90,1), 1000, 3, .8)
area('Violet reflected troughs', (-3,1,.2), (.35,.045,1), 800, 2, 3)
area('Deep red edge light', (3,2,1), (1,.07,.14), 230, .7, 2.6)
area('Back white edge', (1,3,4), (.94,.89,1), 1400, 2, 1)
light = bpy.data.lights.new('Light within plasma', 'POINT')
light.color = (.60,.016,1)
light.energy = 40
light.shadow_soft_size = .30
obj = bpy.data.objects.new('Light within plasma',light)
scene.collection.objects.link(obj)

bpy.ops.object.camera_add(location=(0,-10,5.8))
camera = bpy.context.object
camera.name = 'Fixed three-quarter camera'
aim(camera)
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 7.5
scene.camera = camera

# Local bloom only; alpha remains the sculpture, with soft light near the core.
scene.use_nodes = True
nodes, links = scene.node_tree.nodes, scene.node_tree.links
nodes.clear()
layer = nodes.new('CompositorNodeRLayers')
glare = nodes.new('CompositorNodeGlare')
glare.glare_type = 'FOG_GLOW'
glare.quality = 'HIGH'
glare.threshold = 3.6
glare.size = 7
glare.mix = -.96
out = nodes.new('CompositorNodeComposite')
dispersion = nodes.new('CompositorNodeLensdist')
dispersion.inputs['Dispersion'].default_value = .003
dispersion.use_fit = True
alpha = nodes.new('CompositorNodeSetAlpha')
links.new(layer.outputs['Image'],glare.inputs['Image'])
links.new(glare.outputs['Image'],dispersion.inputs['Image'])
links.new(dispersion.outputs['Image'],alpha.inputs['Image'])
links.new(layer.outputs['Alpha'],alpha.inputs['Alpha'])
links.new(alpha.outputs['Image'],out.inputs['Image'])
scene.frame_set(1)
scene.render.filepath = str(ROOT/'frames'/'frame_')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'chrome-orbit.blend'))
manifest = {'frames':FRAMES,'fps':24,'seconds':16,'size':size,'seed':48,
            'features':['3 warped lens-section chrome ribbons','7 integral curved blade tips',
                        '2 thin thorn cages','violet glass/plasma sphere','fixed camera'],
            'film':'transparent','engine':'cycles','samples':scene.cycles.samples}
(ROOT/'render-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if mode == 'preview':
    for frame in (1,97,193,289,385):
        scene.frame_set(frame)
        scene.render.filepath = str(ROOT/f'preview-{frame:03d}.png')
        bpy.ops.render.render(write_still=True)
elif mode == 'render':
    bpy.ops.render.render(animation=True)
