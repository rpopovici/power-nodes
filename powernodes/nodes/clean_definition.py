import bpy
from mathutils import Vector, Matrix

# Operator enum property list
# (identifier, name, description, icon, number)
CLEAN_ITEMS = [
    ("CLEAN", "Clean", "Clean mesh", "BRUSH_DATA", 0)
]


CLEAN_PROP_DEF = {
    "CLEAN": {
        "label": 'Clean geometry',
        "inputs":  [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "delete_loose_verts", "label": "Delete loose verts", "type": "Bool", "default": False },
            { "name": "delete_loose_edges", "label": "Delete loose edges", "type": "Bool", "default": False },
            { "name": "delete_loose_faces", "label": "Delete loose faces", "type": "Bool", "default": False },
            { "name": "delete_interior", "label": "Delete interior", "type": "Bool", "default": False },
            { "name": "fix_t_junction", "label": "Fix T-Junction", "type": "Bool", "default": False },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "CLEAN", "items": CLEAN_ITEMS },
        ],
        "command": "clean_operator"
    },
}


CLEAN_MODULE = {
    'name': 'CLEAN',
    'items': CLEAN_ITEMS,
    'definition': CLEAN_PROP_DEF,
    'version': '0.1'
}
