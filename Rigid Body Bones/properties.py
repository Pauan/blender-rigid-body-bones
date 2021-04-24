import bpy
from . import utils
from .bones import shape_icon
from .events import (
    event_update, event_rigid_body, event_rigid_body_constraint, event_align,
    event_hide_hitboxes, event_hide_active_bones,
)


# Copied from source/blender/blenlib/BLI_math_base.h
# Needed because of source/blender/makesrna/intern/rna_rigidbody.c
MAX_ROT = 3.14159265358979323846 * 2.0
MIN_ROT = -MAX_ROT


class Dirty(bpy.types.PropertyGroup):
    armature: bpy.props.PointerProperty(type=bpy.types.Object)
    update: bpy.props.BoolProperty(default=False)
    rigid_body: bpy.props.BoolProperty(default=False)
    rigid_body_constraint: bpy.props.BoolProperty(default=False)
    align: bpy.props.BoolProperty(default=False)
    hide_hitboxes: bpy.props.BoolProperty(default=False)
    hide_active_bones: bpy.props.BoolProperty(default=False)


class Scene(bpy.types.PropertyGroup):
    dirties: bpy.props.CollectionProperty(type=Dirty)
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
    compounds: bpy.props.PointerProperty(type=bpy.types.Collection)
    origins: bpy.props.PointerProperty(type=bpy.types.Collection)
    blanks: bpy.props.PointerProperty(type=bpy.types.Collection)
    constraints: bpy.props.PointerProperty(type=bpy.types.Collection)

    root_body: bpy.props.PointerProperty(type=bpy.types.Object)
    parents_stored: bpy.props.BoolProperty(default=False)


    enabled: bpy.props.BoolProperty(
        name="Enable rigid body physics",
        description="Enable rigid body physics for the armature",
        default=True,
        update=event_update,
    )

    hide_active_bones: bpy.props.BoolProperty(
        name="Hide active bones",
        description="Hide bones which have an Active rigid body",
        default=False,
        update=event_hide_active_bones,
    )

    hide_hitboxes: bpy.props.BoolProperty(
        name="Hide hitboxes",
        description="Hide bone hitboxes",
        default=False,
        update=event_hide_hitboxes,
    )

    hide_hitbox_origins: bpy.props.BoolProperty(
        name="Hide hitbox origins",
        description="Hide origins for hitboxes",
        default=False,
        update=event_hide_hitboxes,
    )


    @classmethod
    def register(cls):
        bpy.types.Armature.rigid_body_bones = bpy.props.PointerProperty(type=cls)

    @classmethod
    def unregister(cls):
        del bpy.types.Armature.rigid_body_bones


class ShapeProperties:
    location: bpy.props.FloatVectorProperty(
        name="Location",
        description="Location of the hitbox relative to the origin",
        size=3,
        default=(0.0, 0.0, 0.0),
        precision=5,
        step=1,
        subtype='XYZ',
        unit='LENGTH',
        options=set(),
        update=event_align,
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
        update=event_align,
    )

    scale: bpy.props.FloatVectorProperty(
        name="Scale",
        description="Scale of the hitbox relative to the bone length",
        size=3,
        default=(0.2, 1.0, 0.2),
        min=0.0,
        precision=3,
        step=1,
        subtype='XYZ',
        options=set(),
        update=event_align,
    )

    scale_width: bpy.props.FloatProperty(
        name="Scale Width",
        description="Width of the hitbox relative to the bone length",
        default=0.2,
        min=0.0,
        precision=3,
        step=1,
        options=set(),
        update=event_align,
    )

    scale_length: bpy.props.FloatProperty(
        name="Scale Length",
        description="Length of the hitbox relative to the bone length",
        default=1.0,
        min=0.0,
        precision=3,
        step=1,
        options=set(),
        update=event_align,
    )

    scale_diameter: bpy.props.FloatProperty(
        name="Scale Diameter",
        description="Diameter of the hitbox relative to the bone length",
        default=1.0,
        min=0.0,
        precision=3,
        step=1,
        options=set(),
        update=event_align,
    )

    origin: bpy.props.FloatProperty(
        name="Offset Origin",
        description="Origin relative to the bone: Head=0, Tail=1",
        default=0.5,
        soft_min=0.0,
        soft_max=1.0,
        precision=3,
        options=set(),
        update=event_align,
    )

    use_margin: bpy.props.BoolProperty(
        name="Collision Margin",
        description="Use custom collision margin for the hitbox",
        default=False,
        options=set(),
        update=event_rigid_body,
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
        update=event_rigid_body,
    )


