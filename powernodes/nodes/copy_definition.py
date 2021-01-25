import bpy
from mathutils import Vector, Matrix

# Operator enum property list
# (identifier, name, description, icon, number)
COPY_ITEMS = [
    ("COPY_POINTS", "Copy to Points", "Copy to Points", "LIGHTPROBE_GRID", 0),
]


ALIGN_TYPE = [
    ("NONE", "NONE", ""),
    ("CENTER", "CENTER", ""),
    ("BOTTOM", "BOTTOM", ""),
]


SELECT_TYPE = [
    ("VERT", "Vert", ""),
    ("EDGE", "Edge", ""),
    ("FACE", "Face", ""),
]


COPY_PROP_DEF = {
    "COPY_POINTS": {
        "label": 'Copy geometry',
        "inputs":  [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "input1", "label": "Input", "type": "InputStream" },
            { "name": "select_type", "label": "Type", "type": "Enum", "default": 'VERT', "items": SELECT_TYPE, "expand": True },
            { "name": "expression", "label": "Exp", "type": "Expression", "default": '', 'icon': 'EXPERIMENTAL' },
            { "name": "align_type", "label": "Align", "type": "Enum", "default": 'NONE', "items": ALIGN_TYPE, "expand": True },
            { "name": "normal_align", "label": "Align to normal", "type": "Bool", "default": False },
            { "name": "edge_normal", "label": "Normal to edge", "type": "Bool", "default": False },
            { "name": "use_instance", "label": "Instance", "type": "Bool", "default": False },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "COPY_POINTS", "items": COPY_ITEMS },
        ],
        "command": "copy_operator"
    },
}


COPY_MODULE = {
    'name': 'COPY',
    'items': COPY_ITEMS,
    'definition': COPY_PROP_DEF,
    'version': '0.1'
}
