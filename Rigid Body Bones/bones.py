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

def origin_name(bone):
    return bone.name + " [Origin]"

def blank_name(bone):
    return bone.name + " [Blank]"

def constraint_name(bone):
    return bone.name + " [Head]"

# TODO respect the 64 character name limit
def compound_name(bone, data):
    return "{} - {} [Compound]".format(bone.name, data.name)

# TODO respect the 64 character name limit
def compound_origin_name(bone, data):
    return "{} - {} [Origin]".format(bone.name, data.name)


def shape_icon(shape):
    if shape == 'BOX':
        return 'MESH_CUBE'
    elif shape == 'SPHERE':
        return 'MESH_UVSPHERE'
    elif shape == 'CAPSULE':
        return 'MESH_CAPSULE'
    elif shape == 'CYLINDER':
        return 'MESH_CYLINDER'
    elif shape == 'CONE':
        return 'MESH_CONE'
    elif shape == 'CONVEX_HULL':
        return 'MESH_ICOSPHERE'
    elif shape == 'MESH':
        return 'MESH_MONKEY'
    elif shape == 'COMPOUND':
        return 'MESH_DATA'



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


def make_compound_hitbox(context, collection, bone, data):
    hitbox = utils.make_mesh_object(
        name=compound_name(bone, data),
        collection=collection,
    )

    utils.select_active(context, hitbox)
    bpy.ops.rigidbody.object_add(type='PASSIVE')

    common_settings(hitbox)

    return hitbox


def make_origin(collection, name):
    origin = bpy.data.objects.new(name=name, object_data=None)
    collection.objects.link(origin)

    origin.rotation_euler = (radians(-90.0), 0.0, 0.0)

    common_settings(origin)
    origin.empty_display_type = 'CIRCLE'

    return origin


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

    # TODO remove this after the clear_mesh bug is fixed
    utils.clear_mesh(body.data)

    return body


def make_blank_rigid_body(context, armature, collection, bone, data):
    return make_empty_rigid_body(
        context,
        name=blank_name(bone),
        collection=collection,
        parent=armature,
        parent_bone=bone.name,
    )


def make_constraint(context, collection, bone):
    empty = bpy.data.objects.new(name=constraint_name(bone), object_data=None)
    collection.objects.link(empty)

    empty.rotation_mode = 'QUATERNION'
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

        if type == 'COMPOUND':
            object.display_bounds_type = 'BOX'
        else:
            object.display_bounds_type = type


def update_hitbox_shape(object, data):
    type = data.collision_shape

    update_shape(object, type=type)

    if type == 'COMPOUND':
        for compound in data.compounds:
            assert compound.hitbox is not None
            update_shape(compound.hitbox, type=compound.collision_shape)


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

    if data.collision_shape == 'COMPOUND':
        for compound in data.compounds:
            compound_body = compound.hitbox.rigid_body

            compound_body.use_margin = compound.use_margin
            compound_body.collision_margin = compound.collision_margin


def is_spring(data):
    return (
        data.use_spring_ang_x or
        data.use_spring_ang_y or
        data.use_spring_ang_z or
        data.use_spring_x or
        data.use_spring_y or
        data.use_spring_z
    )


def update_constraint_active(context, constraint, is_active):
    if is_active:
        if not constraint.rigid_body_constraint:
            utils.select_active(context, constraint)
            bpy.ops.rigidbody.constraint_add(type='FIXED')

    else:
        if constraint.rigid_body_constraint:
            utils.select_active(context, constraint)
            bpy.ops.rigidbody.constraint_remove()


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


def hitbox_scale(data, shape):
    if shape == 'BOX':
        return data.scale
    elif shape == 'SPHERE':
        return Vector((data.scale_diameter, data.scale_diameter, data.scale_diameter))
    else:
        return Vector((data.scale_width, data.scale_length, data.scale_width))

def hitbox_scale_y(data, shape):
    if shape == 'BOX':
        return data.scale.y
    elif shape == 'SPHERE':
        return data.scale_diameter
    else:
        return data.scale_length


# TODO this is called with both Bone and Compound properties
def hitbox_dimensions(data, shape, length):
    dimensions = hitbox_scale(data, shape) * length
    dimensions.rotate(Euler((radians(90.0), 0.0, 0.0)))
    return dimensions


# TODO this is called with both Bone and Compound properties
def hitbox_location(data, shape, length):
    origin = length * (data.origin - 0.5)

    location = Vector((0.0, -origin * hitbox_scale_y(data, shape), 0.0))
    location.rotate(data.rotation)

    location.y += origin - (length * 0.5)
    location += data.location
    return location


# TODO this is called with both Bone and Compound properties
def hitbox_rotation(data):
    rotation = Euler((radians(90.0), 0.0, 0.0))
    rotation.rotate(data.rotation)
    return rotation


