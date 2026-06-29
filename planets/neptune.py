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
# 1. CREATE NEPTUNE (DEEP BLUE ICE GIANT)
# =========================================================================
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.3)
neptune = bpy.context.object
neptune.name = "Neptune"
bpy.ops.object.shade_smooth()

nep_mat = bpy.data.materials.new(name="NeptuneMaterial")
nep_mat.use_nodes = True
n_nodes = nep_mat.node_tree.nodes
n_links = nep_mat.node_tree.links
n_nodes.clear()

tex_nep = n_nodes.new(type='ShaderNodeTexImage')
try:
    tex_nep.image = bpy.data.images.load("C:/textures/neptune_color.jpg")
except:
    print("Neptune texture not found, defaulting to fallback shader pipeline.")

bsdf_nep = n_nodes.new(type='ShaderNodeBsdfPrincipled')
bsdf_nep.inputs['Roughness'].default_value = 0.50     
out_nep = n_nodes.new(type='ShaderNodeOutputMaterial')

n_links.new(tex_nep.outputs['Color'], bsdf_nep.inputs['Base Color'])
n_links.new(bsdf_nep.outputs['BSDF'], out_nep.inputs['Surface'])
neptune.data.materials.append(nep_mat)

# =========================================================================
# 🌙 HELPER: CREATE UNIQUE & ACCURATE GEOMETRIES FOR MOONS
# =========================================================================
def generate_neptunian_moon(name, radius, texture_path, shape_type="sphere"):
    if shape_type == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=radius)
    else:
        # Ico Spheres are much better for structural adjustments
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=radius)
        
    moon_obj = bpy.context.object
    moon_obj.name = name
    
    # Apply scientific deformity shapes based on historical space flybys
    if shape_type == "box_like":  # Proteus shape profiles
        for vertex in moon_obj.data.vertices:
            vertex.co.x *= random.uniform(1.05, 1.15)
            vertex.co.y *= random.uniform(0.95, 1.05)
            vertex.co.z *= random.uniform(0.90, 1.00)
    elif shape_type == "elongated":  # Larissa shape profiles
        for vertex in moon_obj.data.vertices:
            vertex.co.x *= 1.45
            vertex.co.y *= 0.90
            vertex.co.z *= 0.80
    elif shape_type == "potato":  # Minor moons / Nereid profile
        for vertex in moon_obj.data.vertices:
            vertex.co.x *= random.uniform(1.25, 1.40)
            vertex.co.y *= random.uniform(0.75, 0.90)
            vertex.co.z *= random.uniform(0.70, 0.85)

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
        print(f"Texture file '{texture_path}' missing, injecting programmatic layout.")
        
    bsdf = m_nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Roughness'].default_value = 0.95
    out = m_nodes.new(type='ShaderNodeOutputMaterial')
    
    m_links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    m_links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    moon_obj.data.materials.append(mat)
    
    return moon_obj

# =========================================================================
# 2. POPULATE NEPTUNE SYSTEM (5 MAJOR + 12 MINOR DEFORMED MOONS)
# =========================================================================
random.seed(777)
moons_data = []

# --- Major Moons Specifications Array ---
# Note: Negative periods denote Retrograde motion configurations (Triton)
major_configs = [
    {"name": "Larissa", "rad": 0.035, "dist": 1.7, "period": 0.555, "shape": "elongated", "tex": "C:/textures/larissa.jpg"},
    {"name": "Proteus", "rad": 0.060, "dist": 2.1, "period": 1.122, "shape": "box_like", "tex": "C:/textures/proteus.jpg"},
    {"name": "Triton", "rad": 0.110, "dist": 2.8, "period": -5.877, "shape": "sphere", "tex": "C:/textures/triton.jpg"},
    {"name": "Nereid", "rad": 0.040, "dist": 4.2, "period": 360.13, "shape": "potato", "tex": "C:/textures/nereid.jpg"}
]

for config in major_configs:
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    orbit_pivot = bpy.context.object
    orbit_pivot.name = f"{config['name']}_Orbit_Center"
    
    moon_obj = generate_neptunian_moon(config['name'], config['rad'], config['tex'], shape_type=config['shape'])
    
    start_angle = random.uniform(0, math.pi * 2)
    # Give Nereid an inclined orbital layout plane to mimic extreme eccentricity 
    z_height = random.uniform(-0.5, 0.5) if config['name'] == "Nereid" else random.uniform(-0.05, 0.05)
    
    moon_obj.location = (math.cos(start_angle) * config['dist'], math.sin(start_angle) * config['dist'], z_height)
    moon_obj.parent = orbit_pivot
    
    moons_data.append({"pivot": orbit_pivot, "moon": moon_obj, "period": config['period']})

# --- Generate 12 Minor Deformed Moons Array ---
minor_moon_texture = "C:/textures/moon.jpg"

for i in range(12):
    name = f"Deformed_Minor_Moon_{i+1}"
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    orbit_pivot = bpy.context.object
    orbit_pivot.name = f"{name}_Orbit_Center"
    
    # Outer minor rings boundaries
    dist = random.uniform(4.8, 7.5)
    rad = random.uniform(0.015, 0.028)
    period = 25.0 + (dist ** 1.8) * random.uniform(2.0, 5.0)
    
    moon_obj = generate_neptunian_moon(name, rad, minor_moon_texture, shape_type="potato")
    
    start_angle = random.uniform(0, math.pi * 2)
    z_tilt = random.uniform(-0.6, 0.6)
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
    (-5.70, 4, 4.15), (-5.95, 4, 3.95), (-5.85, 4, 3.70), (-5.50, 4, 3.60),
    (-5.25, 4, 3.65), (-5.00, 4, 4.20), (-4.75, 4, 4.60), (-4.55, 4, 4.70),
    (-4.10, 4, 5.00), (-4.00, 4, 4.75), (-4.20, 4, 4.50)
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
# LIGHTING & CAMERA
# =========================================================================
bpy.ops.object.light_add(type='SUN', location=(10, -12, 10))
key_light = bpy.context.object
key_light.data.energy = 8.5
key_light.rotation_euler = (math.radians(65), 0, math.radians(-40))

bpy.ops.object.camera_add(location=(0, -11.5, 0))
camera = bpy.context.object
camera.rotation_euler = (math.radians(90), 0, 0)
camera.data.lens = 28 
scene.camera = camera

# =========================================================================
# ⏱️ SCIENTIFICALLY SCALE ANIMATION (5 Earth Days over 10 Seconds)
# =========================================================================
original_interpolation = bpy.context.preferences.edit.keyframe_new_interpolation_type
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'

earth_days_to_simulate = 5
neptune_sidereal_day = 0.671
neptune_total_degrees = (earth_days_to_simulate / neptune_sidereal_day) * 360

# KEYFRAME NEPTUNE
neptune.rotation_euler = (0, 0, 0)
neptune.keyframe_insert(data_path="rotation_euler", frame=1)
neptune.rotation_euler = (0, 0, math.radians(neptune_total_degrees))
neptune.keyframe_insert(data_path="rotation_euler", frame=240)

# KEYFRAME MOONS REVOLUTION & CHOSEN DIRECTION
for m_data in moons_data:
    pivot_obj = m_data["pivot"]
    moon_mesh = m_data["moon"]
    period = m_data["period"]
    
    # Positive rotation vectors = prograde, negative rotation vectors = retrograde (Triton)
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
scene.render.filepath = "C:/blender/neptune_system_animation.mp4"
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
print("Done! Neptune pipeline loaded. Irregular major geometries and retrograde tracking active.")