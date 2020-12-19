import bpy
from mathutils import Vector, Matrix

# Operator enum property list
# (identifier, name, description, icon, number)
PRIMITIVE_ITEMS = [
    ("PLANE", "Plane", "Plane", "MESH_PLANE", 0),
    ("POINT", "Point", "Point", "DOT", 1),
    ("CIRCLE", "Circle", "Circle", "MESH_CIRCLE", 2),
    ("CUBE", "Cube", "Plane", "CUBE", 3),
    ("CYLINDER", "Cylinder", "Cylinder", "MESH_CYLINDER", 4),
    ("CONE", "Cone", "Cone", "CONE", 5),
    ("SPHERE", "Sphere", "Sphere", "SPHERE", 6),
    ("EXTRACT", "Extract", "Extract", "FACE_MAPS", 7),
]


PRIMITIVE_PROP_DEF = {
    "PLANE": {
        "label": 'Plane',
        "inputs": [
            { "name": "matrix", "label": "Matrix",  "type": "Matrix", "default": Matrix()},
            { "name": "size", "label": "Size", "type": "Float", "default": 1.0 },
            { "name": "x_segments", "label": "Columns", "type": "Int", "default": 1, 'min': 1, 'max': 1000 },
            { "name": "y_segments", "label": "Rows", "type": "Int", "default": 1, 'min': 1, 'max': 1000 },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "PLANE", "items": PRIMITIVE_ITEMS },
        ],
        "command": "create_grid"
    },
    "POINT": {
        "label": 'Point',
        "inputs": [
            { "name": "matrix", "label": "Matrix",  "type": "Matrix", "default": Matrix()},
            { "name": "location", "label": "Location", "type": "Vector", "default": (0.0, 0.0, 0.0) },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "POINT", "items": PRIMITIVE_ITEMS },
        ],
        "command": "create_point"
    },    
    "SPHERE": {
        "label": 'Sphere',
        "inputs": [
            { "name": "matrix", "label": "Matrix",  "type": "Matrix", "default": Matrix()},
            { "name": "diameter", "label": "Diameter", "type": "Float", "default": 1.0 },
            { "name": "segments", "label": "Segments", "type": "Int", "default": 16, 'min': 3, 'max': 1000 },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "SPHERE", "items": PRIMITIVE_ITEMS },
        ],
        "command": "create_uvsphere"
    },    
    "CONE": {
        "label": 'Cone',
        "inputs": [
            { "name": "matrix", "label": "Matrix",  "type": "Matrix", "default": Matrix()},
            { "name": "cap_ends", "label": "Cap ends", "type": "Bool", "default": True },
            { "name": "cap_tris", "label": "Cap tris", "type": "Bool", "default": False },
            { "name": "diameter2", "label": "Top", "type": "Float", "default": 0.5 },
            { "name": "diameter1", "label": "Bottom", "type": "Float", "default": 1.0 },
            { "name": "segments", "label": "Segments", "type": "Int", "default": 16, 'min': 3, 'max': 1000 },
            { "name": "depth", "label": "Depth", "type": "Float", "default": 2.0 },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "CONE", "items": PRIMITIVE_ITEMS },
        ],
        "command": "create_cone"
    },
    "CYLINDER": {
        "label": 'Cylinder',
        "inputs": [
            { "name": "matrix", "label": "Matrix",  "type": "Matrix", "default": Matrix()},
            { "name": "cap_ends", "label": "Cap ends", "type": "Bool", "default": True },
            { "name": "cap_tris", "label": "Cap tris", "type": "Bool", "default": False },
            { "name": "diameter", "label": "Diameter", "type": "Float", "default": 1.0 },
            { "name": "segments", "label": "Segments", "type": "Int", "default": 16, 'min': 3, 'max': 1000 },
            { "name": "depth", "label": "Depth", "type": "Float", "default": 1.0 },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "CYLINDER", "items": PRIMITIVE_ITEMS },
        ],
        "command": "create_cylinder"
    },    
    "CIRCLE": {
        "label": 'Circle',
        "inputs": [
            { "name": "matrix", "label": "Matrix",  "type": "Matrix", "default": Matrix()},
            { "name": "cap_ends", "label": "Cap ends", "type": "Bool", "default": True },
            { "name": "cap_tris", "label": "Cap tris", "type": "Bool", "default": False },
            { "name": "radius", "label": "Radius", "type": "Float", "default": 1.0 },
            { "name": "segments", "label": "Segments", "type": "Int", "default": 8, 'min': 3, 'max': 1000 },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "CIRCLE", "items": PRIMITIVE_ITEMS },
        ],
        "command": "create_circle"
    },
    "CUBE": {
        "label": 'Cube',
        "inputs": [
            { "name": "matrix", "label": "Matrix",  "type": "Matrix", "default": Matrix()},
            { "name": "size", "label": "Size", "type": "Float", "default": 1.0 },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "CUBE", "items": PRIMITIVE_ITEMS },
        ],
        "command": "create_cube"
    },
    "EXTRACT": {
        "label": 'Extract',
        "inputs": [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "faces", "label": "Faces", "type": "String", "default": '' },
            { "name": "matrix", "label": "Matrix",  "type": "Matrix", "default": Matrix()},
            { "name": "distance", "label": "Distance", "type": "Float", "default": 1.0 },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "EXTRACT", "items": PRIMITIVE_ITEMS },
        ],
        "command": "create_mesh_from_selection"
    },
}


PRIMITIVE_MODULE = {
    'name': 'PRIMITIVE',
    'items': PRIMITIVE_ITEMS,
    'definition': PRIMITIVE_PROP_DEF,
    'version': '0.1'
}
