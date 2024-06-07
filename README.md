# voice-commander

An application for defining macros and triggers using voice commands and hotkeys. Inspired by the popular commercial
software [VoiceAttack](https://www.voiceattack.com/).

**Requires Python 3.12+**

This is a major rewrite of a pre-existing project. If you're looking for the older version of this software, see the [pre-rewrite tag](https://github.com/spyoungtech/voice-commander/releases/tag/pre-rewrite) (or the now-yanked `0.0.1a` version on PyPI).

## Installation

### Via pip

To install, ideally in a virtualenv, use `pip`:

```bash
pip install voice-commander
```

This software also requires that you have AutoHotkey installed. You can either install AutoHotkey to a default location or, alternatively, install the `ahk-binary` package in your virtualenv:

```bash
pip install ahk-binary
```

### Windows executable

Coming soon.


## Usage

The basic primitives include **profiles**, **triggers**, **actions**, and **conditions**.

- An **action** defines the underlying action is to be performed upon triggering, such as pressing a keyboard key, playing a sound, opening a program, etc.
- A **trigger** is used to trigger an associated set of _actions_. For example, speaking a voice activation phrase, pressing a hotkey combination (like win+n), or similar. A trigger may trigger any number of _actions_.
- A **condition** is used to conditionally control execution of a trigger or any specific action within a trigger. For example, you may only want an action to perform a key press to actually activate when a specific window (like a game) is open/focused. A trigger may be attached to a _trigger_ or an _action_.
- A **profile** is a collection of triggers (and their associated actions/conditions) which can be activated/deactivated together for convenience.

### Basic example

You can define and run profiles in Python code.


```python
from voice_commander.profile import Profile
from voice_commander.triggers import *
from voice_commander.actions import *

profile = Profile("myprofile")

# triggers when any of these phrases are spoken
# You can add as many phrases as you want
trigger = VoiceTrigger('lower landing gear', 'retract landing gear')
# When the above trigger activates from a voice command, presses the "l" button (bound in-game to landing gear toggle)
action = AHKPressAction("l")
trigger.add_action(action)  # you can add multiple actions if you want. Here, we're just adding one action.
profile.add_trigger(trigger)

profile.run()
```

You can also serialize/deserialize profiles to/from JSON.

```python
# save the profile to the present working directory
profile.save_json(dirname='.', filename='myprofile.vcp.json')  # "vcp" means "Voice Commander Profile"
```

```python
from voice_commander.profile import load_profile
# easily load profiles from JSON
profile = load_profile('./myprofile.vcp.json')
profile.run()
```

You may also edit and run JSON files which represent the complete profile directly. The above example produces a JSON file substantially as follows:

```json
{
    "configuration": {
        "profile_name": "myprofile",
        "schema_version": "0",
        "triggers": [
            {
                "trigger_type": "voice_commander.triggers.VoiceTrigger",
                "trigger_config": {
                    "*trigger_phrases": [
                        "lower landing gear",
                        "retract landing gear"
                    ]
                },
                "actions": [
                    {
                        "action_type": "voice_commander.actions.AHKPressAction",
                        "action_config": {
                            "key": "l"
                        }
                    }
                ]
            }
        ]
    }
}
```

JSON5 is also supported. More formats may be supported in the future.

You can run profiles from these files directly from the command line:

```bash
python -m voice_commander run-profile --profile-file ./myprofile.vcp.json
```


Full documentation coming soon.

## Extending voice commander

voice-commander is being built with extension in mind. We don't have much to share here just yet, but you can check out
the [voice-commander-elite](https://github.com/spyoungtech/voice-commander-elite) project, which is an extension intended
to provide special functionality for players of the game _Elite Dangerous_. It is currently being used as a guinea pig
for future extensions. `voice-commander-elite` may also give you ideas of the kinds of other extensions that may be possible.

## Status

This project is in early stages of development, but is ready for use. Efforts will be made to keep existing
profile schemas compatible with (or convertable to) any future schema versions, though the Python API is likely to have
some breaking changes, at least while we're getting off the ground.


### Current Limitations

Some of the notable limitations of this software are as follows:

- Can only read `X`, `Y`, `Z`, `R`, `U`, and `V` axes of Joystick controllers. Some special axes (such as the `Dial` of certain throttle controllers) cannot be used as a trigger
- While controller/joystick inputs can be used for _triggering_ macros, we do not yet support _sending_ joystick or controller inputs in macros. You will, therefore, probably want to make sure you have keyboard bindings available for in-game actions.
- Only wave audio files (`.wav`) are currently supported for playing sounds (and only supported on Windows)
- Does not yet support XInput devices (e.g., Xbox One controllers) for triggers or sending
- Requires `ahk` (and therefore also AutoHotkey, and Windows) for most meaningful functionality. Future versions will support Linux-friendly alternatives
- Input interception (preventing the active program from receiving the input) is not supported for joystick/controller inputs.
