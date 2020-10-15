import bpy
from . import utils
from . import events
from . import properties
from .bones import (
    active_name, align_constraint, align_hitbox, blank_name, constraint_name,
    delete_parent, get_hitbox, hide_active_bone, is_bone_active, is_bone_enabled,
    make_active_hitbox, make_blank_rigid_body, make_constraint, make_empty_rigid_body,
    make_passive_hitbox, remove_active, remove_blank, remove_constraint,
    remove_passive, store_parent, update_constraint, update_hitbox_name,
    update_rigid_body, update_hitbox_shape, passive_name, remove_pose_constraint,
    update_pose_constraint, copy_properties, make_compound_hitbox, remove_compound,
    compound_name,
)


def root_collection(context):
    scene = context.scene

    collection = scene.rigid_body_bones.collection

    if not collection:
        collection = utils.make_collection("RigidBodyBones", scene.collection)
        collection.hide_render = True
        scene.rigid_body_bones.collection = collection

    return collection


def container_collection(context, armature, top):
    collection = top.container

    name = armature.data.name + " [Container]"

    if not collection:
        parent = root_collection(context)
        collection = utils.make_collection(name, parent)
        collection.hide_render = True
        top.container = collection

    else:
        collection.name = name

    return collection


def child_collection(context, armature, top, name):
    parent = container_collection(context, armature, top)
    collection = utils.make_collection(name, parent)
    collection.hide_render = True
    return collection


def actives_collection(context, armature, top):
    collection = top.actives

    name = armature.data.name + " [Actives]"

    if not collection:
        collection = child_collection(context, armature, top, name)
        top.actives = collection

    else:
        collection.name = name

    return collection


def passives_collection(context, armature, top):
    collection = top.passives

    name = armature.data.name + " [Passives]"

    if not collection:
        collection = child_collection(context, armature, top, name)
        top.passives = collection

    else:
        collection.name = name

    return collection


def compounds_collection(context, armature, top):
    collection = top.compounds

    name = armature.data.name + " [Compounds]"

    if not collection:
        collection = child_collection(context, armature, top, name)
        top.compounds = collection

    else:
        collection.name = name

    return collection


def blanks_collection(context, armature, top):
    collection = top.blanks

    name = armature.data.name + " [Blanks]"

    if not collection:
        collection = child_collection(context, armature, top, name)
        top.blanks = collection

    else:
        collection.name = name

    return collection


def constraints_collection(context, armature, top):
    collection = top.constraints

    name = armature.data.name + " [Joints]"

    if not collection:
        collection = child_collection(context, armature, top, name)
        top.constraints = collection

    else:
        collection.name = name

    return collection


def remove_orphans(collection, exists):
    for object in collection.objects:
        if object.name not in exists:
            utils.remove_object(object)

    return utils.safe_remove_collection(collection)


def remove_collection_orphans(collection, exists):
    for sub in collection.children:
        if sub.name not in exists:
            utils.remove_collection_recursive(sub)

    return utils.safe_remove_collection(collection)


def make_root_body(context, armature, top):
    name = armature.data.name + " [Root]"

    if not top.root_body:
        top.root_body = make_empty_rigid_body(
            context,
            name=name,
            collection=blanks_collection(context, armature, top),
            parent=armature,
            parent_bone=None,
        )

    else:
        top.root_body.name = name

    return top.root_body


def remove_root_body(top):
    if top.root_body:
        utils.remove_object(top.root_body)
        top.property_unset("root_body")


