import bpy
from . import utils
from .bones import (
    active_name, align_constraint, align_hitbox, blank_name, constraint_name,
    delete_parent, get_hitbox, hide_active_bone, is_bone_active, is_bone_enabled,
    make_active_hitbox, make_blank_rigid_body, make_constraint, make_empty_rigid_body,
    make_passive_hitbox, remove_active, remove_blank, remove_constraint,
    remove_passive, store_parent, update_constraint, update_hitbox_name,
    update_rigid_body, update_shape, passive_name
)


def show_collection(collection):
    collection.hide_select = False
    collection.hide_viewport = False


def root_collection(context):
    scene = context.scene

    collection = scene.rigid_body_bones.collection

    if not collection:
        collection = utils.make_collection("RigidBodyBones", scene.collection)
        collection.hide_render = True
        scene.rigid_body_bones.collection = collection

    show_collection(collection)

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

    show_collection(collection)

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

    show_collection(collection)

    return collection


def passives_collection(context, armature, top):
    collection = top.passives

    name = armature.data.name + " [Passives]"

    if not collection:
        collection = child_collection(context, armature, top, name)
        top.passives = collection

    else:
        collection.name = name

    show_collection(collection)

    return collection


def blanks_collection(context, armature, top):
    collection = top.blanks

    name = armature.data.name + " [Blanks]"

    if not collection:
        collection = child_collection(context, armature, top, name)
        top.blanks = collection

    else:
        collection.name = name

    show_collection(collection)

    return collection


def constraints_collection(context, armature, top):
    collection = top.constraints

    name = armature.data.name + " [Joints]"

    if not collection:
        collection = child_collection(context, armature, top, name)
        top.constraints = collection

    else:
        collection.name = name

    show_collection(collection)

    return collection


def remove_orphans(collection, exists):
    for object in collection.objects:
        if object.name not in exists:
            utils.remove_object(object)

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


def remove_pose_constraint(pose_bone):
    constraint = pose_bone.constraints.get("Rigid Body Bones [Child Of]")

    if constraint is not None:
        # TODO can this remove an index instead, to make it faster ?
        pose_bone.constraints.remove(constraint)


