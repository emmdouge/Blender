bl_info = {
    "name": "Real-time ToyRig",
    "author": "Frank Li",
    "version": (1, 1, 0),
    "blender": (2, 79, 0),
    "location": "View3D > Pose mode > Tool Shelf > ToyRig",
    "description": "Pose the Model like play the Toy in Real-time !!!",
    "warning": "",
    "wiki_url": "https://github.com/Frank-Li-Code/Real-time_ToyRig",
    "tracker_url": "https://github.com/Frank-Li-Code/Real-time_ToyRig/issues",
    "category": "Rigging",
    }

import bpy
from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import *
import time
import traceback

# --------------------------------------------------------------------------------------------------
#  Properties will store in the active object's custom properties make it can save in blender file
# --------------------------------------------------------------------------------------------------

# Select with right mouse or left mouse
select_with = "RIGHTMOUSE"
# if the armature is be set to ToyRig: { armature name:{"deform_bones_name": {},"deform_bones_add_name": {},"original_show_bones_name": {},"control_bones_name": {},"pole_bones_name": {},"fixed_ik_bones_name": {},"fixed_fk_bones_name": {},"fk_bones_name": {},"fk_show_bone_name": {},"exist_ik_info": {},"ik_follow": {},"exist_fkc_info": {},"ik_show_bone_name": {},"rfk_bone_name": {},"fix_show_bone_name": {},"last_bone_name": "","is_use": True,"is_fk": True,"is_rfk": False,"is_lock": False,"is_fixed": False,"selected_bones_name": {}} }
used_armature = {}
# deform bone's name
deform_bones_name = {}
# deform bone's name add end bone's name
deform_bones_add_name = {}
# original bone's name that can be show
original_show_bones_name = {}
# fk&&ik control bone's name
control_bones_name = {}
# pole bone's name
pole_bones_name = {}
# fixed IK bone's name
fixed_ik_bones_name = {}
# fixed FK bone's name
fixed_fk_bones_name = {}
# name of the bone that is fk control
fk_bones_name = {}
# name of the fk control bone that can be select
fk_show_bone_name = {}
# contain the exist IK chain's info, exist IK info:{control bone name + "control bone's ik type: _end/_begin": ("opposite control bone name",IK chain count)}
exist_ik_info = {}
# relevant deform bone follow the IK controller that in this list
ik_follow = {}
# contain the exist FK chain's info, exist FK chain info:{control bone name + "control bone's fkc type: _end/_begin": ("opposite control bone name",FK chain count)}
exist_fkc_info = {}
# name of the ik control bone(with pole bone) that can be select
ik_show_bone_name = {}
# name of ik control bone that use reverse FK
rfk_bone_name = {}
# name of the fk control bone that can be select in fix mode
fix_show_bone_name = {}
# the last control bone's name be select
last_bone_name = ""
# store keymaps here to access after registration
addon_keymaps = []
# the constraint's name that been use by this tool
constraints_name = {"Copy_Transforms": "ToyRig_Copy_Transforms","IK": "ToyRig_IK","Stretch_To": "ToyRig_Stretch_To"}
# setting of control bone's color and poselib's name
toy_settings = {'FK_color': 'THEME04','IK_color': 'THEME11',"Fix_color": 'THEME13'}
# custom settings: { armature name:{"custom_bones_name": {},"vanish_bones_name": {}} }
custom_settings = {}
# name of the bone that is custom control bone
custom_bones_name = {}
# bone's controller that never can be select once enable the tool
vanish_bones_name = {}
# store the modal's condition, on or not
modal_on = False

#Creates a Panel in the pose mode Tool Shelf
class TOY_PT_panel(bpy.types.Panel):
    bl_label = "ToyRig"
    bl_idname = "toy.panel"
    bl_context = "posemode"
    bl_category = "ToyRig"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    def draw(self, context):
        global select_with
        armature_name = context.object.name
        The_armature = context.object
        if "ToyRig_"+armature_name in The_armature:
            used_armature = The_armature["ToyRig_"+armature_name]
            is_use = used_armature["is_use"]
            is_lock = used_armature["is_lock"]
            is_fixed = used_armature["is_fixed"]
            is_fk = used_armature["is_fk"]
        else:
            is_use = False
        layout = self.layout

        row = layout.row()
        row.label(text = "Switch right / left select")

        row = layout.row()
        if select_with == "RIGHTMOUSE":
            text = "Switch to Left"
        else :
            text = "Switch to Right"
        row.operator(TOY_OT_mouse.bl_idname, text=text, icon = "RESTRICT_SELECT_OFF")

        row = layout.row()
        row.label(text = "Enable / Disable ToyRig")

        # when tool is use on armature
        if is_use:
            row = layout.row()
            row.active = not is_lock
            if row.active:
                row.operator(TOY_OT_off.bl_idname, text="Disable ToyRig", icon = 'ARMATURE_DATA')
            else:
                row.operator(TOY_OT_empty.bl_idname, text="Disable ToyRig", icon = 'ARMATURE_DATA')

            row = layout.row()
            row.active = not is_lock
            row.label(text = "Switch IK/FK")

            row = layout.row()
            row.active = not is_lock and not is_fixed
            if row.active:
                row.operator(TOY_OT_switch.bl_idname, text="Switch IK/FK", icon = 'FILE_REFRESH')
            else:
                row.operator(TOY_OT_empty.bl_idname, text="Switch IK/FK", icon = 'FILE_REFRESH')

            row = layout.row()
            row.active = not is_lock
            row.label(text = "Fix IK/FK")

            row = layout.row()
            row.active = not is_lock
            if is_fixed:
                icon = "OUTLINER_DATA_POSE"
                text = "UnFix IK/FK"
            else:
                icon = "OUTLINER_DATA_ARMATURE"
                text = "Fix IK/FK"
            if row.active:
                row.operator(TOY_OT_fix.bl_idname, text = text, icon = icon)
            else:
                row.operator(TOY_OT_empty.bl_idname, text = text, icon = icon)

            row = layout.row()
            row.active = True
            row.label(text = "Lock Controller")

            row = layout.row()
            row.active = True
            if is_lock:
                icon = "LOCKED"
                text = "UnLock Controller"
            else:
                icon = "UNLOCKED"
                text = "Lock Controller"
            if row.active:
                row.operator(TOY_OT_lock.bl_idname, text = text, icon = icon)
            else:
                row.operator(TOY_OT_empty.bl_idname, text = text, icon = icon)

            row = layout.row()
            row.active = True
            row.label(text = "Set Keyframe")

            row = layout.row()
            row.active = True
            if row.active:
                row.operator(TOY_OT_key.bl_idname, text="Set Keyframe", icon = 'KEY_HLT')
            else:
                row.operator(TOY_OT_empty.bl_idname, text="Set Keyframe", icon = 'KEY_HLT')

            if not is_fk:
                row = layout.row()
                row.active = not is_lock
                row.label(text = "Bake Keyframe")

                row = layout.row()
                row.active = not is_lock
                if row.active:
                    row.operator(TOY_OT_bake.bl_idname, text="Bake Keyframe", icon = 'KEY_HLT')
                else:
                    row.operator(TOY_OT_empty.bl_idname, text="Switch IK follow", icon = 'KEY_HLT')

                row = layout.row()
                row.active = not is_lock
                row.label(text = "Switch IK follow")

                row = layout.row()
                row.active = not is_lock
                if row.active:
                    row.operator(TOY_OT_follow.bl_idname, text="Switch IK follow", icon = 'SNAP_ON')
                else:
                    row.operator(TOY_OT_empty.bl_idname, text="Switch IK follow", icon = 'SNAP_ON')
        # when tool is not use on armature or disabled
        else:
            row = layout.row()
            row.active = True
            row.operator(TOY_OT_on.bl_idname, text="Enable ToyRig", icon = 'POSE_HLT')

            row = layout.row()
            row.active = True
            row.label(text = "Install / Uninstall custom controller")

            row = layout.row()
            row.active = True
            row.operator(TOY_OT_push.bl_idname, text="Install custom controller", icon = 'CONSTRAINT_BONE')

            row = layout.row()
            row.active = True
            row.operator(TOY_OT_pop.bl_idname, text="Uninstall custom controller", icon = 'X')

            row = layout.row()
            row.active = True
            row.label(text = "Vanish / Appear bone's controller")

            row = layout.row()
            row.active = True
            row.operator(TOY_OT_vanish.bl_idname, text="Vanish bone's controller", icon = 'VISIBLE_IPO_ON')

            row = layout.row()
            row.active = True
            row.operator(TOY_OT_appear.bl_idname, text="Appear bone's controller", icon = 'X')

            row = layout.row()
            row.active = True
            row.label(text = "Install / Uninstall stretch constraint")

            row = layout.row()
            row.active = True
            row.operator(TOY_OT_stretch.bl_idname, text="Install stretch constraint", icon = 'CONSTRAINT')

            row = layout.row()
            row.active = True
            row.operator(TOY_OT_stiff.bl_idname, text="Uninstall stretch constraint", icon = 'X')

            row = layout.row()
            if "ToyRig_"+armature_name in The_armature:
                row.active = True
            else:
                row.active = False
            row.label(text = "CleanOff ToyRig")
            
            row = layout.row()
            if "ToyRig_"+armature_name in The_armature:
                row.active = True
                row.operator(TOY_OT_clean.bl_idname, text="CleanOff ToyRig", icon = 'CANCEL')
            else:
                row.active = False
                row.operator(TOY_OT_empty.bl_idname, text="CleanOff ToyRig", icon = 'CANCEL')

def regist_key():
    # handle the keymap
    wm = bpy.context.window_manager
    # Note that in background mode (no GUI available), keyconfigs are not available either, so we have to check this
    # to avoid nasty errors in background case.
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='Pose')
        kmi = km.keymap_items.new(TOY_OT_ik.bl_idname, 'G', 'PRESS')
        addon_keymaps.append((km, kmi))

        km = wm.keyconfigs.addon.keymaps.new(name='Pose')
        kmi = km.keymap_items.new(TOY_OT_fk.bl_idname, 'R', 'PRESS')
        addon_keymaps.append((km, kmi))

        km = wm.keyconfigs.addon.keymaps.new(name='Pose')
        kmi = km.keymap_items.new(TOY_OT_switch.bl_idname, 'Q', 'PRESS', shift=True)
        addon_keymaps.append((km, kmi))

        km = wm.keyconfigs.addon.keymaps.new(name='Pose')
        kmi = km.keymap_items.new(TOY_OT_fix.bl_idname, 'F', 'PRESS')
        addon_keymaps.append((km, kmi))

        km = wm.keyconfigs.addon.keymaps.new(name='Pose')
        kmi = km.keymap_items.new(TOY_OT_lock.bl_idname, 'Q', 'PRESS')
        addon_keymaps.append((km, kmi))

        km = wm.keyconfigs.addon.keymaps.new(name='Pose')
        kmi = km.keymap_items.new(TOY_OT_key.bl_idname, 'K', 'PRESS')
        addon_keymaps.append((km, kmi))

        km = wm.keyconfigs.addon.keymaps.new(name='Pose')
        kmi = km.keymap_items.new(TOY_OT_bake.bl_idname, 'K', 'PRESS', shift=True)
        addon_keymaps.append((km, kmi))

        km = wm.keyconfigs.addon.keymaps.new(name='Pose')
        kmi = km.keymap_items.new(TOY_OT_follow.bl_idname, 'V', 'PRESS')
        addon_keymaps.append((km, kmi))        
        
def unregist_key():
    # Note: when unregistering, it's usually good practice to do it in reverse order you registered.
    # Can avoid strange issues like keymap still referring to operators already unregistered...
    # handle the keymap
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

def set_global_var(armature_name):
    bpy.context.object["ToyRig_"+armature_name] = {"deform_bones_name": {},"deform_bones_add_name": {},"original_show_bones_name": {},"control_bones_name": {},"pole_bones_name": {},"fixed_ik_bones_name": {},"fixed_fk_bones_name": {},"fk_bones_name": {},"fk_show_bone_name": {},"exist_ik_info": {},"ik_follow": {},"exist_fkc_info": {},"ik_show_bone_name": {},"rfk_bone_name": {},"fix_show_bone_name": {},"last_bone_name": None,"is_use": True,"is_fk": True,"is_rfk": False,"is_lock": False,"is_fixed": False,"selected_bones_name": {}}
    if "Custom_"+armature_name not in bpy.context.object:      
        bpy.context.object["Custom_"+armature_name] = {"custom_bones_name": {},"vanish_bones_name": {}}

def get_original_bone_name(name):
    return name.split('_', 1)[1]

def pos_stay_still(The_armature, deform_bone_name, control_bone_name):
    deform_bone_pose = The_armature.pose.bones[deform_bone_name]
    control_bone_pose = The_armature.pose.bones[control_bone_name]
    control_bone_pose.matrix = deform_bone_pose.matrix.copy()

# install or uninstall the control bone to FK control the corresponding deform bone
def set_fk_controller(bone_name, install):
    if bone_name.split('_', 1)[0] == "ToyCtl":
        The_armature = bpy.context.object
        used_armature = The_armature["ToyRig_"+The_armature.name]
        fk_bones_name = used_armature["fk_bones_name"]
        deform_bone_name = get_original_bone_name(bone_name)
        bone_pose = The_armature.pose.bones[bone_name]
        deform_bone_pose = The_armature.pose.bones[deform_bone_name]
        bpy.context.scene.update()
        if install:
            bone_pose_pos = bone_pose.matrix.copy()

            bone_pose.constraints[constraints_name["Copy_Transforms"]].subtarget = ""
            deform_bone_pose.constraints[constraints_name["Copy_Transforms"]].subtarget = bone_name

            bone_pose.matrix = bone_pose_pos
            fk_bones_name[bone_name] = bone_name
        else:
            bone_pose_pos = deform_bone_pose.matrix.copy()

            deform_bone_pose.constraints[constraints_name["Copy_Transforms"]].subtarget = ""
            bone_pose.constraints[constraints_name["Copy_Transforms"]].subtarget = deform_bone_name

            deform_bone_pose.matrix = bone_pose_pos
            del fk_bones_name[bone_name]

