"""Offline mercury sculpture: periodic liquid geometry and enclosed thunder.
Blender 4.5: --python tools/render-hero.py -- preview|render|audit 768.
"""
import bpy, math, os, sys, json, random
import numpy as np
from pathlib import Path
from mathutils import Vector, Euler, Quaternion
ROOT=Path(os.environ.get('ALI_HERO_RENDER_DIR',str(Path(__file__).resolve().parent.parent/'work'/'hero-render'))).resolve()
(ROOT/'frames').mkdir(parents=True,exist_ok=True)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
MODE=args[0] if args else 'preview'; SIZE=int(args[1]) if len(args)>1 else 768
TAU,FPS,SECONDS=math.tau,int(os.environ.get('ALI_HERO_FPS','60')),20
if FPS not in (12,24,60):raise SystemExit('ALI_HERO_FPS must be 12, 24 or 60.')
FRAMES=FPS*SECONDS
CORE_RADIUS=1.08
STORM_ORIGIN=Vector((0,0,0))
def clock(frame):return TAU*(frame-1)/FRAMES
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='CYCLES'
scene.cycles.samples=int(os.environ.get('ALI_HERO_SAMPLES','48' if MODE=='preview' else '32'))
scene.cycles.use_denoising=True;scene.cycles.max_bounces=8;scene.cycles.transmission_bounces=6
gpu_enabled=False
prefs=bpy.context.preferences.addons['cycles'].preferences
for backend in ([os.environ['ALI_HERO_DEVICE']] if os.environ.get('ALI_HERO_DEVICE') else (['METAL'] if sys.platform=='darwin' else ['OPTIX','CUDA'])):
    try:
        prefs.compute_device_type=backend;prefs.get_devices()
        for device in prefs.devices:device.use=device.type!='CPU'
        if any(device.type!='CPU' for device in prefs.devices):
            scene.cycles.device='GPU';gpu_enabled=True
            print('GPU_BACKEND',backend,[(d.name,d.type,d.use) for d in prefs.devices],flush=True);break
    except Exception as error:print('GPU backend unavailable',backend,error,flush=True)
if not gpu_enabled and os.environ.get('ALI_HERO_REQUIRE_GPU')=='1':raise RuntimeError('Cloud GPU is required; refusing CPU render.')
scene.render.resolution_x=SIZE;scene.render.resolution_y=SIZE;scene.render.resolution_percentage=100
scene.render.fps=FPS;scene.frame_start=1;scene.frame_end=FRAMES;scene.render.film_transparent=True
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8'
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.10
scene.world.use_nodes=True;world=scene.world.node_tree.nodes.get('Background')
# Curved silver needs structured reflections, not a uniform grey environment.
# A procedural HDR studio has broad feathered white windows and soft troughs.
height,width=512,1024
yy,xx=np.mgrid[0:height,0:width];u=xx/width;v=yy/height
radiance=np.full((height,width,3),.009,dtype=np.float32)
for position,spread,power,tint in [(.12,.035,6.0,(1,.98,.94)),(.39,.065,3.7,(.96,.97,1)),(.69,.028,7.0,(1,1,1)),(.90,.05,4.6,(.50,.10,1))]:
    distance=np.minimum(np.abs(u-position),1-np.abs(u-position))
    window=np.exp(-(distance/spread)**6)*np.exp(-((v-.49)/.30)**6)
    radiance+=window[:,:,None]*power*np.array(tint,dtype=np.float32)
radiance+=np.exp(-((v-.16)/.12)**2)[:,:,None]*.15
hdr=bpy.data.images.new('Feathered silver studio HDR',width=width,height=height,float_buffer=True)
hdr.pixels.foreach_set(np.concatenate((radiance,np.ones((height,width,1),dtype=np.float32)),axis=2).ravel())
hdr.pack();environment=scene.world.node_tree.nodes.new('ShaderNodeTexEnvironment');environment.image=hdr
scene.world.node_tree.links.new(environment.outputs['Color'],world.inputs['Color']);world.inputs['Strength'].default_value=.65
def material(name,color,metal=0,rough=.08):
    mat=bpy.data.materials.new(name);mat.use_nodes=True;node=mat.node_tree.nodes.get('Principled BSDF')
    node.inputs['Base Color'].default_value=(*color,1);node.inputs['Metallic'].default_value=metal;node.inputs['Roughness'].default_value=rough
    return mat,node
