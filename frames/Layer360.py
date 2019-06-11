bl_info = {
    "name": "Layer 360",
    "description": "Create spheres that act like a 360° layer for drawing and painting.",
    "author": "ZeGuy, Rimrook",
    "version": (1, 3, 0),
    "blender": (2, 78, 0),
    "location": "World > Layer 360",
    "warning": "", # used for warning icon and text in addons panel
    "support": "COMMUNITY",
    "category": "Add Mesh"
}

import bpy
import os
from math import *
from mathutils import Euler
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.types import Panel, PropertyGroup, Operator, Menu
from bpy.props import StringProperty,IntProperty,BoolProperty,PointerProperty,FloatProperty, FloatVectorProperty

#==== Handlers ====

def pre_renderAngle(scene):
    coords = [[90,0,0,"front"],[90,0,-90,"right"],[90,0,-180,"back"],[90,0,-270,"left"],[180,0,0,"top"],[0,0,0,"bottom"]]
    frame = scene.layer360.frameNbr
    print("Rendering " + coords[frame][3] + " view")
    scene.camera.rotation_euler = Euler((radians(coords[frame][0]),radians(coords[frame][1]),radians(coords[frame][2])+scene.layer360.save_camera_rotation_z), "XYZ")
    return

def post_renderAngle(scene):
    names = ["front","right","back","left","top","bottom"]
    bpy.data.images['Render Result'].save_render(scene.layer360.directory + names[scene.layer360.frameNbr] + ".png")

#==== Functions ====

def changedGrid(self, ctx):
    #Delete the current one
    for obj in bpy.context.scene.objects :
            if obj.layer360.type == "grid" :
                bpy.data.objects.remove(obj,True)
                break
    
    #Create a new one if necessary
    if self.useXGrid or self.useYGrid or self.useZGrid : 
        gridMesh = bpy.data.meshes.new("gridMesh")
        gridObj = bpy.data.objects.new("gridMesh", gridMesh)
        gridObj.layer360.type = "grid"
        gridObj.show_x_ray = True
        gridObj.hide_select = True
        gridObj.draw_type = "WIRE"
        
        try :
            bpy.data.groups["justForColor"].objects.link(gridObj)
        except :
            bpy.data.groups.new("justForColor")
            bpy.data.groups["justForColor"].objects.link(gridObj)
        
        bpy.context.scene.objects.link(gridObj)
        
        #Generate grid using parameters
        verts = []
        edges = []
        faces = []
        start = 0
        length = 500
        
        if self.useXGrid :
            for x in range(self.xGrid_x) :
                xPos = x / (self.xGrid_x-1) * 10 - 5
                verts.append((-length,xPos,5))
                verts.append((length,xPos,5))
                faces.append((start,start+1))
                verts.append((-length,xPos,-5))
                verts.append((length,xPos,-5))
                faces.append((start+2,start+3))
                start += 4
                
            for y in range(self.xGrid_y) :
                yPos = y / (self.xGrid_y-1) * 10 - 5
                verts.append((-length,-5,yPos))
                verts.append((length,-5,yPos))
                faces.append((start,start+1))
                verts.append((-length,5,yPos))
                verts.append((length,5,yPos))
                faces.append((start+2,start+3))
                start += 4
                
        if self.useYGrid :
            for x in range(self.yGrid_x) :
                xPos = x / (self.yGrid_x-1) * 10 - 5
                verts.append((xPos,-length,5))
                verts.append((xPos,length,5))
                faces.append((start,start+1))
                verts.append((xPos,-length,-5))
                verts.append((xPos,length,-5))
                faces.append((start+2,start+3))
                start += 4
                
            for y in range(self.yGrid_y) :
                yPos = y / (self.yGrid_y-1) * 10 - 5
                verts.append((-5,-length,yPos))
                verts.append((-5,length,yPos))
                faces.append((start,start+1))
                verts.append((5,-length,yPos))
                verts.append((5,length,yPos))
                faces.append((start+2,start+3))
                start += 4
                
        if self.useZGrid :
            for x in range(self.zGrid_x) :
                xPos = x / (self.zGrid_x-1) * 10 - 5
                verts.append((-5,xPos,-length))
                verts.append((-5,xPos,length))
                faces.append((start,start+1))
                verts.append((5,xPos,-length))
                verts.append((5,xPos,length))
                faces.append((start+2,start+3))
                start += 4
                
            for y in range(self.zGrid_y) :
                yPos = y / (self.zGrid_y-1) * 10 - 5
                verts.append((yPos,-5,-length))
                verts.append((yPos,-5,length))
                faces.append((start,start+1))
                verts.append((yPos,5,-length))
                verts.append((yPos,5,length))
                faces.append((start+2,start+3))
                start += 4
            
        gridMesh.from_pydata(verts,edges,faces)

