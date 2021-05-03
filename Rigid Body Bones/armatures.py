import re
import bpy
from . import utils
from . import events
from . import properties
from .bones import (
    active_name, align_hitbox, blank_name, joint_name, align_joint, make_extra_joint,
    delete_parent, get_hitbox, hide_active_bone, is_bone_active, is_bone_enabled,
    make_active_hitbox, make_blank_rigid_body, make_joint, make_empty_rigid_body,
    make_passive_hitbox, remove_active, remove_blank, remove_joint,
    remove_passive, store_parent, update_joint_constraint, update_hitbox_name,
    update_rigid_body, update_hitbox_shape, passive_name, remove_pose_constraint,
    copy_properties, make_compound_hitbox, remove_compound, compound_name,
    make_origin, origin_name, align_origin, remove_origin, compound_origin_name,
    create_pose_constraint, update_joint_active, mute_pose_constraint,
)


DATA_PATH_REGEXP = re.compile(r"""^pose\.bones\["([^"]+)"\]""")


def add_error(top, name):
    for error in top.errors:
        if error.name == name:
            return

    error = top.errors.add()
    error.name = name


def root_collection(context):
    scene = context.scene

    collection = scene.rigid_body_bones.collection

    if not collection:
        collection = utils.make_collection("RigidBodyBones", scene.collection)
        collection.hide_render = True
        collection.color_tag = 'COLOR_01' # Red
        scene.rigid_body_bones.collection = collection

    return collection


def container_collection(context, armature, top):
    collection = top.container

    name = armature.data.name + " [Container]"

    if not collection:
        parent = root_collection(context)
        collection = utils.make_collection(name, parent)
        collection.hide_render = True
        collection.color_tag = 'COLOR_01' # Red
        top.container = collection

    else:
        collection.name = name

    return collection


def child_collection(context, armature, top, name):
    parent = container_collection(context, armature, top)
    collection = utils.make_collection(name, parent)
    collection.hide_render = True
    collection.color_tag = 'COLOR_01' # Red
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


def origins_collection(context, armature, top):
    collection = top.origins

    name = armature.data.name + " [Origins]"

    if not collection:
        collection = child_collection(context, armature, top, name)
        top.origins = collection

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


def joints_collection(context, armature, top):
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


def remove_root_body(top):
    if top.root_body:
        utils.remove_object(top.root_body)
        top.property_unset("root_body")


