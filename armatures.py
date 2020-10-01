import bpy
from . import utils
from . import bones
from . import properties


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


def update_hide_active_bones(context):
    print("update_hide_active_bones")

    # TODO is context.active_object correct ?
    armature = context.active_object
    data = armature.data.rigid_body_bones

    hidden = set()

    if data.enabled and data.hide_active_bones:
        with utils.Mode(context, 'EDIT'):
            for bone in armature.data.edit_bones:
                if bones.is_active(bone):
                    hidden.add(bone.name)

    # Cannot hide in EDIT mode
    with utils.Mode(context, 'POSE'):
        for bone in armature.data.bones:
            if bone.name in hidden:
                bone.hide = True

            else:
                bone.hide = False

properties.Armature.events["enabled"].append(update_hide_active_bones)
properties.Armature.events["hide_active_bones"].append(update_hide_active_bones)
properties.EditBone.events["enabled"].append(update_hide_active_bones)
properties.EditBone.events["type"].append(update_hide_active_bones)


def set_hide_bone_hitboxes(self, context):
    print("hide_bone_hitboxes")

    # TODO is context.active_object correct ?
    armature = context.active_object
    data = armature.data.rigid_body_bones

    if data.hitboxes:
        data.hitboxes.hide_viewport = data.hide_hitboxes


def set_enabled(self, context):
    print("enabled")

    # TODO is context.active_object correct ?
    armature = context.active_object
    data = armature.data.rigid_body_bones

    if data.enabled:
        make_all(context, armature, data)

    else:
        remove_all(context, armature, data)


class SelectInvalidBones(bpy.types.Operator):
    bl_idname = "rigid_body_bones.select_invalid_bones"
    bl_label = "Select invalid bones"
    bl_description = "Selects bones which have invalid properties (such as Parent)"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return utils.is_edit_mode(context)

    def execute(self, context):
        print("Hello World")
        return {'FINISHED'}


class AlignAllHitboxes(bpy.types.Operator):
    bl_idname = "rigid_body_bones.align_all_hitboxes"
    bl_label = "Align all hitboxes"
    bl_description = "Aligns all hitboxes to their respective bones"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_bone is not None)

    def execute(self, context):
        armature = context.active_object
        data = armature.data.rigid_body_bones

        with utils.Mode(context, 'EDIT'), utils.Selectable(context.scene, data), utils.Selected(context):
            for bone in armature.data.edit_bones:
                bones.align_hitbox(context, armature, bone)

        return {'FINISHED'}
