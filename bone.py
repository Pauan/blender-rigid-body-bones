import bpy


def update(self, context):
    print("BONE")
    if self.enabled:
        print("ENABLED")


class Panel(bpy.types.Panel):
    #bl_space_type = 'PROPERTIES'
    #bl_region_type = 'WINDOW'

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    #bl_category = "Tool"


class BONE_PT_rigid_body_bones_bone(Panel):
    bl_label = "Rigid Body"
    bl_context = 'bone'

    @classmethod
    def poll(cls, context):
        return (
            (context.mode == 'EDIT_ARMATURE') and
            (context.armature is not None) and
            (context.armature.rigid_body_bones.enabled) and
            (context.edit_bone is not None)
        )

    def draw_header(self, context):
        data = context.edit_bone.rigid_body_bones

        self.layout.prop(data, "enabled", text = "")

    def draw(self, context):
        pass
        #subpanel = self.layout.box()
        #subpanel.label(text = "Hello")


class BONE_PT_rigid_body_bones_constraint(Panel):
    bl_label = "Constraint"
    bl_context = 'bone'
    bl_parent_id = "BONE_PT_rigid_body_bones_bone"
    bl_order = 0
    bl_ui_units_x = 200
    #bl_options = {'DEFAULT_CLOSED', 'HEADER_LAYOUT_EXPAND'}

    def draw_header(self, context):
        data = context.edit_bone.rigid_body_bones

        self.layout.prop(data, "enable_constraint", text = "")

    def draw(self, context):
        data = context.edit_bone.rigid_body_bones

        self.layout.use_property_decorate = True
        self.layout.use_property_split = True

        #self.layout.separator()

        self.layout.label(text= "Hi")

        self.layout.prop_search(data, "parent", context.armature, "edit_bones")
