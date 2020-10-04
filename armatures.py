import bpy
from . import utils
from . import bones
from .bones import (
    restore_bone_parent, remove_bone_parent, store_bone_parent, remove_bone, initialize_bone,
    align_bone_hitbox, is_bone_active
)


def root_collection(context):
    scene = context.scene

    root = scene.rigid_body_bones.collection

    if not root:
        root = utils.make_collection("RigidBodyBones", scene.collection)
        root.hide_select = True
        root.hide_render = True
        scene.rigid_body_bones.collection = root

    return root


def constraints_collection(context, armature):
    data = armature.data.rigid_body_bones

    if not data.constraints:
        parent = hitboxes_collection(context, armature)
        data.constraints = utils.make_collection(armature.data.name + " [Constraints]", parent)
        data.constraints.hide_render = True
        data.constraints.hide_viewport = data.hide_constraints

    return data.constraints


def hitboxes_collection(context, armature):
    data = armature.data.rigid_body_bones

    if not data.hitboxes:
        parent = root_collection(context)
        data.hitboxes = utils.make_collection(armature.data.name + " [Hitboxes]", parent)
        data.hitboxes.hide_render = True
        data.hitboxes.hide_viewport = data.hide_hitboxes

    return data.hitboxes


def make_root_body(context, armature, data):
    if not data.root_body:
        data.root_body = make_empty_rigid_body(
            context,
            name=armature.data.name + " [Root]",
            collection=hitboxes_collection(context, armature),
            parent=armature,
        )

    return data.root_body


def safe_remove_collections(context, armature):
    data = armature.data.rigid_body_bones

    if data.constraints and utils.safe_remove_collection(data.constraints):
        data.property_unset("constraints")

    if data.hitboxes and utils.safe_remove_collection(data.hitboxes):
        data.property_unset("hitboxes")

    root = context.scene.rigid_body_bones.collection

    if root and utils.safe_remove_collection(root):
        context.scene.rigid_body_bones.property_unset("collection")


def make_all(context, armature, data):
    with utils.Mode(context, 'EDIT'):
        is_stored = data.parents_stored
        edit_bones = armature.data.edit_bones

        for bone in armature.data.bones:
            if is_stored:
                edit_bone = edit_bones[bone.name]
                remove_bone_parent(bone, edit_bone)

            initialize_bone(context, armature, bone)


def remove_all(context, armature, data):
    with utils.Mode(context, 'EDIT'):
        bones = armature.data.bones
        edit_bones = armature.data.edit_bones

        mapping = make_name_mapping(bones, edit_bones, False)

        for bone in bones:
            edit_bone = edit_bones[bone.name]
            restore_bone_parent(bone, edit_bone, mapping, False)
            remove_bone(bone)

    if data.root_body:
        utils.remove_object(data.root_body)
        data.property_unset("root_body")

    safe_remove_collections(context, armature)


# Fast O(1) lookup rather than O(n) lookup
def make_name_mapping(bones, edit_bones, delete):
    mapping = {}

    # TODO can this be made faster ?
    for bone in bones:
        data = bone.rigid_body_bones

        if data.is_property_set("name"):
            mapping[data.name] = edit_bones[bone.name]

            if delete:
                data.property_unset("name")

    return mapping


def store_parents(context, armature, data):
    if not data.parents_stored:
        is_enabled = data.enabled

        with utils.Mode(context, 'EDIT'):
            edit_bones = armature.data.edit_bones

            for bone in armature.data.bones:
                edit_bone = edit_bones[bone.name]
                store_bone_parent(bone, edit_bone, is_enabled)
                align_bone_hitbox(bone)

        data.parents_stored = True


def restore_parents(armature, data):
    if data.parents_stored:
        bones = armature.data.bones
        edit_bones = armature.data.edit_bones

        # This converts an O(n^2) algorithm into an O(2n) algorithm
        mapping = make_name_mapping(bones, edit_bones, True)

        for bone in bones:
            edit_bone = edit_bones[bone.name]
            restore_bone_parent(bone, edit_bone, mapping, True)

        data.property_unset("parents_stored")


