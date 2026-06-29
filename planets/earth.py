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
# 1. CREATE EARTH (EXTRA ROUGH SURFACE)
# =========================================================================
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1)
earth = bpy.context.object
earth.name = "Earth"
bpy.ops.object.shade_smooth()

earth_mat = bpy.data.materials.new(name="EarthMaterial")
earth_mat.use_nodes = True
e_nodes = earth_mat.node_tree.nodes
e_links = earth_mat.node_tree.links
e_nodes.clear()

tex_earth = e_nodes.new(type='ShaderNodeTexImage')
try:
    tex_earth.image = bpy.data.images.load("C:/textures/earth_color.jpeg")
except:
    print("Earth texture not found, using default color.")

noise_earth = e_nodes.new(type='ShaderNodeTexNoise')
noise_earth.inputs['Scale'].default_value = 25.0       
noise_earth.inputs['Detail'].default_value = 15.0     
noise_earth.inputs['Roughness'].default_value = 0.7    

bump_earth = e_nodes.new(type='ShaderNodeBump')
bump_earth.inputs['Strength'].default_value = 0.85     
bump_earth.inputs['Distance'].default_value = 0.2

bsdf_earth = e_nodes.new(type='ShaderNodeBsdfPrincipled')
bsdf_earth.inputs['Roughness'].default_value = 1.0     

out_earth = e_nodes.new(type='ShaderNodeOutputMaterial')

e_links.new(tex_earth.outputs['Color'], bsdf_earth.inputs['Base Color'])
e_links.new(noise_earth.outputs['Fac'], bump_earth.inputs['Height'])
e_links.new(bump_earth.outputs['Normal'], bsdf_earth.inputs['Normal'])
e_links.new(bsdf_earth.outputs['BSDF'], out_earth.inputs['Surface'])

earth.data.materials.append(earth_mat)

# =========================================================================
# 🌙 CREATE THE MOON & ORBITAL RIG
# =========================================================================
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
orbit_center = bpy.context.object
orbit_center.name = "Moon_Orbit_Center"

bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.27)
moon = bpy.context.object
moon.name = "Moon"
bpy.ops.object.shade_smooth()

# CHANGED: Flipped X-coordinate to start on the LEFT side (-2.6 instead of 2.6)
moon.location = (-2.6, 1.2, -0.4)
moon.parent = orbit_center  

moon_mat = bpy.data.materials.new(name="MoonMaterial")
moon_mat.use_nodes = True
m_nodes = moon_mat.node_tree.nodes
m_links = moon_mat.node_tree.links
m_nodes.clear()

tex_moon = m_nodes.new(type='ShaderNodeTexImage')
try:
    tex_moon.image = bpy.data.images.load("C:/textures/moon.jpg")
except:
    print("Moon texture not found, using default color.")

noise_moon = m_nodes.new(type='ShaderNodeTexNoise')
noise_moon.inputs['Scale'].default_value = 40.0
noise_moon.inputs['Detail'].default_value = 8.0

bump_moon = m_nodes.new(type='ShaderNodeBump')
bump_moon.inputs['Strength'].default_value = 0.4
bump_moon.inputs['Distance'].default_value = 0.1

bsdf_moon = m_nodes.new(type='ShaderNodeBsdfPrincipled')
bsdf_moon.inputs['Roughness'].default_value = 0.95

out_moon = m_nodes.new(type='ShaderNodeOutputMaterial')

m_links.new(tex_moon.outputs['Color'], bsdf_moon.inputs['Base Color'])
m_links.new(noise_moon.outputs['Fac'], bump_moon.inputs['Height'])
m_links.new(bump_moon.outputs['Normal'], bsdf_moon.inputs['Normal'])
m_links.new(bsdf_moon.outputs['BSDF'], out_moon.inputs['Surface'])

moon.data.materials.append(moon_mat)

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
# ⏱️ ANIMATION SEQUENCING (10 Seconds @ 24 FPS = 240 Frames)
# =========================================================================
original_interpolation = bpy.context.preferences.edit.keyframe_new_interpolation_type
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'

# Earth spins exactly 5 times (1800 degrees total)
total_earth_rotations = 5
earth_total_degrees = 360 * total_earth_rotations

# Calculate Moon's orbital travel over 5 Earth days
moon_total_degrees = (total_earth_rotations / 27.3) * 360

# --- Keyframe Earth (Axial Rotation) ---
earth.rotation_euler = (0, 0, 0)
earth.keyframe_insert(data_path="rotation_euler", frame=1)

earth.rotation_euler = (0, 0, math.radians(earth_total_degrees))
earth.keyframe_insert(data_path="rotation_euler", frame=240)

# --- Keyframe Moon Orbit (Revolution via Empty Rig) ---
orbit_center.rotation_euler = (0, 0, 0)
orbit_center.keyframe_insert(data_path="rotation_euler", frame=1)

orbit_center.rotation_euler = (0, 0, math.radians(moon_total_degrees))
orbit_center.keyframe_insert(data_path="rotation_euler", frame=240)

# --- Keyframe Moon Object (Tidal Lock Axial Rotation) ---
# To keep the same side facing Earth, the moon's local rotation must match its orbital rate
moon.rotation_euler = (0, 0, 0)
moon.keyframe_insert(data_path="rotation_euler", frame=1)

moon.rotation_euler = (0, 0, math.radians(moon_total_degrees))
moon.keyframe_insert(data_path="rotation_euler", frame=240)

# Restore original user preference setting
bpy.context.preferences.edit.keyframe_new_interpolation_type = original_interpolation

# OUTPUT SETTINGS
scene.render.filepath = "C:/blender/earth_animation.mp4"
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
print("Done! Moon moved to the left and accurate tidal rotation applied.")