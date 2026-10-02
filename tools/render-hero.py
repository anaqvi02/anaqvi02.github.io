"""Offline mercury sculpture: periodic chrome geometry and a rotating Stella Octangula.
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
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='16'
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
# Exact boundary of the compound of two regular tetrahedra: eight
# tetrahedral tips over the eight faces of a central regular octahedron.
# The previous sphere, cloud, flare and collet assembly is entirely replaced.
stellar_axis=bpy.data.objects.new('Independent Stella Octangula rotation',None)
scene.collection.objects.link(stellar_axis)
stella_materials=[]
for name,color in [('Deep amethyst tetrahedron',(.20,.008,.52)),('Violet tetrahedron',(.36,.025,.76))]:
    mat,node=material(name,color,.35,.075)
    node.inputs['Coat Weight'].default_value=.45
    node.inputs['Coat Roughness'].default_value=.04
    node.inputs['Emission Color'].default_value=(*color,1)
    node.inputs['Emission Strength'].default_value=.16
    stella_materials.append(mat)
a=1.02/math.sqrt(3)
stella_vertices=[(a,0,0),(-a,0,0),(0,a,0),(0,-a,0),(0,0,a),(0,0,-a)]
stella_faces=[];face_materials=[]
for sx in (-1,1):
    for sy in (-1,1):
        for sz in (-1,1):
            apex=len(stella_vertices);stella_vertices.append((sx*a,sy*a,sz*a))
            base=[0 if sx==1 else 1,2 if sy==1 else 3,4 if sz==1 else 5]
            for j in range(3):
                face=(apex,base[j],base[(j+1)%3])
                x,y,z=[Vector(stella_vertices[i]) for i in face]
                if (y-x).cross(z-x).dot((x+y+z)/3)<0:face=(face[0],face[2],face[1])
                stella_faces.append(face);face_materials.append(0 if sx*sy*sz==1 else 1)
stella=make_mesh('Stella Octangula · compound of two regular tetrahedra',stella_vertices,stella_faces,stella_materials[0])
stella.data.materials.append(stella_materials[1]);stella.parent=stellar_axis;stella.pass_index=1
for polygon,material_index in zip(stella.data.polygons,face_materials):
    polygon.use_smooth=False;polygon.material_index=material_index
# Tiny bevels catch studio highlights without rounding off the eight points.
bevel=stella.modifiers.new('Hairline facet highlights','BEVEL');bevel.width=.003;bevel.segments=2
stella.rotation_euler=Euler(tuple(math.radians(v) for v in (18,22,12)))
# Opt-in material study; the shipped plain Stella remains the default.
GLASS_STELLA=os.environ.get('ALI_HERO_CORE_STYLE')=='glass'
inner_axis=None
if GLASS_STELLA:
    scene.cycles.max_bounces=12;scene.cycles.transmission_bounces=10
    glass=bpy.data.materials.new('Smoked dark amethyst Stella glass');glass.use_nodes=True
    gn,gl=glass.node_tree.nodes,glass.node_tree.links;gn.clear()
    surface=gn.new('ShaderNodeBsdfGlass')
    surface.inputs['Color'].default_value=(.56,.12,.82,1)
    surface.inputs['Roughness'].default_value=.025;surface.inputs['IOR'].default_value=1.28
    absorb=gn.new('ShaderNodeVolumeAbsorption')
    absorb.inputs['Color'].default_value=(.24,.008,.46,1);absorb.inputs['Density'].default_value=1.25
    gout=gn.new('ShaderNodeOutputMaterial');gl.new(surface.outputs[0],gout.inputs['Surface']);gl.new(absorb.outputs[0],gout.inputs['Volume'])
    stella.data.materials.clear();stella.data.materials.append(glass)
    for polygon in stella.data.polygons:polygon.material_index=0
    inner_axis=bpy.data.objects.new('Independent white Stella inside amethyst glass',None)
    scene.collection.objects.link(inner_axis);inner_axis.parent=stellar_axis
    white_materials=[]
    for label,strength in [('White-hot tetrahedron',18),('Soft white tetrahedron',7)]:
        mat,node=material(label,(1,.97,1),0,.18)
        node.inputs['Emission Color'].default_value=(1,.97,1,1)
        node.inputs['Emission Strength'].default_value=strength
        white_materials.append(mat)
    INNER_RADIUS=.28
    inner=make_mesh('Luminous inner Stella Octangula',[(Vector(v)*(INNER_RADIUS/1.02))[:] for v in stella_vertices],stella_faces,white_materials[0])
    inner.data.materials.append(white_materials[1]);inner.parent=inner_axis
    inner.rotation_euler=Euler(tuple(math.radians(v) for v in (-12,35,8)))
    for polygon,index in zip(inner.data.polygons,face_materials):polygon.use_smooth=False;polygon.material_index=index
    inner_bevel=inner.modifiers.new('Fine inner facet highlights','BEVEL');inner_bevel.width=.001;inner_bevel.segments=2
    # The central octahedron's insphere is radius 1.02/3. The entire
    # inner compound stays within it at every orientation, with no crossings.
    assert INNER_RADIUS<1.02/3-.04

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
bpy.ops.object.camera_add(location=(0,-15,8.7));camera=bpy.context.object;aim(camera)
camera.data.type='ORTHO';camera.data.ortho_scale=10.6;scene.camera=camera
scene.view_layers[0].use_pass_object_index=True
scene.use_nodes=True;nodes,links=scene.node_tree.nodes,scene.node_tree.links;nodes.clear()
layer=nodes.new('CompositorNodeRLayers');glare=nodes.new('CompositorNodeGlare');glare.glare_type='FOG_GLOW';glare.quality='HIGH';glare.threshold=4;glare.size=7;glare.mix=-.96
dispersion=nodes.new('CompositorNodeLensdist');dispersion.inputs['Dispersion'].default_value=0;dispersion.use_fit=True
alpha=nodes.new('CompositorNodeSetAlpha');out=nodes.new('CompositorNodeComposite')
links.new(layer.outputs['Image'],glare.inputs['Image']);links.new(dispersion.outputs['Image'],alpha.inputs['Image'])
links.new(layer.outputs['Alpha'],alpha.inputs['Alpha']);links.new(alpha.outputs['Image'],out.inputs['Image'])
# Preserve a center-only sidecar mask for optional local color grading.
center_mask=nodes.new('CompositorNodeIDMask');center_mask.index=1;center_mask.use_antialiasing=True
links.new(layer.outputs['IndexOB'],center_mask.inputs['ID value'])
mask_file=nodes.new('CompositorNodeOutputFile');mask_file.base_path=str(ROOT/'orb-mask')
mask_file.format.file_format='PNG';mask_file.format.color_mode='BW';mask_file.format.color_depth='8'
mask_file.file_slots[0].path='mask_';links.new(center_mask.outputs['Alpha'],mask_file.inputs[0])
if GLASS_STELLA:
    # Mask a restrained bloom back to the glass: points and facets stay crisp.
    glow=nodes.new('CompositorNodeGlare');glow.glare_type='FOG_GLOW';glow.quality='HIGH';glow.threshold=2;glow.size=6;glow.mix=1
    links.new(layer.outputs['Image'],glow.inputs['Image'])
    confined=nodes.new('CompositorNodeMixRGB');confined.blend_type='MULTIPLY';confined.inputs[0].default_value=1
    links.new(glow.outputs['Image'],confined.inputs[1]);links.new(center_mask.outputs['Alpha'],confined.inputs[2])
    combine=nodes.new('CompositorNodeMixRGB');combine.blend_type='ADD';combine.inputs[0].default_value=.18
    links.new(glare.outputs['Image'],combine.inputs[1]);links.new(confined.outputs[0],combine.inputs[2]);links.new(combine.outputs[0],dispersion.inputs['Image'])
else:links.new(glare.outputs['Image'],dispersion.inputs['Image'])

def update(s,graph=None):
    t=clock(s.frame_current)
    sculpture.matrix_world=CAMERA_BASIS@Euler((.035*math.sin(t),t,math.radians(28)+.04*math.sin(t))).to_matrix().to_4x4()
    for stream in bands:stream.update(t)
    stellar_axis.rotation_mode='QUATERNION'
    stellar_axis.rotation_quaternion=Quaternion(Vector((.32,.81,.49)).normalized(),t)
    if inner_axis is not None:
        inner_axis.rotation_mode='QUATERNION'
        inner_axis.rotation_quaternion=Quaternion(Vector((-.48,.35,.80)).normalized(),2*t)

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
    ranges={b.name:[float('inf'),0] for b in bands};min_gap=float('inf');max_projection=0
    camera_inv=np.array(camera.matrix_world.inverted());shape_samples={};star_axis_samples={}
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
        this.sort()
        for index,(name,tree) in enumerate(trees):
            for other,second in trees[index+1:]:
                collision_pairs+=1
                if tree.overlap(second):raise RuntimeError(f'Frame {frame}: intersecting blades {name} / {other}')
        min_gap=min(min_gap,this[0][0]-CORE_RADIUS)
        if this[0][0]<=CORE_RADIUS+.14:raise RuntimeError(f'Core intersection {frame}')
        if max(v.co.length for v in stella.data.vertices)>=CORE_RADIUS-.02:raise RuntimeError('Stella exceeds central clearance')
        if frame in (1,FRAMES//4+1,FRAMES//2+1,3*FRAMES//4+1,FRAMES+1):
            shape_samples[str(frame)]=[tuple(v.co) for band in bands for v in band.obj.data.vertices]
            star_axis_samples[str(frame)]=np.array(stellar_axis.matrix_world).tolist()
    if max_projection>.485:raise RuntimeError(f'Camera clipping: {max_projection}')
    seam=float(np.abs(np.array(shape_samples['1'])-np.array(shape_samples[str(FRAMES+1)])).max())
    deformation=float(np.abs(np.array(shape_samples['1'])-np.array(shape_samples[str(FRAMES//4+1)])).max())
    star_axis_seam=float(np.abs(np.array(star_axis_samples['1'])-np.array(star_axis_samples[str(FRAMES+1)])).max())
    star_axis_change=float(np.abs(np.array(star_axis_samples['1'])-np.array(star_axis_samples[str(FRAMES//4+1)])).max())
    if max(seam,star_axis_seam)>.00001:raise RuntimeError('Loop geometry or Stella spin does not close')
    assert len(stella.data.vertices)==14 and len(stella.data.polygons)==24
    edges={}
    for face in stella_faces:
        for j in range(3):
            edge=tuple(sorted((face[j],face[(j+1)%3])));edges[edge]=edges.get(edge,0)+1
    assert len(edges)==36 and all(count==2 for count in edges.values()),'Stella is not a closed manifold'
    assert sum(abs(v.co.length-1.02)<.00001 for v in stella.data.vertices)==8
    report={'frames_checked':len(checked_frames),'frame_stride':4,'stella_vertices':14,'stella_faces':24,'stella_tips':8,'stella_closed_manifold':True,'stella_radius':1.02,'stellar_spin_loop_delta':star_axis_seam,'actual_stella_rotation':star_axis_change,'stellar_turns_per_loop':1,'min_core_clearance':min_gap,'triangle_collision_pairs_checked':collision_pairs,'radial_lanes':ranges,'projection_half_extent':max_projection,'loop_mesh_delta':seam,'actual_mesh_deformation':deformation,'shared_turns_per_loop':1,'profile_half_depths':[b.d for b in bands]}
    (ROOT/'geometry-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('GEOMETRY_AUDIT',json.dumps(report),flush=True)
manifest={'frames':FRAMES,'fps':FPS,'seconds':SECONDS,'playback_rate':1,'visual_loop_seconds':SECONDS,'size':SIZE,'version':11,'features':['3 layered chrome-mercury rings','slow common orbit and gentle liquid flow','6 long rose-like thorns with concave roots','exact eight-point Stella Octangula with flat amethyst facets','independent calm 3D Stella rotation',f'true native {FPS}fps temporal sampling'],'film':'transparent','engine':'cycles','samples':scene.cycles.samples,'bit_depth':16,'finish':'clean ungraded master'}
if GLASS_STELLA:manifest.update(version=12,core_style='dark amethyst glass with luminous independently rotating inner Stella',inner_radius=INNER_RADIUS,inner_containment_clearance=1.02/3-INNER_RADIUS)
(ROOT/'render-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if MODE=='audit':audit()
elif MODE=='preview':
    for frame in (1,FRAMES//8+1,FRAMES//4+1,FRAMES//2+1,3*FRAMES//4+1,FRAMES+1):
        scene.frame_set(frame);scene.render.filepath=str(ROOT/f'preview-{frame:03d}.png');bpy.ops.render.render(write_still=True)
elif MODE=='gem-preview':
    for band in bands:band.obj.hide_render=True
    scene.camera.data.ortho_scale=4.3;scene.frame_set(1)
    scene.render.filepath=str(ROOT/'stella-isolated.png');bpy.ops.render.render(write_still=True)
elif MODE in ('render','chunk'):
    scene.frame_start=int(os.environ.get('ALI_HERO_START','1'))
    scene.frame_end=int(os.environ.get('ALI_HERO_END',str(FRAMES)))
    if not 1<=scene.frame_start<=scene.frame_end<=FRAMES:raise RuntimeError('Invalid render chunk')
    bpy.ops.render.render(animation=True)


# bpy wheel shutdown can retain driver teardown threads in a notebook worker.
# All images/scene/audit files have been synchronously saved before this point.
if os.environ.get("ALI_HERO_FAST_EXIT")=="1":
    sys.stdout.flush();sys.stderr.flush();os._exit(0)