def hitbox_origin(data, length):
    return Vector((0.0, length * (data.origin - 1.0), 0.0))


def bone_length(pose_bone):
    return pose_bone.bone.length


def align_compound(hitbox, data, compound, length):
    shape = compound.collision_shape

    location = hitbox_location(compound, shape, length)
    location -= hitbox_origin(data, length)
    location.rotate(Euler((radians(-90.0), 0.0, 0.0)))
    hitbox.location = location

    rotation = hitbox_rotation(compound)
    rotation.rotate(Euler((radians(-90.0), 0.0, 0.0)))
    hitbox.rotation_euler = rotation

    utils.set_mesh_cube(hitbox.data, hitbox_dimensions(compound, shape, length))


def align_hitbox(hitbox, armature, pose_bone, data, is_active):
    shape = data.collision_shape

    length = bone_length(pose_bone)
    location = hitbox_location(data, shape, length)

    if is_bone_active(data):
        hitbox.rigid_body.kinematic = not is_active

        if is_active:
            location.y += length
            assert data.constraint is not None
            utils.set_parent(hitbox, data.constraint)
        else:
            utils.set_bone_parent(hitbox, armature, pose_bone.bone.name)

    hitbox.location = location
    hitbox.rotation_euler = hitbox_rotation(data)

    if shape == 'COMPOUND':
        hitbox.hide_viewport = True
        utils.clear_mesh(hitbox.data)

        for compound in data.compounds:
            align_compound(compound.hitbox, data, compound, length)

    else:
        hitbox.hide_viewport = False
        utils.set_mesh_cube(hitbox.data, hitbox_dimensions(data, shape, length))


def update_origin_size(origin, length):
    origin.empty_display_size = length * 0.05

def update_origin_location(origin, data, shape, length):
    origin.location = (0.0, 0.0, (length * (0.5 - data.origin)) * hitbox_scale_y(data, shape))

def align_origin(origin, pose_bone, data, is_active):
    shape = data.collision_shape

    length = bone_length(pose_bone)

    update_origin_size(origin, length)
    update_origin_location(origin, data, shape, length)

    if shape == 'COMPOUND':
        for compound in data.compounds:
            origin = compound.origin_empty
            update_origin_size(origin, length)
            update_origin_location(origin, compound, compound.collision_shape, length)


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

def remove_compound(data):
    if data.hitbox:
        utils.remove_object(data.hitbox)
        data.property_unset("hitbox")

    if data.origin_empty:
        utils.remove_object(data.origin_empty)
        data.property_unset("origin_empty")

def remove_origin(data):
    if data.origin_empty:
        utils.remove_object(data.origin_empty)
        data.property_unset("origin_empty")

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


CHILD_OF_CONSTRAINT_NAME = "RigidBodyBones [Child Of]"

def find_pose_constraint(constraints):
    index = None
    found = None

    # TODO can this be replaced with a collection method ?
    for i, constraint in enumerate(constraints):
        # Migrate from the old name to the new name
        if constraint.name == "Rigid Body Bones [Child Of]":
            constraint.name = CHILD_OF_CONSTRAINT_NAME

        if constraint.name == CHILD_OF_CONSTRAINT_NAME:
            found = constraint
            index = i
            break

    return (index, found)


def mute_pose_constraint(pose_bone):
    (index, found) = find_pose_constraint(pose_bone.constraints)

    if found:
        found.mute = True
        found.target = None


def remove_pose_constraint(pose_bone, data):
    constraints = pose_bone.constraints

    unmute_constraints(constraints, data)

    (index, found) = find_pose_constraint(constraints)

    if found:
        # TODO can this remove an index instead, to make it faster ?
        constraints.remove(found)


def mute_constraints(constraints, data):
    data.is_constraints_hidden = True

    for constraint in constraints:
        if constraint.name != CHILD_OF_CONSTRAINT_NAME:
            # Unfortunately we cannot save the old muting, so we can't restore it later
            constraint.mute = True


def unmute_constraints(constraints, data):
    if data.is_constraints_hidden:
        data.property_unset("is_constraints_hidden")

        for constraint in constraints:
            if constraint.name != CHILD_OF_CONSTRAINT_NAME:
                # Unfortunately we cannot save the old muting, so we can't restore it
                constraint.mute = False


