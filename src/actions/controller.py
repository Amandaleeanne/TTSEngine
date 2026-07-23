"""
This module implements the central engine Controller.

The Controller manages the application State, receives typed Commands,
updates state using navigation rules, and dispatches Events to subscribers.
"""

import dataclasses
from os import path
from importlib.resources import path
from typing import Callable, List, Optional
from modeling.state import State
from communication.commands import *
from communication.events import *
from actions import navigation


# Callback type for event subscribers (UI, Audio Player, Visualizer)
EventCallback = Callable[[Event], None]


class Controller:
    """Central engine controller coordinating commands, state updates, and events."""

    def __init__(self, initial_state: Optional[State] = None) -> None:
        self._state: State = initial_state if initial_state is not None else State()
        self._subscribers: List[EventCallback] = []

    @property
    def state(self) -> State:
        """Returns the current immutable state snapshot."""
        return self._state

    def subscribe(self, callback: EventCallback) -> None:
        """Subscribes a listener to receive engine events."""
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: EventCallback) -> None:
        """Unsubscribes an event listener."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def _emit(self, event: Event) -> None:
        """Broadcasts an event to all registered subscribers."""
        for callback in self._subscribers:
            callback(event)

    def handle_command(self, command: Command) -> None:
        """
        Processes an incoming typed command, computes the new state,
        and emits corresponding events.
        """
        try:
            match command:
                case Play():
                    if not self._state.is_playing:
                        self._state = dataclasses.replace(self._state, is_playing=True)
                        self._emit(PlaybackStarted())

                case Pause():
                    if self._state.is_playing:
                        self._state = dataclasses.replace(self._state, is_playing=False)
                        self._emit(PlaybackPaused())

                case Stop():
                    if self._state.is_playing:
                        self._state = dataclasses.replace(self._state, is_playing=False)
                        self._emit(PlaybackStopped())

                case SeekSentence() as cmd:
                    old_sentence = self._state.current_sentence_index
                    old_chapter = self._state.current_chapter_index

                    self._state = navigation.seek_to_sentence(self._state, cmd.sentence_index)

                    if self._state.current_chapter_index != old_chapter:
                        self._emit(ChapterChanged(chapter_index=self._state.current_chapter_index))
                    if self._state.current_sentence_index != old_sentence:
                        self._emit(SentenceChanged(sentence_index=self._state.current_sentence_index))

                    # Progress event emission
                    if self._state.document and self._state.document.total_sentences > 0:
                        progress = (self._state.current_sentence_index + 1) / self._state.document.total_sentences * 100.0
                        self._emit(ProgressChanged(progress_percentage=round(progress, 2)))

                    # Detect end-of-book state
                    if self._state.document and self._state.current_sentence_index >= self._state.document.total_sentences - 1:
                        if self._state.is_playing:
                            self._state = dataclasses.replace(self._state, is_playing=False)
                            self._emit(PlaybackFinished(total_sentences_read=self._state.document.total_sentences))
                case SeekChapter() as cmd:
                    old_chapter = self._state.current_chapter_index
                    self._state = navigation.seek_to_chapter(self._state, cmd.chapter_index)

                    if self._state.current_chapter_index != old_chapter:
                        self._emit(ChapterChanged(chapter_index=self._state.current_chapter_index))
                        self._emit(SentenceChanged(sentence_index=self._state.current_sentence_index))

                case SeekWord() as cmd:
                    self._state = navigation.seek_to_word(self._state, cmd.word_index)
                    self._emit(WordHighlighted(word_index=self._state.current_word_index))

                case SetSpeed() as cmd:
                    self._state = dataclasses.replace(self._state, speed=cmd.speed)
                    self._emit(SpeedSet(speed=cmd.speed))

                case SetVoice() as cmd:
                    self._state = dataclasses.replace(self._state, voice=cmd.voice)
                    self._emit(VoiceSet(voice=cmd.voice))

                case OpenBook():
                    doc = self._registry.load(path)
                    self._state = State(document=doc, file_path=path)
                    self._emit(BookLoaded(document=doc))

        except Exception as err:
            self._emit(ErrorOccurred(message=str(err)))