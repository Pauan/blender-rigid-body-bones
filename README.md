# Rigid Body Bones

3D engines have support for bone physics, this can be used for a wide variety of things:

* Animated hair that reacts to gravity and wind

* Ragdoll physics

* Simple cloth physics (faster than using real cloth physics, but not as realistic)

* Breast / butt / muscle jiggle

* Collision detection based on simple hitboxes

Blender can do all of that, however it is ***incredibly*** time consuming and tedious.

This add-on makes it super easy. Rather than spending several minutes setting up physics for each bone, it instead takes a couple seconds.

And best of all, this add-on creates normal Blender rigid bodies, so the performance is excellent, and it continues to work perfectly even after disabling the add-on. Which means you can send the `.blend` file to somebody else and they can use it without needing the add-on installed.

## Installation

You must have Blender 2.91.0 or higher.

1. Go to the [Releases page](https://github.com/Pauan/blender-rigid-body-bones/releases) and download the latest release (as a .zip file).

2. In Blender, go to `Edit -> Preferences...`

3. In the Add-ons tab, click the `Install...` button.

4. Select the .zip file and click `Install Add-on`.

5. Enable the checkbox to the left of `Physics: Rigid Body Bones`.

6. Save your preferences.

## How to use

1. Select an Armature object:

   ![](usage01)

2. Go into Pose mode.

3. In the sidebar (keyboard shortcut `N`) open the `Rigid Body Bones` tab:

   ![](usage02)

4. Select the bone that you want physics for.

5. Click the `Rigid Body` checkbox.

6. Now you can change the settings as much as you want.

   By default the hitbox will move with the bone.

   If you instead want the hitbox to cause the bone to move, change the `Type` to `Active`. You will probably want to change the `Limits` as well.

   You can also enable `Springs` to make the bones bouncy.

   All of the rigid body options are available, the less commonly used options are in `Advanced`.

The .zip file also contains an `examples/Simple.blend` file which contains a simple example.

[usage01]: https://raw.githubusercontent.com/Pauan/blender-rigid-body-bones/master/Usage%2001.PNG
[usage02]: https://raw.githubusercontent.com/Pauan/blender-rigid-body-bones/master/Usage%2002.PNG