# This must be an operator, because it creates/destroys data blocks (e.g. objects).
# It must run asynchronously, in a separate tick. This is handled by `events.mark_dirty`.
class Update(bpy.types.Operator):
    bl_idname = "rigid_body_bones.update"
    bl_label = "Update Rigid Body Bones"
    # TODO use UNDO_GROUPED ?
    bl_options = {'REGISTER', 'UNDO'}


    def fix_duplicates(self, data):
        duplicates = self.duplicates

        if data.active:
            name = data.active.name

            if name in duplicates:
                data.property_unset("active")

            else:
                duplicates.add(name)

        if data.passive:
            name = data.passive.name

            if name in duplicates:
                data.property_unset("passive")

            else:
                duplicates.add(name)

        if data.blank:
            name = data.blank.name

            if name in duplicates:
                data.property_unset("blank")

            else:
                duplicates.add(name)

        if data.constraint:
            name = data.constraint.name

            if name in duplicates:
                data.property_unset("constraint")

            else:
                duplicates.add(name)

        for compound in data.compounds:
            if compound.hitbox:
                name = compound.hitbox.name

                if name in duplicates:
                    compound.property_unset("hitbox")

                else:
                    duplicates.add(name)


    # TODO non-recursive version ?
    def is_active_parent(self, bone):
        if bone is None:
            return False

        else:
            is_active = self.active_cache.get(bone.name)

            if is_active is not None:
                return is_active

            else:
                data = bone.rigid_body_bones

                # Cannot use is_bone_enabled
                if data.enabled and is_bone_active(data):
                    self.active_cache[bone.name] = True
                    return True

                else:
                    is_active = self.is_active_parent(bone.parent)
                    self.active_cache[bone.name] = is_active
                    return is_active


    def update_error(self, top, bone, data):
        # Cannot use is_bone_enabled
        if data.enabled and is_bone_active(data):
            self.active_cache[bone.name] = True
            data.property_unset("error")

        else:
            is_active = self.is_active_parent(bone.parent)
            self.active_cache[bone.name] = is_active

            if is_active:
                data.error = 'ACTIVE_PARENT'
                error = top.errors.add()
                error.name = bone.name

            else:
                data.property_unset("error")


    def process_parent(self, armature, top, bone, data):
        if data.is_property_set("parent"):
            assert data.is_property_set("name")
            assert data.is_property_set("use_connect")

            self.names[data.name] = bone.name

            # Can't use is_bone_enabled because this runs before update_error
            if top.enabled and not self.is_edit_mode and data.enabled and is_bone_active(data):
                self.remove_parents.add(bone.name)

            elif bone.parent is None:
                self.restore_parents[bone.name] = (data.parent, data.use_connect)


    def hide_active(self, top, bone, data):
        hide_active_bone(bone, data, top.enabled and top.hide_active_bones)


    def update_active_constraint(self, context, armature, top, bone, data):
        assert data.is_property_set("parent")

        constraint = data.constraint.rigid_body_constraint

        constraint.object2 = data.active

        if data.parent == "":
            self.has_root_body = True
            constraint.object1 = make_root_body(context, armature, top)

        # Will be processed later, by update_joint
        else:
            parent = self.active_children.get(data.parent)

            if parent is None:
                parent = []
                self.active_children[data.parent] = parent

            # TODO is this safe if a reallocation happens ?
            parent.append(constraint)


    def make_compounds(self, context, armature, top, parent, bone, data):
        is_compound = (data.collision_shape == 'COMPOUND')

        for compound in data.compounds:
            if is_compound:
                if not compound.hitbox:
                    collection = compounds_collection(context, armature, top)
                    compound.hitbox = make_compound_hitbox(context, collection, bone, compound)

                else:
                    update_hitbox_name(compound.hitbox, compound_name(bone, compound))

                # TODO only set this if the parent is different ?
                utils.set_parent(compound.hitbox, parent)

                self.exists.add(compound.hitbox.name)

            else:
                remove_compound(compound)


    def update_bone(self, context, armature, top, bone, data):
        if top.enabled and is_bone_enabled(data):
            if is_bone_active(data):
                remove_passive(data)

                if not data.active:
                    collection = actives_collection(context, armature, top)
                    data.active = make_active_hitbox(context, armature, collection, bone, data)

                else:
                    update_hitbox_name(data.active, active_name(bone))

                if not data.constraint:
                    collection = constraints_collection(context, armature, top)
                    data.constraint = make_constraint(context, armature, collection, bone, data)

                else:
                    data.constraint.name = constraint_name(bone)

                self.make_compounds(context, armature, top, data.active, bone, data)
                align_hitbox(data.active, bone, data)
                update_hitbox_shape(data.active, data)
                update_rigid_body(data.active.rigid_body, data)

                align_constraint(data.constraint, bone)
                update_constraint(data.constraint.rigid_body_constraint, data)

                self.update_active_constraint(context, armature, top, bone, data)

                self.exists.add(data.active.name)
                self.exists.add(data.constraint.name)

            else:
                remove_active(data)
                remove_constraint(data)

                if not data.passive:
                    collection = passives_collection(context, armature, top)
                    data.passive = make_passive_hitbox(context, armature, collection, bone, data)

                else:
                    update_hitbox_name(data.passive, passive_name(bone))

                self.make_compounds(context, armature, top, data.passive, bone, data)
                align_hitbox(data.passive, bone, data)
                update_hitbox_shape(data.passive, data)
                update_rigid_body(data.passive.rigid_body, data)

                self.exists.add(data.passive.name)

        else:
            remove_active(data)
            remove_passive(data)
            remove_constraint(data)

            for compound in data.compounds:
                remove_compound(compound)


    def fix_parents(self, armature, top, bone, data):
        if self.store_parents:
            store_parent(bone, data)

        self.process_parent(armature, top, bone, data)

        if self.delete_parents:
            delete_parent(data)


    def process_bone(self, context, armature, top, bone):
        data = bone.rigid_body_bones

        self.update_error(top, bone, data)

        self.fix_duplicates(data)

        self.hide_active(top, bone, data)

        self.update_bone(context, armature, top, bone, data)


    def update_joint(self, context, armature, top, bone):
        data = bone.rigid_body_bones

        assert data.is_property_set("name")

        children = self.active_children.get(data.name)

        if children:
            if is_bone_enabled(data):
                remove_blank(data)

                hitbox = get_hitbox(data)

                assert hitbox is not None

                for constraint in children:
                    constraint.object1 = hitbox

            elif data.error != "":
                remove_blank(data)

                # This is needed in order to avoid cyclic dependencies with invalid Passives
                for constraint in children:
                    constraint.object1 = None

            else:
                blank = data.blank

                if not blank:
                    collection = blanks_collection(context, armature, top)
                    blank = make_blank_rigid_body(context, armature, collection, bone, data)
                    data.blank = blank

                else:
                    blank.name = blank_name(bone)

                self.exists.add(blank.name)

                for constraint in children:
                    constraint.object1 = blank

        else:
            remove_blank(data)


    def update_constraints(self, context, armature, top):
        if top.enabled:
            # Create/update/remove Child Of constraints
            for pose_bone in armature.pose.bones:
                update_pose_constraint(pose_bone)
                self.update_joint(context, armature, top, pose_bone.bone)

        else:
            # Remove Child Of constraints
            for pose_bone in armature.pose.bones:
                remove_pose_constraint(pose_bone)
                remove_blank(pose_bone.bone.rigid_body_bones)

        if self.has_root_body:
            self.exists.add(top.root_body.name)

        else:
            remove_root_body(top)


    def change_parents(self, context, armature):
        edit_bones = armature.data.edit_bones

        for edit_bone in edit_bones:
            name = edit_bone.name
            data = self.restore_parents.get(name)

            # Restore parent
            if data is not None:
                (parent_name, use_connect) = data

                assert edit_bone.parent is None

                if parent_name != "":
                    edit_bone.parent = edit_bones[self.names[parent_name]]

                edit_bone.use_connect = use_connect

            # Remove parent
            elif name in self.remove_parents:
                edit_bone.parent = None


    # This cleans up any objects which are left behind after a bone
    # has been deleted.
    def remove_orphans(self, context, armature, top):
        exists = self.exists

        if top.actives and remove_orphans(top.actives, exists):
            top.property_unset("actives")

        if top.passives and remove_orphans(top.passives, exists):
            top.property_unset("passives")

        if top.compounds and remove_orphans(top.compounds, exists):
            top.property_unset("compounds")

        if top.blanks and remove_orphans(top.blanks, exists):
            top.property_unset("blanks")

        if top.constraints and remove_orphans(top.constraints, exists):
            top.property_unset("constraints")

        if top.container and remove_orphans(top.container, exists):
            top.property_unset("container")


        scene = context.scene.rigid_body_bones

        if scene.collection and utils.safe_remove_collection(scene.collection):
            scene.property_unset("collection")


    def process_edit(self, context, armature, top):
        for pose_bone in armature.pose.bones:
            bone = pose_bone.bone
            data = bone.rigid_body_bones

            remove_pose_constraint(pose_bone)

            self.fix_parents(armature, top, bone, data)

        if top.actives:
            top.actives.hide_viewport = True

        if top.passives:
            top.passives.hide_viewport = True

        if top.compounds:
            top.compounds.hide_viewport = True


    def process_pose(self, context, armature, top):
        top.errors.clear()


        for bone in armature.data.bones:
            data = bone.rigid_body_bones
            self.fix_parents(armature, top, bone, data)


        # This must happen before process_bone
        with utils.Mode(context, 'EDIT'):
            self.change_parents(context, armature)


        for bone in armature.data.bones:
            self.process_bone(context, armature, top, bone)


        self.update_constraints(context, armature, top)

        self.remove_orphans(context, armature, top)

        if top.actives:
            top.actives.hide_viewport = top.hide_hitboxes

        if top.passives:
            top.passives.hide_viewport = top.hide_hitboxes

        if top.compounds:
            top.compounds.hide_viewport = top.hide_hitboxes


    @classmethod
    def poll(cls, context):
        return utils.is_armature(context)


    def execute(self, context):
        armature = context.active_object
        top = armature.data.rigid_body_bones


        # Fast lookup for stored bone names -> new name
        self.names = {}

        # Data for bones which should have their parent restored
        self.restore_parents = {}

        # Names of bones which should have their parent removed
        self.remove_parents = set()

        # Whether to destructively delete/store the bone parent data
        self.delete_parents = False
        self.store_parents = False

        self.is_edit_mode = (top.mode == 'EDIT')


        if self.is_edit_mode:
            assert armature.mode == 'EDIT'
        else:
            assert armature.mode != 'EDIT'


        if self.is_edit_mode or not top.enabled:
            if top.parents_stored:
                top.property_unset("parents_stored")
                self.delete_parents = True

        else:
            if not top.parents_stored:
                top.parents_stored = True
                self.store_parents = True


        if self.is_edit_mode:
            with utils.Mode(context, 'POSE'):
                self.process_edit(context, armature, top)

            self.change_parents(context, armature)

        else:
            # Fast lookup for stored bone names -> list of active children
            self.active_children = {}

            # Names of objects which exist
            self.exists = set()

            # Names of objects for testing for duplicates
            self.duplicates = set()

            # Cache of whether a bone has an active parent or not
            self.active_cache = {}

            # Whether the root body should exist or not
            self.has_root_body = False

            self.process_pose(context, armature, top)


        return {'FINISHED'}


