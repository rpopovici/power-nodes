# Created by Radu-Marius Popovici
# Copyright © 2020 Radu-Marius Popovici

bl_info = {
    "name" : "PowerNodes",
    "author" : "Radu-Marius Popovici",
    "description" : "Power Nodes",
    "blender" : (2, 92, 0),
    "version" : (0, 0, 1),
    "location" : "",
    "warning" : "",
    "category" : "Object"
}


from . powernodes.utils.setup_utils import ensure_user_sitepackages
ensure_user_sitepackages()


from . import auto_load
auto_load.init()


def register():
   auto_load.register()

def unregister():
   auto_load.unregister()
