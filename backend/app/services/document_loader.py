import logging
from pathlib import Path

from docx import Document
from pypdf import PdfReader


logger = logging.getLogger(__name__)


class DocumentLoader:
    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}

    def load(self, file_path: Path) -> list[tuple[int | None, str]]:
        suffix = file_path.suffix.lower()
        if suffix not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {suffix}")

        if suffix == ".pdf":
            return self._load_pdf(file_path)
        if suffix == ".docx":
            return self._load_docx(file_path)
        return [(None, file_path.read_text(encoding="utf-8", errors="ignore"))]

    def _load_pdf(self, file_path: Path) -> list[tuple[int | None, str]]:
        pages: list[tuple[int | None, str]] = []
        reader = PdfReader(str(file_path))
        for index, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append((index, text))
        logger.info("Loaded %s pages from %s", len(pages), file_path.name)
        return pages

    def _load_docx(self, file_path: Path) -> list[tuple[int | None, str]]:
        document = Document(str(file_path))
        paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
        return [(None, "\n".join(paragraphs))]
