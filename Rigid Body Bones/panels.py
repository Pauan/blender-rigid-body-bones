import bpy
from . import utils
from .bones import is_bone_active, shape_icon


def enabled_icon(enabled):
    if enabled:
        return 'IPO_ELASTIC'
    else:
        # Horizontal line
        return 'REMOVE'


def rigid_body_menu(self, context):
    self.layout.menu("VIEW3D_MT_pose_rigid_body")

class RigidBodyMenu(bpy.types.Menu):
    bl_idname = "VIEW3D_MT_pose_rigid_body"
    bl_label = "Rigid Body"

    @classmethod
    def register(cls):
        bpy.types.VIEW3D_MT_pose.append(rigid_body_menu)

    @classmethod
    def unregister(cls):
        bpy.types.VIEW3D_MT_pose.remove(rigid_body_menu)

    @classmethod
    def poll(cls, context):
        return utils.is_pose_mode(context) and utils.is_armature(context) and utils.has_active_bone(context)

    def draw(self, context):
        self.layout.operator("rigid_body_bones.calculate_mass")
        self.layout.operator("rigid_body_bones.copy_from_active")


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
        return utils.is_armature(context) and not utils.is_edit_mode(context)

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

        flow.separator()

        col = flow.column()
        col.prop(data, "hide_active_bones")

        flow.separator()

        col = flow.column()
        col.prop(data, "hide_hitboxes")
        col.prop(data, "hide_hitbox_origins")


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
            layout.label(text="Children of Active must be Active", icon='ERROR')


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


class CompoundList(bpy.types.UIList):
    bl_idname = "DATA_UL_rigid_body_bones_bone_compound"

    def draw_item(self, _context, layout, _data, item, icon, _active_data_, _active_propname, _index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon=shape_icon(item.collision_shape))

        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon=shape_icon(item.collision_shape))


class HitboxesPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_bone_hitboxes"
    bl_label = "Hitboxes"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_parent_id = "DATA_PT_rigid_body_bones_bone"
    bl_options = set()
    bl_order = 1

    @classmethod
    def poll(cls, context):
        data = utils.get_active_bone(context.active_object).rigid_body_bones
        return data.collision_shape == 'COMPOUND'

    def draw(self, context):
        data = utils.get_active_bone(context.active_object).rigid_body_bones
        layout = self.layout

        layout.enabled = data.enabled and utils.is_armature_enabled(context)

        row = layout.row()

        length = len(data.compounds)
        has_items = length > 0

        if has_items:
            rows = 4
        else:
            rows = 2

        row.template_list(
            "DATA_UL_rigid_body_bones_bone_compound",
            "",
            data,
            "compounds",
            data,
            "active_compound_index",
            rows=rows,
            maxrows=4,
            item_dyntip_propname="name",
        )

        col = row.column(align=True)
        col.operator("rigid_body_bones.new_compound", icon='ADD', text="")

        sub = col.column(align=True)
        sub.enabled = has_items
        sub.operator("rigid_body_bones.remove_compound", icon='REMOVE', text="")

        if has_items:
            index = data.active_compound_index

            col.separator()

            sub = col.column(align=True)
            sub.enabled = (index != 0)
            sub.operator("rigid_body_bones.move_compound", icon='TRIA_UP', text="").direction = 'UP'

            sub = col.column(align=True)
            sub.enabled = (index < length - 1)
            sub.operator("rigid_body_bones.move_compound", icon='TRIA_DOWN', text="").direction = 'DOWN'

            compound = data.compounds[index]

            layout.separator()

            flow = layout.grid_flow(row_major=True, columns=1, even_columns=True, even_rows=False, align=True)
            flow.use_property_split = True

            col = flow.column()
            col.prop(compound, "collision_shape", text="Shape")


class HitboxesOffsetPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_bone_hitboxes_offset"
    bl_label = "Offset"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_parent_id = "DATA_PT_rigid_body_bones_bone_hitboxes"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 0

    @classmethod
    def poll(cls, context):
        data = utils.get_active_bone(context.active_object).rigid_body_bones
        return len(data.compounds) > 0

    def draw(self, context):
        data = utils.get_active_bone(context.active_object).rigid_body_bones
        compound = data.compounds[data.active_compound_index]
        layout = self.layout

        layout.enabled = data.enabled and utils.is_armature_enabled(context)
        layout.use_property_split = True

        flow = layout.grid_flow(row_major=True, columns=1, even_columns=True, even_rows=False, align=True)

        flow.separator()

        col = flow.column()
        col.prop(compound, "origin", slider=True, text="Origin")

        flow.separator()

        col = flow.column()
        col.prop(compound, "location")

        flow.separator()

        col = flow.column()
        col.prop(compound, "rotation")

        flow.separator()

        col = flow.column()
        col.prop(compound, "scale")

        flow.separator()


class HitboxesAdvancedPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_hitboxes_advanced"
    bl_label = "Advanced"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_parent_id = "DATA_PT_rigid_body_bones_bone_hitboxes"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 1

    @classmethod
    def poll(cls, context):
        data = utils.get_active_bone(context.active_object).rigid_body_bones
        return len(data.compounds) > 0

    def draw(self, context):
        data = utils.get_active_bone(context.active_object).rigid_body_bones
        compound = data.compounds[data.active_compound_index]
        layout = self.layout

        layout.use_property_split = True
        layout.enabled = data.enabled and utils.is_armature_enabled(context)

        flow = layout.grid_flow(row_major=True, columns=1, even_columns=True, even_rows=False, align=True)

        col = flow.column()
        col.prop(compound, "use_margin")

        col = flow.column()
        col.enabled = compound.use_margin
        col.prop(compound, "collision_margin", text="Margin")

        flow.separator()


class LimitsPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_bone_limits"
    bl_label = "Limits"
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


class LimitsRotatePanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_bone_limits_rotate"
    bl_label = "Rotate"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_parent_id = "DATA_PT_rigid_body_bones_bone_limits"
    bl_options = set()
    bl_order = 0

    def draw(self, context):
        data = utils.get_active_bone(context.active_object).rigid_body_bones
        layout = self.layout

        layout.enabled = data.enabled and utils.is_armature_enabled(context)
        layout.use_property_split = True

        flow = layout.grid_flow(row_major=True, columns=1, even_columns=True, even_rows=False, align=True)

        col = flow.column()
        col.prop(data, "use_limit_ang_x", text="Limit X")

        sub = col.column(align=True)
        sub.enabled = data.use_limit_ang_x
        sub.prop(data, "limit_ang_x_lower", text="Min")
        sub.prop(data, "limit_ang_x_upper", text="Max")

        flow.separator()

        col = flow.column()
        col.prop(data, "use_limit_ang_y", text="Limit Y")

        sub = col.column(align=True)
        sub.enabled = data.use_limit_ang_y
        sub.prop(data, "limit_ang_y_lower", text="Min")
        sub.prop(data, "limit_ang_y_upper", text="Max")

        flow.separator()

        col = flow.column()
        col.prop(data, "use_limit_ang_z", text="Limit Z")

        sub = col.column(align=True)
        sub.enabled = data.use_limit_ang_z
        sub.prop(data, "limit_ang_z_lower", text="Min")
        sub.prop(data, "limit_ang_z_upper", text="Max")

        flow.separator()


class LimitsTranslatePanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_bone_limits_translate"
    bl_label = "Translate"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_parent_id = "DATA_PT_rigid_body_bones_bone_limits"
    bl_options = set()
    bl_order = 1

    def draw(self, context):
        data = utils.get_active_bone(context.active_object).rigid_body_bones
        layout = self.layout

        layout.enabled = data.enabled and utils.is_armature_enabled(context)
        layout.use_property_split = True

        flow = layout.grid_flow(row_major=True, columns=1, even_columns=True, even_rows=False, align=True)

        col = flow.column()
        col.prop(data, "use_limit_lin_x", text="Limit X")

        sub = col.column(align=True)
        sub.enabled = data.use_limit_lin_x
        sub.prop(data, "limit_lin_x_lower", text="Min")
        sub.prop(data, "limit_lin_x_upper", text="Max")

        flow.separator()

        col = flow.column()
        col.prop(data, "use_limit_lin_y", text="Limit Y")

        sub = col.column(align=True)
        sub.enabled = data.use_limit_lin_y
        sub.prop(data, "limit_lin_y_lower", text="Min")
        sub.prop(data, "limit_lin_y_upper", text="Max")

        flow.separator()

        col = flow.column()
        col.prop(data, "use_limit_lin_z", text="Limit Z")

        sub = col.column(align=True)
        sub.enabled = data.use_limit_lin_z
        sub.prop(data, "limit_lin_z_lower", text="Min")
        sub.prop(data, "limit_lin_z_upper", text="Max")

        flow.separator()


class SpringsPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_bone_springs"
    bl_label = "Springs"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_parent_id = "DATA_PT_rigid_body_bones_bone"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 3

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

        col = flow.column(align=True)
        col.prop(data, "use_spring_ang_x", text="Enable X", icon=enabled_icon(data.use_spring_ang_x))
        col.prop(data, "use_spring_ang_y", text="Y", icon=enabled_icon(data.use_spring_ang_y))
        col.prop(data, "use_spring_ang_z", text="Z", icon=enabled_icon(data.use_spring_ang_z))

        flow.separator()

        col = flow.column(align=True)

        sub = col.column()
        sub.enabled = data.use_spring_ang_x
        sub.prop(data, "spring_stiffness_ang_x", text="Stiffness X")

        sub = col.column()
        sub.enabled = data.use_spring_ang_y
        sub.prop(data, "spring_stiffness_ang_y", text="Y")

        sub = col.column()
        sub.enabled = data.use_spring_ang_z
        sub.prop(data, "spring_stiffness_ang_z", text="Z")

        flow.separator()

        col = flow.column(align=True)

        sub = col.column()
        sub.enabled = data.use_spring_ang_x
        sub.prop(data, "spring_damping_ang_x", text="Damping X")

        sub = col.column()
        sub.enabled = data.use_spring_ang_y
        sub.prop(data, "spring_damping_ang_y", text="Y")

        sub = col.column()
        sub.enabled = data.use_spring_ang_z
        sub.prop(data, "spring_damping_ang_z", text="Z")

        flow.separator()


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

        col = flow.column(align=True)
        col.prop(data, "use_spring_x", text="Enable X", icon=enabled_icon(data.use_spring_x))
        col.prop(data, "use_spring_y", text="Y", icon=enabled_icon(data.use_spring_y))
        col.prop(data, "use_spring_z", text="Z", icon=enabled_icon(data.use_spring_z))

        flow.separator()

        col = flow.column(align=True)

        sub = col.column()
        sub.enabled = data.use_spring_x
        sub.prop(data, "spring_stiffness_x", text="Stiffness X")

        sub = col.column()
        sub.enabled = data.use_spring_y
        sub.prop(data, "spring_stiffness_y", text="Y")

        sub = col.column()
        sub.enabled = data.use_spring_z
        sub.prop(data, "spring_stiffness_z", text="Z")

        flow.separator()

        col = flow.column(align=True)

        sub = col.column()
        sub.enabled = data.use_spring_x
        sub.prop(data, "spring_damping_x", text="Damping X")

        sub = col.column()
        sub.enabled = data.use_spring_y
        sub.prop(data, "spring_damping_y", text="Y")

        sub = col.column()
        sub.enabled = data.use_spring_z
        sub.prop(data, "spring_damping_z", text="Z")

        flow.separator()


class OffsetPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_bone_offset"
    bl_label = "Offset"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_parent_id = "DATA_PT_rigid_body_bones_bone"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 4

    def draw(self, context):
        data = utils.get_active_bone(context.active_object).rigid_body_bones
        layout = self.layout

        layout.enabled = data.enabled and utils.is_armature_enabled(context)
        layout.use_property_split = True

        flow = layout.grid_flow(row_major=True, columns=1, even_columns=True, even_rows=False, align=True)

        flow.separator()

        col = flow.column()
        col.prop(data, "origin", slider=True, text="Origin")

        flow.separator()

        col = flow.column()
        col.prop(data, "location")

        flow.separator()

        col = flow.column()
        col.prop(data, "rotation")

        if data.collision_shape != 'COMPOUND':
            flow.separator()

            col = flow.column()
            col.prop(data, "scale")

        flow.separator()


class AdvancedPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_bone_advanced"
    bl_label = "Advanced"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigid Body Bones"
    bl_parent_id = "DATA_PT_rigid_body_bones_bone"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 5

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

        flow.separator()


class CollectionsPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_collections"
    bl_label = "Collision Layers"
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

        layout.separator()


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

        flow.separator()


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
