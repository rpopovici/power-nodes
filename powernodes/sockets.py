import math
from mathutils import Vector, Matrix

import bpy
from bpy.props import CollectionProperty, BoolProperty, BoolVectorProperty, \
    FloatVectorProperty, IntProperty, FloatProperty, EnumProperty, PointerProperty, StringProperty
from bpy.types import PropertyGroup
from bpy.types import NodeTree, NodeSocket, NodeSocketStandard, NodeSocketInterface

from . definition import ENUM_GLOBALS
from . parse import extract_tokens
from . utils.utils import matrix_flatten, ui_scale
from . utils.node_utils import find_socket, collection_poll, object_poll
from . ui.tree_view import OutlinerOperator, ICON_TYPE_MAP


SOCKET_COLORS = {
    "BoolSocket": (0.7, 1.0, 0.7, 1.0),
    "FloatSocket": (0.7, 1.0, 0.7, 1.0),
    "IntSocket": (0.7, 1.0, 0.7, 1.0),
    "EnumSocket": (0.7, 1.0, 0.7, 1.0),
    "ExpressionSocket": (0.9, 0.2, 0.2, 1),
    "StringSocket": (0.7, 0.8, 0.9, 1),
    "QuaternionSocket": (0.9, 0.5, 0.6, 1.0),
    "ColorSocket": (0.9, 0.7, 0.0, 1.0),
    "VectorSocket": (0.4, 0.6, 0.8, 1.0),
    "MatrixSocket": (0.2, 0.5, 0.8, 1.0),
    "ObjectSocket": (1.0, 0.5, 0.1, 1.0),
    "OutputStreamSocket": (1.0, 0.5, 0.1, 1.0),
    "OutputSocket": (1.0, 0.5, 0.1, 1.0),
    "InputStreamSocket": (1.0, 0.5, 0.1, 1.0),
    "MeshSocket": (0.1, 0.6, 0.4, 1.0),
}


EXPRESSION_PRESETS = {
    ('$select', 'Selected', ''),
    ('not $select', 'Invert selected', ''),
    ('True', 'Everything', ''),
    ('len($self.verts) > 4', 'NGons', ''),
    ('$self.is_boundary', 'Boundary', ''),
    ('$self.is_manifold', 'Manifold', ''),
}


def map_display_shape(socket):
    return 'SQUARE' if socket.bl_idname in ['InputStreamSocket', 'OutputStreamSocket', 'OutputSocket', 'ObjectSocket'] else 'DIAMOND'


def enum_index(value, items_path):
    enum_indices = [index for index, item in enumerate(ENUM_GLOBALS[items_path]) if value == item[0]]
    if len(enum_indices) > 0:
        return enum_indices[0]
    return 0


def set_collection_property(to_coll, from_coll):
    to_coll.clear()
    for item in from_coll:
        coll_item = to_coll.add()
        coll_item.name = item.name
        coll_item.object = item.object
        coll_item.type = item.type


def initialize_socket_from_definition(socket, node, entry, module_name):
        socket.prop_name = entry['name']
        socket.prop_label = entry['label']
        socket.prop_type = entry['type']

        if 'icon' in entry:
            socket.prop_icon = entry['icon']
        if 'enabled_by' in entry:
            socket.prop_enabled_by = entry['enabled_by']
        if 'expand' in entry:
            socket.prop_expand = entry['expand']
        if entry['type'] in ['Enum', 'OutputStream']:
            socket.enum_items = module_name + node.ops_type + '.' + entry['name']
        if 'min' in entry:
            socket.prop_min = entry['min']
        if 'max' in entry:
            socket.prop_max = entry['max']

        if 'default' in entry:
            # use socket['prop'] to bypass setter
            if entry['type'] == 'Enum':
                socket['prop'] = enum_index(entry['default'], socket.enum_items)
            elif entry['type'] == 'OutputStream':
                socket['items'] = enum_index(entry['default'], socket.enum_items)
            elif entry['type'] == 'Matrix':
                # socket.prop_default = matrix_flatten(entry['default'])
                socket['prop'] = matrix_flatten(entry['default'])
            else:
                # socket.prop_default = entry['default']
                socket['prop'] = entry['default']