def changeSize(self, ctx) :
    scl = self.layerScale
    self.scale = [scl,scl,scl]
    
def generateSphereWithUV(context,filepath="") :
    #Create Sphere
    layerMesh = bpy.data.meshes.new("mesh")
    layerObj = bpy.data.objects.new("layer", layerMesh)
    layerObj.scale = [5.0,5.0,5.0]
    layerObj.lock_location = [True,True,True] if context.scene.layer360.lock_location else [False, False, False]
    layerObj.lock_rotation = [True,True,True] if context.scene.layer360.lock_rotation else [False, False, False]
    layerObj.lock_scale = [True,True,True]
    layerObj.layer360.type = "layer"
    layerObj.data.uv_textures.new("UVMap")
    context.screen.scene = context.screen.scene     #Refresh the UI
    
    for obj in context.scene.objects :
        obj.select = False
    context.scene.objects.link(layerObj)
    context.scene.objects.active = layerObj
    layerObj.select = True
                
    verts = []
    edges = []
    faces = []
    
    nbrSegments = context.scene.layer360.nbrSegments
    nbrRings = context.scene.layer360.nbrRings
    for r in range(nbrRings + 1) :
        for s in range(nbrSegments + 1) :
            x = sin(radians((r/nbrRings)*180)) * cos(radians((s/nbrSegments)*360))
            y = sin(radians((r/nbrRings)*180)) * sin(radians((s/nbrSegments)*360))
            z = cos(radians((r/nbrRings)*180))
            verts.append((x,y,z))
            

            if r < nbrRings :
                if s < (nbrSegments - 1) :
                    faces.append((r*(nbrSegments+1)+s,r*(nbrSegments+1)+s+1,r*(nbrSegments+1)+(nbrSegments+1)+s+1,r*(nbrSegments+1)+(nbrSegments+1)+s))
                if s == (nbrSegments - 1) :
                    faces.append((r*(nbrSegments+1)+s,r*(nbrSegments+1),r*(nbrSegments+1)+(nbrSegments+1),r*(nbrSegments+1)+(nbrSegments+1)+s))
            
    layerMesh.from_pydata(verts,edges,faces)
    
    #UV coordinates
    for r in range(nbrRings) :
        for s in range(nbrSegments) :
            active = layerObj.data.uv_layers.active
            active.data[r*(nbrSegments*4)+s*4].uv = [1-(s/(nbrSegments*1.0)),1-(r/(nbrRings*1.0))]
            active.data[r*(nbrSegments*4)+s*4+1].uv = [1-((s+1)/(nbrSegments*1.0)),1-(r/(nbrRings*1.0))]
            active.data[r*(nbrSegments*4)+s*4+2].uv = [1-((s+1)/(nbrSegments*1.0)),1-((r+1)/(nbrRings*1.0))]
            active.data[r*(nbrSegments*4)+s*4+3].uv = [1-(s/(nbrSegments*1.0)),1-((r+1)/(nbrRings*1.0))]
            
    #Material
    bgMap = bpy.data.materials.new("BGMap")
    layerObj.data.materials.append(bgMap)
    
    #Blender render
    bgMap.use_shadeless = True
    bgMap.use_transparency = True
    bgMap.alpha = 0.0
    bgMap.texture_slots.add()
    bgMap.texture_slots[0].use_map_alpha = True
    bgMap.texture_slots[0].texture = bpy.data.textures.new("layerTex","IMAGE")
    
    l360 = context.scene.layer360
    if filepath == "" :
        img = bgMap.texture_slots[0].texture.image = bpy.data.images.new("layerImg",l360.width,l360.height)
    else :
        img = bgMap.texture_slots[0].texture.image = bpy.data.images.load(filepath,True)
    bgMap.texture_slots[0].texture.image.generated_color = (l360.color[0],l360.color[1],l360.color[2],l360.alpha/100.0)
    
    #Cycles
    bgMap.use_nodes = True
    bgMap.node_tree.nodes.clear()
    node_output = bgMap.node_tree.nodes.new("ShaderNodeOutputMaterial")
    node_mix = bgMap.node_tree.nodes.new("ShaderNodeMixShader")
    node_mix.location = [-200,0]
    node_transparent = bgMap.node_tree.nodes.new("ShaderNodeBsdfTransparent")
    node_transparent.location = [-400,-100]
    node_emission = bgMap.node_tree.nodes.new("ShaderNodeEmission")
    node_emission.location = [-400,-200]
    node_image = bgMap.node_tree.nodes.new("ShaderNodeTexImage")
    node_image.location = [-600,0]
    node_image.image = img
    bgMap.use_nodes = False if context.scene.render.engine == "BLENDER_RENDER" else True
    
    links = bgMap.node_tree.links
    links.new(node_output.inputs[0], node_mix.outputs[0])
    links.new(node_mix.inputs[0], node_image.outputs[1])
    links.new(node_mix.inputs[1], node_transparent.outputs[0])
    links.new(node_mix.inputs[2], node_emission.outputs[0])
    links.new(node_emission.inputs[0], node_image.outputs[0])
    
    return 