mercury,metal=material('Polished liquid mirror silver',(.94,.95,.98),1,.028)
metal.inputs['Coat Weight'].default_value=.16;metal.inputs['Coat Roughness'].default_value=.045
glass=bpy.data.materials.new('Clear amethyst crystal');glass.use_nodes=True
gn,gl=glass.node_tree.nodes,glass.node_tree.links;gn.clear();surface=gn.new('ShaderNodeBsdfGlass')
surface.inputs['Color'].default_value=(.56,.12,.82,1);surface.inputs['Roughness'].default_value=.025;surface.inputs['IOR'].default_value=1.28
gout=gn.new('ShaderNodeOutputMaterial');gl.new(surface.outputs[0],gout.inputs['Surface'])
absorb=gn.new('ShaderNodeVolumeAbsorption');absorb.inputs['Color'].default_value=(.24,.008,.46,1);absorb.inputs['Density'].default_value=1.25
gl.new(absorb.outputs[0],gout.inputs['Volume'])
# A rotating, lightly rippled glass skin makes the sphere's turn readable.
glass_coords=gn.new('ShaderNodeTexCoord');glass_noise=gn.new('ShaderNodeTexNoise')
glass_noise.inputs['Scale'].default_value=7;glass_noise.inputs['Detail'].default_value=3
gl.new(glass_coords.outputs['Generated'],glass_noise.inputs['Vector'])
glass_bump=gn.new('ShaderNodeBump');glass_bump.inputs['Strength'].default_value=.12;glass_bump.inputs['Distance'].default_value=.035
gl.new(glass_noise.outputs['Fac'],glass_bump.inputs['Height']);gl.new(glass_bump.outputs['Normal'],surface.inputs['Normal'])
def emission(name,color,strength):
    mat=bpy.data.materials.new(name);mat.use_nodes=True;nodes=mat.node_tree.nodes;nodes.clear()
    node=nodes.new('ShaderNodeEmission');node.inputs['Color'].default_value=(*color,1);node.inputs['Strength'].default_value=strength
    out=nodes.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(node.outputs[0],out.inputs['Surface']);return mat,node
hot_material,hot_emission=emission('White violet lightning junction',(.84,.43,1),15)
def make_mesh(name,verts,faces,mat):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();obj=bpy.data.objects.new(name,mesh)
    scene.collection.objects.link(obj);mesh.materials.append(mat)
    for p in mesh.polygons:p.use_smooth=True
    return obj
def swept_faces(n,m,closed=True):
    return [(i*m+j,((i+1)%n)*m+j,((i+1)%n)*m+(j+1)%m,i*m+(j+1)%m) for i in range(n if closed else n-1) for j in range(m)]
CAMERA_BASIS=Vector((0,-10,5.8)).to_track_quat('Z','Y').to_matrix().to_4x4()
bands=[]
sculpture=bpy.data.objects.new('Slow sculptural orbit',None);scene.collection.objects.link(sculpture)
class Stream:
    """Folded mirror ribbons with seamless swept needle extrusions.
    A common orbit retains the interweave; small local waves flow along each band.
    Actual triangle intersections are checked for every frame.
    """
    def __init__(self,name,radius,width,thickness,angles,speed,phase,hooks,claws=()):
        self.name,self.r,self.w,self.d=name,radius,width,thickness
        self.angles,self.speed,self.phase=angles,speed,phase;self.n,self.m=480+15*(len(hooks)+len(claws)),40
        self.thorns=hooks;self.claws=claws
        self.axis=bpy.data.objects.new(name+' orbit',None);scene.collection.objects.link(self.axis);self.axis.parent=sculpture
        self.obj=make_mesh(name,[(0,0,0)]*(self.n*self.m),swept_faces(self.n,self.m),mercury);self.obj.parent=self.axis
        self.hooks=[];bands.append(self)
    def path(self,t,time):
        latitude=.14*math.sin(2*t+self.phase)+.035*math.sin(3*t-time-self.phase)
        angle=t+.065*math.sin(3*t+self.phase)+.018*math.sin(2*t-time)
        radial=Vector((math.cos(angle)*math.cos(latitude),math.sin(angle)*math.cos(latitude),math.sin(latitude)))
        return radial*(self.r+.045*math.sin(3*t+self.phase)+.018*math.sin(4*t-time+self.phase))
    def basis(self,t,time):
        center=self.path(t,time);radial=center.normalized()
        tangent=(self.path(t+.0005,time)-self.path(t-.0005,time)).normalized();cross=radial.cross(tangent).normalized()
        return center,radial,tangent,cross
    def update(self,time):
        p=self.phase
        angles=(math.radians(self.angles[0])+math.radians(2)*math.sin(time+p),
                math.radians(self.angles[1])+math.radians(2)*math.cos(time+p),math.radians(self.angles[2]))
        self.axis.matrix_basis=Euler(angles).to_matrix().to_4x4()
        thorns=[(angle+.012*math.sin(time+p),length*(1+.025*math.sin(time+p+angle)),side) for angle,length,side in self.thorns]
        span=self.w/self.r*.85
        offsets=(-1,-.8,-.6,-.4,-.3,-.2,-.1,0,.1,.2,.3,.4,.6,.8,1)
        sections=sorted([TAU*i/480 for i in range(480)]+[(angle+offset*span)%TAU for angle,_,_ in thorns for offset in offsets])
        claws=[(angle+.008*math.sin(time+p),length*(1+.018*math.sin(time+p+angle))) for angle,length in self.claws]
        sections=sorted(sections+[(angle+offset*span)%TAU for angle,_ in claws for offset in offsets])
        vertices=[]
        for t in sections:
            center,radial,tangent,cross=self.basis(t,time)
            flow=.86+.26*math.sin(2*t+p)+.17*math.cos(3*t-p)+.06*math.sin(3*t-time+p)
            width=self.w*flow;thickness=self.d*(.90+.20*math.sin(3*t+p)+.08*math.sin(3*t-time))
            twist=.25*math.sin(2*t+p)+.12*math.sin(5*t-p)+.035*math.sin(3*t-time+p)
            b=cross*math.cos(twist)+radial*math.sin(twist);n=radial*math.cos(twist)-cross*math.sin(twist)
            nearby=[]
            for angle,length,side in thorns:
                delta=math.atan2(math.sin(t-angle),math.cos(t-angle))
                if abs(delta)<span:nearby.append((max(0,1-abs(delta)/span)**1.65,length,side))
            for j in range(self.m):
                a=TAU*j/self.m;u=math.cos(a)
                # Two folded shoulders and a slim return edge, rather than a tube.
                fold=.34*width*(abs(u-.15)-.52)+.10*width*math.sin(3*t+p)*u
                point=center+b*width*u+n*(thickness*math.sin(a)+fold)
                for along,length,side in nearby:
                    around=abs(math.atan2(math.sin(a-(0 if side==1 else math.pi)),math.cos(a-(0 if side==1 else math.pi))))
                    prickle=along*max(0,1-around/.70)**1.65
                    if prickle:
                        extra=length*prickle
                        # Long swept thorn: concave base, backward hook, hairline apex.
                        point+=cross*side*extra+radial*(extra*(.36-.18*prickle))-tangent*(extra*(.38+.49*prickle))
                for angle,length in claws:
                    delta=math.atan2(math.sin(t-angle),math.cos(t-angle))
                    if abs(delta)>=span:continue
                    along=max(0,1-abs(delta)/span)**1.45
                    around=abs(math.atan2(math.sin(a-3*math.pi/2),math.cos(a-3*math.pi/2)))
                    claw=along*max(0,1-around/.85)**1.6
                    if claw:
                        # Grow from the orb-facing lip, then curl tangent to the
                        # shell. The root is concave and the apex bends back.
                        inward=length*(.92*claw-.25*claw*claw)
                        curl=length*(.28*claw+.70*claw*claw)
                        point-=radial*inward+tangent*curl
                        point+=cross*(length*.18*claw*(1-claw))
                vertices.append(tuple(point))
        self.obj.data.vertices.foreach_set('co',[x for v in vertices for x in v]);self.obj.data.update()

