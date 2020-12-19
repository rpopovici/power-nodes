import bpy
from mathutils import Vector, Matrix

# Operator enum property list
# (identifier, name, description, icon, number)
DELETE_ITEMS = [
    ("DELETE", "Delete", "Delete mesh", "TRASH", 0),
    ("DISSOLVE", "Dissolve", "Dissolve mesh", "TRASH", 1),
]


DELETE_SELECT_TYPE = [
    ("VERTS", "Verts", ""),
    ("EDGES", "Edges", ""),
    ("FACES_ONLY", "Faces only", ""),
    # ("EDGES_FACES", "Edges only", ""),
    ("FACES", "Faces", ""),
    ("FACES_KEEP_BOUNDARY", "Faces Keep Boundary", ""),
    # ("TAGGED_ONLY", "Tagged only", ""),
    ]


DISSOLVE_SELECT_TYPE = [
    ("VERTS", "Verts", ""),
    ("EDGES", "Edges", ""),
    ("FACES", "Faces", ""),
    ]


DELETE_PROP_DEF = {
    "DELETE": {
        "label": 'Delete geometry',
        "inputs":  [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "select_type", "label": "Type", "type": "Enum", "default": 'VERTS', "items": DELETE_SELECT_TYPE, },
            { "name": "expression", "label": "Exp", "type": "Expression", "default": '$select', 'icon': 'EXPERIMENTAL' },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "DELETE", "items": DELETE_ITEMS },
        ],
        "command": "delete_operator"
    },
    "DISSOLVE": {
        "label": 'Dissolve geometry',
        "inputs":  [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "select_type", "label": "Type", "type": "Enum", "default": 'VERTS', "items": DISSOLVE_SELECT_TYPE, "expand": True},
            { "name": "expression", "label": "Exp", "type": "Expression", "default": '$select', 'icon': 'EXPERIMENTAL' },
            { "name": "use_boundary_tear", "label": "Boundary tear", "type": "Bool", "default": False, 'enabled_by': "select_type=VERTS" },
            { "name": "use_face_split", "label": "Face split", "type": "Bool", "default": False, 'enabled_by': "select_type=VERTS,EDGES" },
            { "name": "use_verts", "label": "Use verts", "type": "Bool", "default": False, 'enabled_by': "select_type=EDGES,FACES" },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "DISSOLVE", "items": DELETE_ITEMS },
        ],
        "command": "dissolve_operator"
    },
}


DELETE_MODULE = {
    'name': 'DELETE',
    'items': DELETE_ITEMS,
    'definition': DELETE_PROP_DEF,
    'version': '0.1'
}
