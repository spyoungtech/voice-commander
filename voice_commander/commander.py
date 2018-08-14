from collections import defaultdict
import warnings
from fuzzywuzzy import process
import speech_recognition as sr
import logging


class Commander(object):
    def __init__(self):
        self.commands = defaultdict(list)
        self.recognizer = sr.Recognizer()
        self._recognizer = 'google'
        self.match_threshold = 50

    def analyze(self, *args, **kwargs):
        recognizer_func = getattr(self.recognizer, 'recognize_'+self._recognizer, None)
        if recognizer_func is None:
            recognizer_func = self.recognizer.recognize_google
        try:
            value = recognizer_func(*args, **kwargs)
            logging.debug('Recognized text: "{}"'.format(value))
        except sr.UnknownValueError as e:
            logging.debug('Issue recognizing audio; {}'.format(e))
        except sr.RequestError as e:
            msg = "Couldn't request results from Google Speech Recognition service; {0}".format(e)
            logging.debug(msg)

    def listen(self, *args, **kwargs):
        with sr.Microphone() as source:
            audio = self.recognizer.listen(source, *args, **kwargs)
        return audio

    def match_command(self, text):
        best_match, match_ratio = process.extractOne(text, self.commands.keys())
        if match_ratio > self.match_threshold:
            logging.debug('Matched command "{}" based on heard text "{}" with ratio of "{}"'.format(best_match, text, match_ratio))
            action_list = self.commands[best_match]
            return action_list
        return []

    def add_action(self, hook_text, func):
        assert callable(func)
        self.commands[hook_text].append(func)