# This cleans up any orphan objects when an armature is deleted
class CleanupArmatures(bpy.types.Operator):
    bl_idname = "rigid_body_bones.cleanup_armatures"
    bl_label = "Cleanup Rigid Body Bones"
    # TODO use UNDO_GROUPED ?
    bl_options = {'REGISTER', 'UNDO'}


    @classmethod
    def poll(cls, context):
        return context.scene.rigid_body_bones.collection is not None


    def execute(self, context):
        exists = set()

        for armature in bpy.data.armatures:
            container = armature.rigid_body_bones.container

            if container:
                exists.add(container.name)

        scene = context.scene.rigid_body_bones

        if remove_collection_orphans(scene.collection, exists):
            scene.property_unset("collection")

        return {'FINISHED'}


class CopyFromActive(bpy.types.Operator):
    bl_idname = "rigid_body_bones.copy_from_active"
    bl_label = "Copy from Active"
    bl_description = "Copy Rigid Body settings from active bone to selected bones"
    # TODO use UNDO_GROUPED ?
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return utils.is_pose_mode(context) and utils.is_armature(context) and utils.has_active_bone(context)

    def execute(self, context):
        armature = context.active_object
        active = utils.get_active_bone(armature)
        active_data = active.rigid_body_bones

        for pose_bone in context.selected_pose_bones_from_active_object:
            bone = pose_bone.bone

            if bone.name != active.name:
                copy_properties(active_data, bone.rigid_body_bones)

        return {'FINISHED'}


