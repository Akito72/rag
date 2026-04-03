from abc import ABC, abstractmethod
from pathlib import Path


class ObjectStorage(ABC):
    @abstractmethod
    def save_file(self, source_path: Path, destination_key: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def fetch_to_local(self, storage_path: str, local_path: Path) -> Path:
        raise NotImplementedError
