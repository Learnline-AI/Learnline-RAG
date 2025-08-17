"""
PDF Processor - Enhanced version of the original PDF processing logic.

Migrated from the original implementation with improvements:
- Modular design for multiple PDF types
- Better error handling and recovery
- Progress tracking and reporting
- Configurable processing parameters
"""

import re
import fitz  # PyMuPDF
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from dataclasses import dataclass
import logging
from datetime import datetime

from ..core.models import SourceDocument, ContentType
from ..core.config import get_config
from ..core.exceptions import (
    FileProcessingError, CorruptedFileError, 
    UnsupportedFileTypeError, FileSizeError
)

logger = logging.getLogger(__name__)


@dataclass
class PageExtractionResult:
    """Result of extracting text from a single page"""
    page_number: int  # PDF page number (1-based)
    textbook_page: Optional[int]  # Detected textbook page number
    text: str
    word_count: int
    char_count: int
    line_count: int
    has_figures: bool
    has_activities: bool
    is_mostly_empty: bool
    extraction_method: str
    confidence: float = 1.0


@dataclass
class PDFExtractionResult:
    """Complete result of PDF text extraction"""
    document: SourceDocument
    full_text: str
    pages: List[PageExtractionResult]
    char_to_page_map: Dict[int, int]
    total_pages: int
    total_words: int
    total_characters: int
    content_pages: int
    extraction_method: str
    processing_time_seconds: float
    quality_metrics: Dict[str, Any]
    
    def get_page_by_number(self, page_num: int) -> Optional[PageExtractionResult]:
        """Get page extraction result by page number"""
        for page in self.pages:
            if page.page_number == page_num:
                return page
        return None


