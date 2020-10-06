import bpy
import time
from . import utils


def make_event(name):
    def update(self, context):
        utils.debug("EVENT {} {{".format(name))

        time_start = time.time()

        for f in self.events[name]:
            f(self, context)

        time_end = time.time()
        utils.print_time(time_start, time_end)

        utils.debug("}")

    return update


class Scene(bpy.types.PropertyGroup):
    collection: bpy.props.PointerProperty(type=bpy.types.Collection)

    @classmethod
    def register(cls):
        bpy.types.Scene.rigid_body_bones = bpy.props.PointerProperty(type=cls)

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.rigid_body_bones


class Error(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()


class Armature(bpy.types.PropertyGroup):
    mode: bpy.props.StringProperty()

    errors: bpy.props.CollectionProperty(type=Error)

    container: bpy.props.PointerProperty(type=bpy.types.Collection)
    actives: bpy.props.PointerProperty(type=bpy.types.Collection)
    passives: bpy.props.PointerProperty(type=bpy.types.Collection)
    blanks: bpy.props.PointerProperty(type=bpy.types.Collection)
    constraints: bpy.props.PointerProperty(type=bpy.types.Collection)

    root_body: bpy.props.PointerProperty(type=bpy.types.Object)
    parents_stored: bpy.props.BoolProperty(default=False)

    events = {
        "mode_switch": [],
        "enabled": [],
        "hide_active_bones": [],
        "hide_hitboxes": [],
    }

    enabled: bpy.props.BoolProperty(
        name="Enable rigid bodies",
        description="Enable rigid body physics for the armature",
        default=True,
        update=make_event("enabled"),
    )

    hide_active_bones: bpy.props.BoolProperty(
        name="Hide active bones",
        description="Hide bones which have an Active rigid body",
        default=False,
        update=make_event("hide_active_bones"),
    )

    hide_hitboxes: bpy.props.BoolProperty(
        name="Hide rigid bodies",
        description="Hide bone rigid bodies",
        default=False,
        update=make_event("hide_hitboxes"),
    )

    @classmethod
    def register(cls):
        bpy.types.Armature.rigid_body_bones = bpy.props.PointerProperty(type=cls)

    @classmethod
    def unregister(cls):
        del bpy.types.Armature.rigid_body_bones


class Bone(bpy.types.PropertyGroup):
    constraint: bpy.props.PointerProperty(type=bpy.types.Object)
    hitbox: bpy.props.PointerProperty(type=bpy.types.Object)
    blank: bpy.props.PointerProperty(type=bpy.types.Object)

    error: bpy.props.StringProperty()

    # These properties are used to save/restore the parent
    # TODO replace with PointerProperty
    name: bpy.props.StringProperty()

    # TODO replace with PointerProperty
    parent: bpy.props.StringProperty(
        name="Parent",
        description="Parent bone for joint",
    )

    use_connect: bpy.props.BoolProperty(
        name="Connected",
        description="When bone has a parent, bone's head is stuck to the parent's tail",
    )

    is_hidden: bpy.props.BoolProperty(default=False)

    events = {
        "enabled": [],
        "type": [],
        "collision_shape": [],
        "location": [],
        "rotation": [],
        "scale": [],
        "origin": [],

        "disable_collisions": [],
        "use_breaking": [],
        "breaking_threshold": [],

        "use_spring_ang_x": [],
        "use_spring_ang_y": [],
        "use_spring_ang_z": [],
        "spring_stiffness_ang_x": [],
        "spring_stiffness_ang_y": [],
        "spring_stiffness_ang_z": [],
        "spring_damping_ang_x": [],
        "spring_damping_ang_y": [],
        "spring_damping_ang_z": [],

        "use_spring_x": [],
        "use_spring_y": [],
        "use_spring_z": [],
        "spring_stiffness_x": [],
        "spring_stiffness_y": [],
        "spring_stiffness_z": [],
        "spring_damping_x": [],
        "spring_damping_y": [],
        "spring_damping_z": [],

        "use_limit_lin_x": [],
        "use_limit_lin_y": [],
        "use_limit_lin_z": [],
        "use_limit_ang_x": [],
        "use_limit_ang_y": [],
        "use_limit_ang_z": [],
        "limit_lin_x_lower": [],
        "limit_lin_y_lower": [],
        "limit_lin_z_lower": [],
        "limit_lin_x_upper": [],
        "limit_lin_y_upper": [],
        "limit_lin_z_upper": [],
        "limit_ang_x_lower": [],
        "limit_ang_y_lower": [],
        "limit_ang_z_lower": [],
        "limit_ang_x_upper": [],
        "limit_ang_y_upper": [],
        "limit_ang_z_upper": [],

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
        "use_override_solver_iterations": [],
        "solver_iterations": [],
    }

    enabled: bpy.props.BoolProperty(
        name="Enable Rigid Body",
        description="Enable rigid body for the bone",
        default=False,
        options=set(),
        update=make_event("enabled"),
    )

    type: bpy.props.EnumProperty(
        name="Type",
        description="Behavior of the rigid body",
        default='PASSIVE',
        options=set(),
        items=[
            ('PASSIVE', "Passive", "Rigid body follows the bone", 0),
            ('ACTIVE', "Active", "Bone follows the rigid body", 1),
        ],
        update=make_event("type"),
    )

    location: bpy.props.FloatVectorProperty(
        name="Location",
        description="Location of the rigid body relative to the bone",
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
        description="Rotation of the rigid body relative to the origin",
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
        description="Scale of the rigid body relative to the bone length",
        size=3,
        default=(0.2, 1.0, 0.2),
        precision=3,
        step=1,
        subtype='XYZ',
        options=set(),
        update=make_event("scale"),
    )

    origin: bpy.props.FloatProperty(
        name="Offset Origin",
        description="Origin relative to the bone: Head=0, Tail=1",
        default=0.5,
        soft_min=0.0,
        soft_max=1.0,
        precision=3,
        options=set(),
        update=make_event("origin"),
    )

    mass: bpy.props.FloatProperty(
        name="Mass",
        description="How much the rigid body 'weighs' irrespective of gravity",
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
        description="Collision shape of the rigid body",
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
        description="Resistance of the rigid body to movement",
        default=0.5,
        min=0.0,
        soft_max=1.0,
        precision=3,
        options=set(),
        update=make_event("friction"),
    )

    restitution: bpy.props.FloatProperty(
        name="Restitution",
        description="Tendency of the rigid body to bounce after colliding with another (0 = stays still, 1 = perfectly elastic)",
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
        unit='LENGTH',
        options=set(),
        update=make_event("collision_margin"),
    )

    collision_collections: bpy.props.BoolVectorProperty(
        name="Collision Collections",
        description="Collision collections the rigid body belongs to",
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
        description="Enable deactivation of resting rigid body (increases performance and stability but can cause glitches)",
        default=False,
        options=set(),
        update=make_event("use_deactivation"),
    )

    use_start_deactivated: bpy.props.BoolProperty(
        name="Start Deactivated",
        description="Deactivate rigid body at the start of the simulation",
        default=False,
        options=set(),
        update=make_event("use_start_deactivated"),
    )

    deactivate_linear_velocity: bpy.props.FloatProperty(
        name="Linear Velocity Deactivation Threshold",
        description="Linear Velocity below which simulation stops simulating the rigid body",
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
        description="Angular Velocity below which simulation stops simulating the rigid body",
        default=0.5,
        min=0.0,
        step=10,
        precision=3,
        # TODO use subtype ?
        unit='VELOCITY',
        options=set(),
        update=make_event("deactivate_angular_velocity"),
    )

    use_override_solver_iterations: bpy.props.BoolProperty(
        name="Override Solver Iterations",
        description="Override the number of solver iterations for the limits",
        default=False,
        options=set(),
        update=make_event("use_override_solver_iterations"),
    )

    solver_iterations: bpy.props.IntProperty(
        name="Solver Iterations",
        description="Number of limit solver iterations made per simulation step (higher values are more accurate but slower)",
        default=10,
        min=1,
        max=1000,
        step=1,
        options=set(),
        update=make_event("solver_iterations"),
    )

    disable_collisions: bpy.props.BoolProperty(
        name="Disable Collisions",
        description="Disable collisions with the parent bone",
        default=True,
        options=set(),
        update=make_event("disable_collisions"),
    )

    use_breaking: bpy.props.BoolProperty(
        name="Breakable",
        description="Limits can be broken if it receives an impulse above the threshold",
        default=False,
        options=set(),
        update=make_event("use_breaking"),
    )

    breaking_threshold: bpy.props.FloatProperty(
        name="Breaking Threshold",
        description="Impulse threshold that must be reached for the limits to break",
        default=10.0,
        min=0.0,
        step=100,
        precision=2,
        options=set(),
        update=make_event("breaking_threshold"),
    )


    use_spring_ang_x: bpy.props.BoolProperty(
        name="X Rotate Spring",
        description="Enable spring on X rotational axis",
        default=False,
        options=set(),
        update=make_event("use_spring_ang_x"),
    )

    use_spring_ang_y: bpy.props.BoolProperty(
        name="Y Rotate Spring",
        description="Enable spring on Y rotational axis",
        default=False,
        options=set(),
        update=make_event("use_spring_ang_y"),
    )

    use_spring_ang_z: bpy.props.BoolProperty(
        name="Z Rotate Spring",
        description="Enable spring on Z rotational axis",
        default=False,
        options=set(),
        update=make_event("use_spring_ang_z"),
    )

    spring_stiffness_ang_x: bpy.props.FloatProperty(
        name="X Rotate Stiffness",
        description="Spring stiffness on the X rotational axis",
        default=10.0,
        min=0.0,
        precision=3,
        step=1,
        options=set(),
        update=make_event("spring_stiffness_ang_x"),
    )

    spring_stiffness_ang_y: bpy.props.FloatProperty(
        name="Y Rotate Stiffness",
        description="Spring stiffness on the Y rotational axis",
        default=10.0,
        min=0.0,
        precision=3,
        step=1,
        options=set(),
        update=make_event("spring_stiffness_ang_y"),
    )

    spring_stiffness_ang_z: bpy.props.FloatProperty(
        name="Z Rotate Stiffness",
        description="Spring stiffness on the Z rotational axis",
        default=10.0,
        min=0.0,
        precision=3,
        step=1,
        options=set(),
        update=make_event("spring_stiffness_ang_z"),
    )

    spring_damping_ang_x: bpy.props.FloatProperty(
        name="X Rotate Damping",
        description="Spring damping on the X rotational axis",
        default=0.5,
        min=0.0,
        precision=3,
        step=10,
        options=set(),
        update=make_event("spring_damping_ang_x"),
    )

    spring_damping_ang_y: bpy.props.FloatProperty(
        name="Y Rotate Damping",
        description="Spring damping on the Y rotational axis",
        default=0.5,
        min=0.0,
        precision=3,
        step=10,
        options=set(),
        update=make_event("spring_damping_ang_y"),
    )

    spring_damping_ang_z: bpy.props.FloatProperty(
        name="Z Rotate Damping",
        description="Spring damping on the Z rotational axis",
        default=0.5,
        min=0.0,
        precision=3,
        step=10,
        options=set(),
        update=make_event("spring_damping_ang_z"),
    )


    use_spring_x: bpy.props.BoolProperty(
        name="X Translate Spring",
        description="Enable spring on X translate axis",
        default=False,
        options=set(),
        update=make_event("use_spring_x"),
    )

    use_spring_y: bpy.props.BoolProperty(
        name="Y Translate Spring",
        description="Enable spring on Y translate axis",
        default=False,
        options=set(),
        update=make_event("use_spring_y"),
    )

    use_spring_z: bpy.props.BoolProperty(
        name="Z Translate Spring",
        description="Enable spring on Z translate axis",
        default=False,
        options=set(),
        update=make_event("use_spring_z"),
    )

    spring_stiffness_x: bpy.props.FloatProperty(
        name="X Translate Stiffness",
        description="Spring stiffness on the X translate axis",
        default=10.0,
        min=0.0,
        precision=3,
        step=1,
        options=set(),
        update=make_event("spring_stiffness_x"),
    )

    spring_stiffness_y: bpy.props.FloatProperty(
        name="Y Translate Stiffness",
        description="Spring stiffness on the Y translate axis",
        default=10.0,
        min=0.0,
        precision=3,
        step=1,
        options=set(),
        update=make_event("spring_stiffness_y"),
    )

    spring_stiffness_z: bpy.props.FloatProperty(
        name="Z Translate Stiffness",
        description="Spring stiffness on the Z translate axis",
        default=10.0,
        min=0.0,
        precision=3,
        step=1,
        options=set(),
        update=make_event("spring_stiffness_z"),
    )

    spring_damping_x: bpy.props.FloatProperty(
        name="X Translate Damping",
        description="Spring damping on the X translate axis",
        default=0.5,
        min=0.0,
        precision=3,
        step=10,
        options=set(),
        update=make_event("spring_damping_x"),
    )

    spring_damping_y: bpy.props.FloatProperty(
        name="Y Translate Damping",
        description="Spring damping on the Y translate axis",
        default=0.5,
        min=0.0,
        precision=3,
        step=10,
        options=set(),
        update=make_event("spring_damping_y"),
    )

    spring_damping_z: bpy.props.FloatProperty(
        name="Z Translate Damping",
        description="Spring damping on the Z translate axis",
        default=0.5,
        min=0.0,
        precision=3,
        step=10,
        options=set(),
        update=make_event("spring_damping_z"),
    )


    use_limit_lin_x: bpy.props.BoolProperty(
        name="X Translate Limit",
        description="Limit translation on X axis",
        default=True,
        options=set(),
        update=make_event("use_limit_lin_x"),
    )

    use_limit_lin_y: bpy.props.BoolProperty(
        name="Y Translate Limit",
        description="Limit translation on Y axis",
        default=True,
        options=set(),
        update=make_event("use_limit_lin_y"),
    )

    use_limit_lin_z: bpy.props.BoolProperty(
        name="Z Translate Limit",
        description="Limit translation on Z axis",
        default=True,
        options=set(),
        update=make_event("use_limit_lin_z"),
    )


    use_limit_ang_x: bpy.props.BoolProperty(
        name="X Rotate Limit",
        description="Limit rotation on X axis",
        default=False,
        options=set(),
        update=make_event("use_limit_ang_x"),
    )

    use_limit_ang_y: bpy.props.BoolProperty(
        name="Y Rotate Limit",
        description="Limit rotation on Y axis",
        default=False,
        options=set(),
        update=make_event("use_limit_ang_y"),
    )

    use_limit_ang_z: bpy.props.BoolProperty(
        name="Z Rotate Limit",
        description="Limit rotation on Z axis",
        default=False,
        options=set(),
        update=make_event("use_limit_ang_z"),
    )


    limit_lin_x_lower: bpy.props.FloatProperty(
        name="Lower X Limit",
        description="Lower limit of X axis translation",
        default=0.0,
        precision=3,
        step=10,
        options=set(),
        unit='LENGTH',
        update=make_event("limit_lin_x_lower"),
    )

    limit_lin_y_lower: bpy.props.FloatProperty(
        name="Lower Y Limit",
        description="Lower limit of Y axis translation",
        default=0.0,
        precision=3,
        step=10,
        options=set(),
        unit='LENGTH',
        update=make_event("limit_lin_y_lower"),
    )

    limit_lin_z_lower: bpy.props.FloatProperty(
        name="Lower Z Limit",
        description="Lower limit of Z axis translation",
        default=0.0,
        precision=3,
        step=10,
        options=set(),
        unit='LENGTH',
        update=make_event("limit_lin_z_lower"),
    )


    limit_lin_x_upper: bpy.props.FloatProperty(
        name="Upper X Limit",
        description="Upper limit of X axis translation",
        default=0.0,
        precision=3,
        step=10,
        options=set(),
        unit='LENGTH',
        update=make_event("limit_lin_x_upper"),
    )

    limit_lin_y_upper: bpy.props.FloatProperty(
        name="Upper Y Limit",
        description="Upper limit of Y axis translation",
        default=0.0,
        precision=3,
        step=10,
        options=set(),
        unit='LENGTH',
        update=make_event("limit_lin_y_upper"),
    )

    limit_lin_z_upper: bpy.props.FloatProperty(
        name="Upper Z Limit",
        description="Upper limit of Z axis translation",
        default=0.0,
        precision=3,
        step=10,
        options=set(),
        unit='LENGTH',
        update=make_event("limit_lin_z_upper"),
    )


    limit_ang_x_lower: bpy.props.FloatProperty(
        name="Lower X Angle Limit",
        description="Lower limit of X axis rotation",
        default=0.0,
        precision=3,
        step=10,
        options=set(),
        subtype='ANGLE',
        unit='ROTATION',
        update=make_event("limit_ang_x_lower"),
    )

    limit_ang_y_lower: bpy.props.FloatProperty(
        name="Lower Y Angle Limit",
        description="Lower limit of Y axis rotation",
        default=0.0,
        precision=3,
        step=10,
        options=set(),
        subtype='ANGLE',
        unit='ROTATION',
        update=make_event("limit_ang_y_lower"),
    )

    limit_ang_z_lower: bpy.props.FloatProperty(
        name="Lower Z Angle Limit",
        description="Lower limit of Z axis rotation",
        default=0.0,
        precision=3,
        step=10,
        options=set(),
        subtype='ANGLE',
        unit='ROTATION',
        update=make_event("limit_ang_z_lower"),
    )


    limit_ang_x_upper: bpy.props.FloatProperty(
        name="Upper X Angle Limit",
        description="Upper limit of X axis rotation",
        default=0.0,
        precision=3,
        step=10,
        options=set(),
        subtype='ANGLE',
        unit='ROTATION',
        update=make_event("limit_ang_x_upper"),
    )

    limit_ang_y_upper: bpy.props.FloatProperty(
        name="Upper Y Angle Limit",
        description="Upper limit of Y axis rotation",
        default=0.0,
        precision=3,
        step=10,
        options=set(),
        subtype='ANGLE',
        unit='ROTATION',
        update=make_event("limit_ang_y_upper"),
    )

    limit_ang_z_upper: bpy.props.FloatProperty(
        name="Upper Z Angle Limit",
        description="Upper limit of Z axis rotation",
        default=0.0,
        precision=3,
        step=10,
        options=set(),
        subtype='ANGLE',
        unit='ROTATION',
        update=make_event("limit_ang_z_upper"),
    )


    @classmethod
    def register(cls):
        bpy.types.Bone.rigid_body_bones = bpy.props.PointerProperty(type=cls)

    @classmethod
    def unregister(cls):
        del bpy.types.Bone.rigid_body_bones
