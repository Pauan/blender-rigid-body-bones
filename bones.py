import bpy
from math import radians
from mathutils import Vector, Euler
from . import armatures
from . import utils


def bone_to_object_space(vector):
    vector.rotate(Euler((radians(90.0), 0.0, 0.0)))

def hitbox_dimensions(bone):
    dimensions = bone.rigid_body_bones.scale * bone.length
    bone_to_object_space(dimensions)
    return dimensions


def update_shape(object, type):
    object.display_bounds_type = type
    object.rigid_body.collision_shape = type


def update_rigid_body(rigid_body, data):
    rigid_body.mass = data.mass
    rigid_body.friction = data.friction
    rigid_body.restitution = data.restitution
    rigid_body.linear_damping = data.linear_damping
    rigid_body.angular_damping = data.angular_damping
    rigid_body.use_margin = data.use_margin
    rigid_body.collision_margin = data.collision_margin
    rigid_body.collision_collections = data.collision_collections
    rigid_body.use_deactivation = data.use_deactivation
    rigid_body.use_start_deactivated = data.use_start_deactivated
    rigid_body.deactivate_linear_velocity = data.deactivate_linear_velocity
    rigid_body.deactivate_angular_velocity = data.deactivate_angular_velocity


def init_hitbox(object, type):
    object.hide_render = True
    object.show_in_front = True
    object.show_bounds = True
    object.display_type = 'BOUNDS'
    object.display.show_shadows = False
    update_shape(object, type)


def make_empty_rigid_body(context, name, collection, parent):
    mesh = bpy.data.meshes.new(name=name)
    body = bpy.data.objects.new(name, mesh)
    collection.objects.link(body)

    body.parent = parent
    body.parent_type = 'OBJECT'

    with utils.Selected(context), utils.Selectable(armatures.root_collection(context)):
        utils.select(context, [body])
        bpy.ops.rigidbody.object_add(type='PASSIVE')
        body.rigid_body.kinematic = True
        body.rigid_body.collision_collections[0] = False
        body.hide_select = True
        body.hide_viewport = True
        init_hitbox(body, type='BOX')

    return body


def hitbox_location(bone, type):
    if type == 'ACTIVE':
        location = bone.rigid_body_bones.location.copy()
        bone_to_object_space(location)
        location += bone.center
        return location

    else:
        return Vector((0.0, bone.length * -0.5, 0.0)) + bone.rigid_body_bones.location


def hitbox_rotation(bone, type):
    if type == 'ACTIVE':
        rotation = bone.rigid_body_bones.rotation.copy()
        rotation.rotate(bone.matrix.to_euler())
        rotation.rotate_axis('X', radians(90.0))
        return rotation

    else:
        rotation = Euler((radians(90.0), 0.0, 0.0))
        rotation.rotate(bone.rigid_body_bones.rotation)
        return rotation


def make_active_hitbox(context, armature, bone):
    data = bone.rigid_body_bones

    hitbox = utils.make_cube(
        name=bone.name + " [Hitbox]",
        dimensions=hitbox_dimensions(bone),
        collection=armatures.hitboxes_collection(context, armature),
    )

    hitbox.parent = armature
    hitbox.parent_type = 'OBJECT'

    hitbox.rotation_euler = hitbox_rotation(bone, 'ACTIVE')
    hitbox.location = hitbox_location(bone, 'ACTIVE')

    with utils.Selected(context), utils.Selectable(armatures.root_collection(context)):
        utils.select(context, [hitbox])
        bpy.ops.rigidbody.object_add(type='ACTIVE')
        update_rigid_body(hitbox.rigid_body, data)
        init_hitbox(hitbox, type=data.collision_shape)

    return hitbox


