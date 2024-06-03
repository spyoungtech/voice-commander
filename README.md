# voice-commander

An application for defining macros and triggers using voice commands and hotkeys. Inspired by the popular commercial
software [VoiceAttack](https://www.voiceattack.com/).

**Requires Python 3.12+**

This is a major rewrite of a pre-existing project. If you're looking for the older version of this software, see the [pre-rewrite tag](https://github.com/spyoungtech/voice-commander/releases/tag/pre-rewrite) (or the now-yanked `0.0.1a` version on PyPI).

Installation, ideally in a virtualenv:

```bash
pip install voice-commander
```

Also requires that you have AutoHotkey installed. You can either install AutoHotkey to a default location or, alternatively, install the `ahk-binary` package in your virtualenv:

```bash
pip install ahk-binary
```


## Status

This project is in early stages of development. While it is very much usable in its current state and some efforts will
be made to avoid breaking changes, some breaking changes are likely to occur.

Full documentation coming soon.

### Current Limitations

Some of the notable limitations of this software are as follows:

- Can only read `X`, `Y`, `Z`, `R`, `U`, and `V` axes of Joystick controllers. Some special axes (such as the `Dial` of certain throttle controllers) cannot be used as a trigger
- While controller/joystick inputs can be used for _triggering_ macros, we do not yet support _sending_ joystick or controller inputs in macros. You will, therefore, probably want to make sure you have keyboard bindings available for in-game actions.
- Only wave audio files (`.wav`) are currently supported for playing sounds (and only supported on Windows)
- Does not yet support XInput devices (e.g., Xbox One controllers) for triggers or sending
- Requires `ahk` (and therefore also AutoHotkey, and Windows) for most meaningful functionality. Future versions will support Linux-friendly alternatives
- Input interception (preventing the active program from receiving the input) is not supported for joystick/controller inputs.
