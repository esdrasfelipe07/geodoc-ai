import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

from app.core.config import settings
from app.models.schemas import DocumentMetadata


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

    def get_document_file_path(self, doc_id: str) -> Optional[Path]:
        """
        Locates the physical PDF file associated with a doc_id.
        """
        for f in self.upload_dir.glob(f"{doc_id}_*"):
            if f.is_file():
                return f
        return None

    def _extract_with_pymupdf(self, file_path: Path) -> tuple[int, List[Dict[str, Any]]]:
        """
        Extracts structured text blocks using PyMuPDF (fitz).
        Preserves natural column flow and filters empty artifact blocks.
        """
        import fitz  # PyMuPDF
        doc = fitz.open(str(file_path))
        total_pages = len(doc)
        pages_content: List[Dict[str, Any]] = []

        for page_idx in range(total_pages):
            page = doc[page_idx]
            page_number = page_idx + 1
            # "blocks" returns: (x0, y0, x1, y1, text, block_no, block_type)
            # block_type == 0 represents text blocks (1 represents images)
            blocks = page.get_text("blocks")
            text_blocks = []
            for b in blocks:
                if len(b) >= 7 and b[6] == 0:  # Text block
                    block_text = b[4].strip()
                    if block_text:
                        text_blocks.append(block_text)
                elif len(b) >= 5 and isinstance(b[4], str):
                    block_text = b[4].strip()
                    if block_text:
                        text_blocks.append(block_text)

            combined_page_text = "\n\n".join(text_blocks)
            pages_content.append({
                "page": page_number,
                "text": combined_page_text
            })

        doc.close()
        return total_pages, pages_content

    def _extract_with_pypdf(self, file_path: Path) -> tuple[int, List[Dict[str, Any]]]:
        """
        Fallback extraction using pypdf if PyMuPDF is unavailable.
        """
        import pypdf
        reader = pypdf.PdfReader(str(file_path))
        total_pages = len(reader.pages)
        pages_content = []

        for page_idx, page in enumerate(reader.pages):
            page_text = (page.extract_text() or "").strip()
            pages_content.append({
                "page": page_idx + 1,
                "text": page_text
            })

        return total_pages, pages_content

    def extract_text_and_chunks(
        self,
        file_path: Path,
        doc_id: str,
        filename: str,
        chunk_size: int = 800,
        chunk_overlap: int = 150
    ) -> tuple[int, List[Dict[str, Any]]]:
        """
        Reads a PDF file page by page using PyMuPDF (or pypdf fallback),
        splits by paragraphs/semantic blocks with sliding overlap, and
        returns metadata-enriched chunks for vector indexing.
        """
        try:
            total_pages, pages_data = self._extract_with_pymupdf(file_path)
            logger.info(f"PDF {filename} extraído com sucesso via PyMuPDF ({total_pages} páginas).")
        except Exception as e:
            logger.warning(f"PyMuPDF falhou ou não está instalado ({e}). Tentando fallback com pypdf...")
            total_pages, pages_data = self._extract_with_pypdf(file_path)

        chunks: List[Dict[str, Any]] = []
        chunk_counter = 0

        for item in pages_data:
            page_number = item["page"]
            page_text = item["text"]
            if not page_text:
                continue

            # Semantic-friendly paragraph and character chunking
            paragraphs = [p.strip() for p in page_text.split("\n\n") if p.strip()]
            current_chunk = ""

            for p in paragraphs:
                if len(current_chunk) + len(p) + 2 <= chunk_size:
                    current_chunk = f"{current_chunk}\n\n{p}".strip()
                else:
                    if current_chunk:
                        chunks.append({
                            "id": f"{doc_id}_{chunk_counter}",
                            "text": current_chunk,
                            "metadata": {
                                "doc_id": doc_id,
                                "filename": filename,
                                "page": page_number,
                                "chunk_index": chunk_counter
                            }
                        })
                        chunk_counter += 1

                    # If paragraph itself is bigger than chunk_size, split by sliding window
                    if len(p) > chunk_size:
                        start = 0
                        while start < len(p):
                            end = min(start + chunk_size, len(p))
                            sub_text = p[start:end].strip()
                            if sub_text:
                                chunks.append({
                                    "id": f"{doc_id}_{chunk_counter}",
                                    "text": sub_text,
                                    "metadata": {
                                        "doc_id": doc_id,
                                        "filename": filename,
                                        "page": page_number,
                                        "chunk_index": chunk_counter
                                    }
                                })
                                chunk_counter += 1
                            if end >= len(p):
                                break
                            start += (chunk_size - chunk_overlap)
                        current_chunk = ""
                    else:
                        current_chunk = p

            if current_chunk:
                chunks.append({
                    "id": f"{doc_id}_{chunk_counter}",
                    "text": current_chunk,
                    "metadata": {
                        "doc_id": doc_id,
                        "filename": filename,
                        "page": page_number,
                        "chunk_index": chunk_counter
                    }
                })
                chunk_counter += 1

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