# This must be an operator, because it creates/destroys data blocks (e.g. objects).
# It must run asynchronously, in a separate tick. This is handled by `events.event_update`.
class Update(bpy.types.Operator):
    bl_idname = "rigid_body_bones.update"
    bl_label = "Update Rigid Body Bones"
    # TODO use UNDO_GROUPED ?
    bl_options = {'INTERNAL', 'UNDO'}


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

            if bone.parent is None:
                if data.parent != "":
                    self.restore_parent[bone.name] = (data.parent, data.use_connect)

            else:
                # Can't use is_bone_enabled because this runs before update_error
                if top.enabled and self.is_active and data.enabled and is_bone_active(data):
                    self.remove_parent.add(bone.name)


    def hide_active(self, top, bone, data):
        hide_active_bone(bone, data, top.enabled and top.hide_active_bones)


    def make_root_body(self, context, armature, top):
        name = armature.data.name + " [Root]"

        root = top.root_body

        if not root:
            root = make_empty_rigid_body(
                context,
                name=name,
                collection=blanks_collection(context, armature, top),
                parent=armature,
                parent_bone=None,
            )

            top.root_body = root

        else:
            root.name = name

        self.exists.add(root.name)

        return root


    def make_origin(self, context, armature, top, data, parent, name):
        origin = data.origin_empty

        if not origin:
            collection = origins_collection(context, armature, top)
            origin = make_origin(collection, name)
            data.origin_empty = origin

        else:
            origin.name = name

        # TODO only set this if the parent is different ?
        utils.set_parent(origin, parent)

        self.exists.add(origin.name)


    def make_blank(self, context, armature, top, bone, data):
        blank = data.blank

        if not blank:
            collection = blanks_collection(context, armature, top)
            blank = make_blank_rigid_body(context, armature, collection, bone, data)
            data.blank = blank

        else:
            blank.name = blank_name(bone)

        self.exists.add(blank.name)

        return blank


    def make_joint(self, context, armature, top, data, name, is_extra):
        joint = data.constraint

        if not joint:
            collection = joints_collection(context, armature, top)

            if is_extra:
                joint = make_extra_joint(collection, name)
            else:
                joint = make_joint(collection, name)

            data.constraint = joint

        else:
            joint.name = name

        joint.hide_viewport = True

        self.exists.add(joint.name)

        return joint


    def get_hitbox(self, context, armature, top, bone, data):
        hitbox = get_hitbox(data)

        if hitbox:
            return hitbox

        elif data.error == "":
            return self.make_blank(context, armature, top, bone, data)

        # In order to avoid circular dependencies it must not create a Blank for errored bones
        else:
            return None


    def make_compounds(self, context, armature, top, bone, data, parent):
        if data.collision_shape == 'COMPOUND':
            for compound in data.compounds:
                if not compound.hitbox:
                    collection = compounds_collection(context, armature, top)
                    compound.hitbox = make_compound_hitbox(context, collection, bone, compound)

                else:
                    update_hitbox_name(compound.hitbox, compound_name(bone, compound))

                assert parent is not None

                # TODO only set this if the parent is different ?
                utils.set_parent(compound.hitbox, parent)

                self.exists.add(compound.hitbox.name)

                self.make_origin(context, armature, top, compound, compound.hitbox, compound_origin_name(bone, compound))

        else:
            for compound in data.compounds:
                remove_compound(compound)


    def make_parent_joints(self, context, armature, top, pose_bone, data):
        joint = self.make_joint(context, armature, top, data, joint_name(pose_bone.bone), False)
        parent = pose_bone.parent

        if parent:
            parent_data = parent.bone.rigid_body_bones

            self.make_parent_joints(context, armature, top, parent, parent_data)

            assert parent_data.constraint is not None

            utils.set_parent(joint, parent_data.constraint)
            # This transforms the matrix from armature space to local space
            joint.matrix_basis = parent.matrix.inverted() @ pose_bone.matrix

        else:
            utils.set_parent(joint, armature)
            joint.matrix_basis = pose_bone.matrix

        return joint


    def update_bone(self, context, armature, top, pose_bone, bone, data):
        if top.enabled and is_bone_enabled(data):
            if is_bone_active(data):
                remove_passive(data)

                self.make_parent_joints(context, armature, top, pose_bone, data)

                if not data.active:
                    collection = actives_collection(context, armature, top)
                    data.active = make_active_hitbox(context, armature, collection, bone, data)

                else:
                    update_hitbox_name(data.active, active_name(bone))

                self.make_compounds(context, armature, top, bone, data, data.active)
                self.make_origin(context, armature, top, data, data.active, origin_name(bone))

                align_origin(data.origin_empty, pose_bone, data)

                align_hitbox(data.active, armature, pose_bone, data, self.is_active)
                update_hitbox_shape(data.active, data)
                update_rigid_body(data.active.rigid_body, data)

                self.exists.add(data.active.name)

            else:
                remove_active(data)

                if not data.passive:
                    collection = passives_collection(context, armature, top)
                    data.passive = make_passive_hitbox(context, armature, collection, bone, data)

                else:
                    update_hitbox_name(data.passive, passive_name(bone))

                self.make_compounds(context, armature, top, bone, data, data.passive)
                self.make_origin(context, armature, top, data, data.passive, origin_name(bone))

                align_origin(data.origin_empty, pose_bone, data)

                align_hitbox(data.passive, armature, pose_bone, data, False)
                update_hitbox_shape(data.passive, data)
                update_rigid_body(data.passive.rigid_body, data)

                self.exists.add(data.passive.name)

        else:
            remove_active(data)
            remove_passive(data)
            remove_origin(data)

            for compound in data.compounds:
                remove_compound(compound)


    def fix_parents(self, armature, top, bone, data):
        if self.store_parents:
            store_parent(bone, data)

        self.process_parent(armature, top, bone, data)

        if self.delete_parents:
            delete_parent(data)


    def add_id(self, bone, data):
        id = data.id

        if id != "":
            # TODO handle duplication better somehow ?
            if id in self.ids:
                data.property_unset("id")

            else:
                self.ids[id] = bone


    def process_bone(self, context, armature, top, pose_bone):
        bone = pose_bone.bone
        data = bone.rigid_body_bones

        self.add_id(bone, data)

        self.update_error(top, bone, data)

        self.fix_duplicates(data)

        self.hide_active(top, bone, data)

        self.update_bone(context, armature, top, pose_bone, bone, data)


    def make_joints(self, context, armature, top, pose_bone, bone_data):
        for data in bone_data.joints:
            if data.bone_name == "" or data.error != "":
                add_error(top, pose_bone.bone.name)
                remove_joint(data)

            elif data.bone_id != "":
                connected_bone = self.ids.get(data.bone_id, None)

                if connected_bone:
                    properties.Joint.is_updating = True
                    data.bone_name = connected_bone.name
                    properties.Joint.is_updating = False

                    parent = self.make_parent_joints(context, armature, top, pose_bone, bone_data)
                    joint = self.make_joint(context, armature, top, data, joint_name(pose_bone.bone, name=data.name), True)

                    align_joint(joint, pose_bone, data)

                    utils.set_parent(joint, parent)

                    update_joint_active(context, joint, True)

                    constraint = joint.rigid_body_constraint

                    update_joint_constraint(constraint, data)

                    constraint.object1 = self.get_hitbox(context, armature, top, connected_bone, connected_bone.rigid_body_bones)
                    constraint.object2 = self.get_hitbox(context, armature, top, pose_bone.bone, bone_data)

                else:
                    data.error = 'INVALID_BONE'
                    add_error(top, pose_bone.bone.name)
                    remove_joint(data)

            else:
                data.error = 'INVALID_BONE'
                add_error(top, pose_bone.bone.name)
                remove_joint(data)


    def update_joint(self, context, armature, top, pose_bone):
        bone = pose_bone.bone
        data = bone.rigid_body_bones

        self.make_joints(context, armature, top, pose_bone, data)

        is_active = is_bone_enabled(data) and is_bone_active(data)

        joint = data.constraint

        if joint and joint.name in self.exists:
            update_joint_active(context, joint, is_active)

        if is_active:
            create_pose_constraint(armature, pose_bone, data, self.is_active)

            constraint = joint.rigid_body_constraint

            update_joint_constraint(constraint, data)

            parent = pose_bone.parent

            if parent:
                parent_data = parent.bone.rigid_body_bones
                constraint.object1 = self.get_hitbox(context, armature, top, parent.bone, parent_data)

            else:
                constraint.object1 = self.make_root_body(context, armature, top)

            constraint.object2 = data.active

        else:
            remove_pose_constraint(pose_bone, data)


    def update_joints(self, context, armature, top):
        if top.enabled:
            for pose_bone in armature.pose.bones:
                self.update_joint(context, armature, top, pose_bone)

        else:
            for pose_bone in armature.pose.bones:
                data = pose_bone.bone.rigid_body_bones

                remove_pose_constraint(pose_bone, data)

                for joint in data.joints:
                    remove_joint(joint)


    def update_action(self, seen_actions, should_mute, action):
        if not action.name in seen_actions:
            seen_actions.add(action.name)

            for fcurve in action.fcurves:
                match = DATA_PATH_REGEXP.match(fcurve.data_path)

                if match:
                    name = match.group(1)
                    mute = should_mute.get(name, None)

                    if mute is not None:
                        fcurve.mute = mute


    # This disables keyframe animations for Active bones
    def update_fcurves(self, armature, top):
        seen_actions = set()
        should_mute = {}

        is_active = top.enabled and self.is_active

        for pose_bone in armature.pose.bones:
            bone = pose_bone.bone
            data = bone.rigid_body_bones
            should_mute[bone.name] = is_active and is_bone_enabled(data) and is_bone_active(data)

        if armature.pose_library:
            self.update_action(seen_actions, should_mute, armature.pose_library)

        if armature.animation_data:
            self.update_action(seen_actions, should_mute, armature.animation_data.action)

            for track in armature.animation_data.nla_tracks:
                for strip in track.strips:
                    self.update_action(seen_actions, should_mute, strip.action)


    def restore_parents(self, armature):
        edit_bones = armature.data.edit_bones

        for edit_bone in edit_bones:
            name = edit_bone.name
            data = self.restore_parent.get(name)

            if data is not None:
                (parent_name, use_connect) = data

                assert parent_name != ""
                assert edit_bone.parent is None

                edit_bone.parent = edit_bones[self.names[parent_name]]
                edit_bone.use_connect = use_connect


    def remove_parents(self, armature):
        edit_bones = armature.data.edit_bones

        for edit_bone in edit_bones:
            name = edit_bone.name

            if name in self.remove_parent:
                assert edit_bone.parent is not None
                edit_bone.parent = None


    # This cleans up any objects which are left behind after a bone
    # has been deleted.
    def remove_orphans(self, context, armature, top):
        exists = self.exists

        for bone in armature.data.bones:
            data = bone.rigid_body_bones

            blank = data.blank

            if blank and not blank.name in exists:
                remove_blank(data)

            joint = data.constraint

            if joint and not joint.name in exists:
                remove_joint(data)

        if top.root_body and not top.root_body.name in exists:
            remove_root_body(top)

        if top.actives and remove_orphans(top.actives, exists):
            top.property_unset("actives")

        if top.passives and remove_orphans(top.passives, exists):
            top.property_unset("passives")

        if top.compounds and remove_orphans(top.compounds, exists):
            top.property_unset("compounds")

        if top.origins and remove_orphans(top.origins, exists):
            top.property_unset("origins")

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
        with utils.Mode(context, armature, 'POSE'):
            for bone in armature.data.bones:
                data = bone.rigid_body_bones

                self.fix_parents(armature, top, bone, data)

        self.restore_parents(armature)

        if top.actives:
            top.actives.hide_viewport = True

        if top.passives:
            top.passives.hide_viewport = True

        if top.compounds:
            top.compounds.hide_viewport = True

        if top.origins:
            top.origins.hide_viewport = True

        if top.blanks:
            top.blanks.hide_viewport = True

        if top.constraints:
            top.constraints.hide_viewport = True


    def process_pose(self, context, armature, top):
        top.errors.clear()

        for pose_bone in armature.pose.bones:
            bone = pose_bone.bone
            data = bone.rigid_body_bones
            # This is needed in order to avoid a cyclic dependency
            mute_pose_constraint(pose_bone)
            self.fix_parents(armature, top, bone, data)

        # This must happen before process_bone
        with utils.Mode(context, armature, 'EDIT'):
            self.restore_parents(armature)

        for pose_bone in armature.pose.bones:
            self.process_bone(context, armature, top, pose_bone)

        self.update_joints(context, armature, top)

        self.update_fcurves(armature, top)

        self.remove_orphans(context, armature, top)

        # This must happen after update_joints
        if self.is_active:
            with utils.Mode(context, armature, 'EDIT'):
                self.remove_parents(armature)

        if top.actives:
            top.actives.hide_viewport = self.is_active or top.hide_hitboxes

        if top.passives:
            top.passives.hide_viewport = self.is_active or top.hide_hitboxes

        if top.compounds:
            top.compounds.hide_viewport = self.is_active or top.hide_hitboxes

        if top.origins:
            top.origins.hide_viewport = self.is_active or top.hide_hitbox_origins

        if top.blanks:
            top.blanks.hide_viewport = True

        if top.constraints:
            top.constraints.hide_viewport = True


    @classmethod
    def poll(cls, context):
        return utils.is_armature(context)


    def execute(self, context):
        armature = context.active_object
        top = armature.data.rigid_body_bones


        # Fast lookup for bone ID -> bone
        self.ids = {}

        # Fast lookup for stored bone names -> new name
        self.names = {}

        # Data for bones which should have their parent restored
        self.restore_parent = {}

        # Names of bones which should have their parent removed
        self.remove_parent = set()

        # Whether to destructively delete/store the bone parent data
        self.delete_parents = False
        self.store_parents = False

        is_edit_mode = (armature.mode == 'EDIT')

        # Whether the rigid body simulation should be active
        self.is_active = (armature.mode == 'OBJECT')


        if is_edit_mode or not top.enabled:
            if top.parents_stored:
                top.property_unset("parents_stored")
                self.delete_parents = True

        else:
            if not top.parents_stored:
                top.parents_stored = True
                self.store_parents = True


        if is_edit_mode:
            self.process_edit(context, armature, top)

        else:
            # Names of objects which exist
            self.exists = set()

            # Names of objects for testing for duplicates
            self.duplicates = set()

            # Cache of whether a bone has an active parent or not
            self.active_cache = {}

            if self.is_active:
                with utils.AnimationFrame(context):
                    self.process_pose(context, armature, top)
            else:
                self.process_pose(context, armature, top)


        return {'FINISHED'}