Stream('Outer folded chrome blade',3.25,.54,.115,(54,-18,-32),0,.3,[(.55,1.70,1),(2.65,1.40,-1),(4.70,1.55,1)])
Stream('Middle swept mirror blade',2.42,.29,.10,(-59,26,21),0,1.7,[(1.05,1.15,1),(3.45,1.35,-1),(5.40,.95,1)])
Stream('Inner folded mercury blade',1.73,.30,.08,(60,0,0),0,3.0,[])
def sphere(name,radius,mat,location=(0,0,0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96,ring_count=64,radius=radius,location=location)
    obj=bpy.context.object;obj.name=name;obj.data.materials.append(mat)
    for p in obj.data.polygons:p.use_smooth=True
    return obj
orb_axis=bpy.data.objects.new('Rotating glass ball and storm',None);scene.collection.objects.link(orb_axis)
stellar_axis=bpy.data.objects.new('Independent stellar spin inside the orb',None);scene.collection.objects.link(stellar_axis);stellar_axis.parent=orb_axis
orb_shell=sphere('Rotating rippled glass thunder orb',CORE_RADIUS,glass);orb_shell.parent=orb_axis;orb_shell.pass_index=1
# A real four-claw collet: the narrow girdle rail sits against the stone, and
# each rounded claw grows from that rail, follows the dome, then hooks over it.
# The whole setting is orb-local, so nothing orbits independently around the gem.
orb_prongs=[]
prong_count,prong_sides=128,24
view_dir=Vector((0,-15,8.7)).normalized();screen_right=Vector((1,0,0));screen_up=view_dir.cross(screen_right).normalized()
bpy.ops.mesh.primitive_torus_add(major_segments=192,minor_segments=24,major_radius=.84,minor_radius=.048)
orb_bezel=bpy.context.object;orb_bezel.name='Orb girdle rail · gemstone collet';orb_bezel.data.materials.append(mercury);orb_bezel.parent=orb_axis
orb_bezel.location=view_dir*.64;orb_bezel.rotation_mode='QUATERNION';orb_bezel.rotation_quaternion=view_dir.to_track_quat('Z','Y')
for polygon in orb_bezel.data.polygons:polygon.use_smooth=True
for prong_index,azimuth in enumerate((math.pi/4,3*math.pi/4,5*math.pi/4,7*math.pi/4)):
    meridian=(screen_right*math.cos(azimuth)+screen_up*math.sin(azimuth)).normalized()
    centers=[];radii=[]
    for step in range(prong_count):
        u=step/(prong_count-1)
        if u<.82:
            q=u/.82;ease=q*q*(3-2*q);theta=math.radians(52-34*ease)
        else:
            q=(u-.82)/.18;theta=math.radians(18+8*q*q*(3-2*q))
        direction=(view_dir*math.cos(theta)+meridian*math.sin(theta)).normalized()
        shoulder=math.sin(math.pi*u)**.8
        center=direction*(CORE_RADIUS+.018+.027*shoulder-.040*max(0,(u-.9)/.1))
        radius=.052+.026*shoulder-.039*u
        centers.append(center);radii.append(max(.014,radius))
    vertices=[]
    for step,(center,radius) in enumerate(zip(centers,radii)):
        normal=center.normalized();tangent=(centers[min(step+1,prong_count-1)]-centers[max(step-1,0)]).normalized()
        side=tangent.cross(normal).normalized()
        for side_index in range(prong_sides):
            angle=TAU*side_index/prong_sides
            vertices.append(tuple(center+normal*radius*math.cos(angle)+side*radius*.78*math.sin(angle)))
    prong=make_mesh(f'Gemstone claw {prong_index+1} · tapered silver',vertices,swept_faces(prong_count,prong_sides,False),mercury)
    prong.parent=orb_axis;orb_prongs.append(prong)
    for polygon in prong.data.polygons:polygon.use_smooth=True
# Evolving translucent cloud depth, not a static texture rotating on a sphere.
cloud=bpy.data.materials.new('Evolving violet cloud volume');cloud.use_nodes=True
nodes,links=cloud.node_tree.nodes,cloud.node_tree.links;nodes.clear()
coords=nodes.new('ShaderNodeTexCoord');mapping=nodes.new('ShaderNodeMapping');links.new(coords.outputs['Generated'],mapping.inputs['Vector'])
mapping.inputs['Scale'].default_value=(1.4,.7,1.7)
noise=nodes.new('ShaderNodeTexNoise');noise.noise_dimensions='4D';noise.inputs['Scale'].default_value=3.1;noise.inputs['Detail'].default_value=3
links.new(mapping.outputs['Vector'],noise.inputs['Vector'])
density=nodes.new('ShaderNodeMath');density.operation='MULTIPLY';density.inputs[1].default_value=.24;links.new(noise.outputs['Fac'],density.inputs[0])
volume=nodes.new('ShaderNodeVolumePrincipled');volume.inputs['Color'].default_value=(.028,.001,.075,1);links.new(density.outputs[0],volume.inputs['Density'])
plasma=nodes.new('ShaderNodeValToRGB');plasma.color_ramp.elements[0].position=.35;plasma.color_ramp.elements[0].color=(.025,.002,.10,1)
plasma.color_ramp.elements[1].position=.65;plasma.color_ramp.elements[1].color=(.50,.016,1,1)
links.new(noise.outputs['Fac'],plasma.inputs['Fac']);links.new(plasma.outputs['Color'],volume.inputs['Emission Color']);volume.inputs['Emission Strength'].default_value=.012
out=nodes.new('ShaderNodeOutputMaterial');links.new(volume.outputs[0],out.inputs['Volume']);sphere('Rotating cloud depth inside crystal',1.00,cloud).parent=orb_axis
def curve(name,points,thickness,mat):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=thickness;data.bevel_resolution=2
    spline=data.splines.new('POLY');spline.points.add(len(points)-1)
    for point,v in zip(spline.points,points):point.co=(*v,1)
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);data.materials.append(mat);return obj
# A textured stellar photosphere replaces the old white point and radial spokes.
star=bpy.data.materials.new('Turbulent confined violet star');star.use_nodes=True
sn,sl=star.node_tree.nodes,star.node_tree.links;sn.clear()
scoords=sn.new('ShaderNodeTexCoord');star_mapping=sn.new('ShaderNodeMapping');sl.new(scoords.outputs['Generated'],star_mapping.inputs['Vector'])
star_noise=sn.new('ShaderNodeTexNoise');star_noise.noise_dimensions='4D';star_noise.inputs['Scale'].default_value=5.4;star_noise.inputs['Detail'].default_value=5;star_noise.inputs['Roughness'].default_value=.72
sl.new(star_mapping.outputs['Vector'],star_noise.inputs['Vector'])
star_ramp=sn.new('ShaderNodeValToRGB');ramp=star_ramp.color_ramp
for e in list(ramp.elements)[1:]:ramp.elements.remove(e)
ramp.elements[0].position=.26;ramp.elements[0].color=(.008,.0005,.025,1)
for position,color in [(.43,(.025,.0006,.09,1)),(.54,(.30,.008,.80,1)),(.60,(.90,.40,1,1)),(.67,(1,.90,.98,1))]:ramp.elements.new(position).color=color
sl.new(star_noise.outputs['Fac'],star_ramp.inputs['Fac'])
star_emit=sn.new('ShaderNodeEmission');star_emit.inputs['Strength'].default_value=32;sl.new(star_ramp.outputs['Color'],star_emit.inputs['Color'])
star_out=sn.new('ShaderNodeOutputMaterial');sl.new(star_emit.outputs[0],star_out.inputs['Surface'])
star_obj=sphere('Roiling star photosphere',.225,star);star_obj.parent=stellar_axis
star_base=[v.co.copy() for v in star_obj.data.vertices]
# A clear, uneven eight-ray photosphere gives the tiny core a star silhouette
# at actual portfolio size; the turbulent sphere remains its bright surface.
ray_material,ray_node=emission('Violet-white stellar rays',(.66,.20,1),9)
ray_hot_material,ray_hot_node=emission('White-hot star tips',(.96,.68,1),13)
ray_vertices=[]
for i in range(16):
    angle=TAU*i/16
    radius=.445 if i%4==0 else (.282 if i%2==0 else .165)
    ray_vertices.append(tuple(view_dir*.195+screen_right*(radius*math.cos(angle))+screen_up*(radius*math.sin(angle))))