def init_node_sockets(node, op_type, MODULE):
    OPS_PROP_DEF = MODULE['definition']
    module_name = MODULE['name']
    input_group = OPS_PROP_DEF[op_type]['inputs']
    output_group = OPS_PROP_DEF[op_type]['outputs']

    # clear socket list 
    for socket in node.inputs:
        if (socket.bl_idname != 'InputStreamSocket' or 
            not (socket.is_linked or socket.prop)):
            node.inputs.remove(socket)

    # populate inputs with items
    for index, entry in enumerate(input_group):
        entry_type = entry['type']
        # reuse old items sockets
        if entry_type == 'InputStream' and len(node.inputs) > index and node.inputs[index].bl_idname == 'InputStreamSocket':
            continue
        class_name = entry_type + 'Socket'
        item = node.inputs.new(class_name, entry['name'])
        item.display_shape = map_display_shape(item)
        # item.type = 'CUSTOM'
        if item.bl_idname == 'NodeSocketUndefined':
            continue
        initialize_socket_from_definition(item, node, entry, module_name)

    # # relocate input sockets
    # indices = []
    # for index, socket in enumerate(node.inputs):
    #     if socket.bl_idname == 'InputStreamSocket':
    #         indices.append(index)
    # for count, index in enumerate(indices):
    #         node.inputs.move(from_index = index - count, to_index = len(node.inputs) - 1)

    # populate outputs with items
    for index, entry in enumerate(output_group):
        entry_type = entry['type']
        class_name = entry_type[:1].upper() + entry_type[1:] + 'Socket'
        item = node.outputs.get(entry['name'])
        if item is None:
            item = node.outputs.new(class_name, entry['name'])
            item.display_shape = map_display_shape(item)
            # item.type = 'CUSTOM'
        if item.bl_idname == 'NodeSocketUndefined':
            continue
        initialize_socket_from_definition(item, node, entry, module_name)


def find_other_socket(socket):
    if (not socket.is_linked) or (not socket.links):
        return None

    if socket.is_output:
        other = socket.links[0].to_socket
    else:
        other = socket.links[0].from_socket

    if other.node.bl_idname == 'NodeReroute':
        if socket.is_output:
            return find_other_socket(other.node.outputs[0])
        else:
            return find_other_socket(other.node.inputs[0])
    else:
        return other


def get_prop(self):
    # return self.get("prop")
    # if self.get("prop") is not None:
    try:
        return self['prop']
    except:
        print('Prop needs to be initialized!!')
        return 0


def set_prop(self, value):
    if value >= self.prop_min and value <= self.prop_max:
        self['prop'] = value


def update_prop(self, context):
    # update node on socket changes
    try:
        self.node.update_from_socket(self, context)
    except:
        pass


class SocketBaseInterface:

    def init_socket(self, node, socket, data_path):
        if node.bl_idname == 'PowerGroupNode':
            if socket.is_output:
                group_input_socket = [input for input in node.node_tree.nodes['Group Output'].inputs if input.identifier == socket.identifier][0]
                other = group_input_socket.links[0].from_socket
                group_input_socket.mirror_from_socket(other)
                socket.mirror_from_socket(other)
            else:
                group_output_socket = [output for output in node.node_tree.nodes['Group Input'].outputs if output.identifier == socket.identifier][0]
                other = group_output_socket.links[0].to_socket
                group_output_socket.mirror_from_socket(other)
                socket.mirror_from_socket(other)

            socket.update_tag()


    # def from_socket(self, node, socket):
    #     self.data_path = socket.path_from_id()
    #     self.prop = socket.prop


    # def register_properties(self, data_rna_type):
    #     pass


    def draw(self, context, layout):
        layout.label(text=self.name + ' : ' + self.bl_socket_idname)

    def draw_color(self, context):
        if self.bl_socket_idname in SOCKET_COLORS:
            return SOCKET_COLORS[self.bl_socket_idname]
        else:
            return (1.0, 1.0, 1.0, 0.5)