def make_passive_hitbox(context, armature, bone):
    data = bone.rigid_body_bones

    hitbox = utils.make_cube(
        name=bone.name + " [Hitbox]",
        dimensions=hitbox_dimensions(bone),
        collection=armatures.hitboxes_collection(context, armature),
    )

    hitbox.parent = armature
    hitbox.parent_type = 'BONE'
    hitbox.parent_bone = bone.name

    hitbox.rotation_euler = hitbox_rotation(bone, 'PASSIVE')
    hitbox.location = hitbox_location(bone, 'PASSIVE')

    with utils.Selected(context), utils.Selectable(armatures.root_collection(context)):
        utils.select(context, [hitbox])
        bpy.ops.rigidbody.object_add(type='PASSIVE')
        hitbox.rigid_body.kinematic = True
        init_hitbox(hitbox, type=data.collision_shape)

    return hitbox


def create(context, armature, bone):
    data = bone.rigid_body_bones

    if not data.hitbox:
        if data.type == 'ACTIVE':
            data.hitbox = make_active_hitbox(context, armature, bone)

        else:
            data.hitbox = make_passive_hitbox(context, armature, bone)


def remove(context, armature, bone):
    data = bone.rigid_body_bones

    if data.hitbox:
        utils.remove_object(data.hitbox)
        data.hitbox = None

    if data.constraint:
        utils.remove_object(data.constraint)
        data.constraint = None


def initialize(context, armature, bone):
    data = bone.rigid_body_bones

    if data.enabled:
        create(context, armature, bone)


def is_active(bone):
    data = bone.rigid_body_bones
    return data.enabled and data.type == 'ACTIVE'


def align_hitbox(bone):
    data = bone.rigid_body_bones

    if data.hitbox:
        data.hitbox.location = hitbox_location(bone, data.type)
        data.hitbox.rotation_euler = hitbox_rotation(bone, data.type)
        utils.set_mesh_cube(data.hitbox.data, hitbox_dimensions(bone))


def store_parent(armature, bone):
    data = bone.rigid_body_bones

    if data.enabled and data.type == 'ACTIVE':
        if not data.is_property_set("parent"):
            if bone.parent:
                data.parent = bone.parent.name

            else:
                data.parent = ""

            data.use_connect = bone.use_connect
            bone.parent = None

    else:
        restore_parent(armature, bone)


def restore_parent(armature, bone):
    data = bone.rigid_body_bones

    if data.is_property_set("parent"):
        if data.parent == "":
            bone.parent = None

        else:
            parent = armature.data.edit_bones.get(data.parent)

            if parent is None:
                raise Exception("[{}] could not find parent \"{}\"".format(bone.name, data.parent))

            bone.parent = parent

        bone.use_connect = data.use_connect

        data.property_unset("parent")
        data.property_unset("use_connect")


@utils.bone_event("type")
def event_type(context, armature, bone, data):
    remove(context, armature, bone)
    initialize(context, armature, bone)


@utils.bone_event("collision_shape")
def event_collision_shape(context, armature, bone, data):
    if data.hitbox:
        update_shape(data.hitbox, data.collision_shape)


@utils.bone_event("location")
def event_location(context, armature, bone, data):
    if data.hitbox:
        data.hitbox.location = hitbox_location(bone, data.type)

@utils.bone_event("rotation")
def event_rotation(context, armature, bone, data):
    if data.hitbox:
        data.hitbox.rotation_euler = hitbox_rotation(bone, data.type)

@utils.bone_event("scale")
def event_scale(context, armature, bone, data):
    if data.hitbox:
        utils.set_mesh_cube(data.hitbox.data, hitbox_dimensions(bone))

@utils.bone_event("rigid_body")
def event_rigid_body(context, armature, bone, data):
    if data.hitbox:
        update_rigid_body(data.hitbox.rigid_body, data)


@utils.bone_event("enabled")
def event_enabled(context, armature, bone, data):
    if data.enabled:
        create(context, armature, bone)

    else:
        remove(context, armature, bone)
        armatures.safe_remove_collections(context, armature)
