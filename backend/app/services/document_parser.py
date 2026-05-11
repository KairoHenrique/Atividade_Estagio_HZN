"""
Document Parser Service
Extracts text from PDF and DOCX files for AI analysis.
"""

import os
import logging

from pypdf import PdfReader
from docx import Document

logger = logging.getLogger(__name__)


def extract_text(file_path: str) -> str:
    """
    Extract text content from a PDF or DOCX file.

    Args:
        file_path: Absolute path to the document file.

    Returns:
        Extracted text as a string.

    Raises:
        ValueError: If the file extension is not supported.
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return _extract_from_pdf(file_path)
    elif ext in (".doc", ".docx"):
        return _extract_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")


def _extract_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file using pypdf."""
    try:
        reader = PdfReader(file_path)
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        full_text = "\n\n".join(text_parts)
        if not full_text.strip():
            logger.warning(f"PDF file appears to be empty or image-based: {file_path}")
            return "[Documento PDF sem texto extraível — pode ser baseado em imagens]"
        return full_text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")


def _extract_from_docx(file_path: str) -> str:
    """Extract text from a DOCX file using python-docx."""
    try:
        doc = Document(file_path)
        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)
        full_text = "\n\n".join(text_parts)
        if not full_text.strip():
            logger.warning(f"DOCX file appears to be empty: {file_path}")
            return "[Documento DOCX sem conteúdo de texto]"
        return full_text
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {e}")
        raise ValueError(f"Failed to extract text from DOCX: {str(e)}")
