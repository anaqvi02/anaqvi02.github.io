"""Offline mercury sculpture: periodic liquid geometry and enclosed thunder.
Blender 4.5: --python tools/render-hero.py -- preview|render|audit 768.
"""
import bpy, math, os, sys, json, random
import numpy as np
from pathlib import Path
from mathutils import Vector, Euler
ROOT=Path(os.environ.get('ALI_HERO_RENDER_DIR',str(Path(__file__).resolve().parent.parent/'work'/'hero-render'))).resolve()
(ROOT/'frames').mkdir(parents=True,exist_ok=True)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
MODE=args[0] if args else 'preview'; SIZE=int(args[1]) if len(args)>1 else 768
TAU,FRAMES=math.tau,384
CORE_RADIUS=1.80
STORM_ORIGIN=Vector((.20,-.30,.12))
def clock(frame):return TAU*(frame-1)/FRAMES
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='CYCLES'
scene.cycles.samples=40 if MODE=='preview' else 24
scene.cycles.use_denoising=True;scene.cycles.max_bounces=8;scene.cycles.transmission_bounces=6
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='METAL'
    if any(d.type=='METAL' for d in prefs.devices):scene.cycles.device='GPU'
except Exception as error:print('CPU fallback',error)
scene.render.resolution_x=SIZE;scene.render.resolution_y=SIZE;scene.render.resolution_percentage=100
scene.render.fps=24;scene.frame_start=1;scene.frame_end=FRAMES;scene.render.film_transparent=True
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8'
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.10
scene.world.use_nodes=True;world=scene.world.node_tree.nodes.get('Background')
# Curved silver needs structured reflections, not a uniform grey environment.
# A procedural HDR studio has broad feathered white windows and soft troughs.
height,width=512,1024
yy,xx=np.mgrid[0:height,0:width];u=xx/width;v=yy/height
radiance=np.full((height,width,3),.16,dtype=np.float32)
for position,spread,power,tint in [(.12,.055,4.6,(1,.98,.94)),(.39,.11,2.5,(.95,.97,1)),(.69,.045,5.2,(1,1,1)),(.90,.085,3.6,(.94,.90,1))]:
    distance=np.minimum(np.abs(u-position),1-np.abs(u-position))
    window=np.exp(-(distance/spread)**4)*np.exp(-((v-.49)/.32)**4)
    radiance+=window[:,:,None]*power*np.array(tint,dtype=np.float32)
radiance+=np.exp(-((v-.16)/.12)**2)[:,:,None]*.75
hdr=bpy.data.images.new('Feathered silver studio HDR',width=width,height=height,float_buffer=True)
hdr.pixels.foreach_set(np.concatenate((radiance,np.ones((height,width,1),dtype=np.float32)),axis=2).ravel())
hdr.pack();environment=scene.world.node_tree.nodes.new('ShaderNodeTexEnvironment');environment.image=hdr
scene.world.node_tree.links.new(environment.outputs['Color'],world.inputs['Color']);world.inputs['Strength'].default_value=.55
def material(name,color,metal=0,rough=.08):
    mat=bpy.data.materials.new(name);mat.use_nodes=True;node=mat.node_tree.nodes.get('Principled BSDF')
    node.inputs['Base Color'].default_value=(*color,1);node.inputs['Metallic'].default_value=metal;node.inputs['Roughness'].default_value=rough
    return mat,node
