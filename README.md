# Rigid Body Bones

![][simplegif]

![][marionettegif]

![][kizunagif]

[simplegif]: https://raw.githubusercontent.com/Pauan/blender-rigid-body-bones/master/Simple.gif
[kizunagif]: https://raw.githubusercontent.com/Pauan/blender-rigid-body-bones/master/Kizuna%20AI.gif
[marionettegif]: https://raw.githubusercontent.com/Pauan/blender-rigid-body-bones/master/Marionette.gif

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

* You must unparent/reparent the bones when switching between Pose and Object mode.

If you try to do it by hand, you will waste hundreds of hours of time.

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

6. When you're done making changes, switch into Object mode and then play the animation.


## Useful tips

* Blender often crashes, so save often! You should especially save right before playing an animation, since that's when most crashes happen.

* Do not put any objects into the `RigidBodyBones` collection, they will be deleted. The `RigidBodyBones` collection can only be used by this add-on.

* The `Rigid.Body.Bones.zip` file contains an `examples` folder which contains example `.blend` files.

* If a bone is `Active`, its child bones must also be `Active`, this is a limitation in Blender. So if the child is not `Active`, you must either make the child `Active`, or you must change it to a non-`Active` parent.

   However, you can use `Constraints` to create joints between any bones (even if they aren't in a parent-child relationship). This works with both `Active` and non-`Active` bones.

* If you select multiple bones, you can hold down `Alt` when changing a setting and it will apply the setting to all the selected bones.

* It is sometimes useful to change the `Advanced -> Physics -> Damping Translation` and `Damping Rotation` settings.

   This makes the bone move slower, like it is underwater:

   ![][usage06]

* Inside of the `Advanced -> Collision Layers` panel you can assign the bone to a different layer, which will cause it to only collide with other objects in the same layer.

   You can also assign the bone to multiple layers by holding down `Shift`. Or you can hold down `Shift` to remove it from all the layers, which means it will never collide with anything. This is useful if you want the bone to be affected by motion, gravity, and wind, but not collisions.

* You will probably need to change the `Properties -> Scene -> Rigid Body World -> Substeps Per Frame` and `Solver Iterations` settings.

   Increasing them can make the simulation more realistic, but it can also cause weird glitches, so sometimes you need to lower them.

   The `Substeps Per Frame` option changes how springs behave, so be very careful when changing it:

   ![][usage05]

* The `Armature` panel contains a few useful settings which apply to the entire armature.

   If things somehow get messed up, turn off the `Armature -> Enable rigid body physics` checkbox, and then turn it back on:

   ![][usage04]

* There is a `Pose -> Rigid Body` menu which contains a few useful operators:

   ![][usage03]

   * `Calculate Mass` will change the Mass of the selected bones based on their size and material type.

   * `Copy from Active` will copy all the rigid body settings from the active bone to the other selected bones.

   * `Bake to Keyframes` will bake the selected bones into keyframes, so they can be used in other engines.

* There is a `Constraints` panel which allows you to create joints between a bone and another rigid body (or another bone):

   ![][usage07]

   This can be used for advanced features like IK, or circular dependencies. See the `Constraints.blend`, `IK.blend`, and `Marionette.blend` examples.

[usage01]: https://raw.githubusercontent.com/Pauan/blender-rigid-body-bones/master/Usage%2001.PNG
[usage02]: https://raw.githubusercontent.com/Pauan/blender-rigid-body-bones/master/Usage%2002.PNG
[usage03]: https://raw.githubusercontent.com/Pauan/blender-rigid-body-bones/master/Usage%2003.PNG
[usage04]: https://raw.githubusercontent.com/Pauan/blender-rigid-body-bones/master/Usage%2004.PNG
[usage05]: https://raw.githubusercontent.com/Pauan/blender-rigid-body-bones/master/Usage%2005.PNG
[usage06]: https://raw.githubusercontent.com/Pauan/blender-rigid-body-bones/master/Usage%2006.PNG
[usage07]: https://raw.githubusercontent.com/Pauan/blender-rigid-body-bones/master/Usage%2007.PNG


## For programmers

If you want to modify this add-on, follow these steps:

1. `git clone https://github.com/Pauan/blender-rigid-body-bones.git`

2. `cd blender-rigid-body-bones`

3. `blender --background --python install.py`

   This will install the add-on locally.

4. Now you can open Blender normally and the add-on will be installed.

5. When you make changes to the code, close Blender and then run `blender --background --python install.py` again.