def make_material_preset(presets):
    output = [(preset, preset, "", i) for i, preset in enumerate(presets)]
    output.append(('Custom', "Custom", "", -1))
    return output


class CalculateMass(bpy.types.Operator):
    bl_idname = "rigid_body_bones.calculate_mass"
    bl_label = "Calculate Mass"
    bl_description = "Automatically calculates mass for selected bones based on volume"
    # TODO use UNDO_GROUPED ?
    bl_options = {'REGISTER', 'UNDO'}

    material: bpy.props.EnumProperty(
        name="Material Preset",
        description="Type of material that bones are made of (determines material density)",
        default='Air',
        # Based on source/blender/editors/physics/rigidbody_object.c
        items=make_material_preset([
            'Air',
            'Acrylic',
            'Asphalt (Crushed)',
            'Bark',
            'Beans (Cocoa)',
            'Beans (Soy)',
            'Brick (Pressed)',
            'Brick (Common)',
            'Brick (Soft)',
            'Brass',
            'Bronze',
            'Carbon (Solid)',
            'Cardboard',
            'Cast Iron',
            'Chalk (Solid)',
            'Concrete',
            'Charcoal',
            'Cork',
            'Copper',
            'Garbage',
            'Glass (Broken)',
            'Glass (Solid)',
            'Gold',
            'Granite (Broken)',
            'Granite (Solid)',
            'Gravel',
            'Ice (Crushed)',
            'Ice (Solid)',
            'Iron',
            'Lead',
            'Limestone (Broken)',
            'Limestone (Solid)',
            'Marble (Broken)',
            'Marble (Solid)',
            'Paper',
            'Peanuts (Shelled)',
            'Peanuts (Not Shelled)',
            'Plaster',
            'Plastic',
            'Polystyrene',
            'Rubber',
            'Silver',
            'Steel',
            'Stone',
            'Stone (Crushed)',
            'Timber',
        ])
    )

    density: bpy.props.FloatProperty(
        name="Density",
        description="Density value (kg/m^3) to use when Material Preset is Custom",
        default=1.0,
        min=0.0,
        soft_min=1.0,
        soft_max=2500.0,
        precision=3,
        step=1,
    )

    # TODO check for selected ?
    @classmethod
    def poll(cls, context):
        return utils.is_pose_mode(context) and utils.is_armature(context)

    def execute(self, context):
        datas = []

        with utils.Selected(context), utils.Selectable(context):
            utils.deselect_all(context)

            for pose_bone in context.selected_pose_bones_from_active_object:
                bone = pose_bone.bone
                data = bone.rigid_body_bones
                hitbox = get_hitbox(data)

                if hitbox:
                    datas.append(data)
                    utils.select_active(context, hitbox)

            bpy.ops.rigidbody.mass_calculate(material=self.material, density=self.density)

        # This is only needed to prevent the mass update callback from running.
        # TODO make this more efficient
        events.mark_dirty(context)

        for data in datas:
            hitbox = get_hitbox(data)
            data.mass = hitbox.rigid_body.mass

        return {'FINISHED'}


