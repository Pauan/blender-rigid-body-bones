bl_info = {
    "name": "Rigid Body Bones",
    "author": "Pauan",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "Properties > Rigid Body",
    "description": "Adds rigid body physics to bones",
    "warning": "",
    "doc_url": "",
    "category": "Physics",
}


import bpy
from bpy.types import Operator, Menu
from bpy_extras.object_utils import object_data_add


def make_collection(name, parent):
    collection = bpy.data.collections.new(name)
    collection.hide_select = True
    collection.hide_render = True
    parent.children.link(collection)
    return collection

def remove_collection(collection):
    for child in collection.objects:
        bpy.data.objects.remove(child)

    bpy.data.collections.remove(collection)


def root_collection(context):
    scene = context.scene

    root = scene.rigid_body_bones.collection

    if not root:
        root = make_collection("RigidBodyBones", scene.collection)
        scene.rigid_body_bones.collection = root

    return root



def make_armature_collection(context, armature):
    data = armature.rigid_body_bones

    if not data.collection:
        root = root_collection(context)
        # TODO is context.object correct ?
        data.collection = make_collection(context.object.name + " [Root]", root)

    if not data.constraints:
        # TODO is context.object correct ?
        data.constraints = make_collection(context.object.name + " [Constraints]", data.collection)


def remove_armature_collection(context, armature):
    data = armature.rigid_body_bones

    if data.constraints:
        remove_collection(data.constraints)
        data.constraints = None

    if data.collection:
        remove_collection(data.collection)
        data.collection = None

    root = context.scene.rigid_body_bones.collection

    if root and len(root.children) == 0 and len(root.objects) == 0:
        remove_collection(root)
        context.scene.rigid_body_bones.collection = None


def fix_armature_bones(armature):
    pass


def update_armature(self, context):
    print("UPDATING")

    armature = context.armature

    if armature:
        if armature.rigid_body_bones.enabled:
            make_armature_collection(context, armature)

        else:
            remove_armature_collection(context, armature)
            fix_armature_bones(armature)


def update_bone(self, context):
    print("BONE")
    if self.enabled:
        print("ENABLED")



class VIEW3D_PT_rigid_body_bones_armature(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'
    bl_label = "Rigid Body"

    @classmethod
    def poll(cls, context):
        return (context.armature is not None)

    def draw_header(self, context):
        self.layout.enabled = (context.mode == 'EDIT_ARMATURE')

        self.layout.prop(context.armature.rigid_body_bones, "enabled", text = "")

    def draw(self, context):
        pass



class VIEW3D_PT_rigid_body_bones_bone(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'bone'
    bl_label = "Rigid Body"

    @classmethod
    def poll(cls, context):
        return (
            (context.armature is not None) and
            (context.armature.rigid_body_bones.enabled) and
            (context.edit_bone is not None)
        )

    def draw_header(self, context):
        self.layout.enabled = (context.mode == 'EDIT_ARMATURE')

        self.layout.prop(context.edit_bone.rigid_body_bones, "enabled", text = "")

    def draw(self, context):
        pass



class SceneProperties(bpy.types.PropertyGroup):
    collection: bpy.props.PointerProperty(type = bpy.types.Collection)

    @classmethod
    def register(cls):
        bpy.types.Scene.rigid_body_bones = bpy.props.PointerProperty(type=cls)

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.rigid_body_bones


class ArmatureProperties(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(name = "Rigid Body", description = "Enable rigid body physics for armature", update = update_armature)
    collection: bpy.props.PointerProperty(type = bpy.types.Collection)
    constraints: bpy.props.PointerProperty(type = bpy.types.Collection)

    @classmethod
    def register(cls):
        bpy.types.Armature.rigid_body_bones = bpy.props.PointerProperty(type=cls)

    @classmethod
    def unregister(cls):
        del bpy.types.Armature.rigid_body_bones


class EditBoneProperties(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(name = "Rigid Body", description = "Create rigid body physics for bone", update = update_bone)

    @classmethod
    def register(cls):
        bpy.types.EditBone.rigid_body_bones = bpy.props.PointerProperty(type=cls)

    @classmethod
    def unregister(cls):
        del bpy.types.EditBone.rigid_body_bones



# This allows you to right click on a button and link to documentation
def add_object_manual_map():
    url_manual_prefix = "https://docs.blender.org/manual/en/latest/"
    url_manual_mapping = (
        ("bpy.ops.pose.create_rigid_bodies", "scene_layout/object/types.html"),
    )
    return url_manual_prefix, url_manual_mapping


classes = (
    SceneProperties,
    ArmatureProperties,
    EditBoneProperties,
    VIEW3D_PT_rigid_body_bones_armature,
    VIEW3D_PT_rigid_body_bones_bone,
)

def register():
    print("REGISTERING")
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    #bpy.utils.register_manual_map(add_object_manual_map)
    #bpy.types.VIEW3D_MT_pose.append(add_menu)

def unregister():
    #bpy.types.VIEW3D_MT_pose.remove(add_menu)
    #bpy.utils.unregister_manual_map(add_object_manual_map)

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == "__main__":
    register()
