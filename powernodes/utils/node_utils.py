import bpy


def node_trees(name='PowerTree'):
    return [node_group for node_group in bpy.data.node_groups if node_group.bl_idname == name]


def find_socket(node_group_name, path_to_socket):
    if len(bpy.data.node_groups) > 0 and node_group_name in bpy.data.node_groups:
        node_tree = bpy.data.node_groups.get(node_group_name)
        socket = node_tree.path_resolve(path_to_socket)
        return socket
    return None


def get_active_node_path():
    for area in bpy.context.window.screen.areas:
        if area.type == 'NODE_EDITOR':
            for space in area.spaces:
                if space.type == 'NODE_EDITOR':
                    return space.path

    return None


def get_active_node_group():
    path = get_active_node_path()
    if len(path) > 0:
        active_node_group = path[-1].node_tree
        return active_node_group

    return None


def socket_for_object(obj=None, node_group={}):
    for node in node_group.nodes:
        for socket in node.inputs:
            if socket.bl_idname == 'InputStreamSocket':
                if socket.prop:
                    items = [item.object.name for item in socket.prop if item.object]
                    if obj.name in items:
                        return socket

    for node in node_group.nodes:
        for socket in node.outputs:
            if socket.bl_idname == 'OutputStreamSocket':
                if obj.name in [item.object.name for item in socket.prop if item.object]:
                    return socket

    return None


def node_for_object(obj=None, node_group={}):
    socket = socket_for_object(obj=obj, node_group=node_group)
    if socket:
        if not socket.is_output:
            return socket.node

    return None


def object_poll(self, object):
    if ((object.type in ['EMPTY', 'CURVE', 'FONT', 'LATTICE', 'MESH', 'META', 'SURFACE', 'POINTCLOUD', 'VOLUME']) and
        (object.users > 0) and
        not object.hide_viewport and
        not object.hide_get() and
        ('OUT_' not in object.name) and
        (not ' ' in object.name)):
        return True

    return False


def collection_poll(self, collection):
    if isinstance(collection, bpy.types.Collection):
        return collection.name not in ['POWER_NODES', 'SHADOW_NODES']

    return False