mercury,metal=material('Polished liquid mirror silver',(.91,.92,.96),1,.045)
metal.inputs['Coat Weight'].default_value=.16;metal.inputs['Coat Roughness'].default_value=.045
glass=bpy.data.materials.new('Clear amethyst crystal');glass.use_nodes=True
gn,gl=glass.node_tree.nodes,glass.node_tree.links;gn.clear();surface=gn.new('ShaderNodeBsdfGlass')
surface.inputs['Color'].default_value=(.88,.36,1,1);surface.inputs['Roughness'].default_value=.025;surface.inputs['IOR'].default_value=1.40
gout=gn.new('ShaderNodeOutputMaterial');gl.new(surface.outputs[0],gout.inputs['Surface'])
absorb=gn.new('ShaderNodeVolumeAbsorption');absorb.inputs['Color'].default_value=(.52,.01,.92,1);absorb.inputs['Density'].default_value=.70
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
class Stream:
    """Closed liquid streams in disjoint spherical shells, including hooks.
    Tangential profiles warp freely. Rotation preserves radial separation.
    Every animated pose is numerically audited before rendering the loop.
    """
    def __init__(self,name,radius,width,thickness,angles,speed,phase,hooks):
        self.name,self.r,self.w,self.d=name,radius,width,thickness
        self.angles,self.speed,self.phase=angles,speed,phase;self.n,self.m=480+15*len(hooks),32
        self.thorns=hooks
        self.axis=bpy.data.objects.new(name+' orbit',None);scene.collection.objects.link(self.axis)
        self.obj=make_mesh(name,[(0,0,0)]*(self.n*self.m),swept_faces(self.n,self.m),mercury);self.obj.parent=self.axis
        self.hooks=[]
        bands.append(self)
    def path(self,t,time):
        latitude=.22*math.sin(2*t-3*time+self.phase)+.10*math.sin(3*t+4*time-self.phase)
        angle=t+.09*math.sin(3*t-3*time+self.phase)
        radial=Vector((math.cos(angle)*math.cos(latitude),math.sin(angle)*math.cos(latitude),math.sin(latitude)))
        return radial*(self.r+.055*math.sin(4*t-6*time+self.phase))
    def basis(self,t,time):
        center=self.path(t,time);radial=center.normalized()
        tangent=(self.path(t+.0005,time)-self.path(t-.0005,time)).normalized();cross=radial.cross(tangent).normalized()
        return center,radial,tangent,cross
    def update(self,time):
        p=self.phase
        angles=(math.radians(self.angles[0])+math.radians(12)*math.sin(2*time+p),
                math.radians(self.angles[1])+math.radians(10)*math.cos(2*time+p),math.radians(self.angles[2])+self.speed*time)
        self.axis.matrix_world=CAMERA_BASIS@Euler(angles).to_matrix().to_4x4()
        self.axis.location=(.018*math.sin(time+p),.012*math.cos(time+p),.012*math.sin(2*time+p))
        # Adaptive sections sample every exact thorn apex, keeping needles sharp.
        thorns=[(angle+.06*math.sin(3*time+p),length*(1+.09*math.sin(3*time+p+angle)),side) for angle,length,side in self.thorns]
        span=self.w/self.r*1.20
        offsets=(-1,-.8,-.6,-.4,-.3,-.2,-.1,0,.1,.2,.3,.4,.6,.8,1)
        sections=sorted([TAU*i/480 for i in range(480)]+[(angle+offset*span)%TAU for angle,_,_ in thorns for offset in offsets])
        vertices=[]
        for t in sections:
            center,radial,tangent,cross=self.basis(t,time)
            flow=.98+.27*math.sin(4*t-6*time+p)+.14*math.cos(7*t+4*time-p)
            width=self.w*flow;thickness=self.d*(1+.23*math.sin(4*t-6*time+p)+.07*math.cos(7*t+4*time-p));twist=.46*math.sin(3*t-4*time+p)
            b=cross*math.cos(twist)+radial*math.sin(twist);n=radial*math.cos(twist)-cross*math.sin(twist)
            nearby=[]
            for angle,length,side in thorns:
                delta=math.atan2(math.sin(t-angle),math.cos(t-angle))
                if abs(delta)<span:nearby.append((max(0,1-abs(delta)/span)**1.30,length,side))
            for j in range(self.m):
                a=TAU*j/self.m;point=center+b*width*math.cos(a)+n*thickness*math.sin(a)
                for along,length,side in nearby:
                    around=abs(math.atan2(math.sin(a-(0 if side==1 else math.pi)),math.cos(a-(0 if side==1 else math.pi))))
                    prickle=along*max(0,1-around/.85)**1.30
                    if prickle:
                        # One continuous solid: concave prickle walls merge into
                        # the rounded stem, then end at a swept-back needle.
                        extra=length*prickle
                        direction=(point+cross*side*extra-tangent*extra*.48).normalized()
                        point=direction*(point.length+.34*prickle)
                vertices.append(tuple(point))
        self.obj.data.vertices.foreach_set('co',[x for v in vertices for x in v]);self.obj.data.update()