# install or uninstall the control bone to IK control the corresponding deform bone
def set_ik_controller(bone_name, install, uninstall_way="both", with_pole=True):
    # according to fixed IK bone in the parent or children list, to set the this bone to be the IK controller, one end IK bone relevant one begin IK bone
    The_armature = bpy.context.object
    used_armature = The_armature["ToyRig_"+The_armature.name]
    fixed_ik_bones_name = used_armature["fixed_ik_bones_name"]
    exist_ik_info = used_armature["exist_ik_info"]
    it_happen = True
    if install:
        # if there any parent bone is fixed IK bone
        bone_pose = The_armature.pose.bones[bone_name]
        for bone in bone_pose.parent_recursive:
            if bone.name in fixed_ik_bones_name:
                ik_begin_bone_name = bone_name
                ik_end_bone_name = bone.name
                ik_chain_count = bone_pose.parent_recursive.index(bone)+1
                if ik_end_bone_name+"_end" in exist_ik_info:
                    set_ik_controller(bone_name = ik_end_bone_name, install = False, uninstall_way = "end")
                else:
                    it_happen = False
                exist_ik_info[ik_end_bone_name+"_end"] = {"opposite": ik_begin_bone_name,"count": ik_chain_count}
                exist_ik_info[ik_begin_bone_name+"_begin"] = {"opposite": ik_end_bone_name,"count": ik_chain_count}
                install_ik(The_armature,ik_begin_bone_name,ik_end_bone_name,ik_chain_count,with_pole)                        
                break
        if it_happen:
            # if there any child bone is fixed IK bone
            for bone in bone_pose.children_recursive:
                if bone.name in fixed_ik_bones_name:
                    ik_begin_bone_name = bone.name
                    ik_end_bone_name =  bone_name
                    ik_chain_count = bone.parent_recursive.index(bone_pose)+1
                    exist_ik_info[ik_end_bone_name+"_end"] = {"opposite": ik_begin_bone_name,"count": ik_chain_count}
                    exist_ik_info[ik_begin_bone_name+"_begin"] = {"opposite": ik_end_bone_name,"count": ik_chain_count}
                    install_ik(The_armature,ik_begin_bone_name,ik_end_bone_name,ik_chain_count,with_pole)
                    break
    else:
        have_end = False
        new_ik_begin_bone_name = ""
        if bone_name+"_begin" in exist_ik_info and uninstall_way in ("begin", "both"):
            parent_ik_chain_count = exist_ik_info[bone_name+"_begin"]["count"]-1
            ik_begin_bone_name = bone_name
            have_end = True
            del exist_ik_info[exist_ik_info[bone_name+"_begin"]["opposite"]+"_end"]
            del exist_ik_info[bone_name+"_begin"]
            uninstall_ik(The_armature,ik_begin_bone_name,parent_ik_chain_count,with_pole)

        if bone_name+"_end" in exist_ik_info and uninstall_way in ("end", "both"):
            new_ik_begin_bone_name = exist_ik_info[bone_name+"_end"]["opposite"]

            parent_ik_chain_count = exist_ik_info[bone_name+"_end"]["count"]-1
            ik_begin_bone_name = exist_ik_info[bone_name+"_end"]["opposite"]
            del exist_ik_info[exist_ik_info[bone_name+"_end"]["opposite"]+"_begin"]
            del exist_ik_info[bone_name+"_end"]
            uninstall_ik(The_armature,ik_begin_bone_name,parent_ik_chain_count,with_pole)

        if have_end and new_ik_begin_bone_name:
            set_ik_controller(bone_name = new_ik_begin_bone_name, install = True)

def install_ik(The_armature,ik_begin_bone_name,ik_end_bone_name,ik_chain_count,with_pole):
    bpy.context.scene.update()
    used_armature = The_armature["ToyRig_"+The_armature.name]
    ik_follow = used_armature["ik_follow"]
    ik_show_bone_name = used_armature["ik_show_bone_name"]
    ik_begin_bone_pose = The_armature.pose.bones[ik_begin_bone_name]
    parent_bone_name = ik_begin_bone_pose.parent.name
    deform_bone_pose = The_armature.pose.bones[get_original_bone_name(parent_bone_name)]
    if with_pole:
        pole_bone_name = "ToyPole_"+get_original_bone_name(ik_end_bone_name)
        pole_bone_pose = The_armature.pose.bones[pole_bone_name]

        # calculate the pole angle to make the bones's angle inside IK stay still
        pole_angle_in_radians = get_pole_angle(
            The_armature.pose.bones[get_original_bone_name(ik_end_bone_name)],
            deform_bone_pose,
            pole_bone_pose.matrix.translation)

    # set the IK controller's position base on relevant deform done is connect to parent or not and is it use deform bone follow the IK controller
    if ik_begin_bone_name.split('_', 1)[0] == "ToyCtl":
        bone_pose_pos = The_armature.pose.bones[get_original_bone_name(ik_begin_bone_name)].matrix.copy()     
        if not The_armature.data.bones[get_original_bone_name(ik_begin_bone_name)].use_connect:
            ik_begin_bone_pose.constraints[constraints_name["Copy_Transforms"]].subtarget = ""
            bone_pose_pos.translation = deform_bone_pose.tail.copy()
        elif ik_begin_bone_name in ik_follow:
            set_fk_controller(ik_begin_bone_name,install=True)
        else:
            ik_begin_bone_pose.constraints[constraints_name["Copy_Transforms"]].subtarget = ""
    else:
        bone_pose_pos = ik_begin_bone_pose.matrix.copy()
        bone_pose_pos.translation = deform_bone_pose.tail.copy()
    
    # clear the IK control bone's parent and make it's position stay still
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bone_data = The_armature.data.edit_bones[ik_begin_bone_name]
    edit_bone_data.parent = None
    bpy.ops.object.mode_set(mode='POSE')
    ik_begin_bone_pose.matrix = bone_pose_pos
    bpy.context.scene.update()
    if with_pole:
        # clear the Pole bone's parent and make it's position stay still
        pole_bone_pose_pos = pole_bone_pose.matrix.copy()
        bpy.ops.object.mode_set(mode='EDIT')
        edit_bone_data = The_armature.data.edit_bones[pole_bone_name]
        if pole_bone_name in ik_follow:
            edit_bone_data.parent = None
        else:
            parent_edit_bone_data = The_armature.data.edit_bones[ik_begin_bone_name]
            edit_bone_data.parent = parent_edit_bone_data
        bpy.ops.object.mode_set(mode='POSE')
        pole_bone_pose.matrix = pole_bone_pose_pos

        pole_bone_data = The_armature.data.bones[pole_bone_name]
        pole_bone_data.hide = False
        pole_bone_data.select = False
        ik_show_bone_name[pole_bone_name] = pole_bone_name

    # set IK constraint
    deform_bone_pose.constraints[constraints_name['IK']].subtarget = ik_begin_bone_name
    deform_bone_pose.constraints[constraints_name['IK']].chain_count = ik_chain_count
    if with_pole:
        deform_bone_pose.constraints[constraints_name['IK']].pole_target = The_armature
        deform_bone_pose.constraints[constraints_name['IK']].pole_subtarget = pole_bone_name
        deform_bone_pose.constraints[constraints_name['IK']].pole_angle = pole_angle_in_radians

def uninstall_ik(The_armature,ik_begin_bone_name,parent_ik_chain_count,with_pole):
    bpy.context.scene.update()
    used_armature = The_armature["ToyRig_"+The_armature.name]
    ik_follow = used_armature["ik_follow"]
    ik_show_bone_name = used_armature["ik_show_bone_name"]
    ik_begin_bone_pose = The_armature.pose.bones[ik_begin_bone_name]
    exist_ik_info = used_armature["exist_ik_info"]
    if ik_begin_bone_name.split('_', 1)[0] == "ToyCtl":
        parent_bone_name = "ToyCtl_" + The_armature.pose.bones[get_original_bone_name(ik_begin_bone_name)].parent.name
    else:
        parent_bone_name = "ToyCtl_" + get_original_bone_name(ik_begin_bone_name)
    deform_bone_name = get_original_bone_name(parent_bone_name)
    deform_bone_pose = The_armature.pose.bones[deform_bone_name]
    if with_pole:
        pole_bone_name = deform_bone_pose.constraints[constraints_name['IK']].pole_subtarget

    # clean the IK constraint and make deform bone stay still
    bones_pose_pos = []
    bones_pose_pos.append(deform_bone_pose.matrix)

    for i in range(parent_ik_chain_count):
        bones_pose_pos.append(deform_bone_pose.parent_recursive[i].matrix.copy())

    deform_bone_pose.constraints[constraints_name['IK']].subtarget = ""
    if with_pole:
        deform_bone_pose.constraints[constraints_name['IK']].pole_subtarget = ""
        deform_bone_pose.constraints[constraints_name['IK']].pole_target = None

    deform_bone_pose.matrix = bones_pose_pos.pop(0)
    for i in range(parent_ik_chain_count):  
        deform_bone_pose.parent_recursive[i].matrix = bones_pose_pos[i]

    if parent_ik_chain_count > 0:
        closest_bone_name = deform_bone_pose.parent_recursive[parent_ik_chain_count-1].name
    else:
        closest_bone_name = deform_bone_name
    closest_control_bone_name = "ToyCtl_"+closest_bone_name
    # if IK chain's last bone's control bone is IK controller, then make that IK controller's transforms follow the IK chain's last bone, and make that IK controller's pole target stay still
    if closest_control_bone_name+"_begin" in exist_ik_info and closest_control_bone_name in ik_follow:
        recover_ik(The_armature, closest_control_bone_name, closest_bone_name, with_pole)

    # reset the IK control bone's parent and make it's position stay still
    if ik_begin_bone_name.split('_', 1)[0] == "ToyCtl":
        bone_pose_pos = The_armature.pose.bones[get_original_bone_name(ik_begin_bone_name)].matrix.copy()
    else:
        bone_pose_pos = ik_begin_bone_pose.matrix.copy()
        bone_pose_pos.translation = deform_bone_pose.tail.copy()

    if with_pole:
        # reset the Pole bone's parent and make it's position stay still
        pole_bone_pose = The_armature.pose.bones[pole_bone_name]
        pole_bone_pose_pos = pole_bone_pose.matrix.copy()
        bpy.ops.object.mode_set(mode='EDIT')
        edit_bone_data = The_armature.data.edit_bones[pole_bone_name]
        parent_edit_bone_data = The_armature.data.edit_bones["ToyCtl_"+get_original_bone_name(pole_bone_name)]
        edit_bone_data.parent = parent_edit_bone_data
        bpy.ops.object.mode_set(mode='POSE')
        pole_bone_pose.matrix = pole_bone_pose_pos
        pole_bone_data = The_armature.data.bones[pole_bone_name]
        pole_bone_data.hide = True
        del ik_show_bone_name[pole_bone_name]
    bpy.context.scene.update()
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bone_data = The_armature.data.edit_bones[ik_begin_bone_name]
    parent_edit_bone_data = The_armature.data.edit_bones[parent_bone_name]
    edit_bone_data.parent = parent_edit_bone_data
    bpy.ops.object.mode_set(mode='POSE')
    ik_begin_bone_pose.matrix = bone_pose_pos

    if ik_begin_bone_name.split('_', 1)[0] == "ToyCtl":
        if ik_begin_bone_name in ik_follow:
            set_fk_controller(ik_begin_bone_name,install=False)
        else:
            ik_begin_bone_pose.constraints[constraints_name["Copy_Transforms"]].subtarget = get_original_bone_name(ik_begin_bone_name)

def signed_angle(vector_u, vector_v, normal):
    # Normal specifies orientation
    angle = vector_u.angle(vector_v)
    if vector_u.cross(vector_v).angle(normal) < 1:
        angle = -angle
    return angle

def get_pole_angle(base_bone, ik_bone, pole_location):
    pole_normal = (ik_bone.tail - base_bone.head).cross(pole_location - base_bone.head)
    projected_pole_axis = pole_normal.cross(base_bone.tail - base_bone.head)
    return signed_angle(base_bone.x_axis, projected_pole_axis, base_bone.tail - base_bone.head)

def recover_ik(The_armature, closest_control_bone_name, closest_bone_name, with_pole):
    # make that IK controller's transforms follow the relevant deform bone, and make that IK controller's pole target stay still
    closest_deform_bone_name = The_armature.pose.bones[closest_bone_name].parent.name
    if with_pole:
        closest_pole_bone_name = The_armature.pose.bones[closest_deform_bone_name].constraints[constraints_name['IK']].pole_subtarget
        closest_pole_bone_pose = The_armature.pose.bones[closest_pole_bone_name]
        closest_pole_bone_pose_pos = closest_pole_bone_pose.matrix.copy()

    closest_bone_pose = The_armature.pose.bones[closest_bone_name]
    closest_control_bone_pose = The_armature.pose.bones[closest_control_bone_name]
    closest_control_bone_pose.matrix = closest_bone_pose.matrix.copy()
    bpy.context.scene.update()
    if with_pole:
        closest_pole_bone_pose.matrix = closest_pole_bone_pose_pos

def set_fkc_controller(bone_name, install):
    # according to fixed FK bone in the parent or children list, to set the this bone to be the FKC controller, one end FKC bone relevant many begin FKC bone
    The_armature = bpy.context.object
    used_armature = The_armature["ToyRig_"+The_armature.name]
    fixed_fk_bones_name = used_armature["fixed_fk_bones_name"]
    exist_fkc_info = used_armature["exist_fkc_info"]
    it_happen = True
    no_child = True
    if install:
        # if there any parent bone is fixed FK bone
        bone_pose = The_armature.pose.bones[bone_name]
        for bone in bone_pose.parent_recursive:
            if bone.name in fixed_fk_bones_name:
                it_happen = False
                fk_end_bone_name = bone.name
                fk_chain_count = bone_pose.parent_recursive.index(bone)
                if fk_end_bone_name+"_end" in exist_fkc_info:
                    for bone in bone_pose.children_recursive:
                        if bone.name in fixed_fk_bones_name:
                            no_child = False
                            fk_begin_bone_name = bone.name
                            way_to_install_fkc(The_armature, fk_chain_count, bone_name = bone_name, fk_begin_bone_name = fk_begin_bone_name, fk_end_bone_name = fk_end_bone_name)                                                                      
                if no_child:
                    way_to_install_fkc(The_armature, fk_chain_count, bone_name = bone_name, fk_end_bone_name = fk_end_bone_name)
                break
        if it_happen:
            # if there any child bone is fixed FK bone
            for bone in bone_pose.children_recursive:
                if bone.name in fixed_fk_bones_name:
                    fk_begin_bone_name = bone.name
                    fk_chain_count = bone.parent_recursive.index(bone_pose)
                    way_to_install_fkc(The_armature, fk_chain_count, bone_name = bone_name, fk_begin_bone_name = fk_begin_bone_name)
    else:
        # according to different situation of this bone, uninstall it form FK china, it could be FK china's begin or inside or end
        if bone_name+"_begin" in exist_fkc_info and bone_name+"_end" in exist_fkc_info:
            fk_end_chain_count = exist_fkc_info[bone_name+"_begin"]["count"]
            fk_end_bone_name = exist_fkc_info[bone_name+"_begin"]["opposite"]
            del exist_fkc_info[exist_fkc_info[bone_name+"_begin"]["opposite"]+"_end"]["opposite"][bone_name]
            del exist_fkc_info[exist_fkc_info[bone_name+"_begin"]["opposite"]+"_end"]["count"][bone_name]
            del exist_fkc_info[bone_name+"_begin"]  

            fk_chains_count = exist_fkc_info[bone_name+"_end"]["count"]
            fk_begin_bones_name = exist_fkc_info[bone_name+"_end"]["opposite"]
            for fk_begin_bone_name,fk_begin_chain_count in zip(fk_begin_bones_name,fk_chains_count.values()):
                fk_chain_count = fk_begin_chain_count + fk_end_chain_count + 1
                exist_fkc_info[fk_begin_bone_name+"_begin"] = {"opposite": fk_end_bone_name, "count": fk_chain_count}
                exist_fkc_info[fk_end_bone_name+"_end"]["opposite"][fk_begin_bone_name] = fk_begin_bone_name
                exist_fkc_info[fk_end_bone_name+"_end"]["count"][fk_begin_bone_name] = fk_chain_count
            del exist_fkc_info[bone_name+"_end"]

            install_self_fkc(The_armature,bone_name)

        elif bone_name+"_begin" in exist_fkc_info:
            fk_chain_count = exist_fkc_info[bone_name+"_begin"]["count"]
            fk_begin_bone_name = bone_name
            del exist_fkc_info[exist_fkc_info[bone_name+"_begin"]["opposite"]+"_end"]["opposite"][fk_begin_bone_name]
            del exist_fkc_info[exist_fkc_info[bone_name+"_begin"]["opposite"]+"_end"]["count"][fk_begin_bone_name]
            if not exist_fkc_info[exist_fkc_info[bone_name+"_begin"]["opposite"]+"_end"]["opposite"]:
                del exist_fkc_info[exist_fkc_info[bone_name+"_begin"]["opposite"]+"_end"]
            del exist_fkc_info[bone_name+"_begin"]
            uninstall_fkc(The_armature,fk_begin_bone_name,fk_chain_count)

        elif bone_name+"_end" in exist_fkc_info:
            fk_chains_count = exist_fkc_info[bone_name+"_end"]["count"]
            fk_begin_bones_name = exist_fkc_info[bone_name+"_end"]["opposite"]
            for fk_begin_bone_name,fk_chain_count in zip(fk_begin_bones_name,fk_chains_count.values()):
                del exist_fkc_info[fk_begin_bone_name+"_begin"]
                uninstall_fkc(The_armature,fk_begin_bone_name,fk_chain_count)
            del exist_fkc_info[bone_name+"_end"]

