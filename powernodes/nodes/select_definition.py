import bpy
from mathutils import Vector, Matrix

# Operator enum property list
# (identifier, name, description, icon, number)
SELECT_ITEMS = [
    ("ANGLE", "Angle", "Angle", "RESTRICT_SELECT_ON", 0),
    ("BOUNDARY", "Boundary", "Boundary", "MOD_EDGESPLIT", 1),
    ("BOUNDING_BOX", "Bounding Box", "Bounding Box", "CUBE", 2),
    ("BY_INDEX", "By Index", "By Index", "SURFACE_NCYLINDER", 3),
    ("CLEAR", "Clear", "Clear selection", "TRASH", 4),
    ("EXPRESSION", "Expression", "Expression", "DRIVER_TRANSFORM", 5),
    ("NORMAL", "Normal", "Normal", "ORIENTATION_NORMAL", 6),
    ("CHECKERS", "Checkers", "Checkers select", "VIEW_PERSPECTIVE", 7),
]


SELECT_TYPE = [
    ("VERT", "Vert", ""),
    ("EDGE", "Edge", ""),
    ("FACE", "Face", ""),
]


SELECT_PROP_DEF = {
    "ANGLE": {
        "label": 'Select by angle',
        "inputs": [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "select_type", "label": "Type", "type": "Enum", "default": 'VERT', "items": SELECT_TYPE, "expand": True },
            { "name": "min_angle", "label": "Min angle", "type": "Float", "default": 45.0 },
            { "name": "max_angle", "label": "Max angle", "type": "Float", "default": 180.0 },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "ANGLE", "items": SELECT_ITEMS },
        ],
        "command": "select_by_angle"
    },
    "BOUNDARY": {
        "label": 'Select boundary',
        "inputs": [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "select_type", "label": "Type", "type": "Enum", "default": 'VERT', "items": SELECT_TYPE, "expand": True },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "BOUNDARY", "items": SELECT_ITEMS },
        ],
        "command": "select_by_boundary"
    },
    "BOUNDING_BOX": {
        "label": 'Select bounds',
        "inputs": [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "center", "label": "Center", "type": "Vector", "default": (0.0, 0.0, 0.0) },
            { "name": "diagonal", "label": "Diagonal", "type": "Vector", "default": (1.0, 1.0, 1.0) },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "BOUNDING_BOX", "items": SELECT_ITEMS },
        ],
        "command": "select_by_bbox"
    },
    "BY_INDEX": {
        "label": 'Select by index',
        "inputs": [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "select_type", "label": "Type", "type": "Enum", "default": 'VERT', "items": SELECT_TYPE, "expand": True },
            { "name": "indices", "label": "Indices", "type": "String", "default": '' },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "BY_INDEX", "items": SELECT_ITEMS },
        ],
        "command": "select_by_index"
    },
    "CLEAR": {
        "label": 'Select clear',
        "inputs": [
            { "name": "input0", "label": "Input", "type": "InputStream" },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "CLEAR", "items": SELECT_ITEMS },
        ],
        "command": "select_clear"
    },    
    "EXPRESSION": {
        "label": 'Select by expression',
        "inputs": [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "select_type", "label": "Type", "type": "Enum", "default": 'VERT', "items": SELECT_TYPE, "expand": True },
            { "name": "expression", "label": "Exp", "type": "Expression", "default": '$IDX % 2', 'icon': 'EXPERIMENTAL' },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "EXPRESSION", "items": SELECT_ITEMS },
        ],
        "command": "select_by_expression"
    },
    "NORMAL": {
        "label": 'Select by normal',
        "inputs": [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "select_type", "label": "Type", "type": "Enum", "default": 'VERT', "items": SELECT_TYPE, "expand": True },
            { "name": "normal", "label": "Normal", "type": "Vector", "default": (0.0, 0.0, 1.0) },
            { "name": "angle_tolerance", "label": "Tolerance", "type": "Float", "default": 1.0 },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "NORMAL", "items": SELECT_ITEMS },
        ],
        "command": "select_by_normal"
    },
    "CHECKERS": {
        "label": 'Select checkers',
        "inputs": [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "select_type", "label": "Type", "type": "Enum", "default": 'VERT', "items": SELECT_TYPE, "expand": True },
            { "name": "select_flag", "label": "Deselect", "type": "Bool", "default": False },
            { "name": "select_step", "label": "Select step", "type": "Int", "default": 1 },
            { "name": "deselect_step", "label": "Deselect step", "type": "Int", "default": 1 },
            { "name": "offset", "label": "Offset", "type": "Int", "default": 0 },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "CHECKERS", "items": SELECT_ITEMS },
        ],
        "command": "select_checkers"
    },
}


SELECT_MODULE = {
    'name': 'SELECT',
    'items': SELECT_ITEMS,
    'definition': SELECT_PROP_DEF,
    'version': '0.1'
}