ray_vertices.extend([tuple(view_dir*.34),tuple(view_dir*.12)])
ray_faces=[]
for i in range(16):
    j=(i+1)%16;ray_faces.extend([(16,i,j),(17,j,i)])
star_rays=make_mesh('Eight-point stellar corona inside orb',ray_vertices,ray_faces,ray_material)
star_rays.data.materials.append(ray_hot_material);star_rays.parent=stellar_axis
for i in range(16):
    star_rays.data.polygons[2*i].material_index=1 if i%4==0 else 0
    star_rays.data.polygons[2*i+1].material_index=1 if i%4==0 else 0
star_rays_base=[v.co.copy() for v in star_rays.data.vertices]
# A dim plasma atmosphere gives the compact star a soft, irregular corona.
corona=bpy.data.materials.new('Confined stellar atmosphere');corona.use_nodes=True
cn,cl=corona.node_tree.nodes,corona.node_tree.links;cn.clear()
cc=cn.new('ShaderNodeTexCoord');cnoise=cn.new('ShaderNodeTexNoise');cnoise.inputs['Scale'].default_value=5;cnoise.inputs['Detail'].default_value=3
cl.new(cc.outputs['Generated'],cnoise.inputs['Vector'])
cdensity=cn.new('ShaderNodeMath');cdensity.operation='MULTIPLY';cdensity.inputs[1].default_value=.20;cl.new(cnoise.outputs['Fac'],cdensity.inputs[0])
cv=cn.new('ShaderNodeVolumePrincipled');cv.inputs['Color'].default_value=(.28,.01,.66,1);cl.new(cdensity.outputs[0],cv.inputs['Density'])
cv.inputs['Emission Color'].default_value=(.55,.012,1,1);cv.inputs['Emission Strength'].default_value=1.1
co=cn.new('ShaderNodeOutputMaterial');cl.new(cv.outputs[0],co.inputs['Volume'])
sphere('Small plasma atmosphere around star',.355,corona).parent=stellar_axis
random.seed(62);arcs=[]
for k in range(7):
    direction=Vector((random.uniform(-1,1),random.uniform(-1,1),random.uniform(-1,1))).normalized()
    reference=Vector((0,0,1)) if abs(direction.z)<.8 else Vector((1,0,0))
    tangent=direction.cross(reference).normalized();side=direction.cross(tangent).normalized()
    mat,node=emission(f'Coronal prominence {k}',(.47,.018,1) if k%3 else (.90,.36,1),8)
    obj=curve(f'Curved confined stellar flare {k}',[(0,0,0)]*64,.0055 if k%3 else .008,mat)
    obj.parent=stellar_axis
    arcs.append((obj,[],direction,tangent,side,k*.87))
