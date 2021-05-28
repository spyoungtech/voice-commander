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

You can install via `pip`

```
pip install voice-commander
```

Additionally, check the github releases for binary executables. Right now, that's just Windowze. In the future, we will also provide executables for multiple platforms.


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

- [x] ~~record keyboard actions to be executed on-command~~
- [x] ~~ability for users to define trigger phrases and match voice to commands~~
- [x] ~~make actions able to be serialized/deserialized~~ (ideally to json)
- [ ] Ability to define keyboard macros without need to record input
- [ ] Ability to provide macro playback speed (for the whole macro)
- [ ] more predefined actions; e.g. start a program, mouse control, etc.
- [ ] other action callbacks -- e.g. play a audio file in response to voice command
- [ ] command editor
  - [ ] Ability to edit trigger word
  - [ ] Ability to edit playback speed per individual macro action
- [ ] binaries for additional platforms (Mac OS/Linux)
- [ ] ???