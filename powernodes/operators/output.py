import bpy

from .. ops import link_to_collection

def output_operator(*inputstreams, options={}):
    collection = options['collection']

    objects = []
    for inputstream in inputstreams:
        objects += inputstream

    if collection:
        for obj in objects:
            # link to collection
            link_to_collection(obj, collection)

    return (objects, None)