particles=[]
for k in range(24):
    direction=Vector((random.uniform(-1,1),random.uniform(-1,1),random.uniform(-1,1))).normalized()
    radius=random.uniform(.39,.80);mat,node=emission(f'Contained ember {k}',(.64,.065,1),3)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.0045 if k%3 else .007)
    obj=bpy.context.object;obj.name=f'Confined stellar ember {k}';obj.data.materials.append(mat);obj.parent=stellar_axis
    particles.append((obj,node,direction,radius,k*.91))
def aim(obj):obj.rotation_euler=(-obj.location).to_track_quat('-Z','Y').to_euler()
def area(name,location,color,power,sx,sy):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=color;data.shape='RECTANGLE';data.size=sx;data.size_y=sy
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=Vector(location)*1.5;data.energy*=2.25;data.size*=1.5;data.size_y*=1.5;aim(obj)
area('Broad silver ceiling',(-3,-4,6),(1,.97,.92),850,3.8,1.4)
area('Broad frontal white reflection',(4,-5,1),(.96,.97,1),950,3.2,1.0)
area('Lower silver sweep',(-2,-4,-4),(.95,.95,1),750,3.0,1.0)
area('Narrow mirrored highlight',(5,1,4),(1,1,1),1100,3,.35)
area('Violet edge bounce',(-4,1,1),(.55,.025,1),700,3,2)
area('Deep red reflected accent',(4,3,0),(1,.08,.16),100,1,3)
data=bpy.data.lights.new('Thunder lights the crystal','POINT');data.color=(.5,.025,1);data.energy=26;data.shadow_soft_size=.15
core_light=bpy.data.objects.new('Thunder lights the crystal',data);scene.collection.objects.link(core_light)
core_light.parent=orb_axis;core_light.location=STORM_ORIGIN
bpy.ops.object.camera_add(location=(0,-15,8.7));camera=bpy.context.object;aim(camera)
camera.data.type='ORTHO';camera.data.ortho_scale=10.6;scene.camera=camera
scene.view_layers[0].use_pass_object_index=True
scene.use_nodes=True;nodes,links=scene.node_tree.nodes,scene.node_tree.links;nodes.clear()
layer=nodes.new('CompositorNodeRLayers');glare=nodes.new('CompositorNodeGlare');glare.glare_type='FOG_GLOW';glare.quality='HIGH';glare.threshold=4;glare.size=7;glare.mix=-.96
dispersion=nodes.new('CompositorNodeLensdist');dispersion.inputs['Dispersion'].default_value=0;dispersion.use_fit=True
alpha=nodes.new('CompositorNodeSetAlpha');out=nodes.new('CompositorNodeComposite')
links.new(layer.outputs['Image'],glare.inputs['Image']);links.new(dispersion.outputs['Image'],alpha.inputs['Image'])
links.new(layer.outputs['Alpha'],alpha.inputs['Alpha']);links.new(alpha.outputs['Image'],out.inputs['Image'])
# Bloom is masked twice to keep the star's radiance inside the glass silhouette.
orb_mask=nodes.new('CompositorNodeIDMask');orb_mask.index=1;orb_mask.use_antialiasing=True;links.new(layer.outputs['IndexOB'],orb_mask.inputs['ID value'])
# Sidecar mask lets the export split only the visible glass rim, keeping
# the confined star and chrome mirror faces crisp.
mask_file=nodes.new('CompositorNodeOutputFile');mask_file.base_path=str(ROOT/'orb-mask')
mask_file.format.file_format='PNG';mask_file.format.color_mode='BW';mask_file.format.color_depth='8'
mask_file.file_slots[0].path='mask_';links.new(orb_mask.outputs['Alpha'],mask_file.inputs[0])
orb_image=nodes.new('CompositorNodeMixRGB');orb_image.blend_type='MULTIPLY';orb_image.inputs[0].default_value=1
links.new(layer.outputs['Image'],orb_image.inputs[1]);links.new(orb_mask.outputs['Alpha'],orb_image.inputs[2])
orb_glow=nodes.new('CompositorNodeGlare');orb_glow.glare_type='FOG_GLOW';orb_glow.quality='HIGH';orb_glow.threshold=.8;orb_glow.size=7;orb_glow.mix=1
links.new(orb_image.outputs[0],orb_glow.inputs['Image'])
confined=nodes.new('CompositorNodeMixRGB');confined.blend_type='MULTIPLY';confined.inputs[0].default_value=1
links.new(orb_glow.outputs['Image'],confined.inputs[1]);links.new(orb_mask.outputs['Alpha'],confined.inputs[2])
combine=nodes.new('CompositorNodeMixRGB');combine.blend_type='ADD';combine.inputs[0].default_value=.60
links.new(glare.outputs['Image'],combine.inputs[1]);links.new(confined.outputs[0],combine.inputs[2]);links.new(combine.outputs[0],dispersion.inputs['Image'])