Stream('Outer volumetric mercury current',5.20,.53,.43,(33,-18,-31),2,.3,[(.30,1.9,1),(1.36,1.5,-1),(2.42,1.8,1),(3.48,1.55,-1),(4.54,1.8,1),(5.60,1.6,-1)])
Stream('Middle volumetric mercury current',3.85,.47,.39,(-52,27,23),-2,1.7,[(.60,1.6,1),(1.64,1.3,-1),(2.68,1.55,1),(3.72,1.4,-1),(4.76,1.6,1),(5.80,1.35,-1)])
Stream('Inner volumetric mercury current',2.55,.41,.34,(66,11,-26),2,3.0,[(.20,1.25,-1),(1.24,1.05,1),(2.28,1.2,-1),(3.32,1.0,1),(4.36,1.25,-1),(5.40,1.05,1)])
def sphere(name,radius,mat,location=(0,0,0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96,ring_count=64,radius=radius,location=location)
    obj=bpy.context.object;obj.name=name;obj.data.materials.append(mat)
    for p in obj.data.polygons:p.use_smooth=True
    return obj
orb_axis=bpy.data.objects.new('Rotating glass ball and storm',None);scene.collection.objects.link(orb_axis)
sphere('Rotating rippled glass thunder orb',CORE_RADIUS,glass).parent=orb_axis
# Evolving translucent cloud depth, not a static texture rotating on a sphere.
cloud=bpy.data.materials.new('Evolving violet cloud volume');cloud.use_nodes=True
nodes,links=cloud.node_tree.nodes,cloud.node_tree.links;nodes.clear()
coords=nodes.new('ShaderNodeTexCoord');mapping=nodes.new('ShaderNodeMapping');links.new(coords.outputs['Generated'],mapping.inputs['Vector'])
mapping.inputs['Scale'].default_value=(1.4,.7,1.7)
noise=nodes.new('ShaderNodeTexNoise');noise.noise_dimensions='4D';noise.inputs['Scale'].default_value=3.1;noise.inputs['Detail'].default_value=3
links.new(mapping.outputs['Vector'],noise.inputs['Vector'])
density=nodes.new('ShaderNodeMath');density.operation='MULTIPLY';density.inputs[1].default_value=1.25;links.new(noise.outputs['Fac'],density.inputs[0])
volume=nodes.new('ShaderNodeVolumePrincipled');volume.inputs['Color'].default_value=(.29,.045,.53,1);links.new(density.outputs[0],volume.inputs['Density'])
plasma=nodes.new('ShaderNodeValToRGB');plasma.color_ramp.elements[0].position=.35;plasma.color_ramp.elements[0].color=(.025,.002,.10,1)
plasma.color_ramp.elements[1].position=.65;plasma.color_ramp.elements[1].color=(.50,.016,1,1)
links.new(noise.outputs['Fac'],plasma.inputs['Fac']);links.new(plasma.outputs['Color'],volume.inputs['Emission Color']);volume.inputs['Emission Strength'].default_value=.65
out=nodes.new('ShaderNodeOutputMaterial');links.new(volume.outputs[0],out.inputs['Volume']);sphere('Rotating cloud depth inside crystal',1.70,cloud).parent=orb_axis
def curve(name,points,thickness,mat):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=thickness;data.bevel_resolution=2
    spline=data.splines.new('POLY');spline.points.add(len(points)-1)
    for point,v in zip(spline.points,points):point.co=(*v,1)
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);data.materials.append(mat);return obj
random.seed(62);arcs=[]
for k in range(12):
    end=Vector((random.uniform(-1,1),random.uniform(-1,1),random.uniform(-1,1))).normalized()*1.49
    jitter=[Vector((random.uniform(-1,1),random.uniform(-1,1),random.uniform(-1,1))) for _ in range(24)]
    mat,node=emission(f'Lightning channel {k}',(.58,.025,1) if k%4 else (.88,.5,1),10)
    obj=curve(f'Internal forked thunder {k}',[(0,0,0)]*24,.009 if k%4 else .013,mat)
    branches=[curve(f'Thunder branch {k}-{j}',[(0,0,0)]*12,.0045,mat) for j in range(2)]
    for child in [obj,*branches]:child.parent=orb_axis
    arcs.append((obj,branches,end,jitter,node,k*.83))
