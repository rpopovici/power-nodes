import bpy
import bmesh
from bpy.props import BoolProperty, IntProperty, FloatProperty, PointerProperty, StringProperty
from bpy.types import Node

from .. base_node import BaseNode


class OutputNode(BaseNode):
    '''Output node'''

    bl_idname = 'OutputNode'
    bl_label = 'Output Node'
    bl_icon = 'NODE'

    ops_type : bpy.props.StringProperty(name='ops_type', default='')


    def is_output_node(self):
        return True


    def display(self, display_flag=False):
        # super().display(display_flag)

        outputstream_socket = self.get_first_outputstream_socket()
        outputstream_socket.hide = True
