# <pep8 compliant>

# TODO support animating settings (https://developer.blender.org/T48975)
# TODO support convex hull and mesh shapes
# TODO support cone shape
# TODO FIXED and RAGDOLL types
# TODO different scale settings for different collision shapes

# TODO enabling/disabling bone (or changing type) and then undoing causes a hard crash
# TODO when setting a min/max limit to 180 or -180 it disables the limit
# TODO min/max rotate limits are flipped in Blender's UI

# TODO compound shape
# TODO investigate if compound shape can be used to implement convex hull and mesh shapes
# TODO add in Calculate Mass operator
# TODO add in Bake to Keyframes operator
# TODO add in Apply Transformation operator ?
bl_info = {
    "name": "Rigid Body Bones",
    "author": "Pauan",
    "version": (1, 1),
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
    properties.Bone,

    armatures.Update,
    armatures.CleanupArmatures,
    armatures.CopyFromActive,

    panels.RigidBodyMenu,
    panels.ArmaturePanel,
    panels.ArmatureSettingsPanel,
    panels.BonePanel,
    panels.SettingsPanel,
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