class Compound(bpy.types.PropertyGroup, ShapeProperties):
    # TODO make a Context object for this ?
    is_updating = False

    def update_name(self, context):
        if not Compound.is_updating:
            armature = context.active_object
            bone = utils.get_active_bone(armature)
            data = bone.rigid_body_bones

            seen = set()

            for compound in data.compounds:
                if compound != self:
                    seen.add(compound.name)

            if self.name in seen:
                Compound.is_updating = True
                self.name = utils.make_unique_name(utils.strip_name_suffix(self.name), seen)
                Compound.is_updating = False

            event_update(None, context)

    hitbox: bpy.props.PointerProperty(type=bpy.types.Object)
    origin_empty: bpy.props.PointerProperty(type=bpy.types.Object)

    name: bpy.props.StringProperty(update=update_name)

    # TODO some code duplication
    collision_shape: bpy.props.EnumProperty(
        name="Collision Shape",
        description="Collision shape of the hitbox",
        default='BOX',
        options=set(),
        items=[
            ('BOX', "Box", "", shape_icon('BOX'), 2),
            ('SPHERE', "Sphere", "", shape_icon('SPHERE'), 0),
            ('CAPSULE', "Capsule", "", shape_icon('CAPSULE'), 1),
            ('CYLINDER', "Cylinder", "", shape_icon('CYLINDER'), 3),
            #('CONE', "Cone", "", shape_icon('CONE'), 4),
            #('CONVEX_HULL', "Convex Hull", "A mesh-like surface encompassing (i.e. shrinkwrap over) all vertices (best results with fewer vertices)", shape_icon('CONVEX_HULL'), 5),
            #('MESH', "Mesh", "Mesh consisting of triangles only, allowing for more detailed interactions than convex hulls", shape_icon('MESH'), 6),
        ],
        # TODO more efficient event for this ?
        update=event_update,
    )


