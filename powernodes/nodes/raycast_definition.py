import bpy
from mathutils import Vector, Matrix

# Operator enum property list
# (identifier, name, description, icon, number)
RAYCAST_ITEMS = [
    ("RAYCAST", "Shrinkwrap", "Shrinkwrap", "MOD_SHRINKWRAP", 0),
]


RAYCAST_PROP_DEF = {
    "RAYCAST": {
        "label": 'Shrinkwrap',
        "inputs": [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "input1", "label": "Input", "type": "InputStream" },
            { "name": "distance", "label": "Distance", "type": "Float", "default": 1.0, 'min': -10.0, 'max': 10.0 },
            { "name": "project", "label": "Project", "type": "Bool", "default": False },
            { "name": "use_intersect_normal", "label": "Normal", "type": "Bool", "default": False },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "RAYCAST", "items": RAYCAST_ITEMS },
        ],
        "command": "raycast_operator"
    },
}


RAYCAST_MODULE = {
    'name': 'RAYCAST',
    'items': RAYCAST_ITEMS,
    'definition': RAYCAST_PROP_DEF,
    'version': '0.1'
}
