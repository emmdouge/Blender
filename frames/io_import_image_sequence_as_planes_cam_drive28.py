# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Import Image Sequence",
    "author": "Vicente Carro, Florian Meyer (tstscr), mont29, matali",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "File > Import > Images as Anim Planes or Add > Mesh > Image sequence as planes",
    "description": "Imports image sequence and creates planes with the appropriate aspect ratio. "
                   "The images are mapped to the planes.",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Add_Mesh/Planes_from_Images",
    "tracker_url": "https://projects.blender.org/tracker/index.php?func=detail&aid=21751",
    "category": "Import-Export"}

import bpy
from bpy.types import Operator
import mathutils
from mathutils import Vector
import os
import collections
import pprint
from math import pi, sqrt
import re
from itertools import count, repeat
from collections import namedtuple

from bpy.props import (StringProperty,
                       BoolProperty,
                       EnumProperty,
                       IntProperty,
                       FloatProperty,
                       CollectionProperty,
                       )

from bpy_extras.object_utils import AddObjectHelper, object_data_add, world_to_camera_view
from bpy_extras.image_utils import load_image

# -----------------------------------------------------------------------------
# Global Vars

DEFAULT_EXT = "*"

EXT_FILTER = getattr(collections, "OrderedDict", dict)((
    (DEFAULT_EXT, ((), "All image formats", "Import all known image (or movie) formats.")),
    ("jpeg", (("jpeg", "jpg", "jpe"), "JPEG ({})", "Joint Photographic Experts Group")),
    ("png", (("png", ), "PNG ({})", "Portable Network Graphics")),
    ("tga", (("tga", "tpic"), "Truevision TGA ({})", "")),
    ("tiff", (("tiff", "tif"), "TIFF ({})", "Tagged Image File Format")),
    ("bmp", (("bmp", "dib"), "BMP ({})", "Windows Bitmap")),
    ("cin", (("cin", ), "CIN ({})", "")),
    ("dpx", (("dpx", ), "DPX ({})", "DPX (Digital Picture Exchange)")),
    ("psd", (("psd", ), "PSD ({})", "Photoshop Document")),
    ("exr", (("exr", ), "OpenEXR ({})", "OpenEXR HDR imaging image file format")),
    ("hdr", (("hdr", "pic"), "Radiance HDR ({})", "")),
    ("avi", (("avi", ), "AVI ({})", "Audio Video Interleave")),
    ("mov", (("mov", "qt"), "QuickTime ({})", "")),
    ("mp4", (("mp4", ), "MPEG-4 ({})", "MPEG-4 Part 14")),
    ("ogg", (("ogg", "ogv"), "OGG Theora ({})", "")),
))

PLANE_COUNTER = 1
DURATION = 6

# XXX Hack to avoid allowing videos with Cycles, crashes currently!
VID_EXT_FILTER = {e for ext_k, ext_v in EXT_FILTER.items() if ext_k in {"avi", "mov", "mp4", "ogg"} for e in ext_v[0]}

CYCLES_SHADERS = (
    ('BSDF_DIFFUSE', "Diffuse", "Diffuse Shader"),
    ('EMISSION', "Emission", "Emission Shader"),
    ('BSDF_DIFFUSE_BSDF_TRANSPARENT', "Diffuse & Transparent", "Diffuse and Transparent Mix"),
    ('EMISSION_BSDF_TRANSPARENT', "Emission & Transparent", "Emission and Transparent Mix")
)    # -------------------------------------

# -----------------------------------------------------------------------------
# Image loading

ImageSpec = namedtuple(
    'ImageSpec',
    ['image', 'size', 'frame_start', 'frame_offset', 'frame_duration'])

num_regex = re.compile('[0-9]')  # Find a single number
nums_regex = re.compile('[0-9]+')  # Find a set of numbers


def find_image_sequences(files):
    """From a group of files, detect image sequences.

    This returns a generator of tuples, which contain the filename,
    start frame, and length of the detected sequence

    >>> list(find_image_sequences([
    ...     "test2-001.jp2", "test2-002.jp2",
    ...     "test3-003.jp2", "test3-004.jp2", "test3-005.jp2", "test3-006.jp2",
    ...     "blaah"]))
    [('blaah', 1, 1), ('test2-001.jp2', 1, 2), ('test3-003.jp2', 3, 4)]

    """
    files = iter(sorted(files))
    prev_file = None
    pattern = ""
    matches = []
    segment = None
    length = 1
    for filename in files:
        new_pattern = num_regex.sub('#', filename)
        new_matches = list(map(int, nums_regex.findall(filename)))
        if new_pattern == pattern:
            # this file looks like it may be in sequence from the previous

            # if there are multiple sets of numbers, figure out what changed
            if segment is None:
                for i, prev, cur in zip(count(), matches, new_matches):
                    if prev != cur:
                        segment = i
                        break

            # did it only change by one?
            for i, prev, cur in zip(count(), matches, new_matches):
                if i == segment:
                    # We expect this to increment
                    prev = prev + length
                if prev != cur:
                    break

            # All good!
            else:
                length += 1
                continue

        # No continuation -> spit out what we found and reset counters
        if prev_file:
            if length > 1:
                yield prev_file, matches[segment], length
            else:
                yield prev_file, 1, 1

        prev_file = filename
        matches = new_matches
        pattern = new_pattern
        segment = None
        length = 1

    if prev_file:
        if length > 1:
            yield prev_file, matches[segment], length
        else:
            yield prev_file, 1, 1


