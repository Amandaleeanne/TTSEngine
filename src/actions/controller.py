import dataclasses
from typing import Callable

from communication.commands import EngineCommand, Play, Pause, SeekSentence, SeekChapter
from communication.events import (
    EngineEvent,
    PlaybackStarted,
    PlaybackPaused,
    SentenceChanged,
)
from modeling.state import State
from actions import navigation


Subscriber = Callable[[EngineEvent], None]


class Controller:
    """Engine controller that handles commands and emits events."""

    def __init__(self) -> None:
        self._state = State()
        self._subscribers: list[Subscriber] = []

    @property
    def state(self) -> State:
        return self._state

    def subscribe(self, subscriber: Subscriber) -> None:
        self._subscribers.append(subscriber)

    def unsubscribe(self, subscriber: Subscriber) -> None:
        if subscriber in self._subscribers:
            self._subscribers.remove(subscriber)

    def _emit(self, event: EngineEvent) -> None:
        for subscriber in list(self._subscribers):
            subscriber(event)

    def handle_command(self, command: EngineCommand) -> None:
        if isinstance(command, Play):
            self._state = dataclasses.replace(self._state, is_playing=True)
            self._emit(PlaybackStarted())
            return

        if isinstance(command, Pause):
            self._state = dataclasses.replace(self._state, is_playing=False)
            self._emit(PlaybackPaused())
            return

        if isinstance(command, SeekSentence):
            self._state = navigation.seek_to_sentence(self._state, command.sentence_index)
            self._emit(SentenceChanged(sentence_index=self._state.current_sentence_index))
            return

        if isinstance(command, SeekChapter):
            self._state = navigation.seek_to_chapter(self._state, command.chapter_index)
            self._emit(SentenceChanged(sentence_index=self._state.current_sentence_index))
            return

        # Unsupported commands are ignored for now.
