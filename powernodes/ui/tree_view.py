import bpy

from bpy.props import CollectionProperty, IntProperty, BoolProperty, StringProperty, PointerProperty
from bpy.types import PropertyGroup

from . icons import require_icon
from .. utils.node_utils import find_socket, collection_poll, object_poll
from .. utils.utils import ui_scale

ICON_TYPE_MAP = {
            'UNKNOWN': 'ERROR',
            'COLLECTION': 'OUTLINER_COLLECTION',
            'EMPTY': 'EMPTY_DATA',
            'CURVE': 'OUTLINER_OB_CURVE',
            'FONT': 'OUTLINER_OB_FONT',
            'GPENCIL': 'GP_SELECT_STROKES',
            'LATTICE': 'OUTLINER_OB_LATTICE',
            'MESH': 'OUTLINER_OB_MESH',
            'META': 'OUTLINER_OB_META',
            'POINTCLOUD': 'OUTLINER_OB_POINTCLOUD',
            'SURFACE': 'OUTLINER_OB_SURFACE',
            'VOLUME': 'OUTLINER_OB_VOLUME',
            'TRASH': 'TRASH'
}


class PowerTreeNode(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(default='')
    type: bpy.props.StringProperty(default='UNKNOWN')
    parent_index : bpy.props.IntProperty(default=-1)
    child_count: bpy.props.IntProperty(default=0)
    expanded: bpy.props.BoolProperty(default=False)
    selected: bpy.props.BoolProperty(default=False)


class PowerListItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(default='')
    icon: bpy.props.StringProperty(default='UNKNOWN')
    node_index : bpy.props.IntProperty(default=-1)
    child_count: bpy.props.IntProperty(default=0)
    depth: bpy.props.IntProperty(default=0)
    expanded: bpy.props.BoolProperty(default=False)
    selected: bpy.props.BoolProperty(default=False)


def add_node(tree, name='', type='', parent_index=-1, child_count=0, expanded=True, selected=False):
    node = tree.add()
    node.name = name
    node.type = type
    node.parent_index = parent_index
    node.child_count = child_count
    node.expanded = expanded
    node.selected = selected


def add_item(list, name='', icon='', node_index=-1, child_count=0, depth=0, selected=True, expanded=False):
    item = list.add()
    item.name = name
    item.icon = icon
    item.node_index = node_index
    item.child_count = child_count
    item.depth = depth
    item.selected = selected
    item.expanded = expanded


def load_collection(tree, collection, parent_index=-1):
    add_node(tree, name=collection.name, type='COLLECTION', parent_index=parent_index)
    collection_index = len(tree) - 1

    if parent_index >= 0:
        tree[parent_index].child_count = tree[parent_index].child_count + 1

    for child_collection in collection.children:
        if collection_poll(None, child_collection):
            load_collection(tree, child_collection, collection_index)

    count = 0
    for obj in collection.objects:
        if object_poll(None, obj):
            add_node(tree, name=obj.name, type=obj.type, parent_index=collection_index)
            count += 1

    tree[collection_index].child_count = tree[collection_index].child_count + count


def load_power_tree_from_database(powertree):
    powertree.clear()
    load_collection(powertree, bpy.context.scene.collection)


def is_expandend(tree, index):
    if index == -1:
        return tree[index].expanded

    expanded = True
    while index >= 0:
        expanded = expanded and tree[index].expanded
        index = tree[index].parent_index
    return expanded


def calc_depth(tree, index):
    depth = 0
    while tree[index].parent_index >= 0:
        depth = depth + 1
        index = tree[index].parent_index
    return depth


def update_power_list_from_tree(powerlist, powertree):
    powerlist.clear()
    for index, node in enumerate(powertree):
        expanded = is_expandend(powertree, node.parent_index)
        if node.parent_index == -1 or expanded:
            depth = calc_depth(powertree, index)
            add_item(powerlist, name=node.name, icon=ICON_TYPE_MAP[node.type], node_index=index, child_count=node.child_count, depth=depth, selected=node.selected, expanded=node.expanded)


class PowerTreeItem_Expand(bpy.types.Operator):
    bl_idname = "object.powertree_expand"
    bl_label = "Expand Tree"

    item_index: IntProperty(default=0)

    def execute(self, context):
        powerlist = bpy.context.scene.pn_list
        powertree = bpy.context.scene.pn_tree

        item = powerlist[self.item_index]
        powertree[item.node_index].expanded = not powertree[item.node_index].expanded
        bpy.context.scene.pn_list_index = item.node_index

        update_power_list_from_tree(powerlist, powertree)

        return {'FINISHED'}


class PowerTreeItem_Select(bpy.types.Operator):
    bl_idname = "object.powertree_select"
    bl_label = "Select Object"

    item_index: IntProperty(default=0)

    def execute(self, context):
        powerlist = bpy.context.scene.pn_list
        powertree = bpy.context.scene.pn_tree

        item = powerlist[self.item_index]
        powerlist[self.item_index].selected = not powerlist[self.item_index].selected
        powertree[item.node_index].selected = not powertree[item.node_index].selected
        bpy.context.scene.pn_list_index = item.node_index

        path_to_socket = bpy.context.scene.pn_path_to_socket
        node_group_name = bpy.context.scene.pn_node_group_name
        socket = find_socket(node_group_name, path_to_socket)
        if socket:
            socket.prop.clear()
            for node in powertree:
                if not node.selected:
                    continue
                coll_item = socket.prop.add()
                if node.type == 'COLLECTION':
                    coll_item.object = bpy.data.collections.get(node.name)
                else:
                    coll_item.object = bpy.data.objects.get(node.name)
                coll_item.name = node.name
                coll_item.type = node.type
            socket.update_tag(context)

        return {'FINISHED'}


class POWERTREEITEM_UL_basic(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        self.use_filter_show = True
        # self.filter_name = ''

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.emboss = 'NONE'

            for idx in range(item.depth):
                row.label(icon='BLANK1')

            if item.child_count == 0:
                row.label(icon='BLANK1')
            elif item.expanded:
                op = row.operator(PowerTreeItem_Expand.bl_idname, text='', icon='TRIA_DOWN')
                op.item_index = index
            else:
                op = row.operator(PowerTreeItem_Expand.bl_idname, text='', icon='TRIA_RIGHT')
                op.item_index = index

            row.label(text=item.name, icon=item.icon)

            if index > 0:
                # exclude master collection
                checkbox_icon = 'CHECKBOX_HLT' if item.selected else 'CHECKBOX_DEHLT'
                op = row.operator(PowerTreeItem_Select.bl_idname, text='', icon=checkbox_icon)
                op.item_index = index


class SCENE_PT_powertree(bpy.types.Panel):

    bl_label = "Power List Tree"
    bl_idname = "SCENE_PT_powernodes"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Power Category"

    def draw(self, context):
        layout = self.layout

        layout.label(text='Link Objects')
        row = layout.row()
        row.template_list("POWERTREEITEM_UL_basic", "", bpy.context.scene, "pn_list", bpy.context.scene, "pn_list_index", sort_lock = True, rows=10)


class OutlinerOperator(bpy.types.Operator):
    """ Outliner object """
    bl_idname = "node.outliner_operator"
    bl_label = "Outliner Operator"
    bl_options = {'REGISTER', 'UNDO'}

    tooltip: bpy.props.StringProperty()
    path_to_socket : StringProperty(default='')
    node_group_name : StringProperty(default='')

    @classmethod
    def description(cls, context, properties):
        return properties.tooltip

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        bpy.context.scene.pn_path_to_socket = self.path_to_socket
        bpy.context.scene.pn_node_group_name = self.node_group_name

        load_power_tree_from_database(bpy.context.scene.pn_tree)

        socket = find_socket(self.node_group_name, self.path_to_socket)
        if socket:
            selected_items = [item.name + item.type for item in socket.prop]
            all_items = [node.name + node.type for node in bpy.context.scene.pn_tree]
            for index, item_key in enumerate(all_items):
                if item_key in selected_items:
                    bpy.context.scene.pn_tree[index].selected = True

        update_power_list_from_tree(bpy.context.scene.pn_list, bpy.context.scene.pn_tree)

        # return wm.invoke_props_dialog(self, width=300)
        mouse_x, mouse_y = event.mouse_x, event.mouse_y
        bpy.context.window.cursor_warp(mouse_x - ui_scale() * 300, mouse_y -  ui_scale() * 20)
        ret = wm.invoke_popup(self, width=300)
        bpy.context.window.cursor_warp(mouse_x, mouse_y)
        return ret

    def draw(self, context):
        layout = self.layout
        SCENE_PT_powertree.draw(self, context)


def register():
    # define custom data tree
    bpy.types.Scene.pn_tree = bpy.props.CollectionProperty(type=PowerTreeNode)
    bpy.types.Scene.pn_list = bpy.props.CollectionProperty(type=PowerListItem)
    bpy.types.Scene.pn_list_index = IntProperty()
    bpy.types.Scene.pn_path_to_socket = StringProperty(default='')
    bpy.types.Scene.pn_node_group_name = StringProperty(default='')


def unregister():
    del bpy.types.Scene.pn_tree
    del bpy.types.Scene.pn_list
    del bpy.types.Scene.pn_list_index
    del bpy.types.Scene.pn_path_to_socket
    del bpy.types.Scene.pn_node_group_name
