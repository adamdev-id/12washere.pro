# Derpy Autodrive - Viewpoint Routes 0.5.3

Independent destination and trajectory guidance for Viewpoint's perspective
camera. Requires Build 42.22, Viewpoint 0.1.7 / API 1.0.0, Autodrive and
ZombieBuddy. No Workshop upload or external GPS service is used.

## Install and enable

1. Close Project Zomboid and run patcher 1.5.3 (Patch game), or copy this folder
   into your Zomboid/mods directory for manual installation.
2. Enable DerpyAutodriveViewpoint with DerpyAutodrive, Viewpoint and ZombieBuddy.
   The mod ID is unchanged. The patcher installs this folder at
   %USERPROFILE%/Zomboid/mods/DerpyAutodriveViewpoint.
3. Restart the game. Press Delete > Add-ons and enable Derpy Autodrive -
   Viewpoint Routes. Confirm the changed add-on if Viewpoint asks.
4. Set a destination and start Autodrive in the driver's seat for HUD guidance.
   Autodrive's Navigation line and Trajectory toggles control the two road
   overlays independently. The HUD works even when both road toggles are off.

## General Settings

Each camera independently selects Navigation HUD, Road Guidance, Both, or Off.

- First-person display defaults to Navigation HUD (no road route overlays).
- Third-person display defaults to Road Guidance (no screen HUD).
- Navigation HUD: on-screen next-turn arrow, distance, instruction and approach
  progress. It can be used in either camera mode while driving with Autodrive.
- Road Guidance: yellow destination route and green planned driving trajectory.
  Optional road-network/manual-road overlays also follow this display switch.
- Both shows HUD and road guidance; Off hides both in the selected camera.

## Destination Guidance - Yellow

Enabled: ON by default. Switch it off to hide the yellow destination, whether
it uses lines or arrows. This leaves the green trajectory and Navigation HUD
unchanged. The switch applies live and retains the appearance settings.

Destination line type: Line or Arrow (default Arrow). Independent controls:
line width, brightness, arrow size, arrow spacing, animation speed, and
pulse/fade. Width applies to Line; arrow controls apply to Arrow. Brightness
applies to either type. Arrows retain the yellow destination colour.

Match destination length to green trajectory remains on by default. It clips
the destination at the green endpoint through bends and loops, regardless of
whether the destination uses lines or arrows or the green overlay is visible.
Turning it off restores the longer nearby-route preview. This does not extend
the green trajectory; before a trajectory exists, normal preview is used.

## Trajectory Guidance - Green

Enabled: ON by default. Switch it off to hide the green trajectory, whether
it uses lines or arrows. This leaves the yellow destination and Navigation HUD
unchanged. The switch applies live and retains the appearance settings.

Trajectory line type: Line or Arrow (default Line). It has its OWN line width,
brightness, arrow size, arrow spacing, animation speed, and pulse/fade controls.
Changing destination settings does not change these settings, or vice versa.
The green overlay follows Autodrive's actual planned driving trajectory.

Both lines, both arrows, and either mixed combination are supported. Settings
apply live. Arrows follow turns and sample terrain at their centres and edges.
Their animation freezes when stationary or when Autodrive is not active.

## Navigation HUD

Arrow style: 3D Direction Arrow (default) or Turn Arrow. Animated arrow defaults
ON, animation speed defaults to 1x, and intensity defaults to 0.7. All controls
apply live. The text, distance and approach bar stay anchored while the icon
animates. Disable animation to remove the icon effects; Turn Arrow then becomes static.

- Turn Arrow: a bright light flows from the stem through the bend and arrowhead
  for straight, left, right and U-turn instructions. Arrival gently pulses the
  destination symbol. Turn-arrow look-away fading retains its existing setting.
- 3D Direction Arrow: a shaded extruded arrow points toward
  a point ahead along the driving route. Car Heading (default) shows direction
  relative to the car and stays steady when looking around. Player POV shows
  camera-relative direction, including camera pitch. Road elevation affects tilt. Angle changes follow
  the shortest rotation smoothly. Animation adds a subtle light pulse and bob;
  disabling animation still allows essential camera-direction tracking.
- 3D arrow: fade when looking away defaults OFF, independently of the Turn
  Arrow's fade setting, so the direction remains visible when turning your head.

Position, size and brightness stay independent of the road overlay settings.
Position presets: lower centre, lower left, lower right and upper centre. Both
HUD styles work in either camera when Navigation HUD or Both is selected.
They show the next turn and distance along Autodrive's full route even when road
guidance is hidden or shortened. No speed-limit, ETA or traffic service is used.

## Multiplayer and limits

Rendering is client side. The Lua adapter still needs loading on join,
normally through the server's Mods= entry or a suitable client loader.
With DoLuaChecksum=false a client can update while the server retains an older
copy under the same mod ID. Each player needs a local copy; the server does not
automatically download a non-Workshop mod to players.

Targets player one's normal perspective camera. Keep Panini projection off;
Minecraft/Iris pipelines and split-screen are not supported. Vanilla isometric
view and the map retain Autodrive's original rendering. Camera controls and
physics are unchanged. Coverage opacity preserves the host's blend state.

Automated tests cover all camera display choices, all four line/arrow pairings,
independent appearance changes, real game Lua, GPU occlusion and host loading.
The terrain projection previously verified in game is retained. The new
configuration still needs an actual driving-session check.

Version 0.4.1 fixes a 0.4.0 render-thread camera read that disabled rendering.
Camera visibility and settings are captured on the main thread, then consumed
as immutable snapshots by the render callback. Regression tests draw on a
separate thread and reject main-thread API access from that callback.


Version 0.5.1 previews the green planned trajectory through upcoming bends,
even when that overlay is hidden. When no useful trajectory exists, it uses
the destination route. The target no longer stops at the next corner.
3D arrow controls: Turn anticipation defaults to 25 m (5-60 m); Rotation
smoothness defaults to 0.3 s (0.05-1 s). More anticipation looks farther ahead;
more smoothness makes direction changes gentler. Both apply live. The 3D
Direction Arrow with Car Heading is the default, and 3D look-away fading stays off by default.


Version 0.5.2 adds 3D arrow: direction reference, with Car Heading as the default.
Car Heading uses the car's forward direction and position, so head/camera yaw,
pitch and position do not change arrow orientation. Planned-trajectory turn
anticipation, road-grade tilt and rotation smoothing continue to apply.
Player POV retains camera-relative orientation. The choice applies live under
Navigation HUD and only affects the 3D Direction Arrow. The overall default
is the 3D Direction Arrow with Car Heading; 3D look-away fading remains off by default.


Version 0.5.3 makes 3D Direction Arrow with Car Heading the default HUD style.
Arrow animation remains enabled and 3D look-away fading stays off. Turn Arrow
and Player POV remain available. New defaults apply to fresh/default settings;
previously saved player choices are preserved. Existing players can select
3D Direction Arrow and Car Heading once under Navigation HUD to switch.