def add_new_compound(bone):
    data = bone.rigid_body_bones

    seen = set()

    for compound in data.compounds:
        seen.add(compound.name)

    data.active_compound_index = len(data.compounds)

    new_compound = data.compounds.add()

    properties.Compound.is_updating = True
    new_compound.name = utils.make_unique_name("Hitbox", seen)
    properties.Compound.is_updating = False


def delete_compound(bone):
    data = bone.rigid_body_bones

    old_index = data.active_compound_index

    data.compounds.remove(old_index)

    length = len(data.compounds)

    if old_index >= length:
        data.active_compound_index = max(length - 1, 0)


def move_compound(bone, direction):
    data = bone.rigid_body_bones

    old_index = data.active_compound_index

    if direction == 'UP':
        new_index = max(old_index - 1, 0)

    else:
        new_index = min(old_index + 1, len(data.compounds) - 1)

    if old_index != new_index:
        data.compounds.move(old_index, new_index)
        data.active_compound_index = new_index


class NewCompound(bpy.types.Operator):
    bl_idname = "rigid_body_bones.new_compound"
    bl_label = "Add new hitbox"
    bl_description = "Adds a new hitbox to the compound shape"
    # TODO use UNDO_GROUPED ?
    bl_options = {'UNDO'}

    is_alt: bpy.props.BoolProperty()

    # TODO test for COMPOUND shape ?
    @classmethod
    def poll(cls, context):
        return utils.is_pose_mode(context) and utils.is_armature(context) and utils.has_active_bone(context)

    # TODO is there a better way of handling Alt ?
    def invoke(self, context, event):
        self.is_alt = event.alt
        return self.execute(context)

    def execute(self, context):
        if self.is_alt:
            for pose_bone in context.selected_pose_bones_from_active_object:
                bone = pose_bone.bone
                add_new_compound(bone)

        else:
            armature = context.active_object
            bone = utils.get_active_bone(armature)
            add_new_compound(bone)

        events.mark_dirty(context)

        return {'FINISHED'}


