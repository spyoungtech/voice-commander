import easygui as eg
from threading import Lock, Thread
import keyboard
import time
from voice_commander import Commander
from voice_commander.actions import Action
import logging
import speech_recognition as sr

class App(Commander):
    """
    Provides GUI interface to drive commander voice recognition application.
    """
    def __init__(self):
        self.listen_threads = 3
        self._running_lock = Lock()
        self._running = False
        self._mic_lock = Lock()
        super().__init__()

    def add_command(self):
        command_text = eg.enterbox('Enter command trigger phrase', title='set trigger')
        eg.msgbox('Once you press "record" your keyboard strokes will be recorded. When running, these keyboard strokes will be played back when the trigger phrase is heard', title='record action', ok_button='record')
        box = eg.buttonbox(choices=['OK'], run=False)
        box.ui.set_msg('recording...\nPress Enter to stop recording')
        action = Action.from_recording(until='enter')
        box.ui.set_msg('done!')
        box.run()
        self.add_action(command_text, action)

    def _poll(self):
        self.run_box.msg = 'running {}'.format(time.time())
        self.run_box.ui.boxRoot.after(1000, self._poll)

    def run(self):
        self._running = True
        self.run_box = eg.buttonbox(msg='starting...', choices=['stop'], run=False)
        self.run_box.ui.boxRoot.after(100, self._poll)
        threads = []

        try:
            for _ in range(self.listen_threads):
                th = Thread(target=self.do_listen)
                threads.append(th)
                th.start()
            self.run_box.run()
        except Exception as e:
            logging.debug('Something went wrong: {}'.format(e))
        finally:
            cleanup_box = eg.buttonbox(choices=['OK'], run=False)
            cleanup_box.ui.set_msg("Stopping... this shouldn't take long...")
            with self._running_lock:
                self._running = False
            for th in threads:
                th.join()
            cleanup_box.msg = 'Done!'
            cleanup_box.run()


    def do_listen(self):
        logging.debug('LISTENER STARTED')
        while True:
            try:
                with self._mic_lock:
                    if not self._running:
                        break
                    audio = self.listen(timeout=5)
                logging.debug('Starting analysis')
                value = self.analyze(audio)
                logging.debug('Attempting to match audio to command')
                actions = self.match_command(value)
                for action in actions:
                    logging.debug('Executing action %s' % str(action))
                    action()
            except sr.WaitTimeoutError as e:
                logging.debug('Timed out waiting for audio')
            except Exception as e:
                logging.debug('Something happened; {}'.format(e))
            if not self._running:
                break
        logging.debug('LISTENER STOPPED')


    def save_commands(self):
        fp = eg.filesavebox('choose file to save commands to')
        super().save_commands(fp)

    def load_commands(self):
        fp = eg.fileopenbox('Choose file to load commands from')
        super().load_commands(fp)

    def edit_commands(self):
        choices = list(self.commands.keys())
        if not choices:
            return eg.msgbox('No commands to edit! Add some commands first.')
        command_to_edit = eg.choicebox(msg="Choose a command trigger to edit", choices=choices)
        self.edit_command(command_to_edit)

    def edit_command(self, command_trigger):
        actions = self.commands[command_trigger]
        eg.msgbox('This feature is not currently implemented')

    def main(self):
        choices = {
            'add command': self.add_command,
            'load commands': self.load_commands,
            'save commands': self.save_commands,
            'edit_commands': self.edit_commands,
            'run': self.run,
        }
        while True:
            response = eg.buttonbox(msg="Welcome to Voice Commander. Choose an option.", choices=list(choices.keys()))
            action = choices.get(response)
            if action:
                action()
            else:
                #  X button or ESC was pressed
                logging.info('Exiting')
                return 0
