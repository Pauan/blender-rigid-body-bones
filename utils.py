import bpy


def log(obj):
    from pprint import PrettyPrinter
    PrettyPrinter(indent = 4).pprint(obj)


class Selectable:
    def __init__(self, scene, data):
        self.scene = scene
        self.data = data

    def __enter__(self):
        self.scene.rigid_body_bones.collection.hide_select = False
        self.data.constraints.hide_select = False
        self.data.hitboxes.hide_select = False

    def __exit__(self, exc_type, exc_value, traceback):
        self.scene.rigid_body_bones.collection.hide_select = True
        self.data.constraints.hide_select = True
        self.data.hitboxes.hide_select = True
        return False


class Mode:
    def __init__(self, context, mode):
        self.context = context
        self.mode = mode
        self.old_mode = None

    def __enter__(self):
        # TODO is object correct ?
        self.old_mode = self.context.object.mode
        bpy.ops.object.mode_set(mode=self.mode)

    def __exit__(self, exc_type, exc_value, traceback):
        bpy.ops.object.mode_set(mode=self.old_mode)
        return False


#class Tab:
#    def __init__(self, context, name):
#        self.context = context
#        self.name = name
#        self.space_data = None
#
#    def __enter__(self):
#        self.space_data = self.context.space_data.context
#        self.context.space_data.context = self.name
#
#        for x in self.context.screen.areas:
#            if x.type == 'PROPERTIES':
#                area = x
#                break
#
#        local = self.context.copy()
#        local["area"] = x
#        return local
#
#    def __exit__(self, exc_type, exc_value, traceback):
#        self.context.space_data.context = self.space_data
#        return False


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


def select(context, objs):
    view_layer = context.view_layer

    for obj in view_layer.objects.selected:
        obj.select_set(False)

    for obj in objs:
        obj.select_set(True)

    view_layer.objects.active = objs[-1]


def parent(context, child, parent):
    select(context, [child, parent])
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)


def make_collection(name, parent):
    collection = bpy.data.collections.new(name)
    parent.children.link(collection)
    return collection


def remove_object(object):
    object.data.name = object.data.name + " [DELETED]"
    bpy.data.objects.remove(object)


def remove_collection(collection):
    for child in collection.objects:
        remove_object(child)

    bpy.data.collections.remove(collection)


def init_hitbox(object):
    object.hide_render = True
    object.show_in_front = True
    object.show_bounds = True
    object.display_type = 'BOUNDS'
    object.display_bounds_type = 'BOX'
    object.display.show_shadows = False
    object.rigid_body.collision_shape = 'BOX'


def make_empty_rigid_body(context, name, collection, location):
    mesh = bpy.data.meshes.new(name=name)
    body = bpy.data.objects.new(mesh.name, mesh)
    collection.objects.link(body)
    body.location = location
    select(context, [body])
    bpy.ops.rigidbody.object_add(type='PASSIVE')
    body.rigid_body.kinematic = True
    body.rigid_body.collision_collections[0] = False
    body.hide_select = True
    body.hide_viewport = True
    init_hitbox(body)
    return body


def make_hitbox(context, name, collection, location, rotation, dimensions, active):
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        calc_uvs=False,
        enter_editmode=False,
        align='WORLD',
        location=location,
        rotation=rotation,
    )

    context.active_object.scale = dimensions

    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # TODO is active_object correct ?
    body = context.active_object
    body.name = name
    collection.objects.link(body)
    context.collection.objects.unlink(body)

    if active:
        bpy.ops.rigidbody.object_add(type='ACTIVE')
    else:
        bpy.ops.rigidbody.object_add(type='PASSIVE')
        body.rigid_body.kinematic = True

    init_hitbox(body)
    return body
