import bpy
from math import pi, sqrt, degrees, atan, radians
from mathutils import Matrix
from copy import deepcopy
from bpy.props import (StringProperty,
                       BoolProperty,
                       EnumProperty,
                       IntProperty,
                       FloatProperty,
                       CollectionProperty,
                       )

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
    
active_modals = set()

def callback(func):
    def modal_wrapper(self, context, event):
        cls = type(self)
        _ret, = ret = func(self, context, event)
        if _ret in {'RUNNING_MODAL', 'PASS_THROUGH'}:
            active_modals.add(cls)
        elif _ret in {'FINISHED', 'CANCELLED'}:
            active_modals.discard(cls)
        return ret
    return modal_wrapper
    
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
    zdelta = float(0.2)
    xdelta = float(0.15)
    bone = context.active_pose_bone
    q = get_pose_bone_matrix(bone).to_quaternion()
    orientation = bpy.context.scene.transform_orientation_slots[0].type
    
    if orientation == 'LOCAL':
        #print ("orientation: %s " % bone["BONE_ORIENTATION"])
        if bone["BONE_ORIENTATION"] == 'ACTIVE':
            if bone["BONE_REVO"] == 'SIDE':
                lock = (-1*zdelta) <= z <= zdelta
                bone.lock_rotation[1] = False # y
                if lock:
                    bone.lock_rotation[0] = False # x
                else:
                    bone.lock_rotation[0] = True # x
            if bone["BONE_REVO"] == 'FRONT':
                lock = float(0.7)-xdelta <= y <= float(0.7)+xdelta or (-1*float(0.7))-xdelta <= y <= (-1*float(0.7))+xdelta
                bone.lock_rotation[0] = False # y
                if lock:
                    bone.lock_rotation[2] = False # z
                else:
                    bone.lock_rotation[2] = True # z
        if bone["BONE_ORIENTATION"] == 'GLOBAL_POS_Z':
            lock = float(0.7)-xdelta <= x <= float(0.7)+xdelta or (-1*float(0.7))-xdelta <= x <= (-1*float(0.7))+xdelta
            bone.lock_rotation[0] = False # x
            if lock:
                bone.lock_rotation[1] = False # y
            else:
                bone.lock_rotation[1] = True # y
                
    space = context.space_data
    if not space.show_gizmo:
        space.show_gizmo = True
        space.show_gizmo_object_rotate = True
        space.show_gizmo_tool = True
    
