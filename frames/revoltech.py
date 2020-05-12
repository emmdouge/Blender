import bpy
from math import pi, sqrt, degrees

bl_info = {
    "name": "Revoltech Joint",
    "author": "Emmanuel Douge",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "Pose Mode > Bone Properties",
    "description": "Move selected joint like a revoltech joint. "
                   "Locks rotation based on current rotation.",
    "warning": "",
    "category": "Rigging"}
    
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
        rot = bone.matrix.to_euler()
        #bone.rotation_euler.rotate_axis("Z", radians(90))

        row = layout.row()
        row.label(text="Active object is: " + bone.name)
        row = layout.row()
        row.label(text="bone position z is %.2f" % rot.z)
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