# This cleans up any orphan objects when an armature is deleted
class CleanupArmatures(bpy.types.Operator):
    bl_idname = "rigid_body_bones.cleanup_armatures"
    bl_label = "Cleanup Rigid Body Bones"
    # TODO use UNDO_GROUPED ?
    bl_options = {'INTERNAL', 'UNDO'}


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
        return utils.is_pose_mode(context) and utils.has_active_bone(context)

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

        for data in datas:
            hitbox = get_hitbox(data)
            data.mass = hitbox.rigid_body.mass

        return {'FINISHED'}


class BakeToKeyframes(bpy.types.Operator):
    bl_idname = "rigid_body_bones.bake_to_keyframes"
    bl_label = "Bake to Keyframes"
    bl_description = "Bake rigid body transformations of selected bones to keyframes"
    bl_options = {'REGISTER', 'UNDO'}

    frame_start: bpy.props.IntProperty(
        name="Start Frame",
        description="Start frame for baking",
        default=1,
        min=0,
        max=300000,
    )

    frame_end: bpy.props.IntProperty(
        name="End Frame",
        description="End frame for baking",
        default=250,
        min=0,
        max=300000,
    )

    step: bpy.props.IntProperty(
        name="Frame Step",
        description="Frame Step",
        default=1,
        min=1,
        max=120,
    )

    # TODO check for selected ?
    @classmethod
    def poll(cls, context):
        return utils.is_pose_mode(context) and utils.is_armature(context)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        row = layout.row(align=True)
        row.alignment = 'CENTER'
        row.label(text="Baking removes the parent of Active bones", icon='INFO')

        layout.prop(self, "frame_start")
        layout.prop(self, "frame_end")
        layout.prop(self, "step")

    def invoke(self, context, _event):
        scene = context.scene
        self.frame_start = scene.frame_start
        self.frame_end = scene.frame_end

        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        armature = context.active_object

        active = set()
        selected = {}

        for pose_bone in context.selected_pose_bones_from_active_object:
            bone = pose_bone.bone
            data = bone.rigid_body_bones

            assert not bone.hide

            if is_bone_enabled(data) and is_bone_active(data):
                active.add(bone.name)

            else:
                selected[bone.name] = (bone.select, bone.select_head, bone.select_tail)
                bone.select = False
                bone.select_head = False
                bone.select_tail = False

        has_actives = len(active) > 0
        succeeded = False

        try:
            if has_actives:
                with utils.Mode(context, armature, 'OBJECT'):
                    # Temporarily switch to Object mode
                    events.event_update(None, context)
                    # This causes it to run `rigid_body_bones.update` immediately rather than wait for the next tick
                    utils.run_events()

                assert context.active_object == armature
                assert armature.mode == 'POSE'

                # clean_curves was added in 2.92.0
                if bpy.app.version >= (2, 92, 0):
                    bpy.ops.nla.bake(
                        frame_start=self.frame_start,
                        frame_end=self.frame_end,
                        step=self.step,
                        only_selected=True,
                        visual_keying=True,
                        clear_constraints=False,
                        clear_parents=False,
                        use_current_action=True,
                        clean_curves=True,
                        bake_types={'POSE'},
                    )
                else:
                    bpy.ops.nla.bake(
                        frame_start=self.frame_start,
                        frame_end=self.frame_end,
                        step=self.step,
                        only_selected=True,
                        visual_keying=True,
                        clear_constraints=False,
                        clear_parents=False,
                        use_current_action=True,
                        bake_types={'POSE'},
                    )

                succeeded = True

        finally:
            for pose_bone in armature.pose.bones:
                bone = pose_bone.bone
                data = bone.rigid_body_bones

                assert not bone.hide

                # Remove the parent and also disable the rigid body
                if succeeded and bone.name in active:
                    data.type = 'PASSIVE'
                    data.parent = ""
                    data.use_connect = False

                else:
                    select = selected.get(bone.name, None)

                    if select:
                        bone.select = select[0]
                        bone.select_head = select[1]
                        bone.select_tail = select[2]

            assert context.active_object == armature
            assert armature.mode == 'POSE'

            # Revert back to Pose mode
            if has_actives:
                events.event_update(None, context)

            # This causes it to run `rigid_body_bones.update` immediately rather than wait for the next tick
            utils.run_events()

        return {'FINISHED'}