def remove_constraints(context, armature, data):
    # Remove Child Of constraints
    for pose_bone in armature.pose.bones:
        for constraint in pose_bone.constraints:
            if constraint.name == "Rigid Body Bones [Child Of]":
                pose_bone.constraints.remove(constraint)
                break


# TODO also run this when enabling/disabling the rigid bodies ?
def update_constraints(context, armature, data):
    # Create/update/remove Child Of constraints
    for pose_bone in armature.pose.bones:
        index = None
        found = None

        for i, constraint in enumerate(pose_bone.constraints):
            if constraint.name == "Rigid Body Bones [Child Of]":
                found = constraint
                index = i
                break

        bone = pose_bone.bone

        if is_bone_active(bone):
            if found is None:
                index = len(pose_bone.constraints)
                found = pose_bone.constraints.new(type='CHILD_OF')
                found.name = "Rigid Body Bones [Child Of]"

            assert index is not None

            if index != 0:
                pose_bone.constraints.move(index, 0)

            hitbox = bone.rigid_body_bones.hitbox
            print(hitbox)
            assert hitbox is not None
            found.target = hitbox

        elif found is not None:
            pose_bone.constraints.remove(found)


def event_mode_switch(context):
    # TODO is active_object correct ?
    armature = context.active_object

    if armature and armature.type == 'ARMATURE':
        data = armature.data.rigid_body_bones

        if armature.mode == 'EDIT':
            restore_parents(armature, data)
            remove_constraints(context, armature, data)

        else:
            store_parents(context, armature, data)
            update_constraints(context, armature, data)


# Aligns the hitboxes while moving bones in Edit mode
def event_timer(context):
    # TODO is active_object correct ?
    armature = context.active_object

    if armature and armature.type == 'ARMATURE' and armature.mode == 'EDIT':
        data = armature.data.rigid_body_bones

        if data.enabled and not data.hide_hitboxes:
            for bone in armature.data.bones:
                align_bone_hitbox(bone)


@utils.armature_event("hide_active_bones")
def event_hide_active_bones(context, armature, data):
    # Cannot hide in EDIT mode
    with utils.SelectedBones(armature), utils.Mode(context, 'POSE'):
        for bone in armature.data.bones:
            bone.hide = is_bone_active(bone)


@utils.armature_event("hide_hitboxes")
def event_hide_hitboxes(context, armature, data):
    if data.hitboxes:
        data.hitboxes.hide_viewport = data.hide_hitboxes

@utils.armature_event("hide_constraints")
def event_hide_constraints(context, armature, data):
    if data.constraints:
        data.constraints.hide_viewport = data.hide_constraints


@utils.armature_event("enabled")
def event_enabled(context, armature, data):
    if data.enabled:
        make_all(context, armature, data)

    else:
        remove_all(context, armature, data)


# TODO remove this
class FactoryDefaults(bpy.types.Operator):
    bl_idname = "rigid_body_bones.factory_default"
    bl_label = "Factory defaults"

    @classmethod
    def poll(cls, context):
        return utils.is_armature(context)

    def execute(self, context):
        armature = context.active_object
        data = armature.data.rigid_body_bones

        with utils.Mode(context, 'EDIT'):
            bones = armature.data.bones
            edit_bones = armature.data.edit_bones

            # This converts an O(n^2) algorithm into an O(2n) algorithm
            mapping = make_name_mapping(bones, edit_bones, True)

            for bone in bones:
                edit_bone = edit_bones[bone.name]
                restore_bone_parent(bone, edit_bone, mapping, True)

            data.property_unset("parents_stored")

            data.enabled = True
            data.hide_active_bones = True
            data.hide_hitboxes = False

        return {'FINISHED'}