sphere('Orbiting lightning heart',.11,hot_material,STORM_ORIGIN).parent=orb_axis
def aim(obj):obj.rotation_euler=(-obj.location).to_track_quat('-Z','Y').to_euler()
def area(name,location,color,power,sx,sy):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=color;data.shape='RECTANGLE';data.size=sx;data.size_y=sy
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=Vector(location)*1.5;data.energy*=2.25;data.size*=1.5;data.size_y*=1.5;aim(obj)
area('Broad silver ceiling',(-3,-4,6),(1,.97,.92),1500,5.5,3.8)
area('Broad frontal white reflection',(4,-5,1),(.96,.97,1),1800,4.5,3.0)
area('Lower silver sweep',(-2,-4,-4),(.95,.95,1),1350,4.5,2.5)
area('Narrow mirrored highlight',(5,1,4),(1,1,1),1500,3,.7)
area('Violet edge bounce',(-4,1,1),(.6,.09,1),350,3,3)
area('Deep red reflected accent',(4,3,0),(1,.08,.16),100,1,3)
data=bpy.data.lights.new('Thunder lights the crystal','POINT');data.color=(.5,.025,1);data.energy=26;data.shadow_soft_size=.15
core_light=bpy.data.objects.new('Thunder lights the crystal',data);scene.collection.objects.link(core_light)
core_light.parent=orb_axis;core_light.location=STORM_ORIGIN
bpy.ops.object.camera_add(location=(0,-15,8.7));camera=bpy.context.object;aim(camera)
camera.data.type='ORTHO';camera.data.ortho_scale=12.7;scene.camera=camera
scene.use_nodes=True;nodes,links=scene.node_tree.nodes,scene.node_tree.links;nodes.clear()
layer=nodes.new('CompositorNodeRLayers');glare=nodes.new('CompositorNodeGlare');glare.glare_type='FOG_GLOW';glare.quality='HIGH';glare.threshold=4;glare.size=7;glare.mix=-.96
dispersion=nodes.new('CompositorNodeLensdist');dispersion.inputs['Dispersion'].default_value=.002;dispersion.use_fit=True
alpha=nodes.new('CompositorNodeSetAlpha');out=nodes.new('CompositorNodeComposite')
links.new(layer.outputs['Image'],glare.inputs['Image']);links.new(glare.outputs['Image'],dispersion.inputs['Image']);links.new(dispersion.outputs['Image'],alpha.inputs['Image'])
links.new(layer.outputs['Alpha'],alpha.inputs['Alpha']);links.new(alpha.outputs['Image'],out.inputs['Image'])
def update(s,graph=None):
    t=clock(s.frame_current)
    for stream in bands:stream.update(t)
    orb_axis.rotation_euler=(.22*math.sin(t),2*t,.18*math.cos(t))
    mapping.inputs['Location'].default_value=(.38*math.cos(t),.38*math.sin(t),.20*math.sin(2*t))
    mapping.inputs['Rotation'].default_value=(.10*math.sin(t),.12*math.cos(t),.3*math.sin(t));noise.inputs['W'].default_value=.7*math.sin(2*t)
    for obj,branches,end,jitter,node,p in arcs:
        endpoint=Euler((.22*math.sin(2*t+p),.25*math.cos(2*t+p),.27*math.sin(4*t+p))).to_matrix()@end;points=[]
        for j in range(24):
            u=j/23;q=STORM_ORIGIN*(1-u)+endpoint*u+jitter[j]*.095*math.sin(6*t+p+j*.74)*math.sin(math.pi*u);points.append(q)
        for point,v in zip(obj.data.splines[0].points,points):point.co=(*v,1)
        for index,branch in enumerate(branches):
            origin=points[10+index*4];target=endpoint*.67+Vector((.24*math.cos(2*t+p+index),.24*math.sin(2*t+p+index),.24*math.cos(4*t+p)))
            for j,point in enumerate(branch.data.splines[0].points):
                u=j/11;v=origin*(1-u)+target*u+jitter[j]*.055*math.sin(6*t+p+j)*math.sin(math.pi*u);point.co=(*v,1)
        node.inputs['Strength'].default_value=1.0+12*max(0,math.sin(3*t+p))**10
    hot_emission.inputs['Strength'].default_value=11+3*math.sin(2*t);core_light.data.energy=24+8*math.sin(2*t)
