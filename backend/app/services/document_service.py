import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import pypdf

from app.core.config import settings
from app.models.schemas import DocumentMetadata

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self):
        self.upload_dir: Path = settings.upload_path
        self.manifest_path: Path = self.upload_dir / "documents_manifest.json"
        self._init_manifest()

    def _init_manifest(self):
        if not self.manifest_path.exists():
            self._save_manifest({})

    def _load_manifest(self) -> Dict[str, Any]:
        try:
            if self.manifest_path.exists():
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading documents manifest: {e}")
        return {}

    def _save_manifest(self, data: Dict[str, Any]):
        try:
            with open(self.manifest_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving documents manifest: {e}")

    def save_file(self, filename: str, content: bytes) -> tuple[str, Path]:
        doc_id = str(uuid.uuid4())[:8]
        safe_filename = f"{doc_id}_{Path(filename).name}"
        file_path = self.upload_dir / safe_filename

        with open(file_path, "wb") as f:
            f.write(content)

        return doc_id, file_path

    def extract_text_and_chunks(
        self,
        file_path: Path,
        doc_id: str,
        filename: str,
        chunk_size: int = 800,
        chunk_overlap: int = 150
    ) -> tuple[int, List[Dict[str, Any]]]:
        """
        Reads a PDF file page by page, extracts text, and creates chunked passages
        with rich metadata for RAG retrieval.
        """
        chunks: List[Dict[str, Any]] = []
        reader = pypdf.PdfReader(str(file_path))
        total_pages = len(reader.pages)

        chunk_counter = 0
        for page_idx, page in enumerate(reader.pages):
            page_number = page_idx + 1
            page_text = page.extract_text() or ""
            page_text = page_text.strip()

            if not page_text:
                continue

            # Text chunking with sliding window
            start = 0
            text_length = len(page_text)

            while start < text_length:
                end = min(start + chunk_size, text_length)
                chunk_str = page_text[start:end].strip()

                if chunk_str:
                    chunks.append({
                        "id": f"{doc_id}_{chunk_counter}",
                        "text": chunk_str,
                        "metadata": {
                            "doc_id": doc_id,
                            "filename": filename,
                            "page": page_number,
                            "chunk_index": chunk_counter
                        }
                    })
                    chunk_counter += 1

                if end >= text_length:
                    break
                start += (chunk_size - chunk_overlap)

        return total_pages, chunks

    def register_document(
        self,
        doc_id: str,
        filename: str,
        total_pages: int,
        total_chunks: int,
        file_size_bytes: int
    ) -> DocumentMetadata:
        manifest = self._load_manifest()
        doc_meta = DocumentMetadata(
            doc_id=doc_id,
            filename=filename,
            total_pages=total_pages,
            total_chunks=total_chunks,
            uploaded_at=datetime.utcnow(),
            file_size_bytes=file_size_bytes
        )
        manifest[doc_id] = doc_meta.model_dump(mode="json")
        self._save_manifest(manifest)
        return doc_meta

    def list_documents(self) -> List[DocumentMetadata]:
        manifest = self._load_manifest()
        docs = []
        for item in manifest.values():
            try:
                docs.append(DocumentMetadata(**item))
            except Exception as e:
                logger.warning(f"Failed to parse document item from manifest: {e}")
        return sorted(docs, key=lambda x: x.uploaded_at, reverse=True)

    def get_document(self, doc_id: str) -> Optional[DocumentMetadata]:
        manifest = self._load_manifest()
        if doc_id in manifest:
            return DocumentMetadata(**manifest[doc_id])
        return None

    def delete_document(self, doc_id: str) -> bool:
        manifest = self._load_manifest()
        if doc_id not in manifest:
            return False

        # Remove manifest entry
        del manifest[doc_id]
        self._save_manifest(manifest)

        # Remove physical file matching pattern
        for f in self.upload_dir.glob(f"{doc_id}_*"):
            try:
                f.unlink(missing_ok=True)
            except Exception as e:
                logger.error(f"Error deleting file {f}: {e}")

        return True


document_service = DocumentService()