class BONE_OT_REVORIG(bpy.types.Operator):
    bl_idname = "bone.revorig"
    bl_label = "Revo Rig"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.mode_set(mode='EDIT')
        bone = context.selected_editable_bones[:][0]
        bone_orientation = 'ACTIVE'
        bone_revo = 'SIDE'
        active_bonename = deepcopy(bone.name)
        armature = bone.id_data
        active_armname = deepcopy(armature.name)
        side = ['arm'] 
        front = ['thigh', 'shin', 'knee'] 
        names = [o.name for o in armature.edit_bones]
        arms = [b for b in names if any(a in b for a in side)]
        legs = [b for b in names if any(a in b for a in front)]
        for name in arms:
            bone_orientation = 'ACTIVE'
            bone_revo = 'SIDE'
            bpy.ops.object.mode_set(mode='EDIT')
            bone = context.selected_editable_bones[:][0]
            armature = bone.id_data
            bpy.ops.armature.select_all(action='DESELECT')
            bone = armature.edit_bones[active_bonename]
            print ("active: %s" % active_bonename)
            bone.select = False
            bone = armature.edit_bones[name]
            bone.select = True
            bone = armature.edit_bones[active_bonename]
            bone.select = True
            if len(context.selected_editable_bones[:]) > 1:
                print("1 %s" % context.selected_editable_bones[:][0].name)
                print("2 %s" % context.selected_editable_bones[:][1].name)
            #bpy.ops.object.mode_set(mode='POSE')
            #bpy.ops.pose.armature_apply(selected=True)
            #bpy.ops.object.mode_set(mode='EDIT')
            if name != active_bonename:
                if "lower" in name or "fore" in name:
                    bone_orientation = 'GLOBAL_POS_Z'
                    bone_revo = 'SIDE'
                    armature.edit_bones[name]["BONE_ORIENTATION"] = bone_orientation
                    armature.edit_bones[name]["BONE_REVO"] = bone_revo
                    armature.edit_bones[name]["REVO_ACTIVE"] = 'OFF'
                    bone = armature.edit_bones[active_bonename]
                    bone.select = False
                    bpy.ops.armature.calculate_roll(type='GLOBAL_POS_Z', axis_flip=False, axis_only=True)
                else:
                    bone_orientation = 'ACTIVE'
                    bone_revo = 'SIDE'
                    armature.edit_bones[name]["BONE_ORIENTATION"] = bone_orientation
                    armature.edit_bones[name]["BONE_REVO"] = bone_revo
                    armature.edit_bones[name]["REVO_ACTIVE"] = 'OFF'
                    bpy.ops.armature.calculate_roll(type='ACTIVE', axis_flip=True, axis_only=True)   
            bpy.ops.armature.select_all(action='DESELECT')
            bone = armature.edit_bones[name]
            bone.select = True
            bpy.ops.object.mode_set(mode='POSE')
            posebone = bpy.data.objects[active_armname].pose.bones[name]
            print ("pb: %s" % posebone.name)
            posebone["BONE_ORIENTATION"] = bone_orientation
            posebone["BONE_REVO"] = bone_revo
            posebone["REVO_ACTIVE"] = 'OFF'
        for name in legs:
            bone_orientation = 'ACTIVE'
            bone_revo = 'FRONT'
            bpy.ops.object.mode_set(mode='EDIT')
            bone = context.selected_editable_bones[:][0]
            armature = bone.id_data
            bpy.ops.armature.select_all(action='DESELECT')
            bone = armature.edit_bones[active_bonename]
            print ("active: %s" % active_bonename)
            bone.select = False
            bone = armature.edit_bones[name]
            bone.select = True
            bone = armature.edit_bones[active_bonename]
            bone.select = True
            if len(context.selected_editable_bones[:]) > 1:
                print("1 %s" % context.selected_editable_bones[:][0].name)
                print("2 %s" % context.selected_editable_bones[:][1].name)
            if name != active_bonename:
                    bone_orientation = 'ACTIVE'
                    bone_revo = 'FRONT'
                    armature.edit_bones[name]["BONE_ORIENTATION"] = bone_orientation
                    armature.edit_bones[name]["BONE_REVO"] = bone_revo
                    armature.edit_bones[name]["REVO_ACTIVE"] = 'OFF'
                    bpy.ops.armature.calculate_roll(type='ACTIVE', axis_flip=True, axis_only=True)   
            bpy.ops.armature.select_all(action='DESELECT')
            bone = armature.edit_bones[name]
            bone.select = True
            bpy.ops.object.mode_set(mode='POSE')
            posebone = bpy.data.objects[active_armname].pose.bones[name]
            print ("pb: %s" % posebone.name)
            posebone["BONE_ORIENTATION"] = bone_orientation
            posebone["BONE_REVO"] = bone_revo
            posebone["REVO_ACTIVE"] = 'OFF'
        
        bpy.ops.bone.revorest('INVOKE_DEFAULT')
        return {"FINISHED"}
        

    
