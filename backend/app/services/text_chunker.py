class RecursiveTextChunker:
    def __init__(self, chunk_size: int, chunk_overlap: int) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", ". ", " ", ""]

    def split_text(self, text: str) -> list[str]:
        cleaned = " ".join(text.split())
        if not cleaned:
            return []
        return self._split_with_separator(cleaned, 0)

    def _split_with_separator(self, text: str, separator_index: int) -> list[str]:
        if len(text) <= self.chunk_size:
            return [text]
        if separator_index >= len(self.separators):
            return self._hard_split(text)

        separator = self.separators[separator_index]
        parts = list(text) if separator == "" else text.split(separator)
        if len(parts) == 1:
            return self._split_with_separator(text, separator_index + 1)

        chunks: list[str] = []
        current = ""
        joiner = "" if separator == "" else separator

        for part in parts:
            candidate = f"{current}{joiner}{part}" if current else part
            if len(candidate) <= self.chunk_size:
                current = candidate
                continue
            if current:
                chunks.append(current)
            if len(part) > self.chunk_size:
                chunks.extend(self._split_with_separator(part, separator_index + 1))
                current = ""
            else:
                current = part

        if current:
            chunks.append(current)
        return self._apply_overlap(chunks)

    def _hard_split(self, text: str) -> list[str]:
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunks.append(text[start:end])
            start += self.chunk_size - self.chunk_overlap
        return chunks

    def _apply_overlap(self, chunks: list[str]) -> list[str]:
        if len(chunks) <= 1:
            return chunks
        overlapped: list[str] = []
        for index, chunk in enumerate(chunks):
            if index == 0:
                overlapped.append(chunk)
                continue
            prefix = chunks[index - 1][-self.chunk_overlap :]
            merged = f"{prefix} {chunk}".strip()
            overlapped.append(merged[: self.chunk_size])
        return overlapped
