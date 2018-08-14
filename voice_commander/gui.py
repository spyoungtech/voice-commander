import easygui as eg
from threading import Lock
import keyboard
import time
from voice_commander import Commander
from voice_commander.actions import Action


class App(Commander):
    """
    Provides GUI interface to drive commander voice recognition application.
    """
    def __init__(self):
        self._mic_lock = Lock()
        super().__init__()

    def add_command(self):
        command_text = eg.enterbox('Enter command trigger phrase', title='set trigger')
        eg.msgbox('Once you press "record" your keyboard strokes will be recorded. These keyboard strokes will be played back', title='record action', ok_button='record')
        box = eg.buttonbox(choices=['OK'], run=False)
        box.ui.set_msg('recording...\nPress Enter to stop recording')
        action = Action.from_recording(until='enter')
        box.ui.set_msg('done!')
        box.run()
        self.add_action(command_text, action)

    def _poll(self):
        self.run_box.msg = 'running {}'.format(time.time())
        keyboard.call_later(self.do_listen)
        self.run_box.ui.boxRoot.after(500, self._poll)

    def run(self):
        self.run_box = eg.buttonbox(msg='starting...', choices=['stop'], run=False)
        self.run_box.ui.boxRoot.after(100, self._poll)
        self.run_box.run()

    def do_listen(self):
        try:
            with self._mic_lock:
                audio = self.listen()
            value = self.analyze(audio)
            actions = self.match_command(value)
            for action in actions:
                action()
        except:
            pass

    def main(self):
        while True:
            response = eg.buttonbox(choices=['add command', 'run'])
            if response == 'add command':
                self.add_command()
            if response == 'run':
                self.run()
            else:
                return 0