def load_images(filenames, directory, force_reload=False, frame_start=1, find_sequences=False):
    """Wrapper for bpy's load_image

    Loads a set of images, movies, or even image sequences
    Returns a generator of ImageSpec wrapper objects later used for texture setup
    """
    if find_sequences:  # if finding sequences, we need some pre-processing first
        file_iter = find_image_sequences(filenames)
    else:
        file_iter = zip(filenames, repeat(1), repeat(1))

    for filename, offset, frames in file_iter:
        image = load_image(filename, directory, check_existing=True, force_reload=force_reload)

        # Size is unavailable for sequences, so we grab it early
        size = tuple(image.size)

        if image.source == 'MOVIE':
            # Blender BPY BUG!
            # This number is only valid when read a second time in 2.77
            # This repeated line is not a mistake
            frames = image.frame_duration
            frames = image.frame_duration

        elif frames > 1:  # Not movie, but multiple frames -> image sequence
            image.source = 'SEQUENCE'

        yield ImageSpec(image, size, frame_start, offset - 1, frames)

# -----------------------------------------------------------------------------
# Position & Size Helpers

def offset_planes(planes, gap, axis):
    """Offset planes from each other by `gap` amount along a _local_ vector `axis`

    For example, offset_planes([obj1, obj2], 0.5, Vector(0, 0, 1)) will place
    obj2 0.5 blender units away from obj1 along the local positive Z axis.

    This is in local space, not world space, so all planes should share
    a common scale and rotation.
    """
    prior = planes[0]
    offset = Vector()
    #movement 
    for current in planes[1:]:

        local_offset = abs((prior.dimensions + current.dimensions) * axis) / 2.0 + gap

        offset += local_offset * axis
        current.location = current.matrix_world * offset

        prior = current

def compute_camera_size(context, center, fill_mode, aspect):
    """Determine how large an object needs to be to fit or fill the camera's field of view."""
    scene = context.scene
    camera = scene.camera
    view_frame = camera.data.view_frame(scene=scene)
    frame_size = \
        Vector([max(v[i] for v in view_frame) for i in range(3)]) - \
        Vector([min(v[i] for v in view_frame) for i in range(3)])
    camera_aspect = frame_size.x / frame_size.y

    # Convert the frame size to the correct sizing at a given distance
    if camera.type == 'ORTHO':
        frame_size = frame_size.xy
    else:
        # Perspective transform
        distance = world_to_camera_view(scene, camera, center).z
        frame_size = distance * frame_size.xy / (-view_frame[0].z)

    # Determine what axis to match to the camera
    match_axis = 0  # match the Y axis size
    match_aspect = aspect
    if (fill_mode == 'FILL' and aspect > camera_aspect) or \
            (fill_mode == 'FIT' and aspect < camera_aspect):
        match_axis = 1  # match the X axis size
        match_aspect = 1.0 / aspect

    # scale the other axis to the correct aspect
    frame_size[1 - match_axis] = frame_size[match_axis] / match_aspect

    return frame_size

def midpointXYZ(p1, p2):
    x = (p1.x+p2.x)/2
    y = (p1.y+p2.y)/2
    z = (p1.z+p2.z)/2
    return Vector((x, y, z))

def center_in_camera(scene, camera, obj, axis=(1, 1)):
    """Center object along specified axis of the camera"""
    camera_matrix_col = camera.matrix_world.col
    location = obj.location

    # Vector from the camera's world coordinate center to the object's center
    delta = camera_matrix_col[3].xyz - location

    # How far off center we are along the camera's local X
    camera_x_mag = delta.dot(camera_matrix_col[0].xyz) * axis[0]
    # How far off center we are along the camera's local Y
    camera_y_mag = delta.dot(camera_matrix_col[1].xyz) * axis[1]

    # Now offset only along camera local axis
    offset = camera_matrix_col[0].xyz * camera_x_mag + \
        camera_matrix_col[1].xyz * camera_y_mag

    obj.location = location + offset


# -----------------------------------------------------------------------------
# Misc utils.
def gen_ext_filter_ui_items():
    return tuple((k, name.format(", ".join("." + e for e in exts)) if "{}" in name else name, desc)
                 for k, (exts, name, desc) in EXT_FILTER.items())


def is_image_fn(fn, ext_key):
    if ext_key == DEFAULT_EXT:
        return True  # Using Blender's image/movie filter.
    ext = os.path.splitext(fn)[1].lstrip(".").lower()
    return ext in EXT_FILTER[ext_key][0]


# -----------------------------------------------------------------------------
# Cycles utils.
def get_input_nodes(node, nodes, links):
    # Get all links going to node.
    input_links = {lnk for lnk in links if lnk.to_node == node}
    # Sort those links, get their input nodes (and avoid doubles!).
    sorted_nodes = []
    done_nodes = set()
    for socket in node.inputs:
        done_links = set()
        for link in input_links:
            nd = link.from_node
            if nd in done_nodes:
                # Node already treated!
                done_links.add(link)
            elif link.to_socket == socket:
                sorted_nodes.append(nd)
                done_links.add(link)
                done_nodes.add(nd)
        input_links -= done_links
    return sorted_nodes


def auto_align_nodes(node_tree):
    print('\nAligning Nodes')
    x_gap = 200
    y_gap = 100
    nodes = node_tree.nodes
    links = node_tree.links
    to_node = None
    for node in nodes:
        if node.type == 'OUTPUT_MATERIAL':
            to_node = node
            break
    if not to_node:
        return  # Unlikely, but bette check anyway...

    def align(to_node, nodes, links):
        from_nodes = get_input_nodes(to_node, nodes, links)
        for i, node in enumerate(from_nodes):
            node.location.x = to_node.location.x - x_gap
            node.location.y = to_node.location.y
            node.location.y -= i * y_gap
            node.location.y += (len(from_nodes)-1) * y_gap / (len(from_nodes))
            align(node, nodes, links)

    align(to_node, nodes, links)


