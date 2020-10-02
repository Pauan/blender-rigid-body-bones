import bpy
from . import utils


class Panel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones"
    bl_label = "Armature"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 0

    @classmethod
    def poll(cls, context):
        return utils.is_armature(context)

    def draw(self, context):
        pass


class SettingsPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_settings"
    bl_label = "Bone Settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_parent_id = "DATA_PT_rigid_body_bones"
    bl_options = set()
    bl_order = 0

    def draw(self, context):
        data = context.active_object.data.rigid_body_bones
        layout = self.layout

        flow = layout.grid_flow(row_major=True, columns=1, even_columns=True, even_rows=False, align=True)

        flow = flow.row()
        flow.alignment = 'CENTER'

        flow = flow.column()

        col = flow.column()
        col.prop(data, "enabled")
        col.prop(data, "hide_active_bones")
        col.prop(data, "hide_hitboxes")

        if True:
            flow.separator()

            col = flow.column()
            col.operator("rigid_body_bones.factory_default")


class BonePanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_bone"
    bl_label = "Rigid Body"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_options = set()
    bl_order = 1

    @classmethod
    def poll(cls, context):
        return utils.has_active_bone(context) and utils.is_edit_mode(context)

    def draw_header(self, context):
        data = context.active_bone.rigid_body_bones

        self.layout.prop(data, "enabled", text = "")

    def draw(self, context):
        pass


class HitboxPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_hitbox"
    bl_label = "Hitbox"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_parent_id = "DATA_PT_rigid_body_bones_bone"
    bl_options = set()
    bl_order = 0

    def draw(self, context):
        data = context.active_bone.rigid_body_bones

        layout = self.layout
        layout.enabled = data.enabled
        layout.use_property_split = True

        flow = layout.grid_flow(row_major=True, columns=1, even_columns=True, even_rows=False, align=True)

        col = flow.column()
        col.prop(data, "type")
        flow.separator()

        col = flow.column()
        col.prop(data, "collision_shape", text="Shape")
        flow.separator()

        col = flow.column()
        col.prop(data, "location")
        flow.separator()

        col = flow.column()
        col.prop(data, "rotation")
        flow.separator()

        col = flow.column()
        col.prop(data, "scale")

        if data.type == 'ACTIVE':
            flow.separator()
            col = flow.column()
            col.prop(data, "mass")


class ConstraintPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_constraint"
    bl_label = "Constraint"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_parent_id = "DATA_PT_rigid_body_bones_bone"
    bl_options = set()
    bl_order = 1

    @classmethod
    def poll(cls, context):
        data = context.active_bone.rigid_body_bones
        return (data.type == 'ACTIVE')

    def draw_header(self, context):
        data = context.active_bone.rigid_body_bones
        self.layout.enabled = data.enabled
        self.layout.prop(data, "enable_constraint", text="")

    def draw(self, context):
        data = context.active_bone.rigid_body_bones
        layout = self.layout
        layout.enabled = data.enable_constraint


class AdvancedPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_advanced"
    bl_label = "Advanced"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_parent_id = "DATA_PT_rigid_body_bones_bone"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 2

    def draw(self, context):
        pass


class AdvancedPhysicsPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_advanced_physics"
    bl_label = "Physics"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_parent_id = "DATA_PT_rigid_body_bones_advanced"
    bl_options = set()
    bl_order = 0

    def draw(self, context):
        data = context.active_bone.rigid_body_bones
        self.layout.use_property_split = True
        self.layout.enabled = data.enabled

        flow = self.layout.grid_flow(row_major=True, columns=1, even_columns=True, even_rows=False, align=True)

        col = flow.column()
        col.prop(data, "use_margin")

        col = flow.column()
        col.enabled = data.use_margin
        col.prop(data, "collision_margin", text="Margin")

        flow.separator()

        col = flow.column()
        col.prop(data, "friction", slider=True)

        col = flow.column()
        col.prop(data, "restitution", text="Bounciness", slider=True)

        if data.type == 'ACTIVE':
            flow.separator()

            col = flow.column()
            col.prop(data, "linear_damping", text="Damping Translation", slider=True)

            col = flow.column()
            col.prop(data, "angular_damping", text="Rotation", slider=True)


class CollectionsPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_collections"
    bl_label = "Collections"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_parent_id = "DATA_PT_rigid_body_bones_advanced"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 1

    def draw(self, context):
        data = context.active_bone.rigid_body_bones
        self.layout.enabled = data.enabled
        self.layout.prop(data, "collision_collections", text="")


class DeactivationPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_deactivation"
    bl_label = "Deactivation"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_parent_id = "DATA_PT_rigid_body_bones_advanced"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 2

    @classmethod
    def poll(cls, context):
        data = context.active_bone.rigid_body_bones
        return (data.type == 'ACTIVE')

    def draw_header(self, context):
        data = context.active_bone.rigid_body_bones
        self.layout.enabled = data.enabled
        self.layout.prop(data, "use_deactivation", text="")

    def draw(self, context):
        data = context.active_bone.rigid_body_bones
        self.layout.enabled = data.enabled and data.use_deactivation
        self.layout.use_property_split = True

        flow = self.layout.grid_flow(row_major=True, columns=1, even_columns=True, even_rows=False, align=True)

        col = flow.column()
        col.prop(data, "use_start_deactivated")

        col = flow.column()
        col.prop(data, "deactivate_linear_velocity", text="Velocity Linear")
        col.prop(data, "deactivate_angular_velocity", text="Angular")