class SocketBase():
    prop_name : StringProperty(default='')
    prop_label : StringProperty(default='')
    prop_type : StringProperty(default='')
    prop_description : StringProperty(default='')
    prop_icon : StringProperty(default='')
    prop_enabled_by : StringProperty(default='')
    prop_expand: BoolProperty(default=False)
    prop_min: FloatProperty(default=float('-inf'))
    prop_max: FloatProperty(default=float('inf'))


    @property
    def other(self):
        return find_other_socket(self)


    def mirror_from_socket(self, socket):
        self.prop_name = socket.prop_name
        self.prop_label = socket.prop_label
        self.prop_type = socket.prop_type
        self.prop_icon = socket.prop_icon
        self.prop_enabled_by = socket.prop_enabled_by
        self.prop_expand = socket.prop_expand
        self.prop_min = socket.prop_min
        self.prop_max = socket.prop_max

        if socket.prop_type in ['Enum']:
            self.enum_items = socket.enum_items
            self['prop'] = enum_index(socket.prop, socket.enum_items)
            return

        if isinstance(socket.prop, bpy.types.bpy_prop_collection):
            set_collection_property(self.prop, socket.prop)
        else:
            self['prop'] = socket.prop


    def update_tag(self, context=None):
        update_prop(self, context)


    def draw_color(self, context, node):
        if self.bl_idname in SOCKET_COLORS:
            return SOCKET_COLORS[self.bl_idname] 
        else: 
            return (1.0, 0.5, 0.2, 0.5)


    def draw_items(self, context, layout, node, text):
        if self.prop_enabled_by:
            enable_prop, enable_values, *rest = tuple(self.prop_enabled_by.strip().split('='))
            socket_index = node.inputs.find(enable_prop)
            enable_prop_value = str(node.inputs[socket_index].prop)
            if socket_index >=0 and not enable_prop_value in enable_values:
                layout.enabled = False

        label = self.prop_label
        if self.prop_icon:
            layout.label(text='', icon=self.prop_icon)
            label = ''
        layout.prop(self, "prop", text=label, expand=self.prop_expand)


    def draw(self, context, layout, node, text):
        label = self.prop_label if self.prop_label else text

        if self.is_linked:
            layout.label(text=label)
        elif self.is_output:
            layout.label(text=label)
        else:
            self.draw_items(context, layout, node, label)


class MatrixSocketInterface(NodeSocketInterface, SocketBaseInterface):
    bl_idname = "MatrixSocketInterface"
    bl_label = "MatrixSocket"
    bl_socket_idname = "MatrixSocket"

class MatrixSocket(NodeSocket, SocketBase):
    bl_idname = "MatrixSocket"
    bl_label = "Matrix Socket"
    prop : FloatVectorProperty(name="Matrix", size=16, subtype="MATRIX", update=update_prop)


class VectorSocketInterface(NodeSocketInterface, SocketBaseInterface):
    bl_idname = "VectorSocketInterface"
    bl_label = "VectorSocket"
    bl_socket_idname = "VectorSocket"

class VectorSocket(NodeSocket, SocketBase):
    bl_idname = "VectorSocket"
    bl_label = "Vector Socket"

    prop : FloatVectorProperty(default=(0, 0, 0), size=3, subtype='XYZ', update=update_prop)


class EulerSocketInterface(NodeSocketInterface, SocketBaseInterface):
    bl_idname = "EulerSocketInterface"
    bl_label = "EulerSocket"
    bl_socket_idname = "EulerSocket"

class EulerSocket(NodeSocket, SocketBase):
    bl_idname = "EulerSocket"
    bl_label = "Euler Socket"

    prop : FloatVectorProperty(default=(0, 0, 0), size=3, subtype='EULER', update=update_prop)


class QuaternionSocketInterface(NodeSocketInterface, SocketBaseInterface):
    bl_idname = "QuaternionSocketInterface"
    bl_label = "QuaternionSocket"
    bl_socket_idname = "QuaternionSocket"

class QuaternionSocket(NodeSocket, SocketBase):
    bl_idname = "QuaternionSocket"
    bl_label = "Quaternion Socket"

    prop : FloatVectorProperty(default=(1, 0, 0, 0), size=4, subtype='QUATERNION', update=update_prop)


class ColorSocketInterface(NodeSocketInterface, SocketBaseInterface):
    bl_idname = "ColorSocketInterface"
    bl_label = "ColorSocket"
    bl_socket_idname = "ColorSocket"