def clean_node_tree(node_tree):
    nodes = node_tree.nodes
    for node in nodes:
        if not node.type == 'OUTPUT_MATERIAL':
            nodes.remove(node)
    return node_tree.nodes[0]

def get_shadeless_node(dest_node_tree):
    """Return a "shadless" cycles/eevee node, creating a node group if nonexistent"""
    try:
        node_tree = bpy.data.node_groups['IAP_SHADELESS']

    except KeyError:
        # need to build node shadeless node group
        node_tree = bpy.data.node_groups.new('IAP_SHADELESS', 'ShaderNodeTree')
        output_node = node_tree.nodes.new('NodeGroupOutput')
        input_node = node_tree.nodes.new('NodeGroupInput')

        node_tree.outputs.new('NodeSocketShader', 'Shader')
        node_tree.inputs.new('NodeSocketColor', 'Color')

        # This could be faster as a transparent shader, but then no ambient occlusion
        diffuse_shader = node_tree.nodes.new('ShaderNodeBsdfDiffuse')
        node_tree.links.new(diffuse_shader.inputs[0], input_node.outputs[0])

        emission_shader = node_tree.nodes.new('ShaderNodeEmission')
        node_tree.links.new(emission_shader.inputs[0], input_node.outputs[0])

        light_path = node_tree.nodes.new('ShaderNodeLightPath')
        is_glossy_ray = light_path.outputs['Is Glossy Ray']
        is_shadow_ray = light_path.outputs['Is Shadow Ray']
        ray_depth = light_path.outputs['Ray Depth']
        transmission_depth = light_path.outputs['Transmission Depth']

        unrefracted_depth = node_tree.nodes.new('ShaderNodeMath')
        unrefracted_depth.operation = 'SUBTRACT'
        unrefracted_depth.label = 'Bounce Count'
        node_tree.links.new(unrefracted_depth.inputs[0], ray_depth)
        node_tree.links.new(unrefracted_depth.inputs[1], transmission_depth)

        refracted = node_tree.nodes.new('ShaderNodeMath')
        refracted.operation = 'SUBTRACT'
        refracted.label = 'Camera or Refracted'
        refracted.inputs[0].default_value = 1.0
        node_tree.links.new(refracted.inputs[1], unrefracted_depth.outputs[0])

        reflection_limit = node_tree.nodes.new('ShaderNodeMath')
        reflection_limit.operation = 'SUBTRACT'
        reflection_limit.label = 'Limit Reflections'
        reflection_limit.inputs[0].default_value = 2.0
        node_tree.links.new(reflection_limit.inputs[1], ray_depth)

        camera_reflected = node_tree.nodes.new('ShaderNodeMath')
        camera_reflected.operation = 'MULTIPLY'
        camera_reflected.label = 'Camera Ray to Glossy'
        node_tree.links.new(camera_reflected.inputs[0], reflection_limit.outputs[0])
        node_tree.links.new(camera_reflected.inputs[1], is_glossy_ray)

        shadow_or_reflect = node_tree.nodes.new('ShaderNodeMath')
        shadow_or_reflect.operation = 'MAXIMUM'
        shadow_or_reflect.label = 'Shadow or Reflection?'
        node_tree.links.new(shadow_or_reflect.inputs[0], camera_reflected.outputs[0])
        node_tree.links.new(shadow_or_reflect.inputs[1], is_shadow_ray)

        shadow_or_reflect_or_refract = node_tree.nodes.new('ShaderNodeMath')
        shadow_or_reflect_or_refract.operation = 'MAXIMUM'
        shadow_or_reflect_or_refract.label = 'Shadow, Reflect or Refract?'
        node_tree.links.new(shadow_or_reflect_or_refract.inputs[0], shadow_or_reflect.outputs[0])
        node_tree.links.new(shadow_or_reflect_or_refract.inputs[1], refracted.outputs[0])

        mix_shader = node_tree.nodes.new('ShaderNodeMixShader')
        node_tree.links.new(mix_shader.inputs[0], shadow_or_reflect_or_refract.outputs[0])
        node_tree.links.new(mix_shader.inputs[1], diffuse_shader.outputs[0])
        node_tree.links.new(mix_shader.inputs[2], emission_shader.outputs[0])

        node_tree.links.new(output_node.inputs[0], mix_shader.outputs[0])

        auto_align_nodes(node_tree)

    group_node = dest_node_tree.nodes.new("ShaderNodeGroup")
    group_node.node_tree = node_tree

    return group_node


# -----------------------------------------------------------------------------
# Corner Pin Driver Helpers

@bpy.app.handlers.persistent
def check_drivers(*args, **kwargs):
    """Check if watched objects in a scene have changed and trigger compositor update

    This is part of a hack to ensure the compositor updates
    itself when the objects used for drivers change.

    It only triggers if transformation matricies change to avoid
    a cyclic loop of updates.
    """
    if not watched_objects:
        # if there is nothing to watch, don't bother running this
        bpy.app.handlers.depsgraph_update_post.remove(check_drivers)
        return

    update = False
    for name, matrix in list(watched_objects.items()):
        try:
            obj = bpy.data.objects[name]
        except KeyError:
            # The user must have removed this object
            del watched_objects[name]
        else:
            new_matrix = tuple(map(tuple, obj.matrix_world)).__hash__()
            if new_matrix != matrix:
                watched_objects[name] = new_matrix
                update = True

    if update:
        # Trick to re-evaluate drivers
        bpy.context.scene.frame_current = bpy.context.scene.frame_current



# -----------------------------------------------------------------------------
# Operator

