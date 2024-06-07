from __future__ import annotations

import time
from threading import Lock
from threading import Thread

from ahk import AHK

from ._utils import _get_all_joystick_values
from ._utils import get_logger

logger = get_logger()


class JoyListener:
    """
    Obtains state of joystick axes

    Intended to be used as a global listener to minimize the amount of AHK calls needed to support all triggers
    """

    def __init__(self, polling_frequency: int = 20):
        self.ahk = AHK()
        self._joystick_values: dict[str, dict[str, int | float]] = {}
        self._stopped = True
        self._axis_listener: Thread | None = None
        self._polling_frequency = polling_frequency
        self._lock = Lock()

    def get_joystick_axis_value(self, axis: str, joystick_index: int | str) -> float | int:
        joystick_values = self._joystick_values.get(str(joystick_index), None)
        if joystick_values is None:
            raise ValueError('Could not get value for joystick index {}'.format(joystick_index))
        axis_value = joystick_values.get(axis, None)
        if axis_value is None:
            raise ValueError(f"Joystick {joystick_index} has no value for axis {axis}")
        return axis_value

    def start(self) -> None:
        with self._lock:
            if self._stopped is True:
                assert self._axis_listener is None
                self._stopped = False
                self._axis_listener = Thread(target=self._listen)
                self._axis_listener.start()

    def stop(self) -> None:
        with self._lock:
            if self._stopped is False:
                self._stopped = True
                assert self._axis_listener is not None
                self._axis_listener.join()
                self._axis_listener = None

    def _listen(self) -> None:
        _get_all_joystick_values(self.ahk)
        time.sleep(0.1)
        while True:
            if self._stopped is True:
                break
            self._joystick_values = _get_all_joystick_values(self.ahk)
            time.sleep(1 / self._polling_frequency)