class ColorSocket(NodeSocket, SocketBase):
    bl_idname = "ColorSocket"
    bl_label = "Color Socket"

    prop : FloatVectorProperty(default=(0, 0, 0, 1), size=4, subtype='COLOR', min=0, max=1, update=update_prop)


class StringSocketInterface(NodeSocketInterface, SocketBaseInterface):
    bl_idname = "StringSocketInterface"
    bl_label = "StringSocket"
    bl_socket_idname = "StringSocket"

class StringSocket(NodeSocket, SocketBase):
    bl_idname = "StringSocket"
    bl_label = "String Socket"

    prop : StringProperty(update=update_prop, description='String')

    def draw(self, context, layout, node, text):
        if self.is_linked and not self.is_output:
            layout.label(text)
        if not self.is_linked and not self.is_output:
            if self.prop_icon:
                layout.prop(self, 'prop', text='', icon=self.prop_icon)
            else:
                layout.prop(self, 'prop', text=self.prop_label)


class FloatSocketInterface(NodeSocketInterface, SocketBaseInterface):
    bl_idname = "FloatSocketInterface"
    bl_label = "FloatSocket"
    bl_socket_idname = "FloatSocket"

class FloatSocket(NodeSocket, SocketBase):
    bl_idname = "FloatSocket"
    bl_label = "Float Socket"

    prop : FloatProperty(unit ='LENGTH', get=get_prop, set=set_prop, update=update_prop)


class IntSocketInterface(NodeSocketInterface, SocketBaseInterface):
    bl_idname = "IntSocketInterface"
    bl_label = "IntSocket"
    bl_socket_idname = "IntSocket"

class IntSocket(NodeSocket, SocketBase):
    bl_idname = "IntSocket"
    bl_label = "Int Socket"

    prop : IntProperty(get=get_prop, set=set_prop, update=update_prop)


class BoolSocketInterface(NodeSocketInterface, SocketBaseInterface):
    bl_idname = "BoolSocketInterface"
    bl_label = "BoolSocket"
    bl_socket_idname = "BoolSocket"

class BoolSocket(NodeSocket, SocketBase):
    bl_idname = "BoolSocket"
    bl_label = "Bool Socket"

    prop : BoolProperty(update=update_prop)


class BoolVectorSocketInterface(NodeSocketInterface, SocketBaseInterface):
    bl_idname = "BoolVectorSocketInterface"
    bl_label = "BoolVectorSocket"
    bl_socket_idname = "BoolVectorSocket"

class BoolVectorSocket(NodeSocket, SocketBase):
    bl_idname = "BoolVectorSocket"
    bl_label = "BoolVector Socket"

    prop : BoolVectorProperty(default=(False, False, False), size=3, subtype='XYZ', update=update_prop)


class MaterialSocketInterface(NodeSocketInterface, SocketBaseInterface):
    bl_idname = "MaterialSocketInterface"
    bl_label = "MaterialSocket"
    bl_socket_idname = "MaterialSocket"

class MaterialSocket(NodeSocket, SocketBase):
    bl_idname = "MaterialSocket"
    bl_label = "MaterialVector Socket"

    prop : PointerProperty(type = bpy.types.Material, update=update_prop)

    def draw(self, context, layout, node, text):
        if self.is_linked and not self.is_output:
            layout.label(text)
        if not self.is_linked and not self.is_output:
            row = layout.row(align=True)
            row.prop_search(self, "prop", bpy.data, 'materials', text='', icon='MATERIAL_DATA')


class EnumSocketInterface(NodeSocketInterface, SocketBaseInterface):
    bl_idname = "EnumSocketInterface"
    bl_label = "EnumSocket"
    bl_socket_idname = "EnumSocket"

class EnumSocket(NodeSocket, SocketBase):
    bl_idname = "EnumSocket"
    bl_label = "Enum Socket"

    def esocket_callback(self, context):
        try:
            return ENUM_GLOBALS[self.enum_items]
        except:
            return []

    prop : EnumProperty(items=esocket_callback, update=update_prop)
    enum_items : StringProperty(default='')


def expression_item_cb(self, context):
    return globals()[self.items]

