import bpy
import os
import zipfile

bpy.ops.preferences.addon_disable(module="Rigid Body Bones")

dir_path = os.path.dirname(os.path.realpath(__file__))

zip_path = os.path.join(dir_path, "Rigid Body Bones.zip")

with zipfile.ZipFile(zip_path, "w") as zip:
    for root, dirs, files in os.walk(os.path.join(dir_path, "Rigid Body Bones")):
        for file in files:
            file_path = os.path.join(root, file)
            zip.write(file_path, arcname=os.path.relpath(file_path, start=dir_path))

bpy.ops.preferences.addon_install(filepath=zip_path, overwrite=True)
bpy.ops.preferences.addon_enable(module="Rigid Body Bones")
bpy.ops.wm.save_userpref()
