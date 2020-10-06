import bpy
from math import radians
from mathutils import Vector, Euler
from . import armatures
from . import utils


def common_settings(object):
    object.hide_render = True
    object.show_in_front = True
    object.display.show_shadows = False


def show_bounds(object, type):
    object.show_bounds = True
    object.display_type = 'BOUNDS'
    object.display_bounds_type = type


def update_shape(object, type):
    object.rigid_body.collision_shape = type

    if type == 'CONVEX_HULL' or type == 'MESH':
        object.show_bounds = False
        object.display_type = 'WIRE'
        object.display_bounds_type = 'BOX'

    else:
        show_bounds(object, type)


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
    body.hide_viewport = True
    common_settings(body)
    show_bounds(body, type='BOX')

    return body


def make_empty(context, name, collection, parent):
    empty = bpy.data.objects.new(name=name, object_data=None)
    collection.objects.link(empty)

    empty.parent = parent
    empty.parent_type = 'OBJECT'

    with utils.Selected(context), utils.Selectable(armatures.root_collection(context)):
        utils.select(context, [empty])
        bpy.ops.rigidbody.constraint_add(type='FIXED')

    common_settings(empty)
    empty.empty_display_type = 'CIRCLE'

    return empty


def align_constraint(constraint, bone):
    constraint.location = bone.head_local
    constraint.rotation_euler = bone.matrix_local.to_euler()
    constraint.empty_display_size = bone.length * 0.2


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


def blank_name(bone):
    return bone.name + " [Blank]"

def constraint_name(bone):
    return bone.name + " [Head]"


def create_constraint(context, armature, bone):
    data = bone.rigid_body_bones

    if not data.constraint:
        constraint = make_empty(
            context,
            name=constraint_name(bone),
            collection=armatures.constraints_collection(context, armature),
            parent=armature,
        )

        align_constraint(constraint, bone)
        update_constraint(constraint.rigid_body_constraint, data)

        data.constraint = constraint


def remove_constraint(bone):
    data = bone.rigid_body_bones

    if data.constraint:
        utils.remove_object(data.constraint)
        data.property_unset("constraint")


def hitbox_dimensions(bone):
    dimensions = bone.rigid_body_bones.scale * bone.length
    dimensions.rotate(Euler((radians(90.0), 0.0, 0.0)))
    return dimensions


def hitbox_location(bone, type):
    data = bone.rigid_body_bones

    length = bone.length
    origin = length * (data.origin - 0.5)

    location = Vector((0.0, -origin * data.scale.y, 0.0))
    location.rotate(data.rotation)

    location.y += origin - (length * 0.5)
    location += data.location

    if type == 'ACTIVE':
        location.rotate(bone.matrix_local.to_euler())
        location += bone.tail_local

    return location


def hitbox_rotation(bone, type):
    if type == 'ACTIVE':
        rotation = bone.rigid_body_bones.rotation.copy()
        rotation.rotate(bone.matrix_local.to_euler())
        rotation.rotate_axis('X', radians(90.0))
        return rotation

    else:
        rotation = Euler((radians(90.0), 0.0, 0.0))
        rotation.rotate(bone.rigid_body_bones.rotation)
        return rotation


def hitbox_name(bone, type):
    if type == 'ACTIVE':
        return bone.name + " [Active]"

    else:
        return bone.name + " [Passive]"


def make_active_hitbox(context, armature, bone):
    data = bone.rigid_body_bones

    hitbox = utils.make_cube(
        name=hitbox_name(bone, 'ACTIVE'),
        dimensions=hitbox_dimensions(bone),
        collection=armatures.actives_collection(context, armature),
    )

    hitbox.parent = armature
    hitbox.parent_type = 'OBJECT'

    hitbox.rotation_euler = hitbox_rotation(bone, 'ACTIVE')
    hitbox.location = hitbox_location(bone, 'ACTIVE')

    with utils.Selected(context), utils.Selectable(armatures.root_collection(context)):
        utils.select(context, [hitbox])
        bpy.ops.rigidbody.object_add(type='ACTIVE')

    update_rigid_body(hitbox.rigid_body, data)
    common_settings(hitbox)
    update_shape(hitbox, type=data.collision_shape)

    return hitbox


