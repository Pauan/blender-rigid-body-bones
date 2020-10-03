import bpy

def make_event(name):
    def update(self, context):
        for f in self.events[name]:
            f(self, context)

    return update


class Scene(bpy.types.PropertyGroup):
    collection: bpy.props.PointerProperty(type=bpy.types.Collection)

    @classmethod
    def register(cls):
        bpy.types.Scene.rigid_body_bones = bpy.props.PointerProperty(type=cls)

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.rigid_body_bones


class Armature(bpy.types.PropertyGroup):
    hitboxes: bpy.props.PointerProperty(type=bpy.types.Collection)
    constraints: bpy.props.PointerProperty(type=bpy.types.Collection)
    root_body: bpy.props.PointerProperty(type=bpy.types.Object)
    parents_stored: bpy.props.BoolProperty(default=False)

    events = {
        "enabled": [],
        "hide_active_bones": [],
        "hide_hitboxes": [],
    }

    enabled: bpy.props.BoolProperty(
        name="Enable rigid bodies",
        description="Enable rigid body physics for armature",
        default=True,
        update=make_event("enabled"),
    )

    hide_active_bones: bpy.props.BoolProperty(
        name="Hide active bones",
        description="Hide bones which have an Active hitbox",
        default=True,
        update=make_event("hide_active_bones"),
    )

    hide_hitboxes: bpy.props.BoolProperty(
        name="Hide hitboxes",
        description="Hide bone hitboxes",
        default=False,
        update=make_event("hide_hitboxes"),
    )

    @classmethod
    def register(cls):
        bpy.types.Armature.rigid_body_bones = bpy.props.PointerProperty(type=cls)

    @classmethod
    def unregister(cls):
        del bpy.types.Armature.rigid_body_bones