#==== Properties ====

class WorldButtonsPanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "world"
    
class GR_Layer360_Object(PropertyGroup) :
    type = bpy.props.StringProperty()
    #scale = FloatProperty(default = 5.0, min=0.0,update=changeSize)
    
class GR_Layer360_World(PropertyGroup) :
    width = IntProperty(default = 4000)  
    height = IntProperty(default = 2000)
    color = FloatVectorProperty(subtype="COLOR_GAMMA", default=(1.0,1.0,1.0), min=0.0, max=1.0)
    alpha = FloatProperty(default = 0.0, min=0.0, max=100.0, subtype="PERCENTAGE")
    lock_location = BoolProperty(default = True)
    lock_rotation = BoolProperty(default = True)
    nbrRings = IntProperty(default = 32, min = 4, max= 128)
    nbrSegments = IntProperty(default = 64, min = 4, max=128)
    
    save_samples = IntProperty()
    save_resolution_x = IntProperty()
    save_resolution_y = IntProperty()
    save_resolution_percentage = IntProperty()
    save_camera_angle = FloatProperty()
    save_camera_rotation_x = FloatProperty()
    save_camera_rotation_y = FloatProperty()
    save_camera_rotation_z = FloatProperty()
    directory = StringProperty()
    frameNbr = IntProperty()
    
    #use_grid = BoolProperty(default=False, update=changedGrid)
    
    gridSettings = BoolProperty(default=False)
    useXGrid = BoolProperty(default=False, update=changedGrid)
    useYGrid = BoolProperty(default=False, update=changedGrid)
    useZGrid = BoolProperty(default=False, update=changedGrid)
    xGrid_x = IntProperty(default=11, min=3, max=64, update=changedGrid)
    xGrid_y = IntProperty(default=11, min=3, max=64, update=changedGrid)
    yGrid_x = IntProperty(default=11, min=3, max=64, update=changedGrid)
    yGrid_y = IntProperty(default=11, min=3, max=64, update=changedGrid)
    zGrid_x = IntProperty(default=11, min=3, max=64, update=changedGrid)
    zGrid_y = IntProperty(default=11, min=3, max=64, update=changedGrid)
    
#==== UI ====

