# Rigid Body Bones

3D engines have support for bone physics, this can be used for a wide variety of things:

* Animated hair that reacts to gravity and wind.

* Ragdoll physics.

* Simple cloth physics (faster than using real cloth physics, but not as realistic).

* Breast / butt / muscle jiggle.

* Collision detection based on simple hitboxes.

Blender can do all of that, however it is ***incredibly*** time consuming and tedious. And there are a lot of problems that you need to watch out for. If you try to do it by hand, you will waste many hours of time.

With this add-on, rather than spending several *minutes* (per bone), it instead takes a couple *seconds*, and all of the tricky stuff is handled automatically for you.

And best of all, this add-on creates normal Blender rigid bodies, so the performance is excellent, and it continues to work perfectly even after disabling the add-on.

That means you can send the `.blend` file to somebody else and they can use it without needing the add-on installed.

## Installation

You must have Blender 2.91.0 or higher.

1. Go to the [Releases page](https://github.com/Pauan/blender-rigid-body-bones/releases) and download the most recent `Rigid.Body.Bones.zip` file.

2. In Blender, go to `Edit -> Preferences...`

3. In the `Add-ons` tab, click the `Install...` button.

4. Select the `Rigid.Body.Bones.zip` file and click `Install Add-on`.

5. Enable the checkbox to the left of `Physics: Rigid Body Bones`.

6. Save your preferences.

## How to use

1. Select an Armature object:

   ![][usage01]

2. Go into Pose mode.

3. In the sidebar (keyboard shortcut `N`) open the `Rigid Body Bones` tab:

   ![][usage02]

4. Select the bone that you want physics for.

5. Click the `Rigid Body` checkbox to enable physics.

   If you want the bone to move automatically, change the `Type` to `Active`. You will probably want to change the `Limits` as well.

   You can also enable `Springs` to make the bone bouncy.

   All of the rigid body options are available, the less commonly used options are in `Advanced`.

The `Rigid.Body.Bones.zip` file also contains an `examples` folder which contains example `.blend` files.

[usage01]: https://raw.githubusercontent.com/Pauan/blender-rigid-body-bones/master/Usage%2001.PNG
[usage02]: https://raw.githubusercontent.com/Pauan/blender-rigid-body-bones/master/Usage%2002.PNG


## For programmers

If you want to modify this add-on, follow these steps:

1. `git clone https://github.com/Pauan/blender-rigid-body-bones.git`

2. `cd blender-rigid-body-bones`

3. `blender --background --python install.py`

   This will install the add-on locally.

4. Now you can open Blender normally and the add-on will be installed.

5. When you make changes to the code, close Blender and then run `blender --background --python install.py` again.
