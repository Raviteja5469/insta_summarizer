from abc import ABC, abstractmethod
import os

class BaseDownloader(ABC):
    @abstractmethod
    def download(self, url: str) -> str:
        """Download content from URL, return local file path."""
        pass

    def _cleanup(self, path: str):
        if os.path.exists(path):
            os.remove(path)