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


@utils.armature_event("hide_active_bones")
def event_hide_active_bones(context, armature, data):
    hidden = set()

    if data.enabled and data.hide_active_bones:
        with utils.Mode(context, 'EDIT'):
            for bone in armature.data.edit_bones:
                if bones.is_active(bone):
                    hidden.add(bone.name)

    # Cannot hide in EDIT mode
    with utils.Mode(context, 'POSE'):
        for bone in armature.data.bones:
            bone.hide = (bone.name in hidden)


@utils.armature_event("hide_hitboxes")
def event_hide_hitboxes(context, armature, data):
    if data.hitboxes:
        data.hitboxes.hide_viewport = data.hide_hitboxes


@utils.armature_event("enabled")
def event_enabled(context, armature, data):
    if data.enabled:
        make_all(context, armature, data)

    else:
        remove_all(context, armature, data)


def event_mode_switch(context):
    # TODO is active_object correct ?
    armature = context.active_object

    if armature and armature.type == 'ARMATURE':
        data = armature.data.rigid_body_bones

        print(armature.mode)
        #print(data.is_property_set("enabled"))
        #data.property_unset("enabled")
        #print(data.is_property_set("enabled"))

        if armature.mode == 'EDIT':
            for bone in armature.data.edit_bones:
                bones.restore_parent(armature, bone)

        else:
            is_enabled = data.enabled

            with utils.Mode(context, 'EDIT'):
                for bone in armature.data.edit_bones:
                    if is_enabled:
                        bones.store_parent(armature, bone)
                    else:
                        bones.restore_parent(armature, bone)

                    bones.align_hitbox(bone)


def align_all_bones(context):
    # TODO is active_object correct ?
    armature = context.active_object

    if armature and armature.type == 'ARMATURE' and armature.mode == 'EDIT':
        for bone in armature.data.edit_bones:
            bones.align_hitbox(bone)