class ListOperator(bpy.types.Operator):
    # TODO use UNDO_GROUPED ?
    bl_options = {'INTERNAL', 'UNDO'}

    is_alt: bpy.props.BoolProperty()

    @classmethod
    def poll(cls, context):
        return utils.is_pose_mode(context) and utils.has_active_bone(context)

    # TODO is there a better way of handling Alt ?
    def invoke(self, context, event):
        self.is_alt = event.alt
        return self.execute(context)

    def execute(self, context):
        if self.is_alt:
            for pose_bone in context.selected_pose_bones_from_active_object:
                bone = pose_bone.bone
                self.run(bone)

        else:
            armature = context.active_object
            bone = utils.get_active_bone(armature)
            self.run(bone)

        events.event_update(None, context)

        return {'FINISHED'}


class ListMoveOperator(ListOperator):
    def execute(self, context):
        if self.is_alt:
            for pose_bone in context.selected_pose_bones_from_active_object:
                bone = pose_bone.bone
                self.move(bone, self.direction)

        else:
            armature = context.active_object
            bone = utils.get_active_bone(armature)
            self.move(bone, self.direction)

        return {'FINISHED'}


def list_remove(data, list, active_name):
    old_index = getattr(data, active_name)

    list.remove(old_index)

    length = len(list)

    if old_index >= length:
        setattr(data, active_name, max(length - 1, 0))