class EditBone(bpy.types.PropertyGroup):
    constraint: bpy.props.PointerProperty(type=bpy.types.Object)
    hitbox: bpy.props.PointerProperty(type=bpy.types.Object)

    # These properties are used to save/restore the parent
    # TODO replace with PointerProperty
    name: bpy.props.StringProperty()

    # TODO replace with PointerProperty
    parent: bpy.props.StringProperty(
        name="Parent",
        description="Parent bone for constraint",
    )

    use_connect: bpy.props.BoolProperty(
        name="Connected",
        description="When bone has a parent, bone's head is stuck to the parent's tail",
    )

    events = {
        "enabled": [],
        "type": [],
        "collision_shape": [],
        "location": [],
        "rotation": [],
        "scale": [],
        "origin": [],

        "enable_constraint": [],

        "mass": [],
        "friction": [],
        "restitution": [],
        "linear_damping": [],
        "angular_damping": [],
        "use_margin": [],
        "collision_margin": [],
        "collision_collections": [],
        "use_deactivation": [],
        "use_start_deactivated": [],
        "deactivate_linear_velocity": [],
        "deactivate_angular_velocity": [],
    }

    enabled: bpy.props.BoolProperty(
        name="Enable Rigid Body",
        description="Enable rigid body hitbox for bone",
        default=False,
        options=set(),
        update=make_event("enabled"),
    )

    type: bpy.props.EnumProperty(
        name="Type",
        description="Behavior of the hitbox",
        default='PASSIVE',
        options=set(),
        items=[
            ('PASSIVE', "Passive", "Hitbox follows the bone", 0),
            ('ACTIVE', "Active", "Bone follows the hitbox", 1),
        ],
        update=make_event("type"),
    )

    location: bpy.props.FloatVectorProperty(
        name="Location",
        description="Location of the hitbox relative to the bone",
        size=3,
        default=(0.0, 0.0, 0.0),
        precision=5,
        step=1,
        subtype='XYZ',
        unit='LENGTH',
        options=set(),
        update=make_event("location"),
    )

    rotation: bpy.props.FloatVectorProperty(
        name="Rotation",
        description="Rotation of the hitbox relative to the origin",
        size=3,
        default=(0.0, 0.0, 0.0),
        precision=3,
        step=10,
        subtype='EULER',
        unit='ROTATION',
        options=set(),
        update=make_event("rotation"),
    )

    scale: bpy.props.FloatVectorProperty(
        name="Scale",
        description="Scale of the hitbox relative to the bone length",
        size=3,
        default=(0.2, 1.0, 0.2),
        precision=3,
        step=1,
        subtype='XYZ',
        options=set(),
        update=make_event("scale"),
    )

    origin: bpy.props.FloatProperty(
        name="Origin",
        description="Offset origin (relative to the bone): Head=0, Tail=1",
        default=0.5,
        soft_min=0.0,
        soft_max=1.0,
        precision=3,
        options=set(),
        update=make_event("origin"),
    )

    mass: bpy.props.FloatProperty(
        name="Mass",
        description="How much the hitbox 'weighs' irrespective of gravity",
        default=1.0,
        min=0.001,
        precision=3,
        step=10,
        unit='MASS',
        options=set(),
        update=make_event("mass"),
    )

    collision_shape: bpy.props.EnumProperty(
        name="Collision Shape",
        description="Collision Shape of hitbox in Rigid Body Simulations",
        default='BOX',
        options=set(),
        items=[
            ('BOX', "Box", "Box-like shapes (i.e. cubes), including planes (i.e. ground planes)", 'MESH_CUBE', 2),
            ('SPHERE', "Sphere", "", 'MESH_UVSPHERE', 0),
            ('CAPSULE', "Capsule", "", 'MESH_CAPSULE', 1),
            ('CYLINDER', "Cylinder", "", 'MESH_CYLINDER', 3),
            ('CONE', "Cone", "", "MESH_CONE", 4),
            #('CONVEX_HULL', "Convex Hull", "A mesh-like surface encompassing (i.e. shrinkwrap over) all vertices (best results with fewer vertices)", "MESH_ICOSPHERE", 5),
            #('MESH', "Mesh", "Mesh consisting of triangles only, allowing for more detailed interactions than convex hulls", "MESH_MONKEY", 6),
        ],
        update=make_event("collision_shape"),
    )

    friction: bpy.props.FloatProperty(
        name="Friction",
        description="Resistance of hitbox to movement",
        default=0.5,
        min=0.0,
        soft_max=1.0,
        precision=3,
        options=set(),
        update=make_event("friction"),
    )

    restitution: bpy.props.FloatProperty(
        name="Restitution",
        description="Tendency of hitbox to bounce after colliding with another (0 = stays still, 1 = perfectly elastic)",
        default=0.0,
        min=0.0,
        soft_max=1.0,
        precision=3,
        options=set(),
        update=make_event("restitution"),
    )

    linear_damping: bpy.props.FloatProperty(
        name="Linear Damping",
        description="Amount of linear velocity that is lost over time",
        default=0.04,
        min=0.0,
        max=1.0,
        precision=3,
        options=set(),
        update=make_event("linear_damping"),
    )

    angular_damping: bpy.props.FloatProperty(
        name="Angular Damping",
        description="Amount of angular velocity that is lost over time",
        default=0.1,
        min=0.0,
        max=1.0,
        precision=3,
        options=set(),
        update=make_event("angular_damping"),
    )

    use_margin: bpy.props.BoolProperty(
        name="Collision Margin",
        description="Use custom collision margin",
        default=False,
        options=set(),
        update=make_event("use_margin"),
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
        options=set(),
        update=make_event("collision_margin"),
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
        options=set(),
        update=make_event("collision_collections"),
    )

    use_deactivation: bpy.props.BoolProperty(
        name="Enable Deactivation",
        description="Enable deactivation of resting hitbox (increases performance and stability but can cause glitches)",
        default=False,
        options=set(),
        update=make_event("use_deactivation"),
    )

    use_start_deactivated: bpy.props.BoolProperty(
        name="Start Deactivated",
        description="Deactivate hitbox at the start of the simulation",
        default=False,
        options=set(),
        update=make_event("use_start_deactivated"),
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
        options=set(),
        update=make_event("deactivate_linear_velocity"),
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
        options=set(),
        update=make_event("deactivate_angular_velocity"),
    )

    enable_constraint: bpy.props.BoolProperty(
        name="Enable Constraint",
        description="Enable constraint for hitbox",
        default=True,
        options=set(),
        update=make_event("enable_constraint"),
    )

    @classmethod
    def register(cls):
        bpy.types.EditBone.rigid_body_bones = bpy.props.PointerProperty(type=cls)

    @classmethod
    def unregister(cls):
        del bpy.types.EditBone.rigid_body_bones
