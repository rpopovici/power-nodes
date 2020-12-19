from mathutils import Euler, Vector, Matrix

from .. utils.utils import matrix_flatten


def vector_to_xyz_operator(*inputstreams, options={}):
    vector = options['vector']

    return ([vector.x, vector.y, vector.z], None)


def xyz_to_vector_operator(*inputstreams, options={}):
    x = options['x']
    y = options['y']
    z = options['z']

    return ([Vector((x, y, z))], None)


def transform_to_matrix_operator(*inputstreams, options={}):
    loc = options['loc']
    rot = options['rot']
    sca = options['sca']

    matrix = Matrix.Translation(loc).to_4x4() @ Euler(rot, 'XYZ').to_matrix().to_4x4() @ Matrix.Diagonal(sca).to_4x4()

    return ([matrix_flatten(matrix)], None)


def matrix_to_transform_operator(*inputstreams, options={}):
    matrix = options['matrix']

    (loc, rot, sca) = matrix.decompose()
    rot = rot.to_euler('XYZ')

    return ([loc, Vector((rot.x, rot.y, rot.z)), sca], None)