class ExpressionOperator(bpy.types.Operator):
    bl_idname = "node.expression_operator"
    bl_label = "Expression Operator"
    bl_options = {'REGISTER', 'UNDO'}
    bl_property = "items_enum"

    items_enum : bpy.props.EnumProperty(items=expression_item_cb)
    items : StringProperty(default='')

    expression : StringProperty(default='')
    path_to_socket : StringProperty(default='')
    node_group_name : StringProperty(default='')
    tooltip: bpy.props.StringProperty()

    @classmethod
    def description(cls, context, properties):
        return properties.tooltip

    def execute(self, context):
        socket = find_socket(self.node_group_name, self.path_to_socket)
        if socket:
            if self.items:
                socket.prop = self.items_enum
            else:
                socket.prop = self.expression

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        mouse_y = event.mouse_y
        # bpy.context.window.cursor_warp(event.mouse_x, event.mouse_y - ui_scale() * 20)
        if self.items:
            wm.invoke_search_popup(self)
            # bpy.context.window.cursor_warp(event.mouse_x, mouse_y)
            return {'FINISHED'}
        else:
            ret = wm.invoke_props_dialog(self, width=500)
            # bpy.context.window.cursor_warp(event.mouse_x, mouse_y)
            return ret

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'expression', text='', icon='EXPERIMENTAL')


def update_expression(self, context):
    tokens = extract_tokens(self.prop)
    full_node_data_path = 'bpy.data.node_groups["' + self.node.id_data.name + '"].' + self.node.path_from_id()
    if '$FRAME' in tokens:
        if ('_pn_node_hooks_' not in self.node.id_data or
            '$FRAME' not in self.node.id_data['_pn_node_hooks_']):
            self.node.id_data['_pn_node_hooks_'] = {'$FRAME': [full_node_data_path]}
        frame_hooks = self.node.id_data['_pn_node_hooks_']['$FRAME']
        if full_node_data_path not in frame_hooks:
            frame_hooks.append(full_node_data_path)
            self.node.id_data['_pn_node_hooks_'] = {'$FRAME': frame_hooks}

    # update prop
    update_prop(self, context)


class ExpressionSocketInterface(NodeSocketInterface, SocketBaseInterface):
    bl_idname = "ExpressionSocketInterface"
    bl_label = "Expression Socket"
    bl_socket_idname = "ExpressionSocket"

class ExpressionSocket(NodeSocket, SocketBase):
    bl_idname = "ExpressionSocket"
    bl_label = "Expression Socket"


    def esocket_callback(self, context):
        return [('EXP', self.prop if self.prop else ' ', 'Python expression', 'EXPERIMENTAL', 0)]

    prop : StringProperty(update=update_expression, description='Expression')
    exp_enum : bpy.props.EnumProperty(items=esocket_callback)

    def draw(self, context, layout, node, text):
        if self.is_linked and not self.is_output:
            layout.label(text)
        if not self.is_linked and not self.is_output:
            row = layout.row(align=True)
            exp_button = row.operator(ExpressionOperator.bl_idname, text='', icon='EXPERIMENTAL', emboss=True, depress=False)
            exp_button.expression = self.prop
            exp_button.items = ''
            exp_button.path_to_socket = self.path_from_id()
            exp_button.node_group_name = self.node.id_data.name
            exp_button.tooltip = 'Expression edit'

            row.prop(self, 'prop', text='')

            preset_button = row.operator(ExpressionOperator.bl_idname, text='', icon='DOWNARROW_HLT', emboss=True, depress=False)
            preset_button.items = 'EXPRESSION_PRESETS'
            preset_button.path_to_socket = self.path_from_id()
            preset_button.node_group_name = self.node.id_data.name
            preset_button.tooltip = 'Usual expressions'


def enum_callback(self, context):
    return [
        ("OBJECT", "Object", "Object select", "OUTLINER_OB_MESH", 0),
        ("COLLECTION", "Collection", "Collection select", "GROUP", 1),
    ]


def enum_update(self, context=None):
    pass


class IDProperty(bpy.types.PropertyGroup):
    name : bpy.props.StringProperty(name='name', default='')
    type : bpy.props.StringProperty(name='type', default='')
    object : bpy.props.PointerProperty(name="ID", type=bpy.types.ID,) # update=update_prop, poll=object_poll)

# bpy.utils.register_class(IDProperty)


class ObjectSocketInterface(NodeSocketInterface, SocketBaseInterface):
    bl_idname = "ObjectSocketInterface"
    bl_label = "ObjectSocket"
    bl_socket_idname = "ObjectSocket"