class BONE_OT_REVOACTIVE(bpy.types.Operator):
    bl_idname = "bone.revoactive"
    bl_label = "Revo Active"
    bl_options = {'REGISTER', 'UNDO'}
    active: bpy.props.StringProperty()

    def execute(self, context):
        bpy.ops.object.mode_set(mode='EDIT')
        bone = context.selected_editable_bones[:][0]
        active_bonename = deepcopy(bone.name)
        armature = bone.id_data
        active_armname = deepcopy(armature.name)
        side = ['arm'] 
        front = ['thigh', 'shin', 'knee', 'leg'] 
        names = [o.name for o in armature.edit_bones]
        arms = [b for b in names if any(a in b for a in side)]
        legs = [b for b in names if any(a in b for a in front)]
        for name in arms:
            bpy.ops.object.mode_set(mode='EDIT')
            bone = context.selected_editable_bones[:][0]
            armature = bone.id_data
            bpy.ops.armature.select_all(action='DESELECT')
            bone = armature.edit_bones[active_bonename]
            bone.select = False
            bone = armature.edit_bones[name]
            bone.select = True
            armature.edit_bones[name]["REVO_ACTIVE"] = self.active
            bpy.ops.object.mode_set(mode='POSE')
            posebone = None
            if active_armname in bpy.data.objects:
                posebone = bpy.data.objects[active_armname].pose.bones[name]
            else:
                posebone = bpy.data.objects[active_armname.split('.')[0]].pose.bones[name]
            posebone["REVO_ACTIVE"] = self.active
        for name in legs:
            bpy.ops.object.mode_set(mode='EDIT')
            bone = context.selected_editable_bones[:][0]
            armature = bone.id_data
            bpy.ops.armature.select_all(action='DESELECT')
            bone = armature.edit_bones[active_bonename]
            bone.select = False
            bone = armature.edit_bones[name]
            bone.select = True
            armature.edit_bones[name]["REVO_ACTIVE"] = self.active
            bpy.ops.object.mode_set(mode='POSE')
            posebone = None
            if active_armname in bpy.data.objects:
                posebone = bpy.data.objects[active_armname].pose.bones[name]
            else:
                posebone = bpy.data.objects[active_armname.split('.')[0]].pose.bones[name]
            posebone["REVO_ACTIVE"] = self.active
        

        #if context.mode == 'POSE' and context.active_pose_bone is not None and "REVO_ACTIVE" in context.active_pose_bone and context.active_pose_bone["REVO_ACTIVE"] == 'ON':
        #    override = bpy.context.copy()
        #    active_armname = context.active_pose_bone.id_data.name
        #    active_bonename = context.active_pose_bone.name
        #    #print("%s" % context.area)
        #    #print("evtTy: %s" % evt.type)
        #    #print("evt: %s" % evt.value)
        #    rig = bpy.data.objects[active_armname]
        #    for obj in bpy.data.objects:
        #        if (obj.type == 'MESH' and rig in [m.object for m in obj.modifiers if m.type == 'ARMATURE']):
        #            bpy.context.view_layer.objects.active = obj
        #            m = [m for m in obj.modifiers if m.type == 'ARMATURE'][0]
        #            bpy.ops.object.modifier_copy(modifier=m.name)
        #            bpy.ops.object.modifier_apply(apply_as='DATA', modifier=m.name)
        #    bpy.ops.pose.armature_apply(override)
        #    bpy.context.view_layer.objects.active = rig
        #    bpy.ops.object.mode_set(mode='POSE')
        return {"FINISHED"}

class BONE_OT_REVOFRAMECLEAR(bpy.types.Operator):
    bl_idname = "bone.revoframeclear"
    bl_label = "Revo Frame Clear"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        rig = bpy.data.objects[context.active_pose_bone.id_data.name]
        for ob in bpy.data.objects:
            if (ob.type == 'MESH' and rig in [m.object for m in ob.modifiers if m.type == 'ARMATURE']):
                clearanim_obj(ob)
        clearanim_obj(rig)
        return {"FINISHED"}

