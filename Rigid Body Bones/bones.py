import bpy
from math import radians
from mathutils import Vector, Euler
from . import utils


def is_bone_enabled(data):
    return data.enabled and data.error == ""

def is_bone_active(data):
    return data.type == 'ACTIVE'


def active_name(bone):
    return bone.name + " [Active]"

def passive_name(bone):
    return bone.name + " [Passive]"

def blank_name(bone):
    return bone.name + " [Blank]"

def constraint_name(bone):
    return bone.name + " [Head]"


def common_settings(object):
    object.hide_render = True
    object.show_in_front = True
    object.display.show_shadows = False


def make_active_hitbox(context, armature, collection, bone, data):
    hitbox = utils.make_mesh_object(
        name=active_name(bone),
        collection=collection,
    )

    utils.set_parent(hitbox, armature)

    utils.select_active(context, hitbox)
    bpy.ops.rigidbody.object_add(type='ACTIVE')

    common_settings(hitbox)

    return hitbox


def make_passive_hitbox(context, armature, collection, bone, data):
    hitbox = utils.make_mesh_object(
        name=passive_name(bone),
        collection=collection,
    )

    utils.set_bone_parent(hitbox, armature, bone.name)

    utils.select_active(context, hitbox)
    bpy.ops.rigidbody.object_add(type='PASSIVE')

    hitbox.rigid_body.kinematic = True
    common_settings(hitbox)

    return hitbox


def make_empty_rigid_body(context, name, collection, parent, parent_bone):
    body = utils.make_mesh_object(
        name=name,
        collection=collection,
    )

    if parent_bone is None:
        utils.set_parent(body, parent)

    else:
        utils.set_bone_parent(body, parent, parent_bone)

    utils.select_active(context, body)
    bpy.ops.rigidbody.object_add(type='PASSIVE')

    body.rigid_body.kinematic = True
    body.rigid_body.collision_collections[0] = False

    common_settings(body)
    update_shape(body, type='BOX')

    return body


def make_blank_rigid_body(context, armature, collection, bone, data):
    return make_empty_rigid_body(
        context,
        name=blank_name(bone),
        collection=collection,
        parent=armature,
        parent_bone=bone.name,
    )


def make_constraint(context, armature, collection, bone, data):
    empty = bpy.data.objects.new(name=constraint_name(bone), object_data=None)
    collection.objects.link(empty)

    utils.set_parent(empty, armature)

    utils.select_active(context, empty)
    bpy.ops.rigidbody.constraint_add(type='FIXED')

    empty.hide_render = True
    empty.empty_display_size = 0.0

    return empty


def update_shape(object, type):
    object.rigid_body.collision_shape = type

    if type == 'CONVEX_HULL' or type == 'MESH':
        object.show_bounds = False
        object.display_type = 'WIRE'
        object.display_bounds_type = 'BOX'

    else:
        object.show_bounds = True
        object.display_type = 'BOUNDS'
        object.display_bounds_type = type


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


def is_spring(data):
    return (
        data.use_spring_ang_x or
        data.use_spring_ang_y or
        data.use_spring_ang_z or
        data.use_spring_x or
        data.use_spring_y or
        data.use_spring_z
    )

def update_constraint(constraint, data):
    if is_spring(data):
        constraint.type = 'GENERIC_SPRING'
    else:
        constraint.type = 'GENERIC'

    constraint.disable_collisions = data.disable_collisions
    constraint.use_breaking = data.use_breaking
    constraint.breaking_threshold = data.breaking_threshold
    constraint.use_override_solver_iterations = data.use_override_solver_iterations
    constraint.solver_iterations = data.solver_iterations

    constraint.use_spring_ang_x = data.use_spring_ang_x
    constraint.use_spring_ang_y = data.use_spring_ang_y
    constraint.use_spring_ang_z = data.use_spring_ang_z
    constraint.spring_stiffness_ang_x = data.spring_stiffness_ang_x
    constraint.spring_stiffness_ang_y = data.spring_stiffness_ang_y
    constraint.spring_stiffness_ang_z = data.spring_stiffness_ang_z
    constraint.spring_damping_ang_x = data.spring_damping_ang_x
    constraint.spring_damping_ang_y = data.spring_damping_ang_y
    constraint.spring_damping_ang_z = data.spring_damping_ang_z

    constraint.use_spring_x = data.use_spring_x
    constraint.use_spring_y = data.use_spring_y
    constraint.use_spring_z = data.use_spring_z
    constraint.spring_stiffness_x = data.spring_stiffness_x
    constraint.spring_stiffness_y = data.spring_stiffness_y
    constraint.spring_stiffness_z = data.spring_stiffness_z
    constraint.spring_damping_x = data.spring_damping_x
    constraint.spring_damping_y = data.spring_damping_y
    constraint.spring_damping_z = data.spring_damping_z

    constraint.use_limit_lin_x = data.use_limit_lin_x
    constraint.use_limit_lin_y = data.use_limit_lin_y
    constraint.use_limit_lin_z = data.use_limit_lin_z
    constraint.use_limit_ang_x = data.use_limit_ang_x
    constraint.use_limit_ang_y = data.use_limit_ang_y
    constraint.use_limit_ang_z = data.use_limit_ang_z

    constraint.limit_lin_x_lower = data.limit_lin_x_lower
    constraint.limit_lin_y_lower = data.limit_lin_y_lower
    constraint.limit_lin_z_lower = data.limit_lin_z_lower
    constraint.limit_lin_x_upper = data.limit_lin_x_upper
    constraint.limit_lin_y_upper = data.limit_lin_y_upper
    constraint.limit_lin_z_upper = data.limit_lin_z_upper

    # For some strange reason, Blender flips the min/max for the angular limits
    constraint.limit_ang_x_lower = -data.limit_ang_x_upper
    constraint.limit_ang_x_upper = -data.limit_ang_x_lower

    constraint.limit_ang_y_lower = -data.limit_ang_y_upper
    constraint.limit_ang_y_upper = -data.limit_ang_y_lower

    constraint.limit_ang_z_lower = -data.limit_ang_z_upper
    constraint.limit_ang_z_upper = -data.limit_ang_z_lower


