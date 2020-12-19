import bpy
from mathutils import Vector, Matrix

# Operator enum property list
# (identifier, name, description, icon, number)
MATERIAL_ITEMS = [
    ("MATERIAL", "Material", "Material", "MATERIAL", 0),
]


MATERIAL_PROP_DEF = {
    "MATERIAL": {
        "label": 'Material',
        "inputs":  [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "material", "label": "Material", "type": "Material", },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "MATERIAL", "items": MATERIAL_ITEMS },
        ],
        "command": "material_operator"
    },
}


MATERIAL_MODULE = {
    'name': 'MATERIAL',
    'items': MATERIAL_ITEMS,
    'definition': MATERIAL_PROP_DEF,
    'version': '0.1'
}
