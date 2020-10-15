# Rigid Body Bones

3D engines have support for bone physics, this can be used for a wide variety of things:

* Hair that reacts to motion, gravity, and wind.

* Antennas, wings, tails, etc.

* Breast / butt / muscle jiggle.

* Ragdoll physics.

* Simple cloth physics (faster than using real cloth physics, but not as realistic).

* Collision detection with the environment based on simple hitboxes.

* Exporting baked physics animations to game engines.

----

Blender can do all of that, however it is ***incredibly*** time consuming and tedious:

* You must manually create a cube for every bone and align them with the bones (in the correct position, size, and rotation).

   Whenever you change the bones you must manually realign the cubes.

* You must manually set all the proper settings (rigid body, wireframe, show on top, unselectable, etc.)

* You must manually create an empty for every cube (in the correct position and rotation) and set up constraints between the cubes.

   Whenever you change the bones you must manually realign the empties.

* You must create "blank" cubes which are parented to bones, and then attach other cubes to it.

   You must remember to manually disable collisions for these blank cubes.

* You must add `Child Of` bone constraints to the bones and use `Set Inverse`.

   You must do this again every time you change the bones.

* You must unparent/reparent the bones when changing between Edit and Pose mode.

If you try to do it by hand, you will waste many hours of time.

With this add-on, *all* of the above steps are automatically done for you. Rather than spending several *minutes* (per bone), it instead takes a couple *seconds*.

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

   You can also enable `Springs` to make the bone bouncy. And you can change the position of the hitbox in `Offset`.

   All of the rigid body options are available, the less commonly used options are in `Advanced`.


## Useful tips

* Do not put any objects into the `RigidBodyBones` collection, they will be deleted.

   The `RigidBodyBones` collection can only be used by this add-on.

* The `Rigid.Body.Bones.zip` file contains an `examples` folder which contains example `.blend` files.

* If you select multiple bones, you can hold down `Alt` when changing a setting and it will apply the change to all the selected bones.

* It is sometimes useful to change the `Advanced -> Physics -> Damping Translation` and `Damping Rotation` settings.

   This makes the bone move slower, like it is underwater:

   ![][usage06]

* You will probably need to adjust the `Properties -> Scene -> Rigid Body World -> Substeps Per Frame` and `Solver Iterations` settings.

   Increase them as high as you can, but decrease them if it causes weird glitches:

   ![][usage05]

* The `Armature` panel contains a few useful settings which apply to the entire armature.

   If things somehow get messed up, turn off the `Armature -> Enable rigid body physics` checkbox, and then turn it back on:

   ![][usage04]

* There is a `Pose -> Rigid Body` menu which contains a few useful operators:

   ![][usage03]

[usage01]: https://raw.githubusercontent.com/Pauan/blender-rigid-body-bones/master/Usage%2001.PNG
[usage02]: https://raw.githubusercontent.com/Pauan/blender-rigid-body-bones/master/Usage%2002.PNG
[usage03]: https://raw.githubusercontent.com/Pauan/blender-rigid-body-bones/master/Usage%2003.PNG
[usage04]: https://raw.githubusercontent.com/Pauan/blender-rigid-body-bones/master/Usage%2004.PNG
[usage05]: https://raw.githubusercontent.com/Pauan/blender-rigid-body-bones/master/Usage%2005.PNG
[usage06]: https://raw.githubusercontent.com/Pauan/blender-rigid-body-bones/master/Usage%2006.PNG


## For programmers

If you want to modify this add-on, follow these steps:

1. `git clone https://github.com/Pauan/blender-rigid-body-bones.git`

2. `cd blender-rigid-body-bones`

3. `blender --background --python install.py`

   This will install the add-on locally.

4. Now you can open Blender normally and the add-on will be installed.

5. When you make changes to the code, close Blender and then run `blender --background --python install.py` again.
