import bpy
from . import utils


def is_edit_mode(context):
    return (
        (context.active_bone is not None) and
        (context.mode == 'EDIT_ARMATURE')
    )


def make_root_body(context, armature, data):
    if not data.root_body:
        with utils.Mode(context, 'EDIT'):
            #bpy.context.space_data.context = 'PHYSICS'

            #bpy.ops.screen.space_type_set_or_cycle(space_type='PROPERTIES')

            #with Tab(context, 'PHYSICS'):
                #log(local["area"].type)

            #root_body = utils.make_empty_rigid_body(
                #context,
                #name=armature.name + " [Root]",
                #collection=hitboxes_collection(context, armature),
                #location=armature.location,
            #)

            #with utils.Mode(context, 'EDIT'):

            #hitboxes = [hitbox_data(bone) for bone in armature.data.edit_bones]

            for bone in armature.data.edit_bones:
                print(bone)
                make_hitbox(context, armature, bone)
                    #utils.log(bone.name)

                    #empty = utils.make_empty_rigid_body(
                        #context,
                        #name=bone.name + " [Empty]",
                        #collection=data.hitboxes,
                        #location=Vector(bone.head) + Vector(armature.location),
                        #rotation=hitbox_rotation(bone),
                    #)

            #data.root_body = root_body


def make_hitbox(context, armature, bone):
    data = bone.rigid_body_bones

    if not data.hitbox:
        with utils.Selectable(root_collection(context)):
            empty = utils.make_empty_rigid_body(
                context,
                name=bone.name + " [Empty]",
                collection=hitboxes_collection(context, armature),
                parent=armature,
            )

            hitbox = utils.make_active_hitbox(context, armature, bone)
            hitbox = utils.make_passive_hitbox(context, armature, bone)

            return

            data.hitbox = hitbox

    return data.hitbox


def align_hitbox(context, armature, bone):
    data = bone.rigid_body_bones
    hitbox = data.hitbox

    if hitbox:
        utils.select(context, [hitbox])
        hitbox.location = hitbox_location(armature, bone)
        hitbox.rotation = hitbox_rotation(bone)
        hitbox.dimensions = hitbox_dimensions(bone)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    if data.constraint:
        pass


def cleanup_bone(bone):
    data = bone.rigid_body_bones
    data.constraint = None
    data.hitbox = None


def remove_collection(context, armature, data):
    with utils.Mode(context, 'EDIT'):
        for bone in armature.data.edit_bones:
            cleanup_bone(bone)

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
    armature = context.active_object
    data = armature.data.rigid_body_bones

    if data.enabled:
        make_root_body(context, armature, data)

    else:
        remove_collection(context, armature, data)


class AlignHitbox(bpy.types.Operator):
    bl_idname = "rigid_body_bones.align_hitbox"
    bl_label = "Align to bone"
    bl_description = "Aligns the hitbox to the bone"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return is_edit_mode(context)

    def execute(self, context):
        armature = context.active_object
        data = armature.data.rigid_body_bones

        with utils.Selectable(context.scene, data), utils.Selected(context):
            align_hitbox(context, armature, context.active_bone)

        return {'FINISHED'}


class SelectInvalidBones(bpy.types.Operator):
    bl_idname = "rigid_body_bones.select_invalid_bones"
    bl_label = "Select invalid bones"
    bl_description = "Selects bones which have invalid properties (such as Parent)"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return is_edit_mode(context)

    def execute(self, context):
        print("Hello World")
        return {'FINISHED'}


class AlignAllHitboxes(bpy.types.Operator):
    bl_idname = "rigid_body_bones.align_all_hitboxes"
    bl_label = "Align all hitboxes"
    bl_description = "Aligns all hitboxes to their respective bones"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_bone is not None)

    def execute(self, context):
        armature = context.active_object
        data = armature.data.rigid_body_bones

        with utils.Mode(context, 'EDIT'), utils.Selectable(context.scene, data), utils.Selected(context):
            for bone in armature.data.edit_bones:
                align_hitbox(context, armature, bone)

        return {'FINISHED'}


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
        return (context.active_bone is not None)

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
        layout.use_property_split = True

        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)

        col = flow.column()
        col.prop(data, "enabled")
        col.prop(data, "hide_active_bones")
        col.prop(data, "hide_hitboxes")

        flow.separator()

        col = flow.column()
        col.operator("rigid_body_bones.align_all_hitboxes")
        col.operator("rigid_body_bones.select_invalid_bones")


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
        return is_edit_mode(context)

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

        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)

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

            flow.separator()

            row = flow.row()
            row.alignment = 'CENTER'
            row.operator("rigid_body_bones.align_hitbox")


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


class AdvancedSettingsPanel(bpy.types.Panel):
    bl_idname = "DATA_PT_rigid_body_bones_advanced_settings"
    bl_label = "Settings"
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

        flow = self.layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)

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

        flow = self.layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)

        col = flow.column()
        col.prop(data, "use_start_deactivated")

        col = flow.column()
        col.prop(data, "deactivate_linear_velocity", text="Velocity Linear")
        col.prop(data, "deactivate_angular_velocity", text="Angular")
