import bpy

bl_info = {
    "name": "Revoltech Joint",
    "author": "Vicente Carro, Florian Meyer (tstscr), mont29, matali",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "File > Import > Images as Anim Planes or Add > Mesh > Image sequence as planes",
    "description": "Move selected joint like a revoltech joint. "
                   "Locks rotation based on current rotation.",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Add_Mesh/Planes_from_Images",
    "tracker_url": "https://projects.blender.org/tracker/index.php?func=detail&aid=21751",
    "category": "Import-Export"}
    
class Revoltech(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Display Data"
    bl_idname = "OBJECT_PT_hello"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout

        obj = context.object
        pos = obj.matrix_world.to_translation()

        row = layout.row()
        row.label(text="Active object is: " + obj.name)
        row = layout.row()
        row.label(text="object position z is %.2f" % pos.z)
        printf("object position z is %.2f" % pos.z)

def prop_redraw(scene):
    for area in bpy.context.screen.areas:
        if area.type == 'PROPERTIES':
            if area.spaces.active.context == 'OBJECT':
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