bpy.app.handlers.frame_change_pre.append(update)
scene.frame_set(1);update(scene);bpy.context.view_layer.update();scene.render.filepath=str(ROOT/'frames'/'frame_')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'chrome-orbit.blend'))
def audit():
    ranges={b.name:[float('inf'),0] for b in bands};min_gap=float('inf');max_projection=0
    camera_inv=np.array(camera.matrix_world.inverted());shape_samples={};thunder_samples={};texture_samples={};orb_samples={};max_thunder_radius=0
    for frame in range(1,FRAMES+2):
        scene.frame_set(frame);bpy.context.view_layer.update();this=[]
        for band in bands:
            low,high=float('inf'),0
            for obj in [band.obj,*[h[0] for h in band.hooks]]:
                flat=np.empty(len(obj.data.vertices)*3,dtype=np.float32);obj.data.vertices.foreach_get('co',flat)
                points=flat.reshape(-1,3);matrix=np.array(obj.matrix_world);world=points@matrix[:3,:3].T+matrix[:3,3]
                radius=np.linalg.norm(world,axis=1);low=min(low,float(radius.min()));high=max(high,float(radius.max()))
                view=world@camera_inv[:3,:3].T+camera_inv[:3,3];max_projection=max(max_projection,float(np.abs(view[:,:2]).max())/camera.data.ortho_scale)
            this.append((low,high,band.name));ranges[band.name][0]=min(ranges[band.name][0],low);ranges[band.name][1]=max(ranges[band.name][1],high)
        this.sort()
        for a,b in zip(this,this[1:]):
            gap=b[0]-a[1];min_gap=min(min_gap,gap)
            if gap<=.015:raise RuntimeError(f'Frame {frame}: radial overlap {a[2]} / {b[2]}: {gap}')
        if this[0][0]<=CORE_RADIUS+.01:raise RuntimeError(f'Core intersection {frame}')
        thunder=[]
        for obj,branches,*_ in arcs:
            for curve_obj in [obj,*branches]:
                points=np.array([tuple(point.co[:3]) for point in curve_obj.data.splines[0].points])
                matrix=np.array(curve_obj.matrix_world);points=points@matrix[:3,:3].T+matrix[:3,3]
                max_thunder_radius=max(max_thunder_radius,float(np.linalg.norm(points,axis=1).max())+curve_obj.data.bevel_depth)
                thunder.extend(points.tolist())
        if max_thunder_radius>=CORE_RADIUS:raise RuntimeError(f'Lightning escapes the glass at frame {frame}')
        if frame in (1,97,193,289,385):
            shape_samples[str(frame)]=[tuple(v.co) for v in bands[0].obj.data.vertices]
            thunder_samples[str(frame)]=thunder
            texture_samples[str(frame)]=[*mapping.inputs['Location'].default_value,*mapping.inputs['Rotation'].default_value,noise.inputs['W'].default_value]
            orb_samples[str(frame)]=np.array(orb_axis.matrix_world).tolist()
    if max_projection>.485:raise RuntimeError(f'Camera clipping: {max_projection}')
    seam=float(np.abs(np.array(shape_samples['1'])-np.array(shape_samples['385'])).max())
    deformation=float(np.abs(np.array(shape_samples['1'])-np.array(shape_samples['97'])).max())
    thunder_seam=float(np.abs(np.array(thunder_samples['1'])-np.array(thunder_samples['385'])).max())
    thunder_change=float(np.abs(np.array(thunder_samples['1'])-np.array(thunder_samples['97'])).max())
    texture_seam=float(np.abs(np.array(texture_samples['1'])-np.array(texture_samples['385'])).max())
    texture_change=float(np.abs(np.array(texture_samples['1'])-np.array(texture_samples['97'])).max())
    orb_seam=float(np.abs(np.array(orb_samples['1'])-np.array(orb_samples['385'])).max())
    orb_change=float(np.abs(np.array(orb_samples['1'])-np.array(orb_samples['97'])).max())
    if max(seam,thunder_seam,texture_seam,orb_seam)>.00001:raise RuntimeError('Loop geometry, orb or cloud does not close')
    report={'frames_checked':FRAMES+1,'min_ring_clearance':min_gap,'radial_lanes':ranges,'projection_half_extent':max_projection,'loop_mesh_delta':seam,'actual_mesh_deformation':deformation,'max_thunder_radius':max_thunder_radius,'thunder_loop_delta':thunder_seam,'actual_thunder_deformation':thunder_change,'cloud_loop_delta':texture_seam,'actual_cloud_change':texture_change,'orb_rotation_loop_delta':orb_seam,'actual_orb_rotation':orb_change,'ring_turns_per_loop':[b.speed for b in bands],'profile_half_depths':[b.d for b in bands]}
    (ROOT/'geometry-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('GEOMETRY_AUDIT',json.dumps(report),flush=True)
manifest={'frames':FRAMES,'fps':24,'seconds':16,'size':SIZE,'version':3,'features':['3 full rounded mercury streams','double-speed orbit and faster liquid warping','18 broad rose thorns','rotating rippled glass ball and internal storm','changing volume and forked internal lightning'],'film':'transparent','engine':'cycles','samples':scene.cycles.samples}
(ROOT/'render-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if MODE=='audit':audit()
elif MODE=='preview':
    for frame in (1,49,97,193,289,385):
        scene.frame_set(frame);scene.render.filepath=str(ROOT/f'preview-{frame:03d}.png');bpy.ops.render.render(write_still=True)
elif MODE=='render':bpy.ops.render.render(animation=True)
