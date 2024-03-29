# <pep8 compliant>

# ---- New features
# TODO support animating settings (https://developer.blender.org/T48975)
# TODO support convex hull and mesh shapes
# TODO support cone shape
# TODO FIXED and RAGDOLL types
# TODO MOTOR type
# TODO add in language translation support
# TODO add in Apply Transformation operator ?
# TODO Collision support for colliding with soft bodies and clothes ?
# TODO add in scale for compounds (but be careful of non-uniform scale skewing)
# TODO add in color coding / custom shapes for the bones (e.g. active, error, passive)
# TODO maybe allow for changing the settings even if the armature is disabled
# TODO only show the origin/joint for the selected/active bones
# TODO add in support for different armatures for constraints
# TODO add in automatic support for IK (without needing to manually setup constraints)
# TODO display the error symbol on the Rigid Body header if there is an error
# TODO if an error happens, disable all of the bones

# ---- Bugs
# TODO if dimensions are 0 (in any axis) then only create 0/2/4 vertices for the hitbox
# TODO investigate the todo in clear_mesh
# TODO if the user removes the RigidBodyWorld then a lot of stuff breaks
# TODO if a constraint is added to a different armature, and that other armature is changed, it doesn't mark the first armature as dirty
# TODO test whether it works properly when multiple armatures share the same bones

# ---- Breaking changes
# TODO rename constraint to joint ?
# TODO merge active and passive properties together into hitbox property
# TODO replace name with id, and parent with parent_id ?

# ---- Blender bugs
# TODO enabling/disabling bone (or changing type) and then undoing causes a hard crash
# TODO when setting a min/max limit to 180 or -180 it disables the limit
# TODO min/max rotate limits are flipped in Blender's UI
# TODO when using IK with non-uniform bone scale (shearing) the matrix of the joints is wrong
# TODO rigid bodies don't work correctly with non-uniform scale (shearing)
# TODO even if a Child Of constraint is placed at the bottom of the stack, it does not override the previous constraints
# TODO even if a Child Of constraint exists, it can still be overridden by manual keyframes
# TODO pose bone matrix is wrong when enabling rigid body physics in Object mode
# TODO missing show_expanded for collections
# TODO skewed bones break the matrix calculations (see Test.blend)
# TODO there is a difference between using matrix_parent_inverse and manually calculating the parent's inverse
bl_info = {
    "name": "Rigid Body Bones",
    "author": "Pauan",
    "version": (1, 6, 2),
    # Minimum version because of https://developer.blender.org/T81345
    "blender": (2, 91, 0),
    "location": "View3D > Sidebar > Rigid Body Bones",
    "description": "Adds rigid body / spring physics to bones",
    "warning": "",
    "doc_url": "",
    "category": "Physics",
    "wiki_url": "https://github.com/Pauan/blender-rigid-body-bones#readme",
    "tracker_url": "https://github.com/Pauan/blender-rigid-body-bones/issues",
}

import bpy

if bpy.app.version < (2, 91, 0):
    raise Exception("Rigid Body Bones requires Blender 2.91.0 or higher")

from . import armatures
from . import events
from . import panels
from . import properties
from . import utils

classes = (
    properties.Dirty,
    properties.Scene,
    properties.Error,
    properties.Armature,
    properties.Compound,
    properties.Constraint,
    properties.Bone,

    armatures.Update,
    armatures.CleanupArmatures,
    armatures.CopyFromActive,
    armatures.CalculateMass,
    armatures.BakeToKeyframes,
    armatures.NewCompound,
    armatures.RemoveCompound,
    armatures.MoveCompound,
    armatures.NewConstraint,
    armatures.RemoveConstraint,
    armatures.MoveConstraint,

    panels.RigidBodyMenu,
    panels.ArmaturePanel,
    panels.ArmatureSettingsPanel,
    panels.BonePanel,
    panels.SettingsPanel,
    panels.CompoundList,
    panels.HitboxesPanel,
    panels.HitboxesOffsetPanel,
    panels.HitboxesAdvancedPanel,
    panels.LimitsPanel,
    panels.LimitsRotatePanel,
    panels.LimitsTranslatePanel,
    panels.SpringsPanel,
    panels.SpringsRotatePanel,
    panels.SpringsTranslatePanel,
    panels.OffsetPanel,
    panels.AdvancedPanel,
    panels.AdvancedPhysicsPanel,
    panels.CollectionsPanel,
    panels.DeactivationPanel,
    panels.OverrideIterationsPanel,
    panels.ConstraintList,
    panels.ConstraintsPanel,
    panels.ConstraintLimitsPanel,
    panels.ConstraintLimitsRotatePanel,
    panels.ConstraintLimitsTranslatePanel,
    panels.ConstraintSpringsPanel,
    panels.ConstraintSpringsRotatePanel,
    panels.ConstraintSpringsTranslatePanel,
    panels.ConstraintOffsetPanel,
    panels.ConstraintAdvancedPanel,
    panels.ConstraintAdvancedPhysicsPanel,
    panels.ConstraintOverrideIterationsPanel,
)

def register():
    utils.debug("REGISTERING")

    if utils.DEBUG:
        import faulthandler
        faulthandler.enable()

    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    events.register()

def unregister():
    utils.debug("UNREGISTERING")

    events.unregister()

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
