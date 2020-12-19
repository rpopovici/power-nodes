import bpy


def material_operator(inputstream0, options={}):
    material = options['material']

    for obj in inputstream0:
        keep_mats = [mat for mat in obj.data.materials if '_pn_material_tag_' in mat]
        obj.data.materials.clear()
        for mat in keep_mats:
            obj.data.materials.append(mat)
        if material and not obj.data.materials.get(material.name):
            material['_pn_material_tag_'] = True
            obj.data.materials.append(material)

    return (inputstream0, None)