def way_to_install_fkc(The_armature, fk_chain_count, bone_name="", fk_begin_bone_name = "", fk_end_bone_name = ""):
    # according to different situation of this bone, install it to FK china, it could be FK china's begin or inside or end
    bpy.context.scene.update()
    used_armature = The_armature["ToyRig_"+The_armature.name]
    exist_fkc_info = used_armature["exist_fkc_info"]
    if fk_begin_bone_name and fk_end_bone_name:
        exist_fkc_info[fk_begin_bone_name+"_begin"] = {"opposite": bone_name, "count": exist_fkc_info[fk_begin_bone_name+"_begin"]["count"]-fk_chain_count-1}
        if bone_name+"_end" in exist_fkc_info:             
            exist_fkc_info[bone_name+"_end"]["opposite"][fk_begin_bone_name] = fk_begin_bone_name
            exist_fkc_info[bone_name+"_end"]["count"][fk_begin_bone_name] = fk_chain_count            
        else:
            exist_fkc_info[bone_name+"_end"] = {"opposite": {fk_begin_bone_name: fk_begin_bone_name}, "count": {fk_begin_bone_name: exist_fkc_info[fk_begin_bone_name+"_begin"]["count"]}}
        exist_fkc_info[bone_name+"_begin"] = {"opposite": fk_end_bone_name, "count": fk_chain_count}
        if fk_end_bone_name+"_end" in exist_fkc_info:
            del exist_fkc_info[fk_end_bone_name+"_end"]["opposite"][fk_begin_bone_name]
            del exist_fkc_info[fk_end_bone_name+"_end"]["count"][fk_begin_bone_name]
            if bone_name not in exist_fkc_info[fk_end_bone_name+"_end"]["opposite"]:
                exist_fkc_info[fk_end_bone_name+"_end"]["opposite"][bone_name] = bone_name
                exist_fkc_info[fk_end_bone_name+"_end"]["count"][bone_name] = fk_chain_count
        else:        
            exist_fkc_info[fk_end_bone_name+"_end"] = {"opposite": {bone_name: bone_name}, "count": {bone_name: fk_chain_count}}
        uninstall_self_fkc(The_armature,bone_name)

    elif fk_begin_bone_name:
        exist_fkc_info[fk_begin_bone_name+"_begin"] = {"opposite": bone_name, "count": fk_chain_count}
        if bone_name+"_end" in exist_fkc_info:
            exist_fkc_info[bone_name+"_end"]["opposite"][fk_begin_bone_name] = fk_begin_bone_name
            exist_fkc_info[bone_name+"_end"]["count"][fk_begin_bone_name] = fk_chain_count 
        else:
            exist_fkc_info[bone_name+"_end"] = {"opposite": {fk_begin_bone_name: fk_begin_bone_name}, "count": {fk_begin_bone_name: fk_chain_count}}
        install_fkc(The_armature,fk_begin_bone_name,fk_chain_count)

    elif fk_end_bone_name:
        if fk_end_bone_name+"_end" in exist_fkc_info:
            exist_fkc_info[fk_end_bone_name+"_end"]["opposite"][bone_name] = bone_name
            exist_fkc_info[fk_end_bone_name+"_end"]["count"][bone_name] = fk_chain_count
        else:
            exist_fkc_info[fk_end_bone_name+"_end"] = {"opposite": {bone_name: bone_name}, "count": {bone_name: fk_chain_count}}
        exist_fkc_info[bone_name+"_begin"] = {"opposite": fk_end_bone_name, "count": fk_chain_count}
        install_fkc(The_armature,bone_name,fk_chain_count)        

def install_fkc(The_armature,first_chain_bone_name,fk_chain_count):
    # according to fk_chain_coun, in proper order set the driver that make pose bone copy it parent's rotation, begin from first_chain_bone's child
    bpy.context.scene.update()
    first_bone_pose = The_armature.pose.bones[first_chain_bone_name]
    for i in range(fk_chain_count):
        bone_pose = The_armature.pose.bones[get_original_bone_name(first_bone_pose.parent_recursive[i].name)]
        parent_bone_pose = The_armature.pose.bones[get_original_bone_name(first_bone_pose.parent_recursive[i+1].name)]
        bone_pose.rotation_mode = 'XYZ'
        parent_bone_pose.rotation_mode = 'XYZ'
        add_fkc_driver(bone_pose, parent_bone_pose, The_armature)

def uninstall_fkc(The_armature,first_chain_bone_name,fk_chain_count):
    # according to fk_chain_count, in proper order remover the driver of pose bone copy it parent's rotation, begin from first_chain_bone's child
    bpy.context.scene.update()
    first_bone_pose = The_armature.pose.bones[first_chain_bone_name]
    for i in range(fk_chain_count):
        bone_pose = The_armature.pose.bones[get_original_bone_name(first_bone_pose.parent_recursive[i].name)]
        bone_pose.rotation_mode = 'XYZ'
        remove_fkc_driver(bone_pose)

def install_self_fkc(The_armature,bone_name):
    # only set one driver, begin from first_chain_bone
    bone_pose = The_armature.pose.bones[get_original_bone_name(bone_name)]
    parent_bone_pose = bone_pose.parent
    bone_pose.rotation_mode = 'XYZ'
    parent_bone_pose.rotation_mode = 'XYZ'
    add_fkc_driver(bone_pose, parent_bone_pose, The_armature)

def uninstall_self_fkc(The_armature,bone_name):
    # only remover one driver, begin from first_chain_bone
    bone_pose = The_armature.pose.bones[get_original_bone_name(bone_name)]
    bone_pose.rotation_mode = 'XYZ'
    remove_fkc_driver(bone_pose)

def add_fkc_driver(bone_pose, parent_bone_pose, The_armature):
    # Add copy parent rotation driver to pose bone's unlock orientation and maintain pose bone's rotation
    fs = bone_pose.driver_add("rotation_euler")
    index_list = ["x","y","z"]
    for i in range(3):
        if not bone_pose.lock_rotation[i]:
            f = fs[i]
            bone_transform_type = index_list[i]

            d = f.driver
            d.type = "SCRIPTED"
            v = d.variables.new()
            v.name = "toy_rotation_euler_" + bone_transform_type
            v.type = "TRANSFORMS"
            v.targets[0].id = The_armature
            v.targets[0].bone_target = parent_bone_pose.name
            v.targets[0].transform_type = "ROT_" + bone_transform_type.upper()
            v.targets[0].transform_space = 'LOCAL_SPACE'

            self_initial_angle = bone_pose.rotation_euler[i]
            parent_initial_angle = parent_bone_pose.rotation_euler[i]
            d.expression = "fkc_driver_func(toy_rotation_euler_"+ bone_transform_type + ",'" + str(self_initial_angle) + "','" + str(parent_initial_angle) + "')"

def remove_fkc_driver(bone_pose):
    # Remove the pose bone's copy parent rotation driver and maintain pose bone's rotation
    tmp_rotation_euler = bone_pose.rotation_euler[:]
    bone_pose.driver_remove("rotation_euler")
    for i in range(3):
        bone_pose.rotation_euler[i] = tmp_rotation_euler[i]

def fkc_driver_func(parent_angle, self_initial_angle, parent_initial_angle):
    # copy parent rotation and from pose bone's initial rotation
    self_initial_angle = float(self_initial_angle)
    parent_initial_angle = float(parent_initial_angle)
    return self_initial_angle + parent_angle - parent_initial_angle  

def set_fk_var(context):
    # when change to fk mode, change few setting
    The_armature = context.object
    used_armature = The_armature["ToyRig_"+The_armature.name]
    used_armature["is_fk"] = True
    The_armature.pose.bone_groups["ToyRigGroups"].color_set = toy_settings['FK_color']

def set_ik_var(context):
    # when change to ik mode, change few setting
    The_armature = context.object
    used_armature = The_armature["ToyRig_"+The_armature.name]
    used_armature["is_fk"] = False
    The_armature.pose.bone_groups["ToyRigGroups"].color_set = toy_settings['IK_color']

def fk_to_ik(context):
    # when form fk mode to ik mode, uninstall all controller in fk mode, and install corresponding controller in IK mode
    The_armature = context.object
    used_armature = The_armature["ToyRig_"+The_armature.name]
    fixed_ik_bones_name = used_armature["fixed_ik_bones_name"]
    ik_show_bone_name = used_armature["ik_show_bone_name"]
    control_bones_name = used_armature["control_bones_name"]
    uninstall_all_fk(The_armature)
    uninstall_all_fkc(The_armature)
    # the controller that be selected in fk mode, if is qualified, then become the fixed IK controller
    for bone in context.visible_pose_bones:
        if bone.name in control_bones_name:
            if bone.name.split('_', 1)[0] == "ToyCtl":
                deform_bone_name = get_original_bone_name(bone.name)
            else:
                deform_bone_name = bone.name
            if deform_bone_name in ik_show_bone_name:
                bone_data = The_armature.data.bones[bone.name]
                if bone.name not in fixed_ik_bones_name:
                    if bone_data.select:
                            fixed_ik_bones_name[bone.name] = bone.name
                    else:
                        bone_data.hide = True
            else:
                bone_data.select = False
                bone_data.hide = True
    install_all_fixed_ik(The_armature)

def ik_to_fk(context):
    # when form ik mode to fk mode, uninstall all controller in ik mode, and install corresponding controller in FK mode
    The_armature = context.object
    used_armature = The_armature["ToyRig_"+The_armature.name]
    fixed_fk_bones_name = used_armature["fixed_fk_bones_name"]
    fk_show_bone_name = used_armature["fk_show_bone_name"]
    control_bones_name = used_armature["control_bones_name"]
    uninstall_all_ik(The_armature)
    # the controller that be selected in ik mode, if is qualified, then become the fixed IK controller
    for bone in context.visible_pose_bones:
        if bone.name in control_bones_name:
            if bone.name.split('_', 1)[0] == "ToyCtl":
                deform_bone_name = get_original_bone_name(bone.name)
            else:
                deform_bone_name = bone.name
            if deform_bone_name in fk_show_bone_name:
                bone_data = The_armature.data.bones[bone.name]
                if bone.name not in fixed_fk_bones_name:
                    if bone_data.select:
                        fixed_fk_bones_name[bone.name] = bone.name
                    else:
                        bone_data.hide = True
                if bone_data.select and bone.name.split('_', 1)[0] != "ToyCtlEnd":
                    set_fk_controller(bone_name = bone.name, install = True)
            else:
                bone_data.select = False
                bone_data.hide = True
    install_all_fixed_fk(The_armature)

def install_all_fixed_ik(The_armature):
    used_armature = The_armature["ToyRig_"+The_armature.name]
    fixed_ik_bones_name = used_armature["fixed_ik_bones_name"]
    exist_ik_info = used_armature["exist_ik_info"]
    for bone_name in fixed_ik_bones_name:
        bone_data = The_armature.data.bones[bone_name]
        bone_data.hide = False
        if bone_name+"_begin" in exist_ik_info or bone_name+"_end" in exist_ik_info:
            continue
        else:
            set_ik_controller(bone_name = bone_name, install = True)

def install_all_fixed_fk(The_armature):
    used_armature = The_armature["ToyRig_"+The_armature.name]
    exist_fkc_info = used_armature["exist_fkc_info"]
    fixed_fk_bones_name = used_armature["fixed_fk_bones_name"]
    for bone_name in fixed_fk_bones_name:
        bone_data = The_armature.data.bones[bone_name]
        bone_data.hide = False
        if bone_name+"_begin" in exist_fkc_info or bone_name+"_end" in exist_fkc_info:
            continue
        else:
            set_fkc_controller(bone_name = bone_name, install = True)        

def uninstall_all_ik(The_armature):
    used_armature = The_armature["ToyRig_"+The_armature.name]
    fixed_ik_bones_name = used_armature["fixed_ik_bones_name"]
    for bone_name in fixed_ik_bones_name:
        bone_data = The_armature.data.bones[bone_name]
        set_ik_controller(bone_name = bone_name, install = False)
        if bone_data.select == False:
            bone_data.hide = True

def uninstall_all_fk(The_armature):
    used_armature = The_armature["ToyRig_"+The_armature.name]
    fk_bones_name = used_armature["fk_bones_name"]    
    for bone_name in fk_bones_name:
        set_fk_controller(bone_name = bone_name, install = False)

def uninstall_all_fkc(The_armature):
    used_armature = The_armature["ToyRig_"+The_armature.name]
    fixed_fk_bones_name = used_armature["fixed_fk_bones_name"]     
    for bone_name in fixed_fk_bones_name:
        bone_data = The_armature.data.bones[bone_name]
        set_fkc_controller( bone_name, install = False )
        if bone_data.select == False:
            bone_data.hide = True

def uninstall_fk_in_fix(context):
    # fix mode only can set fk controller,so
    The_armature = context.object
    used_armature = The_armature["ToyRig_"+The_armature.name]
    fix_show_bone_name = used_armature["fix_show_bone_name"]
    fk_bones_name = used_armature["fk_bones_name"]
    for bone_name in fk_bones_name:
        if get_original_bone_name(bone_name) in fix_show_bone_name:
            set_fk_controller(bone_name = bone_name, install = False)
            The_armature.data.bones[bone_name].select = False
            The_armature.data.bones[bone_name].hide = True

