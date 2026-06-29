import bpy
import math
import random

# RESET SCENE
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# RENDER ENGINE (Eevee Next / 5.1 API Compatibility)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
if hasattr(scene, "eevee"):
    if hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = 16
    elif hasattr(scene.eevee, "ta_samples"):
        scene.eevee.ta_samples = 16
    else:
        scene.eevee.aa_samples = 16

# FPS & DURATION (EXACTLY 10 SECONDS @ 24 FPS = 240 FRAMES)
scene.frame_start = 1
scene.frame_end = 240   
scene.render.fps = 24

# RESOLUTION
scene.render.resolution_x = 1280
scene.render.resolution_y = 1280

# ----------------------------
# 🌌 STAR BACKGROUND
# ----------------------------
world = scene.world
world.use_nodes = True
nodes = world.node_tree.nodes
links = world.node_tree.links
nodes.clear()

bg = nodes.new(type='ShaderNodeBackground')
output = nodes.new(type='ShaderNodeOutputWorld')
noise = nodes.new(type='ShaderNodeTexNoise')
ramp = nodes.new(type='ShaderNodeValToRGB')
math_mult = nodes.new(type='ShaderNodeMath')

noise.inputs['Scale'].default_value = 500.0
noise.inputs['Detail'].default_value = 15.0
noise.inputs['Roughness'].default_value = 0.9

ramp.color_ramp.interpolation = 'CONSTANT'
ramp.color_ramp.elements[0].position = 0.0
ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
ramp.color_ramp.elements[1].position = 0.63      
ramp.color_ramp.elements[1].color = (1, 1, 1, 1)

math_mult.operation = 'MULTIPLY'
math_mult.inputs[1].default_value = 8.0

links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
links.new(ramp.outputs['Color'], math_mult.inputs[0])
links.new(math_mult.outputs['Value'], bg.inputs['Color'])
links.new(bg.outputs['Background'], output.inputs['Surface'])

# =========================================================================
# 1. CREATE JUPITER
# =========================================================================
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.5)
jupiter = bpy.context.object
jupiter.name = "Jupiter"
bpy.ops.object.shade_smooth()

jup_mat = bpy.data.materials.new(name="JupiterMaterial")
jup_mat.use_nodes = True
j_nodes = jup_mat.node_tree.nodes
j_links = jup_mat.node_tree.links
j_nodes.clear()

tex_jup = j_nodes.new(type='ShaderNodeTexImage')
try:
    tex_jup.image = bpy.data.images.load("C:/textures/jupiter_color.jpg")
except:
    print("Jupiter texture not found.")

bsdf_jup = j_nodes.new(type='ShaderNodeBsdfPrincipled')
bsdf_jup.inputs['Roughness'].default_value = 0.60     
out_jup = j_nodes.new(type='ShaderNodeOutputMaterial')

j_links.new(tex_jup.outputs['Color'], bsdf_jup.inputs['Base Color'])
j_links.new(bsdf_jup.outputs['BSDF'], out_jup.inputs['Surface'])
jupiter.data.materials.append(jup_mat)

# =========================================================================
# 🌙 HELPER: CREATE, DEFORM & TEXTURE MOON OBJECTS
# =========================================================================
def create_moon(name, radius, texture_path, compress=False):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=radius)
    moon_obj = bpy.context.object
    moon_obj.name = name
    
    # Compress/Flatten the minor moons physically to make them potato-shaped
    if compress:
        for vertex in moon_obj.data.vertices:
            vertex.co.x *= random.uniform(1.2, 1.4)  # Elongate x
            vertex.co.y *= random.uniform(0.8, 0.95) # Squish y
            vertex.co.z *= random.uniform(0.7, 0.85) # Flatten z
            
    bpy.ops.object.shade_smooth()
    
    mat = bpy.data.materials.new(name=f"{name}_Mat")
    mat.use_nodes = True
    m_nodes = mat.node_tree.nodes
    m_links = mat.node_tree.links
    m_nodes.clear()
    
    tex = m_nodes.new(type='ShaderNodeTexImage')
    try:
        tex.image = bpy.data.images.load(texture_path)
    except:
        print(f"Texture {texture_path} not found.")
        
    bsdf = m_nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Roughness'].default_value = 0.90
    out = m_nodes.new(type='ShaderNodeOutputMaterial')
    
    m_links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    m_links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    moon_obj.data.materials.append(mat)
    
    return moon_obj