class BONE_OT_REVOFRAMEDUPE(bpy.types.Operator):
    bl_idname = "bone.revoframedupe"
    bl_label = "Revo Frame Dupe"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
    
        bpy.ops.bone.revoframeinsert('INVOKE_DEFAULT')
        active_bonename = context.active_pose_bone.name
        active_armname = deepcopy(context.active_pose_bone.id_data.name)
        
        #print ("%s" % active_armname)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        for ob in bpy.data.objects:
            if (ob.type == 'MESH' and bpy.data.objects[active_armname] in [m.object for m in ob.modifiers if m.type == 'ARMATURE']):
                ob.select_set(True)
        bpy.data.objects[active_armname].select_set(True)
        bpy.ops.object.duplicate()
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='POSE')
        #print ("%s" % active_armname)
        bone = bpy.data.objects[active_armname].pose.bones[active_bonename].bone
        bone.select = True
        bpy.ops.bone.revoframeclear('INVOKE_DEFAULT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.select_all(action='SELECT')
        bpy.ops.object.mode_set(mode='POSE')
        DURATION = context.scene.anim_dpf
        START_FRAME = bpy.context.scene.frame_current
        bpy.context.scene.frame_set(START_FRAME+DURATION)
        return {"FINISHED"}

class BONE_OT_REVOFRAMEMESHDUPE(bpy.types.Operator):
    bl_idname = "bone.revoframemeshdupe"
    bl_label = "Revo Frame Dupe"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        active_bonename = context.active_pose_bone.name
        active_armname = deepcopy(context.active_pose_bone.id_data.name)
        
        #print ("%s" % active_armname)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        for ob in bpy.data.objects:
            if (ob.type == 'MESH' and bpy.data.objects[active_armname] in [m.object for m in ob.modifiers if m.type == 'ARMATURE']):
                ob.select_set(True)
        bpy.data.objects[active_armname].select_set(True)
        bpy.ops.object.duplicate()
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='POSE')
        #print ("%s" % active_armname)
        bone = bpy.data.objects[active_armname].pose.bones[active_bonename].bone
        bone.select = True
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.select_all(action='SELECT')
        bpy.ops.object.mode_set(mode='POSE')
        return {"FINISHED"}
    
class BONE_OT_REVOFRAMEINSERT(bpy.types.Operator):
    bl_idname = "bone.revoframeinsert"
    bl_label = "Revo Frame Insert"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        
        DURATION = context.scene.anim_dpf
        START_FRAME = bpy.context.scene.frame_current
        LOOPS = 1
        
        #sets the new interpolation type to linear
        bpy.context.preferences.edit.keyframe_new_interpolation_type = "CONSTANT"

        rig = bpy.data.objects[context.active_pose_bone.id_data.name]
        for ob in bpy.data.objects:
            if (ob.type == 'MESH' and rig in [m.object for m in ob.modifiers if m.type == 'ARMATURE']):
                animate_obj(ob, START_FRAME, DURATION, LOOPS)
        animate_obj(rig, START_FRAME, DURATION, LOOPS)
        bpy.context.view_layer.update()
        return {"FINISHED"}

def clearanim_obj(ob):
    if ob.animation_data is not None and ob.animation_data.action is not None:
        fc = ob.animation_data.action.fcurves
        for c in fc:
            if c.data_path.startswith("hide"):
                fc.remove(c)
                
