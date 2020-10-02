import bpy
from . import utils
from . import bones


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
        data.constraints = utils.make_collection(armature.name + " [Constraints]", parent)
        data.constraints.hide_render = True
        data.constraints.hide_viewport = True

    return data.constraints


def hitboxes_collection(context, armature):
    data = armature.data.rigid_body_bones

    if not data.hitboxes:
        parent = root_collection(context)
        data.hitboxes = utils.make_collection(armature.name + " [Hitboxes]", parent)
        data.hitboxes.hide_render = True
        data.hitboxes.hide_viewport = data.hide_hitboxes

    return data.hitboxes


def make_root_body(context, armature, data):
    if not data.root_body:
        data.root_body = make_empty_rigid_body(
            context,
            name=armature.name + " [Root]",
            collection=hitboxes_collection(context, armature),
            parent=armature,
        )

    return data.root_body


def safe_remove_collections(context, armature):
    data = armature.data.rigid_body_bones

    if data.constraints and utils.safe_remove_collection(data.constraints):
        data.constraints = None

    if data.hitboxes and utils.safe_remove_collection(data.hitboxes):
        data.hitboxes = None

    root = context.scene.rigid_body_bones.collection

    if root and utils.safe_remove_collection(root):
        context.scene.rigid_body_bones.collection = None


def make_all(context, armature, data):
    with utils.Mode(context, 'EDIT'):
        for bone in armature.data.edit_bones:
            bones.initialize(context, armature, bone)


def remove_all(context, armature, data):
    with utils.Mode(context, 'EDIT'):
        for bone in armature.data.edit_bones:
            bones.remove(context, armature, bone)

    if data.root_body:
        utils.remove_object(data.root_body)
        data.root_body = None

    if data.constraints:
        utils.remove_collection(data.constraints, recursive=True)
        data.constraints = None

    if data.hitboxes:
        utils.remove_collection(data.hitboxes, recursive=True)
        data.hitboxes = None

    safe_remove_collections(context, armature)


def store_parents(context, armature, data):
    if not data.parents_stored:
        is_enabled = data.enabled

        with utils.Mode(context, 'EDIT'):
            for bone in armature.data.edit_bones:
                bones.store_parent(armature, bone, is_enabled)
                bones.align_hitbox(bone)

        data.parents_stored = True


def restore_parents(context, armature, data):
    if data.parents_stored:
        edit_bones = armature.data.edit_bones

        # Fast O(1) lookup rather than O(n) lookup
        # This converts an O(n^2) algorithm into an O(2n) algorithm
        mapping = {}

        # TODO can this be made faster ?
        for bone in edit_bones:
            bone_data = bone.rigid_body_bones

            if bone_data.is_property_set("name"):
                mapping[bone_data.name] = bone
                bone_data.property_unset("name")

        for bone in edit_bones:
            bones.restore_parent(armature, bone, mapping)

        data.parents_stored = False


def event_mode_switch(context):
    import time
    time_start = time.time()

    # TODO is active_object correct ?
    armature = context.active_object

    if armature and armature.type == 'ARMATURE':
        data = armature.data.rigid_body_bones

        print("MODE SWITCH", armature.mode)

        if armature.mode == 'EDIT':
            restore_parents(context, armature, data)

        else:
            store_parents(context, armature, data)

    print("My Script Finished: %.4f sec" % (time.time() - time_start))


# Aligns the hitboxes while moving bones
def event_timer(context):
    # TODO is active_object correct ?
    armature = context.active_object

    if armature and armature.type == 'ARMATURE' and armature.mode == 'EDIT':
        data = armature.data.rigid_body_bones

        if data.enabled and not data.hide_hitboxes:
            for bone in armature.data.edit_bones:
                pass
                #bones.align_hitbox(bone)


@utils.armature_event("hide_active_bones")
def event_hide_active_bones(context, armature, data):
    hidden = set()

    if data.enabled and data.hide_active_bones:
        with utils.Mode(context, 'EDIT'):
            for bone in armature.data.edit_bones:
                if bones.is_active(bone):
                    hidden.add(bone.name)

    # Cannot hide in EDIT mode
    with utils.SelectedBones(armature), utils.Mode(context, 'POSE'):
        for bone in armature.data.bones:
            bone.hide = (bone.name in hidden)


@utils.armature_event("hide_hitboxes")
def event_hide_hitboxes(context, armature, data):
    if data.hitboxes:
        data.hitboxes.hide_viewport = data.hide_hitboxes


@utils.armature_event("enabled")
def event_enabled(context, armature, data):
    print("ENABLING")

    if data.enabled:
        make_all(context, armature, data)

    else:
        remove_all(context, armature, data)
