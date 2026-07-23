import pytest

from modeling.models import Document, Chapter, Paragraph, Sentence, Word
from modeling.state import State
from actions.controller import Controller


@pytest.fixture
def sample_document() -> Document:
    # Create a small document with two chapters and a few words/sentences
    w0 = Word(text="W0", start_time=0.0, end_time=0.5, word_index=0)
    w1 = Word(text="W1", start_time=0.5, end_time=1.0, word_index=1)
    s0 = Sentence(text="Sentence 0", words=(w0, w1), sentence_index=0)

    w2 = Word(text="W2", start_time=1.0, end_time=1.5, word_index=2)
    w3 = Word(text="W3", start_time=1.5, end_time=2.0, word_index=3)
    s1 = Sentence(text="Sentence 1", words=(w2, w3), sentence_index=1)

    p0 = Paragraph(sentences=(s0,), paragraph_index=0)
    p1 = Paragraph(sentences=(s1,), paragraph_index=0)

    c0 = Chapter(title="Chapter 1", paragraphs=(p0,), chapter_index=0)
    c1 = Chapter(title="Chapter 2", paragraphs=(p1,), chapter_index=1)

    return Document(title="Sample", chapters=(c0, c1))


@pytest.fixture
def loaded_controller(sample_document: Document) -> Controller:
    controller = Controller()
    controller._state = State(document=sample_document, file_path="/tmp/sample.txt")
    return controller
