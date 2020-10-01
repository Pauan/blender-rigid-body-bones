import bpy
import bmesh
from math import radians
from mathutils import Vector, Euler, Matrix


def log(obj):
    from pprint import PrettyPrinter
    PrettyPrinter(indent = 4).pprint(obj)


class Selectable:
    def __init__(self, collection):
        self.collection = collection
        self.hidden = False

    def __enter__(self):
        self.hidden = self.collection.hide_select
        self.collection.hide_select = False
        return self.collection

    def __exit__(self, exc_type, exc_value, traceback):
        self.collection.hide_select = self.hidden
        return False


class Mode:
    def __init__(self, context, mode):
        self.context = context
        self.mode = mode
        self.old_mode = None

    def __enter__(self):
        # TODO is object correct ?
        self.old_mode = self.context.object.mode
        bpy.ops.object.mode_set(mode=self.mode)

    def __exit__(self, exc_type, exc_value, traceback):
        bpy.ops.object.mode_set(mode=self.old_mode)
        return False


#class Tab:
#    def __init__(self, context, name):
#        self.context = context
#        self.name = name
#        self.space_data = None
#
#    def __enter__(self):
#        self.space_data = self.context.space_data.context
#        self.context.space_data.context = self.name
#
#        for x in self.context.screen.areas:
#            if x.type == 'PROPERTIES':
#                area = x
#                break
#
#        local = self.context.copy()
#        local["area"] = x
#        return local
#
#    def __exit__(self, exc_type, exc_value, traceback):
#        self.context.space_data.context = self.space_data
#        return False


class Selected:
    def __init__(self, context):
        self.context = context
        self.view_layer = None
        self.selected = None
        self.active = None

    def __enter__(self):
        self.view_layer = self.context.view_layer
        self.selected = list(self.view_layer.objects.selected)
        self.active = self.view_layer.objects.active

    def __exit__(self, exc_type, exc_value, traceback):
        for obj in self.view_layer.objects.selected:
            obj.select_set(False)

        for obj in self.selected:
            obj.select_set(True)

        self.view_layer.objects.active = self.active

        return False


def is_edit_mode(context):
    return (
        (context.active_bone is not None) and
        (context.mode == 'EDIT_ARMATURE')
    )


def select(context, objs):
    view_layer = context.view_layer

    for obj in view_layer.objects.selected:
        obj.select_set(False)

    for obj in objs:
        obj.select_set(True)

    view_layer.objects.active = objs[-1]


def set_parent(context, child, parent):
    with Selected(context):
        select(context, [child, parent])
        bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)


def set_parent_relative(context, child, parent):
    with Selected(context):
        select(context, [child, parent])
        bpy.ops.object.parent_no_inverse_set()


def make_collection(name, parent):
    collection = bpy.data.collections.new(name)
    parent.children.link(collection)
    return collection


def remove_object(object):
    object.data.name = object.data.name + " [DELETED]"
    bpy.data.objects.remove(object)


def remove_collection(collection, recursive=False):
    for child in collection.objects:
        remove_object(child)

    if recursive:
        for child in collection.children:
            remove_collection(child, recursive)

    bpy.data.collections.remove(collection)


def safe_remove_collection(collection):
    if len(collection.children) == 0 and len(collection.objects) == 0:
        bpy.data.collections.remove(collection)
        return True

    else:
        return False


def set_mesh_cube(mesh, dimensions):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, calc_uvs=False)
    bmesh.ops.scale(bm, vec=dimensions, verts=bm.verts)
    bm.to_mesh(mesh)
    bm.free()


def make_cube(name, dimensions, collection):
    mesh = bpy.data.meshes.new(name=name)
    set_mesh_cube(mesh, dimensions)
    cube = bpy.data.objects.new(name, mesh)
    collection.objects.link(cube)
    return cube
