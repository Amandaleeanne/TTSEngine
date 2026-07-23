"""
Unit Tests for Communication Sector (commands.py & events.py)

Validates:
- Correct instantiation & immutability of commands and events.
- Defensive validation in commands (__post_init__).
- Edge cases in payloads (empty strings, negative indices, out-of-bounds speed rates).
- File system sanity checks for OpenBook commands.
"""

import pytest
from pathlib import Path

from communication.commands import (
    Play, Pause, Stop, OpenBook, SeekSentence, SeekChapter,
    SeekWord, SetSpeed, SetVoice, Command, EngineCommand
)
from communication.events import (
    BookLoaded, PlaybackStarted, PlaybackPaused, PlaybackStopped,
    WordHighlighted, SentenceChanged, ChapterChanged, SpeedSet, VoiceSet,
    ErrorOccurred, Event, EngineEvent
)
from modeling.models import Document, Chapter, Paragraph, Sentence, Word


# =============================================================================
# 1. Commands Tests
# =============================================================================

class TestCommands:
    
    # --- No-Data Commands ---
    
    def test_no_data_commands_instantiation(self):
        play = Play()
        pause = Pause()
        stop = Stop()

        assert isinstance(play, EngineCommand)
        assert isinstance(pause, EngineCommand)
        assert isinstance(stop, EngineCommand)

    def test_commands_are_immutable(self):
        play = Play()
        with pytest.raises(AttributeError):
            play.some_attribute = True

    # --- OpenBook Commands ---

    def test_open_book_valid_path(self, tmp_path: Path):
        valid_file = tmp_path / "test_book.epub"
        valid_file.write_text("dummy content")

        cmd = OpenBook(file_path=str(valid_file))
        assert cmd.file_path == str(valid_file)

    def test_open_book_empty_path_raises_error(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            OpenBook(file_path="")
        with pytest.raises(ValueError, match="cannot be empty"):
            OpenBook(file_path="   ")

    def test_open_book_non_existent_file_raises_error(self, tmp_path: Path):
        non_existent = tmp_path / "missing.epub"
        with pytest.raises(FileNotFoundError):
            OpenBook(file_path=str(non_existent))

    # --- Seek Commands ---

    @pytest.mark.parametrize("index", [0, 1, 100, 999999])
    def test_seek_commands_valid_indices(self, index: int):
        s_cmd = SeekSentence(sentence_index=index)
        c_cmd = SeekChapter(chapter_index=index)
        w_cmd = SeekWord(word_index=index)

        assert s_cmd.sentence_index == index
        assert c_cmd.chapter_index == index
        assert w_cmd.word_index == index

    @pytest.mark.parametrize("negative_index", [-1, -50, -999])
    def test_seek_commands_negative_indices_raise_error(self, negative_index: int):
        with pytest.raises(ValueError, match="must be non-negative"):
            SeekSentence(sentence_index=negative_index)
        with pytest.raises(ValueError, match="must be non-negative"):
            SeekChapter(chapter_index=negative_index)
        with pytest.raises(ValueError, match="must be non-negative"):
            SeekWord(word_index=negative_index)

    # --- Setting Commands ---

    @pytest.mark.parametrize("valid_speed", [0.25, 0.5, 1.0, 1.5, 2.0, 4.0])
    def test_set_speed_valid_rates(self, valid_speed: float):
        cmd = SetSpeed(speed=valid_speed)
        assert cmd.speed == valid_speed

    @pytest.mark.parametrize("invalid_speed", [0.0, 0.1, 0.24, 4.01, 5.0, -1.0])
    def test_set_speed_out_of_bounds_raises_error(self, invalid_speed: float):
        with pytest.raises(ValueError, match="must be between 0.25 and 4.0"):
            SetSpeed(speed=invalid_speed)

    def test_set_voice_valid(self):
        cmd = SetVoice(voice="en-US-AvaNeural")
        assert cmd.voice == "en-US-AvaNeural"

    def test_set_voice_empty_raises_error(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            SetVoice(voice="")
        with pytest.raises(ValueError, match="cannot be empty"):
            SetVoice(voice="   ")
# =============================================================================
# 2. Events Tests
# =============================================================================

class TestEvents:

    def test_playback_events_instantiation(self):
        e_start = PlaybackStarted()
        e_pause = PlaybackPaused()
        e_stop = PlaybackStopped()

        assert isinstance(e_start, EngineEvent)
        assert isinstance(e_pause, EngineEvent)
        assert isinstance(e_stop, EngineEvent)

    def test_text_sync_events_payload(self):
        e_word = WordHighlighted(word_index=42)
        e_sent = SentenceChanged(sentence_index=10)
        e_chap = ChapterChanged(chapter_index=2)

        assert e_word.word_index == 42
        assert e_sent.sentence_index == 10
        assert e_chap.chapter_index == 2

    def test_book_loaded_event_payload(self):
        empty_doc = Document(title="Empty", chapters=())
        e_loaded = BookLoaded(file_path="/path/to/book.epub", document=empty_doc)

        assert e_loaded.file_path == "/path/to/book.epub"
        assert e_loaded.document.title == "Empty"

    def test_settings_events_payload(self):
        e_speed = SpeedSet(speed=1.75)
        e_voice = VoiceSet(voice="en-GB-SoniaNeural")

        assert e_speed.speed == 1.75
        assert e_voice.voice == "en-GB-SoniaNeural"

    def test_error_occurred_event_payload(self):
        e_err = ErrorOccurred(message="TTS Network Timeout")
        assert e_err.message == "TTS Network Timeout"