import sys, time, traceback
import bpy
from bpy.app.handlers import persistent
from mathutils import Vector, Matrix

import functools
import queue

from . utils.node_utils import node_trees, socket_for_object, node_for_object
from . utils.utils import get_last_operation
from . ops import initialize_default_collections, unlink_from_collection

# import cProfile
# profiler = cProfile.Profile()
# call profiler.print_stats(1) from console

# global power nodes context
POWER_CONTEXT = {
        'is_processing': False,
        'is_rendering': False,
        'frame': None,
        'mode': None, # OBJECT EDIT
        'timestamp': None,
        'after_undo' : False,
        'after_timer': False,
        'after_info': False
    }


undo_stack = []

def get_undo_flag():
    global POWER_CONTEXT
    return POWER_CONTEXT['after_undo']


def set_undo_flag(flag):
    global POWER_CONTEXT
    POWER_CONTEXT['after_undo'] = flag


def get_timer_flag():
    global POWER_CONTEXT
    return POWER_CONTEXT['after_timer']


def set_timer_flag(flag):
    global POWER_CONTEXT
    POWER_CONTEXT['after_timer'] = flag


def get_info_flag():
    global POWER_CONTEXT
    return POWER_CONTEXT['after_info']


def set_info_flag(flag):
    global POWER_CONTEXT
    POWER_CONTEXT['after_info'] = flag


def lock_processing():
    global POWER_CONTEXT
    POWER_CONTEXT['is_processing'] = True


def unlock_processing():
    global POWER_CONTEXT
    POWER_CONTEXT['is_processing'] = False


def is_processing_locked():
    global POWER_CONTEXT
    return POWER_CONTEXT['is_processing'] == True


def has_frame_changed(scene):
    global POWER_CONTEXT
    last_frame = POWER_CONTEXT['frame']
    POWER_CONTEXT['frame'] = scene.frame_current
    return not last_frame == scene.frame_current


def has_mode_changed():
    global POWER_CONTEXT
    last_mode = POWER_CONTEXT['mode']
    POWER_CONTEXT['mode'] = bpy.context.active_object.mode
    return not last_mode == bpy.context.active_object.mode


def update_timestamp():
    global POWER_CONTEXT
    POWER_CONTEXT['timestamp'] = time.time()


def get_rendering_flag():
    global POWER_CONTEXT
    return POWER_CONTEXT['is_rendering']


def set_rendering_flag(flag):
    global POWER_CONTEXT
    POWER_CONTEXT['is_rendering'] = flag


def check_for_updates(ctx, edg, node_group):
    for update in edg.updates:
        if not isinstance(update.id, bpy.types.Object):
            continue

        update_loc = False
        if '_pn_matrix_world_' not in update.id.original:
            update.id.original['_pn_matrix_world_'] = update.id.original.matrix_world.copy()
        else:
            if update.is_updated_transform and (Matrix(update.id.original['_pn_matrix_world_']) != update.id.original.matrix_world):
                update.id.original['_pn_matrix_world_'] = update.id.original.matrix_world.copy()
                update_loc = True

        if update.is_updated_geometry or update_loc: # or update.is_updated_transform:
            if isinstance(update.id, bpy.types.Object):
                node = node_for_object(update.id.original, node_group)
                if node:
                    node.update_from_edg(ctx, edg)


@persistent
def frame_update_handler_post(scene, edg):
    if not has_frame_changed(scene):
        return

    for node_group in node_trees():
        try:
            node_group.update_frame()
            depsgraph_update_handler_post(scene, edg)
        except Exception as e:
            print('Failed to update from frame handler: ', str(e))


@persistent
def depsgraph_update_handler_pre(scene):
    pass


