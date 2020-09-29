import bpy
from math import radians
from mathutils import Vector, Euler
from . import utils


def make_collection(context):
    scene = context.scene

    root = scene.rigid_body_bones.collection

    if not root:
        root = utils.make_collection("RigidBodyBones", scene.collection)
        root.hide_select = True
        root.hide_render = True
        scene.rigid_body_bones.collection = root

    return root

def make_constraints(context, object, data):
    if not data.constraints:
        data.constraints = utils.make_collection(object.name + " [Constraints]", data.hitboxes)
        data.constraints.hide_render = True
        data.constraints.hide_viewport = True

def make_hitboxes(context, object, data):
    if not data.hitboxes:
        root = make_collection(context)
        data.hitboxes = utils.make_collection(object.name + " [Hitboxes]", root)
        data.hitboxes.hide_render = True


def make_root_body(context, object, data):
    if not data.root_body:
        with utils.Mode(context, 'OBJECT'), utils.Selectable(context.scene, data), utils.Selected(context):
        #with Selected(context):
            #bpy.context.space_data.context = 'PHYSICS'

            #bpy.ops.mesh.primitive_cube_add(size=1.0, calc_uvs=False, enter_editmode=False)
            #root_body = context.active_object
            #root_body.name = object.name + " [Root]"

            #bpy.ops.screen.space_type_set_or_cycle(space_type='PROPERTIES')

            #with Tab(context, 'PHYSICS'):
                #log(local["area"].type)

            #bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

            root_body = utils.make_empty_rigid_body(
                context,
                name=object.name + " [Root]",
                collection=data.hitboxes,
                location=object.location,
            )

            utils.parent(context, root_body, object)

            with utils.Mode(context, 'EDIT'):
                for bone in object.data.edit_bones:
                    utils.log(bone.name)
                    rotation = bone.matrix.to_euler()
                    rotation.rotate_axis('X', radians(90.0))

                    other = utils.make_hitbox(
                        context,
                        name=bone.name + " [Hitbox]",
                        collection=data.hitboxes,
                        # TODO does this need 2 vectors ?
                        # TODO better way to normalize this ?
                        location=Vector(bone.center) + Vector(object.location),
                        rotation=rotation,
                        dimensions=(bone.length * 0.2, bone.length * 0.2, bone.length),
                        active=False,
                    )

            data.root_body = root_body


def fix_bones(object):
    pass


def remove_collection(context, object, data):
    fix_bones(object)

    if data.constraints:
        utils.remove_collection(data.constraints)
        data.constraints = None

    if data.hitboxes:
        utils.remove_collection(data.hitboxes)
        data.hitboxes = None

    data.root_body = None

    root = context.scene.rigid_body_bones.collection

    if root and len(root.children) == 0 and len(root.objects) == 0:
        utils.remove_collection(root)
        context.scene.rigid_body_bones.collection = None


def update(self, context):
    print("UPDATING")

    # TODO is context.active_object correct ?
    object = context.active_object
    armature = object.data

    if armature.rigid_body_bones.enabled:
        data = armature.rigid_body_bones

        make_hitboxes(context, object, data)
        make_constraints(context, object, data)
        make_root_body(context, object, data)

    else:
        remove_collection(context, object, armature.rigid_body_bones)


class ResetDimensionsXOperator(bpy.types.Operator):
    bl_idname = "rigid_body_bones.reset_dimensions_x"
    bl_label = "Reset X dimension"
    bl_description = "Reset the X dimension to the width of the bone"
    bl_options = {'UNDO'}

    def execute(self, context):
        print("Hello World")
        return {'FINISHED'}

    def draw(self, context):
        pass


class ResetDimensionsYOperator(bpy.types.Operator):
    bl_idname = "rigid_body_bones.reset_dimensions_y"
    bl_label = "Reset Y dimension"
    bl_description = "Reset the Y dimension to the height of the bone"
    bl_options = {'UNDO'}

    def execute(self, context):
        print("Hello World")
        return {'FINISHED'}

    def draw(self, context):
        pass


class ResetDimensionsZOperator(bpy.types.Operator):
    bl_idname = "rigid_body_bones.reset_dimensions_z"
    bl_label = "Reset Z dimension"
    bl_description = "Reset the Z dimension to the length of the bone"
    bl_options = {'UNDO'}

    def execute(self, context):
        print("Hello World")
        return {'FINISHED'}

    def draw(self, context):
        pass


class Panel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones"
    bl_label = "Rigid Body Bones"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_options = set()

    @classmethod
    def poll(cls, context):
        return (
            #(context.active_object is not None) and
            #(context.active_object.type == 'ARMATURE') and
            (context.active_bone is not None) and
            (
                (context.mode == 'OBJECT') or
                (context.mode == 'EDIT_ARMATURE')
            )
        )

    def draw_header(self, context):
        pass
        #data = context.active_object.data.rigid_body_bones

        #self.layout.enabled = (context.mode == 'EDIT_ARMATURE')

        #self.layout.prop(data, "enabled", text = "")

    def draw(self, context):
        layout = self.layout

        if context.mode == 'OBJECT':
            data = context.active_object.data.rigid_body_bones

            layout.prop(data, "enabled")

        else:
            data = context.active_bone.rigid_body_bones

            layout.enabled = (context.mode == 'EDIT_ARMATURE')

            layout.prop(data, "enabled")

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)
            flow.use_property_split = True
            flow.enabled = data.enabled

            col = flow.column()
            col.prop(data, "type")
            col.separator()

            col = flow.column()
            col.prop(data, "shape")
            col.separator()

            col = flow.column(align=True)

            row = col.row(align=True)
            row.prop(data, "width")
            row.operator("rigid_body_bones.reset_dimensions_x", text="", icon='X')

            row = col.row(align=True)
            row.prop(data, "height")
            row.operator("rigid_body_bones.reset_dimensions_y", text="", icon='X')

            row = col.row(align=True)
            row.prop(data, "length")
            row.operator("rigid_body_bones.reset_dimensions_z", text="", icon='X')

            if data.type == 'ACTIVE':
                col = flow.column()
                col.separator()
                col.prop(data, "mass")


class RigidBodyPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_bone"
    bl_label = "Rigid Body"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_parent_id = "DATA_PT_rigid_body_bones"
    #bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        return (context.mode == 'EDIT_ARMATURE')

    def draw_header(self, context):
        pass

    def draw(self, context):
        pass


class ConstraintPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_constraint"
    bl_label = "Constraint"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_parent_id = "DATA_PT_rigid_body_bones"
    bl_options = set()

    @classmethod
    def poll(cls, context):
        data = context.active_bone.rigid_body_bones
        return (data.type == 'ACTIVE')

    def draw_header(self, context):
        self.layout.prop(context.active_bone.rigid_body_bones, "enable_constraint", text="")

    def draw(self, context):
        data = context.active_bone.rigid_body_bones

        self.layout.enabled = data.enable_constraint
        pass