class PDFProcessor:
    """
    Enhanced PDF processor with support for educational documents.
    
    Preserves the working logic from the original implementation while
    adding modularity, better error handling, and progress tracking.
    """
    
    def __init__(self):
        self.config = get_config()
        
        # Processing parameters (can be overridden)
        self.extraction_method = "simple_left_right"
        self.min_textbook_page = 1
        self.max_textbook_page = 1000
        self.ncert_page_range = (80, 120)  # Typical NCERT page ranges
        
        # Progress tracking
        self._progress_callback = None
        
    def set_progress_callback(self, callback):
        """Set callback function for progress updates"""
        self._progress_callback = callback
    
    def process_document(self, document: SourceDocument) -> PDFExtractionResult:
        """
        Process a PDF document and extract structured text.
        
        Args:
            document: SourceDocument containing file path and metadata
            
        Returns:
            PDFExtractionResult with extracted text and metadata
        """
        start_time = datetime.now()
        
        # Validate input
        self._validate_document(document)
        
        try:
            # Open and validate PDF
            pdf_doc = self._open_pdf(document.file_path)
            
            # Extract text with progress tracking
            extraction_result = self._extract_text_with_progress(pdf_doc, document)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            extraction_result.processing_time_seconds = processing_time
            
            # Close PDF
            pdf_doc.close()
            
            logger.info(f"Successfully processed PDF {document.document_id} in {processing_time:.1f}s")
            return extraction_result
            
        except Exception as e:
            logger.error(f"Failed to process PDF {document.document_id}: {e}")
            raise FileProcessingError(f"PDF processing failed: {e}", document.file_path)
    
    def _validate_document(self, document: SourceDocument):
        """Validate document for PDF processing"""
        if document.content_type != ContentType.PDF:
            raise UnsupportedFileTypeError(
                document.file_path, 
                document.content_type.value, 
                [ContentType.PDF.value]
            )
        
        # Check file exists
        path = Path(document.file_path)
        if not path.exists():
            raise FileProcessingError(f"File not found: {document.file_path}", document.file_path)
        
        # Check file size
        if document.file_size > self.config.storage.max_file_size_mb * 1024 * 1024:
            raise FileSizeError(
                document.file_path, 
                document.file_size, 
                self.config.storage.max_file_size_mb * 1024 * 1024
            )
    
    def _open_pdf(self, file_path: str) -> fitz.Document:
        """Open PDF document with error handling"""
        try:
            doc = fitz.open(file_path)
            
            # Basic validation
            if doc.page_count == 0:
                raise CorruptedFileError(file_path, "PDF contains no pages")
            
            if doc.is_encrypted:
                # Try to decrypt with empty password
                if not doc.authenticate(""):
                    raise CorruptedFileError(file_path, "PDF is password protected")
            
            return doc
            
        except fitz.FileDataError as e:
            raise CorruptedFileError(file_path, f"Invalid PDF format: {e}")
        except fitz.FileNotFoundError as e:
            raise FileProcessingError(f"PDF file not found: {e}", file_path)
        except Exception as e:
            raise FileProcessingError(f"Failed to open PDF: {e}", file_path)
    
    def _extract_text_with_progress(self, 
                                   pdf_doc: fitz.Document, 
                                   document: SourceDocument) -> PDFExtractionResult:
        """Extract text with progress tracking"""
        total_pages = len(pdf_doc)
        
        # Initialize data structures
        pages_data = []
        full_text = ""
        char_to_page_map = {}
        current_position = 0
        
        logger.info(f"Extracting text from {total_pages} pages using {self.extraction_method}")
        
        # Process each page
        for page_num in range(total_pages):
            if self._progress_callback:
                self._progress_callback(page_num + 1, total_pages, f"Processing page {page_num + 1}")
            
            page = pdf_doc[page_num]
            
            # Extract text from page
            page_result = self._extract_page_text(page, page_num + 1)
            
            # Build character-to-page mapping
            for char_pos in range(current_position, current_position + len(page_result.text)):
                char_to_page_map[char_pos] = page_num + 1
            
            # Add to collections
            pages_data.append(page_result)
            full_text += page_result.text + "\n"
            current_position += len(page_result.text) + 1
            
            # Log progress for significant pages
            if page_num < 5 or page_result.word_count > 500:
                logger.debug(f"Page {page_num + 1}: {page_result.word_count} words, "
                           f"{page_result.char_count} chars, textbook p.{page_result.textbook_page}")
        
        # Calculate metrics
        total_words = sum(page.word_count for page in pages_data)
        total_chars = len(full_text)
        content_pages = len([p for p in pages_data if not p.is_mostly_empty])
        
        # Generate quality metrics
        quality_metrics = self._calculate_quality_metrics(pages_data, total_words, total_chars)
        
        logger.info(f"Extraction complete: {content_pages}/{total_pages} content pages, "
                   f"{total_words:,} words, {total_chars:,} characters")
        
        return PDFExtractionResult(
            document=document,
            full_text=full_text,
            pages=pages_data,
            char_to_page_map=char_to_page_map,
            total_pages=total_pages,
            total_words=total_words,
            total_characters=total_chars,
            content_pages=content_pages,
            extraction_method=self.extraction_method,
            processing_time_seconds=0.0,  # Will be set by caller
            quality_metrics=quality_metrics
        )
    
    def _extract_page_text(self, page: fitz.Page, pdf_page_num: int) -> PageExtractionResult:
        """
        Extract text from a single page using the proven left-right method.
        
        This preserves the working logic from the original implementation.
        """
        if self.extraction_method == "simple_left_right":
            page_text = self._extract_page_left_then_right(page)
        else:
            # Fallback to simple extraction
            page_text = page.get_text()
        
        # Clean the extracted text
        cleaned_text = self._clean_extracted_text(page_text)
        
        # Extract textbook page number
        textbook_page = self._extract_textbook_page_number(cleaned_text, pdf_page_num)
        
        # Calculate statistics
        word_count = len(cleaned_text.split())
        char_count = len(cleaned_text)
        line_count = cleaned_text.count('\n') + 1
        
        # Detect content types
        has_figures = bool(re.search(r'Fig\.|Figure', cleaned_text))
        has_activities = bool(re.search(r'Activity', cleaned_text))
        is_mostly_empty = char_count < 50
        
        return PageExtractionResult(
            page_number=pdf_page_num,
            textbook_page=textbook_page,
            text=cleaned_text,
            word_count=word_count,
            char_count=char_count,
            line_count=line_count,
            has_figures=has_figures,
            has_activities=has_activities,
            is_mostly_empty=is_mostly_empty,
            extraction_method=self.extraction_method,
            confidence=0.9  # Default confidence for this method
        )
    
    def _extract_page_left_then_right(self, page: fitz.Page) -> str:
        """
        Extract text with simple left-then-right ordering.
        
        PRESERVED from original implementation - this is the proven method.
        """
        # Get text with positioning information
        text_dict = page.get_text("dict")
        page_width = page.rect.width
        center_x = page_width / 2
        
        left_blocks = []
        right_blocks = []
        
        # Split blocks into left and right columns
        for block in text_dict.get("blocks", []):
            if "lines" in block:  # Text block (not image)
                # Extract all text from this block
                block_text = self._extract_block_text(block)
                
                if block_text.strip():  # Only process non-empty blocks
                    block_bbox = block.get("bbox", [0, 0, 0, 0])
                    block_left = block_bbox[0]  # Left edge of block
                    block_top = block_bbox[1]   # Top edge of block
                    
                    block_info = {
                        'text': block_text,
                        'x': block_left,
                        'y': block_top,
                        'bbox': block_bbox
                    }
                    
                    # Simple split: left of center = left column, right of center = right column
                    if block_left < center_x:
                        left_blocks.append(block_info)
                    else:
                        right_blocks.append(block_info)
        
        # Sort each column top-to-bottom (by Y coordinate)
        left_blocks.sort(key=lambda b: b['y'])
        right_blocks.sort(key=lambda b: b['y'])
        
        # Combine: left column first, then right column
        page_text_parts = []
        
        # Add left column text
        if left_blocks:
            left_text = '\n'.join(block['text'] for block in left_blocks)
            page_text_parts.append(left_text)
        
        # Add right column text
        if right_blocks:
            right_text = '\n'.join(block['text'] for block in right_blocks)
            page_text_parts.append(right_text)
        
        # Join columns with double newline to separate them clearly
        return '\n\n'.join(page_text_parts)
    
    def _extract_block_text(self, block: Dict) -> str:
        """
        Extract all text from a text block, preserving line structure.
        
        PRESERVED from original implementation.
        """
        block_lines = []
        
        for line in block.get("lines", []):
            line_text_parts = []
            
            for span in line.get("spans", []):
                text_content = span.get("text", "").strip()
                if text_content:
                    line_text_parts.append(text_content)
            
            if line_text_parts:
                # Join spans in the line with spaces
                line_text = ' '.join(line_text_parts)
                block_lines.append(line_text)
        
        # Join lines in the block with newlines
        return '\n'.join(block_lines)
    
    def _clean_extracted_text(self, raw_text: str) -> str:
        """
        Minimal cleaning - preserve structure since extraction is already clean.
        
        PRESERVED from original implementation.
        """
        # Basic normalization only
        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', raw_text)  # Multiple newlines → double newline
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)              # Multiple spaces → single space
        cleaned = cleaned.strip()
        
        # Remove only obvious PDF artifacts
        cleaned = re.sub(r'Reprint\s+\d{4}-\d{2}', '', cleaned)
        
        return cleaned
    
    def _extract_textbook_page_number(self, page_text: str, pdf_page_num: int) -> Optional[int]:
        """
        Extract textbook page number with enhanced NCERT detection.
        
        PRESERVED from original implementation with improvements.
        """
        # Strategy 1: Look for isolated numbers at end of text (most reliable for NCERT)
        end_number_match = re.search(r'\b(\d+)\s*$', page_text.strip())
        if end_number_match:
            potential_page = int(end_number_match.group(1))
            # Check if it's in a reasonable range
            if self.ncert_page_range[0] <= potential_page <= self.ncert_page_range[1]:
                return potential_page
        
        # Strategy 2: Look for numbers in the last few lines (NCERT footer pattern)
        lines = page_text.strip().split('\n')
        if lines:
            # Check last 3 lines for page numbers
            for line in lines[-3:]:
                line = line.strip()
                # Look for standalone numbers that could be page numbers
                number_matches = re.findall(r'\b(\d+)\b', line)
                for num_str in number_matches:
                    potential_page = int(num_str)
                    # NCERT page range validation
                    if self.ncert_page_range[0] <= potential_page <= self.ncert_page_range[1]:
                        return potential_page
        
        # Strategy 3: Look for NCERT-specific patterns
        ncert_patterns = [
            r'SCIENCE\s+(\d+)',           # "SCIENCE 89"
            r'(\d+)\s+SCIENCE',           # "89 SCIENCE"
            r'Reprint.*?(\d+)',           # Around reprint notices
            r'(\d+)\s*$',                 # Number at very end
        ]
        
        for pattern in ncert_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            for match in matches:
                potential_page = int(match)
                if self.ncert_page_range[0] <= potential_page <= self.ncert_page_range[1]:
                    return potential_page
        
        # Strategy 4: Look for explicit page indicators
        page_patterns = [
            r'Page\s+(\d+)',
            r'p\.\s*(\d+)',
            r'Pg\s+(\d+)',
        ]
        
        for pattern in page_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                potential_page = int(match.group(1))
                if self.min_textbook_page <= potential_page <= self.max_textbook_page:
                    return potential_page
        
        # Strategy 5: Fallback - if we find any reasonable number, use it
        end_number_match = re.search(r'\b(\d+)\s*$', page_text.strip())
        if end_number_match:
            potential_page = int(end_number_match.group(1))
            if self.min_textbook_page <= potential_page <= self.max_textbook_page:
                return potential_page
        
        # Final fallback: use PDF page number
        logger.debug(f"Could not detect textbook page number for PDF page {pdf_page_num}, using PDF page number")
        return pdf_page_num
    
    def _calculate_quality_metrics(self, 
                                  pages: List[PageExtractionResult], 
                                  total_words: int, 
                                  total_chars: int) -> Dict[str, Any]:
        """Calculate quality metrics for the extraction"""
        if not pages:
            return {"overall_quality": 0.0}
        
        # Basic metrics
        content_pages = [p for p in pages if not p.is_mostly_empty]
        avg_words_per_page = total_words / len(content_pages) if content_pages else 0
        
        # Text density (characters per page)
        avg_chars_per_page = total_chars / len(content_pages) if content_pages else 0
        
        # Educational content detection
        pages_with_figures = len([p for p in pages if p.has_figures])
        pages_with_activities = len([p for p in pages if p.has_activities])
        
        # Textbook page number detection success rate
        detected_textbook_pages = len([p for p in pages if p.textbook_page is not None])
        detection_rate = detected_textbook_pages / len(pages) if pages else 0
        
        # Overall quality score (0.0 to 1.0)
        quality_factors = []
        
        # Factor 1: Content density
        if avg_words_per_page > 200:
            quality_factors.append(1.0)
        elif avg_words_per_page > 100:
            quality_factors.append(0.8)
        else:
            quality_factors.append(0.5)
        
        # Factor 2: Educational content presence
        educational_ratio = (pages_with_figures + pages_with_activities) / len(pages) if pages else 0
        quality_factors.append(min(educational_ratio * 2, 1.0))  # Scale to 0-1
        
        # Factor 3: Page number detection
        quality_factors.append(detection_rate)
        
        # Factor 4: Content vs empty pages ratio
        content_ratio = len(content_pages) / len(pages) if pages else 0
        quality_factors.append(content_ratio)
        
        overall_quality = sum(quality_factors) / len(quality_factors)
        
        return {
            "overall_quality": overall_quality,
            "avg_words_per_page": avg_words_per_page,
            "avg_chars_per_page": avg_chars_per_page,
            "content_pages_ratio": content_ratio,
            "pages_with_figures": pages_with_figures,
            "pages_with_activities": pages_with_activities,
            "textbook_page_detection_rate": detection_rate,
            "total_content_pages": len(content_pages),
            "extraction_method": self.extraction_method
        }
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats"""
        return [".pdf"]
    
    def validate_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Validate if file can be processed"""
        path = Path(file_path)
        
        # Check extension
        if path.suffix.lower() not in self.get_supported_formats():
            return False, f"Unsupported file format: {path.suffix}"
        
        # Check if file exists
        if not path.exists():
            return False, "File does not exist"
        
        # Check file size
        size = path.stat().st_size
        max_size = self.config.storage.max_file_size_mb * 1024 * 1024
        if size > max_size:
            return False, f"File too large: {size} bytes (max: {max_size} bytes)"
        
        # Try to open PDF
        try:
            doc = fitz.open(str(path))
            if doc.page_count == 0:
                doc.close()
                return False, "PDF contains no pages"
            doc.close()
            return True, None
        except Exception as e:
            return False, f"Cannot open PDF: {e}"