def need_rfk(context):
    # check if the last bone be selected can be set to reverse FK or not
    The_armature = context.object
    used_armature = The_armature["ToyRig_"+The_armature.name]
    exist_ik_info = used_armature["exist_ik_info"]
    last_bone_name = used_armature["last_bone_name"]
    if last_bone_name and last_bone_name+"_begin" in exist_ik_info and last_bone_name+"_end" in exist_ik_info:
        return True
    else:
        return False

def set_rfk(context,install):
    # install or uninstall reverse FK to the last bone be selected, achieve reverse FK use rotate around cursor and set IK without pole
    The_armature = context.object
    used_armature = The_armature["ToyRig_"+The_armature.name]
    exist_ik_info = used_armature["exist_ik_info"]
    rfk_bone_name = used_armature["rfk_bone_name"]
    fixed_ik_bones_name = used_armature["fixed_ik_bones_name"]
    bone_name = used_armature["last_bone_name"]
    if install:
        fixed_ik_bones_name[bone_name] = bone_name
        cursor_bone_name = exist_ik_info[bone_name+"_end"]["opposite"]
        rfk_bone_name[cursor_bone_name] = bone_name
        set_ik_controller(bone_name = cursor_bone_name, install = False, uninstall_way = "begin")
        set_ik_controller(bone_name = cursor_bone_name, install = True, with_pole = False)
        set_ik_controller(bone_name = bone_name, install = False, uninstall_way = "begin")
        set_ik_controller(bone_name = bone_name, install = True, with_pole = False)
        bpy.ops.pose.select_all(action='DESELECT')
        cursor_bone_data = The_armature.data.bones[cursor_bone_name]
        cursor_bone_data.select = True
        bpy.ops.view3d.snap_cursor_to_selected()
        cursor_bone_data.select = False
        bone_data = The_armature.data.bones[bone_name]
        bone_data.select = True
        The_armature.data.bones.active = bone_data
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].pivot_point='CURSOR'
                area.spaces[0].transform_manipulators = {'ROTATE'}       
        used_armature["is_rfk"] = True
    else:
        for cursor_bone_name in rfk_bone_name:
            set_ik_controller(bone_name = cursor_bone_name, install = False, uninstall_way = "begin", with_pole = False)
            set_ik_controller(bone_name = cursor_bone_name, install = True)
            set_ik_controller(bone_name = bone_name, install = False, uninstall_way = "begin", with_pole = False)
            set_ik_controller(bone_name = bone_name, install = True)
            del rfk_bone_name[cursor_bone_name]
        del fixed_ik_bones_name[bone_name]

        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].pivot_point='MEDIAN_POINT'
                area.spaces[0].transform_manipulators = {'TRANSLATE'}
        used_armature["is_rfk"] = False

def reset_controller(context):
    # recover the controller in corresponding mode to where it leave
    The_armature = context.object
    used_armature = The_armature["ToyRig_"+The_armature.name]
    last_bone_name = used_armature["last_bone_name"]
    is_fixed = used_armature["is_fixed"]
    is_fk = used_armature["is_fk"]
    if is_fk:
        context.space_data.transform_manipulators = {'ROTATE'}
        install_all_fixed_fk(The_armature)
        for bone_name in used_armature["selected_bones_name"]:
            bone_data = The_armature.data.bones[bone_name]
            bone_data.hide = False
            set_fk_controller(bone_name = bone_name, install = True)
    else:
        context.space_data.transform_manipulators = {'TRANSLATE'}
        install_all_fixed_ik(The_armature)
        if last_bone_name:
            bone_data = The_armature.data.bones[last_bone_name]
            bone_data.hide = False
            set_ik_controller(bone_name = last_bone_name, install = True)
            is_rfk = used_armature["is_rfk"]
            if is_rfk:
                set_rfk(context,install=True)
        if is_fixed:
            for bone_name in used_armature["selected_bones_name"]:
                bone_data = The_armature.data.bones[bone_name]
                bone_data.hide = False
                set_fk_controller(bone_name = bone_name, install = True)            
    if last_bone_name and not is_fixed:
        bone_data = The_armature.data.bones[last_bone_name]
        The_armature.data.bones.active = bone_data

    for bone_name in used_armature["selected_bones_name"]:
        The_armature.data.bones[bone_name].select = True
    used_armature["selected_bones_name"].clear()

def display_all_deform_bones(context,display,select_all = False):
    The_armature = context.object
    used_armature = The_armature["ToyRig_"+The_armature.name]
    deform_bones_name = used_armature["deform_bones_name"]
    custom_settings = The_armature["Custom_"+The_armature.name]
    custom_bones_name = custom_settings["custom_bones_name"]
    if display:
        The_armature.data.layers[0] = True
        for bone_name in deform_bones_name:
            The_armature.data.bones[bone_name].hide = False
        for bone_name in custom_bones_name:
            The_armature.data.bones[bone_name].hide = False
        if select_all:
            for bone_name in deform_bones_name:
                The_armature.data.bones[bone_name].select = True
            for bone_name in custom_bones_name:
                The_armature.data.bones[bone_name].select = True
    else:
        for bone_name in deform_bones_name:
            The_armature.data.bones[bone_name].hide = True  
        for bone_name in custom_bones_name:
            The_armature.data.bones[bone_name].hide = True
        if select_all:
            for bone_name in deform_bones_name:
                The_armature.data.bones[bone_name].select = False
            for bone_name in custom_bones_name:
                The_armature.data.bones[bone_name].select = False
        The_armature.data.layers[0] = False

def mouse_in_3dview(context, x, y):
    # if the mouse is in 3D view, then return it coordinate in that 3D view
    context.scene.update()
    mouse_is_in = (None, None, None, None)
    for area in context.screen.areas:
        if area.type != 'VIEW_3D':
            continue
        for region in area.regions:
            if region.type == 'WINDOW':
                if (x >= region.x and
                    y >= region.y and
                    x < region.width + region.x and
                    y < region.height + region.y):
                    mouse_is_in = (region, area.spaces.active.region_3d, x - region.x, y - region.y)
    return mouse_is_in

def install_custom_controller(context):
    # install custom controller, so the tool will leave it alone, which is mean the tool will not install any other controller over it
    armature_name = context.object.name
    The_armature = context.object
    if "Custom_"+armature_name not in The_armature:
        The_armature["Custom_"+armature_name] = {"custom_bones_name": {},"vanish_bones_name": {}}
    custom_settings = The_armature["Custom_"+armature_name]
    for bone in context.selected_pose_bones:
        if bone.name not in custom_settings["custom_bones_name"]:
            custom_settings["custom_bones_name"][bone.name] = bone.name

def uninstall_custom_controller(context):
    armature_name = context.object.name
    The_armature = context.object
    if "Custom_"+armature_name not in The_armature:
        The_armature["Custom_"+armature_name] = {"custom_bones_name": {},"vanish_bones_name": {}}
    else:
        custom_settings = The_armature["Custom_"+armature_name]
        for bone in context.selected_pose_bones:
            if bone.name in custom_settings["custom_bones_name"]:
                del custom_settings["custom_bones_name"][bone.name]

def vanish_bones_controller(context):
    # if the deform bone's controller is vanish, then it controller cannot be selected
    armature_name = context.object.name
    The_armature = context.object
    if "Custom_"+armature_name not in The_armature:
        The_armature["Custom_"+armature_name] = {"custom_bones_name": {},"vanish_bones_name": {}}
    custom_settings = The_armature["Custom_"+armature_name]
    for bone in context.selected_pose_bones:
        if bone.name not in custom_settings["vanish_bones_name"]:
            custom_settings["vanish_bones_name"][bone.name] = bone.name

def appear_bones_controller(context):
    armature_name = context.object.name
    The_armature = context.object
    if "Custom_"+armature_name not in The_armature:
        The_armature["Custom_"+armature_name] = {"custom_bones_name": {},"vanish_bones_name": {}}
    else:
        custom_settings = The_armature["Custom_"+armature_name]
        for bone in context.selected_pose_bones:
            if bone.name in custom_settings["vanish_bones_name"]:
                del custom_settings["vanish_bones_name"][bone.name]

def set_stretch_controller(stretch_begin_bone_name, install):
    The_armature = bpy.context.object
    bpy.context.scene.update()
    bone_pose = The_armature.pose.bones[stretch_begin_bone_name]
    deform_bone_name = stretch_begin_bone_name.split('_', 1)[1]
    deform_bone_data = The_armature.data.bones[deform_bone_name]
    deform_bone_pose = The_armature.pose.bones[deform_bone_name]
    deform_bone_data.hide = False
    if deform_bone_pose.child:
        child_bone_pose = deform_bone_pose.child
        child_bone_data = The_armature.data.bones[child_bone_pose.name]
        child_bone_data.hide = False
    if install:
        new_constraint = deform_bone_pose.constraints.new(type='STRETCH_TO')
        new_constraint.name = constraints_name["Stretch_To"]
        deform_bone_pose.constraints[constraints_name["Stretch_To"]].target = The_armature
        deform_bone_pose.constraints[constraints_name["Stretch_To"]].subtarget = stretch_begin_bone_name

        if deform_bone_pose.child:
            bone_pose.matrix = child_bone_pose.matrix.copy()
            # set child of deform bone's copy the empty transforms
            new_constraint = child_bone_pose.constraints.new("COPY_TRANSFORMS")
            new_constraint.name = constraints_name["Stretch_To"] + "_copy_transforms"
            child_bone_pose.constraints[constraints_name["Stretch_To"] + "_copy_transforms"].target = The_armature
            child_bone_pose.constraints[constraints_name["Stretch_To"] + "_copy_transforms"].subtarget = stretch_begin_bone_name
            child_bone_pose.constraints[constraints_name["Stretch_To"] + "_copy_transforms"].target_space = 'WORLD'
            child_bone_pose.constraints[constraints_name["Stretch_To"] + "_copy_transforms"].owner_space = 'WORLD'

        ToyStretchCtl_Shape = bpy.data.objects["ToyStretchCtl_Shape"]
        bone_pose.custom_shape = ToyStretchCtl_Shape
        The_armature.data.bones[stretch_begin_bone_name].show_wire = True   
    else:
        deform_bone_pose.constraints.remove(deform_bone_pose.constraints[constraints_name["Stretch_To"]])
        if deform_bone_pose.child:
            bone_pose.matrix = child_bone_pose.matrix.copy()

            child_bone_pose_pos = bone_pose.matrix.copy()        
            child_bone_pose.constraints.remove(child_bone_pose.constraints[constraints_name["Stretch_To"] + "_copy_transforms"])
            child_bone_pose.matrix = child_bone_pose_pos

def set_fix_show_bone_name(context):
    # when enter the fix mode, according to corresponding show bone name in that mode, and controller in that mode, get show bone name in fix mode
    The_armature = context.object
    used_armature = The_armature["ToyRig_"+The_armature.name]
    custom_settings = The_armature["Custom_"+The_armature.name]
    custom_bones_name = custom_settings["custom_bones_name"]
    fix_show_bone_name = used_armature["fix_show_bone_name"]
    fix_show_bone_name.clear()
    is_fk = used_armature["is_fk"]
    if is_fk:
        show_bone_name = used_armature["fk_show_bone_name"]
        fixed_bones_name = used_armature["fixed_fk_bones_name"]
        exist_info = used_armature["exist_fkc_info"]
    else:
        show_bone_name = used_armature["ik_show_bone_name"]
        fixed_bones_name = used_armature["fixed_ik_bones_name"]
        exist_info = used_armature["exist_ik_info"]
    # bone inside the FK china or IK china will not show in fix mode
    for bone_name in show_bone_name:
        if bone_name in custom_bones_name:
            fix_show_bone_name[bone_name] = bone_name
        elif bone_name.split('_', 1)[0] != "ToyCtlEnd" and bone_name.split('_', 1)[0] != "ToyPole" and "ToyCtl_"+bone_name not in fixed_bones_name:
            bone_pose = The_armature.pose.bones[bone_name]
            for bone in bone_pose.parent_recursive:
                if "ToyCtl_"+bone.name in fixed_bones_name and "ToyCtl_"+bone.name+"_end" in exist_info:
                    if not bone_pose.child:
                        if "ToyCtlEnd_"+bone_name in fixed_bones_name:
                            break
                    else:
                        for bone in bone_pose.children_recursive:                       
                            if "ToyCtl_"+bone.name in fixed_bones_name:
                                break
                            if not bone.child:
                                if "ToyCtlEnd_"+bone.name in fixed_bones_name:
                                    break
                        else:
                            continue
                        break
            else:
                fix_show_bone_name[bone_name] = bone_name

def lock_switch(context):
    # entry or quit the lock mode
    used_armature = context.object["ToyRig_"+context.object.name]
    if used_armature["is_lock"]:
        if context.object.data.layers[0]:
            display_all_deform_bones(context,display = False)        
        reset_controller(context)
        used_armature["is_lock"] = False
    else:
        The_armature = context.object
        # if select the pole bone before enter the lock mode,then show the selected pole bone inside the lock mode for position adjustment
        selected_pole_bone_name = []
        for bone in context.selected_pose_bones:
            if bone.name.split('_', 1)[0] == "ToyPole":
                selected_pole_bone_name.append(bone.name)

        uninstall_all_controller(context)

        for bone_name in selected_pole_bone_name:
            bone_data = The_armature.data.bones[bone_name]
            bone_data.hide = False 
            bone_data.select = True

        used_armature["is_lock"] = True

def uninstall_all_controller(context):
    The_armature = context.object
    used_armature = The_armature["ToyRig_"+The_armature.name]
    for bone in context.selected_pose_bones:
        used_armature["selected_bones_name"][bone.name] = bone.name
    is_fixed = used_armature["is_fixed"]
    if is_fixed:
        uninstall_fk_in_fix(context)
    is_fk = used_armature["is_fk"]
    if is_fk:
        uninstall_all_fk(The_armature)
    else:
        is_rfk = used_armature["is_rfk"]
        if is_rfk:
            set_rfk(context,install=False)
            used_armature["is_rfk"] = True
        uninstall_all_ik(The_armature)

    for bone in context.visible_pose_bones:
        if bone.name.split('_', 1)[0] == "ToyCtl" or bone.name.split('_', 1)[0] == "ToyCtlEnd":
            bone_data = The_armature.data.bones[bone.name]
            bone_data.select = False
            bone_data.hide = True

def set_keyframe(context):
    used_armature = context.object["ToyRig_"+context.object.name]
    is_lock = used_armature["is_lock"]
    if not is_lock:
        lock_switch(context)
        key_the_frame(context)
        lock_switch(context)
    else:
        key_the_frame(context)
        
def key_the_frame(context):
    bpy.ops.pose.select_all(action='DESELECT')
    display_all_deform_bones(context,display = True,select_all=True)
    bpy.ops.anim.keyframe_insert_menu(type='BUILTIN_KSI_VisualLocRotScale')
    display_all_deform_bones(context,display = False,select_all=True)
        