def create_pose_constraint(armature, pose_bone, data, is_active):
    constraints = pose_bone.constraints

    if is_active:
        mute_constraints(constraints, data)
    else:
        unmute_constraints(constraints, data)


    (index, found) = find_pose_constraint(constraints)

    if found is None:
        index = len(constraints)
        found = constraints.new(type='CHILD_OF')
        found.name = CHILD_OF_CONSTRAINT_NAME

    assert index is not None

    last = len(constraints) - 1

    if index != last:
        constraints.move(index, last)


    hitbox = data.active

    assert hitbox is not None

    found.show_expanded = False

    if is_active:
        found.mute = False
        found.target = hitbox

        found.inverse_matrix = (
            # TODO rather than using matrix_world, instead manually calculate the hitbox's matrix
            # This is the same as the standard Set Inverse
            hitbox.matrix_world.inverted() @ armature.matrix_world @
            # This is needed because we're removing the parent, so we have to preserve the parent transformations
            # It inverts the matrix_basis and matrix_local in order to reset the position to the armature's origin
            # And then it adds the matrix in order to move it to where it should be based on its parent
            pose_bone.matrix @ pose_bone.matrix_basis.inverted() @ pose_bone.bone.matrix_local.inverted()
        )

    else:
        found.mute = True
        found.target = None


# TODO better way of doing this
def copy_properties(active, data):
    data.enabled = active.enabled
    data.type = active.type
    data.location = active.location
    data.rotation = active.rotation
    data.scale = active.scale
    data.scale_diameter = active.scale_diameter
    data.scale_width = active.scale_width
    data.scale_length = active.scale_length
    data.origin = active.origin
    data.mass = active.mass
    data.collision_shape = active.collision_shape
    data.friction = active.friction
    data.restitution = active.restitution
    data.linear_damping = active.linear_damping
    data.angular_damping = active.angular_damping
    data.use_margin = active.use_margin
    data.collision_margin = active.collision_margin
    data.collision_collections = active.collision_collections
    data.use_deactivation = active.use_deactivation
    data.use_start_deactivated = active.use_start_deactivated
    data.deactivate_linear_velocity = active.deactivate_linear_velocity
    data.deactivate_angular_velocity = active.deactivate_angular_velocity
    data.use_override_solver_iterations = active.use_override_solver_iterations
    data.solver_iterations = active.solver_iterations
    data.disable_collisions = active.disable_collisions
    data.use_breaking = active.use_breaking
    data.breaking_threshold = active.breaking_threshold
    data.use_spring_ang_x = active.use_spring_ang_x
    data.use_spring_ang_y = active.use_spring_ang_y
    data.use_spring_ang_z = active.use_spring_ang_z
    data.spring_stiffness_ang_x = active.spring_stiffness_ang_x
    data.spring_stiffness_ang_y = active.spring_stiffness_ang_y
    data.spring_stiffness_ang_z = active.spring_stiffness_ang_z
    data.spring_damping_ang_x = active.spring_damping_ang_x
    data.spring_damping_ang_y = active.spring_damping_ang_y
    data.spring_damping_ang_z = active.spring_damping_ang_z
    data.use_spring_x = active.use_spring_x
    data.use_spring_y = active.use_spring_y
    data.use_spring_z = active.use_spring_z
    data.spring_stiffness_x = active.spring_stiffness_x
    data.spring_stiffness_y = active.spring_stiffness_y
    data.spring_stiffness_z = active.spring_stiffness_z
    data.spring_damping_x = active.spring_damping_x
    data.spring_damping_y = active.spring_damping_y
    data.spring_damping_z = active.spring_damping_z
    data.use_limit_lin_x = active.use_limit_lin_x
    data.use_limit_lin_y = active.use_limit_lin_y
    data.use_limit_lin_z = active.use_limit_lin_z
    data.use_limit_ang_x = active.use_limit_ang_x
    data.use_limit_ang_y = active.use_limit_ang_y
    data.use_limit_ang_z = active.use_limit_ang_z
    data.limit_lin_x_lower = active.limit_lin_x_lower
    data.limit_lin_y_lower = active.limit_lin_y_lower
    data.limit_lin_z_lower = active.limit_lin_z_lower
    data.limit_lin_x_upper = active.limit_lin_x_upper
    data.limit_lin_y_upper = active.limit_lin_y_upper
    data.limit_lin_z_upper = active.limit_lin_z_upper
    data.limit_ang_x_lower = active.limit_ang_x_lower
    data.limit_ang_y_lower = active.limit_ang_y_lower
    data.limit_ang_z_lower = active.limit_ang_z_lower
    data.limit_ang_x_upper = active.limit_ang_x_upper
    data.limit_ang_y_upper = active.limit_ang_y_upper
    data.limit_ang_z_upper = active.limit_ang_z_upper

    data.compounds.clear()

    for compound in active.compounds:
        new = data.compounds.add()
        new.name = compound.name
        new.collision_shape = compound.collision_shape
        new.location = compound.location
        new.rotation = compound.rotation
        new.scale = compound.scale
        new.scale_diameter = compound.scale_diameter
        new.scale_width = compound.scale_width
        new.scale_length = compound.scale_length
        new.origin = compound.origin
        new.use_margin = compound.use_margin
        new.collision_margin = compound.collision_margin

    data.active_compound_index = active.active_compound_index
