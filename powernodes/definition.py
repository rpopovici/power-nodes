import bpy
import importlib
from pathlib import Path
from .. auto_load import iter_submodule_names


ENUM_GLOBALS = {}


def init_enum_globals(MODULE):
    global ENUM_GLOBALS

    OPS_PROP_DEF = MODULE['definition']
    module_name = MODULE['name']

    for ops_type in OPS_PROP_DEF:
        for prop_group in OPS_PROP_DEF[ops_type]:
            for index, entry in enumerate(OPS_PROP_DEF[ops_type][prop_group]):
                if not isinstance(entry, dict):
                    continue
                if entry['type'] in ['Enum', 'OutputStream']:
                    entry_path = module_name + ops_type + '.' + entry['name']
                    ENUM_GLOBALS[entry_path] = entry['items']


# initialize enum map, blender needs this to be global..
def init_enums_from_definition():
    module_path = Path(__file__).parent
    modules = {name for name in iter_submodule_names(module_path) if 'nodes.' in name and '_definition' in name}

    for name in sorted(list(modules)):
        module_name = name.replace('nodes.', '').replace('_definition', '')
        module_key = module_name.upper() + '_MODULE'

        module = importlib.import_module(".powernodes." + name, module_path.parent.name)
        init_enum_globals(module.__dict__[module_key])


init_enums_from_definition()
