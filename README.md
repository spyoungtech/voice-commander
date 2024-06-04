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

_Profiles_ defines a group of triggers respective associated actions that are to be activated at any given time.

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

You may also edit JSON files directly. The above example produces the following JSON file:

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

You can also run profiles directly from the command line:

```bash
python -m voice_commander run_profile --filename="./myprofile.vcp.json"
```



Full documentation coming soon.

## Status

This project is in early stages of development. While it is very much usable in its current state and some efforts will
be made to avoid breaking changes, some breaking changes are likely to occur.


### Current Limitations

Some of the notable limitations of this software are as follows:

- Can only read `X`, `Y`, `Z`, `R`, `U`, and `V` axes of Joystick controllers. Some special axes (such as the `Dial` of certain throttle controllers) cannot be used as a trigger
- While controller/joystick inputs can be used for _triggering_ macros, we do not yet support _sending_ joystick or controller inputs in macros. You will, therefore, probably want to make sure you have keyboard bindings available for in-game actions.
- Only wave audio files (`.wav`) are currently supported for playing sounds (and only supported on Windows)
- Does not yet support XInput devices (e.g., Xbox One controllers) for triggers or sending
- Requires `ahk` (and therefore also AutoHotkey, and Windows) for most meaningful functionality. Future versions will support Linux-friendly alternatives
- Input interception (preventing the active program from receiving the input) is not supported for joystick/controller inputs.
