import bpy
from . import utils
from . import bones
from .bones import (
    restore_bone_parent, store_bone_parent, remove_bone, initialize_bone,
    align_bone, is_bone_enabled, is_bone_active
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


def store_parents(context, armature, data):
    assert armature.mode != 'EDIT'

    if not data.parents_stored:
        data.parents_stored = True

        stored = set()

        for bone in armature.data.bones:
            if store_bone_parent(bone):
                stored.add(bone.name)

            align_bone(armature, bone)

        # TODO if this triggers a mode_switch event then it can break everything
        with utils.Mode(context, 'EDIT'):
            for bone in armature.data.edit_bones:
                if bone.name in stored:
                    bone.parent = None


def restore_parents(context, armature, data):
    if data.parents_stored:
        data.property_unset("parents_stored")

        # Fast O(1) lookup rather than O(n) lookup
        # This converts an O(n^2) algorithm into an O(2n) algorithm
        names = {}
        datas = {}

        # TODO if this triggers a mode_switch event then it can break everything
        with utils.ModeCAS(context, 'EDIT', 'POSE'):
            for bone in armature.data.bones:
                restore_bone_parent(bone, names, datas)

        # TODO if this triggers a mode_switch event then it can break everything
        with utils.Mode(context, 'EDIT'):
            edit_bones = armature.data.edit_bones

            for bone in edit_bones:
                data = datas.get(bone.name)

                if data is not None:
                    (name, use_connect) = data

                    if name == "":
                        bone.parent = None

                    else:
                        parent = edit_bones[names[name]]
                        #if parent is None:
                            #utils.error("[{}] could not find parent \"{}\"".format(bone.name, names[data.parent]))
                        bone.parent = parent

                    bone.use_connect = use_connect


def remove_bone_constraint(pose_bone):
    constraint = pose_bone.constraints.get("Rigid Body Bones [Child Of]")

    if constraint is not None:
        pose_bone.constraints.remove(constraint)


def update_bone_constraint(pose_bone):
    index = None
    found = None

    # TODO can this be replaced with a collection method ?
    for i, constraint in enumerate(pose_bone.constraints):
        if constraint.name == "Rigid Body Bones [Child Of]":
            found = constraint
            index = i
            break

    data = pose_bone.bone.rigid_body_bones

    if is_bone_enabled(data) and is_bone_active(data):
        hitbox = data.hitbox

        assert hitbox is not None

        if found is None:
            index = len(pose_bone.constraints)
            found = pose_bone.constraints.new(type='CHILD_OF')
            found.name = "Rigid Body Bones [Child Of]"
            # TODO verify that this properly sets the inverse
            found.set_inverse_pending = True

        assert index is not None

        if index != 0:
            pose_bone.constraints.move(index, 0)

        found.target = hitbox

    elif found is not None:
        pose_bone.constraints.remove(found)


# TODO non-recursive version ?
def is_active_parent(bone, seen):
    if bone is None:
        return False

    else:
        is_active = seen.get(bone.name)

        if is_active is not None:
            return is_active

        else:
            data = bone.rigid_body_bones

            # Cannot use is_bone_enabled
            if data.enabled and is_bone_active(data):
                seen[bone.name] = True
                return True

            else:
                is_active = is_active_parent(bone.parent, seen)
                seen[bone.name] = is_active
                return is_active


def update_bone_error(context, armature, bone, seen):
    data = bone.rigid_body_bones

    # Cannot use is_bone_enabled
    if data.enabled:
        if is_bone_active(data):
            seen[bone.name] = True
            data.property_unset("error")

        else:
            is_active = is_active_parent(bone.parent, seen)
            seen[bone.name] = is_active

            if is_active:
                data.error = 'ACTIVE_PARENT'
                remove_bone(bone)
                return True

            else:
                data.property_unset("error")
                initialize_bone(context, armature, bone)

    else:
        data.property_unset("error")

    return False


@utils.armature_event("change_parents")
def event_change_parents(context, armature, data):
    if not data.enabled or armature.mode == 'EDIT':
        restore_parents(context, armature, data)

    else:
        store_parents(context, armature, data)


@utils.armature_event("update_errors")
def event_update_errors(context, armature, data):
    assert armature.mode != 'EDIT'

    seen = {}

    data.errors.clear()

    for bone in armature.data.bones:
        if update_bone_error(context, armature, bone, seen):
            error = data.errors.add()
            error.name = bone.name


@utils.armature_event("update_constraints")
def event_update_constraints(context, armature, data):
    if data.enabled:
        if armature.mode != 'EDIT':
            # Create/update/remove Child Of constraints
            for pose_bone in armature.pose.bones:
                update_bone_constraint(pose_bone)

    else:
        # Remove Child Of constraints
        for pose_bone in armature.pose.bones:
            remove_bone_constraint(pose_bone)


@utils.armature_event("hide_active_bones")
def event_hide_active_bones(context, armature, data):
    # utils.SelectedBones(armature),
    with utils.ModeCAS(context, 'EDIT', 'POSE'):
        armature_enabled = data.enabled and data.hide_active_bones

        for bone in armature.data.bones:
            data = bone.rigid_body_bones
            bone.hide = armature_enabled and is_bone_enabled(data) and is_bone_active(data)


@utils.armature_event("hide_hitboxes")
def event_hide_hitboxes(context, armature, data):
    if data.hitboxes:
        if armature.mode == 'EDIT':
            data.hitboxes.hide_viewport = True

        else:
            data.hitboxes.hide_viewport = data.hide_hitboxes


@utils.armature_event("hide_constraints")
def event_hide_constraints(context, armature, data):
    if data.constraints:
        data.constraints.hide_viewport = data.hide_constraints


@utils.armature_event("enabled")
def event_enabled(context, armature, data):
    # utils.SelectedBones(armature),
    with utils.ModeCAS(context, 'EDIT', 'POSE'):
        if data.enabled:
            for bone in armature.data.bones:
                initialize_bone(context, armature, bone)

        else:
            for bone in armature.data.bones:
                remove_bone(bone)

            if data.root_body:
                utils.remove_object(data.root_body)
                data.property_unset("root_body")

            safe_remove_collections(context, armature)


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
            mapping = make_name_mapping(bones, edit_bones)

            data.property_unset("parents_stored")
            data.property_unset("enabled")
            data.property_unset("hide_active_bones")
            data.property_unset("hide_hitboxes")

            for bone in bones:
                edit_bone = edit_bones[bone.name]
                restore_bone_parent(bone, edit_bone, mapping)
                initialize_bone(context, armature, bone)

            # TODO code duplication
            for pose_bone in armature.pose.bones:
                update_bone_constraint(pose_bone)

        return {'FINISHED'}
