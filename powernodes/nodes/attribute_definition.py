import bpy
from mathutils import Vector, Matrix

# Operator enum property list
# (identifier, name, description, icon, number)
ATTRIBUTE_ITEMS = [
    ("CREATE", "Create", "Create", "MESH_DATA", 0),
    ("COPY", "Copy", "Copy", "COPYDOWN", 1),
    ("ELEVATE", "Elevate", "Elevate attribute", "EXPORT", 2),
    ("EXPRESSION", "Formula", "Expression evaluate", "EXPERIMENTAL", 3),
    ("TRANSPORT", "Transport", "Attribute transfer", "CENTER_ONLY", 4),
    ("SMOOTH", "Smooth", "Attribute smooth", "MOD_SMOOTH", 5),
    ("RANDOM", "Random", "Attribute randomize", "MOD_NOISE", 6),
]


DOMAIN_TYPE = [
    ("VERTEX", "Vertex", ""),
    ("EDGE", "Edge", ""),
    ("CORNER", "Loop", ""),
    ("POLYGON", "Face", ""),
    # ("POINT", "Point", ""),
    # ("CURVE", "Curve", ""),
]


TRANSPORT_DOMAIN_TYPE = [
    ("VERTEX", "Vertex", ""),
    # ("EDGE", "Edge", ""),
    # ("CORNER", "Loop", ""),
    ("POLYGON", "Face", ""),
    # ("POINT", "Point", ""),
    # ("CURVE", "Curve", ""),
]


ATTRIBUTE_TYPE = [
    ("FLOAT", "Float", ""),
    ("INT", "Int", ""),
    ("FLOAT_VECTOR", "Vector(Float)", ""),
    ("FLOAT_COLOR", "Color(Float)", ""),
    ("BYTE_COLOR", "Color(Byte)", ""),
    ("STRING", "String", ""),
]


ATTRIBUTE_PROP_DEF = {
    "CREATE": {
        "label": 'Attribute create',
        "inputs": [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "domain", "label": "Domain", "type": "Enum", "default": 'VERTEX', "items": DOMAIN_TYPE,},
            { "name": "attribute_type", "label": "Type", "type": "Enum", "default": 'INT', "items": ATTRIBUTE_TYPE,},
            { "name": "attribute_name", "label": "Name", "type": "String", "default": 'id', 'icon': 'COPY_ID' },
            { "name": "attr_default_value", "label": "Value", "type": "String", "default": '0' },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "CREATE", "items": ATTRIBUTE_ITEMS },
        ],
        "command": "create_attribute_op"
    },
    "COPY": {
        "label": 'Attribute copy',
        "inputs": [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "input1", "label": "Input", "type": "InputStream" },
            { "name": "from_domain", "label": "Type", "type": "Enum", "default": 'VERTEX', "items": DOMAIN_TYPE, },
            { "name": "attribute_name", "label": "Name", "type": "String", "default": 'id', 'icon': 'COPY_ID' },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "COPY", "items": ATTRIBUTE_ITEMS },
        ],
        "command": "copy_attribute_op"
    },
    "ELEVATE": {
        "label": 'Attribute elevate',
        "inputs": [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "from_domain", "label": "From", "type": "Enum", "default": 'VERTEX', "items": DOMAIN_TYPE, },
            { "name": "to_domain", "label": "To", "type": "Enum", "default": 'VERTEX', "items": DOMAIN_TYPE, },
            { "name": "attribute_name", "label": "Name", "type": "String", "default": 'id', 'icon': 'COPY_ID' },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "ELEVATE", "items": ATTRIBUTE_ITEMS },
        ],
        "command": "elevate_attribute_op"
    },
    "EXPRESSION": {
        "label": 'Attribute expression',
        "inputs": [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "domain", "label": "Domain", "type": "Enum", "default": 'VERTEX', "items": DOMAIN_TYPE, },
            { "name": "attribute_name", "label": "Name", "type": "String", "default": 'id', 'icon': 'COPY_ID' },
            { "name": "expression", "label": "Exp", "type": "Expression", "default": '$IDX', 'icon': 'EXPERIMENTAL' },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "EXPRESSION", "items": ATTRIBUTE_ITEMS },
        ],
        "command": "evaluate_attribute_expression_op"
    },
    "TRANSPORT": {
        "label": 'Attribute transport',
        "inputs": [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "input1", "label": "Input", "type": "InputStream" },
            { "name": "from_domain", "label": "Type", "type": "Enum", "default": 'VERTEX', "items": TRANSPORT_DOMAIN_TYPE, },
            { "name": "attribute_name", "label": "Name", "type": "String", "default": 'id', 'icon': 'COPY_ID' },
            { "name": "distance", "label": "Distance", "type": "Float", "default": 0.01 },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "TRANSPORT", "items": ATTRIBUTE_ITEMS },
        ],
        "command": "transport_attribute_op"
    },
    "SMOOTH": {
        "label": 'Attribute smooth',
        "inputs": [
            { "name": "input0", "label": "Input", "type": "InputStream" },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "SMOOTH", "items": ATTRIBUTE_ITEMS },
        ],
        "command": "smooth_attribute_op"
    },
    "RANDOM": {
        "label": 'Attribute randomize',
        "inputs": [
            { "name": "input0", "label": "Input", "type": "InputStream" },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "SMOOTH", "items": ATTRIBUTE_ITEMS },
        ],
        "command": "randomize_attribute_op"
    },
}


ATTRIBUTE_MODULE = {
    'name': 'ATTRIBUTE',
    'items': ATTRIBUTE_ITEMS,
    'definition': ATTRIBUTE_PROP_DEF,
    'version': '0.1'
}
