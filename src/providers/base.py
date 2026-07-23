from typing import Protocol
from modeling.models import Document

class DocumentProvider(Protocol):
    """Protocol for document loaders (TXT, EPUB, PDF)."""
    
    def can_open(self, file_path: str) -> bool:
        ...

    def parse(self, file_path: str) -> Document:
        ...


# Convenience loader used by tests and simple consumers.
def load_txt_file(file_path: str) -> Document:
    """Load a plain-text file and return a `Document` using the TXT provider.

    This is a small compatibility helper so callers may import
    `load_txt_file` from `providers.base` for simple test fixtures.
    """
    # Import locally to avoid circular imports at module import time.
    from providers.txt_provider import TXTProvider

    provider = TXTProvider()
    return provider.parse(file_path)