import re
import sys
import time
import bpy
import bmesh
from math import radians
from mathutils import Vector, Euler, Matrix


DEBUG = False

def log(obj):
    from pprint import PrettyPrinter
    PrettyPrinter(indent = 4).pprint(obj)

def error(message):
    print(message, file=sys.stderr)

def debug(message):
    global DEBUG

    if DEBUG:
        print(message)

def print_time(time_start, time_end):
    debug("  TIME: %.10f ms" % ((time_end - time_start) * 1000.0))


def timed(name):
    def decorator(f):
        def update(*args):
            debug("EVENT {} {{".format(name))

            time_start = time.time()

            f(*args)

            time_end = time.time()
            print_time(time_start, time_end)

            debug("}")

        return update
    return decorator


class Mode:
    def __init__(self, context, object, mode):
        self.context = context
        self.object = object
        self.mode = mode
        self.old_mode = None

    def __enter__(self):
        self.old_mode = self.object.mode
        select_active(self.context, self.object)
        assert self.context.active_object is self.object
        bpy.ops.object.mode_set(mode=self.mode)

    def __exit__(self, exc_type, exc_value, traceback):
        if self.old_mode is not None:
            select_active(self.context, self.object)
            assert self.context.active_object is self.object
            bpy.ops.object.mode_set(mode=self.old_mode)
        return False


class Selected:
    def __init__(self, context):
        self.context = context
        self.view_layer = None
        self.selected = None
        self.active = None

    def __enter__(self):
        self.view_layer = self.context.view_layer
        self.selected = list(self.view_layer.objects.selected)
        self.active = self.view_layer.objects.active

    def __exit__(self, exc_type, exc_value, traceback):
        for obj in self.view_layer.objects.selected:
            obj.select_set(False)

        for obj in self.selected:
            obj.select_set(True)

        self.view_layer.objects.active = self.active

        return False


# This is needed in order to select the objects.
class Selectable:
    def __init__(self, context):
        self.context = context

    def __enter__(self):
        scene = self.context.scene.rigid_body_bones

        if scene.collection:
            scene.collection.hide_select = False

    def __exit__(self, exc_type, exc_value, traceback):
        scene = self.context.scene.rigid_body_bones

        if scene.collection:
            scene.collection.hide_select = True

        return False


class Viewable:
    def __init__(self, object):
        self.object = object
        self.hidden = None

    def __enter__(self):
        self.hidden = self.object.hide_viewport
        self.object.hide_viewport = False

    def __exit__(self, exc_type, exc_value, traceback):
        if self.hidden is not None:
            self.object.hide_viewport = self.hidden

        return False


# Temporarily resets the frame to the starting simulation frame
class AnimationFrame:
    def __init__(self, context):
        self.scene = context.scene
        self.old_frame = None

    def __enter__(self):
        scene = self.scene

        if scene.rigidbody_world:
            self.old_frame = scene.frame_current
            scene.frame_set(scene.rigidbody_world.point_cache.frame_start)

    def __exit__(self, exc_type, exc_value, traceback):
        if self.old_frame is not None:
            self.scene.frame_set(self.old_frame)

        return False


def get_active_pose_bone(context):
    return context.active_pose_bone

def get_active_bone(armature):
    return armature.data.bones.active

def has_active_bone(context):
    return is_armature(context) and (get_active_bone(context.active_object) is not None)

def is_pose_mode(context):
    # TODO use the mode of the active_object ?
    return (context.mode == 'POSE')

def is_armature(context):
    return (
        (context.active_object is not None) and
        (context.active_object.type == 'ARMATURE')
    )

def is_armature_enabled(context):
    return context.active_object.data.rigid_body_bones.enabled


def deselect_all(context):
    for obj in context.view_layer.objects.selected:
        obj.select_set(False)

def select_active(context, obj):
    obj.select_set(True)
    context.view_layer.objects.active = obj


def set_parent(child, parent):
    child.parent = parent
    child.parent_type = 'OBJECT'


def set_bone_parent(child, parent, bone):
    child.parent = parent
    child.parent_type = 'BONE'
    child.parent_bone = bone


