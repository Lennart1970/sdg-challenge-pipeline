"""
Text chunking module for splitting documents into manageable pieces
"""

import logging
import re
from typing import List, Dict

logger = logging.getLogger(__name__)


class TextChunker:
    """Split text into chunks for LLM processing"""
    
    def __init__(self, chunk_size: int = 1000, overlap: float = 0.15):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.overlap_size = int(chunk_size * overlap)
        
    def chunk_by_sections(self, text: str) -> List[Dict]:
        """Split text by section headings"""
        chunks = []
        
        # Split by common heading patterns
        sections = re.split(r'\n(?:#+\s+|[A-Z][^:\n]*:\s*\n)', text)
        
        for i, section in enumerate(sections):
            if len(section.strip()) > 50:  # Skip very short sections
                chunks.append({
                    "text": section.strip(),
                    "index": i,
                    "method": "section"
                })
                
        return chunks
        
    def chunk_by_size(self, text: str) -> List[Dict]:
        """Split text into fixed-size chunks with overlap"""
        chunks = []
        words = text.split()
        
        start = 0
        chunk_index = 0
        
        while start < len(words):
            end = min(start + self.chunk_size, len(words))
            chunk_text = " ".join(words[start:end])
            
            if len(chunk_text.strip()) > 50:
                chunks.append({
                    "text": chunk_text,
                    "index": chunk_index,
                    "method": "fixed_size",
                    "word_count": end - start
                })
                chunk_index += 1
                
            # Move forward with overlap
            start = end - self.overlap_size if end < len(words) else end
            
        return chunks
        
    def chunk_smart(self, text: str) -> List[Dict]:
        """Intelligent chunking: try sections first, fall back to fixed size"""
        # Try section-based chunking
        section_chunks = self.chunk_by_sections(text)
        
        if len(section_chunks) > 1:
            # Use section-based if we got multiple sections
            return section_chunks
        else:
            # Fall back to fixed-size chunking
            return self.chunk_by_size(text)
            
    def chunk_document(self, text: str, metadata: Dict = None) -> List[Dict]:
        """Chunk a document and return with metadata"""
        if not text or len(text.strip()) < 100:
            logger.warning("Text too short to chunk")
            return []
            
        chunks = self.chunk_smart(text)
        
        # Add metadata to each chunk
        for chunk in chunks:
            chunk["metadata"] = metadata or {}
            
        logger.info(f"Created {len(chunks)} chunks from document")
        return chunks
