import bpy
from . import armature
from . import bone

class Scene(bpy.types.PropertyGroup):
    collection: bpy.props.PointerProperty(type=bpy.types.Collection)

    @classmethod
    def register(cls):
        bpy.types.Scene.rigid_body_bones = bpy.props.PointerProperty(type=cls)

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.rigid_body_bones


class Armature(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(name="Enabled", description="Enable rigid body physics for armature", update=armature.update)

    hitboxes: bpy.props.PointerProperty(type=bpy.types.Collection)
    constraints: bpy.props.PointerProperty(type=bpy.types.Collection)
    root_body: bpy.props.PointerProperty(type=bpy.types.Object)

    @classmethod
    def register(cls):
        bpy.types.Armature.rigid_body_bones = bpy.props.PointerProperty(type=cls)

    @classmethod
    def unregister(cls):
        del bpy.types.Armature.rigid_body_bones


class EditBone(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(name="Rigid Body", description="Enable rigid body hitbox for bone", update=bone.update)

    type: bpy.props.EnumProperty(
        name="Type",
        description="Behavior of the hitbox",
        default='PASSIVE',
        items=[
            ('PASSIVE', "Passive", "Hitbox moves with the bone", 0),
            ('ACTIVE', "Active", "Bone moves with the hitbox", 1),
        ],
    )

    width: bpy.props.FloatProperty(
        name="Dimensions X",
        description="Width of the hitbox",
        default=0.0,
        min=0.0,
        precision=5,
        step=10,
        subtype='DISTANCE',
        unit='LENGTH',
        update=bone.update,
    )

    height: bpy.props.FloatProperty(
        name="Y",
        description="Height of the hitbox",
        default=0.0,
        min=0.0,
        precision=5,
        step=10,
        subtype='DISTANCE',
        unit='LENGTH',
        update=bone.update,
    )

    length: bpy.props.FloatProperty(
        name="Z",
        description="Length of the hitbox",
        default=0.0,
        min=0.0,
        precision=5,
        step=10,
        subtype='DISTANCE',
        unit='LENGTH',
        update=bone.update,
    )

    mass: bpy.props.FloatProperty(
        name="Mass",
        description="How much the hitbox 'weighs' irrespective of gravity",
        default=1.0,
        min=0.001,
        precision=3,
        step=10,
        unit='MASS',
        update=bone.update,
    )

    shape: bpy.props.EnumProperty(
        name="Shape",
        description="Collision Shape of hitbox in Rigid Body Simulations",
        default='CAPSULE',
        items=[
            ('SPHERE', "Sphere", "", 'MESH_UVSPHERE', 0),
            ('CAPSULE', "Capsule", "", 'MESH_CAPSULE', 1),
            ('BOX', "Box", "Box-like shapes (i.e. cubes), including planes (i.e. ground planes)", 'MESH_CUBE', 2),
            ('CYLINDER', "Cylinder", "", 'MESH_CYLINDER', 3),
            ('CONE', "Cone", "", 'MESH_CONE', 4),
        ],
    )

    enable_constraint: bpy.props.BoolProperty(name="Constraint", description="Enable constraint for hitbox", update=bone.update)
    # TODO replace with PointerProperty
    parent: bpy.props.StringProperty(name="Parent", description="Parent bone for constraint", update=bone.update)

    @classmethod
    def register(cls):
        bpy.types.EditBone.rigid_body_bones = bpy.props.PointerProperty(type=cls)

    @classmethod
    def unregister(cls):
        del bpy.types.EditBone.rigid_body_bones
