# Created by Radu-Marius Popovici
# Copyright © 2020 Radu-Marius Popovici

bl_info = {
    "name" : "PowerNodes",
    "author" : "Radu-Marius Popovici",
    "description" : "Power Nodes",
    "blender" : (2, 92, 0),
    "version" : (0, 0, 1),
    "location" : "Node Editor",
    "warning" : "BETA version. Blender 2.92+ is required!",
    "doc_url": "https://github.com/rpopovici/power-nodes",
    "category" : "Node"
}


from . powernodes.utils.setup_utils import ensure_user_sitepackages, setup_numba, detect_cuda

# Ensure user site packages folder exists and add it to the path
ensure_user_sitepackages()

# activate CUDASIM if CUDA device is missing
detect_cuda()

# install numba if missing
setup_numba()


from . import auto_load
auto_load.init()


def register():
   auto_load.register()

def unregister():
   auto_load.unregister()
