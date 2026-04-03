import shutil
from pathlib import Path

from backend.app.storage.base import ObjectStorage


class LocalObjectStorage(ObjectStorage):
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def save_file(self, source_path: Path, destination_key: str) -> str:
        target_path = self.root_dir / destination_key
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_path), str(target_path))
        return str(target_path)

    def fetch_to_local(self, storage_path: str, local_path: Path) -> Path:
        source_path = Path(storage_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        if source_path.resolve() != local_path.resolve():
            shutil.copy2(source_path, local_path)
        return local_path
