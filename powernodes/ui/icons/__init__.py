import bpy
import os

from ... draw import PREVIEW_COLLECTIONS

ICONS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))

def require_icon(name):
    global PREVIEW_COLLECTIONS
    if not 'POWER_ICONS' in PREVIEW_COLLECTIONS:
        preview_collection = bpy.utils.previews.new()
        PREVIEW_COLLECTIONS['POWER_ICONS'] = preview_collection
    power_icons = PREVIEW_COLLECTIONS["POWER_ICONS"]

    if name in power_icons:
        return power_icons[name]

    return power_icons.load(name, os.path.join(ICONS_PATH, name + '.png'), 'IMAGE')