# =========================================================================
# 2. CREATE GALILEAN MOONS & TIGHTER MINOR MOONS RIGS
# =========================================================================
random.seed(42)
moons_data = []

# Major 4 Galilean Moons (Kept pristine & round)
galilean_configs = [
    {"name": "Io", "rad": 0.05, "dist": 2.2, "period": 1.769, "tex": "C:/textures/io.jpg"},
    {"name": "Europa", "rad": 0.045, "dist": 2.8, "period": 3.551, "tex": "C:/textures/europa.jpg"},
    {"name": "Ganymede", "rad": 0.07, "dist": 3.6, "period": 7.155, "tex": "C:/textures/ganymede.jpg"},
    {"name": "Callisto", "rad": 0.065, "dist": 4.6, "period": 16.689, "tex": "C:/textures/callisto.jpg"}
]

for config in galilean_configs:
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    orbit_pivot = bpy.context.object
    orbit_pivot.name = f"{config['name']}_Orbit_Center"
    
    moon_obj = create_moon(config['name'], config['rad'], config['tex'], compress=False)
    
    start_angle = random.uniform(0, math.pi * 2)
    moon_obj.location = (math.cos(start_angle) * config['dist'], math.sin(start_angle) * config['dist'], random.uniform(-0.1, 0.1))
    moon_obj.parent = orbit_pivot
    
    moons_data.append({"pivot": orbit_pivot, "moon": moon_obj, "period": config['period']})

# --- COMPRESSED 91 MINOR MOONS ---
minor_moon_texture = "C:/textures/moon.jpg"

for i in range(91):
    name = f"Minor_Moon_{i+1}"
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    orbit_pivot = bpy.context.object
    orbit_pivot.name = f"{name}_Orbit_Center"
    
    # COMPRESSED ORBITS: Brought the outer cloud in from (5.5 - 9.0) to (5.0 - 6.8)
    dist = random.uniform(5.0, 6.8)
    rad = random.uniform(0.015, 0.03)
    period = 15.0 + (dist ** 1.5) * random.uniform(1.0, 1.8) 
    
    # compress=True activates irregular potato flattening
    moon_obj = create_moon(name, rad, minor_moon_texture, compress=True)
    
    start_angle = random.uniform(0, math.pi * 2)
    z_tilt = random.uniform(-0.5, 0.5) # Compressed orbital inclination angle as well
    moon_obj.location = (math.cos(start_angle) * dist, math.sin(start_angle) * dist, z_tilt)
    moon_obj.parent = orbit_pivot
    
    moons_data.append({"pivot": orbit_pivot, "moon": moon_obj, "period": period})

# =========================================================================
# 3. SCORPIO CONSTELLATION
# =========================================================================
star_mat = bpy.data.materials.new(name="StarMaterial")
star_mat.use_nodes = True
s_nodes = star_mat.node_tree.nodes
s_nodes.clear()
node_emit = s_nodes.new(type='ShaderNodeEmission')
node_emit.inputs['Strength'].default_value = 6.0
node_emit.inputs['Color'].default_value = (0.85, 0.9, 1.0, 1.0)
node_out = s_nodes.new(type='ShaderNodeOutputMaterial')
star_mat.node_tree.links.new(node_emit.outputs['Emission'], node_out.inputs['Surface'])

scorpio_stars_coords = [
    (-5.70, 14, 4.15), (-5.95, 14, 3.95), (-5.85, 14, 3.70), (-5.50, 14, 3.60),
    (-5.25, 14, 3.65), (-5.00, 14, 4.20), (-4.75, 14, 4.60), (-4.55, 14, 4.70),
    (-4.10, 14, 5.00), (-4.00, 14, 4.75), (-4.20, 14, 4.50)
]

