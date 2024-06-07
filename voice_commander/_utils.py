from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any
from typing import Union

from ahk import AHK
from ahk.directives import NoTrayIcon


_global_ahk: Union[None, AHK[Any]] = None
_global_listener: Union[None, Listener] = None
_global_joy_listener: Union[None, JoyListener] = None


def get_logger() -> logging.Logger:
    return logging.getLogger('voice_commander')


def get_ahk(use_global: bool = True) -> AHK[Any]:
    global _global_ahk
    if use_global:
        if _global_ahk is None:
            _global_ahk = AHK(directives=[NoTrayIcon(apply_to_hotkeys_process=True)])
        return _global_ahk
    return AHK(directives=[NoTrayIcon(apply_to_hotkeys_process=True)])


def get_listener() -> Listener:
    global _global_listener
    if _global_listener is None:
        _global_listener = Listener()
    return _global_listener


def get_joy_listener() -> JoyListener:
    global _global_joy_listener
    if _global_joy_listener is None:
        _global_joy_listener = JoyListener()
    return _global_joy_listener


def get_joystick_button() -> tuple[str, str]:
    """
    Wait for any joystick button to be pressed, return a tuple the AHK index of the
     joystick and the button's name (as strings)

    NOTE: POV hats do not count as buttons. Use get_joystick_axis_or_pov for waiting on POV hat inputs.
    """
    ahk = get_ahk(use_global=False)
    import queue

    q: queue.Queue[tuple[str | int, int]] = queue.Queue()

    def make_callback(index: str | int, button: int) -> Callable[..., None]:
        def inner() -> None:
            q.put((index, button))

        return inner

    for button in range(1, 33):
        ahk.add_hotkey(f'Joy{button}', callback=make_callback('', button))

    for joystick in range(1, 17):
        for button in range(1, 33):
            ahk.add_hotkey(f'{joystick}Joy{button}', callback=make_callback(joystick, button))
    try:
        ahk.start_hotkeys()
        index, button = q.get()
        return str(index), str(button)
    finally:
        ahk.stop_hotkeys()
        del ahk


def _get_all_joystick_values(ahk: AHK[Any]) -> dict[str, dict[str, int | float]]:
    joystick_initial_values = {}
    joystick: str | int
    for joystick in range(0, 17):
        supported_axes = 'XY'
        if joystick == 0:
            joystick = ''
        info_resp = ahk.key_state(f'{joystick}JoyInfo')
        if not info_resp:
            continue
        assert isinstance(info_resp, str)
        for additional_axis in 'ZRUV':
            if additional_axis in info_resp:
                supported_axes += additional_axis
        initial_values = {}
        for axis in supported_axes:
            initial_value = ahk.key_state(f'{joystick}Joy{axis}')
            if isinstance(initial_value, (int, float)):
                initial_values[axis] = initial_value
            else:
                continue
        if 'P' in info_resp:
            pov_value = ahk.key_state(f'{joystick}JoyPOV')
            if isinstance(pov_value, (int, float)):
                initial_values['POV'] = pov_value
        joystick_initial_values[str(joystick)] = initial_values
    return joystick_initial_values


def get_joystick_axis_or_pov() -> tuple[str, str, int | float]:
    ahk = get_ahk(use_global=False)
    # XXX: for some reason, we have to prime this, as some axes report 100 on first poll always
    _get_all_joystick_values(ahk)
    time.sleep(0.1)

    joystick_initial_values = _get_all_joystick_values(ahk)
    while True:
        current_values = _get_all_joystick_values(ahk)
        for joystick, joystick_values in current_values.items():
            initial_values = joystick_initial_values.get(joystick)
            if not initial_values:
                continue
            for axis in joystick_values:
                current_value = joystick_values[axis]
                initial_value = initial_values[axis]
                if abs(current_value - initial_value) > 30 or (axis == 'POV' and current_value != initial_value):
                    return joystick, axis, current_value
        time.sleep(0.1)


from .voice_listener import Listener  # noqa
from .joy_listener import JoyListener  # noqa
