import bpy
from mathutils import Vector, Matrix

# Operator enum property list
# (identifier, name, description, icon, number)
OUTPUT_ITEMS = [
    ("OUTPUT", "Output", "Output", "OUTLINER", 0),
]


OUTPUT_PROP_DEF = {
    "OUTPUT": {
        "label": 'Output',
        "inputs":  [
            { "name": "input0", "label": "Input", "type": "InputStream", "expand": True},
            { "name": "collection", "label": "Collection", "type": "String", 'default': 'OUT'},
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "OUTPUT", "items": OUTPUT_ITEMS },
        ],
        "command": "output_operator"
    },
}


OUTPUT_MODULE = {
    'name': 'OUTPUT',
    'items': OUTPUT_ITEMS,
    'definition': OUTPUT_PROP_DEF,
    'version': '0.1'
}