def animate_obj(ob, START_FRAME, DURATION, LOOPS):
    #stores the previous interpolation default
    keyinter = bpy.context.preferences.edit.keyframe_new_interpolation_type
    
    clearanim_obj(ob)
    ob.animation_data_create()
        
    #creates a new action for the object, if needed
    actionname = "RevoAnim for %s"% ob.name
    if not actionname in bpy.data.actions:
        ob.animation_data.action = bpy.data.actions.new(actionname)
    else:
        ob.animation_data.action = bpy.data.actions[actionname]
    
    #add a new fcurve for the "hide" property 
    if not "hide_viewport" in [ x.data_path for x in ob.animation_data.action.fcurves ]:
        fcu = ob.animation_data.action.fcurves.new(data_path="hide_viewport")
    else:
        fcu = [ x for x in ob.animation_data.action.fcurves if x.data_path == 'hide_viewport' ][0]
        
    #add a new fcurve for the "hide render" property  
    if not "hide_render" in [ x.data_path for x in ob.animation_data.action.fcurves ]:
        fcu2 = ob.animation_data.action.fcurves.new(data_path="hide_render")
    else:
        fcu2 = [ x for x in ob.animation_data.action.fcurves if x.data_path == 'hide_render' ][0]
    
    #add 2 points, one for hide, one for hide render
    fcu.keyframe_points.add(1)
    fcu2.keyframe_points.add(1)
    fcu.keyframe_points.add(2 * LOOPS)
    fcu2.keyframe_points.add(2 * LOOPS)

    hide = 1
    show = 0
    
    fcu.keyframe_points[0].interpolation = "CONSTANT"
    fcu2.keyframe_points[0].interpolation = "CONSTANT"   
    fcu.keyframe_points[0].co = 0, hide
    fcu2.keyframe_points[0].co = 0, hide

    pointX = 1
    loopcount = 0
    while pointX < (2*LOOPS):
        #set interpolation to constant
        fcu.keyframe_points[pointX].interpolation = "CONSTANT"
        fcu.keyframe_points[pointX+1].interpolation = "CONSTANT"
        fcu2.keyframe_points[pointX].interpolation = "CONSTANT"
        fcu2.keyframe_points[pointX+1].interpolation = "CONSTANT"       

        #sets the first point: hide
        fcu.keyframe_points[pointX].co = START_FRAME * (loopcount+1), show
        fcu2.keyframe_points[pointX].co = START_FRAME * (loopcount+1), show

        #how long to show frame
        fcu.keyframe_points[pointX+1].co = fcu.keyframe_points[pointX].co.x + DURATION, hide
        fcu2.keyframe_points[pointX+1].co = fcu2.keyframe_points[pointX].co.x + DURATION, hide

        pointX += 2
        loopcount += 1

    #recovers the previous interpolation setting
    bpy.context.preferences.edit.keyframe_new_interpolation_type = keyinter
    
