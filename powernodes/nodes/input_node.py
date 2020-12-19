import bpy
import bmesh
from bpy.props import BoolProperty, IntProperty, FloatProperty, PointerProperty, StringProperty
from bpy.types import Node

from .. base_node import BaseNode


class InputNode(BaseNode):
    '''Input node'''

    bl_idname = 'InputNode'

    bl_label = 'Input Node'

    bl_icon = 'NODE'

    ops_type : bpy.props.StringProperty(name='ops_type', default='')


    def is_input_node(self):
        return True


    def process(self, MODULE=None, OPSCOPE=None):
        self.needs_processing = False
        self.is_processing = True

        options = self.get_options_from_inputs(self.inputs)
        options['ops_type'] = self.ops_type

        OPS_PROP_DEF = MODULE['definition']
        (ops_output, preview_data) = OPSCOPE[OPS_PROP_DEF[self.ops_type]['command']](options=options)

        for out_val, socket in zip(ops_output, self.outputs):
            socket.prop = out_val

        self.is_processing = False