@persistent
def depsgraph_update_handler_post(scene, edg):
    # if not hasattr(bpy.context, "active_operator") or bpy.context.active_operator is None:
    #     return

    # if bpy.context.mode not in ['OBJECT', 'EDIT_MESH']:
    #     return

    update_timestamp()

    for node_group in node_trees():
        if node_group.needs_update:
            check_for_updates(bpy.context, edg, node_group)

            if is_processing_locked():
                # defer processing for the next run
                node_group.update_tag()
            else:
                lock_processing()

                if bpy.context.mode in ['EDIT_MESH', 'EDIT_CURVE', 'EDIT_LATTICE', 'EDIT_SURFACE', 'EDIT_METABALL', 'EDIT_TEXT']:
                    for obj in bpy.context.objects_in_mode:
                        obj.update_from_editmode()
                    for area in bpy.context.screen.areas:
                        # needed to fix a crash in outliner
                        if area.type == 'OUTLINER':
                            area.tag_redraw()

                try:
                    # profiler.runcall(node_group.process)
                    node_group.process()
                except Exception as e:
                    print('Failed to process from depsgraph handler: ', str(e))
                    traceback.print_exc()

                unlock_processing()


@persistent
def load_update_handler_post(scene):
    # add default collections if they don't exist
    # initialize_default_collections()

    for node_group in node_trees():
        for node in node_group.nodes:
            if node.bl_idname not in ['NodeGroupInput', 'NodeGroupOutput']:
                node.needs_processing = True


@persistent
def undo_update_handler_pre(scene):
    if get_undo_flag():
        return

    set_undo_flag(True)

    out_col = bpy.data.collections.get('POWER_NODES')
    if out_col:
        for obj in out_col.objects:
            unlink_from_collection(obj=obj, collection='POWER_NODES')

    set_undo_flag(False)
    pass


@persistent
def undo_update_handler_post(scene):
    pass


@persistent
def redo_update_handler_pre(scene):
    pass


@persistent
def redo_update_handler_post(scene):
    # fix crash in redo
    bpy.context.view_layer.update()


@persistent
def render_handler_init(scene):
    if scene.render and not scene.render.use_lock_interface:
        # attempt to fix render crash
        scene.render.use_lock_interface = True


@persistent
def render_handler_pre(scene):
    set_rendering_flag(True)


@persistent
def render_handler_post(scene):
    set_rendering_flag(False)


def register():
    # define custom props
    bpy.types.Object.pn_original = bpy.props.PointerProperty(name="pn_original", type=bpy.types.ID)

    bpy.app.handlers.depsgraph_update_pre.append(depsgraph_update_handler_pre)
    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_handler_post)

    bpy.app.handlers.frame_change_post.append(frame_update_handler_post)

    bpy.app.handlers.load_post.append(load_update_handler_post)

    bpy.app.handlers.undo_pre.append(undo_update_handler_pre)
    bpy.app.handlers.undo_post.append(undo_update_handler_post)

    bpy.app.handlers.redo_pre.append(redo_update_handler_pre)
    bpy.app.handlers.redo_post.append(redo_update_handler_post)

    bpy.app.handlers.render_init.append(render_handler_init)
    bpy.app.handlers.render_pre.append(render_handler_pre)
    bpy.app.handlers.render_post.append(render_handler_post)


def unregister():
    del bpy.types.Object.pn_original

    bpy.app.handlers.depsgraph_update_pre.remove(depsgraph_update_handler_pre)
    bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update_handler_post)

    bpy.app.handlers.frame_change_post.remove(frame_update_handler_post)

    bpy.app.handlers.load_post.remove(load_update_handler_post)

    bpy.app.handlers.undo_pre.remove(undo_update_handler_pre)
    bpy.app.handlers.undo_post.remove(undo_update_handler_post)

    bpy.app.handlers.redo_pre.remove(redo_update_handler_pre)
    bpy.app.handlers.redo_post.remove(redo_update_handler_post)

    bpy.app.handlers.render_init.remove(render_handler_init)
    bpy.app.handlers.render_pre.remove(render_handler_pre)
    bpy.app.handlers.render_post.remove(render_handler_post)
