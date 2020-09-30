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


def root_collection(context):
    scene = context.scene

    root = scene.rigid_body_bones.collection

    if not root:
        root = make_collection("RigidBodyBones", scene.collection)
        root.hide_select = True
        root.hide_render = True
        scene.rigid_body_bones.collection = root

    return root


def constraints_collection(context, armature):
    data = armature.data.rigid_body_bones

    if not data.constraints:
        parent = hitboxes_collection(context, armature)
        data.constraints = make_collection(armature.name + " [Constraints]", parent)
        data.constraints.hide_render = True
        data.constraints.hide_viewport = True

    return data.constraints


def hitboxes_collection(context, armature):
    data = armature.data.rigid_body_bones

    if not data.hitboxes:
        parent = root_collection(context)
        data.hitboxes = make_collection(armature.name + " [Hitboxes]", parent)
        data.hitboxes.hide_render = True

    return data.hitboxes


def init_hitbox(object):
    object.hide_render = True
    object.show_in_front = True
    object.show_bounds = True
    object.display_type = 'BOUNDS'
    object.display_bounds_type = 'BOX'
    object.display.show_shadows = False
    object.rigid_body.collision_shape = 'BOX'


def make_empty_rigid_body(context, name, collection, parent):
    mesh = bpy.data.meshes.new(name=name)
    body = bpy.data.objects.new(name, mesh)
    collection.objects.link(body)
    set_parent_relative(context, body, parent)

    with Selected(context):
        select(context, [body])
        bpy.ops.rigidbody.object_add(type='PASSIVE')
        body.rigid_body.kinematic = True
        body.rigid_body.collision_collections[0] = False
        body.hide_select = True
        body.hide_viewport = True
        init_hitbox(body)

    return body


def make_cube(name, dimensions, collection):
    mesh = bpy.data.meshes.new(name=name)

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, calc_uvs=False)
    bmesh.ops.scale(bm, vec=dimensions, verts=bm.verts)
    bm.to_mesh(mesh)
    bm.free()

    cube = bpy.data.objects.new(name, mesh)
    collection.objects.link(cube)
    return cube


def bone_to_object_space(vector):
    vector.rotate(Euler((radians(90.0), 0.0, 0.0)))

def hitbox_dimensions(bone):
    length = bone.length
    dimensions = Vector((length * 0.2, length, length * 0.2)) * bone.rigid_body_bones.scale
    bone_to_object_space(dimensions)
    return dimensions


def make_active_hitbox(context, armature, bone):
    hitbox = make_cube(
        name=bone.name + " [Hitbox]",
        dimensions=hitbox_dimensions(bone),
        collection=hitboxes_collection(context, armature),
    )

    hitbox.parent = armature
    hitbox.parent_type = 'OBJECT'

    location = bone.rigid_body_bones.location.copy()
    bone_to_object_space(location)
    location += bone.center

    rotation = bone.rigid_body_bones.rotation.copy()
    rotation.rotate(bone.matrix.to_euler())
    rotation.rotate_axis('X', radians(90.0))

    hitbox.rotation_euler = rotation
    hitbox.location = location

    with Selected(context):
        select(context, [hitbox])
        bpy.ops.rigidbody.object_add(type='ACTIVE')
        init_hitbox(hitbox)

    return hitbox


def make_passive_hitbox(context, armature, bone):
    hitbox = make_cube(
        name=bone.name + " [Hitbox]",
        dimensions=hitbox_dimensions(bone),
        collection=hitboxes_collection(context, armature),
    )

    hitbox.parent = armature
    hitbox.parent_type = 'BONE'
    hitbox.parent_bone = bone.name

    rotation = Euler((radians(90.0), 0.0, 0.0))
    rotation.rotate(bone.rigid_body_bones.rotation)

    location = Vector((0.0, bone.length * -0.5, 0.0)) + bone.rigid_body_bones.location

    hitbox.rotation_euler = rotation
    hitbox.location = location

    with Selected(context):
        select(context, [hitbox])
        bpy.ops.rigidbody.object_add(type='PASSIVE')
        hitbox.rigid_body.kinematic = True
        init_hitbox(hitbox)

    return hitbox
