import bpy
import random
from math import sqrt, copysign, atan2
from mathutils import Vector, Matrix
import colorsys
import time
import pickle

START_TIME = 0.0

def timer_start():
    global START_TIME
    START_TIME = time.time_ns()
    return START_TIME


def timer_end(message=''):
    timer_end = time.time_ns()
    elapsed = (timer_end - START_TIME)
    if message != '':
        print(message + str(elapsed / 1000000 ) + 'ms')
    return (START_TIME, timer_end, elapsed)


def serialize_to_string(data):
    return pickle.dumps(data, 0).decode()


def deserialize_from_string(datastr):
    return pickle.loads(datastr.encode())


def collinear(vec1, vec2, epsilon):
    if (vec1.length == 0.0) or (vec2.length == 0.0):
        return False
    return ((vec1.angle(vec2) < epsilon) or (abs(radians(180) - vec1.angle(vec2)) < epsilon))


def signed_angle(v, w, n):
    angle = atan2(n.cross(v).dot(w), v.dot(w))
    return angle


def matrix_flatten(mat):
    dimension = len(mat)
    return [mat[j][i] for i in range(dimension) for j in range(dimension)]


def matrix_make_positive(matrix):
    (loc, rot, sca) = matrix.decompose()
    sca = [abs(axis) for axis in sca]
    sca = Vector(sca)
    positive_matrix = Matrix.Translation(loc).to_4x4() @ rot.to_matrix().to_4x4() @ Matrix.Diagonal(sca).to_4x4()
    return positive_matrix


def ui_scale():
    return bpy.context.preferences.system.ui_scale


def calc_bbox_center(obj):
    return 1 / 8 * sum((Vector(bound) for bound in obj.bound_box), Vector())


def squarify_vector(vec, axis, normal=Vector((0.0, 0.0, 1.0))):
    rot_quat = normal.to_track_quat("Z", "X")
    mat_rot = rot_quat.to_matrix().to_4x4()
    vec = mat_rot.inverted() @ vec
    axis = mat_rot.inverted() @ axis

    seq = [abs(i) for i in axis]
    sign = [copysign(1.0, i) for i in axis]
    sort_axis = sorted(range(len(seq)), key=seq.__getitem__)
    val = list(vec)
    # val[sort_axis[0]] = vec[sort_axis[0]] # min -> min
    val[sort_axis[1]] = vec[sort_axis[1]] + sign[sort_axis[1]] * (seq[sort_axis[2]] - seq[sort_axis[1]]) # max -> mid
    # val[sort_axis[2]] = vec[sort_axis[2]] # max -> max
    return mat_rot @ Vector(tuple(val))


def curve_length(curve):
    curve_length = sum(spline.calc_length() for spline in curve.data.splines)
    return curve_length


def context_override(area_type='VIEW_3D'):
    override = bpy.context.copy()
    for window in bpy.data.window_managers[0].windows:
        for area in window.screen.areas:
            if area.type == area_type:
                override["area"] = area
                override["region"] = [region for region in area.regions if region.type == 'WINDOW'][0]
                return override

    return override


def change_viewport_shading(shade='OBJECT'):
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        # space.viewport_shade = shade
                        # space.shading.type = 'MATERIAL'
                        space.shading.color_type = shade


def random_color():
    (h, s, v) = (random.randint(0, 360) / 360, random.randint(40, 70) / 100, random.randint(60, 80) / 100)
    (r, g, b) = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)


def get_last_operation():
    clipboard = get_info_report()
    if len(clipboard) > 0:
        last = clipboard[len(clipboard)-1]
    else:
        last = None
    return last


def get_info_report():
    ctx_area = None
    ctx_screen = None
    for workspace in bpy.data.workspaces:
        if workspace.name == 'Scripting':
            for screen in workspace.screens:
                for area in screen.areas:
                    if area.type == 'INFO':
                        ctx_screen = screen
                        ctx_area = area

    win = bpy.context.window_manager.windows[0]
    override = bpy.context.copy()
    override['window'] = win
    override['screen'] = ctx_screen
    override['area'] = ctx_area
    ctx = override

    bpy.ops.info.select_all(ctx, 'EXEC_DEFAULT', False, action='TOGGLE')
    bpy.ops.info.report_copy(ctx, 'EXEC_DEFAULT', False)
    bpy.ops.info.select_all(ctx, 'EXEC_DEFAULT', False, action='TOGGLE')
    #area.type = area_type

    clipboard = bpy.context.window_manager.clipboard
    clipboard = clipboard.splitlines()
    return clipboard


def _get_last_operation(ctx):
    ctx['area'].type = 'INFO'

    bpy.ops.info.select_all(ctx, 'EXEC_DEFAULT', action='TOGGLE')
    bpy.ops.info.report_copy(ctx, 'EXEC_DEFAULT')
    bpy.ops.info.select_all(ctx, 'EXEC_DEFAULT', action='TOGGLE')

    clipboard = bpy.context.window_manager.clipboard
    clipboard = clipboard.splitlines()
    last = clipboard[len(clipboard)-1]
    return last


change_viewport_shading()
