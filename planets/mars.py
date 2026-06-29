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
# 1. CREATE MARS
# =========================================================================
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1)
mars = bpy.context.object
mars.name = "Mars"
bpy.ops.object.shade_smooth()

mars_mat = bpy.data.materials.new(name="MarsMaterial")
mars_mat.use_nodes = True
ma_nodes = mars_mat.node_tree.nodes
ma_links = mars_mat.node_tree.links
ma_nodes.clear()

tex_mars = ma_nodes.new(type='ShaderNodeTexImage')
try:
    tex_mars.image = bpy.data.images.load("C:/textures/mars_color.jpg")
except:
    print("Mars texture not found, using default reddish color.")

noise_mars = ma_nodes.new(type='ShaderNodeTexNoise')
noise_mars.inputs['Scale'].default_value = 30.0       
noise_mars.inputs['Detail'].default_value = 12.0      
noise_mars.inputs['Roughness'].default_value = 0.65   

bump_mars = ma_nodes.new(type='ShaderNodeBump')
bump_mars.inputs['Strength'].default_value = 0.70     
bump_mars.inputs['Distance'].default_value = 0.15     

bsdf_mars = ma_nodes.new(type='ShaderNodeBsdfPrincipled')
bsdf_mars.inputs['Roughness'].default_value = 0.90     

out_mars = ma_nodes.new(type='ShaderNodeOutputMaterial')

ma_links.new(tex_mars.outputs['Color'], bsdf_mars.inputs['Base Color'])
ma_links.new(noise_mars.outputs['Fac'], bump_mars.inputs['Height'])
ma_links.new(bump_mars.outputs['Normal'], bsdf_mars.inputs['Normal'])
ma_links.new(bsdf_mars.outputs['BSDF'], out_mars.inputs['Surface'])

mars.data.materials.append(mars_mat)

# =========================================================================
# 🌙 CREATE MARTIAN MOONS WITH SEVERE DEFORMITY
# =========================================================================
random.seed(101)

# --- PHOBOS RIG ---
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
phobos_orbit_center = bpy.context.object
phobos_orbit_center.name = "Phobos_Orbit_Center"

bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=0.09)
phobos = bpy.context.object
phobos.name = "Phobos"

for vertex in phobos.data.vertices:
    vertex.co.x *= 1.35
    vertex.co.y *= 0.95
    vertex.co.z *= 0.85
    disp_x = math.sin(vertex.co.y * 15.0) * 0.015
    disp_y = math.cos(vertex.co.z * 15.0) * 0.015
    disp_z = math.sin(vertex.co.x * 12.0) * 0.012
    vertex.co.x += disp_x
    vertex.co.y += disp_y
    vertex.co.z += disp_z

bpy.ops.object.shade_smooth()
phobos.location = (-1.5, 0.4, 0.1)  
phobos.parent = phobos_orbit_center

# Phobos Material (FIXED LINKS)
phobos_mat = bpy.data.materials.new(name="PhobosMaterial")
phobos_mat.use_nodes = True
ph_nodes = phobos_mat.node_tree.nodes
ph_links = phobos_mat.node_tree.links  # <-- Added links handle
ph_nodes.clear()

tex_phobos = ph_nodes.new(type='ShaderNodeTexImage')
try:
    tex_phobos.image = bpy.data.images.load("C:/textures/phobos.jpg")
except:
    print("Phobos texture not found.")

bsdf_phobos = ph_nodes.new(type='ShaderNodeBsdfPrincipled')
out_phobos = ph_nodes.new(type='ShaderNodeOutputMaterial')

ph_links.new(tex_phobos.outputs['Color'], bsdf_phobos.inputs['Base Color'])
ph_links.new(bsdf_phobos.outputs['BSDF'], out_phobos.inputs['Surface'])
phobos.data.materials.append(phobos_mat)


# --- DEIMOS RIG ---
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
deimos_orbit_center = bpy.context.object
deimos_orbit_center.name = "Deimos_Orbit_Center"

bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=0.05)
deimos = bpy.context.object
deimos.name = "Deimos"