class RemoveCompound(bpy.types.Operator):
    bl_idname = "rigid_body_bones.remove_compound"
    bl_label = "Remove hitbox"
    bl_description = "Deletes the selected hitbox"
    # TODO use UNDO_GROUPED ?
    bl_options = {'UNDO'}

    is_alt: bpy.props.BoolProperty()

    # TODO test for COMPOUND shape ?
    @classmethod
    def poll(cls, context):
        return utils.is_pose_mode(context) and utils.is_armature(context) and utils.has_active_bone(context)

    # TODO is there a better way of handling Alt ?
    def invoke(self, context, event):
        self.is_alt = event.alt
        return self.execute(context)

    def execute(self, context):
        if self.is_alt:
            for pose_bone in context.selected_pose_bones_from_active_object:
                bone = pose_bone.bone
                delete_compound(bone)

        else:
            armature = context.active_object
            bone = utils.get_active_bone(armature)
            delete_compound(bone)

        events.mark_dirty(context)

        return {'FINISHED'}


class MoveCompound(bpy.types.Operator):
    bl_idname = "rigid_body_bones.move_compound"
    bl_label = "Move hitbox"
    bl_description = "Moves the selected hitbox up/down in the list"
    # TODO use UNDO_GROUPED ?
    bl_options = {'UNDO'}

    is_alt: bpy.props.BoolProperty()

    direction: bpy.props.EnumProperty(
        items=[
            ('UP', "", ""),
            ('DOWN', "", ""),
        ]
    )

    # TODO test for COMPOUND shape ?
    @classmethod
    def poll(cls, context):
        return utils.is_pose_mode(context) and utils.is_armature(context) and utils.has_active_bone(context)

    # TODO is there a better way of handling Alt ?
    def invoke(self, context, event):
        self.is_alt = event.alt
        return self.execute(context)

    def execute(self, context):
        if self.is_alt:
            for pose_bone in context.selected_pose_bones_from_active_object:
                bone = pose_bone.bone
                move_compound(bone, self.direction)

        else:
            armature = context.active_object
            bone = utils.get_active_bone(armature)
            move_compound(bone, self.direction)

        return {'FINISHED'}