def align_constraint(constraint, bone):
    constraint.location = bone.head_local
    constraint.rotation_euler = bone.matrix_local.to_euler()


def hitbox_dimensions(bone):
    dimensions = bone.rigid_body_bones.scale * bone.length
    dimensions.rotate(Euler((radians(90.0), 0.0, 0.0)))
    return dimensions


def hitbox_location(bone, data):
    length = bone.length
    origin = length * (data.origin - 0.5)

    location = Vector((0.0, -origin * data.scale.y, 0.0))
    location.rotate(data.rotation)

    location.y += origin - (length * 0.5)
    location += data.location

    if is_bone_active(data):
        location.rotate(bone.matrix_local.to_euler())
        location += bone.tail_local

    return location


def hitbox_rotation(bone, data):
    if is_bone_active(data):
        rotation = bone.rigid_body_bones.rotation.copy()
        rotation.rotate(bone.matrix_local.to_euler())
        rotation.rotate_axis('X', radians(90.0))
        return rotation

    else:
        rotation = Euler((radians(90.0), 0.0, 0.0))
        rotation.rotate(bone.rigid_body_bones.rotation)
        return rotation


def align_hitbox(hitbox, bone, data):
    hitbox.location = hitbox_location(bone, data)
    hitbox.rotation_euler = hitbox_rotation(bone, data)
    utils.set_mesh_cube(hitbox.data, hitbox_dimensions(bone))


def update_hitbox_name(hitbox, name):
    hitbox.name = name
    hitbox.data.name = name


def get_hitbox(data):
    if data.active:
        return data.active

    elif data.passive:
        return data.passive

    else:
        return None


def remove_active(data):
    if data.active:
        utils.remove_object(data.active)
        data.property_unset("active")

def remove_passive(data):
    if data.passive:
        utils.remove_object(data.passive)
        data.property_unset("passive")

def remove_blank(data):
    if data.blank:
        utils.remove_object(data.blank)
        data.property_unset("blank")

def remove_constraint(data):
    if data.constraint:
        utils.remove_object(data.constraint)
        data.property_unset("constraint")


def hide_active_bone(bone, data, should_hide):
    if should_hide and is_bone_enabled(data) and is_bone_active(data):
        if not data.is_property_set("is_hidden"):
            data.is_hidden = bone.hide

        bone.hide = True

    elif data.is_property_set("is_hidden"):
        bone.hide = data.is_hidden
        data.property_unset("is_hidden")


def store_parent(bone, data):
    assert not data.is_property_set("name")
    assert not data.is_property_set("parent")
    assert not data.is_property_set("use_connect")

    data.name = bone.name

    parent = bone.parent

    if parent:
        data.parent = parent.name

    else:
        data.parent = ""

    data.use_connect = bone.use_connect


def delete_parent(data):
    assert data.is_property_set("name")
    assert data.is_property_set("parent")
    assert data.is_property_set("use_connect")

    data.property_unset("name")
    data.property_unset("parent")
    data.property_unset("use_connect")


def remove_pose_constraint(pose_bone):
    constraint = pose_bone.constraints.get("Rigid Body Bones [Child Of]")

    if constraint is not None:
        # TODO can this remove an index instead, to make it faster ?
        pose_bone.constraints.remove(constraint)


def update_pose_constraint(pose_bone):
    index = None
    found = None

    constraints = pose_bone.constraints

    # TODO can this be replaced with a collection method ?
    for i, constraint in enumerate(constraints):
        if constraint.name == "Rigid Body Bones [Child Of]":
            found = constraint
            index = i
            break

    data = pose_bone.bone.rigid_body_bones

    if is_bone_enabled(data) and is_bone_active(data):
        hitbox = data.active

        assert hitbox is not None

        if found is None:
            index = len(constraints)
            found = constraints.new(type='CHILD_OF')
            found.name = "Rigid Body Bones [Child Of]"

        # TODO verify that this properly sets the inverse
        # TODO reset the locrotscale ?
        found.set_inverse_pending = True

        assert index is not None

        if index != 0:
            constraints.move(index, 0)

        found.target = hitbox

    elif found is not None:
        # TODO can this remove an index instead, to make it faster ?
        constraints.remove(found)
