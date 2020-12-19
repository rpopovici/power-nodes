import bpy
from mathutils import Vector, Matrix


POWER_ITEMS = [
    ("PASS", "Pass", "Pass node", "NODE", 0),
    ("TRANSFORM", "Transform", "Transform object", "EMPTY_ARROWS", 1),
    ("BEVEL", "Bevel", "Bevel mesh", "MOD_BEVEL", 2),
    ("BOOLEAN", "Boolean", "Boolean operations", "MOD_BOOLEAN", 3),
    ("EXTRUDE", "Extrude", "Extrude operations", "FACESEL", 4),
    ("INSET", "Inset", "Inset operations", "FULLSCREEN_EXIT", 5),
    ("ARRAY", "Array", "Array operations", "MOD_ARRAY", 6),
    ("SWEEP", "Sweep", "Sweep operations", "BRUSH_DATA", 7),
    ("MIRROR", "Mirror", "Mirror", "MOD_MIRROR", 8),
    ("WELD", "Weld", "Merge vertices", "AUTOMERGE_OFF", 9),
    ("SUBDIV", "Subdivide", "Subdivide mesh", "MOD_SUBSURF", 10),
    ("TRIANGULATE", "Triangulate", "Triangulate mesh", "MOD_TRIANGULATE", 11),
    ("SOLIDIFY", "Solidify", "Solidify mesh", "MOD_SOLIDIFY", 12),
    ("BISECT", "Bisect", "Bisect mesh", "MESH_GRID", 13),
    ("RESAMPLE", "Resample", "Resample mesh", "SELECT_SET", 14),
    ("SMOOTH", "Smooth", "Smooth mesh", "MOD_SMOOTH", 15),
    ("EXPLODE", "Explode", "Explode mesh", "MOD_EXPLODE", 16),
    ("SCREW", "Screw", "Screw mesh", "MOD_SCREW", 17),
    ("SKIN", "Skin", "Skin mesh", "MOD_SKIN", 18)
]


AXIS_TYPE = [
    ("X", "X", ""),
    ("Y", "Y", ""),
    ("Z", "Z", ""),
]


SELECT_TYPE = [
    ("VERT", "Vert", ""),
    ("EDGE", "Edge", ""),
    ("FACE", "Face", ""),
]


BEVEL_TYPE = [
    ("VERT", "Vert", ""),
    ("EDGE", "Edge", ""),
    ("FACE", "Face", ""),
]


BEVEL_OFFSET_TYPE = [
    ("OFFSET", "Offset", ""),
    ("WIDTH", "Width", ""),
    ("DEPTH", "Depth", ""),
    ("PERCENT", "Percent", ""),
]


BOOLEAN_OPERATION_TYPE = [
    ("DIFFERENCE", "DIFFERENCE", ""),
    ("UNION", "UNION", ""),
    ("INTERSECT", "INTERSECT", ""),
    ("SLICE", "SLICE", ""),
]

BOOLEAN_SOLVER_TYPE = [
    ("FAST", "FAST", ""),
    ("EXACT", "EXACT", ""),
    ("CSG", "CSG(Experimental)", ""),
]


ARRAY_FIT_TYPE = [
    ("FIXED_COUNT", "FIXED_COUNT", ""),
    ("FIT_LENGTH", "FIT_LENGTH", ""),
    ("FIT_CURVE", "FIT_CURVE", ""),
    ("RADIAL", "RADIAL", ""),
]


EXTRUDE_TYPE = [
    ("VERT", "Vert", ""),
    ("EDGE", "Edge", ""),
    ("FACE", "Face", ""),
    ("REGION", "Region", ""),
]

INSET_TYPE = [
    ("FACE", "Face", ""),
    ("REGION", "Region", ""),
]

SOLIDIFY_MODE_TYPE = [
    ("EXTRUDE", "Simple", ""),
    ("NON_MANIFOLD", "Complex", "")
]

SMOOTH_MODE_TYPE = [
    ("SIMPLE", "Simple", ""),
    ("LAPLACIAN", "Laplacian", "")
]