def list_move(data, direction, list, active_name):
    old_index = getattr(data, active_name)

    if direction == 'UP':
        new_index = max(old_index - 1, 0)

    else:
        new_index = min(old_index + 1, len(list) - 1)

    if old_index != new_index:
        list.move(old_index, new_index)
        setattr(data, active_name, new_index)


class NewCompound(ListOperator):
    bl_idname = "rigid_body_bones.new_compound"
    bl_label = "Add new hitbox"
    bl_description = "Adds a new hitbox to the compound shape"

    def run(self, bone):
        data = bone.rigid_body_bones

        seen = set()

        for compound in data.compounds:
            seen.add(compound.name)

        data.active_compound_index = len(data.compounds)

        new_compound = data.compounds.add()

        properties.Compound.is_updating = True
        new_compound.name = utils.make_unique_name("Hitbox", seen)
        properties.Compound.is_updating = False


class RemoveCompound(ListOperator):
    bl_idname = "rigid_body_bones.remove_compound"
    bl_label = "Remove hitbox"
    bl_description = "Deletes the selected hitbox"

    def run(self, bone):
        data = bone.rigid_body_bones
        list_remove(data, data.compounds, "active_compound_index")


class MoveCompound(ListMoveOperator):
    bl_idname = "rigid_body_bones.move_compound"
    bl_label = "Move hitbox"
    bl_description = "Moves the selected hitbox up/down in the list"

    direction: bpy.props.EnumProperty(
        items=[
            ('UP', "", ""),
            ('DOWN', "", ""),
        ]
    )

    def move(self, bone, direction):
        data = bone.rigid_body_bones
        list_move(data, direction, data.compounds, "active_compound_index")


