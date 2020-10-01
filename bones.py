import bpy
from math import radians
from mathutils import Vector, Euler
from . import armatures
from . import utils


def bone_to_object_space(vector):
    vector.rotate(Euler((radians(90.0), 0.0, 0.0)))

def hitbox_dimensions(bone):
    length = bone.length
    dimensions = Vector((length * 0.2, length, length * 0.2)) * bone.rigid_body_bones.scale
    bone_to_object_space(dimensions)
    return dimensions


def init_hitbox(object, type):
    object.hide_render = True
    object.show_in_front = True
    object.show_bounds = True
    object.display_type = 'BOUNDS'
    object.display_bounds_type = type
    object.display.show_shadows = False
    object.rigid_body.collision_shape = type


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
        body.hide_select = True
        body.hide_viewport = True
        init_hitbox(body, type='BOX')

    return body


def make_active_hitbox(context, armature, bone):
    data = bone.rigid_body_bones

    hitbox = utils.make_cube(
        name=bone.name + " [Hitbox]",
        dimensions=hitbox_dimensions(bone),
        collection=armatures.hitboxes_collection(context, armature),
    )

    hitbox.parent = armature
    hitbox.parent_type = 'OBJECT'

    location = bone.rigid_body_bones.location.copy()
    bone_to_object_space(location)
    location += bone.center

    rotation = bone.rigid_body_bones.rotation.copy()
    rotation.rotate(bone.matrix.to_euler())
    rotation.rotate_axis('X', radians(90.0))

    hitbox.rotation_euler = rotation
    hitbox.location = location

    with utils.Selected(context), utils.Selectable(armatures.root_collection(context)):
        utils.select(context, [hitbox])
        bpy.ops.rigidbody.object_add(type='ACTIVE')
        init_hitbox(hitbox, type=data.collision_shape)

    return hitbox


def make_passive_hitbox(context, armature, bone):
    data = bone.rigid_body_bones

    hitbox = utils.make_cube(
        name=bone.name + " [Hitbox]",
        dimensions=hitbox_dimensions(bone),
        collection=armatures.hitboxes_collection(context, armature),
    )

    hitbox.parent = armature
    hitbox.parent_type = 'BONE'
    hitbox.parent_bone = bone.name

    rotation = Euler((radians(90.0), 0.0, 0.0))
    rotation.rotate(bone.rigid_body_bones.rotation)

    location = Vector((0.0, bone.length * -0.5, 0.0)) + bone.rigid_body_bones.location

    hitbox.rotation_euler = rotation
    hitbox.location = location

    with utils.Selected(context), utils.Selectable(armatures.root_collection(context)):
        utils.select(context, [hitbox])
        bpy.ops.rigidbody.object_add(type='PASSIVE')
        hitbox.rigid_body.kinematic = True
        init_hitbox(hitbox, type=data.collision_shape)

    return hitbox


def create(context, armature, bone):
    data = bone.rigid_body_bones

    if not data.hitbox:
        if data.type == 'ACTIVE':
            data.hitbox = make_active_hitbox(context, armature, bone)

        else:
            data.hitbox = make_passive_hitbox(context, armature, bone)


def remove(context, armature, bone):
    data = bone.rigid_body_bones

    if data.hitbox:
        utils.remove_object(data.hitbox)
        data.hitbox = None

    if data.constraint:
        utils.remove_object(data.constraint)
        data.constraint = None


def initialize(context, armature, bone):
    data = bone.rigid_body_bones

    if data.enabled:
        create(context, armature, bone)


def is_active(bone):
    data = bone.rigid_body_bones

    return data.enabled and data.type == 'ACTIVE'


def align_hitbox(context, armature, bone):
    data = bone.rigid_body_bones
    hitbox = data.hitbox

    if hitbox:
        pass
        #utils.select(context, [hitbox])
        #hitbox.location = hitbox_location(armature, bone)
        #hitbox.rotation = hitbox_rotation(bone)
        #hitbox.dimensions = hitbox_dimensions(bone)
        #bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    if data.constraint:
        pass


def update(self, context):
    print("BONE")

    armature = context.active_object
    bone = context.active_bone

    if self.enabled:
        create(context, armature, bone)
        #update(context, armature, bone)

    else:
        remove(context, armature, bone)
        armatures.safe_remove_collections(context, armature)


class AlignHitbox(bpy.types.Operator):
    bl_idname = "rigid_body_bones.align_hitbox"
    bl_label = "Align to bone"
    bl_description = "Aligns the hitbox to the bone"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return utils.is_edit_mode(context)

    def execute(self, context):
        armature = context.active_object
        data = armature.data.rigid_body_bones

        with utils.Selectable(context.scene, data), utils.Selected(context):
            align_hitbox(context, armature, context.active_bone)

        return {'FINISHED'}