def update(s,graph=None):
    t=clock(s.frame_current)
    sculpture.matrix_world=CAMERA_BASIS@Euler((.035*math.sin(t),t,math.radians(28)+.04*math.sin(t))).to_matrix().to_4x4()
    for stream in bands:stream.update(t)
    orb_axis.rotation_euler=(.12*math.sin(t),t,.10*math.cos(t))
    stellar_axis.rotation_mode='QUATERNION';stellar_axis.rotation_quaternion=Quaternion(view_dir,2*t)
    mapping.inputs['Location'].default_value=(.38*math.cos(t),.38*math.sin(t),.20*math.sin(2*t))
    mapping.inputs['Rotation'].default_value=(.10*math.sin(t),.12*math.cos(t),.3*math.sin(t));noise.inputs['W'].default_value=.7*math.sin(2*t)
    star_mapping.inputs['Location'].default_value=(.20*math.cos(2*t),.20*math.sin(2*t),.14*math.sin(3*t))
    star_mapping.inputs['Rotation'].default_value=(.12*math.sin(t),.18*math.cos(t),t)
    star_noise.inputs['W'].default_value=.65*math.sin(3*t)
    star_emit.inputs['Strength'].default_value=30+5*math.sin(4*t)
    star_obj.data.vertices.foreach_set('co',[component for base in star_base for component in base*(1+.075*math.sin(base.x*19+base.y*13+2*t)*math.cos(base.z*17-3*t))]);star_obj.data.update()
    ray_coords=[]
    spin=.20*math.sin(t)
    for base in star_rays_base:
        x,y,z=base.dot(screen_right),base.dot(screen_up),base.dot(view_dir)
        angle=math.atan2(y,x)+spin;scale=1+.045*math.sin(2*t+angle)
        radius=math.hypot(x,y)*scale
        ray_coords.append(view_dir*z+screen_right*(radius*math.cos(angle-spin))+screen_up*(radius*math.sin(angle-spin)))
    star_rays.data.vertices.foreach_set('co',[component for vertex in ray_coords for component in vertex]);star_rays.data.update()
    for obj,branches,direction,tangent,side,p in arcs:
        turn=.22*math.sin(2*t+p);rotation=Euler((.14*math.sin(t+p),.16*math.cos(t+p),turn)).to_matrix()
        for j,point in enumerate(obj.data.splines[0].points):
            u=j/63;arch=math.sin(math.pi*u)
            radial=.24+(.39+.075*math.sin(2*t+p))*arch
            q=direction*radial+tangent*(.15*math.cos(math.pi*u))              +side*(.09*math.sin(TAU*u+2*t+p)*arch)
            point.co=(*(rotation@q),1)
        node=obj.data.materials[0].node_tree.nodes.get('Emission')
        node.inputs['Strength'].default_value=4+18*(.5+.5*math.sin(2*t+p))**3
    for obj,node,direction,radius,p in particles:
        obj.location=Euler((.08*math.sin(2*t+p),.16*math.cos(t+p),t)).to_matrix()@direction*(radius+.02*math.sin(3*t+p))
        node.inputs['Strength'].default_value=.5+3*(.5+.5*math.sin(3*t+p))**4
    core_light.data.energy=7+2*math.sin(4*t)

