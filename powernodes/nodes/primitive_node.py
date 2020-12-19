import bpy
import bmesh
from bpy.props import BoolProperty, IntProperty, FloatProperty, PointerProperty, StringProperty
from bpy.types import Node

import math
from mathutils.geometry import intersect_line_plane, intersect_point_line, intersect_line_line

from .. ops import initialize_default_collections, link_to_collection, unlink_from_collection, clone_object, delete_object

from .. base_node import BaseNode
from .. utils.utils import random_color, change_viewport_shading, squarify_vector
from .. sockets import init_node_sockets
from .. handlers import get_rendering_flag
from .. draw import copy_offscreen_to_image


class PrimitiveNode(BaseNode):
    '''Live primitive node'''

    bl_idname = 'PrimitiveNode'

    bl_label = 'Primitive Node'

    bl_icon = 'NODE'

    start_point : bpy.props.FloatVectorProperty(default=(0, 0, 0), size=3, subtype='XYZ')
    end_point : bpy.props.FloatVectorProperty(default=(0, 0, 0), size=3, subtype='XYZ')
    depth_point : bpy.props.FloatVectorProperty(default=(0, 0, 0), size=3, subtype='XYZ')
    normal_point : bpy.props.FloatVectorProperty(default=(0, 0, 0), size=3, subtype='XYZ')
    sign : bpy.props.FloatProperty(default=0.0)

    ops_type : bpy.props.StringProperty(name='ops_type', default='PLANE')


    def init(self, context):
        super().init(context)

        col = self.output_color
        self.output_color = (col[0], col[1], col[3], 0.1)

        self.needs_processing = True


    def copy(self, node):
        super().copy(node)
        outputstream_socket = self.get_first_outputstream_socket()
        outputstream_socket.prop = '' # clear output
        self.needs_processing = True


    def is_input_node(self):
        return True


    def process(self, MODULE=None, OPSCOPE=None):
        self.needs_processing = False
        self.is_processing = True

        # process node
        inputstream_socket = self.get_first_inputstream_socket()
        outputstream_socket = self.get_first_outputstream_socket()

        op_inputs = []
        input_objects = self.get_items_from_stream_socket(inputstream_socket)
        op_inputs.append(input_objects)

        # clone inputs
        op_clone_inputs = []
        for op_input in op_inputs:
            input_clones = [clone_object(obj, name='CLONE_' + obj.name.replace('OUT_', '')) for obj in op_input]
            op_clone_inputs.append(input_clones)

        options = self.get_options_from_inputs(self.inputs)
        options['ops_type'] = self.ops_type

        OPS_PROP_DEF = MODULE['definition']
        (objects, preview_data) = OPSCOPE[OPS_PROP_DEF[self.ops_type]['command']](*op_clone_inputs, options=options)

        output_objects = self.get_items_from_stream_socket(outputstream_socket)
        keep_output_objects = [obj for obj in output_objects if obj and not self.owns_object(obj)]
        [delete_object(obj) for obj in output_objects if obj and self.owns_object(obj)]

        for obj in objects:
            obj['_pn_node_tag_'] = self.id
            obj.color = self.output_color
            # shade_smooth_operator([obj])

        # delete clones
        for op_clone_input in op_clone_inputs:
            [delete_object(obj) for obj in op_clone_input if obj and not self.owns_object(obj)]

        outputstream_keep_items = [obj.name for obj in keep_output_objects]
        self.set_items_to_stream_socket(outputstream_socket, outputstream_keep_items + objects)

        if not get_rendering_flag() and self.get_node_tree().show_preview and len(objects) > 0:
            prev_obj = objects[0]
            self.preview_name = copy_offscreen_to_image(obj_preview_name='PREVIEW_' + prev_obj.name, obj=prev_obj, preview_data=preview_data)

        self.is_processing = False
