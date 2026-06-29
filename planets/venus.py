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
# 🌌 STAR BACKGROUND (Procedural Stars & Shine)
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
# 1. CREATE VENUS (THICK ATMOSPHERE / SMOOTHER CLOUD SURFACE)
# =========================================================================
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1)
venus = bpy.context.object
venus.name = "Venus"
bpy.ops.object.shade_smooth()

# Venus Material
venus_mat = bpy.data.materials.new(name="VenusMaterial")
venus_mat.use_nodes = True
v_nodes = venus_mat.node_tree.nodes
v_links = venus_mat.node_tree.links
v_nodes.clear()

tex_venus = v_nodes.new(type='ShaderNodeTexImage')
try:
    tex_venus.image = bpy.data.images.load("C:/textures/venus_color.jpg")
except:
    print("Venus texture not found, using default atmospheric color.")

# Soft, sweeping atmospheric noise instead of sharp impact craters
noise_venus = v_nodes.new(type='ShaderNodeTexNoise')
noise_venus.inputs['Scale'].default_value = 12.0       
noise_venus.inputs['Detail'].default_value = 6.0      
noise_venus.inputs['Roughness'].default_value = 0.40   

bump_venus = v_nodes.new(type='ShaderNodeBump')
bump_venus.inputs['Strength'].default_value = 0.25     # Smooth cloud blankets
bump_venus.inputs['Distance'].default_value = 0.05     

bsdf_venus = v_nodes.new(type='ShaderNodeBsdfPrincipled')
bsdf_venus.inputs['Roughness'].default_value = 0.85     

out_venus = v_nodes.new(type='ShaderNodeOutputMaterial')

# Link Venus Nodes
v_links.new(tex_venus.outputs['Color'], bsdf_venus.inputs['Base Color'])
v_links.new(noise_venus.outputs['Fac'], bump_venus.inputs['Height'])
v_links.new(bump_venus.outputs['Normal'], bsdf_venus.inputs['Normal'])
v_links.new(bsdf_venus.outputs['BSDF'], out_venus.inputs['Surface'])

venus.data.materials.append(venus_mat)

# =========================================================================
# 2. CREATE FLOATING ASTEROIDS
# =========================================================================
ast_mat = bpy.data.materials.new(name="AsteroidMaterial")
ast_mat.use_nodes = True
a_nodes = ast_mat.node_tree.nodes
a_links = ast_mat.node_tree.links
a_nodes.clear()

tex_ast = a_nodes.new(type='ShaderNodeTexImage')
try:
    tex_ast.image = bpy.data.images.load("C:/textures/asteroid.jpg")
except:
    print("Asteroid texture not found, using default color.")

bsdf_ast = a_nodes.new(type='ShaderNodeBsdfPrincipled')
bsdf_ast.inputs['Roughness'].default_value = 0.9
out_ast = a_nodes.new(type='ShaderNodeOutputMaterial')

a_links.new(tex_ast.outputs['Color'], bsdf_ast.inputs['Base Color'])
a_links.new(bsdf_ast.outputs['BSDF'], out_ast.inputs['Surface'])

random.seed(42) 
for i in range(15):
    rad = random.uniform(0.04, 0.08)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=rad)
    asteroid = bpy.context.object
    asteroid.name = f"Asteroid_{i}"
    
    for vertex in asteroid.data.vertices:
        vertex.co.x += random.uniform(-0.015, 0.015)
        vertex.co.y += random.uniform(-0.015, 0.015)
        vertex.co.z += random.uniform(-0.015, 0.015)
        
    bpy.ops.object.shade_smooth()
    asteroid.data.materials.append(ast_mat)
    
    angle = random.uniform(0, math.pi * 2)
    height = random.uniform(-0.6, 0.6)
    dist = random.uniform(1.4, 2.2)
    
    asteroid.location = (math.cos(angle) * dist, math.sin(angle) * dist, height)
    asteroid.parent = venus

