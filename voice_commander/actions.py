import subprocess
import keyboard
from threading import Lock

action_lock = Lock()

def default_ex_handler(action, exc):
    print('failed to execute action "{}".\n{}'.format(action, exc))


class Action(object):
    def __init__(self, func, ex_handler=None, args=None, kwargs=None, concurrent=False):
        if ex_handler is None:
            ex_handler = default_ex_handler
        assert callable(func)
        assert callable(ex_handler)
        self.concurrent = concurrent
        self.ex_handler = ex_handler
        self.func = func
        self.args = args or list()
        self.kwargs = kwargs or dict()

    @classmethod
    def from_recording(cls, speed_factor=1.0, ex_handler=None, **record_args):
        events = keyboard.record(**record_args)
        kwargs = {'events': events, 'speed_factor': speed_factor}
        return cls(play_macro, ex_handler=ex_handler, kwargs=kwargs)

    def __call__(self):
        try:
            if self.concurrent:
                return self.func(*self.args, **self.kwargs)
            else:
                with action_lock:
                    return self.func(*self.args, **self.kwargs)
        except Exception as e:
            return self.ex_handler(self.func, e)

def _press_key(key):
    keyboard.write(key)


def play_macro(events, speed_factor):
    keyboard.play(events, speed_factor=speed_factor)


def press_key(key, ex_handler=None):
    return Action(_press_key, ex_handler=ex_handler, args=(key,))


def _run_command(*args, **kwargs):
    subprocess.run(*args, **kwargs)


def run_command(*args, ex_handler=None, **kwargs):
    return Action(_run_command, args=args, kwargs=kwargs, ex_handler=ex_handler)
