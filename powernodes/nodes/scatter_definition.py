import bpy
from mathutils import Vector, Matrix

# Operator enum property list
# (identifier, name, description, icon, number)
SCATTER_ITEMS = [
    ("RANDOM", "Random", "Random", "GPBRUSH_RANDOMIZE", 0),
]


SELECT_TYPE = [
    ("VERT", "Vert", ""),
    ("EDGE", "Edge", ""),
    ("FACE", "Face", ""),
]


SCATTER_PROP_DEF = {
    "RANDOM": {
        "label": 'Scatter',
        "inputs": [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "select_type", "label": "Type", "type": "Enum", "default": 'VERT', "items": SELECT_TYPE, "expand": True },
            { "name": "amount", "label": "Amount", "type": "Int", "default": 1000, 'min': 0, 'max': 1000000 },
            { "name": "seed", "label": "Seed", "type": "Int", "default": 0 },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "RANDOM", "items": SCATTER_ITEMS },
        ],
        "command": "scatter_operator"
    },
}


SCATTER_MODULE = {
    'name': 'SCATTER',
    'items': SCATTER_ITEMS,
    'definition': SCATTER_PROP_DEF,
    'version': '0.1'
}