class NewJoint(ListOperator):
    bl_idname = "rigid_body_bones.new_joint"
    bl_label = "Add new joint"
    bl_description = "Adds a new joint to the bone"

    def run(self, bone):
        data = bone.rigid_body_bones

        seen = set()

        for joint in data.joints:
            seen.add(joint.name)

        data.active_joint_index = len(data.joints)

        new_joint = data.joints.add()

        properties.Joint.is_updating = True
        new_joint.name = utils.make_unique_name("Joint", seen)
        properties.Joint.is_updating = False


class RemoveJoint(ListOperator):
    bl_idname = "rigid_body_bones.remove_joint"
    bl_label = "Remove joint"
    bl_description = "Deletes the selected joint"

    def run(self, bone):
        data = bone.rigid_body_bones
        list_remove(data, data.joints, "active_joint_index")


class MoveJoint(ListMoveOperator):
    bl_idname = "rigid_body_bones.move_joint"
    bl_label = "Move joint"
    bl_description = "Moves the selected joint up/down in the list"

    direction: bpy.props.EnumProperty(
        items=[
            ('UP', "", ""),
            ('DOWN', "", ""),
        ]
    )

    def move(self, bone, direction):
        data = bone.rigid_body_bones
        list_move(data, direction, data.joints, "active_joint_index")