bpy.app.handlers.frame_change_pre.append(update)
scene.frame_set(1);update(scene);bpy.context.view_layer.update();scene.render.filepath=str(ROOT/'frames'/'frame_')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'chrome-orbit.blend'))
def audit():
    from mathutils.bvhtree import BVHTree
    collision_pairs=0;hook_collision_pairs=0;hook_self_pairs=0
    def proxy_faces(n,m,along=2,around=4):
        rows=list(range(0,n,along));cols=list(range(0,m,around));faces=[]
        for i,row in enumerate(rows):
            next_row=rows[(i+1)%len(rows)]
            for j,col in enumerate(cols):
                next_col=cols[(j+1)%len(cols)]
                faces.append((row*m+col,next_row*m+col,next_row*m+next_col,row*m+next_col))
        return faces
    # Keep the full smooth mesh for rendering, but use a dense-enough proxy for
    # the many-pose broad collision audit so Modal can complete the preflight.
    faces={b.name:proxy_faces(b.n,b.m) for b in bands}
    prong_faces={obj.name:proxy_faces(len(obj.data.vertices)//prong_sides,prong_sides) for obj in orb_prongs}
    ranges={b.name:[float('inf'),0] for b in bands};min_gap=float('inf');max_projection=0
    camera_inv=np.array(camera.matrix_world.inverted());shape_samples={};thunder_samples={};texture_samples={};orb_samples={};star_axis_samples={};max_thunder_radius=0;star_samples={};star_texture_samples={};ember_samples={}
    # The sculpt deforms continuously and slowly. A 67 ms sample plus the
    # exact loop seam catches crossings throughout the motion efficiently.
    checked_frames=sorted(set(range(1,FRAMES+2,4))|{FRAMES+1})
    for frame in checked_frames:
        scene.frame_set(frame);bpy.context.view_layer.update();this=[];trees=[]
        for band in bands:
            low,high=float('inf'),0
            for obj in [band.obj,*[h[0] for h in band.hooks]]:
                flat=np.empty(len(obj.data.vertices)*3,dtype=np.float32);obj.data.vertices.foreach_get('co',flat)
                points=flat.reshape(-1,3);matrix=np.array(obj.matrix_world);world=points@matrix[:3,:3].T+matrix[:3,3]
                trees.append((band.name,BVHTree.FromPolygons(world.tolist(),faces[band.name],all_triangles=False,epsilon=.002)))
                radius=np.linalg.norm(world,axis=1);low=min(low,float(radius.min()));high=max(high,float(radius.max()))
                view=world@camera_inv[:3,:3].T+camera_inv[:3,3];max_projection=max(max_projection,float(np.abs(view[:,:2]).max())/camera.data.ortho_scale)
            this.append((low,high,band.name));ranges[band.name][0]=min(ranges[band.name][0],low);ranges[band.name][1]=max(ranges[band.name][1],high)
        for obj in orb_prongs:
            flat=np.empty(len(obj.data.vertices)*3,dtype=np.float32);obj.data.vertices.foreach_get('co',flat)
            points=flat.reshape(-1,3);matrix=np.array(obj.matrix_world);world=points@matrix[:3,:3].T+matrix[:3,3]
            trees.append((obj.name,BVHTree.FromPolygons(world.tolist(),prong_faces[obj.name],all_triangles=False,epsilon=.002)))
        this.sort()
        for index,(name,tree) in enumerate(trees):
            for other,second in trees[index+1:]:
                collision_pairs+=1
                in_prong=name in prong_faces;other_prong=other in prong_faces
                if in_prong != other_prong:hook_collision_pairs+=1
                elif in_prong:hook_self_pairs+=1
                if tree.overlap(second):
                    if in_prong or other_prong:raise RuntimeError(f'Frame {frame}: orb setting prong intersects sculpture {name} / {other}')
                    raise RuntimeError(f'Frame {frame}: intersecting blades {name} / {other}')
        min_gap=min(min_gap,this[0][0]-CORE_RADIUS)
        if this[0][0]<=CORE_RADIUS+.14:raise RuntimeError(f'Core intersection {frame}')
        thunder=[]
        for obj,branches,*_ in arcs:
            for curve_obj in [obj,*branches]:
                points=np.array([tuple(point.co[:3]) for point in curve_obj.data.splines[0].points])
                matrix=np.array(curve_obj.matrix_world);points=points@matrix[:3,:3].T+matrix[:3,3]
                max_thunder_radius=max(max_thunder_radius,float(np.linalg.norm(points,axis=1).max())+curve_obj.data.bevel_depth)
                thunder.extend(points.tolist())
        for ember,*_ in particles:
            if ember.location.length+.008>=CORE_RADIUS:raise RuntimeError(f'Ember escapes the shell at frame {frame}')
        if max(v.co.length for v in star_rays.data.vertices)>=.56:raise RuntimeError(f'Star escapes its corona at frame {frame}')
        if max_thunder_radius>=CORE_RADIUS:raise RuntimeError(f'Lightning escapes the glass at frame {frame}')
        if frame in (1,FRAMES//4+1,FRAMES//2+1,3*FRAMES//4+1,FRAMES+1):
            shape_samples[str(frame)]=[tuple(v.co) for band in bands for v in band.obj.data.vertices]
            thunder_samples[str(frame)]=thunder
            texture_samples[str(frame)]=[*mapping.inputs['Location'].default_value,*mapping.inputs['Rotation'].default_value,noise.inputs['W'].default_value]
            orb_samples[str(frame)]=np.array(orb_axis.matrix_world).tolist()
            star_axis_samples[str(frame)]=np.array(stellar_axis.matrix_world).tolist()
            star_samples[str(frame)]=[tuple(v.co) for v in star_rays.data.vertices]
            star_texture_samples[str(frame)]=[*star_mapping.inputs['Location'].default_value,star_noise.inputs['W'].default_value,*np.array(Euler(star_mapping.inputs['Rotation'].default_value).to_matrix()).ravel()]
            ember_samples[str(frame)]=[tuple(obj.location) for obj,*_ in particles]
    if max_projection>.485:raise RuntimeError(f'Camera clipping: {max_projection}')
    seam=float(np.abs(np.array(shape_samples['1'])-np.array(shape_samples[str(FRAMES+1)])).max())
    deformation=float(np.abs(np.array(shape_samples['1'])-np.array(shape_samples[str(FRAMES//4+1)])).max())
    thunder_seam=float(np.abs(np.array(thunder_samples['1'])-np.array(thunder_samples[str(FRAMES+1)])).max())
    thunder_change=float(np.abs(np.array(thunder_samples['1'])-np.array(thunder_samples[str(FRAMES//4+1)])).max())
    texture_seam=float(np.abs(np.array(texture_samples['1'])-np.array(texture_samples[str(FRAMES+1)])).max())
    texture_change=float(np.abs(np.array(texture_samples['1'])-np.array(texture_samples[str(FRAMES//4+1)])).max())
    orb_seam=float(np.abs(np.array(orb_samples['1'])-np.array(orb_samples[str(FRAMES+1)])).max())
    orb_change=float(np.abs(np.array(orb_samples['1'])-np.array(orb_samples[str(FRAMES//4+1)])).max())
    star_axis_seam=float(np.abs(np.array(star_axis_samples['1'])-np.array(star_axis_samples[str(FRAMES+1)])).max())
    star_seam=float(np.abs(np.array(star_samples['1'])-np.array(star_samples[str(FRAMES+1)] )).max())
    star_texture_seam=float(np.abs(np.array(star_texture_samples['1'])-np.array(star_texture_samples[str(FRAMES+1)])).max())
    ember_seam=float(np.abs(np.array(ember_samples['1'])-np.array(ember_samples[str(FRAMES+1)])).max())
    if max(seam,thunder_seam,texture_seam,orb_seam,star_axis_seam,star_seam,star_texture_seam,ember_seam)>.00001:raise RuntimeError('Loop geometry, orb, stellar spin or cloud does not close')
    report={'frames_checked':len(checked_frames),'frame_stride':4,'star_surface_loop_delta':star_seam,'star_texture_loop_delta':star_texture_seam,'stellar_spin_loop_delta':star_axis_seam,'stellar_turns_per_loop':2,'ember_loop_delta':ember_seam,'orb_gem_prongs':len(orb_prongs),'prong_parents':[obj.parent.name for obj in orb_prongs],'prong_radius_bounds':[min(v.co.length for obj in orb_prongs for v in obj.data.vertices),max(v.co.length for obj in orb_prongs for v in obj.data.vertices)],'min_core_clearance':min_gap,'triangle_collision_pairs_checked':collision_pairs,'prong_band_collision_pairs_checked':hook_collision_pairs,'prong_prong_collision_pairs_checked':hook_self_pairs,'radial_lanes':ranges,'projection_half_extent':max_projection,'loop_mesh_delta':seam,'actual_mesh_deformation':deformation,'max_thunder_radius':max_thunder_radius,'thunder_loop_delta':thunder_seam,'actual_thunder_deformation':thunder_change,'cloud_loop_delta':texture_seam,'actual_cloud_change':texture_change,'orb_rotation_loop_delta':orb_seam,'actual_orb_rotation':orb_change,'shared_turns_per_loop':1,'independent_ring_turns_per_loop':[b.speed for b in bands],'profile_half_depths':[b.d for b in bands]}
    (ROOT/'geometry-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('GEOMETRY_AUDIT',json.dumps(report),flush=True)
manifest={'frames':FRAMES,'fps':FPS,'seconds':SECONDS,'playback_rate':1,'visual_loop_seconds':SECONDS,'size':SIZE,'version':10,'features':['3 layered chrome-mercury rings; inner orbit frames the setting','slow common orbit and gentle liquid flow','6 long rose-like thorns with concave roots','4 rounded silver claws on a girdle rail, fixed to the orb','smoked amethyst glass with an eight-point stellar core','curved confined coronal flares and stellar embers',f'true native {FPS}fps temporal sampling'],'film':'transparent','engine':'cycles','samples':scene.cycles.samples}
(ROOT/'render-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if MODE=='audit':audit()
elif MODE=='preview':
    for frame in (1,FRAMES//8+1,FRAMES//4+1,FRAMES//2+1,3*FRAMES//4+1,FRAMES+1):
        scene.frame_set(frame);scene.render.filepath=str(ROOT/f'preview-{frame:03d}.png');bpy.ops.render.render(write_still=True)
elif MODE=='gem-preview':
    for band in bands:band.obj.hide_render=True
    scene.camera.data.ortho_scale=4.3;scene.frame_set(1)
    scene.render.filepath=str(ROOT/'gem-setting-isolated.png');bpy.ops.render.render(write_still=True)
elif MODE in ('render','chunk'):
    scene.frame_start=int(os.environ.get('ALI_HERO_START','1'))
    scene.frame_end=int(os.environ.get('ALI_HERO_END',str(FRAMES)))
    if not 1<=scene.frame_start<=scene.frame_end<=FRAMES:raise RuntimeError('Invalid render chunk')
    bpy.ops.render.render(animation=True)


# bpy wheel shutdown can retain driver teardown threads in a notebook worker.
# All images/scene/audit files have been synchronously saved before this point.
if os.environ.get("ALI_HERO_FAST_EXIT")=="1":
    sys.stdout.flush();sys.stderr.flush();os._exit(0)
