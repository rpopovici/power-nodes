import bpy
import bmesh
import math
from bpy.props import BoolProperty, IntProperty, FloatProperty, PointerProperty, StringProperty
import functools
from uuid import uuid4

from . ops import initialize_default_collections, link_to_collection, unlink_from_collection, clone_object, delete_object

from . draw import copy_offscreen_to_image, PREVIEW_COLLECTIONS
from . utils.utils import random_color, change_viewport_shading
from . sockets import init_node_sockets, object_poll
from . handlers import get_rendering_flag
from . utils.node_utils import get_active_node_group


def update_active_node(node_tree_name, node_name):
    active_node_group = get_active_node_group()

    if active_node_group and active_node_group.name == node_tree_name:
        if len(bpy.data.node_groups) > 0 and node_tree_name in bpy.data.node_groups:
            node_tree = bpy.data.node_groups.get(node_tree_name)
            if node_name in node_tree.nodes:
                node = node_tree.nodes[node_name]
                if node and node_tree.nodes.active:
                    # is_active = self == self.get_node_tree().nodes.active # slow because of deep comparison
                    is_active = node.name == node_tree.nodes.active.name
                    if node.is_active != is_active:
                        node.is_active = is_active


class BaseNode:
    '''Base node'''

    bl_idname = 'BaseNode'
    bl_label = 'Base Node'
    bl_icon = 'NODE'

    bl_width_default = 200
    bl_height_default = 200

    needs_update : BoolProperty(default=False)
    needs_processing : BoolProperty(default=False)
    needs_display : BoolProperty(default=False)

    always_display : BoolProperty(default=False)

    is_active : BoolProperty(default=False, update=lambda self, context: self._update())
    is_processing : BoolProperty(default=False)
    it_displays : BoolProperty(default=False)

    path_to_node : bpy.props.StringProperty(name='path_to_node', default='')

    preview_name : bpy.props.StringProperty(name='preview_name', default='')

    output_color : bpy.props.FloatVectorProperty(name="output_color", subtype='COLOR', size=4, default=(1.0, 1.0, 1.0, 1.0), min=0.0, max=1.0)

    ops_type : bpy.props.StringProperty(name='ops_type', default='NONE')

    node_label : bpy.props.StringProperty(name='node_label', default='NODE')

    i_d: StringProperty(name='id')

    @property
    def id(self):
        """ Node identifier """
        if not self.i_d:
            self.i_d = uuid4().hex
        return self.i_d


    @classmethod
    def poll(cls, tree):
        # this node is only available in trees of the 'PowerTree'
        return tree.bl_idname == 'PowerTree'


    def poll_instance(self, tree):
        # this node is only available in trees of the 'PowerTree'
        return tree.bl_idname == 'PowerTree'


    def init(self, context):
        self.path_to_node = self.path_from_id()

        self.output_color = random_color()

        self.use_custom_color = True

        # self.inputs[0].link_limit = 2

        initialize_default_collections()


    def copy(self, node):
        self.i_d = ''
        print("New node ", self.name, "copied from", node.name)


    def free(self):
        print("Removing node: ", self.name)
        inputstream_socket = self.get_first_inputstream_socket()
        outputstream_socket = self.get_first_outputstream_socket()
        input_objects = self.get_items_from_stream_socket(inputstream_socket)
        output_objects = self.get_items_from_stream_socket(outputstream_socket)

        # put back original object if input node
        if self.is_input_node() and input_objects and len(input_objects) > 0:
            for input_object in input_objects:
                input_object.display_type = 'TEXTURED'
                #make_active(self.input_objects)
                #self.input_objects.hide_viewport = False

        # unlink if output
        if output_objects and len(output_objects) > 0:
            for output_object in output_objects:
                delete_object(output_object)

        if inputstream_socket and outputstream_socket and inputstream_socket.links and outputstream_socket.links:
            from_socket = inputstream_socket.links[0].from_socket
            to_socket = outputstream_socket.links[0].to_socket

            self.get_node_tree().links.new(from_socket, to_socket)


    # we want to avoid the native callback because is being called even from unrelated events
    # def update(self):
    #     pass


    # update on related events
    def _update(self):
        # ensure is_active is up to date
        node_tree = self.get_node_tree()
        if node_tree.nodes.active:
            self['is_active'] = self.name == node_tree.nodes.active.name

        # check needs display
        if self.is_active or self.is_output_node():
            self.needs_display = True
        else:
            self.needs_display = False

        # force node tree update
        self.needs_update = True
        self.get_node_tree().update()

        # update background color
        self.draw_color()


    # update from evaluated depsgraph
    def update_from_edg(self, context=None, edg=None):
        # dg events fire in the same run loop for modifiers and ops
        # we have to deffer their processing for later to avoid infinite loop
        if not self.is_processing:
            self.needs_processing = True
        self._update()


    # update on socket changes
    def update_from_socket(self, socket, context=None):
        if self.is_processing:
            return
        self.needs_processing = True
        self._update()


    # update on modal GUI events
    def update_from_event(self, context=None, event=None, payload=None):
        self.needs_processing = True
        self._update()


    # update from operator type change
    def update_from_op_type(self, socket, context):
        pass


    # update from active node change
    def update_active(self):
        active = self.get_node_tree().nodes.active
        if active is None:
            return
        if (self.is_active and self.name != active.name) or (not self.is_active and self.name == active.name):
            # hack needed to notify active change
            update_active_node_call = functools.partial(update_active_node, self.get_node_tree().name, self.name)
            bpy.app.timers.register(update_active_node_call, first_interval=0.01)


    def socket_value_update(self, context):
        pass


    def insert_link(self, link):
        EXCEPT_LIST = ['InputStreamSocket', 'OutputStreamSocket', 'NodeSocketVirtual']
        if (link.from_socket.bl_idname != link.to_socket.bl_idname and not
            (link.from_socket.bl_idname in EXCEPT_LIST and
            link.to_socket.bl_idname in EXCEPT_LIST)):
            # reject invalid links
            if self.name == link.from_node.name:
                self.get_node_tree().invalid_links.add(link)

        if self.name == link.from_node.name:
            # input node
            self.update_from_socket(link.from_socket)
        elif self.name == link.to_node.name:
            # output node
            self.update_from_socket(link.to_socket)
            self.get_node_tree().nodes.active = self

            if self.ops_type in ['OUTPUT', 'PASS'] and self.bl_idname != 'PowerGroupNode':
                if len([input for input in self.inputs if input.is_linked == False and input.bl_idname == 'InputStreamSocket']) == 1:
                    self.inputs.new('InputStreamSocket', link.to_socket.name)
                    self.inputs.move(from_index = len(self.inputs) - 1, to_index = 1)


    def remove_link(self, link):
        pass


    def get_node_tree(self):
        # apparently parent node_tree can be accessed via id_data attr
        return self.id_data


    def get_inputstream_sockets(self):
        return [input for input in self.inputs if input.bl_idname == 'InputStreamSocket']


    def get_first_inputstream_socket(self):
        for input in self.inputs:
            if input.bl_idname == 'InputStreamSocket':
                return input
        return None


    def get_second_inputstream_socket(self):
        count = 0
        for input in self.inputs:
            if input.bl_idname == 'InputStreamSocket':
                count += 1
                if count == 2:
                    return input
        return None


    def get_first_outputstream_socket(self):
        for output in self.outputs:
            if output.bl_idname == 'OutputStreamSocket':
                return output
        return None


    def get_items_from_socket(self, socket):
        if not socket:
            return None
        return socket.other.prop if socket.is_linked else socket.prop


    def get_items_from_stream_socket(self, socket):
        def collection_objects(collection):
            objects = []
            for child in collection.children:
                objects.extend(collection_objects(child))
            objects.extend(collection.objects[:])
            return objects

        if not socket:
            return []
        input_socket = socket.other if socket.is_linked and not socket.is_output else socket
        items_stream = input_socket.prop if input_socket else []
        objects = set()
        for item in items_stream:
            if isinstance(item.object, bpy.types.Collection):
                # collection
                cobjects = collection_objects(item.object)
                cobjects = [obj for obj in cobjects if object_poll(self, obj)]
                objects.update(cobjects)
            else:
                # individual objects
                objects.add(item.object)
        objects = [obj for obj in objects if obj]
        return objects


    def set_items_to_stream_socket(self, socket, items):
        socket.prop.clear()
        for item in items:
            coll_item = socket.prop.add()
            coll_item.object = item
            coll_item.name = item.name
            coll_item.type = item.type


    def is_input_node(self):
        inputstream_socket = self.get_first_inputstream_socket()
        return inputstream_socket and (not inputstream_socket.is_linked)


    def is_output_node(self):
        outputstream_socket = self.get_first_outputstream_socket()
        return outputstream_socket and (not outputstream_socket.is_linked)


    def get_options_from_inputs(self, sockets=[]):
        options = {}
        for socket in sockets:
            if socket.bl_idname in ['InputStreamSocket', 'OutputStreamSocket']:
                continue
            if socket.is_linked:
                options[socket.prop_name] = socket.other.prop
            else:
                options[socket.prop_name] = socket.prop
        return options


    def owns_object(self, obj):
        if '_pn_node_tag_' in obj:
            return obj['_pn_node_tag_'] == self.id
        return False


    def process(self, MODULE=None, OPSCOPE=None):
        self.needs_processing = False
        self.is_processing = True

        # process node
        inputstream_sockets = self.get_inputstream_sockets()
        outputstream_socket = self.get_first_outputstream_socket()

        op_inputs = []
        for inputstream_socket in inputstream_sockets:
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
            obj.name = obj.name.replace('CLONE_', 'OUT_')
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
        else:
            self.preview_name = ''

        self.is_processing = False


    def display(self, display_flag=False):
        inputstream_socket = self.get_first_inputstream_socket()
        outputstream_socket = self.get_first_outputstream_socket()
        input_objects = self.get_items_from_stream_socket(inputstream_socket)
        output_objects = self.get_items_from_stream_socket(outputstream_socket)
        if not output_objects or len(output_objects) == 0:
            return

        if self.is_input_node() and input_objects:
            for input_obj in input_objects:
                input_obj.display_type = 'WIRE'
                #col = random_color()
                #self.input_objects.color = (col[0], col[1], col[3], 0.1)
                #self.input_objects.hide_viewport = True

        if display_flag or self.always_display:
            self.it_displays = True
            for output_object in output_objects:
                # # link to collection
                output_object.display_type = 'SOLID' # 'TEXTURED'
                output_object.hide_select = True
                # output_objects.data.use_auto_smooth = 1
                # output_objects.data.auto_smooth_angle = math.pi/4  # 45 degrees
                #outputstream_socket.object_ref.show_in_front = True
                #outputstream_socket.object_ref.show_wire = True
                link_to_collection(output_object, 'POWER_NODES')
        else:
            self.it_displays = False
            for output_object in output_objects:
                # # unlink from collection
                unlink_from_collection(output_object, 'POWER_NODES')

        #bpy.context.view_layer.update()


    # # Additional buttons displayed on the node.
    def draw_buttons(self, context, layout):
        layout.separator()

        global PREVIEW_COLLECTIONS

        preview_name = self.preview_name
        if preview_name:
            power_icons = PREVIEW_COLLECTIONS['POWER_THUMBNAILS']
            if preview_name in power_icons:
                icon = power_icons[preview_name]
                layout.template_icon(icon.icon_id, scale=5.0)

        # hack required to update the active node from UI
        self.update_active()


    # # Detail buttons in the sidebar.
    # # If this function is not defined, the draw_buttons function is used instead
    def draw_buttons_ext(self, context, layout):
        layout.separator()


    # Explicit user label overrides this, but here we can define a label dynamically
    def draw_label(self):
        return self.node_label


    def draw_color(self):
        # ui = bpy.context.preferences.themes[0].user_interface
        theme = bpy.context.preferences.themes[0]
        color = theme.node_editor.node_backdrop[:3]

        if self.is_active:
            self.color = [color[0] * 1.7, color[1] * 1.7, color[2] * 0.9]
        else:
            self.color = [x * 0.8 for x in color]
