import subprocess
import keyboard
from threading import Lock

action_lock = Lock()

def default_ex_handler(action, exc):
    print('failed to execute action "{}".\n{}'.format(action, exc))


class Action(object):
    def __init__(self, func, ex_handler=None, concurrent=False):
        if ex_handler is None:
            ex_handler = default_ex_handler
        assert callable(func)
        assert callable(ex_handler)
        self.concurrent = concurrent
        self.ex_handler = ex_handler
        self.func = func

    @classmethod
    def from_recording(cls, speed_factor=1.0, ex_handler=None, **record_args):
        events = keyboard.record(**record_args)
        def play_macro():
            keyboard.play(events, speed_factor=speed_factor)
        return cls(play_macro, ex_handler=ex_handler)

    def __call__(self):
        try:
            if self.concurrent:
                return self.func()
            else:
                with action_lock:
                    return self.func()
        except Exception as e:
            return self.ex_handler(self.func, e)


def press_key(key, ex_handler=None):
    def _press_key():
        keyboard.write(key)
    return Action(_press_key, ex_handler=ex_handler)


def run_command(cmd, timeout=3, ex_handler=None, **kwargs):
    def _run_command():
        subprocess.run(cmd, timeout=timeout, **kwargs)
    return Action(_run_command, ex_handler=ex_handler)
