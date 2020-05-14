import bpy
from math import pi, sqrt, degrees
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
   
class Revoltech(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Display Data"
    bl_idname = "BONE_PT_hello"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "bone"

    @classmethod
    def poll(cls, context):
        return context.active_pose_bone is not None

    def draw(self, context):
        layout = self.layout

        bone = context.active_pose_bone
        armature = bone.id_data
        
        #debone = Matrix([[1,0,0,0],[0,0,-1,0], [0,1,0,0],[0,0,0,1]]) #because bones are wacky
        #m = armature.matrix_world @ bone.matrix @ debone

        q = get_pose_bone_matrix(bone).to_quaternion()

        row = layout.row()
        row.label(text="Active object is: " + bone.name)
        row = layout.row()
        row.label(text="Parent object is: " + bone.parent.name)
        row = layout.row()
        row.label(text="x is %.2f" % q[3])
        row.label(text="y is %.2f" % q[1])
        row.label(text="z is %.2f" % q[2])
        #row = layout.row()
        #row.label(text="xd is %.2f" % (abs(prot.x-rot.x)))
        #row.label(text="yd is %.2f" % (abs(prot.y-rot.y)))
        #row.label(text="zd is %.2f" % (abs(prot.z-rot.z)))
        #row = layout.row()
        print ("bone position z is %.2f" % rot.z)

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