for idx, coord in enumerate(scorpio_stars_coords):
    size = 0.08 if idx == 7 else random.uniform(0.03, 0.04)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=size, location=coord)
    star = bpy.context.object
    star.name = f"Scorpio_Star_{idx}"
    star.data.materials.append(star_mat)

line_mat = bpy.data.materials.new(name="ConstellationLineMaterial")
line_mat.use_nodes = True
l_nodes = line_mat.node_tree.nodes
l_nodes.clear()
l_emit = l_nodes.new(type='ShaderNodeEmission')
l_emit.inputs['Strength'].default_value = 2.0  
l_emit.inputs['Color'].default_value = (0.4, 0.6, 1.0, 1.0) 
l_out = l_nodes.new(type='ShaderNodeOutputMaterial')
line_mat.node_tree.links.new(l_emit.outputs['Emission'], l_out.inputs['Surface'])

scorpio_line_sequences = [
    [0, 1, 2, 3, 4, 5, 6],                                                                             
    [7, 8],
    [7, 9],
    [7, 10]                                             
]

for sequence_idx, seq in enumerate(scorpio_line_sequences):
    curve_data = bpy.data.curves.new(name=f"Scorpio_LineData_{sequence_idx}", type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = 0.006  
    
    polyline = curve_data.splines.new(type='POLY')
    polyline.points.add(len(seq) - 1)
    
    for point_idx, star_idx in enumerate(seq):
        coord = scorpio_stars_coords[star_idx]
        polyline.points[point_idx].co = (coord[0], coord[1], coord[2], 1.0)
        
    curve_obj = bpy.data.objects.new(f"Scorpio_Line_{sequence_idx}", curve_data)
    bpy.context.collection.objects.link(curve_obj)
    curve_obj.data.materials.append(line_mat)


# =========================================================================
# LIGHTING & CAMERA (Brought in slightly since system is compressed)
# =========================================================================
bpy.ops.object.light_add(type='SUN', location=(10, -12, 10))
key_light = bpy.context.object
key_light.data.energy = 9.0
key_light.rotation_euler = (math.radians(65), 0, math.radians(-40))

bpy.ops.object.camera_add(location=(0, -12.5, 0)) # Closer tracking bounds
camera = bpy.context.object
camera.rotation_euler = (math.radians(90), 0, 0)
camera.data.lens = 28 
scene.camera = camera

# =========================================================================
# ⏱️ ANIMATION
# =========================================================================
original_interpolation = bpy.context.preferences.edit.keyframe_new_interpolation_type
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'

earth_days_to_simulate = 5
jupiter_total_degrees = (earth_days_to_simulate / 0.414) * 360

# KEYFRAME JUPITER
jupiter.rotation_euler = (0, 0, 0)
jupiter.keyframe_insert(data_path="rotation_euler", frame=1)
jupiter.rotation_euler = (0, 0, math.radians(jupiter_total_degrees))
jupiter.keyframe_insert(data_path="rotation_euler", frame=240)

# KEYFRAME ALL MOONS
for m_data in moons_data:
    pivot_obj = m_data["pivot"]
    moon_mesh = m_data["moon"]
    period = m_data["period"]
    
    total_degrees = (earth_days_to_simulate / period) * 360
    
    pivot_obj.rotation_euler = (0, 0, 0)
    pivot_obj.keyframe_insert(data_path="rotation_euler", frame=1)
    pivot_obj.rotation_euler = (0, 0, math.radians(total_degrees))
    pivot_obj.keyframe_insert(data_path="rotation_euler", frame=240)
    
    moon_mesh.rotation_euler = (0, 0, 0)
    moon_mesh.keyframe_insert(data_path="rotation_euler", frame=1)
    moon_mesh.rotation_euler = (0, 0, math.radians(total_degrees))
    moon_mesh.keyframe_insert(data_path="rotation_euler", frame=240)

bpy.context.preferences.edit.keyframe_new_interpolation_type = original_interpolation

# OUTPUT SETTINGS
scene.render.filepath = "C:/blender/jupiter_compressed_system.mp4"
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
print("Done! Minor moons physically compressed and orbital rings tightly pulled inward.")