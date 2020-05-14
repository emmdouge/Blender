import bpy
from math import pi, sqrt, degrees, atan, radians
from mathutils import Matrix

bl_info = {
    "name": "Revoltech Joint",
    "author": "Emmanuel Douge",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "Pose Mode > Bone Properties",
    "description": "Move selected joint like a revoltech joint. "
                   "Locks rotation based on current rotation.",
    "warning": "",
    "category": "Animation"}
   
def get_pose_bone_matrix(pose_bone):
    local_matrix = pose_bone.matrix_channel.to_3x3()
    if pose_bone.parent is None:
        return local_matrix
    else:
        return pose_bone.parent.matrix_channel.to_3x3().inverted() @ local_matrix

def getRoll(bone):
    mat = bone.matrix.to_3x3()
    quat = mat.to_quaternion()
    if abs(quat.w) < 1e-4:
        roll = pi
    else:
        roll = 2*atan(quat.y/quat.w)
    return roll

def lock(self, context, x, y, z):
    delta = float(0.2)
    bone = context.active_pose_bone
    q = get_pose_bone_matrix(bone).to_quaternion()
    orientation = bpy.context.scene.transform_orientation_slots[0].type
    
    if orientation == 'LOCAL':
        if 1 == 1:
            lock = (-1*delta) <= z <= delta
            bone.lock_rotation[1] = False # y
            if lock:
                bone.lock_rotation[0] = False # x
            else:
                bone.lock_rotation[0] = True # x
        else:
            edit_bone.roll = Math.radians(90)
            lock = (-1*delta) <= z <= delta
            bone.lock_rotation[1] = False # y
            if lock:
                bone.lock_rotation[0] = False # x
            else:
                bone.lock_rotation[0] = True # x
                
    space = context.space_data
    if not space.show_gizmo:
        space.show_gizmo = True
        space.show_gizmo_object_rotate = True
        space.show_gizmo_tool = True
    
    # transform operator must be executed before modal
    # handler is added, otherwise it will block events    
class Revoltech(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Display Data"
    bl_idname = "BONE_PT_hello"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    #bl_context = "bone"

    @classmethod
    def poll(cls, context):
        return context.active_pose_bone is not None

    def draw(self, context):
        layout = self.layout

        delta = float(0.2)

        bone = context.active_pose_bone
        active_bone = context.active_bone
        armature = bone.id_data
        edit_bone = armature.data.edit_bones.active
        #debone = Matrix([[1,0,0,0],[0,0,-1,0], [0,1,0,0],[0,0,0,1]]) #because bones are wacky
        #m = armature.matrix_world @ bone.matrix @ debone

        q = get_pose_bone_matrix(bone).to_quaternion()

        row = layout.row()
        row.label(text="Active object is: " + bone.name)
        row = layout.row()
        row.label(text="Parent object is: " + bone.parent.name)
        row = layout.row()
        x = q[3]
        y = q[1]
        z = q[2]
        row.label(text="x is %.2f" % x)
        row.label(text="y is %.2f" % y)
        row.label(text="z is %.2f" % z)
        
        lock(self, context, x, y, z)
        
        bpy.context.area.tag_redraw()

        
def prop_redraw(scene):
    for area in bpy.context.screen.areas:
        if area.type == 'PROPERTIES':
            #printf ("active space: %s" % area.spaces.active.context)
            if area.spaces.active.context == 'BONE':
                area.tag_redraw()

def register():
    #clear handlers for testing
    bpy.app.handlers.render_post.clear()
    # add a handler to make the area "live" without mouse over
    bpy.app.handlers.render_post.append(prop_redraw)
    bpy.utils.register_class(Revoltech)

def unregister():
    bpy.utils.unregister_class(Revoltech)

if __name__ == "__main__":
    register()