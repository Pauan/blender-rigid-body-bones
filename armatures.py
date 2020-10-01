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


def make_all(context, armature, data):
    with utils.Mode(context, 'EDIT'):
        for bone in armature.data.edit_bones:
            bones.initialize(context, armature, bone)


def remove_all(context, armature, data):
    with utils.Mode(context, 'EDIT'):
        for bone in armature.data.edit_bones:
            bones.cleanup(bone)

    hitboxes = data.hitboxes
    data.root_body = None
    data.constraints = None
    data.hitboxes = None

    if hitboxes:
        utils.remove_collection(hitboxes, recursive=True)

    root = context.scene.rigid_body_bones.collection

    if root and utils.safe_remove_collection(root):
        context.scene.rigid_body_bones.collection = None


def hide_bone_hitboxes(self, context):
    pass

def hide_active_bones(self, context):
    pass


def update(self, context):
    print("UPDATING")

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
