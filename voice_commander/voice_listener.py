from __future__ import annotations

import logging
import queue
import time
import warnings
from collections.abc import Sequence
from threading import Lock
from threading import Thread
from typing import TYPE_CHECKING

import speech_recognition as sr  # type: ignore[import-untyped]
from speech_recognition import AudioData
from thefuzz import process  # type: ignore[import-untyped]

from voice_commander._utils import get_logger

logger = get_logger()


class Listener:
    def __init__(self) -> None:
        self._listen_threads: int = 3
        self._listen_timeout: int = 5
        self._listening: bool = False
        self._running: bool = False
        self._mic_lock = Lock()
        self._reporting_lock = Lock()
        self._recognizer_name = 'google'
        self._recognizer = sr.Recognizer()
        self._listener_threads: list[Thread] = []
        self._reporting_queues: dict[str, queue.Queue[str]] = {}
        self._match_threshold: int = 50

    def add_trigger_phrases(self, phrases: Sequence[str]) -> queue.Queue[str]:
        q: queue.Queue[str] = queue.Queue()
        for phrase in phrases:
            phrase = phrase.lower()
            if phrase in self._reporting_queues:
                raise ValueError(f'Phrase {phrase!r} already registered')
            with self._reporting_lock:
                self._reporting_queues[phrase] = q
        return q

    def remove_trigger_phrase(self, phrase: str) -> None:
        if phrase not in self._reporting_queues:
            raise ValueError('Phrase not registered')
        self._reporting_queues.pop(phrase)
        return None

    def _match_command(self, value: str) -> str | None:
        item, ratio = process.extractOne(value, self._reporting_queues.keys())
        if ratio >= self._match_threshold:
            if TYPE_CHECKING:
                assert isinstance(item, str)
            return item
        else:
            return None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._listening = True
        for _ in range(self._listen_threads):
            t = Thread(target=self._listen)
            t.start()
            self._listener_threads.append(t)

    def stop(self) -> None:
        if self._running or self._listening:
            logger.info('Stopping voice listener (this may take a few seconds)...')
            self._running = False
            self._listening = False
            while self._listener_threads:
                t = self._listener_threads.pop()
                t.join()
            logger.info('Voice listener stopped')
        else:
            logger.debug('Stop called on already-stopped listener')

    def start_listening(self) -> None:
        self._listening = True

    def stop_listening(self) -> None:
        self._listening = False

    def _analyze(self, audio: AudioData) -> str | None:
        recognizer_func = getattr(self._recognizer, f'recognize_{self._recognizer_name}', None)
        if recognizer_func is None:
            warnings.warn(f'Unknown recognizer name {self._recognizer_name!r}. Falling back to google recognizer')
            recognizer_func = self._recognizer.recognize_google
        try:
            value = recognizer_func(audio)
            if TYPE_CHECKING:
                assert isinstance(value, str)
            logging.info('Recognized text: "{}"'.format(value))
            return value
        except sr.UnknownValueError as e:
            logging.debug('Issue recognizing audio; {}'.format(e))
        except sr.RequestError as e:
            msg = "Couldn't request results from Google Speech Recognition service; {0}".format(e)
            logging.warning(msg)
        return None

    def _listen(self) -> None:
        logging.debug('LISTENER STARTED')
        while True:
            if not self._listening:
                logging.debug('Listening is currently disabled. Waiting one second.')
                time.sleep(1)
                continue
            if not self._running:
                break
            try:
                with self._mic_lock:
                    if not self._running or not self._listening:
                        break
                    with sr.Microphone() as source:
                        audio = self._recognizer.listen(source, timeout=self._listen_timeout)
                logging.debug('Starting analysis')
                value = self._analyze(audio)
                if value is None:
                    continue
                logging.debug('Attempting to match audio to known phrase')
                matching_phrase = self._match_command(value)
                if matching_phrase is not None:
                    with self._reporting_lock:
                        q = self._reporting_queues[matching_phrase]
                        q.put(value)
            except sr.WaitTimeoutError:
                logging.debug('Timed out waiting for audio')
            except Exception as e:
                logging.error(e, exc_info=True)
            if not self._running:
                break
        logging.debug('LISTENER STOPPED')
