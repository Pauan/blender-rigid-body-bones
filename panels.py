import bpy
from . import utils
from .bones import is_bone_active


class ArmaturePanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_armature"
    bl_label = "Armature"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 0

    @classmethod
    def poll(cls, context):
        return utils.is_armature(context)

    def draw_header(self, context):
        data = context.active_object.data.rigid_body_bones
        layout = self.layout

        if len(data.errors) != 0:
            layout.label(text="", icon='ERROR')

    def draw(self, context):
        data = context.active_object.data.rigid_body_bones
        layout = self.layout

        if len(data.errors) != 0:
            layout.label(text="Invalid bones:")

            box = layout.box()

            for error in data.errors:
                box.label(text=error.name, icon='BONE_DATA')


class ArmatureSettingsPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_armature_settings"
    bl_label = "Bone Settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_parent_id = "DATA_PT_rigid_body_bones_armature"
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
        col.prop(data, "hide_constraints")
        col.prop(data, "hide_active_bones")
        col.prop(data, "hide_hitboxes")


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
        return utils.has_active_bone(context) and utils.is_pose_mode(context)

    def draw_header(self, context):
        data = utils.get_active_bone(context.active_object).rigid_body_bones
        layout = self.layout

        layout.enabled = utils.is_armature_enabled(context)

        layout.prop(data, "enabled", text = "")

    def draw(self, context):
        data = utils.get_active_bone(context.active_object).rigid_body_bones
        layout = self.layout

        if data.error == 'ACTIVE_PARENT':
            layout.label(text="Passive bone cannot have an Active parent", icon='ERROR')


class SettingsPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_bone_settings"
    bl_label = "Settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_parent_id = "DATA_PT_rigid_body_bones_bone"
    bl_options = set()
    bl_order = 0

    def draw(self, context):
        data = utils.get_active_bone(context.active_object).rigid_body_bones
        layout = self.layout

        layout.enabled = data.enabled and utils.is_armature_enabled(context)
        layout.use_property_split = True

        flow = layout.grid_flow(row_major=True, columns=1, even_columns=True, even_rows=False, align=True)

        col = flow.column()
        col.prop(data, "type")

        flow.separator()

        col = flow.column()
        col.prop(data, "collision_shape", text="Shape")

        if is_bone_active(data):
            flow.separator()

            col = flow.column()
            col.prop(data, "mass")

            flow.separator()

            col = flow.column()
            col.prop(data, "disable_collisions")


class LimitsPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_bone_limits"
    bl_label = "Limits"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_parent_id = "DATA_PT_rigid_body_bones_bone"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 1

    @classmethod
    def poll(cls, context):
        data = utils.get_active_bone(context.active_object).rigid_body_bones
        return is_bone_active(data)

    def draw(self, context):
        pass


class SpringsPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_bone_springs"
    bl_label = "Springs"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_parent_id = "DATA_PT_rigid_body_bones_bone"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 2

    @classmethod
    def poll(cls, context):
        data = utils.get_active_bone(context.active_object).rigid_body_bones
        return is_bone_active(data)

    def draw(self, context):
        pass


class SpringsRotatePanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_bone_springs_rotate"
    bl_label = "Rotate"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_parent_id = "DATA_PT_rigid_body_bones_bone_springs"
    bl_options = set()
    bl_order = 0

    def draw(self, context):
        data = utils.get_active_bone(context.active_object).rigid_body_bones
        layout = self.layout

        layout.enabled = data.enabled and utils.is_armature_enabled(context)
        layout.use_property_split = True

        flow = layout.grid_flow(row_major=True, columns=1, even_columns=True, even_rows=False, align=True)

        col = flow.column()
        col.prop(data, "use_spring_ang_x")

        sub = col.column(align=True)
        sub.enabled = data.use_spring_ang_x
        sub.prop(data, "spring_stiffness_ang_x", text="X Stiffness")
        sub.prop(data, "spring_damping_ang_x", text="Damping")

        col = flow.column()
        col.prop(data, "use_spring_ang_y")

        sub = col.column(align=True)
        sub.enabled = data.use_spring_ang_y
        sub.prop(data, "spring_stiffness_ang_y", text="Y Stiffness")
        sub.prop(data, "spring_damping_ang_y", text="Damping")

        col = flow.column()
        col.prop(data, "use_spring_ang_z")

        sub = col.column(align=True)
        sub.enabled = data.use_spring_ang_z
        sub.prop(data, "spring_stiffness_ang_z", text="Z Stiffness")
        sub.prop(data, "spring_damping_ang_z", text="Damping")


class SpringsTranslatePanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_bone_springs_translate"
    bl_label = "Translate"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_parent_id = "DATA_PT_rigid_body_bones_bone_springs"
    bl_options = set()
    bl_order = 1

    def draw(self, context):
        data = utils.get_active_bone(context.active_object).rigid_body_bones
        layout = self.layout

        layout.enabled = data.enabled and utils.is_armature_enabled(context)
        layout.use_property_split = True

        flow = layout.grid_flow(row_major=True, columns=1, even_columns=True, even_rows=False, align=True)

        col = flow.column()
        col.prop(data, "use_spring_x")

        sub = col.column(align=True)
        sub.enabled = data.use_spring_x
        sub.prop(data, "spring_stiffness_x", text="X Stiffness")
        sub.prop(data, "spring_damping_x", text="Damping")

        col = flow.column()
        col.prop(data, "use_spring_y")

        sub = col.column(align=True)
        sub.enabled = data.use_spring_y
        sub.prop(data, "spring_stiffness_y", text="Y Stiffness")
        sub.prop(data, "spring_damping_y", text="Damping")

        col = flow.column()
        col.prop(data, "use_spring_z")

        sub = col.column(align=True)
        sub.enabled = data.use_spring_z
        sub.prop(data, "spring_stiffness_z", text="Z Stiffness")
        sub.prop(data, "spring_damping_z", text="Damping")


class OffsetPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_bone_offset"
    bl_label = "Offset"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_parent_id = "DATA_PT_rigid_body_bones_bone"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 3

    def draw(self, context):
        data = utils.get_active_bone(context.active_object).rigid_body_bones
        layout = self.layout

        layout.enabled = data.enabled and utils.is_armature_enabled(context)
        layout.use_property_split = True

        flow = layout.grid_flow(row_major=True, columns=1, even_columns=True, even_rows=False, align=True)

        col = flow.column()
        col.prop(data, "origin", slider=True, text="Origin")

        flow.separator()

        col = flow.column()
        col.prop(data, "location")

        flow.separator()

        col = flow.column()
        col.prop(data, "rotation")

        flow.separator()

        col = flow.column()
        col.prop(data, "scale")


class AdvancedPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_bone_advanced"
    bl_label = "Advanced"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_parent_id = "DATA_PT_rigid_body_bones_bone"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 4

    def draw(self, context):
        pass


class AdvancedPhysicsPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_advanced_physics"
    bl_label = "Physics"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_parent_id = "DATA_PT_rigid_body_bones_bone_advanced"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 0

    def draw(self, context):
        data = utils.get_active_bone(context.active_object).rigid_body_bones
        layout = self.layout

        layout.use_property_split = True
        layout.enabled = data.enabled and utils.is_armature_enabled(context)

        flow = layout.grid_flow(row_major=True, columns=1, even_columns=True, even_rows=False, align=True)

        if is_bone_active(data):
            col = flow.column()
            col.prop(data, "use_breaking")

            sub = col.column()
            sub.enabled = data.use_breaking
            sub.prop(data, "breaking_threshold", text="Threshold")

            flow.separator()

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

        if is_bone_active(data):
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
    bl_parent_id = "DATA_PT_rigid_body_bones_bone_advanced"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 1

    def draw(self, context):
        data = utils.get_active_bone(context.active_object).rigid_body_bones
        layout = self.layout

        layout.enabled = data.enabled and utils.is_armature_enabled(context)
        layout.prop(data, "collision_collections", text="")


class DeactivationPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_deactivation"
    bl_label = "Deactivation"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_parent_id = "DATA_PT_rigid_body_bones_bone_advanced"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 2

    @classmethod
    def poll(cls, context):
        data = utils.get_active_bone(context.active_object).rigid_body_bones
        return is_bone_active(data)

    def draw_header(self, context):
        data = utils.get_active_bone(context.active_object).rigid_body_bones
        layout = self.layout

        layout.enabled = data.enabled and utils.is_armature_enabled(context)

        layout.prop(data, "use_deactivation", text="")

    def draw(self, context):
        data = utils.get_active_bone(context.active_object).rigid_body_bones
        layout = self.layout

        layout.enabled = data.enabled and utils.is_armature_enabled(context) and data.use_deactivation
        layout.use_property_split = True

        flow = layout.grid_flow(row_major=True, columns=1, even_columns=True, even_rows=False, align=True)

        col = flow.column()
        col.prop(data, "use_start_deactivated")

        col = flow.column()
        col.prop(data, "deactivate_linear_velocity", text="Velocity Linear")
        col.prop(data, "deactivate_angular_velocity", text="Angular")


class OverrideIterationsPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_override_iterations"
    bl_label = "Override Iterations"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_parent_id = "DATA_PT_rigid_body_bones_bone_advanced"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 3

    @classmethod
    def poll(cls, context):
        data = utils.get_active_bone(context.active_object).rigid_body_bones
        return is_bone_active(data)

    def draw_header(self, context):
        data = utils.get_active_bone(context.active_object).rigid_body_bones
        layout = self.layout

        layout.enabled = data.enabled and utils.is_armature_enabled(context)

        layout.prop(data, "use_override_solver_iterations", text="")

    def draw(self, context):
        data = utils.get_active_bone(context.active_object).rigid_body_bones
        layout = self.layout

        layout.enabled = data.enabled and utils.is_armature_enabled(context)and data.use_override_solver_iterations
        layout.use_property_split = True

        layout.prop(data, "solver_iterations", text="Iterations")