def make_collection(name, parent):
    collection = bpy.data.collections.new(name)
    parent.children.link(collection)
    return collection


def remove_object(object):
    data = object.data

    bpy.data.objects.remove(object)

    if data is not None:
        bpy.data.meshes.remove(data)


def safe_remove_collection(collection):
    if len(collection.children) == 0 and len(collection.objects) == 0:
        bpy.data.collections.remove(collection)
        return True

    else:
        return False


def remove_collection_recursive(collection):
    for child in collection.objects:
        remove_object(child)

    for sub in collection.children:
        remove_collection_recursive(sub)

    assert len(collection.children) == 0 and len(collection.objects) == 0

    bpy.data.collections.remove(collection)


def set_mesh_cube(mesh, dimensions):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, calc_uvs=False)
    bmesh.ops.scale(bm, vec=dimensions, verts=bm.verts)
    bm.to_mesh(mesh)
    bm.free()


def clear_mesh(mesh):
    # TODO when undoing, Blender will sometimes cause empty meshes to have big bounding boxes
    #      if that happens, change to use this implementation instead
    #set_mesh_cube(mesh, (0.0, 0.0, 0.0))

    # TODO is there a faster way ?
    bm = bmesh.new()
    bm.to_mesh(mesh)
    bm.free()


def make_mesh_object(name, collection):
    mesh = bpy.data.meshes.new(name=name)
    cube = bpy.data.objects.new(name, mesh)
    collection.objects.link(cube)
    return cube


re_strip = re.compile(r"\.[0-9]+$")

# TODO is there a builtin utility for this ?
def strip_name_suffix(name):
    return re_strip.sub("", name)


# TODO is there a builtin utility for this ?
def make_unique_name(prefix, seen):
    index = 1

    while True:
        # TODO respect the 64 character name limit
        new_name = "{}.{:0>3}".format(prefix, index)

        if new_name in seen:
            index += 1

        else:
            return new_name


# Event system
EVENTS = {}


def get_dirty(armature, scene):
    # If the dirty already exists then return it
    for dirty in scene.dirties:
        # TODO better cherk for this ?
        if dirty.armature and dirty.armature.name == armature.name:
            return dirty

    # If it doesn't exist, create a new one
    dirty = scene.dirties.add()
    dirty.armature = armature
    return dirty


# This is used to run the event during the next main event tick.
#
# It also causes multiple update operations to be batched
# into one operation, which makes Alt updating work correctly.
def mark_dirty(context, name):
    scene = context.scene.rigid_body_bones

    if is_armature(context):
        armature = context.active_object

        dirty = get_dirty(armature, scene)
        setattr(dirty, name, True)

        debug("DIRTY {}".format(name))

    if len(scene.dirties) > 0:
        if not bpy.app.timers.is_registered(run_events):
            bpy.app.timers.register(run_events)


@timed("run_events")
def run_events():
    context = bpy.context
    scene = context.scene.rigid_body_bones

    for dirty in scene.dirties:
        armature = dirty.armature

        if armature:
            for (name, f) in EVENTS.items():
                if getattr(dirty, name):
                    f(context, dirty, armature)

    scene.dirties.clear()


def event(name):
    def decorator(f):
        def run(context, dirty, armature):
            debug("EVENT {} {{".format(name))

            time_start = time.time()

            f(context, dirty, armature)

            time_end = time.time()
            print_time(time_start, time_end)

            debug("}")

        EVENTS[name] = run

        def update(self, context):
            mark_dirty(context, name)

        return update
    return decorator


def if_armature_enabled(f):
    def run(context, dirty, armature):
        # event_update already updates everything, so we don't need to run this too
        if not dirty.update:
            top = armature.data.rigid_body_bones

            if top.enabled and armature.mode != 'EDIT':
                f(context, dirty, armature, top)

    return run


def if_armature_pose(f):
    def run(context, dirty, armature):
        # event_update already updates everything, so we don't need to run this too
        if not dirty.update:
            top = armature.data.rigid_body_bones

            if top.enabled and armature.mode == 'POSE':
                f(context, dirty, armature, top)

    return run


def unregister():
    if bpy.app.timers.is_registered(run_events):
        bpy.app.timers.unregister(run_events)