class TOY_OT_empty(bpy.types.Operator):
    bl_idname = "toy.empty"
    bl_label = "TOY_OT_empty"

    def execute(self, context):
        return {'FINISHED'}

class TOY_OT_mouse(bpy.types.Operator):
    # change the way to select controller
    bl_idname = "toy.mouse"
    bl_label = "TOY_OT_mouse"

    def execute(self, context):
        global select_with
        if select_with == "RIGHTMOUSE":
            select_with = "LEFTMOUSE"
        else:
            select_with = "RIGHTMOUSE"
        return {'FINISHED'}

class TOY_OT_on(bpy.types.Operator):
    bl_idname = "toy.on"
    bl_label = "TOY_OT_on"

    def execute(self, context):   
        try:
            armature_name = context.object.name
            The_armature = context.object
            self.apply_transform(context, The_armature)
            if "ToyRig_"+armature_name not in The_armature:
                set_global_var(armature_name)
                self.create_controller(context)
            if fkc_driver_func not in bpy.app.driver_namespace:
                # add dirver function for FK china
                bpy.app.driver_namespace['fkc_driver_func'] = fkc_driver_func
            regist_key()
            global modal_on
            if not modal_on:
                bpy.ops.toy.play()
                modal_on = True
            used_armature = The_armature["ToyRig_"+armature_name]
            used_armature["is_use"] = True
            context.space_data.pivot_point = 'MEDIAN_POINT'
            context.space_data.transform_orientation = 'LOCAL'
            for mesh in bpy.data.objects[armature_name].children:
                mesh.hide_select = True

            self.adjust_controller(The_armature)
            display_all_deform_bones(context, display=False)
            reset_controller(context)
            bpy.ops.ed.undo_push(message="ToyRig_history_on")
        except Exception:
            self.report({'ERROR'}, traceback.format_exc())
            self.report({'ERROR'}, "Magic lose contol.....please tell Magician the message above.")
        return {'FINISHED'}

    def apply_transform(self, context, The_armature):
        # apply armature's transform
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        The_armature.select = True
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.ops.object.mode_set(mode='POSE')

    def create_controller(self, context):
        # create control bone
        The_armature = context.object
        used_armature = The_armature["ToyRig_"+The_armature.name]
        deform_bones_name = used_armature["deform_bones_name"]
        deform_bones_add_name = used_armature["deform_bones_add_name"]
        original_show_bones_name = used_armature["original_show_bones_name"]
        fk_show_bone_name = used_armature["fk_show_bone_name"]
        ik_show_bone_name = used_armature["ik_show_bone_name"]
        control_bones_name = used_armature["control_bones_name"]
        pole_bones_name = used_armature["pole_bones_name"]
        custom_settings = The_armature["Custom_"+The_armature.name]
        custom_bones_name = custom_settings["custom_bones_name"]
        The_armature.data.show_bone_custom_shapes = True
        The_armature.data.show_group_colors = True
        The_armature.show_x_ray = True
        bpy.ops.object.mode_set(mode='EDIT')
        if The_armature.type == 'ARMATURE':
            deform_bones = []
            for bone in The_armature.data.edit_bones:
                if bone.name not in custom_bones_name:
                    deform_bones.append(bone)
                    deform_bones_name[bone.name] = bone.name
                    deform_bones_add_name[bone.name] = bone.name
                    original_show_bones_name[bone.name] = bone.name
                    fk_show_bone_name[bone.name] = bone.name
                    ik_show_bone_name[bone.name] = bone.name
                
            for bone in deform_bones:
                # add fk&&ik control bone
                new_bone = The_armature.data.edit_bones.new("ToyCtl_"+bone.name)
                control_bones_name[new_bone.name] = new_bone.name
                new_bone.head = bone.head
                new_bone.tail = bone.tail
                new_bone.roll = bone.roll

                if not bone.children:
                    new_bone = The_armature.data.edit_bones.new("ToyCtlEnd_"+bone.name)
                    control_bones_name[new_bone.name] = new_bone.name
                    fk_show_bone_name[new_bone.name] = new_bone.name
                    ik_show_bone_name[new_bone.name] = new_bone.name
                    deform_bones_add_name[new_bone.name] = new_bone.name
                    original_show_bones_name[new_bone.name] = new_bone.name
                    new_bone.head = bone.tail
                    new_bone.tail = bone.tail
                    for i in range(3):
                        new_bone.tail[i] = new_bone.tail[i] + bone.vector[i]
                    new_bone.roll = bone.roll

                # add pole bone
                new_bone = The_armature.data.edit_bones.new("ToyPole_"+bone.name)
                pole_bones_name[new_bone.name] = new_bone.name
                if bone.children:
                    self.set_pole_position_normal(new_bone, bone)
                else:
                    self.set_pole_position_unusual(new_bone, bone)

        # create custom shape if not already created
        bpy.ops.object.mode_set(mode='OBJECT')
        if "ToyCtl_Shape" not in bpy.data.objects:
            # create fk&&ik controller shape
            bpy.ops.mesh.primitive_torus_add(location=(0, 0, 0), rotation=(0, 0, 0), layers=(True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False), view_align=False, major_radius=0.2, minor_radius=0.01, abso_major_rad=1.25, abso_minor_rad=0.75)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.transform.rotate(value=1.5708, axis=(1, 0, 0), constraint_axis=(True, False, False), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)
            bpy.ops.mesh.delete(type='ONLY_FACE')
            bpy.ops.object.mode_set(mode='OBJECT')
            context.object.name = "ToyCtl_Shape"
            ToyCtl_Shape = context.object
            ToyCtl_Shape.hide_render = True
            ToyCtl_Shape.hide = True
        else:
            ToyCtl_Shape = bpy.data.objects["ToyCtl_Shape"]
        if "ToyPole_Shape" not in bpy.data.objects:
            # create pole controller shape
            bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, size=0.2, view_align=False, enter_editmode=False, location=(0, 0, 0), layers=(True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.delete(type='ONLY_FACE')
            bpy.ops.object.mode_set(mode='OBJECT')
            context.object.name = "ToyPole_Shape"
            ToyPole_Shape = context.object
            ToyPole_Shape.hide_render = True
            ToyPole_Shape.hide = True
        else:
            ToyPole_Shape = bpy.data.objects["ToyPole_Shape"]
        bpy.ops.object.select_all(action='DESELECT')
        context.scene.objects.active = The_armature
        bpy.ops.object.mode_set(mode='POSE')
        if "ToyRigGroups" not in The_armature.pose.bone_groups:
            The_armature.pose.bone_groups.new(name="ToyRigGroups")
        The_armature.pose.bone_groups["ToyRigGroups"].color_set = toy_settings['FK_color']
        # create constraint for all control bone
        for bone_name in control_bones_name:
            The_armature.data.bones[bone_name].use_deform = False

            deform_bone_name = get_original_bone_name(bone_name)
            if bone_name.split('_', 1)[0] == "ToyCtl":
                deform_bone_pose = The_armature.pose.bones[deform_bone_name]
                deform_bone_data = The_armature.data.bones[deform_bone_name]

                bone_pose = The_armature.pose.bones[bone_name]
                bone_data = The_armature.data.bones[bone_name]
                bone_pose.custom_shape = ToyCtl_Shape
                bone_data.show_wire = True
                The_armature.data.bones.active = bone_data
                # set control bone copy the corresponding deform bone's transforms
                new_constraint = bone_pose.constraints.new("COPY_TRANSFORMS")
                new_constraint.name = constraints_name["Copy_Transforms"]
                bone_pose.constraints[constraints_name["Copy_Transforms"]].target = The_armature
                bone_pose.constraints[constraints_name["Copy_Transforms"]].subtarget = deform_bone_name
                bone_pose.constraints[constraints_name["Copy_Transforms"]].target_space = 'WORLD'
                bone_pose.constraints[constraints_name["Copy_Transforms"]].owner_space = 'WORLD'

                The_armature.data.bones.active = deform_bone_data
                # set corresponding deform bone's copy the empty transforms
                new_constraint = deform_bone_pose.constraints.new("COPY_TRANSFORMS")
                new_constraint.name = constraints_name["Copy_Transforms"]
                deform_bone_pose.constraints[constraints_name["Copy_Transforms"]].target = The_armature
                deform_bone_pose.constraints[constraints_name["Copy_Transforms"]].subtarget = ""
                deform_bone_pose.constraints[constraints_name["Copy_Transforms"]].target_space = 'WORLD'
                deform_bone_pose.constraints[constraints_name["Copy_Transforms"]].owner_space = 'WORLD'         
                # set corresponding deform bone's empty IK
                new_constraint = deform_bone_pose.constraints.new('IK')
                new_constraint.name = constraints_name['IK']
                deform_bone_pose.constraints[constraints_name['IK']].target = The_armature
                deform_bone_pose.constraints[constraints_name['IK']].subtarget = ""
                deform_bone_pose.constraints[constraints_name['IK']].pole_target = None

                deform_bone_pose.rotation_mode = 'XYZ'
                bone_pose.rotation_mode = 'XYZ'
                for i in range(3):
                    bone_pose.lock_location[i] = deform_bone_pose.lock_location[i]
                    bone_pose.lock_rotation[i] = deform_bone_pose.lock_rotation[i]
                    bone_pose.lock_scale[i] = deform_bone_pose.lock_scale[i]
                # set control bone's parent
                if deform_bone_pose.parent:
                    parent_bone_name = "ToyCtl_"+deform_bone_pose.parent.name 
                    bpy.ops.object.mode_set(mode='EDIT')
                    edit_bone_data = The_armature.data.edit_bones[bone_name]
                    parent_edit_bone_data = The_armature.data.edit_bones[parent_bone_name]
                    edit_bone_data.parent = parent_edit_bone_data
                    bpy.ops.object.mode_set(mode='POSE')

            else:
                # set the end IK control bone offset parent of the last control bone
                parent_bone_name = "ToyCtl_"+deform_bone_name                
                bone_pose = The_armature.pose.bones[bone_name]
                bone_data = The_armature.data.bones[bone_name]
                bone_pose.custom_shape = ToyCtl_Shape
                bone_data.show_wire = True
                bpy.ops.object.mode_set(mode='EDIT')
                edit_bone_data = The_armature.data.edit_bones[bone_name]
                parent_edit_bone_data = The_armature.data.edit_bones[parent_bone_name]
                edit_bone_data.parent = parent_edit_bone_data
                bpy.ops.object.mode_set(mode='POSE')

        for bone_name in pole_bones_name:
            The_armature.data.bones[bone_name].use_deform = False      
            control_bone_name = "ToyCtl_"+get_original_bone_name(bone_name)
            # set corresponding control bone offset parent of the pole bone
            bone_pose = The_armature.pose.bones[bone_name]
            bone_data = The_armature.data.bones[bone_name]
            bone_pose.custom_shape = ToyPole_Shape
            bone_data.show_wire = True
            bpy.ops.object.mode_set(mode='EDIT')
            edit_bone_data = The_armature.data.edit_bones[bone_name]
            control_edit_bone_data = The_armature.data.edit_bones[control_bone_name]
            edit_bone_data.parent = control_edit_bone_data
            bpy.ops.object.mode_set(mode='POSE')

        for i in range(32):
            The_armature.data.layers[i] = True
        bpy.ops.pose.select_all(action='DESELECT')
        # change deform bone's layer to layers[0]
        for bone_name in deform_bones_name:
            bone_data = The_armature.data.bones[bone_name]
            bone_data.select = True
        bpy.ops.pose.bone_layers(layers=(True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
        bpy.ops.pose.select_all(action='DESELECT')
        # change control bone's layer and pole bone's layer to layers[16]
        for bone_name in control_bones_name:
            bone_data = The_armature.data.bones[bone_name]
            bone_data.select = True
        for bone_name in pole_bones_name:
            bone_data = The_armature.data.bones[bone_name]
            bone_data.select = True
        bpy.ops.pose.bone_layers(layers=(False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
        # assign all control bone and pole bone to bone group just create and hide all control&&pole bones
        bpy.ops.pose.group_assign(type=The_armature.pose.bone_groups.active_index + 1)
        bpy.ops.pose.select_all(action='DESELECT')
        for bone_name in control_bones_name:
            bone_data = The_armature.data.bones[bone_name]
            bone_data.hide = True
        for bone_name in pole_bones_name:
            bone_data = The_armature.data.bones[bone_name]
            bone_data.hide = True

    def set_pole_position_normal(self, new_bone, bone):
        # set pole bone's position according to related deform bone's direction and deform bone's child direction, use Law of cosines
        bone_child = bone.children[0]
        new_bone.head = bone.head
        new_bone.tail = bone_child.tail
        
        a = 0
        v = [0] * 3
        for i in range(3):
            v[i] = pow(bone_child.tail[i] - bone.tail[i], 2)
        for i in range(3):
            a = a + v[i]
        a = pow(a, 0.5)

        b = bone.length

        c = 0
        v = [0] * 3
        for i in range(3):
            v[i] = pow(bone_child.tail[i] - bone.head[i], 2)
        for i in range(3):
            c = c + v[i]
        c = pow(c, 0.5)
        # if three point defined a Triangle not a line then
        if c != a + b:
            # b * cos(a) = ( b^2 + c^2 - a^2 ) / (2 * c) 
            new_length = ( pow(b, 2) + pow(c, 2) - pow(a, 2) ) / ( 2 * c)
            new_bone.length = new_length
            new_bone.head = new_bone.tail
            new_bone.tail = bone.tail
            # determine the distance between deform bone's tail and pole bone's head
            pole_offset = bone_child.length + b
            new_bone.length = new_bone.length + pole_offset
            new_bone.head = bone.tail
            old_tail = new_bone.tail.copy()
            # determine the length of pole
            pole_length = b
            new_bone.length = new_bone.length + pole_length
            new_bone.head = old_tail
        else:
            self.set_pole_position_unusual(new_bone, bone)

    def set_pole_position_unusual(self, new_bone, bone):
        # use on if deform bone's direction and deform bone's child direction is same or deform bone don't have child
        new_bone.head = bone.head
        new_bone.tail = bone.tail
        pole_offset = bone.length * 2
        new_bone.head[2] += pole_offset
        new_bone.tail[2] += pole_offset

    def adjust_controller(self, The_armature):
        used_armature = The_armature["ToyRig_"+The_armature.name]
        deform_bones_add_name = used_armature["deform_bones_add_name"]
        original_show_bones_name = used_armature["original_show_bones_name"]
        ik_show_bone_name = used_armature["ik_show_bone_name"]
        fk_show_bone_name = used_armature["fk_show_bone_name"]
        custom_settings = The_armature["Custom_"+The_armature.name]
        custom_bones_name = custom_settings["custom_bones_name"]
        vanish_bones_name = custom_settings["vanish_bones_name"]

        # make bone_name in vanish_bones_name vanish from show_bone_name_list, and make bone_name in custom_bones_name appear from show_bone_name_list
        show_bone_name_list = [deform_bones_add_name, ik_show_bone_name, fk_show_bone_name]
        for bone_name in vanish_bones_name:
            for show_bone_name in show_bone_name_list:
                if bone_name in show_bone_name:
                    del show_bone_name[bone_name]
            if "ToyCtl_" + bone_name in used_armature["selected_bones_name"]:
                del used_armature["selected_bones_name"][bone_name]
        for bone_name in custom_bones_name:
            if bone_name not in The_armature.data.bones:
                del custom_bones_name[bone_name]
                if bone_name in used_armature["selected_bones_name"]:
                    del used_armature["selected_bones_name"][bone_name]
            if bone_name not in deform_bones_add_name:
                for show_bone_name in show_bone_name_list:
                    show_bone_name[bone_name] = bone_name
        # make bone_name be uninstall from custom_bones_name vanish from show_bone_name_list, and make bone_name appear from vanish_bones_name appear from show_bone_name_list
        for bone_name in original_show_bones_name:
            if bone_name not in vanish_bones_name and bone_name not in deform_bones_add_name:
                for show_bone_name in show_bone_name_list:
                    show_bone_name[bone_name] = bone_name
        for bone_name in deform_bones_add_name:
            if bone_name not in custom_bones_name and bone_name not in original_show_bones_name:
                for show_bone_name in show_bone_name_list:
                    if bone_name in show_bone_name:
                        del show_bone_name[bone_name]
                if "ToyCtl_" + bone_name in used_armature["selected_bones_name"]:
                    del used_armature["selected_bones_name"][bone_name]
                             
        # move the custom controller to bone layer 16
        for i in range(32):
            The_armature.data.layers[i] = True
        bpy.ops.pose.select_all(action='DESELECT')
        for bone_name in custom_bones_name:
            bone_data = The_armature.data.bones[bone_name]
            bone_data.hide = False
            bone_data.select = True
        bpy.ops.pose.bone_layers(layers=(False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
        for bone_name in custom_bones_name:
            bone_data = The_armature.data.bones[bone_name]
            bone_data.select = False
            bone_data.hide = True
        # always will have one layer and must have one layer be showed,we want only layer 16 is show,so
        for i in range(31):
            The_armature.data.layers[i] = False
        The_armature.data.layers[16] = True
        The_armature.data.layers[31] = False     
            
class TOY_OT_off(bpy.types.Operator):
    bl_idname = "toy.off"
    bl_label = "TOY_OT_off"

    def execute(self, context):
        try:
            unregist_key()
            armature_name = context.object.name
            used_armature = context.object["ToyRig_"+armature_name]
            uninstall_all_controller(context)
            used_armature["is_use"] = False
            for mesh in bpy.data.objects[armature_name].children:
                mesh.hide_select = False
            display_all_deform_bones(context, display=True)
            bpy.ops.ed.undo_push(message="ToyRig_history_off")
        except Exception:
            self.report({'ERROR'}, traceback.format_exc())
            self.report({'ERROR'}, "Magic lose contol.....please tell Magician the message above.")
        return {'FINISHED'}

class TOY_OT_push(bpy.types.Operator):
    bl_idname = "toy.push"
    bl_label = "TOY_OT_push"

    def execute(self, context):
        try:
            install_custom_controller(context)
            bpy.ops.ed.undo_push(message="ToyRig_history_push")
            self.report({'INFO'}, "Install custom controller success.")
        except Exception:
            self.report({'ERROR'}, traceback.format_exc())
            self.report({'ERROR'}, "Magic lose contol.....please tell Magician the message above.")
        return {'FINISHED'}

class TOY_OT_pop(bpy.types.Operator):
    bl_idname = "toy.pop"
    bl_label = "TOY_OT_pop"

    def execute(self, context):
        try:
            uninstall_custom_controller(context)
            bpy.ops.ed.undo_push(message="ToyRig_history_pop")
            self.report({'INFO'}, "Uninstall custom controller success.")
        except Exception:
            self.report({'ERROR'}, traceback.format_exc())
            self.report({'ERROR'}, "Magic lose contol.....please tell Magician the message above.")
        return {'FINISHED'}

class TOY_OT_vanish(bpy.types.Operator):
    bl_idname = "toy.vanish"
    bl_label = "TOY_OT_vanish"

    def execute(self, context):
        try:
            vanish_bones_controller(context)
            bpy.ops.ed.undo_push(message="ToyRig_history_vanish")
            self.report({'INFO'}, "Vanish bone's controller success.")
        except Exception:
            self.report({'ERROR'}, traceback.format_exc())
            self.report({'ERROR'}, "Magic lose contol.....please tell Magician the message above.")
        return {'FINISHED'}

class TOY_OT_appear(bpy.types.Operator):
    bl_idname = "toy.appear"
    bl_label = "TOY_OT_appear"

    def execute(self, context):
        try:
            appear_bones_controller(context)
            bpy.ops.ed.undo_push(message="ToyRig_history_appear")
            self.report({'INFO'}, "Appear bone's controller success.")
        except Exception:
            self.report({'ERROR'}, traceback.format_exc())
            self.report({'ERROR'}, "Magic lose contol.....please tell Magician the message above.") 
        return {'FINISHED'}

class TOY_OT_stretch(bpy.types.Operator):
    bl_idname = "toy.stretch"
    bl_label = "TOY_OT_stretch"

    def execute(self, context):
        try:
            The_armature = context.object
            tmp_child_bones_name = []
            for bone in context.selected_pose_bones:
                The_armature.data.bones[bone.name].select = False
                if "ToyStretch_"+bone.name not in The_armature.pose.bones:
                    The_armature.data.bones[bone.name].select = True
                    if bone.child:
                        tmp_child_bones_name.append(bone.child.name)
            for child_bone_name in tmp_child_bones_name:
                The_armature.data.bones[child_bone_name].select = True    
            vanish_bones_controller(context)
            for child_bone_name in tmp_child_bones_name:
                The_armature.data.bones[child_bone_name].select = False
            for bone in context.selected_pose_bones:
                The_armature.data.bones[bone.name].select = False
                self.creat_stretch_controller(bone.name, context)
                set_stretch_controller("ToyStretch_"+bone.name,install=True)
                The_armature.data.bones["ToyStretch_"+bone.name].select = True
            install_custom_controller(context)
            bpy.ops.ed.undo_push(message="ToyRig_history_stretch")
            self.report({'INFO'}, "Install stretch controller success.")
        except Exception:
            self.report({'ERROR'}, traceback.format_exc())
            self.report({'ERROR'}, "Magic lose contol.....please tell Magician the message above.")
        return {'FINISHED'}

    def creat_stretch_controller(self, bone_name, context):
        The_armature = context.object
        if The_armature.pose.bones[bone_name].child:
            child_bone_name = The_armature.pose.bones[bone_name].child.name
        else:
            child_bone_name = ""
        bpy.ops.object.mode_set(mode='EDIT')
        bone = The_armature.data.edit_bones[bone_name]
        if child_bone_name:
            bone_child = The_armature.data.edit_bones[child_bone_name]
        else:
            bone_child = ""
        new_bone = The_armature.data.edit_bones.new("ToyStretch_"+bone_name)
        if bone_child:
            new_bone.head = bone_child.head
            new_bone.tail = bone_child.tail
        else:
            new_bone.head = bone.tail
            new_bone.tail = bone.tail
            for i in range(3):
                new_bone.tail[i] = new_bone.tail[i] + bone.vector[i]

        if "ToyStretchCtl_Shape" not in bpy.data.objects:
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.mesh.primitive_cone_add(radius1=0.5, radius2=0.25, depth=0.5, view_align=False, enter_editmode=False, location=(0, 0, 0), layers=(True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.transform.rotate(value=-1.5708, axis=(1, 0, 0), constraint_axis=(True, False, False), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)
            bpy.ops.mesh.delete(type='ONLY_FACE')
            bpy.ops.object.mode_set(mode='OBJECT')
            context.object.name = "ToyStretchCtl_Shape"
            ToyStretchCtl_Shape = context.object
            ToyStretchCtl_Shape.hide_render = True
            ToyStretchCtl_Shape.hide = True
            bpy.ops.object.select_all(action='DESELECT')
            context.scene.objects.active = The_armature
        bpy.ops.object.mode_set(mode='POSE')
        
class TOY_OT_stiff(bpy.types.Operator):
    bl_idname = "toy.stiff"
    bl_label = "TOY_OT_stiff"

    def execute(self, context):
        try:
            The_armature = context.object
            tmp_selected_bones_name = []
            tmp_child_bones_name = []
            for bone in context.selected_pose_bones:
                tmp_selected_bones_name.append(bone.name)
                if bone.child:
                    tmp_child_bones_name.append(bone.child.name)
            for bone_name in tmp_selected_bones_name:
                if "ToyStretch_"+bone_name in The_armature.pose.bones:
                    set_stretch_controller("ToyStretch_"+bone_name,install=False)
                    The_armature.data.bones["ToyStretch_"+bone_name].select = True
            for child_bone_name in tmp_child_bones_name:
                The_armature.data.bones[child_bone_name].select = True
            uninstall_custom_controller(context)
            appear_bones_controller(context)
            for bone_name in tmp_selected_bones_name:
                if "ToyStretch_"+bone_name in The_armature.pose.bones:
                    self.delete_stretch_controller("ToyStretch_"+bone_name, context)
            for bone_name in tmp_selected_bones_name:
                The_armature.data.bones[bone_name].select = True
            bpy.ops.ed.undo_push(message="ToyRig_history_stiff")
            self.report({'INFO'}, "Uninstall stretch controller success.")
        except Exception:
            self.report({'ERROR'}, traceback.format_exc())
            self.report({'ERROR'}, "Magic lose contol.....please tell Magician the message above.")
        return {'FINISHED'}

    def delete_stretch_controller(self, bone_name, context):
        The_armature = context.object
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.select_all(action='DESELECT')
        bone_data = The_armature.data.edit_bones[bone_name]
        bone_data.select = True
        bpy.ops.armature.delete()
        bpy.ops.object.mode_set(mode='POSE')    

class TOY_OT_play(bpy.types.Operator):
    bl_idname = "toy.play"
    bl_label = "TOY_OT_play"
    _timer = None
    last_click_time = time.time()

    def modal(self, context, event):
        try:
            if context.object and context.object.mode == "POSE":
                global select_with
                armature_name = context.object.name
                The_armature = context.object
                
                if "ToyRig_"+armature_name in The_armature:
                    used_armature = The_armature["ToyRig_"+armature_name]
                    if used_armature["is_use"] == False:
                        if addon_keymaps:
                            unregist_key()
                    else:
                        if not addon_keymaps:
                            regist_key()

                        elif event.type == select_with and event.value == 'PRESS':
                            region, r3d, x, y = mouse_in_3dview(context, event.mouse_x, event.mouse_y)
                            if region:
                                last_bone_name = used_armature["last_bone_name"]
                                fk_show_bone_name = used_armature["fk_show_bone_name"]
                                ik_show_bone_name = used_armature["ik_show_bone_name"]
                                fixed_fk_bones_name = used_armature["fixed_fk_bones_name"]
                                fk_bones_name = used_armature["fk_bones_name"]
                                fixed_ik_bones_name = used_armature["fixed_ik_bones_name"]
                                custom_settings = The_armature["Custom_"+The_armature.name]
                                custom_bones_name = custom_settings["custom_bones_name"]
                                rfk_bone_name = used_armature["rfk_bone_name"]
                                fix_show_bone_name = used_armature["fix_show_bone_name"]
                                is_fk = used_armature["is_fk"]
                                is_fixed = used_armature["is_fixed"]
                                is_lock = used_armature["is_lock"]
                                if is_fixed:
                                    show_bone_name = fix_show_bone_name
                                elif is_fk:
                                    show_bone_name = fk_show_bone_name
                                else:
                                    show_bone_name = ik_show_bone_name
                                #In lock mode double click: hide or show the deform bones
                                if is_lock:
                                    if 0.1 < time.time() - self.last_click_time < 0.25:
                                        if The_armature.data.layers[0]:
                                            display_all_deform_bones(context,display = False)
                                        else:
                                            display_all_deform_bones(context,display = True)
                                #In none-lock mode and none-fix mode double click: enable or disable the controller
                                elif 0.1 < time.time() - self.last_click_time < 0.25 and not is_fixed:
                                    distance = []
                                    distance_bone_name = []
                                    deform_bones_add_name = used_armature["deform_bones_add_name"]
                                    # find the deform bone that most close to mouse location
                                    for bone_name in deform_bones_add_name:
                                        bone_pose = The_armature.pose.bones[bone_name]        
                                        loc = [0]*3
                                        if bone_name.split('_', 1)[0] == "ToyCtlEnd":
                                            bone_pose = The_armature.pose.bones[get_original_bone_name(bone_name)]
                                            for i in range(3):
                                                loc[i] = bone_pose.tail[i]
                                        else:
                                            bone_pose = The_armature.pose.bones[bone_name]    
                                            for i in range(3):
                                                loc[i] = (bone_pose.head[i] + bone_pose.tail[i]) / 2
                                        loc_2d = location_3d_to_region_2d(region,r3d,loc)
                                        if loc_2d:
                                            distance.append( pow((x-loc_2d.x),2) + pow((y-loc_2d.y),2) )
                                            distance_bone_name.append(bone_name)
                                    closest_bone_name = distance_bone_name[distance.index(min(distance))]

                                    if closest_bone_name in custom_bones_name:
                                        closest_control_bone_name = closest_bone_name
                                        bone_data = The_armature.data.bones[closest_control_bone_name]
                                        # disable custom controller
                                        if closest_bone_name in show_bone_name:
                                            del show_bone_name[closest_bone_name]
                                            bone_data.select = False
                                            bone_data.hide = True
                                        # enable custom controller
                                        else:
                                            show_bone_name[closest_bone_name] = closest_bone_name
                                            for bone in context.selected_pose_bones:
                                                The_armature.data.bones[bone.name].select = False
                                                if bone.name in custom_bones_name:
                                                    The_armature.data.bones[bone.name].hide = True
                                            bone_data.hide = False
                                            The_armature.data.bones.active = bone_data
                                            bone_data.select = True                                    
                                    elif is_fk:
                                        if closest_bone_name.split('_', 1)[0] == "ToyCtlEnd":
                                            closest_control_bone_name = closest_bone_name
                                        else:
                                            closest_control_bone_name = "ToyCtl_"+closest_bone_name
                                        bone_data = The_armature.data.bones[closest_control_bone_name]  
                                        # disable fk controller
                                        if closest_bone_name in fk_show_bone_name:
                                            del fk_show_bone_name[closest_bone_name]
                                            set_fkc_controller(bone_name = closest_control_bone_name, install = False)
                                            if closest_control_bone_name in fk_bones_name:
                                                set_fk_controller(bone_name = closest_control_bone_name, install = False)
                                            if closest_control_bone_name in fixed_fk_bones_name:
                                                del fixed_fk_bones_name[closest_control_bone_name]
                                            bone_data.select = False
                                            bone_data.hide = True
                                            used_armature["last_bone_name"] = ""
                                        # enable fk controller
                                        else:
                                            fk_show_bone_name[closest_bone_name] = closest_bone_name
                                            for bone_name in fk_bones_name:
                                                set_fk_controller(bone_name = bone_name, install = False)
                                                The_armature.data.bones[bone_name].select = False
                                                if bone_name not in fixed_fk_bones_name:
                                                    The_armature.data.bones[bone_name].hide = True
                                            bone_data.hide = False
                                            The_armature.data.bones.active = bone_data
                                            bone_data.select = True
                                            set_fkc_controller(bone_name = closest_control_bone_name, install = True)
                                            set_fk_controller(bone_name = closest_control_bone_name, install = True)
                                            used_armature["last_bone_name"] = closest_control_bone_name
                                    else:
                                        if closest_bone_name.split('_', 1)[0] == "ToyCtlEnd":
                                            ik_control_bone_name = closest_bone_name
                                        else:
                                            ik_control_bone_name = "ToyCtl_"+closest_bone_name
                                        bone_data = The_armature.data.bones[ik_control_bone_name]
                                        # disable ik controller
                                        if closest_bone_name in ik_show_bone_name:
                                            del ik_show_bone_name[closest_bone_name]
                                            set_ik_controller(bone_name = ik_control_bone_name, install = False)
                                            if ik_control_bone_name in fixed_ik_bones_name:
                                                del fixed_ik_bones_name[ik_control_bone_name]
                                            bone_data = The_armature.data.bones[ik_control_bone_name]
                                            bone_data.select = False
                                            bone_data.hide = True
                                            used_armature["last_bone_name"] = ""
                                        # enable ik controller
                                        else:
                                            ik_show_bone_name[closest_bone_name] = closest_bone_name
                                            for bone in context.selected_pose_bones:
                                                The_armature.data.bones[bone.name].select = False
                                            bone_data.hide = False
                                            The_armature.data.bones.active = bone_data
                                            bone_data.select = True
                                            # hide and uninstall the last bone if is not in fixed_ik_bones_name list
                                            if last_bone_name and last_bone_name not in fixed_ik_bones_name:
                                                set_ik_controller(bone_name = last_bone_name, install = False)
                                                The_armature.data.bones[last_bone_name].select = False
                                                The_armature.data.bones[last_bone_name].hide = True
                                            set_ik_controller(bone_name = ik_control_bone_name, install = True)
                                            used_armature["last_bone_name"] = ik_control_bone_name
                                # when single click,according to actual condition to set IK/FK controller in real time        
                                else:
                                    # find the conntrol bone that can select and most close to mouse location
                                    distance = []
                                    distance_bone_name = []
                                    for bone_name in show_bone_name:
                                        loc = [0]*3  
                                        if bone_name.split('_', 1)[0] == "ToyCtlEnd":
                                            bone_pose = The_armature.pose.bones[get_original_bone_name(bone_name)]
                                            for i in range(3):
                                                loc[i] = bone_pose.tail[i]
                                        else:
                                            bone_pose = The_armature.pose.bones[bone_name]
                                            for i in range(3):
                                                loc[i] = (bone_pose.head[i] + bone_pose.tail[i]) / 2                                  
                                        loc_2d = location_3d_to_region_2d(region,r3d,loc)
                                        if loc_2d:
                                            distance.append( pow((x-loc_2d.x),2) + pow((y-loc_2d.y),2) )
                                            distance_bone_name.append(bone_name)
                                    closest_bone_name = distance_bone_name[distance.index(min(distance))]
                                    # when custom controller is be selected
                                    if closest_bone_name in custom_bones_name:
                                        closest_control_bone_name = closest_bone_name
                                        bone_data = The_armature.data.bones[closest_control_bone_name]
                                        if event.ctrl:
                                            bone_data.select = False
                                            bone_data.hide = True                                
                                        elif event.shift:
                                            bone_data.hide = False
                                            if The_armature.data.bones.active.name != closest_control_bone_name:
                                                The_armature.data.bones.active = bone_data
                                                bone_data.select = True
                                            else:
                                                if bone_data.select:
                                                    bone_data.select = False
                                                else:
                                                    bone_data.select = True
                                        else:                            
                                            for bone in context.selected_pose_bones:
                                                The_armature.data.bones[bone.name].select = False
                                                if bone.name in custom_bones_name:
                                                    The_armature.data.bones[bone.name].hide = True
                                            bone_data.hide = False
                                            The_armature.data.bones.active = bone_data
                                            bone_data.select = True
                                    # when is in fix mode
                                    elif is_fixed:
                                        if closest_bone_name.split('_', 1)[0] == "ToyCtlEnd":
                                            closest_control_bone_name = closest_bone_name
                                        else:
                                            closest_control_bone_name = "ToyCtl_"+closest_bone_name
                                        pos_stay_still(The_armature, closest_bone_name, closest_control_bone_name)

                                        bone_data = The_armature.data.bones[closest_control_bone_name]
                                        if event.ctrl:
                                            if closest_control_bone_name in fk_bones_name:
                                                set_fk_controller(bone_name = closest_control_bone_name, install = False)
                                            bone_data.select = False
                                            bone_data.hide = True
                                        elif event.shift:
                                            bone_data.hide = False
                                            if The_armature.data.bones.active.name != closest_control_bone_name:
                                                The_armature.data.bones.active = bone_data
                                                bone_data.select = True
                                                if closest_control_bone_name not in fk_bones_name:
                                                    set_fk_controller(bone_name = closest_control_bone_name, install = True)
                                            elif bone_data.select:
                                                bone_data.select = False
                                                if closest_control_bone_name in fk_bones_name:
                                                    set_fk_controller(bone_name = closest_control_bone_name, install = False)
                                            else:
                                                bone_data.select = True
                                                if closest_control_bone_name not in fk_bones_name:
                                                    set_fk_controller(bone_name = closest_control_bone_name, install = True)
                                        else:                            
                                            # hide and uninstall the other fk controller
                                            tmp_bones_name = []
                                            if closest_control_bone_name in fk_bones_name:
                                                del fk_bones_name[closest_control_bone_name]
                                                tmp_bones_name.append(closest_control_bone_name)
                                            for bone in context.selected_pose_bones:
                                                The_armature.data.bones[bone.name].select = False
                                            for bone_name in fk_bones_name:
                                                if get_original_bone_name(bone_name) in fix_show_bone_name:
                                                    set_fk_controller(bone_name = bone_name, install = False)
                                                    The_armature.data.bones[bone_name].hide = True
                                            for bone_name in tmp_bones_name:
                                                fk_bones_name[bone_name] = bone_name
                                            # unhide and activation the closest bone
                                            bone_data.hide = False
                                            The_armature.data.bones.active = bone_data
                                            bone_data.select = True
                                            # make closest bone become the fk controller
                                            if closest_control_bone_name not in fk_bones_name:
                                                set_fk_controller(bone_name = closest_control_bone_name, install = True)
                                    # when is in fk mode
                                    elif is_fk:
                                        if closest_bone_name.split('_', 1)[0] == "ToyCtlEnd":
                                            closest_control_bone_name = closest_bone_name
                                        else:
                                            closest_control_bone_name = "ToyCtl_"+closest_bone_name                            
                                        pos_stay_still(The_armature, closest_bone_name, closest_control_bone_name)

                                        bone_data = The_armature.data.bones[closest_control_bone_name]
                                        if event.ctrl:
                                            # hide and uninstall the controller that be CTRL selected
                                            if closest_control_bone_name in fk_bones_name:
                                                set_fk_controller(bone_name = closest_control_bone_name, install = False)
                                            if closest_control_bone_name in fixed_fk_bones_name:
                                                del fixed_fk_bones_name[closest_control_bone_name]
                                            set_fkc_controller(bone_name = closest_control_bone_name, install = False)
                                            bone_data.select = False
                                            bone_data.hide = True
                                            if closest_control_bone_name == last_bone_name:
                                                used_armature["last_bone_name"] = ""
                                        elif event.shift:
                                            # unhide the closest controller, and make it become the fixed fk bone, and install it be fkc controller, when it be select it will become fk controller
                                            bone_data.hide = False
                                            if closest_control_bone_name not in fixed_fk_bones_name:
                                                fixed_fk_bones_name[closest_control_bone_name] = closest_control_bone_name
                                                if closest_control_bone_name != last_bone_name:
                                                    if last_bone_name and last_bone_name not in fixed_fk_bones_name:
                                                        fixed_fk_bones_name[last_bone_name] = last_bone_name
                                                    set_fkc_controller(bone_name = closest_control_bone_name, install = True)
                                            else: 
                                                if The_armature.data.bones.active.name != closest_control_bone_name:
                                                    The_armature.data.bones.active = bone_data
                                                    bone_data.select = True
                                                    if closest_control_bone_name not in fk_bones_name:
                                                        set_fk_controller(bone_name = closest_control_bone_name, install = True)
                                                elif bone_data.select:
                                                    bone_data.select = False
                                                    if closest_control_bone_name in fk_bones_name:
                                                        set_fk_controller(bone_name = closest_control_bone_name, install = False)
                                                else:
                                                    bone_data.select = True
                                                    if closest_control_bone_name not in fk_bones_name:
                                                        set_fk_controller(bone_name = closest_control_bone_name, install = True)
                                            used_armature["last_bone_name"] = closest_control_bone_name
                                        else:
                                            # hide and uninstall the other fk controller
                                            tmp_bones_name = []
                                            if closest_control_bone_name in fk_bones_name:
                                                del fk_bones_name[closest_control_bone_name]
                                                tmp_bones_name.append(closest_control_bone_name)
                                            for bone in context.selected_pose_bones:
                                                The_armature.data.bones[bone.name].select = False
                                            for bone_name in fk_bones_name:
                                                set_fk_controller(bone_name = bone_name, install = False)
                                                if bone_name not in fixed_fk_bones_name:
                                                    The_armature.data.bones[bone_name].hide = True
                                            for bone_name in tmp_bones_name:
                                                fk_bones_name[bone_name] = bone_name
                                            # unhide and activation the closest bone
                                            bone_data.hide = False
                                            The_armature.data.bones.active = bone_data
                                            bone_data.select = True

                                            if closest_control_bone_name != last_bone_name:
                                                if last_bone_name and last_bone_name not in fixed_fk_bones_name:
                                                    set_fkc_controller(bone_name = last_bone_name, install = False)
                                                    The_armature.data.bones[last_bone_name].hide = True
                                                if closest_control_bone_name not in fixed_fk_bones_name:
                                                    set_fkc_controller(bone_name = closest_control_bone_name, install = True)
                                            # make closest bone become the fk controller
                                            if closest_control_bone_name not in fk_bones_name:
                                                set_fk_controller(bone_name = closest_control_bone_name, install = True)
                                            used_armature["last_bone_name"] = closest_control_bone_name
                                    # when is in ik mode
                                    else:
                                        # when pole controller is be selected
                                        if closest_bone_name.split('_', 1)[0] == "ToyPole":
                                            bone_data = The_armature.data.bones[closest_bone_name]
                                            if event.shift:
                                                if The_armature.data.bones.active.name != closest_bone_name:
                                                    The_armature.data.bones.active = bone_data
                                                    bone_data.select = True
                                                else:
                                                    if bone_data.select:
                                                        bone_data.select = False
                                                    else:
                                                        bone_data.select = True
                                            else:
                                                for bone in context.selected_pose_bones:
                                                    The_armature.data.bones[bone.name].select = False
                                                bone_data.select = True
                                        # when none-pole controller is be selected, according to the way user click, install or uninstall the IK controller to bone be selected
                                        else:
                                            if closest_bone_name.split('_', 1)[0] == "ToyCtlEnd":
                                                ik_control_bone_name = closest_bone_name
                                            else:
                                                ik_control_bone_name = "ToyCtl_"+closest_bone_name

                                            if rfk_bone_name and ( ik_control_bone_name not in rfk_bone_name.values() or event.ctrl ):
                                                set_rfk(context,install=False)
                                            bone_data = The_armature.data.bones[ik_control_bone_name]
                                            if event.shift:
                                                # unhide the closest controller, and make it become the fixed ik bone, and install it be IK controller
                                                bone_data.hide = False
                                                if ik_control_bone_name not in fixed_ik_bones_name:
                                                    fixed_ik_bones_name[ik_control_bone_name] = ik_control_bone_name
                                                    if ik_control_bone_name != last_bone_name:
                                                        if last_bone_name and last_bone_name not in fixed_ik_bones_name:
                                                            fixed_ik_bones_name[last_bone_name] = last_bone_name
                                                        set_ik_controller(bone_name = ik_control_bone_name, install = True)
                                                else: 
                                                    if The_armature.data.bones.active.name != ik_control_bone_name:
                                                        The_armature.data.bones.active = bone_data
                                                        bone_data.select = True
                                                    else:
                                                        if bone_data.select:
                                                            bone_data.select = False
                                                        else:
                                                            bone_data.select = True
                                                    used_armature["last_bone_name"] = ik_control_bone_name                    
                                            elif event.ctrl:
                                                # hide and uninstall the controller that be CTRL selected
                                                if ik_control_bone_name in fixed_ik_bones_name:
                                                    del fixed_ik_bones_name[ik_control_bone_name]
                                                set_ik_controller(bone_name = ik_control_bone_name, install = False)
                                                bone_data = The_armature.data.bones[ik_control_bone_name]
                                                bone_data.select = False
                                                bone_data.hide = True
                                                if ik_control_bone_name == last_bone_name:
                                                    used_armature["last_bone_name"] = ""
                                            else:
                                                for bone in context.selected_pose_bones:
                                                    The_armature.data.bones[bone.name].select = False
                                                # unhide and activation the closest bone
                                                bone_data.hide = False
                                                The_armature.data.bones.active = bone_data
                                                bone_data.select = True
                                                if ik_control_bone_name != last_bone_name:
                                                    # hide and uninstall the last bone if is not in fixed_ik_bones_name list
                                                    if last_bone_name and last_bone_name not in fixed_ik_bones_name:
                                                        set_ik_controller(bone_name = last_bone_name, install = False)
                                                        The_armature.data.bones[last_bone_name].select = False
                                                        The_armature.data.bones[last_bone_name].hide = True                     
                                                    if ik_control_bone_name not in fixed_ik_bones_name:
                                                        # make closest ik control bone become the ik controller                    
                                                        set_ik_controller(bone_name = ik_control_bone_name, install = True)
                                                used_armature["last_bone_name"] = ik_control_bone_name
                                self.last_click_time = time.time()
                                bpy.ops.ed.undo_push(message="ToyRig_history_play")
                        else:
                            # force update drives dependencies of fkc bones when it be selected
                            is_fk = used_armature["is_fk"]
                            if is_fk and The_armature.animation_data:
                                exist_fkc_info = used_armature["exist_fkc_info"]
                                for bone in context.selected_pose_bones:
                                    if bone.name+"_end" in exist_fkc_info:
                                        for d in The_armature.animation_data.drivers:
                                            if d.data_path.startswith('pose.bones') and d.data_path.rsplit('.', 1)[1] == 'rotation_euler':
                                                d.driver.expression += " "
                                                d.driver.expression = d.driver.expression[:-1]
                                        break                                    

        except Exception:
            self.report({'ERROR'}, traceback.format_exc())
            self.report({'ERROR'}, "Magic lose contol.....please tell Magician the message above.")
        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

class TOY_OT_switch(bpy.types.Operator):
    bl_idname = "toy.switch"
    bl_label = "TOY_OT_switch"

    def execute(self, context):
        try:
            used_armature = context.object["ToyRig_"+context.object.name]
            is_lock = used_armature["is_lock"]
            if not is_lock:
                is_fk = used_armature["is_fk"]
                is_fixed = used_armature["is_fixed"]
                if is_fixed:
                    if context.space_data.transform_manipulators == {'ROTATE'}:
                        context.space_data.transform_manipulators = {'TRANSLATE'}
                    elif context.space_data.transform_manipulators == {'TRANSLATE'}:
                        context.space_data.transform_manipulators = {'ROTATE'}
                elif is_fk:
                    context.space_data.transform_manipulators = {'TRANSLATE'}
                    set_ik_var(context)
                    fk_to_ik(context)
                else :
                    is_rfk = used_armature["is_rfk"]
                    if need_rfk(context):
                        if is_rfk:
                            set_rfk(context,install=False)
                        else:
                            set_rfk(context,install=True)
                    else:
                        if is_rfk:
                            set_rfk(context,install=False)
                        context.space_data.transform_manipulators = {'ROTATE'}
                        set_fk_var(context)
                        ik_to_fk(context)
                bpy.ops.ed.undo_push(message="ToyRig_history_switch")
        except Exception:
            self.report({'ERROR'}, traceback.format_exc())
            self.report({'ERROR'}, "Magic lose contol.....please tell Magician the message above.")
        return {'FINISHED'}

class TOY_OT_ik(bpy.types.Operator):
    bl_idname = "toy.ik"
    bl_label = "TOY_OT_ik"

    def execute(self, context):
        # change to the IK mode
        try:
            used_armature = context.object["ToyRig_"+context.object.name]
            is_lock = used_armature["is_lock"]
            if not is_lock:
                is_fk = used_armature["is_fk"]
                is_rfk = used_armature["is_rfk"]
                is_fixed = used_armature["is_fixed"]
                if is_fk and not is_fixed:
                    set_ik_var(context)
                    fk_to_ik(context)
                elif is_rfk:
                    set_rfk(context,install=False)
            context.space_data.transform_manipulators = {'TRANSLATE'}
            bpy.ops.transform.translate('INVOKE_DEFAULT')
        except Exception:
            self.report({'ERROR'}, traceback.format_exc())
            self.report({'ERROR'}, "Magic lose contol.....please tell Magician the message above.")
        return {'FINISHED'}
        
class TOY_OT_fk(bpy.types.Operator):
    bl_idname = "toy.fk"
    bl_label = "TOY_OT_fk"

    def execute(self, context):
        # change to the FK mode
        try:
            used_armature = context.object["ToyRig_"+context.object.name]
            is_lock = used_armature["is_lock"]
            if not is_lock:
                is_fk = used_armature["is_fk"]
                if not is_fk:
                    is_rfk = used_armature["is_rfk"]
                    if need_rfk(context):
                        if not is_rfk:
                            set_rfk(context,install=True)
                    else:
                        if is_rfk:
                            set_rfk(context,install=False)
                        is_fixed = used_armature["is_fixed"]
                        if not is_fixed:
                            set_fk_var(context)
                            ik_to_fk(context)
            context.space_data.transform_manipulators = {'ROTATE'}        
            bpy.ops.transform.rotate('INVOKE_DEFAULT')
        except Exception:
            self.report({'ERROR'}, traceback.format_exc())
            self.report({'ERROR'}, "Magic lose contol.....please tell Magician the message above.")
        return {'FINISHED'}

class TOY_OT_follow(bpy.types.Operator):
    bl_idname = "toy.follow"
    bl_label = "TOY_OT_follow"

    def execute(self, context):
        try:
            The_armature = context.object
            used_armature = The_armature["ToyRig_"+The_armature.name]
            exist_ik_info = used_armature["exist_ik_info"]
            is_fk = used_armature["is_fk"]
            ik_follow = used_armature["ik_follow"]
            if not is_fk:
                for bone in context.selected_pose_bones:
                    # if controller be select is IK controller,then make selected controller's relevant deform bone switch follow to it
                    if bone.name+"_begin" in exist_ik_info:
                        if bone.name in ik_follow:
                            del ik_follow[bone.name]
                            set_fk_controller(bone.name, install = False)
                            bone_pose_pos = bone.matrix.copy()
                            bone.constraints[constraints_name["Copy_Transforms"]].subtarget = ""
                            bone.matrix = bone_pose_pos
                        elif bone.name.split('_', 1)[0] == "ToyCtl" and The_armature.data.bones[get_original_bone_name(bone.name)].use_connect:
                            ik_follow[bone.name] = bone.name
                            recover_ik(The_armature, bone.name, get_original_bone_name(bone.name), with_pole=True)
                            set_fk_controller(bone.name, install = True)
                    # if controller be select is pole controller,then make selected controller switch follow to it's relevant IK controller 
                    elif bone.name.split('_', 1)[0] == "ToyPole" and "ToyCtl_"+get_original_bone_name(bone.name)+"_end" in exist_ik_info:
                        if bone.name in ik_follow:
                            del ik_follow[bone.name]
                            ik_begin_bone_name = exist_ik_info["ToyCtl_"+get_original_bone_name(bone.name)+"_end"]["opposite"]
                            pole_bone_pose_pos = bone.matrix.copy()
                            bpy.ops.object.mode_set(mode='EDIT')
                            edit_bone_data = The_armature.data.edit_bones[bone.name]
                            parent_edit_bone_data = The_armature.data.edit_bones[ik_begin_bone_name]
                            edit_bone_data.parent = parent_edit_bone_data
                            bpy.ops.object.mode_set(mode='POSE')
                            bone.matrix = pole_bone_pose_pos             
                        else:
                            ik_follow[bone.name] = bone.name
                            pole_bone_pose_pos = bone.matrix.copy()
                            bpy.ops.object.mode_set(mode='EDIT')
                            edit_bone_data = The_armature.data.edit_bones[bone.name]
                            edit_bone_data.parent = None
                            bpy.ops.object.mode_set(mode='POSE')
                            bone.matrix = pole_bone_pose_pos

                bpy.ops.ed.undo_push(message="ToyRig_history_follow")
        except Exception:
            self.report({'ERROR'}, traceback.format_exc())
            self.report({'ERROR'}, "Magic lose contol.....please tell Magician the message above.")
        return {'FINISHED'}

class TOY_OT_fix(bpy.types.Operator):
    bl_idname = "toy.fix"
    bl_label = "TOY_OT_fix"

    def execute(self, context):
        # entry or quit the fix mode
        try:
            The_armature = context.object
            used_armature = The_armature["ToyRig_"+The_armature.name]
            fixed_ik_bones_name = used_armature["fixed_ik_bones_name"]
            fixed_fk_bones_name = used_armature["fixed_fk_bones_name"]
            exist_ik_info = used_armature["exist_ik_info"]
            exist_fkc_info = used_armature["exist_fkc_info"]
            last_bone_name = used_armature["last_bone_name"]
            if used_armature["is_fixed"]:
                is_fk = used_armature["is_fk"]
                uninstall_fk_in_fix(context)
                if not is_fk:
                    The_armature.pose.bone_groups["ToyRigGroups"].color_set = toy_settings['IK_color']
                    context.space_data.transform_manipulators = {'TRANSLATE'}
                else:
                    The_armature.pose.bone_groups["ToyRigGroups"].color_set = toy_settings['FK_color']
                    context.space_data.transform_manipulators = {'ROTATE'}
                used_armature["is_fixed"] = False
            else:
                if last_bone_name:
                    is_fk = used_armature["is_fk"]
                    if is_fk:
                        if last_bone_name + "_begin" in exist_fkc_info or last_bone_name + "_end" in exist_fkc_info:
                            if last_bone_name not in fixed_fk_bones_name:
                                fixed_fk_bones_name[last_bone_name] = last_bone_name
                        else:
                            set_fk_controller(last_bone_name, install = True)
                    else:
                        if last_bone_name + "_begin" in exist_ik_info or last_bone_name + "_end" in exist_ik_info:
                            if last_bone_name not in fixed_ik_bones_name:
                                fixed_ik_bones_name[last_bone_name] = last_bone_name
                        else:
                            set_fk_controller(last_bone_name, install = True)
                The_armature.pose.bone_groups["ToyRigGroups"].color_set = toy_settings['Fix_color']
                set_fix_show_bone_name(context)
                used_armature["is_fixed"] = True
            bpy.ops.ed.undo_push(message="ToyRig_history_fix")
        except Exception:
            self.report({'ERROR'}, traceback.format_exc())
            self.report({'ERROR'}, "Magic lose contol.....please tell Magician the message above.")
        return {'FINISHED'}

class TOY_OT_lock(bpy.types.Operator):
    bl_idname = "toy.lock"
    bl_label = "TOY_OT_lock"
    def execute(self, context):
        # entry or quit the lock mode, in lock mode no controller can be selected
        try:
            lock_switch(context)
            bpy.ops.ed.undo_push(message="ToyRig_history_lock")
        except Exception:
            self.report({'ERROR'}, traceback.format_exc())
            self.report({'ERROR'}, "Magic lose contol.....please tell Magician the message above.")
        return {'FINISHED'} 

class TOY_OT_key(bpy.types.Operator):
    bl_idname = "toy.key"
    bl_label = "TOY_OT_key"
    def execute(self, context):
        # set the Keyframe to every deform bone
        try:
            set_keyframe(context)
            bpy.ops.ed.undo_push(message="ToyRig_history_key")
            self.report({'INFO'}, "Key set success.")
        except Exception:
            self.report({'ERROR'}, traceback.format_exc())
            self.report({'ERROR'}, "Magic lose contol.....please tell Magician the message above.")
        return {'FINISHED'}

class TOY_OT_bake(bpy.types.Operator):
    bl_idname = "toy.bake"
    bl_label = "TOY_OT_bake"
    def execute(self, context): 
        # bake the Keyframe from current frame to the previous keyframe by follow the action of the controller
        try:
            The_armature = context.object
            used_armature = The_armature["ToyRig_"+The_armature.name]
            is_fk = used_armature["is_fk"]
            if not is_fk:
                now_keyframe = context.scene.frame_current
                previous_keyframe = self.get_previous_keyframe(The_armature, now_keyframe)
                if previous_keyframe == "previous_empty":
                    self.report({'WARNING'}, "Key bake fail! controller has no previous keyframe!")
                elif previous_keyframe == "next_empty":
                    self.report({'WARNING'}, "Key bake fail! controller has no next keyframe!")
                else:
                    for f in range(previous_keyframe, now_keyframe + 1):
                        context.scene.frame_set(f)
                        set_keyframe(context)
                    bpy.ops.ed.undo_push(message="ToyRig_history_bake")
                    self.report({'INFO'}, "Key bake success.")
        except Exception:
            self.report({'ERROR'}, traceback.format_exc())
            self.report({'ERROR'}, "Magic lose contol.....please tell Magician the message above.")
        return {'FINISHED'}

    def get_previous_keyframe(self, The_armature, now_keyframe):
        # get the controller bone's previous keyframe number
        used_armature = The_armature["ToyRig_"+The_armature.name]
        control_bones_name = used_armature["control_bones_name"]
        pole_bones_name = used_armature["pole_bones_name"]
        previous_keyframe = "previous_empty"
        have_next = False
        for fcurve in The_armature.animation_data.action.fcurves:
            bone_name = fcurve.data_path.split('"', 2)[1]
            if bone_name in control_bones_name or bone_name in pole_bones_name:
                keyframePoints = fcurve.keyframe_points
                for keyframe in keyframePoints:
                    test_keyframe = int(keyframe.co[0])                   
                    if test_keyframe >= now_keyframe:
                        have_next = True
                        break
                    elif previous_keyframe == "previous_empty" or test_keyframe > previous_keyframe:
                        previous_keyframe = test_keyframe           
        if not have_next:
            previous_keyframe = "next_empty"
        return previous_keyframe

class TOY_OT_clean(bpy.types.Operator):
    bl_idname = "toy.clean"
    bl_label = "TOY_OT_clean"
    def execute(self, context):
        # delete all controller, constraints and all info that ToyRig create for this armature
        try:
            The_armature = context.object
            self.delete_controller(The_armature)
            del The_armature["ToyRig_"+The_armature.name]
            del The_armature["Custom_"+The_armature.name]
            bpy.ops.ed.undo_push(message="ToyRig_history_clean")
            self.report({'INFO'}, "clean is success.")
        except Exception:
            self.report({'ERROR'}, traceback.format_exc())
            self.report({'ERROR'}, "Magic lose contol.....please tell Magician the message above.")
        return {'FINISHED'}

    def delete_controller(self,The_armature):
        used_armature = The_armature["ToyRig_"+The_armature.name]
        deform_bones_name = used_armature["deform_bones_name"]
        control_bones_name = used_armature["control_bones_name"]
        pole_bones_name = used_armature["pole_bones_name"]      
        # delete all constraints that deform bones use in this tool        
        for bone_name in deform_bones_name:
            if bone_name in The_armature.pose.bones:
                bone_pose = The_armature.pose.bones[bone_name]
                for constraint in bone_pose.constraints:
                    for constraint_type in constraints_name:
                        if constraint.name == constraints_name[constraint_type]:
                            bone_pose.constraints.remove(constraint)
                            break

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.select_all(action='DESELECT')
        # delete all control bone and all pole bone
        for bone_name in control_bones_name:
            if bone_name in The_armature.data.edit_bones:
                bone_data = The_armature.data.edit_bones[bone_name]
                bone_data.select = True
        for bone_name in pole_bones_name:
            if bone_name in The_armature.data.edit_bones:
                bone_data = The_armature.data.edit_bones[bone_name]
                bone_data.select = True
        bpy.ops.armature.delete()
        bpy.ops.object.mode_set(mode='POSE')

# ------------------------------------------------------------------------
#   register and unregister
# ------------------------------------------------------------------------

classes = (
    TOY_PT_panel,
    TOY_OT_empty,
    TOY_OT_mouse,
    TOY_OT_on,
    TOY_OT_off,
    TOY_OT_push,
    TOY_OT_pop,
    TOY_OT_vanish,
    TOY_OT_appear,
    TOY_OT_stretch,
    TOY_OT_stiff,
    TOY_OT_play,
    TOY_OT_switch,
    TOY_OT_ik,
    TOY_OT_fk,
    TOY_OT_follow,
    TOY_OT_fix,
    TOY_OT_lock,
    TOY_OT_key,
    TOY_OT_bake,
    TOY_OT_clean,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    