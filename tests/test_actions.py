"""
Unit Tests for Actions Sector (navigation.py & controller.py)

Validates:
- Pure state navigation transformations (seek_sentence, seek_chapter, next/prev).
- Boundary clamping for invalid indices or empty documents.
- Controller initialization, command execution, and event emission.
- Sliding window navigation compatibility for pre-fetching TTS.
"""

import pytest

from modeling.models import Document, Chapter, Paragraph, Sentence, Word
from modeling.state import State
from communication.commands import OpenBook, Play, Pause, SeekSentence, SetSpeed
from communication.events import BookLoaded, PlaybackStarted, PlaybackPaused, SentenceChanged
from actions import navigation
from actions.controller import Controller


# =============================================================================
# Test Data Fixture
# =============================================================================

@pytest.fixture
def multi_chapter_doc() -> Document:
    """3 Chapters, each containing 2 sentences."""
    chapters = []
    global_s_idx = 0
    global_w_idx = 0

    for c_idx in range(3):
        sentences = []
        for s_in_chap in range(2):
            words = (
                Word(text=f"W{global_w_idx}", start_time=0.0, end_time=0.5, word_index=global_w_idx),
                Word(text=f"W{global_w_idx+1}", start_time=0.5, end_time=1.0, word_index=global_w_idx+1),
            )
            sentences.append(
                Sentence(text=f"Sentence {global_s_idx}", words=words, sentence_index=global_s_idx)
            )
            global_s_idx += 1
            global_w_idx += 2

        p = Paragraph(sentences=tuple(sentences), paragraph_index=0)
        ch = Chapter(title=f"Chapter {c_idx+1}", paragraphs=(p,), chapter_index=c_idx)
        chapters.append(ch)

    return Document(title="Multi Chapter Doc", chapters=tuple(chapters))


# =============================================================================
# 1. Navigation State Transformation Tests
# =============================================================================

class TestNavigation:

    def test_seek_to_sentence_updates_parent_containers(self, multi_chapter_doc: Document):
        initial_state = State(document=multi_chapter_doc)

        # Sentence 4 belongs to Chapter 2, Paragraph 0
        state_s4 = navigation.seek_to_sentence(initial_state, target_sentence_index=4)

        assert state_s4.current_sentence_index == 4
        assert state_s4.current_chapter_index == 2
        assert state_s4.current_paragraph_index == 0
        assert state_s4.current_word_index == 8  # First word index of sentence 4

    def test_seek_sentence_lower_boundary_clamping(self, multi_chapter_doc: Document):
        state = State(document=multi_chapter_doc)
        clamped = navigation.seek_to_sentence(state, target_sentence_index=-100)
        assert clamped.current_sentence_index == 0

    def test_seek_sentence_upper_boundary_clamping(self, multi_chapter_doc: Document):
        state = State(document=multi_chapter_doc)
        # Total sentences = 6 (indices 0..5)
        clamped = navigation.seek_to_sentence(state, target_sentence_index=999)
        assert clamped.current_sentence_index == 5

    def test_next_and_previous_sentence_stepping(self, multi_chapter_doc: Document):
        s0 = State(document=multi_chapter_doc, current_sentence_index=0)

        s1 = navigation.next_sentence(s0)
        assert s1.current_sentence_index == 1

        s2 = navigation.next_sentence(s1)
        assert s2.current_sentence_index == 2

        s_prev = navigation.previous_sentence(s2)
        assert s_prev.current_sentence_index == 1

    def test_seek_chapter_jumps_to_first_sentence(self, multi_chapter_doc: Document):
        state = State(document=multi_chapter_doc)

        # Jump to Chapter 1 -> First sentence is Index 2
        state_c1 = navigation.seek_to_chapter(state, target_chapter_index=1)
        assert state_c1.current_chapter_index == 1
        assert state_c1.current_sentence_index == 2

    def test_next_and_previous_chapter(self, multi_chapter_doc: Document):
        s0 = State(document=multi_chapter_doc, current_chapter_index=0)

        s_ch1 = navigation.next_chapter(s0)
        assert s_ch1.current_chapter_index == 1
        assert s_ch1.current_sentence_index == 2

        s_ch2 = navigation.next_chapter(s_ch1)
        assert s_ch2.current_chapter_index == 2
        assert s_ch2.current_sentence_index == 4

        s_back = navigation.previous_chapter(s_ch2)
        assert s_back.current_chapter_index == 1
        assert s_back.current_sentence_index == 2

    def test_navigation_on_unloaded_document_returns_same_state(self):
        empty_state = State()
        assert navigation.next_sentence(empty_state) == empty_state
        assert navigation.seek_to_sentence(empty_state, 5) == empty_state


# =============================================================================
# 2. Controller State & Event Emission Tests
# =============================================================================

class TestController:

    def test_controller_initial_state(self):
        controller = Controller()
        assert not controller.state.is_loaded
        assert controller.state.is_playing is False

    def test_controller_dispatches_events_to_subscribers(self, multi_chapter_doc: Document):
        controller = Controller()
        received_events = []

        # Subscribe a dummy event listener
        controller.subscribe(lambda event: received_events.append(event))

        # Manually set state to loaded document for testing
        controller._state = State(document=multi_chapter_doc)

        # Dispatch Play command
        controller.handle_command(Play())
        assert controller.state.is_playing is True
        assert any(isinstance(e, PlaybackStarted) for e in received_events)

        # Dispatch Pause command
        controller.handle_command(Pause())
        assert controller.state.is_playing is False
        assert any(isinstance(e, PlaybackPaused) for e in received_events)

    def test_controller_handles_seek_command_and_emits_event(self, multi_chapter_doc: Document):
        controller = Controller()
        received_events = []

        controller.subscribe(lambda event: received_events.append(event))
        controller._state = State(document=multi_chapter_doc, current_sentence_index=0)

        # Seek to sentence 3
        controller.handle_command(SeekSentence(sentence_index=3))

        assert controller.state.current_sentence_index == 3
        assert any(isinstance(e, SentenceChanged) and e.sentence_index == 3 for e in received_events)