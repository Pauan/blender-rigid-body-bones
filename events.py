import bpy
from bpy.app.handlers import persistent
from . import properties
from . import armatures
from . import bones


fps = 1 / 60

owner = object()

def timer():
    armatures.event_timer(bpy.context)
    return fps


def register_subscribers():
    bpy.msgbus.clear_by_owner(owner)

    # TODO use PERSISTENT ?
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Object, "mode"),
        owner=owner,
        args=(bpy.context,),
        notify=armatures.event_mode_switch,
        options={'PERSISTENT'}
    )

    armatures.event_mode_switch(bpy.context)

@persistent
def load_post(dummy):
    register_subscribers()


def register():
    print("REGISTER EVENTS")

    properties.Armature.events["enabled"].append(armatures.event_enabled)

    properties.Armature.events["enabled"].append(armatures.event_hide_active_bones)
    properties.Armature.events["hide_active_bones"].append(armatures.event_hide_active_bones)
    # TODO more efficient function for these
    properties.EditBone.events["enabled"].append(armatures.event_hide_active_bones)
    properties.EditBone.events["type"].append(armatures.event_hide_active_bones)

    properties.Armature.events["hide_hitboxes"].append(armatures.event_hide_hitboxes)


    properties.EditBone.events["enabled"].append(bones.event_enabled)

    properties.EditBone.events["type"].append(bones.event_type)

    properties.EditBone.events["collision_shape"].append(bones.event_collision_shape)

    properties.EditBone.events["origin"].append(bones.event_location)
    properties.EditBone.events["location"].append(bones.event_location)
    properties.EditBone.events["rotation"].append(bones.event_location)
    properties.EditBone.events["scale"].append(bones.event_location)

    properties.EditBone.events["rotation"].append(bones.event_rotation)

    properties.EditBone.events["scale"].append(bones.event_scale)

    properties.EditBone.events["mass"].append(bones.event_rigid_body)
    properties.EditBone.events["friction"].append(bones.event_rigid_body)
    properties.EditBone.events["restitution"].append(bones.event_rigid_body)
    properties.EditBone.events["linear_damping"].append(bones.event_rigid_body)
    properties.EditBone.events["angular_damping"].append(bones.event_rigid_body)
    properties.EditBone.events["use_margin"].append(bones.event_rigid_body)
    properties.EditBone.events["collision_margin"].append(bones.event_rigid_body)
    properties.EditBone.events["collision_collections"].append(bones.event_rigid_body)
    properties.EditBone.events["use_deactivation"].append(bones.event_rigid_body)
    properties.EditBone.events["use_start_deactivated"].append(bones.event_rigid_body)
    properties.EditBone.events["deactivate_linear_velocity"].append(bones.event_rigid_body)
    properties.EditBone.events["deactivate_angular_velocity"].append(bones.event_rigid_body)


    # This is needed in order to re-subscribe when the file changes
    bpy.app.handlers.load_post.append(load_post)

    register_subscribers()

    # This re-aligns the hitboxes when the bones move
    # TODO super gross, figure out a better way
    bpy.app.timers.register(
        timer,
        first_interval=fps,
        persistent=True,
    )


def unregister():
    print("UNREGISTER EVENTS")

    if bpy.app.timers.is_registered(timer):
        bpy.app.timers.unregister(timer)

    bpy.msgbus.clear_by_owner(owner)

    if load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_post)
