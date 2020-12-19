import bpy
from mathutils import Vector, Matrix

# Operator enum property list
# (identifier, name, description, icon, number)
INPUT_ITEMS = [
    ("INPUT_VECTOR_TO_XYZ", "Vector to XYZ", "Vector to XYZ", "SHORTDISPLAY", 0),
    ("INPUT_XYZ_TO_VECTOR", "XYZ to Vector", "XYZ to Vector", "SHORTDISPLAY", 1),
    ("INPUT_TRANSFORM_TO_MATRIX", "Transform to Matrix", "Transform to Matrix", "SHORTDISPLAY", 2),
    ("INPUT_MATRIX_TO_TRANSFORM", "Matrix to Transform", "Matrix to Transform", "SHORTDISPLAY", 3),
]


INPUT_PROP_DEF = {
    "INPUT_VECTOR_TO_XYZ": {
        "label": 'Vector to XYZ',
        "inputs":  [
            { "name": "vector", "label": "Vector", "type": "Vector", "default": (0.0, 0.0, 0.0), },
        ],
        "outputs": [
            { "name": "x", "label": "X", "type": "Float", "default": 0.0 },
            { "name": "y", "label": "Y", "type": "Float", "default": 0.0 },
            { "name": "z", "label": "Z", "type": "Float", "default": 0.0 },
        ],
        "command": "vector_to_xyz_operator"
    },
    "INPUT_XYZ_TO_VECTOR": {
        "label": 'XYZ to Vector',
        "inputs":  [
            { "name": "x", "label": "X", "type": "Float", "default": 0.0 },
            { "name": "y", "label": "Y", "type": "Float", "default": 0.0 },
            { "name": "z", "label": "Z", "type": "Float", "default": 0.0 },
        ],
        "outputs": [
            { "name": "vector", "label": "Vector", "type": "Vector", "default": (0.0, 0.0, 0.0), },
        ],
        "command": "xyz_to_vector_operator"
    },
    "INPUT_TRANSFORM_TO_MATRIX": {
        "label": 'Transform to Matrix',
        "inputs":  [
            { "name": "loc", "label": "Translation", "type": "Vector", "default": (0.0, 0.0, 0.0), },
            { "name": "rot", "label": "Rotation", "type": "Vector", "default": (0.0, 0.0, 0.0), },
            { "name": "sca", "label": "Scale", "type": "Vector", "default": (1.0, 1.0, 1.0), },
        ],
        "outputs": [
            { "name": "matrix", "label": "Matrix",  "type": "Matrix", "default": Matrix()},
        ],
        "command": "transform_to_matrix_operator"
    },
    "INPUT_MATRIX_TO_TRANSFORM": {
        "label": 'Matrix to Transform',
        "inputs":  [
            { "name": "matrix", "label": "Matrix",  "type": "Matrix", "default": Matrix()},
        ],
        "outputs": [
            { "name": "loc", "label": "Translation", "type": "Vector", "default": (0.0, 0.0, 0.0), },
            { "name": "rot", "label": "Rotation", "type": "Vector", "default": (0.0, 0.0, 0.0), },
            { "name": "sca", "label": "Scale", "type": "Vector", "default": (0.0, 0.0, 0.0), },
        ],
        "command": "matrix_to_transform_operator"
    },
}


INPUT_MODULE = {
    'name': 'INPUT',
    'items': INPUT_ITEMS,
    'definition': INPUT_PROP_DEF,
    'version': '0.1'
}