# =========================================================================
# 3. 🦂 SCORPIO CONSTELLATION (Positioned Upper-Left in Flat Camera View)
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
    (-4.70, 10, 3.15),  # 0
    (-4.95, 10, 2.95),  # 1
    (-4.85, 10, 2.70),  # 2
    (-4.50, 10, 2.60),  # 3
    (-4.25, 10, 2.65),  # 4
    (-4.00, 10, 3.20),  # 5
    (-3.75, 10, 3.60),  # 6
    (-3.55, 10, 3.70),  # 7  Antares
    (-3.10, 10, 4.00),  # 8
    (-3.00, 10, 3.75),  # 9
    (-3.20, 10, 3.50),  # 10
]

for idx, coord in enumerate(scorpio_stars_coords):
    is_antares = (idx == 7)
    is_dschubba = (idx == 1)

    if is_antares:
        size = 0.065
    elif is_dschubba:
        size = 0.045
    else:
        size = random.uniform(0.02, 0.03)

    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=size, location=coord)
    star = bpy.context.object
    star.name = f"Scorpio_Star_{idx}"
    
    if is_antares:
        antares_mat = bpy.data.materials.new(name="AntaresMaterial")
        antares_mat.use_nodes = True
        an_nodes = antares_mat.node_tree.nodes
        an_nodes.clear()
        an_emit = an_nodes.new(type='ShaderNodeEmission')
        an_emit.inputs['Strength'].default_value = 10.0
        an_emit.inputs['Color'].default_value = (1.0, 0.35, 0.05, 1.0)
        an_out = an_nodes.new(type='ShaderNodeOutputMaterial')
        antares_mat.node_tree.links.new(an_emit.outputs['Emission'], an_out.inputs['Surface'])
        star.data.materials.append(antares_mat)
    else:
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
# 💡 LIGHTING
# =========================================================================
bpy.ops.object.light_add(type='SUN', location=(6, -6, 6))
key_light = bpy.context.object
key_light.name = "UpperRight_Key"
key_light.data.energy = 8.0
key_light.rotation_euler = (math.radians(65), 0, math.radians(-40))

bpy.ops.object.light_add(type='SUN', location=(-4, -4, -3))
fill_light = bpy.context.object
fill_light.name = "LowerLeft_Fill"
fill_light.data.energy = 3.0
fill_light.rotation_euler = (math.radians(120), 0, math.radians(140))

# =========================================================================
# CAMERA
# =========================================================================
bpy.ops.object.camera_add(location=(0, -6, 0))
camera = bpy.context.object
camera.rotation_euler = (math.radians(90), 0, 0)
camera.data.lens = 24 
scene.camera = camera

# =========================================================================
# ⏱️ SCIENTIFICALLY SCALE ANIMATION (5 Earth Days over 10 Seconds)
# =========================================================================
original_interpolation = bpy.context.preferences.edit.keyframe_new_interpolation_type
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'

# 1 Sidereal Rotation of Venus = 243 Earth Days.
# Calculation: (5 Days / 243 Days) * 360 Degrees = 7.407 Degrees
# NOTICE THE NEGATIVE SIGN: Venus rotates in a clockwise (Retrograde) direction!
earth_days_to_simulate = 5
venus_sidereal_rotation_period = 243
venus_total_degrees = -(earth_days_to_simulate / venus_sidereal_rotation_period) * 360

# --- Keyframe Venus (Axial Retrograde Rotation) ---
venus.rotation_euler = (0, 0, 0)
venus.keyframe_insert(data_path="rotation_euler", frame=1)

venus.rotation_euler = (0, 0, math.radians(venus_total_degrees))
venus.keyframe_insert(data_path="rotation_euler", frame=240)

# Restore original user preference setting
bpy.context.preferences.edit.keyframe_new_interpolation_type = original_interpolation

# OUTPUT SETTINGS
scene.render.filepath = "C:/blender/venus_animation.mp4"
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
print(f"Done! Scaled Venus retrograde rotation to {earth_days_to_simulate} Earth days ({venus_total_degrees:.2f}°).")