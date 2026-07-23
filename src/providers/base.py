from typing import Protocol
from src.modeling.models import Document

class DocumentProvider(Protocol):
    """Protocol for document loaders (TXT, EPUB, PDF)."""
    
    def can_open(self, file_path: str) -> bool:
        ...

    def parse(self, file_path: str) -> Document:
        ...