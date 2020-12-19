import bpy
from mathutils import Vector, Matrix

# Operator enum property list
# (identifier, name, description, icon, number)
SORT_ITEMS = [
    ("XYZ", "XYZ", "XYZ", "EMPTY_AXIS", 0),
    ("EXPRESSION", "Expression", "Expression", "DRIVER_TRANSFORM", 1),
    ("RANDOM", "Random", "Random", "GPBRUSH_RANDOMIZE", 2),
]


SELECT_TYPE = [
    ("VERT", "Vert", ""),
    ("EDGE", "Edge", ""),
    ("FACE", "Face", ""),
]


SORT_PROP_DEF = {
    "XYZ": {
        "label": 'Sort XYZ',
        "inputs": [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "select_type", "label": "Type", "type": "Enum", "default": 'VERT', "items": SELECT_TYPE, "expand": True },
            { "name": "attribute_name", "label": "Attribute", "type": "String", "default": 'id' },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "XYZ", "items": SORT_ITEMS },
        ],
        "command": "sort_by_xyz"
    },
    "EXPRESSION": {
        "label": 'Sort by expression',
        "inputs": [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "select_type", "label": "Type", "type": "Enum", "default": 'VERT', "items": SELECT_TYPE, "expand": True },
            { "name": "attribute_name", "label": "Attribute", "type": "String", "default": 'id' },
            { "name": "expression", "label": "Exp", "type": "String", "default": '' },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "EXPRESSION", "items": SORT_ITEMS },
        ],
        "command": "sort_by_expression"
    },
    "RANDOM": {
        "label": 'Sort random',
        "inputs": [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "select_type", "label": "Type", "type": "Enum", "default": 'VERT', "items": SELECT_TYPE, "expand": True },
            { "name": "attribute_name", "label": "Attribute", "type": "String", "default": 'id' },
            { "name": "seed", "label": "Seed", "type": "Int", "default": 0 },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "RANDOM", "items": SORT_ITEMS },
        ],
        "command": "sort_by_random"
    },
}


SORT_MODULE = {
    'name': 'SORT',
    'items': SORT_ITEMS,
    'definition': SORT_PROP_DEF,
    'version': '0.1'
}
