import bpy
from mathutils import Vector
import bmesh
from math import radians

scene = bpy.context.scene

def spiralUVs(mesh, xPlus):
	# add a UV layer called "spiral" and make it slanted.
	lm = mesh.uv_textures.new("spiral")
	bm = bmesh.new()
	bm.from_mesh(mesh)

	uv_layer = bm.loops.layers.uv[0]

	nFaces = len(bm.faces)
	bm.faces.ensure_lookup_table()
	for fi in range(nFaces):
		x0 = fi*2/nFaces
		x1 = (fi+1)*2/nFaces
		bm.faces[fi].loops[0][uv_layer].uv = (x0, 0)
		bm.faces[fi].loops[1][uv_layer].uv = (x1, 0)
		bm.faces[fi].loops[2][uv_layer].uv = (xPlus+x1, 1)
		bm.faces[fi].loops[3][uv_layer].uv = (xPlus+x0, 1)
		bm.to_mesh(mesh)

def FindActiveObjectInObjectMode():
	# Create a list of all the selected objects
	selected = bpy.context.selected_objects
	# Loop through all selected objects and add a modifier to each.
	for obj in selected:
		if obj == bpy.context.active_object:
			bpy.context.scene.objects.active = obj
		else:
			obj.select = False
			
def GetClosestObject(point):
	#YOUR point in 3D
	dist = []
	for i,obj in enumerate(bpy.data.objects[:]):
		#print(obj.name)
		dist.append([(point-obj.location).length,i])
		
	dist.sort()
	#print(dist)	
	print(bpy.data.objects[dist[0][1]].name)
				   
def main():
	if(bpy.context.object.mode != 'EDIT'):
		return 

	# we need to switch from Edit mode to Object mode so the selection gets updated
	bpy.ops.object.mode_set(mode='OBJECT')

	point = Vector((1,2,3))
	#selectedVerts = [v for v in bpy.context.active_object.data.vertices if v.select]
	#print(selectedVerts[0])
	#print(bpy.context.active_object)
	bpy.context.active_object.select = True
	bpy.context.scene.tool_settings.use_uv_select_sync = False
	bpy.ops.object.mode_set(mode='EDIT')

	scene = bpy.context.scene
	object = bpy.context.object
	mesh = bpy.context.object.data
		
	bpy.ops.object.mode_set(mode='OBJECT')
	spiralUVs(mesh, 0)

	uvs_layer = mesh.uv_layers[0]

	#Create control armature
	uvs_data = bpy.data.armatures.new('UVs')
	uvs_obj = bpy.data.objects.new('UVs', uvs_data)
	scene.objects.link(uvs_obj)

	bpy.ops.object.mode_set(mode='OBJECT')
	
	for uv in uvs_layer.data:
		
		scene.objects.active = object
	
		uv.pin_uv = True
		
		if uv.pin_uv:
			bone_name = 'uv_%s_%s' % (round(uv.uv.x, 2), round(uv.uv.y, 2))
			
			print (bone_name)
			
			# Create bone if it doesn't exist already
			scene.objects.active = uvs_obj
			bpy.ops.object.mode_set(mode='EDIT')
			
			if not bone_name in uvs_data.edit_bones:
				bone = uvs_data.edit_bones.new(bone_name)
				bone.tail = (uv.uv.x-0.5, -0.1, uv.uv.y-0.5)
				bone.head = (uv.uv.x-0.5, 0.0, uv.uv.y-0.5)
				
			# UV X
			# Create driver
			driver = uv.driver_add('uv', 0)
			
			# Remove the useless modifier
			driver.modifiers.remove(driver.modifiers[0])
			
			# Add Transform Channel variable
			variable = driver.driver.variables.new()
			variable.type = 'TRANSFORMS'
			variable.name = 'uv_x'
			
			# Set target
			variable.targets[0].id = uvs_obj
			variable.targets[0].bone_target = bone_name
			variable.targets[0].transform_type = 'LOC_X'
			variable.targets[0].transform_space = 'LOCAL_SPACE'
			
			bpy.ops.object.mode_set(mode='OBJECT')
			
			driver.driver.expression = 'uv_x + %s' % (uv.uv.x)
			
			# UV Y
			# Create driver
			driver = uv.driver_add('uv', 1)
			
			# Remove the useless modifier
			driver.modifiers.remove(driver.modifiers[0])
			
			# Add Transform Channel variable
			variable = driver.driver.variables.new()
			variable.type = 'TRANSFORMS'
			variable.name = 'uv_y'
			
			# Set target
			variable.targets[0].id = uvs_obj
			variable.targets[0].bone_target = bone_name
			variable.targets[0].transform_type = 'LOC_Z'
			variable.targets[0].transform_space = 'LOCAL_SPACE'
			
			bpy.ops.object.mode_set(mode='OBJECT')
			
			driver.driver.expression = '-uv_y + %s' % (uv.uv.y)

	bpy.context.active_object.select = True
	const = bpy.context.active_object.constraints.new(type='CHILD_OF')
	const.target = object

main()