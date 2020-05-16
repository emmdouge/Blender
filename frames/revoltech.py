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
    mat = bone.matrix_local.to_3x3()
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
    
class BONE_OT_GRZ(bpy.types.Operator):
    bl_idname = "bone.grz"
    bl_label = "Gizmo Rotate Z"
    bl_options = {'REGISTER', 'UNDO'}
    
    #@classmethod
    #def poll(cls, context):
    #    return context.mode == 'POSE'

    def execute(self, context):
        bpy.ops.object.mode_set(mode='EDIT')
        bone = context.selected_editable_bones[:][0]
        armature = bone.id_data
        side = ['arm', 'hand', 'wrist'] 
        front = ['thigh', 'shin', 'knee'] 
        names = [o.name for o in armature.edit_bones]
        arms = [b for b in names if any(a in b for a in side)]
        legs = [b for b in names if any(a in b for a in front)]
        for bone in armature.edit_bones:
            bone.select = True
            if bone.name in arms:
                bpy.ops.armature.calculate_roll(type='GLOBAL_NEG_Z', axis_flip=False, axis_only=False)
            if bone.name in legs:
                bpy.ops.armature.calculate_roll(type='GLOBAL_POS_Z', axis_flip=False, axis_only=False)
            #if fnmatch.fnmatchcase(bone.name, "something"): 
            #    armature.edit_bones.remove(bone)
         
        bpy.ops.object.mode_set(mode='POSE')   
        return {"FINISHED"}
        
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

        q = get_pose_bone_matrix(bone).to_quaternion()

        row = layout.row()
        row.label(text="Active object is: " + bone.name)
        row = layout.row()
        if bone.parent is not None:
            row.label(text="Parent object is: " + bone.parent.name)
            row = layout.row()
        x = q[3]
        y = q[1]
        z = q[2]
        row.label(text="x is %.2f" % x)
        row.label(text="y is %.2f" % y)
        row.label(text="z is %.2f" % z)
        
        row = layout.row()
        layout.operator('bone.grz', text='Revo Rig')
        
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
    bpy.utils.register_class(BONE_OT_GRZ)

def unregister():
    bpy.utils.unregister_class(Revoltech)
    bpy.utils.unregister_class(BONE_OT_GRZ)

if __name__ == "__main__":
    register()