import bpy
import nodeitems_utils
from nodeitems_utils import NodeItem, NodeCategory

from . node_register import register_node_classes, unregister_node_classes


class PowerNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == "PowerTree"


def get_categories():
    POWER_CATEGORIES = [
        #     PowerNodeCategory("POWER_CATEGORY", "Primitives", items = [
        #     # NodeItem("AttributeNode"),
        #     # NodeItem("CleanNode"),
        #     # NodeItem("CopyNode"),
        #     # NodeItem("DeleteNode"),
        #     # NodeItem("NoiseNode"),
        #     # NodeItem("PowerGroupNode"),
        #     # NodeItem("PowerNode"),
        #     # NodeItem("PrimitiveNode"),
        #     # NodeItem("RaycastNode"),
        #     # NodeItem("ScatterNode"),
        #     # NodeItem("SelectNode"),
        #     # NodeItem("SortNode"),
        # ]),
        PowerNodeCategory("POWER_MISC_CATEGORY", "Layout", items = [
            NodeItem("NodeFrame"),
            NodeItem("NodeReroute"),
            NodeItem("NodeGroupInput"),
            NodeItem("NodeGroupOutput"),
        ]),
    ]

    return POWER_CATEGORIES


def draw_power_nodes_header(self, context):
    if context.space_data.tree_type != "PowerTree":
        return
    if context.space_data.node_tree:
        self.layout.prop(context.space_data.node_tree, "show_preview", text="Preview")


def load_node_categories(categories_map):
    categories = get_categories()
    for key, classes in categories_map.items():
        items = [NodeItem(class_bl_idname) for class_bl_idname in sorted(classes)]
        categories.append(PowerNodeCategory("POWER_" + key, key, items=items),)
    return categories


def register():
    bpy.types.NODE_HT_header.append(draw_power_nodes_header)

    categories_map = register_node_classes()
    categories = load_node_categories(categories_map)

    nodeitems_utils.register_node_categories("POWER_CATEGORIES", categories)


def unregister():
    bpy.types.NODE_HT_header.remove(draw_power_nodes_header)
    unregister_node_classes()
    nodeitems_utils.unregister_node_categories("POWER_CATEGORIES")
