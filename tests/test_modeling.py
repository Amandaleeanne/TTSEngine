"""
Unit Tests for Modeling Sector (models.py & state.py)

Validates:
- Hierarchy integrity: Document > Chapter > Paragraph > Sentence > Word.
- Global index semantics & boundary helpers (first_word_index, last_word_index).
- Instant O(1) reverse lookup maps inside Document (_sentence_to_chapter, _sentence_to_paragraph).
- Engine State defaults, immutability, and computed active properties.
"""

import pytest

from modeling.models import *
from modeling.state import State


# =============================================================================
# Test Data Fixtures
# =============================================================================

@pytest.fixture
def populated_document() -> Document:
    """
    Constructs a 2-Chapter document:
    Chapter 0 (Title: 'Intro'):
      Paragraph 0:
        Sentence 0 (Global): Words 0..1 ("Hello", "World")
        Sentence 1 (Global): Words 2..3 ("Testing", "Engine")
    Chapter 1 (Title: 'Deep Dive'):
      Paragraph 0:
        Sentence 2 (Global): Words 4..5 ("Final", "Sentence")
    """
    w0 = Word(text="Hello", start_time=0.0, end_time=0.5, word_index=0)
    w1 = Word(text="World", start_time=0.5, end_time=1.0, word_index=1)
    s0 = Sentence(text="Hello World", words=(w0, w1), sentence_index=0)

    w2 = Word(text="Testing", start_time=1.0, end_time=1.5, word_index=2)
    w3 = Word(text="Engine", start_time=1.5, end_time=2.0, word_index=3)
    s1 = Sentence(text="Testing Engine", words=(w2, w3), sentence_index=1)

    p0 = Paragraph(sentences=(s0, s1), paragraph_index=0)
    c0 = Chapter(title="Intro", paragraphs=(p0,), chapter_index=0)

    w4 = Word(text="Final", start_time=2.0, end_time=2.5, word_index=4)
    w5 = Word(text="Sentence", start_time=2.5, end_time=3.0, word_index=5)
    s2 = Sentence(text="Final Sentence", words=(w4, w5), sentence_index=2)

    p1 = Paragraph(sentences=(s2,), paragraph_index=0)
    c1 = Chapter(title="Deep Dive", paragraphs=(p1,), chapter_index=1)

    return Document(title="Architecture Spec", chapters=(c0, c1))


# =============================================================================
# 1. Domain Models Tests
# =============================================================================

class TestModels:

    def test_word_duration(self):
        w = Word(text="sample", start_time=10.5, end_time=12.0, word_index=0)
        assert pytest.approx(w.duration) == 1.5

    def test_sentence_first_and_last_word_indices(self):
        w0 = Word(text="A", start_time=0.0, end_time=0.1, word_index=100)
        w1 = Word(text="B", start_time=0.1, end_time=0.2, word_index=101)
        w2 = Word(text="C", start_time=0.2, end_time=0.3, word_index=102)
        s = Sentence(text="A B C", words=(w0, w1, w2), sentence_index=5)

        assert s.first_word_index == 100
        assert s.last_word_index == 102

    def test_empty_sentence_boundaries_return_minus_one(self):
        empty_s = Sentence(text="", words=(), sentence_index=0)
        assert empty_s.first_word_index == -1
        assert empty_s.last_word_index == -1

    def test_paragraph_sentence_boundaries(self):
        s0 = Sentence(text="One", words=(), sentence_index=10)
        s1 = Sentence(text="Two", words=(), sentence_index=11)
        p = Paragraph(sentences=(s0, s1), paragraph_index=0)

        assert p.first_sentence_index == 10
        assert p.last_sentence_index == 11

    def test_chapter_paragraph_boundaries(self):
        p0 = Paragraph(sentences=(), paragraph_index=0)
        p1 = Paragraph(sentences=(), paragraph_index=1)
        c = Chapter(title="Chapter 1", paragraphs=(p0, p1), chapter_index=0)

        assert c.first_paragraph_index == 0
        assert c.last_paragraph_index == 1

    def test_document_o1_reverse_lookups(self, populated_document: Document):
        doc = populated_document

        # Sentence 0 & 1 -> Chapter 0, Paragraph 0
        assert doc.get_chapter_index_for_sentence(0) == 0
        assert doc.get_paragraph_index_for_sentence(0) == 0
        assert doc.get_chapter_index_for_sentence(1) == 0
        assert doc.get_paragraph_index_for_sentence(1) == 0

        # Sentence 2 -> Chapter 1, Paragraph 0
        assert doc.get_chapter_index_for_sentence(2) == 1
        assert doc.get_paragraph_index_for_sentence(2) == 0

        # Missing sentence returns -1
        assert doc.get_chapter_index_for_sentence(999) == -1
        assert doc.get_paragraph_index_for_sentence(999) == -1

    def test_document_total_counts(self, populated_document: Document):
        assert populated_document.total_chapters == 2
        assert populated_document.total_sentences == 3


# =============================================================================
# 2. State & Computed Properties Tests
# =============================================================================

class TestState:

    def test_unloaded_state_defaults(self):
        state = State()
        assert not state.is_loaded
        assert state.document is None
        assert state.current_chapter is None
        assert state.current_paragraph is None
        assert state.current_sentence is None

    def test_state_computed_properties_when_loaded(self, populated_document: Document):
        state = State(
            document=populated_document,
            file_path="/books/spec.epub",
            current_chapter_index=1,
            current_paragraph_index=0,
            current_sentence_index=2,
            current_word_index=4
        )

        assert state.is_loaded
        assert state.current_chapter.title == "Deep Dive"
        assert state.current_sentence.text == "Final Sentence"

    def test_out_of_bounds_state_indices_gracefully_return_none(self, populated_document: Document):
        state = State(
            document=populated_document,
            current_chapter_index=99,      # Invalid
            current_paragraph_index=99,    # Invalid
            current_sentence_index=99      # Invalid
        )

        assert state.current_chapter is None
        assert state.current_paragraph is None
        assert state.current_sentence is None