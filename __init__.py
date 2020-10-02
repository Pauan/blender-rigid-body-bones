# TODO support undo/redo
# TODO support animating settings
# TODO support alt click to change all selected objects
bl_info = {
    "name": "Rigid Body Bones",
    "author": "Pauan",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Rigid Body Bones",
    "description": "Adds rigid body physics to bones",
    "warning": "",
    "doc_url": "",
    "category": "Physics",
}

import faulthandler

from . import armatures
from . import bones
from . import events
from . import panels
from . import properties
from . import utils

from importlib import reload
reload(utils)
reload(properties)
reload(armatures)
reload(bones)
reload(events)
reload(panels)

# This allows you to right click on a button and link to documentation
def add_object_manual_map():
    url_manual_prefix = "https://docs.blender.org/manual/en/latest/"
    url_manual_mapping = (
        ("bpy.ops.pose.create_rigid_bodies", "scene_layout/object/types.html"),
    )
    return url_manual_prefix, url_manual_mapping

classes = (
    properties.Scene,
    properties.Armature,
    properties.EditBone,
    panels.Panel,
    panels.SettingsPanel,
    panels.BonePanel,
    panels.HitboxPanel,
    panels.ConstraintPanel,
    panels.AdvancedPanel,
    panels.AdvancedPhysicsPanel,
    panels.CollectionsPanel,
    panels.DeactivationPanel,
)

def register():
    print("REGISTERING")
    faulthandler.enable()
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    events.register()

    #bpy.utils.register_manual_map(add_object_manual_map)

def unregister():
    print("UNREGISTERING")
    #bpy.utils.unregister_manual_map(add_object_manual_map)

    events.unregister()

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == "__main__":
    register()
