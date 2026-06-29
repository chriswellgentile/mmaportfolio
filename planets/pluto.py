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
# 🌀 HELPER: CREATE & DEFORM WORLD BODIES
# =========================================================================
def generate_plutonian_body(name, radius, texture_path, shape_type="sphere"):
    if shape_type == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=radius)
    else:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=radius)
        
    obj = bpy.context.object
    obj.name = name
    
    # Apply unique irregular structures to the minor moons based on New Horizons data
    if shape_type == "elongated_potato": # Nix / Hydra profile
        for vertex in obj.data.vertices:
            vertex.co.x *= 1.60
            vertex.co.y *= 0.95
            vertex.co.z *= 0.80
    elif shape_type == "lumpy":            # Styx / Kerberos profile
        for vertex in obj.data.vertices:
            vertex.co.x *= random.uniform(1.20, 1.35)
            vertex.co.y *= random.uniform(1.10, 1.25)
            vertex.co.z *= random.uniform(0.75, 0.90)

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
        print(f"Texture asset '{texture_path}' not found, applying default map.")
        
    bsdf = m_nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Roughness'].default_value = 0.90
    out = m_nodes.new(type='ShaderNodeOutputMaterial')
    
    m_links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    m_links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    obj.data.materials.append(mat)
    
    return obj

# =========================================================================
# 🏛️ SYSTEM RIGGING (THE PLUTO-CHARON BARYCENTER)
# =========================================================================
random.seed(999)
moons_data = []

# Create central tracking empty to act as the gravitational center of mass
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
system_barycenter = bpy.context.object
system_barycenter.name = "Pluto_Charon_Barycenter"

# --- 1. PLUTO ---
pluto = generate_plutonian_body("Pluto", 0.65, "C:/textures/pluto_color.jpg", shape_type="sphere")
# Offset from barycenter (Pluto is heavier, so it stays closer to the center)
pluto.location = (0.25, 0, 0)
pluto.parent = system_barycenter

# --- 2. CHARON (THE BIG MOON) ---
charon = generate_plutonian_body("Charon", 0.33, "C:/textures/charon.jpg", shape_type="sphere")
# Offset opposite to Pluto across the barycenter line
charon.location = (-0.75, 0, 0)
charon.parent = system_barycenter

# Shared tidal binary lock metadata values
pluto_charon_period = -6.387

# --- 3. THE MINOR MOONS (Orbits around the shared barycenter) ---
minor_configs = [
    {"name": "Styx", "rad": 0.020, "dist": 1.4, "period": -20.16, "shape": "lumpy", "tex": "C:/textures/moon.jpg"},
    {"name": "Nix", "rad": 0.042, "dist": 1.8, "period": -24.85, "shape": "elongated_potato", "tex": "C:/textures/nix.jpg"},
    {"name": "Kerberos", "rad": 0.024, "dist": 2.3, "period": -32.16, "shape": "lumpy", "tex": "C:/textures/moon.jpg"},
    {"name": "Hydra", "rad": 0.055, "dist": 2.8, "period": -38.20, "shape": "elongated_potato", "tex": "C:/textures/hydra.jpg"}
]

for config in minor_configs:
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    orbit_pivot = bpy.context.object
    orbit_pivot.name = f"{config['name']}_Orbit_Center"
    orbit_pivot.parent = system_barycenter
    
    moon_obj = generate_plutonian_body(config['name'], config['rad'], config['tex'], shape_type=config['shape'])
    
    start_angle = random.uniform(0, math.pi * 2)
    moon_obj.location = (math.cos(start_angle) * config['dist'], math.sin(start_angle) * config['dist'], random.uniform(-0.02, 0.02))
    moon_obj.parent = orbit_pivot
    
    moons_data.append({"pivot": orbit_pivot, "moon": moon_obj, "period": config['period']})

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
    (-4.70, 10, 3.15), (-4.95, 10, 2.95), (-4.85, 10, 2.70), (-4.50, 10, 2.60),
    (-4.25, 10, 2.65), (-4.00, 10, 3.20), (-3.75, 10, 3.60), (-3.55, 10, 3.70),
    (-3.10, 10, 4.00), (-3.00, 10, 3.75), (-3.20, 10, 3.50)
]

for idx, coord in enumerate(scorpio_stars_coords):
    size = 0.065 if idx == 7 else random.uniform(0.02, 0.03)
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
bpy.ops.object.light_add(type='SUN', location=(6, -6, 6))
key_light = bpy.context.object
key_light.data.energy = 7.0
key_light.rotation_euler = (math.radians(65), 0, math.radians(-40))

bpy.ops.object.camera_add(location=(0, -5.5, 0))
camera = bpy.context.object
camera.rotation_euler = (math.radians(90), 0, 0)
camera.data.lens = 26 
scene.camera = camera

# =========================================================================
# ⏱️ SCIENTIFICALLY SCALE ANIMATION (5 Earth Days over 10 Seconds)
# =========================================================================
original_interpolation = bpy.context.preferences.edit.keyframe_new_interpolation_type
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'

earth_days_to_simulate = 5

# --- Mutual Binary Lock Rotations ---
binary_total_degrees = (earth_days_to_simulate / pluto_charon_period) * 360

# Keyframe the central system barycenter pivot (simulating orbital revolution of Pluto and Charon around each other)
system_barycenter.rotation_euler = (0, 0, 0)
system_barycenter.keyframe_insert(data_path="rotation_euler", frame=1)
system_barycenter.rotation_euler = (0, 0, math.radians(binary_total_degrees))
system_barycenter.keyframe_insert(data_path="rotation_euler", frame=240)

# Local rotation animations to keep them locked facing one another
pluto.rotation_euler = (0, 0, 0)
pluto.keyframe_insert(data_path="rotation_euler", frame=1)
pluto.rotation_euler = (0, 0, math.radians(binary_total_degrees))
pluto.keyframe_insert(data_path="rotation_euler", frame=240)

charon.rotation_euler = (0, 0, 0)
charon.keyframe_insert(data_path="rotation_euler", frame=1)
charon.rotation_euler = (0, 0, math.radians(binary_total_degrees))
charon.keyframe_insert(data_path="rotation_euler", frame=240)

# --- Keyframe the Minor Outer Moons ---
for m_data in moons_data:
    pivot_obj = m_data["pivot"]
    moon_mesh = m_data["moon"]
    period = m_data["period"]
    
    total_degrees = (earth_days_to_simulate / period) * 360
    
    pivot_obj.rotation_euler = (0, 0, 0)
    pivot_obj.keyframe_insert(data_path="rotation_euler", frame=1)
    pivot_obj.rotation_euler = (0, 0, math.radians(total_degrees))
    pivot_obj.keyframe_insert(data_path="rotation_euler", frame=240)
    
    # Minor moons do not have synchronous locks due to severe chaotic system tumbles, 
    # but we rotate them relative to their path here for visual engine tracking.
    moon_mesh.rotation_euler = (0, 0, 0)
    moon_mesh.keyframe_insert(data_path="rotation_euler", frame=1)
    moon_mesh.rotation_euler = (0, 0, math.radians(total_degrees * 1.5))
    moon_mesh.keyframe_insert(data_path="rotation_euler", frame=240)

bpy.context.preferences.edit.keyframe_new_interpolation_type = original_interpolation

# OUTPUT SETTINGS
scene.render.filepath = "C:/blender/pluto_system_animation.mp4"
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
print("Done! Pluto-Charon binary barycenter rig and minor deformed satellites successfully built.")