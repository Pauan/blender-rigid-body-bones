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
    enabled: bpy.props.BoolProperty(
        name="Enabled",
        description="Enable rigid body physics for armature",
        default=True,
        update=armature.update,
    )

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
    enabled: bpy.props.BoolProperty(
        name="Enable Rigid Body",
        description="Enable rigid body hitbox for bone",
        default=False,
        update=bone.update,
    )

    type: bpy.props.EnumProperty(
        name="Type",
        description="Behavior of the hitbox",
        default='PASSIVE',
        items=[
            ('PASSIVE', "Passive", "Hitbox follows the bone", 0),
            ('ACTIVE', "Active", "Bone follows the hitbox", 1),
        ],
    )

    x: bpy.props.FloatProperty(
        name="",
        description="Width of the hitbox",
        default=0.0,
        min=0.0,
        precision=5,
        step=1,
        subtype='DISTANCE',
        unit='LENGTH',
        update=bone.update,
    )

    y: bpy.props.FloatProperty(
        name="",
        description="Height of the hitbox",
        default=0.0,
        min=0.0,
        precision=5,
        step=1,
        subtype='DISTANCE',
        unit='LENGTH',
        update=bone.update,
    )

    z: bpy.props.FloatProperty(
        name="",
        description="Length of the hitbox",
        default=0.0,
        min=0.0,
        precision=5,
        step=1,
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

    collision_shape: bpy.props.EnumProperty(
        name="Collision Shape",
        description="Collision Shape of hitbox in Rigid Body Simulations",
        default='CAPSULE',
        items=[
            ('SPHERE', "Sphere", "", 'MESH_UVSPHERE', 0),
            ('CAPSULE', "Capsule", "", 'MESH_CAPSULE', 1),
            ('BOX', "Box", "Box-like shapes (i.e. cubes), including planes (i.e. ground planes)", 'MESH_CUBE', 2),
            ('CYLINDER', "Cylinder", "", 'MESH_CYLINDER', 3),
        ],
    )

    friction: bpy.props.FloatProperty(
        name="Friction",
        description="Resistance of hitbox to movement",
        default=0.5,
        min=0.0,
        soft_max=1.0,
        precision=3,
        update=bone.update,
    )

    restitution: bpy.props.FloatProperty(
        name="Restitution",
        description="Tendency of hitbox to bounce after colliding with another (0 = stays still, 1 = perfectly elastic)",
        default=0.0,
        min=0.0,
        soft_max=1.0,
        precision=3,
        update=bone.update,
    )

    linear_damping: bpy.props.FloatProperty(
        name="Linear Damping",
        description="Amount of linear velocity that is lost over time",
        default=0.04,
        min=0.0,
        max=1.0,
        precision=3,
        update=bone.update,
    )

    angular_damping: bpy.props.FloatProperty(
        name="Angular Damping",
        description="Amount of angular velocity that is lost over time",
        default=0.1,
        min=0.0,
        max=1.0,
        precision=3,
        update=bone.update,
    )

    use_margin: bpy.props.BoolProperty(
        name="Collision Margin",
        description="Use custom collision margin",
        default=False,
        update=bone.update,
    )

    collision_margin: bpy.props.FloatProperty(
        name="Collision Margin",
        description="Threshold of distance near surface where collisions are still considered (best results when non-zero)",
        default=0.04,
        min=0.0,
        max=1.0,
        step=1,
        precision=3,
        subtype='DISTANCE',
        unit='LENGTH',
        update=bone.update,
    )

    collision_collections: bpy.props.BoolVectorProperty(
        name="Collision Collections",
        description="Collision collections hitbox belongs to",
        default=(
            True,  False, False, False, False, False, False, False, False, False,
            False, False, False, False, False, False, False, False, False, False
        ),
        subtype='LAYER_MEMBER',
        size=20,
        update=bone.update,
    )

    use_deactivation: bpy.props.BoolProperty(
        name="Enable Deactivation",
        description="Enable deactivation of resting hitbox (increases performance and stability but can cause glitches)",
        default=False,
        update=bone.update,
    )

    use_start_deactivated: bpy.props.BoolProperty(
        name="Start Deactivated",
        description="Deactivate hitbox at the start of the simulation",
        default=False,
        update=bone.update,
    )

    deactivate_linear_velocity: bpy.props.FloatProperty(
        name="Linear Velocity Deactivation Threshold",
        description="Linear Velocity below which simulation stops simulating hitbox",
        default=0.4,
        min=0.0,
        step=10,
        precision=3,
        # TODO use subtype ?
        unit='VELOCITY',
        update=bone.update,
    )

    deactivate_angular_velocity: bpy.props.FloatProperty(
        name="Angular Velocity Deactivation Threshold",
        description="Angular Velocity below which simulation stops simulating hitbox",
        default=0.5,
        min=0.0,
        step=10,
        precision=3,
        # TODO use subtype ?
        unit='VELOCITY',
        update=bone.update,
    )

    enable_constraint: bpy.props.BoolProperty(
        name="Enable Constraint",
        description="Enable constraint for hitbox",
        default=False,
        update=bone.update,
    )

    # TODO replace with PointerProperty
    parent: bpy.props.StringProperty(name="Parent", description="Parent bone for constraint", update=bone.update)

    @classmethod
    def register(cls):
        bpy.types.EditBone.rigid_body_bones = bpy.props.PointerProperty(type=cls)

    @classmethod
    def unregister(cls):
        del bpy.types.EditBone.rigid_body_bones
