import bpy
import mathutils
import re
import math
from functools import reduce

MATH_NAMESPACE = {key: getattr(math, key) for key in dir(math) if '__' not in key}

NOISE_NAMESPACE = {key: getattr(mathutils.noise, key) for key in dir(mathutils.noise) if '__' not in key}

BUILTINS = {
    "abs": abs,
    "all": all,
    "any": any,
    "len": len,
    "range": range,
    "enumerate": enumerate,
    "hex": hex,
    "iter": iter,
    "list": list,
    "dict": dict,
    "set": set,
    "tuple": tuple,
    "zip": zip,
    "next": next,
    "slice": slice,
    "sorted": sorted,
    "map": map,
    "filter": filter,
    "reduce": reduce,
    "str": str,
    "print": print,
    "min": min,
    "max": max,
    "pow": pow,
    "round": round,
    "sum": sum,
    "bool": bool,
    "int": int,
    "float": float,
    "True": True,
    "False": False,
    "None": None,

    "Color": mathutils.Color,
    "Euler": mathutils.Euler,
    "Quaternion": mathutils.Quaternion,
    "Matrix": mathutils.Matrix,
    "Vector": mathutils.Vector,
}


FIELD_LIST = ['area', 'center', 'co', 'index', 'bevel_weight', 'is_boundary', 'is_manifold',
    'edge_index', 'normal', 'select', 'hide', 'tangent', 'bitangent',
    'material_index', 'vertex_index', 'vertices', 'key', 'crease', 'use_edge_sharp', 'use_seam', 'tag']

GLOBAL_ATTRIBUTES = ['CTX', 'IDX', 'FRAME', 'FSTART', 'FEND', 'FPS', 'FPS_BASE', 'LEN', 'LOC', 'ROT', 'SCA']


DOMAIN_MAP = {
    # 'VERTEX': 'VERTEX', 'VERT': 'VERTEX', 'VERTS': 'VERTEX',
    'VERTEX': 'POINT', 'VERT': 'POINT', 'VERTS': 'POINT',
    'EDGE': 'EDGE', 'EDGES': 'EDGE',
    'POLYGON': 'POLYGON', 'FACE': 'POLYGON', 'FACES': 'POLYGON', 'FACES_ONLY': 'POLYGON', 'FACES_KEEP_BOUNDARY': 'POLYGON', 'REGION': 'POLYGON',
    'CORNER': 'CORNER', 'LOOP': 'CORNER',
}


TYPE_INITIAL_VALUE = {'INT': 0,
                'FLOAT': 0.0,
                'FLOAT_VECTOR': mathutils.Vector((0.0,0.0,0.0)),
                'FLOAT_COLOR': mathutils.Vector((0.0,0.0,0.0,0.0)),
                'BYTE_COLOR': mathutils.Vector((0.0,0.0,0.0,0.0)),
                'STRING': '',
}


range_pattern = r'''(
        \d+:\d+      # range 10:55
    )'''

token_pattern = r'''(
        [@\#$]\w+(?:[-']\w+)*   # #id, @user, $token
    )'''

token_func_pattern = r'''(
        \$\(.*?\)   # $(.datapath/subpath)
    )'''

backticks_pattern = r'''(
        `.*?`  # backticks string `hello..`
    )'''


def extract_tokens(expression):
    pattern = re.compile(token_pattern, re.VERBOSE)
    return set(re.findall(pattern, expression))


def extract_func_tokens(expression):
    pattern = re.compile(token_func_pattern, re.VERBOSE)
    return re.findall(pattern, expression)


def extract_backticks_pattern(expression):
    pattern = re.compile(backticks_pattern, re.VERBOSE)
    return re.findall(pattern, expression)


def extract_range(expression):
    pattern = re.compile(range_pattern, re.VERBOSE)
    return re.findall(pattern, expression)


def attribute_create(mesh, name, domain, data_type):
    for attribute in mesh.attributes:
        if attribute.name == name and attribute.domain == DOMAIN_MAP[domain]:
            mesh.attributes.remove(attribute)

    attr_def = mesh.attributes.new(name=name, type=data_type, domain=DOMAIN_MAP[domain])
    return attr_def