class WORLD_PT_layer360(WorldButtonsPanel, Panel):
    bl_label = "Layer 360"
    COMPAT_ENGINES = {'BLENDER_RENDER'}

    def draw(self, context):
        layout = self.layout
        
        col = layout.column(align=True)
        box = col.box()
        for obj in sorted(context.scene.objects,key=lambda s:s.scale.x):
            if obj.layer360.type == "layer" :
                row = box.row(align=True)
                iconName = "RADIOBUT_ON" if obj.select else "RADIOBUT_OFF"
                row.operator("layer360.select",text="",icon=iconName, emboss=False).name = obj.name
                row.prop(obj,"hide",text="")
                iconName = "WIRE" if obj.show_wire else "SOLID"
                row.prop(obj,"show_wire",text="",icon=iconName)
                row.prop(obj,"name",text="")
                row.prop(obj,"layerScale",index=0,text="")
                
        col.separator()
        col.operator("layer360.new_layer",text="New layer360",icon="ZOOMIN")
        col.operator("layer360.import_image",text="Import Image",icon="IMAGE_DATA")
        
        col.separator()
        #col.prop(context.scene.layer360,"use_grid", text="Use grid", icon="OUTLINER_OB_LATTICE")
        
        icon = "TRIA_RIGHT" if not context.scene.layer360.gridSettings else "TRIA_DOWN"
        col.prop(context.scene.layer360,"gridSettings", text="Show grid settings", icon=icon)
        
        if context.scene.layer360.gridSettings :
            box = col.box()
            col = box.column()
            
            row = col.row(align=True)
            row.prop(context.scene.layer360,"useXGrid", text="X Grid")
            if context.scene.layer360.useXGrid :
                row.prop(context.scene.layer360,"xGrid_x", text="X")
                row.prop(context.scene.layer360,"xGrid_y", text="Y")
            
            row = col.row(align=True)
            row.prop(context.scene.layer360,"useYGrid", text="Y Grid")
            if context.scene.layer360.useYGrid :
                row.prop(context.scene.layer360,"yGrid_x", text="X")
                row.prop(context.scene.layer360,"yGrid_y", text="Y")
            
            row = col.row(align=True)
            row.prop(context.scene.layer360,"useZGrid", text="Z Grid")
            if context.scene.layer360.useZGrid :
                row.prop(context.scene.layer360,"zGrid_x", text="X")
                row.prop(context.scene.layer360,"zGrid_y", text="Y")
                
        col.separator()
        col.operator("layer360.generate_equirectangular_render",text="Generate Equirectangular", icon="GROUP")
        if not context.scene.render.use_freestyle :
            col.label("Pointless if Freestyle is not active", icon="ERROR")
        
# ==== Operators ====

class Layer360_newLayer(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "layer360.new_layer"
    bl_label = "Layer360 : New layer"

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=300)
    
    def draw(self, context):
        layout = self.layout
        
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(context.scene.layer360,"color",text="")
        row.prop(context.scene.layer360,"alpha")
        col.separator()
        row = col.row(align=True)
        row.prop(context.scene.layer360,"width")
        row.prop(context.scene.layer360,"height")
        col.separator()
        row = col.row()
        row.prop(context.scene.layer360,"lock_location", text="Lock Location")
        row.prop(context.scene.layer360,"lock_rotation", text="Lock Rotation")
        col.separator()
        row = col.row(align=True)
        row.prop(context.scene.layer360,"nbrSegments", text="Segments")
        row.prop(context.scene.layer360,"nbrRings", text="Rings")
        
    def execute(self,context) :
        generateSphereWithUV(context)
        return {"FINISHED"}
    