POWER_PROP_DEF = {
    "PASS": {
        "label": 'Pass',
        "inputs": [
            { "name": "input0", "label": "Input", "type": "InputStream", "expand": True },
            { "name": "join", "label": "Join", "type": "Bool", "default": False },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "PASS", "items": POWER_ITEMS },
        ],
        "command": "passthrough_operator"
    },
    "TRANSFORM": {
        "label": 'Transform',
        "inputs":  [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "apply_transform", "label": "Apply transform", "type": "Bool", "default": False },
            { "name": "use_local_space", "label": "Local space", "type": "Bool", "default": True },
            { "name": "use_relative", "label": "Relative", "type": "Bool", "default": True },
            { "name": "use_radians", "label": "Use radians", "type": "Bool", "default": False },
            { "name": "loc", "label": "Translation", "icon": "ORIENTATION_GLOBAL", "type": "Vector", "default": (0.0, 0.0, 0.0) },
            { "name": "rot", "label": "Rotation", "icon": "ORIENTATION_GIMBAL", "type": "Vector", "default": (0.0, 0.0, 0.0) },
            { "name": "sca", "label": "Scale", "icon": "FULLSCREEN_ENTER", "type": "Vector", "default": (1.0, 1.0, 1.0) },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "TRANSFORM", "items": POWER_ITEMS },
        ],
        "command": "transform_operator"
    },
    "BEVEL": {
        "label": 'Bevel',
        "inputs":  [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "mode", "label": "Mode", "type": "Enum", "default": 'EDGE', "items": BEVEL_TYPE, "expand": True },
            { "name": "expression", "label": "Exp", "type": "Expression", "default": '$select', 'icon': 'EXPERIMENTAL' },
            { "name": "offset", "label": "Offset", "type": "Float", "default": 0.1 },
            { "name": "offset_type", "label": "Offset Type", "type": "Enum", "default": "OFFSET", "items": BEVEL_OFFSET_TYPE},
            { "name": "segments", "label": "Segments", "type": "Int", "default": 1, 'min': 1, 'max': 100 },
            { "name": "profile", "label": "Profile", "type": "Float", "default": 0.5 },
            { "name": "clamp_overlap", "label": "Clamp overlap", "type": "Bool", "default": True },
            { "name": "vertex_only", "label": "Vertex only", "type": "Bool", "default": False },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "BEVEL", "items": POWER_ITEMS },
        ],
        "command": "bevel_operator"
    },
    "BOOLEAN": {
        "label": 'Boolean',
        "inputs":  [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "input1", "label": "Input", "type": "InputStream" },
            { "name": "solver", "label": "Solver", "type": "Enum", "default": 'FAST', "items": BOOLEAN_SOLVER_TYPE, "expand": True },
            { "name": "operation_type", "label": "Operation", "type": "Enum", "default": "DIFFERENCE", "items": BOOLEAN_OPERATION_TYPE},
            { "name": "error_tolerance", "label": "Error Tolerance", "type": "Float", "default": 0.0 },
            { "name": "fix_boolean", "label": "Fix boolean", "type": "Bool", "default": True },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "BOOLEAN", "items": POWER_ITEMS },
        ],
        "command": "boolean_operator"
    },
    "EXTRUDE": {
        "label": 'Extrude',
        "inputs":  [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "mode", "label": "Mode", "type": "Enum", "default": 'VERT', "items": EXTRUDE_TYPE, "expand": True },
            { "name": "expression", "label": "Exp", "type": "Expression", "default": '$select', 'icon': 'EXPERIMENTAL' },
            { "name": "offset_displace", "label": "Offset", "type": "Vector", "default": (0.0, 0.0, 1.0) },
            { "name": "use_keep_orig", "label": "Keep original", "type": "Bool", "default": False },
            { "name": "use_normal_flip", "label": "Normal flip", "type": "Bool", "default": False },
            { "name": "use_normal_from_adjacent", "label": "Normal adjacent", "type": "Bool", "default": False },
            { "name": "use_dissolve_ortho_edges", "label": "Dissolve edges", "type": "Bool", "default": False },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "EXTRUDE", "items": POWER_ITEMS },
        ],
        "command": "extrude_operator"
    },
    "INSET": {
        "label": 'Inset',
        "inputs":  [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "mode", "label": "Mode", "type": "Enum", "default": 'FACE', "items": INSET_TYPE, "expand": True },
            { "name": "expression", "label": "Exp", "type": "Expression", "default": '$select', 'icon': 'EXPERIMENTAL' },
            { "name": "thickness", "label": "Thickness", "type": "Float", "default": 0.1 },
            { "name": "depth", "label": "Depth", "type": "Float", "default": 0.0 },
            { "name": "use_boundary", "label": "Use boundary only", "type": "Bool", "default": False },
            { "name": "use_even_offset", "label": "Even_offset", "type": "Bool", "default": False },
            { "name": "use_interpolate", "label": "Interpolate", "type": "Bool", "default": False },
            { "name": "use_relative_offset", "label": "Relative offset", "type": "Bool", "default": False },
            { "name": "use_edge_rail", "label": "Edge rail", "type": "Bool", "default": False },
            { "name": "use_outset", "label": "Outset", "type": "Bool", "default": False },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "INSET", "items": POWER_ITEMS },
        ],
        "command": "inset_operator"
    },
    "ARRAY": {
        "label": 'Array',
        "inputs":  [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "input1", "label": "Input", "type": "InputStream" },
            { "name": "fit_type", "label": "Fit", "type": "Enum", "default": 'FIXED_COUNT', "items": ARRAY_FIT_TYPE, },
            { "name": "use_local_space", "label": "Local space", "type": "Bool", "default": True },
            { "name": "count", "label": "Count", "type": "Int", "default": 1, 'min': 1, 'max': 10000 },
            { "name": "use_relative_offset", "label": "Relative offset", "type": "Bool", "default": True },
            { "name": "relative_offset_displace", "label": "Offset", "type": "Vector", "default": (1.0, 0.0, 0.0), 'enabled_by': "use_relative_offset=True" },
            { "name": "axis", "label": "Axis", "type": "Enum", "default": 'Z', "items": AXIS_TYPE, "expand": True, 'enabled_by': "fit_type=RADIAL" },
            { "name": "use_merge_vertices", "label": "Merge", "type": "Bool", "default": False },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "ARRAY", "items": POWER_ITEMS },
        ],
        "command": "array_operator"
    },
    "SWEEP": {
        "label": 'Sweep',
        "inputs":  [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "use_local_space", "label": "Local space", "type": "Bool", "default": True },
            { "name": "axis", "label": "Axis", "type": "Enum", "default": 'Z', "items": AXIS_TYPE, "expand": True },
            { "name": "count", "label": "Count", "type": "Int", "default": 6 },
            { "name": "angle", "label": "Angle", "type": "Float", "default": 360.0 },
            { "name": "offset", "label": "Offset", "type": "Float", "default": 1.0 },
            { "name": "use_merge_vertices", "label": "Merge", "type": "Bool", "default": True },
            { "name": "delete_interior", "label": "Delete interior", "type": "Bool", "default": True },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "SWEEP", "items": POWER_ITEMS },
        ],
        "command": "sweep_operator"
    },
    "MIRROR": {
        "label": 'Mirror',
        "inputs":  [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "axis", "label": "Axis", "type": "BoolVector", "default": (True, False, False) },
            { "name": "use_mirror_merge", "label": "Merge", "type": "Bool", "default": False },
            { "name": "merge_threshold", "label": "Merge Limit", "type": "Float", "default": 0.0001 },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "MIRROR", "items": POWER_ITEMS },
        ],
        "command": "mirror_operator"
    },
    "WELD": {
        "label": 'Weld',
        "inputs":  [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "distance", "label": "Offset", "type": "Float", "default": 0.0001 },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "WELD", "items": POWER_ITEMS },
        ],
        "command": "weld_operator"
    },
    "SUBDIV": {
        "label": 'Subdiv',
        "inputs":  [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "levels", "label": "Levels", "type": "Int", "default": 1 },
            { "name": "quality", "label": "Quality", "type": "Int", "default": 3 },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "SUBDIV", "items": POWER_ITEMS },
        ],
        "command": "subdivide_operator"
    },
    "TRIANGULATE": {
        "label": 'Triangulate',
        "inputs":  [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            # { "name": "quad_method", "label": "quad_method", "type": "Int", "default": 0 },
            # { "name": "ngon_method", "label": "ngon_method", "type": "Int", "default": 0 },
            # { "name": "min_vertices", "label": "min_vertices", "type": "Int", "default": 4 },
            # { "name": "keep_custom_normals", "label": "Keep normals", "type": "Bool", "default": False },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "TRIANGULATE", "items": POWER_ITEMS },
        ],
        "command": "triangulate_operator"
    },
    "SOLIDIFY": {
        "label": 'Solidify',
        "inputs":  [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "solidify_mode", "label": "Mode", "type": "Enum", "default": 'EXTRUDE', "items": SOLIDIFY_MODE_TYPE },
            { "name": "thickness", "label": "Thickness", "type": "Float", "default": 0.01 },
            { "name": "offset", "label": "Offset", "type": "Float", "default": -1.0 },
            { "name": "use_rim", "label": "Rim", "type": "Bool", "default": True },
            { "name": "use_rim_only", "label": "Only rim", "type": "Bool", "default": False },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "SOLIDIFY", "items": POWER_ITEMS },
        ],
        "command": "solidify_operator"
    },
    "BISECT": {
        "label": 'Bisect',
        "inputs":  [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "axis", "label": "Axis", "type": "Enum", "default": 'Z', "items": AXIS_TYPE, "expand": True },
            { "name": "cuts", "label": "Cuts", "type": "Int", "default": 1 },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "BISECT", "items": POWER_ITEMS },
        ],
        "command": "bisect_operator"
    },
    "RESAMPLE": {
        "label": 'Resample',
        "inputs":  [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "length", "label": "Length", "type": "Float", "default": 0.1, 'min': 0.001, 'max': 100.0 },
            { "name": "segments", "label": "Segments", "type": "Float", "default": 0.1, 'min': 0.001, 'max': 100.0 },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "RESAMPLE", "items": POWER_ITEMS },
        ],
        "command": "resample_operator"
    },
    "SMOOTH": {
        "label": 'Smooth',
        "inputs":  [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "smooth_type", "label": "Type", "type": "Enum", "default": 'SIMPLE', "items": SMOOTH_MODE_TYPE, "expand": True },
            { "name": "repeat", "label": "Repeat", "type": "Int", "default": 1, 'min': 0, 'max': 1000.0 },
            { "name": "factor", "label": "Factor", "type": "Float", "default": 0.1, 'min': -10.0, 'max': 10.0 },
            { "name": "preserve_volume", "label": "Preserve volume", "type": "Bool", "default": True },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "SMOOTH", "items": POWER_ITEMS },
        ],
        "command": "smooth_operator"
    },
    "EXPLODE": {
        "label": 'Explode',
        "inputs":  [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "value", "label": "Value", "type": "Float", "default": 0.1 },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "EXPLODE", "items": POWER_ITEMS },
        ],
        "command": "explode_operator"
    },
    "SCREW": {
        "label": 'Screw',
        "inputs":  [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "input1", "label": "Input", "type": "InputStream" },
            { "name": "angle", "label": "Angle", "type": "Float", "default": 360.0, },
            { "name": "screw_offset", "label": "Screw Offset", "type": "Float", "default": 0.0, },
            { "name": "iterations", "label": "Iterations", "type": "Int", "default": 1, 'min': 0, 'max': 100 },
            { "name": "axis", "label": "Axis", "type": "Enum", "default": 'Z', "items": AXIS_TYPE, "expand": True },
            { "name": "use_object_screw_offset", "label": "Object screw", "type": "Bool", "default": False },
            { "name": "steps", "label": "Steps", "type": "Int", "default": 16, 'min': 0, 'max': 1000 },
            { "name": "use_merge_vertices", "label": "Merge", "type": "Bool", "default": False },
            { "name": "merge_threshold", "label": "Merge Threshold", "type": "Float", "default": 0.001, },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "SCREW", "items": POWER_ITEMS },
        ],
        "command": "screw_operator"
    },
    "SKIN": {
        "label": 'Skin',
        "inputs":  [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            # { "name": "attribute_name", "label": "Name", "type": "String", "default": 'id', 'icon': 'COPY_ID' },
            { "name": "scale", "label": "Scale", "type": "Float", "default": 0.1, 'min': -1.0, 'max': 1.0 },
            { "name": "branch_smoothing", "label": "Branch smooth", "type": "Float", "default": 0.0, 'min': 0.0, 'max': 1.0 },
            { "name": "mark_root", "label": "Mark root", "type": "Bool", "default": True },
            { "name": "mark_loose", "label": "Mark loose", "type": "Bool", "default": False },
            { "name": "use_smooth_shade", "label": "Smooth shade", "type": "Bool", "default": False },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "SKIN", "items": POWER_ITEMS },
        ],
        "command": "skin_operator"
    },
}


POWER_MODULE = {
    'name': 'POWER',
    'items': POWER_ITEMS,
    'definition': POWER_PROP_DEF,
    'version': '0.1'
}