def make_passive_hitbox(context, armature, bone):
    data = bone.rigid_body_bones

    hitbox = utils.make_cube(
        name=hitbox_name(bone, 'PASSIVE'),
        dimensions=hitbox_dimensions(bone),
        collection=armatures.passives_collection(context, armature),
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
    common_settings(hitbox)
    update_shape(hitbox, type=data.collision_shape)

    return hitbox


def create(context, armature, bone):
    data = bone.rigid_body_bones

    if not data.hitbox:
        if is_bone_active(data):
            data.hitbox = make_active_hitbox(context, armature, bone)
            create_constraint(context, armature, bone)

        else:
            data.hitbox = make_passive_hitbox(context, armature, bone)
            assert data.constraint is None

    assert data.blank is None


def remove_bone(bone):
    data = bone.rigid_body_bones

    if data.hitbox:
        utils.remove_object(data.hitbox)
        data.property_unset("hitbox")

    remove_constraint(bone)

    assert data.blank is None


def add_bone_objects(bone, exists):
    data = bone.rigid_body_bones

    if data.hitbox:
        exists.add(data.hitbox.name)

    if data.constraint:
        exists.add(data.constraint.name)

    if data.blank:
        exists.add(data.blank.name)


def fix_bone_duplicates(context, armature, bone, seen):
    data = bone.rigid_body_bones

    if data.hitbox:
        name = data.hitbox.name

        if name in seen:
            data.property_unset("hitbox")

        else:
            seen.add(name)

    if data.constraint:
        name = data.constraint.name

        if name in seen:
            data.property_unset("constraint")

        else:
            seen.add(name)

    if data.blank:
        name = data.blank.name

        if name in seen:
            data.property_unset("blank")

        else:
            seen.add(name)


def is_bone_enabled(data):
    return data.enabled and data.error == ""


def initialize_bone(context, armature, bone):
    data = bone.rigid_body_bones

    if is_bone_enabled(data):
        create(context, armature, bone)


def is_bone_active(data):
    return data.type == 'ACTIVE'


def bone_set_inverse(armature, bone, data):
    if is_bone_active(data):
        pose_bone = armature.pose.bones[bone.name]
        constraint = pose_bone.constraints["Rigid Body Bones [Child Of]"]
        constraint.set_inverse_pending = True


def align_bone(armature, bone):
    data = bone.rigid_body_bones

    hitbox = data.hitbox

    if hitbox:
        name = hitbox_name(bone, data.type)
        hitbox.name = name
        hitbox.data.name = name
        hitbox.location = hitbox_location(bone, data.type)
        hitbox.rotation_euler = hitbox_rotation(bone, data.type)
        utils.set_mesh_cube(hitbox.data, hitbox_dimensions(bone))
        bone_set_inverse(armature, bone, data)

    constraint = data.constraint

    if constraint:
        constraint.name = constraint_name(bone)
        align_constraint(constraint, bone)

    blank = data.blank

    if blank:
        blank.name = blank_name(bone)


def store_bone_parent(bone):
    data = bone.rigid_body_bones

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

    return is_bone_enabled(data) and is_bone_active(data)


def restore_bone_parent(bone, names, datas):
    data = bone.rigid_body_bones

    assert data.is_property_set("name")
    assert data.is_property_set("parent")
    assert data.is_property_set("use_connect")

    names[data.name] = bone.name

    if is_bone_enabled(data) and is_bone_active(data):
        datas[bone.name] = (data.parent, data.use_connect)

    data.property_unset("name")
    data.property_unset("parent")
    data.property_unset("use_connect")


@utils.bone_event("type_add")
def event_type_add(context, armature, bone, data):
    initialize_bone(context, armature, bone)

@utils.bone_event("type_remove")
def event_type_remove(context, armature, bone, data):
    remove_bone(bone)


@utils.bone_event("collision_shape")
def event_collision_shape(context, armature, bone, data):
    if data.hitbox:
        update_shape(data.hitbox, data.collision_shape)


@utils.bone_event("location")
def event_location(context, armature, bone, data):
    if data.hitbox:
        data.hitbox.location = hitbox_location(bone, data.type)
        bone_set_inverse(armature, bone, data)

@utils.bone_event("rotation")
def event_rotation(context, armature, bone, data):
    if data.hitbox:
        data.hitbox.rotation_euler = hitbox_rotation(bone, data.type)
        bone_set_inverse(armature, bone, data)

@utils.bone_event("scale")
def event_scale(context, armature, bone, data):
    if data.hitbox:
        utils.set_mesh_cube(data.hitbox.data, hitbox_dimensions(bone))
        bone_set_inverse(armature, bone, data)

@utils.bone_event("rigid_body")
def event_rigid_body(context, armature, bone, data):
    if data.hitbox:
        update_rigid_body(data.hitbox.rigid_body, data)

@utils.bone_event("constraint")
def event_constraint(context, armature, bone, data):
    if data.constraint:
        update_constraint(data.constraint.rigid_body_constraint, data)


@utils.bone_event("enabled_add")
def event_enabled_add(context, armature, bone, data):
    if is_bone_enabled(data):
        create(context, armature, bone)

@utils.bone_event("enabled_remove")
def event_enabled_remove(context, armature, bone, data):
    if not is_bone_enabled(data):
        remove_bone(bone)
        armatures.safe_remove_collections(context, armature)


@utils.bone_event("fix_parent")
def event_fix_parent(context, armature, bone, data):
    assert data.is_property_set("name")
    assert data.is_property_set("parent")
    assert data.is_property_set("use_connect")

    # Cannot use is_bone_enabled because then it won't work if:
    #   1. Changing type from Passive -> Active
    #   2. There was an error when it was Passive
    if data.enabled and is_bone_active(data):
        if bone.parent is not None:
            name = bone.name

            with utils.Mode(context, 'EDIT'):
                armature.data.edit_bones[name].parent = None

    else:
        if bone.parent is None:
            parent = data.parent
            use_connect = data.use_connect

            if parent == "" and bone.use_connect == use_connect:
                return

            name = bone.name
            parent_name = None

            if parent != "":
                # TODO make this faster somehow ?
                for bone in armature.data.bones:
                    if bone.rigid_body_bones.name == parent:
                        parent_name = bone.name
                        break

                assert parent_name is not None

            with utils.Mode(context, 'EDIT'):
                edit_bones = armature.data.edit_bones
                edit_bone = edit_bones[name]

                if parent_name is None:
                    assert edit_bone.parent is None

                else:
                    edit_bone.parent = edit_bones[parent_name]

                edit_bone.use_connect = use_connect
