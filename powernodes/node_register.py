import bpy
import importlib
import inspect
from pathlib import Path

from . base_node import BaseNode
from . sockets import init_node_sockets
from .. auto_load import iter_submodule_names

DYNAMIC_CLASSES = []

EXCLUDE_NODES = []


# overloaded BaseNode.init
def init(self, context, MODULE):
    super(self.__class__, self).init(context)
    # BaseNode.init(context)
    init_node_sockets(self, self.ops_type, MODULE)


# overloaded BaseNode.update_from_op_type
def update_from_op_type(self, socket, context, MODULE):
    self.ops_type = socket.items
    init_node_sockets(self, self.ops_type, MODULE)
    self.needs_processing = True
    self._update()


# overloaded BaseNode.process
def process(self, MODULE, OPSCOPE):
    super(self.__class__, self).process(MODULE=MODULE, OPSCOPE=OPSCOPE)
    # BaseNode.process(MODULE=MODULE, OPSCOPE=OPSCOPE)


def register_dynamic_class(class_name, class_label, base_class, ops_type, module, operators):
    global DYNAMIC_CLASSES

    def get_icon(module, ops_type):
        icon = 'NODE'
        icons = [item[3] for item in module['items'] if item[0] == ops_type]
        if len(icons) > 0:
            icon = icons[0]
        return icon

    # register class dynamically
    DynamicClass = type(class_name, (bpy.types.Node, base_class,), {
        # constructor
        "init": lambda self, context: init(self, context, module),

        # type hints
        '__annotations__': {
            'ops_type': (bpy.props.StringProperty, {'name': 'ops_type', 'default': ops_type}),
            'node_label': (bpy.props.StringProperty, {'name': 'node_label', 'default': class_label}),
            },

        # fields
        'bl_idname': class_name,
        'bl_label': class_label,
        'bl_icon': get_icon(module, ops_type),

        # methods
        'update_from_op_type': lambda self, socket, context: update_from_op_type(self, socket, context, module),
        'process': lambda self: process(self, module, operators),
    })

    DYNAMIC_CLASSES.append(DynamicClass)
    bpy.utils.register_class(DynamicClass)


def register_node_classes():
    module_path = Path(__file__).parent
    modules = {name for name in iter_submodule_names(module_path) if 'nodes.' in name and '_definition' in name}

    categories = {}
    for name in sorted(list(modules)):
        module_name = name.replace('nodes.', '').replace('_definition', '')
        module_key = module_name.upper() + '_MODULE'
        operators_module = name.replace('nodes', 'operators').replace('_definition', '')
        node_name = name.replace('definition', 'node')

        if module_name in EXCLUDE_NODES:
            continue

        module = importlib.import_module(".powernodes." + name, module_path.parent.name)
        operators = importlib.import_module(".powernodes." + operators_module, module_path.parent.name)
        BaseClass = BaseNode

        node_spec = importlib.util.find_spec(".powernodes." + node_name, package=module_path.parent.name)
        if node_spec:
            # overload base class if overloaded class exists in module
            node_module = importlib.import_module(".powernodes." + node_name, module_path.parent.name)
            classes = [m[1] for m in inspect.getmembers(node_module, inspect.isclass) if m[1].__module__ == node_module.__name__]
            if len(classes) > 0:
                BaseClass = classes[0]

        group_name = module_name.capitalize()
        for key, node_item in module.__dict__[module_key]['definition'].items():
            class_name = group_name + key.lower().capitalize() + 'Node'
            node_title = node_item['label']
            register_dynamic_class(class_name, node_title, BaseClass, key, module.__dict__[module_key], operators.__dict__)

            if group_name not in categories:
                categories[group_name] = []
            categories[group_name].append(class_name)

    return categories


def unregister_node_classes():
    for cls in reversed(DYNAMIC_CLASSES):
        bpy.utils.unregister_class(cls)