def attribute_get(mesh, name, domain):
    for attribute in mesh.attributes:
        if attribute.name == name and attribute.domain == DOMAIN_MAP[domain]:
            return attribute

    return None


def extract_custom_attribute_layers(attributes, mesh, bmesh, domain):
    attribute_layers = []
    domain_map = {'VERTEX': 'verts', 'POINT': 'verts', 'EDGE': 'edges', 'CORNER': 'loops', 'POLYGON': 'faces'}
    type_map = {'INT': 'int', 'FLOAT': 'float', 'FLOAT_VECTOR': 'float_vector', 'FLOAT_COLOR': 'float_color', 'BYTE_COLOR': 'color', 'STRING': 'string'}
    custom_attributes = [attr for attr in attributes if attr not in FIELD_LIST + GLOBAL_ATTRIBUTES]
    for attr in custom_attributes:
        attribute = attribute_get(mesh, attr, domain)
        if attribute:
            bmesh_elements = getattr(bmesh, domain_map[attribute.domain])
            attr_layer_item = getattr(bmesh_elements.layers, type_map[attribute.data_type]).get(attr)
            attribute_layers.append((attr, attr_layer_item, attribute.domain, attribute.data_type))

    return attribute_layers


def compile_expression_func(expression, mesh, bmesh, domain):
    evaluation_func = '''
{_R_E_T_} = {expression}
'''

    namespace = {
        '__builtins__': None,
        '__name__': None,
        '__file__': None,
        }

    namespace.update(BUILTINS)
    namespace.update(MATH_NAMESPACE)
    namespace.update(NOISE_NAMESPACE)

    tokens = extract_tokens(expression)
    attributes = [token.replace('$', '') for token in tokens]
    for token, attr in zip(tokens, attributes):
        if attr == 'self':
            # element
            expression = expression.replace(token, '_self_')
        if attr in FIELD_LIST:
            # elem fields
            expression = expression.replace(token, '_self_.' + attr)
        elif attr in GLOBAL_ATTRIBUTES:
            # globals
            expression = expression.replace(token, '_' + attr + '_')
        else:
            # custom attributes
            expression = expression.replace(token, '_self_[_' + attr + '_]')

    # inject custom attributes into local scope
    attribute_layers = extract_custom_attribute_layers(attributes, mesh, bmesh, domain)
    for attr, attr_layer_item, _, _ in attribute_layers:
        namespace['_' + attr + '_'] = attr_layer_item

    func_to_eval = evaluation_func.format(_R_E_T_='_R_E_T_', expression=expression)

    compiled_func = compile(func_to_eval, 'expression', 'exec')

    return (compiled_func, namespace)


def evaluate_expression(exp, global_scope, local_scope):
    exec(exp, global_scope, local_scope)
    return local_scope['_R_E_T_']


def evaluate_expression_foreach(elements, expression, obj, me, bm, domain):
    if not expression:
        return []

    fexp, namespace = compile_expression_func(expression, me, bm, domain)
    namespace['_CTX_'] = bpy.context
    namespace['_FRAME_'] = bpy.context.scene.frame_current
    namespace['_FSTART_'] = bpy.context.scene.frame_start
    namespace['_FEND_'] = bpy.context.scene.frame_end
    namespace['_FPS_'] = bpy.context.scene.render.fps
    namespace['_FPS_BASE_'] = bpy.context.scene.render.fps_base
    namespace['_LEN_'] = len(elements)
    namespace['_LOC_'] = obj.location
    namespace['_ROT_'] = obj.rotation_euler
    namespace['_SCA_'] = obj.scale

    values = [evaluate_expression(fexp, namespace, {'_self_': elem, '_IDX_': index}) for index, elem in enumerate(elements)]
    return values


def evaluate_stream_exp(expression, filter_rules=''):
    items = [item for item in expression.split()]
    return items
