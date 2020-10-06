import bpy
import time
from bpy.app.handlers import persistent
from . import properties
from . import armatures
from . import bones
from . import utils


def mode_switch(context):
    object = context.active_object

    if object and object.type == 'ARMATURE':
        data = object.data.rigid_body_bones

        if data.mode != object.mode:
            data.mode = object.mode

            print("EVENT", "mode_switch", object.mode, "{")

            time_start = time.time()

            for f in properties.Armature.events["mode_switch"]:
                # TODO pass something other than None ?
                f(None, context)

            time_end = time.time()
            utils.print_time(time_start, time_end)

            print("}")


owner = object()

def register_subscribers():
    bpy.msgbus.clear_by_owner(owner)

    # TODO use PERSISTENT ?
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Object, "mode"),
        owner=owner,
        args=(bpy.context,),
        notify=mode_switch,
        options={'PERSISTENT'}
    )

    mode_switch(bpy.context)

@persistent
def load_post(dummy):
    register_subscribers()


def register():
    print("REGISTER EVENTS")

    properties.Bone.events["enabled"].append(bones.event_enabled_remove)
    properties.Bone.events["enabled"].append(bones.event_fix_parent)
    properties.Bone.events["enabled"].append(armatures.event_update_errors)
    properties.Bone.events["enabled"].append(bones.event_enabled_add)
    # TODO more efficient function for this event
    properties.Bone.events["enabled"].append(armatures.event_update_constraints)
    # TODO more efficient function for this event
    properties.Bone.events["enabled"].append(armatures.event_hide_active_bones)

    properties.Bone.events["type"].append(bones.event_type_remove)
    properties.Bone.events["type"].append(bones.event_fix_parent)
    properties.Bone.events["type"].append(armatures.event_update_errors)
    properties.Bone.events["type"].append(bones.event_type_add)
    # TODO more efficient function for this event
    properties.Bone.events["type"].append(armatures.event_update_constraints)
    # TODO more efficient function for this event
    properties.Bone.events["type"].append(armatures.event_hide_active_bones)

    properties.Bone.events["collision_shape"].append(bones.event_collision_shape)

    properties.Bone.events["origin"].append(bones.event_location)

    properties.Bone.events["location"].append(bones.event_location)

    properties.Bone.events["rotation"].append(bones.event_location)

    properties.Bone.events["scale"].append(bones.event_location)

    properties.Bone.events["rotation"].append(bones.event_rotation)

    properties.Bone.events["scale"].append(bones.event_scale)

    properties.Bone.events["mass"].append(bones.event_rigid_body)

    properties.Bone.events["friction"].append(bones.event_rigid_body)

    properties.Bone.events["restitution"].append(bones.event_rigid_body)

    properties.Bone.events["linear_damping"].append(bones.event_rigid_body)

    properties.Bone.events["angular_damping"].append(bones.event_rigid_body)

    properties.Bone.events["use_margin"].append(bones.event_rigid_body)

    properties.Bone.events["collision_margin"].append(bones.event_rigid_body)

    properties.Bone.events["collision_collections"].append(bones.event_rigid_body)

    properties.Bone.events["use_deactivation"].append(bones.event_rigid_body)

    properties.Bone.events["use_start_deactivated"].append(bones.event_rigid_body)

    properties.Bone.events["deactivate_linear_velocity"].append(bones.event_rigid_body)

    properties.Bone.events["deactivate_angular_velocity"].append(bones.event_rigid_body)

    properties.Bone.events["disable_collisions"].append(bones.event_constraint)

    properties.Bone.events["use_breaking"].append(bones.event_constraint)

    properties.Bone.events["breaking_threshold"].append(bones.event_constraint)

    properties.Bone.events["use_override_solver_iterations"].append(bones.event_constraint)

    properties.Bone.events["solver_iterations"].append(bones.event_constraint)

    properties.Bone.events["use_spring_ang_x"].append(bones.event_constraint)

    properties.Bone.events["use_spring_ang_y"].append(bones.event_constraint)

    properties.Bone.events["use_spring_ang_z"].append(bones.event_constraint)

    properties.Bone.events["spring_stiffness_ang_x"].append(bones.event_constraint)

    properties.Bone.events["spring_stiffness_ang_y"].append(bones.event_constraint)

    properties.Bone.events["spring_stiffness_ang_z"].append(bones.event_constraint)

    properties.Bone.events["spring_damping_ang_x"].append(bones.event_constraint)

    properties.Bone.events["spring_damping_ang_y"].append(bones.event_constraint)

    properties.Bone.events["spring_damping_ang_z"].append(bones.event_constraint)

    properties.Bone.events["use_spring_x"].append(bones.event_constraint)

    properties.Bone.events["use_spring_y"].append(bones.event_constraint)

    properties.Bone.events["use_spring_z"].append(bones.event_constraint)

    properties.Bone.events["spring_stiffness_x"].append(bones.event_constraint)

    properties.Bone.events["spring_stiffness_y"].append(bones.event_constraint)

    properties.Bone.events["spring_stiffness_z"].append(bones.event_constraint)

    properties.Bone.events["spring_damping_x"].append(bones.event_constraint)

    properties.Bone.events["spring_damping_y"].append(bones.event_constraint)

    properties.Bone.events["spring_damping_z"].append(bones.event_constraint)

    properties.Armature.events["enabled"].append(armatures.event_remove_orphans)
    properties.Armature.events["enabled"].append(armatures.event_enabled)
    properties.Armature.events["enabled"].append(armatures.event_update_constraints)
    properties.Armature.events["enabled"].append(armatures.event_change_parents)
    properties.Armature.events["enabled"].append(armatures.event_hide_active_bones)

    properties.Armature.events["mode_switch"].append(armatures.event_fix_duplicates)
    properties.Armature.events["mode_switch"].append(armatures.event_update_errors)
    properties.Armature.events["mode_switch"].append(armatures.event_update_joints)
    properties.Armature.events["mode_switch"].append(armatures.event_remove_orphans)
    properties.Armature.events["mode_switch"].append(armatures.event_hide_hitboxes)
    properties.Armature.events["mode_switch"].append(armatures.event_hide_constraints)
    properties.Armature.events["mode_switch"].append(armatures.event_update_constraints)
    properties.Armature.events["mode_switch"].append(armatures.event_change_parents)

    properties.Armature.events["hide_active_bones"].append(armatures.event_hide_active_bones)

    properties.Armature.events["hide_hitboxes"].append(armatures.event_hide_hitboxes)

    properties.Armature.events["hide_constraints"].append(armatures.event_hide_constraints)


    # This is needed in order to re-subscribe when the file changes
    bpy.app.handlers.load_post.append(load_post)

    register_subscribers()


def unregister():
    print("UNREGISTER EVENTS")

    if load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_post)

    bpy.msgbus.clear_by_owner(owner)
