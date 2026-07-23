"""
This module implements the central engine Controller.

The Controller manages the application State, receives typed Commands,
updates state using navigation rules (see navigation.py), and dispatches Events to subscribers.
"""

import dataclasses
from typing import Callable, List, Optional
from modeling.state import State
from communication.events import *
from actions import navigation
from providers.registry import ProviderRegistry


# Callback type for event subscribers (UI, Audio Player, Visualizer)
EventCallback = Callable[[Event], None]


class Controller:
    """Central engine controller coordinating commands, state updates, and events."""

    def __init__(self, initial_state: Optional[State] = None, registry: Optional[ProviderRegistry] = None) -> None:
        self._state: State = initial_state if initial_state is not None else State()
        self._subscribers: List[EventCallback] = []
        self._registry: ProviderRegistry = registry if registry is not None else ProviderRegistry()

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

    # --- Command Handler ---
    def play(self) -> None:
        """
        Updates the state of the engine and emits the play event
        """
        try:
            if not self.state.is_playing:
                self._state = dataclasses.replace(self._state, is_playing=True)
                self._emit(PlaybackStarted())
        except Exception as err:
            self._emit(ErrorOccurred(message=str(err)))

    # Backwards-compatible capitalized method names
    def Play(self) -> None:
        self.play()

    def pause(self) -> None:
        """
        Updates the state of the engine and emits the Pause event
        """
        try:
            if self._state.is_playing:
                self._state = dataclasses.replace(self._state, is_playing=False)
                self._emit(PlaybackPaused())
        except Exception as err:
                    self._emit(ErrorOccurred(message=str(err)))

    def Pause(self) -> None:
        self.pause()

    def stop(self) -> None:
        """
        Updates the state of the engine and emits the Stop event
        """
        try:
            if self._state.is_playing:
                self._state = dataclasses.replace(self._state, is_playing=False)
                self._emit(PlaybackStopped())
        except Exception as err:
            self._emit(ErrorOccurred(message=str(err)))

    def Stop(self) -> None:
        self.stop()

    def seek_sentence(self, sentence_index: int) -> None:
        """
        seeks for a sentence, updates the state of the engine, and emits the corresponding events needed
        """
        #No silly, you are already on that sentence
        if (sentence_index == self._state.current_sentence_index):
            return # @TODO: Add event for "Already on that sentence"

        try:
            old_sentence = self._state.current_sentence_index
            old_chapter = self._state.current_chapter_index
            old_paragraph = self._state.current_paragraph_index

            self._state = navigation.seek_to_sentence(self._state, sentence_index)

            if self._state.current_chapter_index != old_chapter:
                self._emit(ChapterChanged(chapter_index=self._state.current_chapter_index))
            if self._state.current_sentence_index != old_sentence:
                self._emit(SentenceChanged(sentence_index=self._state.current_sentence_index))
            if self._state.current_paragraph_index != old_paragraph:
                self._emit(ParagraphChanged(paragraph_index=self._state.current_paragraph_index))

            # Narrow document into a local variable to satisfy type checkers
            doc = self._state.document
            if doc and doc.total_sentences > 0:
                progress = (self._state.current_sentence_index + 1) / doc.total_sentences * 100.0
                self._emit(ProgressChanged(progress_percentage=round(progress, 2)))

            if doc and self._state.current_sentence_index >= doc.total_sentences - 1:
                if self._state.is_playing:
                    self._state = dataclasses.replace(self._state, is_playing=False)
                    self._emit(PlaybackFinished(total_sentences_read=doc.total_sentences))
        except Exception as err:
            self._emit(ErrorOccurred(message=str(err)))

    def seek_chapter(self, chapter_index: int) -> None:
        """
        seeks for a chapter, updates the state of the engine, and emits the corresponding events needed
        """
        try:
            old_chapter = self._state.current_chapter_index
            old_paragraph = self._state.current_paragraph_index
            self._state = navigation.seek_to_chapter(self._state, chapter_index)

            if self._state.current_chapter_index != old_chapter:
                self._emit(ChapterChanged(chapter_index=self._state.current_chapter_index))
                self._emit(SentenceChanged(sentence_index=self._state.current_sentence_index))
            if self._state.current_paragraph_index != old_paragraph:
                self._emit(ParagraphChanged(paragraph_index=self._state.current_paragraph_index))
        except Exception as err:
            self._emit(ErrorOccurred(message=str(err)))
    
    def seek_word(self, word_index: int) -> None:
        """
        seeks for a word, updates the state of the engine, and emits the corresponding events needed
        """
        try:
            old_paragraph = self._state.current_paragraph_index
            self._state = navigation.seek_to_word(self._state, word_index)
            if self._state.current_paragraph_index != old_paragraph:
                self._emit(ParagraphChanged(paragraph_index=self._state.current_paragraph_index))
            self._emit(WordHighlighted(word_index=self._state.current_word_index))
        except Exception as err:
            self._emit(ErrorOccurred(message=str(err)))

    def set_speed(self, speed: float) -> None:
        """
        sets the speed of the engine, and emits the corresponding event, for TTS only
        """
        try:
            self._state = dataclasses.replace(self._state, speed=speed)
            self._emit(SpeedSet(speed=speed))
        except Exception as err:
            self._emit(ErrorOccurred(message=str(err)))

    def set_voice(self, voice: str) -> None:
        """
        sets the voice of the engine, and emits the corresponding event, for TTS only
        """
        try:
            self._state = dataclasses.replace(self._state, voice=voice)
            self._emit(VoiceSet(voice=voice))
        except Exception as err:
            self._emit(ErrorOccurred(message=str(err)))

    def open_book(self, file_path: str) -> None:
        """
        loads the book into the engine and emits the corresponding events sucsessful or not
        """
        try:
            document = self._registry.load(file_path)
            self._state = State(document=document, file_path=file_path)
            self._emit(BookLoaded(file_path=file_path, document=document))
        except Exception as err:
            self._emit(ErrorOccurred(message=str(err)))

#@TODO:this may change to skipping to words, but for now its sentences
    def skip_forward(self, sentences: int = 1) -> None:
        """Skip forward by N sentences (relative seek)."""
        try:
            if sentences <= 0:
                raise ValueError("sentences must be a positive integer")
            target = self._state.current_sentence_index + sentences
            self.seek_sentence(target)
        except Exception as err:
            self._emit(ErrorOccurred(message=str(err)))

    def skip_backward(self, sentences: int = 1) -> None:
        """Skip backward by N sentences (relative seek)."""
        try:
            if sentences <= 0:
                raise ValueError("sentences must be a positive integer")
            target = self._state.current_sentence_index - sentences
            self.seek_sentence(target)
        except Exception as err:
            self._emit(ErrorOccurred(message=str(err)))