class Revoltech(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Display Data"
    bl_idname = "BONE_PT_hello"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    #bl_context = "bone"
    bpy.types.Scene.anim_dpf = IntProperty(name="DPF", min=1, soft_min=1, default=6, description="In an animation each frame will be shown this number of frames.")
    
    @classmethod
    def poll(cls, context):
        return context.active_pose_bone is not None
        
    def execute(self, context):
        bpy.ops.bone.revorest('INVOKE_DEFAULT')

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
        current_tool = bpy.context.workspace.tools.from_space_view3d_mode("POSE", create=False).idname
        row.label(text="ct is %s" % current_tool)
        
        row = layout.row()
        layout.operator('bone.revorig', text='Revo Rig')
        row = layout.row()
        layout.operator('bone.revoactive', text='Revo Active').active = 'ON'
        row = layout.row()
        layout.operator('bone.revoactive', text='Revo OFF').active = 'OFF'
        row = layout.row()
        layout.operator('bone.revoframemeshdupe', text='Dupe Armature')
        
        box = layout.box()
        box.prop(context.scene, "anim_dpf")
        
        row = layout.row()
        layout.operator('bone.revoframedupe', text='Revo Frame')
        row = layout.row()
        layout.operator('bone.revoframeinsert', text='Insert Frame')
        row = layout.row()
        layout.operator('bone.revoframeclear', text='Clear Frame')
        
        if "BONE_REVO" in context.active_pose_bone.keys():
            lock(self, context, x, y, z)
        
        bpy.context.area.tag_redraw()
        
def gen_C_dict(context, win, area_type='VIEW_3D'):

    C_dict = context.copy()

    for area in win.screen.areas:
        if area.type == area_type:
            for region in area.regions:
                if region.type == 'WINDOW':
                    break
            for space in area.spaces:
                if space.type == area_type:
                    region_data = None
                    if area_type == 'VIEW_3D':
                        region_data = space.region_3d
                    break
            break
    
    C_dict.update(
        area=area,
        region=region,
        region_data=region_data,
        screen=win.screen,
        space_data=space)

    return C_dict
    
class BONE_OT_APPLYREST(bpy.types.Operator):
    bl_idname = "bone.revorest"
    bl_label = "Revo Apply as Rest Pose"
        
    def modal(self, context, evt):
        print("running")
        if context.mode == 'POSE' and context.active_pose_bone is not None and context.active_pose_bone["REVO_ACTIVE"] == 'ON':
            override = bpy.context.copy()
            active_armname = context.active_pose_bone.id_data.name
            active_bonename = context.active_pose_bone.name
            #print("%s" % context.area)
            #print("evtTy: %s" % evt.type)
            #print("evt: %s" % evt.value)
            if evt.type == 'INBETWEEN_MOUSEMOVE':
                if evt.value == 'RELEASE':
                    rig = bpy.data.objects[active_armname]
                    for obj in bpy.data.objects:
                        if (obj.type == 'MESH' and rig in [m.object for m in obj.modifiers if m.type == 'ARMATURE']):
                            bpy.context.view_layer.objects.active = obj
                            m = [m for m in obj.modifiers if m.type == 'ARMATURE'][0]
                            bpy.ops.object.modifier_copy(modifier=m.name)
                            bpy.ops.object.modifier_apply(apply_as='DATA', modifier=m.name)
                    #print("armature applied!!!")
                    bpy.ops.pose.armature_apply(override)
                    bpy.context.view_layer.objects.active = rig
                    bpy.ops.object.mode_set(mode='POSE')
                    #bpy.context.view_layer.update()
        return {'PASS_THROUGH'}
        
    def invoke(self, context, event):
        print("invoke")
        running = False
        for cls in bpy.types.Operator.__subclasses__():
            if hasattr(cls, "modal") and getattr(cls, "bl_idname") == "bone.revorest":
                print("revo running")
                running = True
        if running == False:
            context.window_manager.modal_handler_add(self)
        else:
            return {'FINISHED'}
        return {'RUNNING_MODAL'}

    def execute(self, context):
        print("execute")
        running = False
        for cls in bpy.types.Operator.__subclasses__():
            if hasattr(cls, "modal") and getattr(cls, "bl_idname") == "bone.revorest":
                print("revo running")
                running = True
        if running == False:
            context.window_manager.modal_handler_add(self)
        else:
            return {'FINISHED'}
        return {'RUNNING_MODAL'}
        
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
    bpy.utils.register_class(BONE_OT_REVOFRAMEINSERT)
    bpy.utils.register_class(BONE_OT_REVOFRAMECLEAR)
    bpy.utils.register_class(BONE_OT_REVOFRAMEDUPE)
    #bpy.utils.register_class(BONE_OT_REVORIG)
    bpy.utils.register_class(BONE_OT_REVOFRAMEMESHDUPE)
    bpy.utils.register_class(BONE_OT_REVOACTIVE)
    bpy.utils.register_class(BONE_OT_APPLYREST)

def unregister():
    bpy.utils.unregister_class(Revoltech)
    bpy.utils.unregister_class(BONE_OT_REVOFRAMEINSERT)
    bpy.utils.unregister_class(BONE_OT_REVOFRAMEDUPE)
    bpy.utils.unregister_class(BONE_OT_REVOFRAMEMESHDUPE)
    #bpy.utils.unregister_class(BONE_OT_REVORIG)
    bpy.utils.unregister_class(BONE_OT_REVOFRAMECLEAR)
    bpy.utils.unregister_class(BONE_OT_REVOACTIVE)
    bpy.utils.unregister_class(BONE_OT_APPLYREST)

if __name__ == "__main__":
    register()
    