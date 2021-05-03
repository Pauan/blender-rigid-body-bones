import time
import bpy
from bpy.app.handlers import persistent
from . import utils
from . import bones


@utils.event("update")
def event_update(context, dirty, armature):
    with utils.Selected(context), utils.Selectable(context):
        utils.select_active(context, armature)
        assert context.active_object.name == armature.name
        bpy.ops.rigid_body_bones.update()


@utils.event("rigid_body")
@utils.if_armature_pose
def event_rigid_body(context, dirty, armature, top):
    for bone in armature.data.bones:
        data = bone.rigid_body_bones

        if data.active:
            bones.update_rigid_body(data.active.rigid_body, data)

        elif data.passive:
            bones.update_rigid_body(data.passive.rigid_body, data)


@utils.event("rigid_body_constraint")
@utils.if_armature_pose
def event_rigid_body_constraint(context, dirty, armature, top):
    for bone in armature.data.bones:
        data = bone.rigid_body_bones

        constraint = data.constraint

        if constraint and constraint.rigid_body_constraint:
            bones.update_joint_constraint(constraint.rigid_body_constraint, data)

        for joint in data.joints:
            constraint = joint.constraint

            if constraint and constraint.rigid_body_constraint:
                bones.update_joint_constraint(constraint.rigid_body_constraint, joint)


@utils.event("align")
@utils.if_armature_pose
def event_align(context, dirty, armature, top):
    for pose_bone in armature.pose.bones:
        bone = pose_bone.bone
        data = bone.rigid_body_bones

        if data.active:
            bones.align_hitbox(data.active, armature, pose_bone, data, False)

        elif data.passive:
            bones.align_hitbox(data.passive, armature, pose_bone, data, False)

        if data.origin_empty:
            bones.align_origin(data.origin_empty, pose_bone, data, False)


@utils.event("hide_hitboxes")
@utils.if_armature_enabled
def event_hide_hitboxes(context, dirty, armature, top):
    if top.actives:
        top.actives.hide_viewport = top.hide_hitboxes

    if top.passives:
        top.passives.hide_viewport = top.hide_hitboxes

    if top.compounds:
        top.compounds.hide_viewport = top.hide_hitboxes

    if top.origins:
        top.origins.hide_viewport = top.hide_hitbox_origins


@utils.event("hide_active_bones")
@utils.if_armature_enabled
def event_hide_active_bones(context, dirty, armature, top):
    for bone in armature.data.bones:
        data = bone.rigid_body_bones
        bones.hide_active_bone(bone, data, top.hide_active_bones)


def mode_switch():
    context = bpy.context

    if utils.is_armature(context):
        armature = context.active_object
        top = armature.data.rigid_body_bones
        mode = armature.mode

        # TODO handle this better, such as a "do not update mode" flag
        if top.mode != mode:
            top.mode = mode
            event_update(None, context)


# TODO make this an event ?
def bone_name_changed():
    context = bpy.context

    if utils.is_armature(context):
        armature = context.active_object

        if armature.mode != 'EDIT':
            # TODO maybe this doesn't need a full update, but only a partial name update ?
            event_update(None, context)


# This is needed to cleanup the rigid body objects when the armature is deleted
def cleanup_armatures():
    if bpy.ops.rigid_body_bones.cleanup_armatures.poll():
        bpy.ops.rigid_body_bones.cleanup_armatures()

    return 5.0


@persistent
def fix_undo(scene):
    context = bpy.context
    event_update(None, context)


owner = object()

def register_subscribers():
    bpy.msgbus.clear_by_owner(owner)

    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Object, "mode"),
        owner=owner,
        args=(),
        notify=mode_switch,
        # TODO does this need PERSISTENT ?
        options={'PERSISTENT'}
    )

    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Bone, "name"),
        owner=owner,
        args=(),
        notify=bone_name_changed,
        # TODO does this need PERSISTENT ?
        options={'PERSISTENT'}
    )

@persistent
def load_post(dummy):
    register_subscribers()

    # When opening an old file, if an armature is selected it will update it.
    # This is only really needed when updating the add-on.
    event_update(None, bpy.context)


def register():
    utils.debug("REGISTER EVENTS")

    # This is needed in order to re-subscribe when the file changes
    bpy.app.handlers.load_post.append(load_post)

    # This is needed in order to fix up problems caused by undo/redo
    #bpy.app.handlers.undo_post.append(fix_undo)
    #bpy.app.handlers.redo_post.append(fix_undo)

    bpy.app.timers.register(cleanup_armatures, persistent=True)

    register_subscribers()


def unregister():
    utils.debug("UNREGISTER EVENTS")

    utils.unregister()

    if bpy.app.timers.is_registered(cleanup_armatures):
        bpy.app.timers.unregister(cleanup_armatures)

    if fix_undo in bpy.app.handlers.redo_post:
        bpy.app.handlers.redo_post.remove(fix_undo)

    if fix_undo in bpy.app.handlers.undo_post:
        bpy.app.handlers.undo_post.remove(fix_undo)

    if load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_post)

    bpy.msgbus.clear_by_owner(owner)