class Bone(bpy.types.PropertyGroup, ShapeProperties):
    active: bpy.props.PointerProperty(type=bpy.types.Object)
    passive: bpy.props.PointerProperty(type=bpy.types.Object)
    origin_empty: bpy.props.PointerProperty(type=bpy.types.Object)
    blank: bpy.props.PointerProperty(type=bpy.types.Object)
    constraint: bpy.props.PointerProperty(type=bpy.types.Object)

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

    is_constraints_hidden: bpy.props.BoolProperty(default=False)


    compounds: bpy.props.CollectionProperty(type=Compound)

    active_compound_index: bpy.props.IntProperty(name="", description="", default=0, min=0, subtype='UNSIGNED')


    enabled: bpy.props.BoolProperty(
        name="Enable Rigid Body",
        description="Enable rigid body physics for the bone",
        default=False,
        options=set(),
        update=event_update,
    )

    type: bpy.props.EnumProperty(
        name="Type",
        description="Behavior of the bone physics",
        default='PASSIVE',
        options=set(),
        items=[
            ('PASSIVE', "Passive", "Bone stays still unless manually moved", 0),
            ('ACTIVE', "Active", "Bone automatically moves", 1),
        ],
        update=event_update,
    )

    mass: bpy.props.FloatProperty(
        name="Mass",
        description="How much the bone 'weighs' irrespective of gravity",
        default=1.0,
        min=0.001,
        precision=3,
        step=10,
        unit='MASS',
        options=set(),
        update=event_rigid_body,
    )

    collision_shape: bpy.props.EnumProperty(
        name="Collision Shape",
        description="Collision shape of the hitbox",
        default='BOX',
        options=set(),
        items=[
            ('BOX', "Box", "", shape_icon('BOX'), 2),
            ('SPHERE', "Sphere", "", shape_icon('SPHERE'), 0),
            ('CAPSULE', "Capsule", "", shape_icon('CAPSULE'), 1),
            ('CYLINDER', "Cylinder", "", shape_icon('CYLINDER'), 3),
            #('CONE', "Cone", "", shape_icon('CONE'), 4),
            #('CONVEX_HULL', "Convex Hull", "A mesh-like surface encompassing (i.e. shrinkwrap over) all vertices (best results with fewer vertices)", shape_icon('CONVEX_HULL'), 5),
            #('MESH', "Mesh", "Mesh consisting of triangles only, allowing for more detailed interactions than convex hulls", shape_icon('MESH'), 6),
            None,
            ('COMPOUND', "Compound", "Combines multiple hitboxes into one hitbox", shape_icon('COMPOUND'), 7),
        ],
        update=event_update,
    )

    friction: bpy.props.FloatProperty(
        name="Friction",
        description="Resistance of the bone to movement",
        default=0.5,
        min=0.0,
        soft_max=1.0,
        precision=3,
        options=set(),
        update=event_rigid_body,
    )

    restitution: bpy.props.FloatProperty(
        name="Restitution",
        description="Tendency of the bone to bounce after colliding (0 = stays still, 1 = perfectly elastic)",
        default=0.0,
        min=0.0,
        soft_max=1.0,
        precision=3,
        options=set(),
        update=event_rigid_body,
    )

    linear_damping: bpy.props.FloatProperty(
        name="Linear Damping",
        description="Amount of linear velocity that is lost over time",
        default=0.04,
        min=0.0,
        max=1.0,
        precision=3,
        options=set(),
        update=event_rigid_body,
    )

    angular_damping: bpy.props.FloatProperty(
        name="Angular Damping",
        description="Amount of angular velocity that is lost over time",
        default=0.1,
        min=0.0,
        max=1.0,
        precision=3,
        options=set(),
        update=event_rigid_body,
    )

    collision_collections: bpy.props.BoolVectorProperty(
        name="Collision Layers",
        description="The hitbox will only collide with other objects in the same collision layer",
        default=(
            True,  False, False, False, False, False, False, False, False, False,
            False, False, False, False, False, False, False, False, False, False
        ),
        subtype='LAYER_MEMBER',
        size=20,
        options=set(),
        update=event_rigid_body,
    )

    use_deactivation: bpy.props.BoolProperty(
        name="Enable Deactivation",
        description="Enable deactivation of non-moving bones (increases performance and stability but can cause glitches)",
        default=False,
        options=set(),
        update=event_rigid_body,
    )

    use_start_deactivated: bpy.props.BoolProperty(
        name="Start Deactivated",
        description="Deactivate the bone's physics at the start of the simulation",
        default=False,
        options=set(),
        update=event_rigid_body,
    )

    deactivate_linear_velocity: bpy.props.FloatProperty(
        name="Linear Velocity Deactivation Threshold",
        description="Linear Velocity below which simulation stops simulating the bone's physics",
        default=0.4,
        min=0.0,
        step=10,
        precision=3,
        # TODO use subtype ?
        unit='VELOCITY',
        options=set(),
        update=event_rigid_body,
    )

    deactivate_angular_velocity: bpy.props.FloatProperty(
        name="Angular Velocity Deactivation Threshold",
        description="Angular Velocity below which simulation stops simulating the bone's physics",
        default=0.5,
        min=0.0,
        step=10,
        precision=3,
        # TODO use subtype ?
        unit='VELOCITY',
        options=set(),
        update=event_rigid_body,
    )

    use_override_solver_iterations: bpy.props.BoolProperty(
        name="Override Solver Iterations",
        description="Override the number of solver iterations for the limits",
        default=False,
        options=set(),
        update=event_rigid_body_constraint,
    )

    solver_iterations: bpy.props.IntProperty(
        name="Solver Iterations",
        description="Number of limit solver iterations made per simulation step (higher values are more accurate but slower)",
        default=10,
        min=1,
        max=1000,
        step=1,
        options=set(),
        update=event_rigid_body_constraint,
    )

    disable_collisions: bpy.props.BoolProperty(
        name="Disable Parent Collisions",
        description="Disable collisions with the parent bone",
        default=True,
        options=set(),
        update=event_rigid_body_constraint,
    )

    use_breaking: bpy.props.BoolProperty(
        name="Breakable",
        description="Limits can be broken if it receives an impulse above the threshold",
        default=False,
        options=set(),
        update=event_rigid_body_constraint,
    )

    breaking_threshold: bpy.props.FloatProperty(
        name="Breaking Threshold",
        description="Impulse threshold that must be reached for the limits to break",
        default=10.0,
        min=0.0,
        step=100,
        precision=2,
        options=set(),
        update=event_rigid_body_constraint,
    )


    use_spring_ang_x: bpy.props.BoolProperty(
        name="Enable X Rotate Spring",
        description="Enable spring on X rotational axis",
        default=False,
        options=set(),
        update=event_rigid_body_constraint,
    )

    use_spring_ang_y: bpy.props.BoolProperty(
        name="Enable Y Rotate Spring",
        description="Enable spring on Y rotational axis",
        default=False,
        options=set(),
        update=event_rigid_body_constraint,
    )

    use_spring_ang_z: bpy.props.BoolProperty(
        name="Enable Z Rotate Spring",
        description="Enable spring on Z rotational axis",
        default=False,
        options=set(),
        update=event_rigid_body_constraint,
    )

    spring_stiffness_ang_x: bpy.props.FloatProperty(
        name="X Rotate Stiffness",
        description="Spring stiffness on the X rotational axis",
        default=10.0,
        min=0.0,
        precision=3,
        step=1,
        options=set(),
        update=event_rigid_body_constraint,
    )

    spring_stiffness_ang_y: bpy.props.FloatProperty(
        name="Y Rotate Stiffness",
        description="Spring stiffness on the Y rotational axis",
        default=10.0,
        min=0.0,
        precision=3,
        step=1,
        options=set(),
        update=event_rigid_body_constraint,
    )

    spring_stiffness_ang_z: bpy.props.FloatProperty(
        name="Z Rotate Stiffness",
        description="Spring stiffness on the Z rotational axis",
        default=10.0,
        min=0.0,
        precision=3,
        step=1,
        options=set(),
        update=event_rigid_body_constraint,
    )

    spring_damping_ang_x: bpy.props.FloatProperty(
        name="X Rotate Damping",
        description="Spring damping on the X rotational axis",
        default=0.5,
        min=0.0,
        precision=3,
        step=10,
        options=set(),
        update=event_rigid_body_constraint,
    )

    spring_damping_ang_y: bpy.props.FloatProperty(
        name="Y Rotate Damping",
        description="Spring damping on the Y rotational axis",
        default=0.5,
        min=0.0,
        precision=3,
        step=10,
        options=set(),
        update=event_rigid_body_constraint,
    )

    spring_damping_ang_z: bpy.props.FloatProperty(
        name="Z Rotate Damping",
        description="Spring damping on the Z rotational axis",
        default=0.5,
        min=0.0,
        precision=3,
        step=10,
        options=set(),
        update=event_rigid_body_constraint,
    )


    use_spring_x: bpy.props.BoolProperty(
        name="Enable X Translate Spring",
        description="Enable spring on X translate axis",
        default=False,
        options=set(),
        update=event_rigid_body_constraint,
    )

    use_spring_y: bpy.props.BoolProperty(
        name="Enable Y Translate Spring",
        description="Enable spring on Y translate axis",
        default=False,
        options=set(),
        update=event_rigid_body_constraint,
    )

    use_spring_z: bpy.props.BoolProperty(
        name="Enable Z Translate Spring",
        description="Enable spring on Z translate axis",
        default=False,
        options=set(),
        update=event_rigid_body_constraint,
    )

    spring_stiffness_x: bpy.props.FloatProperty(
        name="X Translate Stiffness",
        description="Spring stiffness on the X translate axis",
        default=10.0,
        min=0.0,
        precision=3,
        step=1,
        options=set(),
        update=event_rigid_body_constraint,
    )

    spring_stiffness_y: bpy.props.FloatProperty(
        name="Y Translate Stiffness",
        description="Spring stiffness on the Y translate axis",
        default=10.0,
        min=0.0,
        precision=3,
        step=1,
        options=set(),
        update=event_rigid_body_constraint,
    )

    spring_stiffness_z: bpy.props.FloatProperty(
        name="Z Translate Stiffness",
        description="Spring stiffness on the Z translate axis",
        default=10.0,
        min=0.0,
        precision=3,
        step=1,
        options=set(),
        update=event_rigid_body_constraint,
    )

    spring_damping_x: bpy.props.FloatProperty(
        name="X Translate Damping",
        description="Spring damping on the X translate axis",
        default=0.5,
        min=0.0,
        precision=3,
        step=10,
        options=set(),
        update=event_rigid_body_constraint,
    )

    spring_damping_y: bpy.props.FloatProperty(
        name="Y Translate Damping",
        description="Spring damping on the Y translate axis",
        default=0.5,
        min=0.0,
        precision=3,
        step=10,
        options=set(),
        update=event_rigid_body_constraint,
    )

    spring_damping_z: bpy.props.FloatProperty(
        name="Z Translate Damping",
        description="Spring damping on the Z translate axis",
        default=0.5,
        min=0.0,
        precision=3,
        step=10,
        options=set(),
        update=event_rigid_body_constraint,
    )


    use_limit_lin_x: bpy.props.BoolProperty(
        name="X Translate Limit",
        description="Limit translation on X axis",
        default=True,
        options=set(),
        update=event_rigid_body_constraint,
    )

    use_limit_lin_y: bpy.props.BoolProperty(
        name="Y Translate Limit",
        description="Limit translation on Y axis",
        default=True,
        options=set(),
        update=event_rigid_body_constraint,
    )

    use_limit_lin_z: bpy.props.BoolProperty(
        name="Z Translate Limit",
        description="Limit translation on Z axis",
        default=True,
        options=set(),
        update=event_rigid_body_constraint,
    )


    use_limit_ang_x: bpy.props.BoolProperty(
        name="X Rotate Limit",
        description="Limit rotation on X axis",
        default=False,
        options=set(),
        update=event_rigid_body_constraint,
    )

    use_limit_ang_y: bpy.props.BoolProperty(
        name="Y Rotate Limit",
        description="Limit rotation on Y axis",
        default=False,
        options=set(),
        update=event_rigid_body_constraint,
    )

    use_limit_ang_z: bpy.props.BoolProperty(
        name="Z Rotate Limit",
        description="Limit rotation on Z axis",
        default=False,
        options=set(),
        update=event_rigid_body_constraint,
    )


    limit_lin_x_lower: bpy.props.FloatProperty(
        name="Lower X Limit",
        description="Lower limit of X axis translation",
        default=0.0,
        precision=3,
        step=10,
        options=set(),
        unit='LENGTH',
        update=event_rigid_body_constraint,
    )

    limit_lin_y_lower: bpy.props.FloatProperty(
        name="Lower Y Limit",
        description="Lower limit of Y axis translation",
        default=0.0,
        precision=3,
        step=10,
        options=set(),
        unit='LENGTH',
        update=event_rigid_body_constraint,
    )

    limit_lin_z_lower: bpy.props.FloatProperty(
        name="Lower Z Limit",
        description="Lower limit of Z axis translation",
        default=0.0,
        precision=3,
        step=10,
        options=set(),
        unit='LENGTH',
        update=event_rigid_body_constraint,
    )


    limit_lin_x_upper: bpy.props.FloatProperty(
        name="Upper X Limit",
        description="Upper limit of X axis translation",
        default=0.0,
        precision=3,
        step=10,
        options=set(),
        unit='LENGTH',
        update=event_rigid_body_constraint,
    )

    limit_lin_y_upper: bpy.props.FloatProperty(
        name="Upper Y Limit",
        description="Upper limit of Y axis translation",
        default=0.0,
        precision=3,
        step=10,
        options=set(),
        unit='LENGTH',
        update=event_rigid_body_constraint,
    )

    limit_lin_z_upper: bpy.props.FloatProperty(
        name="Upper Z Limit",
        description="Upper limit of Z axis translation",
        default=0.0,
        precision=3,
        step=10,
        options=set(),
        unit='LENGTH',
        update=event_rigid_body_constraint,
    )


    limit_ang_x_lower: bpy.props.FloatProperty(
        name="Lower X Angle Limit",
        description="Lower limit of X axis rotation",
        default=0.0,
        min=MIN_ROT,
        max=MAX_ROT,
        precision=3,
        step=10,
        options=set(),
        subtype='ANGLE',
        unit='ROTATION',
        update=event_rigid_body_constraint,
    )

    limit_ang_y_lower: bpy.props.FloatProperty(
        name="Lower Y Angle Limit",
        description="Lower limit of Y axis rotation",
        default=0.0,
        min=MIN_ROT,
        max=MAX_ROT,
        precision=3,
        step=10,
        options=set(),
        subtype='ANGLE',
        unit='ROTATION',
        update=event_rigid_body_constraint,
    )

    limit_ang_z_lower: bpy.props.FloatProperty(
        name="Lower Z Angle Limit",
        description="Lower limit of Z axis rotation",
        default=0.0,
        min=MIN_ROT,
        max=MAX_ROT,
        precision=3,
        step=10,
        options=set(),
        subtype='ANGLE',
        unit='ROTATION',
        update=event_rigid_body_constraint,
    )


    limit_ang_x_upper: bpy.props.FloatProperty(
        name="Upper X Angle Limit",
        description="Upper limit of X axis rotation",
        default=0.0,
        min=MIN_ROT,
        max=MAX_ROT,
        precision=3,
        step=10,
        options=set(),
        subtype='ANGLE',
        unit='ROTATION',
        update=event_rigid_body_constraint,
    )

    limit_ang_y_upper: bpy.props.FloatProperty(
        name="Upper Y Angle Limit",
        description="Upper limit of Y axis rotation",
        default=0.0,
        min=MIN_ROT,
        max=MAX_ROT,
        precision=3,
        step=10,
        options=set(),
        subtype='ANGLE',
        unit='ROTATION',
        update=event_rigid_body_constraint,
    )

    limit_ang_z_upper: bpy.props.FloatProperty(
        name="Upper Z Angle Limit",
        description="Upper limit of Z axis rotation",
        default=0.0,
        min=MIN_ROT,
        max=MAX_ROT,
        precision=3,
        step=10,
        options=set(),
        subtype='ANGLE',
        unit='ROTATION',
        update=event_rigid_body_constraint,
    )


    @classmethod
    def register(cls):
        bpy.types.Bone.rigid_body_bones = bpy.props.PointerProperty(type=cls)

    @classmethod
    def unregister(cls):
        del bpy.types.Bone.rigid_body_bones
