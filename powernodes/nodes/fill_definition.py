import bpy
from mathutils import Vector, Matrix

# Operator enum property list
# (identifier, name, description, icon, number)
FILL_ITEMS = [
    ("FILL", "Fill", "Fill(F-key)", "SNAP_FACE", 0),
]


SELECT_TYPE = [
    ("VERTS", "Verts", ""),
    ("EDGES", "Edges", ""),
    ("FACES", "Faces", ""),
    ]


FILL_PROP_DEF = {
    "FILL": {
        "label": 'Fill(F-key)',
        "inputs": [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "select_type", "label": "Type", "type": "Enum", "default": 'VERTS', "items": SELECT_TYPE, "expand": True},
            { "name": "expression", "label": "Exp", "type": "Expression", "default": '$select', 'icon': 'EXPERIMENTAL' },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "FILL", "items": FILL_ITEMS },
        ],
        "command": "fill_operator"
    },
}


FILL_MODULE = {
    'name': 'FILL',
    'items': FILL_ITEMS,
    'definition': FILL_PROP_DEF,
    'version': '0.1'
}