for vertex in deimos.data.vertices:
    vertex.co.x *= 0.90
    vertex.co.y *= 1.40
    vertex.co.z *= 0.80
    disp_x = math.cos(vertex.co.z * 22.0) * 0.008
    disp_y = math.sin(vertex.co.x * 22.0) * 0.008
    disp_z = math.cos(vertex.co.y * 18.0) * 0.006
    vertex.co.x += disp_x
    vertex.co.y += disp_y
    vertex.co.z += disp_z

bpy.ops.object.shade_smooth()
deimos.location = (-2.4, -0.6, -0.2)  
deimos.parent = deimos_orbit_center

# Deimos Material (FIXED LINKS)
deimos_mat = bpy.data.materials.new(name="DeimosMaterial")
deimos_mat.use_nodes = True
de_nodes = deimos_mat.node_tree.nodes
de_links = deimos_mat.node_tree.links  # <-- Added links handle
de_nodes.clear()

tex_deimos = de_nodes.new(type='ShaderNodeTexImage')
try:
    tex_deimos.image = bpy.data.images.load("C:/textures/deimos.jpg")
except:
    print("Deimos texture not found.")

bsdf_deimos = de_nodes.new(type='ShaderNodeBsdfPrincipled')
out_deimos = de_nodes.new(type='ShaderNodeOutputMaterial')

de_links.new(tex_deimos.outputs['Color'], bsdf_deimos.inputs['Base Color'])
de_links.new(bsdf_deimos.outputs['BSDF'], out_deimos.inputs['Surface'])
deimos.data.materials.append(deimos_mat)

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
    size = 0.065 if idx == 7 else (0.045 if idx == 1 else random.uniform(0.02, 0.03))
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
key_light.data.energy = 8.0
key_light.rotation_euler = (math.radians(65), 0, math.radians(-40))

bpy.ops.object.light_add(type='SUN', location=(-4, -4, -3))
fill_light = bpy.context.object
fill_light.data.energy = 3.0
fill_light.rotation_euler = (math.radians(120), 0, math.radians(140))

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

earth_days_to_simulate = 5
mars_total_degrees = (earth_days_to_simulate / 1.026) * 360
phobos_total_degrees = (earth_days_to_simulate / 0.318) * 360
deimos_total_degrees = (earth_days_to_simulate / 1.263) * 360

# KEYFRAME MARS
mars.rotation_euler = (0, 0, 0)
mars.keyframe_insert(data_path="rotation_euler", frame=1)
mars.rotation_euler = (0, 0, math.radians(mars_total_degrees))
mars.keyframe_insert(data_path="rotation_euler", frame=240)

# KEYFRAME PHOBOS
phobos_orbit_center.rotation_euler = (0, 0, 0)
phobos_orbit_center.keyframe_insert(data_path="rotation_euler", frame=1)
phobos_orbit_center.rotation_euler = (0, 0, math.radians(phobos_total_degrees))
phobos_orbit_center.keyframe_insert(data_path="rotation_euler", frame=240)

phobos.rotation_euler = (0, 0, 0)
phobos.keyframe_insert(data_path="rotation_euler", frame=1)
phobos.rotation_euler = (0, 0, math.radians(phobos_total_degrees))
phobos.keyframe_insert(data_path="rotation_euler", frame=240)

# KEYFRAME DEIMOS
deimos_orbit_center.rotation_euler = (0, 0, 0)
deimos_orbit_center.keyframe_insert(data_path="rotation_euler", frame=1)
deimos_orbit_center.rotation_euler = (0, 0, math.radians(deimos_total_degrees))
deimos_orbit_center.keyframe_insert(data_path="rotation_euler", frame=240)

deimos.rotation_euler = (0, 0, 0)
deimos.keyframe_insert(data_path="rotation_euler", frame=1)
deimos.rotation_euler = (0, 0, math.radians(deimos_total_degrees))
deimos.keyframe_insert(data_path="rotation_euler", frame=240)

bpy.context.preferences.edit.keyframe_new_interpolation_type = original_interpolation

# OUTPUT SETTINGS
scene.render.filepath = "C:/blender/mars_animation.mp4"
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
print("Done! Fixed both material node link bugs.")