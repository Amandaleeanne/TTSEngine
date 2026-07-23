import os
from modeling.models import Document, Chapter, Paragraph, Sentence, Word
from providers.base import DocumentProvider

class TXTProvider(DocumentProvider):
    """Basic plain text loader."""

    def can_open(self, file_path: str) -> bool:
        return file_path.lower().endswith(".txt")

    def parse(self, file_path: str) -> Document:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        title = os.path.splitext(os.path.basename(file_path))[0]
        
        # Simple sentence extraction split on periods
        raw_sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
        
        sentences = []
        global_w_idx = 0
        for s_idx, raw_s in enumerate(raw_sentences):
            words = []
            for raw_w in raw_s.split():
                # TXT provider cannot infer timings; use zeroed times as placeholders
                words.append(Word(text=raw_w, start_time=0.0, end_time=0.0, word_index=global_w_idx))
                global_w_idx += 1
            
            sentences.append(
                Sentence(text=raw_s + ".", words=tuple(words), sentence_index=s_idx)
            )

        paragraph = Paragraph(sentences=tuple(sentences), paragraph_index=0)
        chapter = Chapter(title="Chapter 1", paragraphs=(paragraph,), chapter_index=0)

        return Document(title=title, chapters=(chapter,))