class ObjectSocket(NodeSocket, SocketBase):
    bl_idname = "ObjectSocket"
    bl_label = "Object Socket"
    bl_color = (1.0, 0.4, 0.216, 0.5)

    #object_ref: StringProperty(update=update_prop)
    object_ref : PointerProperty(name="object_ref", type=bpy.types.ID, update=update_prop, poll=object_poll)
    data_type : EnumProperty(name='Input Type', items=enum_callback, update=enum_update)

    def draw(self, context, layout, node, text):
        if not self.is_output and not self.is_linked:
            # box = layout.box()
            # row = box.row(align=True)
            # split = row.split(factor=0.2, align=True)
            # split_left = split.row(align=True)
            # split_left.prop(self, "data_type", text="", expand=False, icon_only=True)
            # split.prop_search(self, 'object_ref', bpy.data, 'objects', text=self.name)

            row = layout.row(align=True)
            row.prop(self, "data_type", text="", expand=False, icon_only=True)

            if self.data_type == 'OBJECT':
                row.prop_search(self, 'object_ref', bpy.data, 'objects', text='')
            else:
                row.prop_search(self, 'object_ref', bpy.data, 'collections', text='')
        elif not self.is_output and self.is_linked:
            layout.label(text=self.other.object_ref.name)
        else:
            #layout.label(text=text)
            layout.label(text='Output')


class OutputStreamSocketInterface(NodeSocketInterface, SocketBaseInterface):
    bl_idname = "OutputStreamSocketInterface"
    bl_label = "OutputStreamSocket"
    bl_socket_idname = "OutputStreamSocket"

class OutputStreamSocket(NodeSocket, SocketBase):
    bl_idname = "OutputStreamSocket"
    bl_label = "Output Ref Socket"

    def esocket_callback(self, context):
        if self.enum_items:
            return ENUM_GLOBALS[self.enum_items]
        else:
            return []

    def enum_prop_update(self, context):
            self.node.update_from_op_type(self, context)

    items : EnumProperty(name='Operation Type', description='Operation Type', items=esocket_callback, update=enum_prop_update)
    enum_items : StringProperty(default='')
    always_show_items : BoolProperty(default=False)

    # item refs
    prop : CollectionProperty(name='Objects', type=IDProperty)

    # def draw(self, context, layout, node, text):
    #     if (self.always_show_items or self.is_output) and node.bl_idname != 'PowerGroupNode':
    #         row = layout.row(align=True)
    #         row.prop(self, "items", text='')
    #     else:
    #         layout.label(text='Output')


class OutputSocketInterface(NodeSocketInterface, SocketBaseInterface):
    bl_idname = "OutputSocketInterface"
    bl_label = "OutputSocket"
    bl_socket_idname = "OutputSocket"

class OutputSocket(NodeSocket, SocketBase):
    bl_idname = "OutputSocket"
    bl_label = "Output Socket"


    def prop_callback(self, context):
        if self.items:
            return ENUM_GLOBALS[self.items]
        else:
            return []


    def prop_update(self, context):
        if self.callback_name:
            getattr(self.node, self.callback_name)(context)


    object_ref : PointerProperty(name="object_ref", type=bpy.types.ID, update=update_prop)
    prop : EnumProperty(items=prop_callback, update=prop_update)
    items : StringProperty(default='')
    callback_name : StringProperty(default='')
    show_prop : BoolProperty(default=False)


    def draw(self, context, layout, node, text):
        if self.show_prop:
            row = layout.row(align=True)
            row.prop(self, "prop", text='')
        else:
            layout.label(text='Output')


def search_item_cb(self, context):
    socket = find_socket(self.node_group_name, self.path_to_socket)
    if not socket:
        return []

    loaded_objs = [item.object for item in socket.prop]
    items = []
    for collection in bpy.data.collections:
        if collection_poll(self, collection):
            icon = 'TRASH' if collection in loaded_objs else 'OUTLINER_COLLECTION'
            items.append({'name': '[' + collection.name + ']', 'label': collection.name, 'type': 'COLLECTION', 'icon': icon})
            for obj in collection.objects:
                if object_poll(self, obj):
                    icon = 'TRASH' if obj in loaded_objs else obj.type
                    items.append({'name': obj.name, 'label': '    ' + obj.name, 'type': obj.type, 'icon': ICON_TYPE_MAP[icon]})

    # add objects from master collection
    for obj in bpy.context.scene.collection.objects:
        if object_poll(self, obj):
            items.append({'name': obj.name, 'label': '  ' + obj.name, 'type': obj.type, 'icon': ICON_TYPE_MAP[obj.type]})

    return [(item['name'], item['label'], '', item['icon'], index) for index, item in enumerate(items)]