class IMPORT_OT_image_to_plane(Operator, AddObjectHelper):
    """Create mesh plane(s) from image files with the appropiate aspect ratio"""
    bl_idname = "import_image.to_plane"
    bl_label = "Import Images as Planes"
    bl_options = {'REGISTER', 'UNDO'}
    #TODO: good place to have this?
    anim_counter = 0

    # -----------
    # File props.
    files: CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})

    directory: StringProperty(maxlen=1024, subtype='FILE_PATH', options={'HIDDEN', 'SKIP_SAVE'})

    # Show only images/videos, and directories!
    filter_image: BoolProperty(default=True, options={'HIDDEN', 'SKIP_SAVE'})
    filter_movie: BoolProperty(default=True, options={'HIDDEN', 'SKIP_SAVE'})
    filter_folder: BoolProperty(default=True, options={'HIDDEN', 'SKIP_SAVE'})
    filter_glob: StringProperty(default="", options={'HIDDEN', 'SKIP_SAVE'})

    # --------
    # Options.
    align: BoolProperty(name="Align Planes", default=True, description="Create Planes in a row")
    
    #Callback to set as False the align option when the animate one is enabled
    def update_animate(self, context):
        if self.animate:
            self.align = False

    
    animate: BoolProperty(name="Animate Planes", default=True, description="Display only one plane at the time to create an animation. 'Align' options should be disabled to be able to see the animation.", update=update_animate)
    animate_duration: IntProperty(name="Animation duration per frame", min=1, soft_min=1, default=4, description="In an animation each frame will be shown this number of frames.")
    animate_start: IntProperty(name="Animation start frame", min=1, soft_min=1, default=1, description="The frame the animation will begin.")
    animate_loop: IntProperty(name="Animation loop count", min=1, soft_min=1, default=1, description="The number of times the animation will be repeated.")

    align_offset: FloatProperty(name="Offset", min=0, soft_min=0, default=0.1, description="Space between Planes")
    
    
    # Callback which will update File window's filter options accordingly to extension setting.
    def update_extensions(self, context):
        is_cycles = context.scene.render.engine == 'CYCLES'
        if self.extension == DEFAULT_EXT:
            self.filter_image = True
            # XXX Hack to avoid allowing videos with Cycles, crashes currently!
            self.filter_movie = True and not is_cycles
            self.filter_glob = ""
        else:
            self.filter_image = False
            self.filter_movie = False
            if is_cycles:
                # XXX Hack to avoid allowing videos with Cycles!
                flt = ";".join(("*." + e for e in EXT_FILTER[self.extension][0] if e not in VID_EXT_FILTER))
            else:
                flt = ";".join(("*." + e for e in EXT_FILTER[self.extension][0]))
            self.filter_glob = flt
        # And now update space (file select window), if possible.
        space = bpy.context.space_data
        # XXX Can't use direct op comparison, these are not the same objects!
        if (space.type != 'FILE_BROWSER' or space.operator.bl_rna.identifier != self.bl_rna.identifier):
            return
        space.params.use_filter_image = self.filter_image
        space.params.use_filter_movie = self.filter_movie
        space.params.filter_glob = self.filter_glob
        # XXX Seems to be necessary, else not all changes above take effect...
        bpy.ops.file.refresh()
    extension = EnumProperty(name="Extension", items=gen_ext_filter_ui_items(),
                             description="Only import files of this type", update=update_extensions)

    # -------------------
    # Plane size options.

    def align_plane(self, context, plane):
        """Pick an axis and align the plane to it"""
        if 'CAM' in self.align_axis:
            # Camera-aligned
            camera = context.scene.camera
            if (camera):
                # Find the axis that best corresponds to the camera's view direction
                axis = camera.matrix_world @ \
                    Vector((0, 0, 1)) - camera.matrix_world.col[3].xyz
                # pick the axis with the greatest magnitude
                mag = max(map(abs, axis))
                # And use that axis & direction
                axis = Vector([
                    n / mag if abs(n) == mag else 0.0
                    for n in axis
                ])
            else:
                # No camera? Just face Z axis
                axis = Vector((0, 0, 1))
                self.align_axis = 'Z+'
        else:
            # Axis-aligned
            axis = self.axis_id_to_vector[self.align_axis]

        # rotate accordingly for x/y axiis
        if not axis.z:
            plane.rotation_euler.x = pi / 2

            if axis.y > 0:
                plane.rotation_euler.z = pi
            elif axis.y < 0:
                plane.rotation_euler.z = 0
            elif axis.x > 0:
                plane.rotation_euler.z = pi / 2
            elif axis.x < 0:
                plane.rotation_euler.z = -pi / 2

        # or flip 180 degrees for negative z
        elif axis.z < 0:
            plane.rotation_euler.y = pi

        constraint = plane.constraints.new('COPY_ROTATION')
        constraint.target = camera
        constraint.use_x = constraint.use_y = constraint.use_z = True


        if self.align_axis == 'CAM_AX' and self.align_track:
            constraint = plane.constraints.new('LOCKED_TRACK')
            constraint.target = camera
            constraint.track_axis = 'TRACK_Z'
            constraint.lock_axis = 'LOCK_Y'
    
    def update_size_mode(self, context):
        """If sizing relative to the camera, always face the camera"""
        if self.size_mode == 'CAMERA':
            self.prev_align_axis = self.align_axis
            self.align_axis = 'CAM'
        else:
            # if a different alignment was set revert to that when
            # size mode is changed
            if self.prev_align_axis != 'NONE':
                self.align_axis = self.prev_align_axis
                self._prev_align_axis = 'NONE'
    
    _size_modes = (
        ('ABSOLUTE', "Absolute", "Use absolute size"),
        ('CAMERA', "Camera Relative", "Scale to the camera frame"),
        ('DPI', "Dpi", "Use definition of the image as dots per inch"),
        ('DPBU', "Dots/BU", "Use definition of the image as dots per Blender Unit"),
    )
    size_mode: EnumProperty(name="Size Mode", default='CAMERA', items=_size_modes,
                             update=update_size_mode, description="How the size of the plane is computed")
    FILL_MODES = (
        ('FILL', "Fill", "Fill camera frame, spilling outside the frame"),
        ('FIT', "Fit", "Fit entire image within the camera frame"),
    )
    fill_mode: EnumProperty(name="Scale", default='FILL', items=FILL_MODES,
                             description="How large in the camera frame is the plane")

    height: FloatProperty(name="Height", description="Height of the created plane",
                           default=1.0, min=0.001, soft_min=0.001, subtype='DISTANCE', unit='LENGTH')

    factor: FloatProperty(name="Definition", min=1.0, default=600.0,
                           description="Number of pixels per inch or Blender Unit")

    # ----------------------
    # Properties - Importing
    force_reload: BoolProperty(
        name="Force Reload", default=False,
        description="Force reloading of the image if already opened elsewhere in Blender"
    )

    image_sequence: BoolProperty(
        name="Animate Image Sequences", default=False,
        description="Import sequentially numbered images as an animated "
                    "image sequence instead of separate planes"
    )

    # Properties - Position and Orientation
    axis_id_to_vector = {
        'X+': Vector(( 1,  0,  0)),
        'Y+': Vector(( 0,  1,  0)),
        'Z+': Vector(( 0,  0,  1)),
        'X-': Vector((-1,  0,  0)),
        'Y-': Vector(( 0, -1,  0)),
        'Z-': Vector(( 0,  0, -1)),
    }

    offset: BoolProperty(name="Offset Planes", default=True, description="Offset Planes From Each Other")

    OFFSET_MODES = (
        ('X+', "X+", "Side by Side to the Left"),
        ('Y+', "Y+", "Side by Side, Downward"),
        ('Z+', "Z+", "Stacked Above"),
        ('X-', "X-", "Side by Side to the Right"),
        ('Y-', "Y-", "Side by Side, Upward"),
        ('Z-', "Z-", "Stacked Below"),
    )
    offset_axis: EnumProperty(
        name="Orientation", default='Z+', items=OFFSET_MODES,
        description="How planes are oriented relative to each others' local axis"
    )

    offset_amount: FloatProperty(
        name="Offset", soft_min=0, default=0.1, description="Space between planes",
        subtype='DISTANCE', unit='LENGTH'
    )

    AXIS_MODES = (
        ('X+', "X+", "Facing Positive X"),
        ('Y+', "Y+", "Facing Positive Y"),
        ('Z+', "Z+ (Up)", "Facing Positive Z"),
        ('X-', "X-", "Facing Negative X"),
        ('Y-', "Y-", "Facing Negative Y"),
        ('Z-', "Z- (Down)", "Facing Negative Z"),
        ('CAM', "Face Camera", "Facing Camera"),
        ('CAM_AX', "Main Axis", "Facing the Camera's dominant axis"),
    )
    align_axis: EnumProperty(
        name="Align", default='CAM_AX', items=AXIS_MODES,
        description="How to align the planes"
    )
    # prev_align_axis is used only by update_size_model
    prev_align_axis = EnumProperty(
        items=AXIS_MODES + (('NONE', '', ''),), default='NONE', options={'HIDDEN', 'SKIP_SAVE'})
    align_track: BoolProperty(
        name="Track Camera", default=True, description="Always face the camera"
    )

    # ------------------------------
    # Properties - Material / Shader
    SHADERS = (
        ('PRINCIPLED',"Principled","Principled Shader"),
        ('SHADELESS', "Shadeless", "Only visible to camera and reflections"),
        ('EMISSION', "Emit", "Emission Shader"),
    )
    shader: EnumProperty(name="Shader", items=SHADERS, default='SHADELESS', description="Node shader to use")

    emit_strength: FloatProperty(
        name="Strength", min=0.0, default=1.0, soft_max=10.0,
        step=100, description="Brightness of Emission Texture")

    overwrite_material: BoolProperty(
        name="Overwrite Material", default=True,
        description="Overwrite existing Material (based on material name)")

    compositing_nodes: BoolProperty(
        name="Setup Corner Pin", default=False,
        description="Build Compositor Nodes to reference this image "
                    "without re-rendering")

    # ------------------
    # Properties - Image
    use_transparency: BoolProperty(
        name="Use Alpha", default=True,
        description="Use alpha channel for transparency")

    t = bpy.types.Image.bl_rna.properties["alpha_mode"]
    alpha_mode_items = tuple((e.identifier, e.name, e.description) for e in t.enum_items)
    alpha_mode: EnumProperty(
        name=t.name, items=alpha_mode_items, default=t.default,
        description=t.description)

    t = bpy.types.ImageUser.bl_rna.properties["use_auto_refresh"]
    use_auto_refresh: BoolProperty(name=t.name, default=True, description=t.description)

    relative: BoolProperty(name="Relative Paths", default=True, description="Use relative file paths")

    # ------------------
    # Properties - Image
    use_transparency: BoolProperty(
        name="Use Alpha", default=True,
        description="Use alpha channel for transparency")

    t = bpy.types.Image.bl_rna.properties["alpha_mode"]
    alpha_mode_items = tuple((e.identifier, e.name, e.description) for e in t.enum_items)
    alpha_mode: EnumProperty(
        name=t.name, items=alpha_mode_items, default="PREMUL",
        description=t.description)

    t = bpy.types.ImageUser.bl_rna.properties["use_auto_refresh"]
    use_auto_refresh: BoolProperty(name=t.name, default=True, description=t.description)

    relative: BoolProperty(name="Relative Paths", default=True, description="Use relative file paths")

    # -------
    # Draw UI
    def draw_import_config(self, context):
        # --- Import Options --- #
        layout = self.layout
        box = layout.box()

        box.label(text="Import Options:", icon='IMPORT')
        row = box.row()
        row.active = bpy.data.is_saved
        row.prop(self, "relative")
        box.prop(self, "align")
        box.prop(self, "align_offset")
        box.prop(self, "animate")
        box.prop(self, "animate_duration")
        box.prop(self, "animate_start")
        box.prop(self, "animate_loop")

    def draw_material_config(self, context):
        # --- Material / Rendering Properties --- #
        layout = self.layout
        box = layout.box()

        box.label(text="Compositing Nodes:", icon='RENDERLAYERS')
        box.prop(self, "compositing_nodes")

        box.label(text="Material Settings:", icon='MATERIAL')

        row = box.row()
        row.prop(self, 'shader', expand=True)
        if self.shader == 'EMISSION':
            box.prop(self, "emit_strength")

        engine = context.scene.render.engine
        if engine not in ('CYCLES', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'):
            box.label(text="%s is not supported" % engine, icon='ERROR')

        box.prop(self, "overwrite_material")

        box.label(text="Texture Settings:", icon='TEXTURE')
        row = box.row()
        row.prop(self, "use_transparency")
        sub = row.row()
        sub.active = self.use_transparency
        sub.prop(self, "alpha_mode", text="")
        box.prop(self, "use_auto_refresh")

    def draw_spatial_config(self, context):
        # --- Spatial Properties: Position, Size and Orientation --- #
        layout = self.layout
        box = layout.box()

        box.label(text="Position:", icon='SNAP_GRID')
        box.prop(self, "offset")
        col = box.column()
        row = col.row()
        #row.prop(self, "offset_axis", expand=True)
        #row = col.row()
        row.prop(self, "offset_amount")
        col.enabled = self.offset

        box.label(text="Plane dimensions:", icon='ARROW_LEFTRIGHT')
        row = box.row()
        row.prop(self, "size_mode", expand=True)
        if self.size_mode == 'ABSOLUTE':
            box.prop(self, "height")
        elif self.size_mode == 'CAMERA':
            row = box.row()
            row.prop(self, "fill_mode", expand=True)
        else:
            box.prop(self, "factor")

        box.label(text="Orientation:")
        row = box.row()
        row.enabled = 'CAM' not in self.size_mode
        row.prop(self, "align_axis")
        row = box.row()
        row.enabled = 'CAM' in self.align_axis
        row.alignment = 'RIGHT'
        row.prop(self, "align_track")

    def draw(self, context):

        # Draw configuration sections
        self.draw_import_config(context)
        self.draw_material_config(context)
        self.draw_spatial_config(context)

    def invoke(self, context, event):
        engine = context.scene.render.engine
        if engine not in {'CYCLES', 'BLENDER_EEVEE'}:
            if engine != 'BLENDER_WORKBENCH':
                self.report({'ERROR'}, "Cannot generate materials for unknown %s render engine" % engine)
                return {'CANCELLED'}
            else:
                self.report({'WARNING'},
                            "Generating Cycles/EEVEE compatible material, but won't be visible with %s engine" % engine)

        self.report({'WARNING'}, "Using %s" % engine)
        #self.update_extensions(context)
        self.update_animate(context)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if not bpy.data.is_saved:
            self.relative = False

        # this won't work in edit mode
        editmode = context.preferences.edit.use_enter_edit_mode
        context.preferences.edit.use_enter_edit_mode = False
        if context.active_object and context.active_object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        self.report({'WARNING'}, "IMPORTING")
        self.import_images(context)

        context.preferences.edit.use_enter_edit_mode = editmode
        return {'FINISHED'}

    # Main...
    def import_images(self, context):
        # load images / sequences
        images = tuple(load_images(
            (fn.name for fn in self.files),
            self.directory,
            force_reload=self.force_reload,
            find_sequences=self.animate
        ))


        #materials = list(materials)[0::self.animate_duration]
        
        #planes = tuple(self.create_image_plane(context, mat) for mat in materials)
        planes = [self.single_image_spec_to_plane(context, img_spec) for img_spec in images]
        ratio = '0.25'
        
        if self.animate:
            for plane in planes:
                self.animate_plane(plane, len(planes))

        context.view_layer.update()
        if self.align:
            self.align_planes(planes)

        context.view_layer.update()                
        target = context.scene.camera
        for plane in planes:
            plane.select_set(True)
            self.align_plane(context, plane)
            self.add_driver(plane, target, 'scale', 'scale.x', "0")
            self.add_driver(plane, target, 'scale', 'scale.y', "1")
            self.add_driver(plane, target, 'scale', 'scale.z', "2")
        context.view_layer.update() 
        for plane in planes:
            plane.parent = target
            plane.matrix_parent_inverse = target.matrix_world.inverted()
        context.view_layer.update() 
        self.report({'INFO'}, "Added {} Image Plane(s)".format(len(planes)))

    # operate on a single image
    def single_image_spec_to_plane(self, context, img_spec):

        # Configure image
        self.apply_image_options(img_spec.image)

        # Configure material
        engine = context.scene.render.engine
        if engine in {'CYCLES', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}:
            material = self.create_cycles_material(context, img_spec)

        # Create and position plane object
        plane = self.create_image_plane(context, material.name, img_spec)

        # Assign Material
        plane.data.materials.append(material)

        # If applicable, setup Corner Pin node
        #if self.compositing_nodes:
        #    setup_compositing(context, plane, img_spec)

        return plane

    def apply_image_options(self, image):
        if self.use_transparency == False:
            image.alpha_mode = 'NONE'
        else:
            image.alpha_mode = self.alpha_mode

        if self.relative:
            try:  # can't always find the relative path (between drive letters on windows)
                image.filepath = bpy.path.relpath(image.filepath)
            except ValueError:
                pass

    def apply_texture_options(self, texture, img_spec):
        # Shared by both Cycles and Blender Internal
        image_user = texture.image_user
        image_user.use_auto_refresh = self.use_auto_refresh
        image_user.frame_start = img_spec.frame_start
        image_user.frame_offset = img_spec.frame_offset
        image_user.frame_duration = img_spec.frame_duration

        # Image sequences need auto refresh to display reliably
        if img_spec.image.source == 'SEQUENCE':
            image_user.use_auto_refresh = True

        texture.extension = 'CLIP'  # Default of "Repeat" can cause artifacts

    def apply_material_options(self, material, slot):
        shader = self.shader

        if self.use_transparency:
            material.alpha = 0.0
            material.specular_alpha = 0.0
            slot.use_map_alpha = True
        else:
            material.alpha = 1.0
            material.specular_alpha = 1.0
            slot.use_map_alpha = False

        material.specular_intensity = 0
        material.diffuse_intensity = 1.0
        material.use_transparency = self.use_transparency
        material.transparency_method = 'Z_TRANSPARENCY'
        material.use_shadeless = (shader == 'SHADELESS')
        material.use_transparent_shadows = (shader == 'DIFFUSE')
        material.emit = self.emit_strength if shader == 'EMISSION' else 0.0

    # -------------------------------------------------------------------------
    # Cycles/Eevee
    def create_cycles_texnode(self, context, node_tree, img_spec):
        tex_image = node_tree.nodes.new('ShaderNodeTexImage')
        tex_image.image = img_spec.image
        tex_image.show_texture = True
        self.apply_texture_options(tex_image, img_spec)
        return tex_image

    def create_cycles_material(self, context, img_spec):
        image = img_spec.image
        name_compat = bpy.path.display_name_from_filepath(image.filepath)
        material = None
        if self.overwrite_material:
            for mat in bpy.data.materials:
                if mat.name == name_compat:
                    material = mat
        if not material:
            material = bpy.data.materials.new(name=name_compat)

        material.use_nodes = True
        if self.use_transparency:
            material.blend_method = 'BLEND'
        node_tree = material.node_tree
        out_node = clean_node_tree(node_tree)

        tex_image = self.create_cycles_texnode(context, node_tree, img_spec)

        if self.shader == 'PRINCIPLED':
            core_shader = node_tree.nodes.new('ShaderNodeBsdfPrincipled')
        elif self.shader == 'SHADELESS':
            core_shader = get_shadeless_node(node_tree)
        else:  # Emission Shading
            core_shader = node_tree.nodes.new('ShaderNodeEmission')
            core_shader.inputs[1].default_value = self.emit_strength

        # Connect color from texture
        node_tree.links.new(core_shader.inputs[0], tex_image.outputs[0])

        if self.use_transparency:
            if self.shader == 'PRINCIPLED':
                node_tree.links.new(core_shader.inputs[18], tex_image.outputs[1])
            else:
                bsdf_transparent = node_tree.nodes.new('ShaderNodeBsdfTransparent')

                mix_shader = node_tree.nodes.new('ShaderNodeMixShader')
                node_tree.links.new(mix_shader.inputs[0], tex_image.outputs[1])
                node_tree.links.new(mix_shader.inputs[1], bsdf_transparent.outputs[0])
                node_tree.links.new(mix_shader.inputs[2], core_shader.outputs[0])
                core_shader = mix_shader

        node_tree.links.new(out_node.inputs[0], core_shader.outputs[0])

        auto_align_nodes(node_tree)
        return material

    def create_image_plane(self, context, name, img_spec):
        width, height = self.compute_plane_size(context, img_spec)

        bpy.ops.mesh.primitive_plane_add('INVOKE_REGION_WIN')
        plane = context.active_object
        # Why does mesh.primitive_plane_add leave the object in edit mode???
        if plane.mode is not 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        plane.dimensions = width, height, 0.0
        plane.data.name = plane.name = name
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        
        #plane.data.uv_textures.new()
        #plane.data.materials.append(material)
        #plane.data.uv_textures[0].data[0].image = img

        offset_axis = self.axis_id_to_vector[self.offset_axis]
        translate_axis = [0 if offset_axis[i] else 1 for i in (0, 1)]

        center_in_camera(context.scene, context.scene.camera, plane, translate_axis)
    
        #material.game_settings.use_backface_culling = False
        #material.game_settings.alpha_blend = 'ALPHA'
        
        return plane

    def compute_plane_size(self, context, img_spec):
        """Given the image size in pixels and location, determine size of plane"""
        px, py = img_spec.size

        # can't load data
        if px == 0 or py == 0:
            px = py = 1

        if self.size_mode == 'ABSOLUTE':
            y = self.height
            x = px / py * y
        elif self.size_mode == 'CAMERA':
            x, y = compute_camera_size(
                context, context.scene.cursor.location,
                self.fill_mode, px / py
            )
        elif self.size_mode == 'DPI':
            fact = 1 / self.factor / context.scene.unit_settings.scale_length * 0.0254
            x = px * fact
            y = py * fact
        else:  # elif self.size_mode == 'DPBU'
            fact = 1 / self.factor
            x = px * fact
            y = py * fact

        return x, y


    def animate_plane(self, plane, numPlanes):
        
        global PLANE_COUNTER
        DURATION = self.animate_duration
        START_FRAME = self.animate_start
        LOOPS = self.animate_loop
        
        print ("animating plane: %s"% plane)
        
        #we are going to animate the layer visibility and render-ability.

        #stores the previous interpolation default
        keyinter = bpy.context.preferences.edit.keyframe_new_interpolation_type 
        
        #sets the new interpolation type to linear
        bpy.context.preferences.edit.keyframe_new_interpolation_type = "CONSTANT"
        
        #references the plane
        ob = plane
        
        #create animation data
        ob.animation_data_create()
        
        #creates a new action for the object, if needed
        actionname = "Plane import animation for %s"% ob.name
        if not actionname in bpy.data.actions:
            ob.animation_data.action = bpy.data.actions.new(actionname)
        else:
            ob.animation_data.action = bpy.data.actions[actionname]
        
        #add a new fcurve for the "hide" property 
        if not "hide" in [ x.data_path for x in ob.animation_data.action.fcurves ]:
            fcu = ob.animation_data.action.fcurves.new(data_path="hide")
        else:
            fcu = [ x for x in ob.animation_data.action.fcurves if x.data_path == 'hide' ][0]
            
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
        fcu.keyframe_points[0].co = START_FRAME - 1, hide
        fcu2.keyframe_points[0].co = START_FRAME - 1, hide

        pointX = 1
        loopcount = 0
        while pointX < (2*LOOPS)+1:
            #set interpolation to constant
            fcu.keyframe_points[pointX].interpolation = "CONSTANT"
            fcu.keyframe_points[pointX+1].interpolation = "CONSTANT"
            fcu2.keyframe_points[pointX].interpolation = "CONSTANT"
            fcu2.keyframe_points[pointX+1].interpolation = "CONSTANT"       

            planeX = (self.anim_counter * (DURATION)) 

            #sets the first point: hide
            fcu.keyframe_points[pointX].co = START_FRAME + planeX + (loopcount*DURATION*(numPlanes)), show
            fcu2.keyframe_points[pointX].co = START_FRAME + planeX + (loopcount*DURATION*(numPlanes)), show

            #how long to show frame
            fcu.keyframe_points[pointX+1].co = fcu.keyframe_points[pointX].co.x + DURATION, hide
            fcu2.keyframe_points[pointX+1].co = fcu2.keyframe_points[pointX].co.x + DURATION, hide

            pointX += 2
            loopcount += 1
        
        self.anim_counter = self.anim_counter + 1
        
        #recovers the previous interpolation setting
        bpy.context.preferences.edit.keyframe_new_interpolation_type = keyinter

    def add_driver(self, source, target, prop, dataPath, index, func = ''):
        ''' Add driver to source prop (at index), driven by target dataPath '''
        negative = False
        prop = str(prop)
        dataPath = str(dataPath)
        index = int(index)
        if index != -1:
            f = source.driver_add(prop, index)
            d = f.driver
        else:
            d = f.driver

        v = d.variables.new()
        v.type = 'LOC_DIFF'
        v.name                 = prop
        v.targets[0].id        = source
        v.targets[1].id        = target
        v.targets[0].data_path = dataPath

        camloc = target.matrix_world.translation

        x, y, z = [ sum( [v.co[i] for v in source.data.vertices] ) for i in range(3)]
        count = float(len(source.data.vertices))
        center = source.matrix_world @ \
            (Vector( (x, y, z ) ) / count )
        
        locx = camloc[0] - center[0]
        locy = camloc[1] - center[1]
        locz = camloc[2] - center[2]

        distance = sqrt((locx)**2 + (locy)**2 + (locz)**2)
        
        d.expression = func + "(" + v.name + "/" + str(distance) + ")"
        #d.expression = d.expression if not negative else "-1 * " + d.expression

    def align_planes(self, planes):
        gap = self.align_offset
        offset_axis = Vector((0,  0,  1))
        offset_planes(planes, self.offset_amount, offset_axis)

    def generate_paths(self):
        return (fn.name for fn in self.files if is_image_fn(fn.name, self.extension)), self.directory

    def set_image_options(self, image):
        image.alpha_mode = self.alpha_mode
        image.use_fields = self.use_fields

        if self.relative:
            try:  # can't always find the relative path (between drive letters on windows)
                image.filepath = bpy.path.relpath(image.filepath)
            except ValueError:
                pass

    def set_texture_options(self, context, texture):
        texture.image.use_alpha = self.use_transparency
        texture.image_user.use_auto_refresh = self.use_auto_refresh
        if self.match_len:
            ctx = context.copy()
            ctx["edit_image"] = texture.image
            ctx["edit_image_user"] = texture.image_user
            bpy.ops.image.match_movie_length(ctx)

    def set_material_options(self, material, slot):
        if self.use_transparency:
            material.alpha = 0.0
            material.specular_alpha = 0.0
            slot.use_map_alpha = True
        else:
            material.alpha = 1.0
            material.specular_alpha = 1.0
            slot.use_map_alpha = False
        material.use_transparency = self.use_transparency
        material.transparency_method = self.transparency_method
        material.use_shadeless = self.use_shadeless
        material.use_transparent_shadows = self.use_transparent_shadows

# -----------------------------------------------------------------------------
# Register
def menu_func(self, context):
    self.layout.operator(IMPORT_OT_image_to_plane.bl_idname, icon="TEXTURE")

def register():
    # register classes so blender knows about them
    bpy.utils.register_class(IMPORT_OT_image_to_plane)
    # this adds your menu to shift-a add object menu (VIEW3D_MT_add)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)
    # if you want to add to mesh menu use INFO_MT_mesh_add
    # other menu classes you can find in \scripts\startup\bl_ui\
    # by looking into the files there (i.e.: space_view3d.py)

def unregister():
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
    bpy.utils.unregister_class(IMPORT_OT_image_to_plane)

if __name__ == "__main__":
    register()
