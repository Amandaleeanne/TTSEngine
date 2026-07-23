from typing import List, Optional
from modeling.models import Document
from providers.base import DocumentProvider

class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: List[DocumentProvider] = []

    def register(self, provider: DocumentProvider) -> None:
        self._providers.append(provider)

    def get_provider_for(self, file_path: str) -> Optional[DocumentProvider]:
        for provider in self._providers:
            if provider.can_open(file_path):
                return provider
        return None

    def load(self, file_path: str) -> Document:
        provider = self.get_provider_for(file_path)
        if provider is None:
            raise ValueError(f"No document provider found for file: {file_path}")
        return provider.parse(file_path)