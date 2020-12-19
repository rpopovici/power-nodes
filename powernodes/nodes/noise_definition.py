import bpy
from mathutils import Vector, Matrix

# Operator enum property list
# (identifier, name, description, icon, number)
NOISE_ITEMS = [
    ("RANDOM", "Random", "Random", "MOD_NOISE", 0),
    ("NOISE", "Noise", "Noise", "MOD_NOISE", 1),
    ("TERRAIN", "Terrain", "Terrain", "MOD_NOISE", 2),
    ("HYBRID_MULTI_FRACTAL", "Hybrid Multi Fractal", "Hybrid Multi Fractal", "MOD_NOISE", 3),
]


SELECT_TYPE = [
    ("OBJECT", "Object", ""),
    ("VERT", "Vert", ""),
    ("EXPRESSION", "Expression", ""),
]


NOISE_TYPE = [
    ("BLENDER", "BLENDER", ""),
    ("PERLIN_ORIGINAL", "PERLIN_ORIGINAL", ""),
    ("PERLIN_NEW", "PERLIN_NEW", ""),
    ("VORONOI_F1", "VORONOI_F1", ""),
    ("VORONOI_F2", "VORONOI_F2", ""),
    ("VORONOI_F3", "VORONOI_F3", ""),
    ("VORONOI_F4", "VORONOI_F4", ""),
    ("VORONOI_F2F1", "VORONOI_F2F1", ""),
    ("VORONOI_CRACKLE", "VORONOI_CRACKLE", ""),
    ("CELLNOISE", "CELLNOISE", ""),
]


NOISE_PROP_DEF = {
    "RANDOM": {
        "label": 'Jitter',
        "inputs": [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "select_type", "label": "Type", "type": "Enum", "default": 'VERT', "items": SELECT_TYPE, "expand": True },
            { "name": "seed", "label": "Seed", "type": "Int", "default": 0 },
            { "name": "factor", "label": "Factor", "type": "Float", "default": 0.01, "min": -10.0, "max": 10.0 },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "RANDOM", "items": NOISE_ITEMS },
        ],
        "command": "random_operator"
    },
    "NOISE": {
        "label": 'Noise',
        "inputs": [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "factor", "label": "Factor", "type": "Float", "default": 0.1, "min": -10.0, "max": 10.0 },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "NOISE", "items": NOISE_ITEMS },
        ],
        "command": "noise_operator"
    },
    "TERRAIN": {
        "label": 'Terrrain',
        "inputs": [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "noise_basis", "label": "Noise type", "type": "Enum", "default": 'PERLIN_ORIGINAL', "items": NOISE_TYPE },
            { "name": "factor", "label": "Factor", "type": "Float", "default": 0.1, "min": -10.0, "max": 10.0 },
            { "name": "H", "label": "H", "type": "Float", "default": 1.0, "min": 0.0, "max": 100.0 },
            { "name": "lacunarity", "label": "Lacunarity", "type": "Float", "default": 0.1, "min": 0.0, "max": 10.0 },
            { "name": "octaves", "label": "Octaves", "type": "Int", "default": 1, "min": 0, "max": 8 },
            { "name": "offset", "label": "Offset", "type": "Float", "default": 0.0, "min": -10.0, "max": 10.0 },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "TERRAIN", "items": NOISE_ITEMS },
        ],
        "command": "terrain_noise_operator"
    },
    "HYBRID_MULTI_FRACTAL": {
        "label": 'Hybrid multi-fractal',
        "inputs": [
            { "name": "input0", "label": "Input", "type": "InputStream" },
            { "name": "noise_basis", "label": "Noise type", "type": "Enum", "default": 'PERLIN_ORIGINAL', "items": NOISE_TYPE },
            { "name": "factor", "label": "Factor", "type": "Float", "default": 0.1, "min": -10.0, "max": 10.0 },
            { "name": "H", "label": "H", "type": "Float", "default": 1.0, "min": 0.0, "max": 100.0 },
            { "name": "lacunarity", "label": "Lacunarity", "type": "Float", "default": 0.1, "min": 0.0, "max": 100.0 },
            { "name": "octaves", "label": "Octaves", "type": "Int", "default": 1, "min": 0, "max": 8 },
            { "name": "offset", "label": "Offset", "type": "Float", "default": 0.0, "min": -10.0, "max": 10.0 },
            { "name": "gain", "label": "Gain", "type": "Float", "default": 0.0, "min": -1.0, "max": 1.0 },
        ],
        "outputs": [
            { "name": "output", "label": "Output", "type": "OutputStream", "default": "HYBRID_MULTI_FRACTAL", "items": NOISE_ITEMS },
        ],
        "command": "hybrid_multi_fractal_noise_operator"
    },
}


NOISE_MODULE = {
    'name': 'NOISE',
    'items': NOISE_ITEMS,
    'definition': NOISE_PROP_DEF,
    'version': '0.1'
}