class Layer360_select(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "layer360.select"
    bl_label = "Layer360 : Select"
    
    name = StringProperty()

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        #Deselect every layer360 in oreder to have only one selection
        for obj in context.scene.objects :
            if obj.layer360.type == "layer" :
                if self.name == obj.name :
                    obj.select = True
                    context.scene.objects.active = obj
                else :
                    obj.select = False 
        return {'FINISHED'}
    
class Layer360_importImage(Operator, ImportHelper):
    bl_idname = "layer360.import_image"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Layer 360: Import Image"

    # ImportHelper mixin class uses this
    filename_ext = ""

    filter_glob = StringProperty(
            default="*",
            options={'HIDDEN'},
            maxlen=255,  # Max internal buffer length, longer would be clamped.
            )

    def execute(self, context):
        generateSphereWithUV(context,self.filepath)
        return {'FINISHED'}
        #return read_some_data(context, self.filepath, self.use_setting)
        
class Layer360_generateEquirectangularRender(Operator, ImportHelper):
    bl_idname = "layer360.generate_equirectangular_render"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Layer 360: Generate equirectangular render"
    
    # ExportHelper mixin class uses this
    filename_ext = ".txt"

    filter_glob = StringProperty(
            default="*.png",
            options={'HIDDEN'},
            maxlen=255,  # Max internal buffer length, longer would be clamped.
            )
        
    #UI part
    cubemapLength = IntProperty(name = "Cubemap texture size (px)", default=2000)
    forceLowSample = BoolProperty(name = "Force Cycles samples to 1", default=True)
    switchToScene = BoolProperty(name = "Switch to generated scene", default=True)
    
    def execute(self, context):
        hand = bpy.app.handlers.render_pre.append(pre_renderAngle)
        hand = bpy.app.handlers.render_post.append(post_renderAngle)
        layer360 = context.scene.layer360
        
        #temp save
        layer360.save_samples = context.scene.cycles.samples
        layer360.save_resolution_x = context.scene.render.resolution_x
        layer360.save_resolution_y = context.scene.render.resolution_y
        layer360.save_resolution_percentage = context.scene.render.resolution_percentage
        layer360.save_camera_angle = context.scene.camera.data.angle
        layer360.directory = os.path.dirname(self.filepath) + "/"
        layer360.save_camera_rotation_x = context.scene.camera.rotation_euler.x
        layer360.save_camera_rotation_y = context.scene.camera.rotation_euler.y
        layer360.save_camera_rotation_z = context.scene.camera.rotation_euler.z
        
        if self.forceLowSample :
            context.scene.cycles.samples = 1
        
        #Set up the camera for cubemap rendering
        size = self.cubemapLength
        context.scene.camera.data.angle = radians(90)
        context.scene.render.resolution_x = size
        context.scene.render.resolution_y = size
        context.scene.render.resolution_percentage = 100
        
        #Render each angle
        for i in range(6) :
            layer360.frameNbr = i
            bpy.ops.render.render()
        
        #temp reload
        context.scene.cycles.samples = layer360.save_samples
        context.scene.camera.data.angle = layer360.save_camera_angle
        context.scene.render.resolution_x = layer360.save_resolution_x
        context.scene.render.resolution_y = layer360.save_resolution_y
        context.scene.render.resolution_percentage = layer360.save_resolution_percentage
        context.scene.camera.rotation_euler.x = layer360.save_camera_rotation_x
        context.scene.camera.rotation_euler.y = layer360.save_camera_rotation_y
        context.scene.camera.rotation_euler.z = layer360.save_camera_rotation_z
        
        bpy.app.handlers.render_pre.remove(pre_renderAngle)
        bpy.app.handlers.render_post.remove(post_renderAngle)
        
        #Generate scene for Final equirectangular rendering
        #(It's up to the user to check the cubemap and start rendering)
        sceneSphereMap = bpy.data.scenes.new("layer360 - SphereMap")
        sceneSphereMap.render.engine = "CYCLES"
        sceneSphereMap.render.resolution_x = layer360.width
        sceneSphereMap.render.resolution_y = layer360.height
        sceneSphereMap.render.resolution_percentage = 100
        #Lower samples for a faster rendering
        sceneSphereMap.cycles.samples = 1
        sceneSphereMap.cycles.preview_samples = 1
        sceneSphereMap.cycles.min_bounces = 0
        sceneSphereMap.cycles.max_bounces = 0
        sceneSphereMap.cycles.transparent_min_bounces = 0
        sceneSphereMap.cycles.transparent_max_bounces = 0
        sceneSphereMap.cycles.diffuse_bounces = 0
        sceneSphereMap.cycles.glossy_bounces = 0
        sceneSphereMap.cycles.transmission_bounces = 0
        sceneSphereMap.cycles.volume_bounces = 0
        sceneSphereMap.cycles.use_transparent_shadows = False
        sceneSphereMap.cycles.caustics_reflective = False
        sceneSphereMap.cycles.caustics_refractive = False
        
        #Create a camera
        cam = bpy.data.cameras.new("l360-Camera")
        camObj = bpy.data.objects.new("l360-Camera",cam)
        camObj.rotation_euler = Euler((radians(90),0,0),"XYZ")
        camObj.data.type = "PANO"
        camObj.data.cycles.panorama_type = "EQUIRECTANGULAR"
        sceneSphereMap.objects.link(camObj)
        sceneSphereMap.update()
        
        
        #Create the cube
        for ind,i in enumerate(["front","right","back","left","top","bottom"]) :
            #Create a plane
            mesh = bpy.data.meshes.new("mesh-" + i)
            obj = bpy.data.objects.new(i,mesh)
            verts = [[-5,5,-5],[5,5,-5],[5,5,5],[-5,5,5]]
            edges = []
            faces = [[0,1,2,3]]
            mesh.from_pydata(verts,edges,faces)
            
            coords = [[0,0,0,"front"],[0,0,-90,"right"],[0,0,-180,"back"],[0,0,-270,"left"],[90,0,0,"top"],[270,0,0,"bottom"]]
            obj.rotation_euler = Euler((radians(coords[ind][0]),radians(coords[ind][1]),radians(coords[ind][2])),"XYZ")
            
            #UVmap
            obj.data.uv_textures.new("UVMap")
            active = obj.data.uv_layers.active 
            active.data[0].uv = [0,0] 
            active.data[1].uv = [1,0] 
            active.data[2].uv = [1,1] 
            active.data[3].uv = [0,1]
            
            #Material (No need to do something for Blender render this time)
            mat = bpy.data.materials.new("Mat-" + i)
            obj.data.materials.append(mat)
            mat.use_nodes = True
            mat.node_tree.nodes.clear()
            node_output = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
            node_mix = mat.node_tree.nodes.new("ShaderNodeMixShader")
            node_mix.location = [-200,0]
            node_transparent = mat.node_tree.nodes.new("ShaderNodeBsdfTransparent")
            node_transparent.location = [-400,-100]
            node_emission = mat.node_tree.nodes.new("ShaderNodeEmission")
            node_emission.location = [-400,-200]
            node_image = mat.node_tree.nodes.new("ShaderNodeTexImage")
            node_image.location = [-600,0]
            node_image.image = bpy.data.images.load(layer360.directory + i + ".png", True)
            
            links = mat.node_tree.links 
            links.new(node_output.inputs[0], node_mix.outputs[0])
            links.new(node_mix.inputs[0], node_image.outputs[1])
            links.new(node_mix.inputs[1], node_transparent.outputs[0])
            links.new(node_mix.inputs[2], node_emission.outputs[0])
            links.new(node_emission.inputs[0], node_image.outputs[0])
            
            #Link to the scene
            sceneSphereMap.objects.link(obj)
        
        #Go to the new scene
        if self.switchToScene :
            context.screen.scene = sceneSphereMap
        
        #It's up to the user to render it now
        #Doing it that way, he can check the cubemap before doing a long rendering process
        
        return {"FINISHED"}

def register():
    bpy.utils.register_class(WORLD_PT_layer360)
    bpy.utils.register_class(GR_Layer360_World)
    bpy.utils.register_class(GR_Layer360_Object)
    
    bpy.utils.register_class(Layer360_newLayer)
    bpy.utils.register_class(Layer360_select)
    bpy.utils.register_class(Layer360_importImage)
    bpy.utils.register_class(Layer360_generateEquirectangularRender)
    
    bpy.types.Scene.layer360 = PointerProperty(type = GR_Layer360_World)
    bpy.types.Object.layer360 = PointerProperty(type = GR_Layer360_Object)
    bpy.types.Object.layerScale = FloatProperty(default = 5.0, min=0.0,update=changeSize)

def unregister():
    bpy.utils.unregister_class(WORLD_PT_layer360)
    bpy.utils.unregister_class(GR_Layer360_World)
    bpy.utils.unregister_class(GR_Layer360_Object)
    
    bpy.utils.unregister_class(Layer360_newLayer)
    bpy.utils.unregister_class(Layer360_select)
    bpy.utils.unregister_class(Layer360_importImage)
    bpy.utils.unregister_class(Layer360_generateEquirectangularRender)


if __name__ == "__main__":
    register()