def update_pose_constraint(pose_bone):
    index = None
    found = None

    constraints = pose_bone.constraints

    # TODO can this be replaced with a collection method ?
    for i, constraint in enumerate(constraints):
        if constraint.name == "Rigid Body Bones [Child Of]":
            found = constraint
            index = i
            break

    data = pose_bone.bone.rigid_body_bones

    if is_bone_enabled(data) and is_bone_active(data):
        hitbox = data.active

        assert hitbox is not None

        if found is None:
            index = len(constraints)
            found = constraints.new(type='CHILD_OF')
            found.name = "Rigid Body Bones [Child Of]"

        # TODO verify that this properly sets the inverse
        # TODO reset the locrotscale ?
        found.set_inverse_pending = True

        assert index is not None

        if index != 0:
            constraints.move(index, 0)

        found.target = hitbox

    elif found is not None:
        # TODO can this remove an index instead, to make it faster ?
        constraints.remove(found)


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
            self.bones[data.name] = bone

            if top.enabled and not self.is_edit_mode and is_bone_enabled(data) and is_bone_active(data):
                self.remove_parents.add(bone.name)

            elif bone.parent is None:
                self.restore_parents[bone.name] = (data.parent, data.use_connect)


    def hide_active(self, top, bone, data):
        hide_active_bone(bone, data, top.enabled and top.hide_active_bones)


    def update_bone(self, context, armature, top, bone, data):
        # TODO figure out a way to not always remove blanks
        remove_blank(data)

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

                align_hitbox(data.active, bone, data)
                update_shape(data.active, type=data.collision_shape)
                update_rigid_body(data.active.rigid_body, data)

                align_constraint(data.constraint, bone)
                update_constraint(data.constraint.rigid_body_constraint, data)

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

                align_hitbox(data.passive, bone, data)
                update_shape(data.passive, type=data.collision_shape)
                update_rigid_body(data.passive.rigid_body, data)

                self.exists.add(data.passive.name)

        else:
            remove_active(data)
            remove_passive(data)
            remove_constraint(data)


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

        self.update_bone(context, armature, top, bone, data)

        self.fix_parents(armature, top, bone, data)

        self.hide_active(top, bone, data)


    def update_joint(self, context, armature, top, bone):
        data = bone.rigid_body_bones

        if is_bone_enabled(data) and is_bone_active(data):
            assert data.active is not None
            assert data.is_property_set("parent")

            constraint = data.constraint.rigid_body_constraint

            if data.parent == "":
                self.has_root_body = True
                constraint.object1 = make_root_body(context, armature, top)

            else:
                parent = self.bones[data.parent]
                parent_data = parent.rigid_body_bones

                if parent_data.error == "":
                    if is_bone_enabled(parent_data):
                        hitbox = get_hitbox(parent_data)
                        assert hitbox is not None
                        constraint.object1 = hitbox

                    else:
                        if not parent_data.blank:
                            collection = blanks_collection(context, armature, top)
                            parent_data.blank = make_blank_rigid_body(context, armature, collection, parent, parent_data)

                        else:
                            parent_data.blank.name = blank_name(parent)

                        self.exists.add(parent_data.blank.name)
                        constraint.object1 = parent_data.blank

                else:
                    constraint.object1 = None

            constraint.object2 = data.active


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


    def update_hitboxes(self, top, collection):
        show_collection(collection)

        collection.hide_viewport = top.hide_hitboxes


    # This cleans up any objects which are left behind after a bone
    # has been deleted.
    #
    # The calls to show_collection are needed in order to cause
    # Blender to update the rigid body simulation.
    def after_bones(self, context, armature, top):
        exists = self.exists


        if top.actives:
            if remove_orphans(top.actives, exists):
                top.property_unset("actives")

            else:
                self.update_hitboxes(top, top.actives)


        if top.passives:
            if remove_orphans(top.passives, exists):
                top.property_unset("passives")

            else:
                self.update_hitboxes(top, top.passives)


        if top.blanks:
            if remove_orphans(top.blanks, exists):
                top.property_unset("blanks")

            else:
                show_collection(top.blanks)
                top.blanks.hide_viewport = True


        if top.constraints:
            if remove_orphans(top.constraints, exists):
                top.property_unset("constraints")

            else:
                show_collection(top.constraints)
                top.constraints.hide_viewport = True


        if top.container:
            if remove_orphans(top.container, exists):
                top.property_unset("container")

            else:
                show_collection(top.container)


        scene = context.scene.rigid_body_bones

        if scene.collection:
            if utils.safe_remove_collection(scene.collection):
                scene.property_unset("collection")

            else:
                show_collection(scene.collection)
                scene.collection.hide_select = True


        # Not safe to access bones after changing mode
        self.bones = None


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


    def process_pose(self, context, armature, top):
        with utils.Selected(context):
            top.errors.clear()

            for bone in armature.data.bones:
                self.process_bone(context, armature, top, bone)

            self.update_constraints(context, armature, top)

            self.after_bones(context, armature, top)


    @classmethod
    def poll(cls, context):
        return utils.is_armature(context)


    def execute(self, context):
        armature = context.active_object
        top = armature.data.rigid_body_bones


        # Fast lookup for stored bone names -> new name
        self.names = {}

        # Fast lookup for stored bone names -> bone
        self.bones = {}

        # Data for bones which should have their parent restored
        self.restore_parents = {}

        # Names of bones which should have their parent removed
        self.remove_parents = set()

        # Whether to destructively delete/store the bone parent data
        self.delete_parents = False
        self.store_parents = False

        self.is_edit_mode = (top.mode == 'EDIT')


        if self.is_edit_mode or not top.enabled:
            if top.parents_stored:
                top.property_unset("parents_stored")
                self.delete_parents = True

        else:
            if not top.parents_stored:
                top.parents_stored = True
                self.store_parents = True


        if self.is_edit_mode:
            assert armature.mode == 'EDIT'

            # TODO if this triggers a mode_switch event then it can break everything
            with utils.Mode(context, 'POSE'):
                self.process_edit(context, armature, top)

            self.change_parents(context, armature)


        else:
            assert armature.mode != 'EDIT'


            # Names of objects which exist
            self.exists = set()

            # Names of objects for testing for duplicates
            self.duplicates = set()

            # Cache of whether a bone has an active parent or not
            self.active_cache = {}

            # Whether the root body should exist or not
            self.has_root_body = False


            self.process_pose(context, armature, top)

            # TODO if this triggers a mode_switch event then it can break everything
            with utils.Mode(context, 'EDIT'):
                self.change_parents(context, armature)


        return {'FINISHED'}
