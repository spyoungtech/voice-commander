# Voice-Commander

Cross-platform voice-activation hooks and keyboard macros. Largely inspired by the popular software "Voice Attack"


## Status

This project is currently a work-in-progress and is minimally functional.

## Goals

- Provide ability to execute predefined actions (e.g. open a program, execute macros, etc.) by voice-activated command
- Provide an interface to add and edit commands and keywords
- Ability to import and export commands (e.g. to a json file)
- other stuff


## Installation

For now, you can install via pip+git. For example

```
pip install git+https://github.com/spyoungtech/voice-commander.git
```

In the future, we'll be releasing on PyPI as well as executables for Windows, Mac OS, and Linux.


## Running the gui app

After installing, simply run

```
python -m voice_commander
```

The GUI application should start. There are two options in the menu: 'add command' and 'run'. Other options are not yet implemented

Right now, you can add command keyword phrases as text and record corresponding actions as keyboard macros.

When you select run, it will be constantly listening for the phrases.

By default, uses a Google API for speech-to-text conversion. Can support any other engine supported by [SpeechRecognition](https://pypi.org/project/SpeechRecognition/).


## TODO

- [x] record keyboard actions to be executed on-command
- [x] ability for users to define trigger phrases and match voice to commands
- [ ] make actions able to be serialized/deserialized (ideally to json)
- [ ] more predefined actions; e.g. start a program, mouse control, etc.
- [ ] other action callbacks -- e.g. play a audio file in response to voice command
- [ ] command editor
- [ ] ???