class SearchOperator(bpy.types.Operator):
    bl_idname = "node.search_operator"
    bl_label = "Search Operator"
    bl_property = "items_enum"
    bl_options = {'REGISTER', 'UNDO'}

    items_enum : bpy.props.EnumProperty(items=search_item_cb)
    items : StringProperty(default='')
    path_to_socket : StringProperty(default='')
    node_group_name : StringProperty(default='')
    tooltip: bpy.props.StringProperty()

    def set_item(self, context, item):
        socket = find_socket(self.node_group_name, self.path_to_socket)
        if socket:
            if item == '':
                socket.prop.clear()
                update_prop(socket, context)
                return

            if '[' in item:
                collection_name = item.replace('[', '').replace(']', '')
                obj = bpy.data.collections.get(collection_name)
            else:
                obj = bpy.data.objects.get(item)

            loaded_objs = [item.object for item in socket.prop]
            if obj in loaded_objs:
                socket.prop.remove(loaded_objs.index(obj))
                update_prop(socket, context)
                return

            coll_item = socket.prop.add()
            coll_item.object = obj
            coll_item.name = obj.name
            if isinstance(obj, bpy.types.Collection):
                coll_item.type = 'COLLECTION'
            else:
                coll_item.type = obj.type
            update_prop(socket, context)


    @classmethod
    def description(cls, context, properties):
        return properties.tooltip


    def execute(self, context):
            self.set_item(context, self.items_enum)
            return {'FINISHED'}

    def invoke(self, context, event):
        if self.items:
            wm = context.window_manager
            mouse_y = event.mouse_y
            # bpy.context.window.cursor_warp(event.mouse_x, event.mouse_y - ui_scale() * 20)
            wm.invoke_search_popup(self)
            # bpy.context.window.cursor_warp(event.mouse_x, mouse_y)
        else:
            self.set_item(context, '')

        return {'FINISHED'}


class InputStreamSocketInterface(NodeSocketInterface, SocketBaseInterface):
    bl_idname = "InputStreamSocketInterface"
    bl_label = "InputStreamSocket"
    bl_socket_idname = "InputStreamSocket"

class InputStreamSocket(NodeSocket, SocketBase):
    bl_idname = "InputStreamSocket"
    bl_label = "Items Socket"

    def esocket_callback(self, context):
        return [(item.object.name, item.object.name, '') for item in self.prop]

    def enum_prop_update(self, context):
            update_prop(self, context)

    items_enum : EnumProperty(name='Selected Objects', description='Selected Objects', items=esocket_callback, update=enum_prop_update)

    prop : CollectionProperty(name='Objects', type=IDProperty)

    active_index : bpy.props.IntProperty()

    def draw(self, context, layout, node, text):
        if not self.is_output and not self.is_linked:
            row = layout.row(align=True)

            search_button = row.operator(OutlinerOperator.bl_idname, text='', icon='ADD', emboss=True, depress=False)
            # search_button = row.operator(SearchOperator.bl_idname, text='', icon='ADD', emboss=True, depress=False)
            # search_button.items = 'ALL'
            search_button.path_to_socket = self.path_from_id()
            search_button.node_group_name = self.node.id_data.name
            search_button.tooltip = 'Link objects'

            row.prop(self, 'items_enum', text='')

            clear_button = row.operator(SearchOperator.bl_idname, text='', icon='X', emboss=True, depress=False)
            clear_button.items = ''
            clear_button.path_to_socket = self.path_from_id()
            clear_button.node_group_name = self.node.id_data.name
            clear_button.tooltip = 'Remove all'
        elif not self.is_output and self.is_linked:
            layout.label(text='Objects')
        else:
            layout.label(text=text)
