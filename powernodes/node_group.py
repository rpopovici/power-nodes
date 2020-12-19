import bpy
from bpy.types import NodeCustomGroup
from mathutils import Vector
import nodeitems_utils

from . base_node import BaseNode
from . node_tree import PowerTree
from . utils.utils import context_override
from . utils.node_utils import get_active_node_path, get_active_node_group


class NestedPowerTree(bpy.types.NodeTree):
    """ Nested PowerTree class """
    bl_idname = 'NestedPowerTree'
    bl_label = "Nested Power Tree"
    bl_icon = 'NODETREE'

    @classmethod
    def poll(cls, context):
        """ Exclude from node tree windows manager """
        return False


class PowerGroupNode(NodeCustomGroup, BaseNode):
    """ Power Group node """
    bl_idname = 'PowerGroupNode'
    bl_label = 'Group Node'
    bl_icon = 'FILE_FOLDER'


    @classmethod
    def poll(cls, tree):
        return tree.bl_idname == "PowerTree"


    def init(self, context):
        super().init(context)


    def mirror_node_state(self, node):
        self.preview_name = node.preview_name


    def mirror_from_incoming(self):
        for socket in self.inputs:
            if socket.is_linked:
                other = socket.links[0].from_socket
                socket.mirror_from_socket(other)


    def mirror_input_sockets_across(self):
        # inputs
        for socket in self.inputs:
            group_output_socket = [output for output in self.node_tree.nodes['Group Input'].outputs if output.identifier == socket.identifier][0]
            other = group_output_socket.links[0].to_socket
            group_output_socket.mirror_from_socket(socket)
            other.mirror_from_socket(socket)
            group_output_socket.update_tag()
            other.update_tag()


    def mirror_output_sockets_across(self):
        # outputs
        for socket in self.outputs:
            group_input_socket = [input for input in self.node_tree.nodes['Group Output'].inputs if input.identifier == socket.identifier][0]
            other = group_input_socket.links[0].from_socket
            group_input_socket.mirror_from_socket(other)
            socket.mirror_from_socket(other)
            self.mirror_node_state(other.node)
            group_input_socket.update_tag()
            socket.update_tag()


    def process(self):
        self.needs_processing = False
        self.is_processing = True

        if self.node_tree:
            self.mirror_from_incoming()
            self.mirror_input_sockets_across()
            self.node_tree.process()
            self.mirror_output_sockets_across()

        self.is_processing = False


    def draw_label(self):
        return 'GROUP'


class NodeGroupCreate(bpy.types.Operator):
    """ Create group node from selection """
    bl_idname = "power.node_group_create"
    bl_label = "Create node group"


    @classmethod
    def poll(cls, context):
        space = context.space_data
        if hasattr(space, "node_tree"):
            if (space.node_tree):
                return space.tree_type == "PowerTree"
        return False


    def execute(self, context):
        # get active nodetree path
        path = get_active_node_path()
        node_tree = path[-1].node_tree

        # create new nodetree
        node_group = bpy.data.node_groups.new("GroupNodeTree", "PowerTree")

        # prepare selected nodes
        selected_nodes = []
        for node in node_tree.nodes:
            if node.select:
                if node.bl_idname in ['NodeGroupInput', 'NodeGroupOutput']:
                    node.select = False
                else:
                    selected_nodes.append(node)
        selected_len = len(selected_nodes)

        # determine the location of the group node
        group_loc = Vector((0, 0))
        input_loc = 0
        output_loc = 0
        for node in selected_nodes:
            group_loc += node.location / selected_len
            if (node.location.x < input_loc):
                input_loc = node.location.x
            if (node.location.x > output_loc):
                output_loc = node.location.x

        # create group input/output nodes
        group_input = node_group.nodes.new("NodeGroupInput")
        group_output = node_group.nodes.new("NodeGroupOutput")
        group_input.location = Vector((input_loc - 250, group_loc.y))
        group_output.location = Vector((output_loc + 250, group_loc.y))

        # copy selected nodes to clipboard
        if (selected_len > 0):
            bpy.ops.node.clipboard_copy(context_override(area_type='NODE_EDITOR'))

        # create new group node and attach the newly created nodetree
        group_node = node_tree.nodes.new("PowerGroupNode")
        group_node.location = group_loc
        group_node.node_tree = node_group

        # push new nodetree into the path
        path.append(node_group, node=group_node)

        # paste selected nodes to the new nodetree
        if (selected_len > 0):
            bpy.ops.node.clipboard_paste(context_override(area_type='NODE_EDITOR'))

        # remove selected from original nodetree
        for node in selected_nodes:
            node_tree.nodes.remove(node)

        return {"FINISHED"}


class NodeGroupEdit(bpy.types.Operator):
    """ TAB in and out from group node """
    bl_idname = "power.node_group_edit"
    bl_label = "Switch to node group"


    def execute(self, context):
        path = get_active_node_path()
        node_tree = path[-1].node_tree
        node = node_tree.nodes.active

        if len(path) > 1:
            parent_tree = path[-2].node_tree

        if hasattr(node, "node_tree"):
            if (node.node_tree):
                # push new nodetree into stack
                path.append(node.node_tree, node=node)
        elif len(path) > 1:
            if node is not None:
                node_tree.nodes.active = None
                if node.bl_idname not in ['NodeGroupInput', 'NodeGroupOutput']:
                    node.is_active = False
                    node._update()
            path.pop()

            if parent_tree:
                parent_tree.needs_update = True
                parent_tree.update_tag()

        return {"FINISHED"}


keymaps = []

def register():
    # create keymap
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name="Node Editor", space_type='NODE_EDITOR')
    kmi = km.keymap_items.new(NodeGroupCreate.bl_idname, 'G', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new(NodeGroupEdit.bl_idname, 'TAB', 'PRESS')
    keymaps.append(km)

def unregister():
    # remove keymap
    wm = bpy.context.window_manager
    for km in keymaps:
        wm.keyconfigs.addon.keymaps.remove(km)
    keymaps.clear()
